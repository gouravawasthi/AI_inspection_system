import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional


class AsyncAPIManager:
    def __init__(self, inspection_config: Dict[str, Dict[str, str]], storage_path: str = "pending_actions.json"):
        """
        inspection_config = {
            "visual": {"api1": "http://server1/visual/check_previous",
                       "api2": "http://server2/visual/check_duplicate"},
            "electrical": {"api1": "http://server1/electrical/check_previous",
                           "api2": "http://server2/electrical/check_duplicate"}
        }
        """
        self.inspection_config = inspection_config
        self.storage_path = storage_path
        self.pending_actions: Dict[str, Dict[str, Any]] = self._load_pending_actions()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _call_api(self, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> tuple[bool, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method.upper(), url, json=payload, timeout=5) as resp:
                    if resp.status not in (200, 201, 204):
                        return False, None
                    try:
                        return True, await resp.json()
                    except aiohttp.ContentTypeError:
                        return True, None
        except aiohttp.ClientConnectionError:
            return False, None
        except Exception as e:
            print(f"[AsyncAPIManager] Error calling {url}: {e}")
            return False, None

    def _save_pending_actions(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.pending_actions, f, indent=2)
        except Exception as e:
            print(f"[AsyncAPIManager] Error saving pending actions: {e}")

    def _load_pending_actions(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------
    # Core Logic — Validation + Duplicate check
    # ------------------------------------------------------------------
    async def process_barcode(self, barcode: str, inspection_type: str) -> Dict[str, Any]:
        """
        Called when a new barcode is scanned.
        Runs api1 + api2 concurrently.
        Returns a message dict for GUI.
        """
        msg = {"status": "error", "message": "", "buttons": [], "data": None, "action_required": False}

        if inspection_type not in self.inspection_config:
            msg["message"] = f"Unknown inspection type: {inspection_type}"
            return msg

        cfg = self.inspection_config[inspection_type]
        api1_url, api2_url = cfg["api1"], cfg["api2"]

        # Call both APIs concurrently
        results = await asyncio.gather(
            self._call_api("post", api1_url, {"barcode": barcode}),
            self._call_api("post", api2_url, {"barcode": barcode}),
            return_exceptions=True
        )

        # Unpack
        (ok1, result1), (ok2, result2) = results if isinstance(results[0], tuple) else [(False, None), (False, None)]

        # --- Server errors ---
        if not ok1 and not ok2:
            msg["message"] = f"Can't proceed — both {inspection_type} servers are not running."
            return msg
        elif not ok1:
            msg["message"] = f"Can't proceed — {inspection_type} Server 1 not running."
            return msg
        elif not ok2:
            msg["message"] = f"Can't proceed — {inspection_type} Server 2 not running."
            return msg

        # --- API1 returned None ---
        if result1 in (None, "", {}, []):
            msg["message"] = f"Barcode was not tested in previous {inspection_type} inspection, can’t proceed."
            return msg

        # --- API1 returned True ---
        if result1 is True:
            if result2 in (None, "", {}, []):
                return {
                    "status": "success",
                    "message": "Proceed with inspection.",
                    "buttons": [],
                    "data": None,
                    "action_required": False
                }

            if isinstance(result2, dict) and result2:
                msg.update({
                    "status": "warning",
                    "message": f"Barcode already scanned in {inspection_type} — duplicate record. Do you want to proceed?",
                    "buttons": ["Delete", "Update", "Append"],
                    "data": result2,
                    "action_required": True
                })
                return msg

        msg["message"] = "Unexpected API response."
        return msg

    # ------------------------------------------------------------------
    # Handle user choice (Delete / Update / Append)
    # ------------------------------------------------------------------
    async def execute_action(self, inspection_type: str, action: str, barcode: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {"status": "error", "message": "", "data": None}

        if inspection_type not in self.inspection_config:
            result["message"] = f"Unknown inspection type: {inspection_type}"
            return result

        api2_url = self.inspection_config[inspection_type]["api2"]
        action = action.lower().strip()

        if action == "delete":
            ok, resp = await self._call_api("delete", api2_url, {"barcode": barcode})
            result.update({
                "status": "success" if ok else "error",
                "message": f"Barcode {barcode} deleted successfully." if ok else f"Failed to delete barcode {barcode}.",
                "data": resp
            })
            return result

        elif action in ("update", "append"):
            # Store for deferred commit
            self.pending_actions[barcode] = {"inspection_type": inspection_type, "action": action, "data": data}
            self._save_pending_actions()
            result["status"] = "pending"
            result["message"] = f"Action '{action}' recorded for barcode {barcode} ({inspection_type}). Will execute after inspection."
            return result

        result["message"] = f"Invalid action '{action}'."
        return result

    # ------------------------------------------------------------------
    # Commit pending update/append (after inspection ends)
    # ------------------------------------------------------------------
    async def commit_pending_actions(self) -> Dict[str, int]:
        summary = {"executed": 0, "failed": 0}

        for barcode, info in list(self.pending_actions.items()):
            inspection_type = info["inspection_type"]
            api2_url = self.inspection_config[inspection_type]["api2"]
            action = info["action"]
            data = info["data"]

            if action == "update":
                ok, _ = await self._call_api("put", api2_url, {"barcode": barcode, "data": data})
            elif action == "append":
                ok, _ = await self._call_api("post", api2_url, {"barcode": barcode, "data": data})
            else:
                ok = False

            if ok:
                summary["executed"] += 1
                del self.pending_actions[barcode]
            else:
                summary["failed"] += 1

        self._save_pending_actions()
        return summary

#------------------------------------------------------------------Call-----------------------------------------

import asyncio
from api_manager_async import AsyncAPIManager

config = {
    "visual": {
        "api1": "http://localhost:5001/visual/check_previous",
        "api2": "http://localhost:5002/visual/check_duplicate"
    },
    "electrical": {
        "api1": "http://localhost:5001/electrical/check_previous",
        "api2": "http://localhost:5002/electrical/check_duplicate"
    }
}

api = AsyncAPIManager(config)

async def main():
    # GUI scans barcode
    result = await api.process_barcode("ABC123", "visual")
    print(result["message"])

    if result["action_required"]:
        # simulate user choice
        user_action = "update"
        r = await api.execute_action("visual", user_action, "ABC123", data={"temp": 42})
        print(r["message"])

    # after inspection done for ABC123
    summary = await api.commit_pending_actions()
    print("Pending summary:", summary)

asyncio.run(main())
