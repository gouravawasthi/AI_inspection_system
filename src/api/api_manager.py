import requests
from typing import Any, Dict, Optional, Tuple


class APIManager:
    """
    Handles two dependent API calls (API1 and API2) and subsequent actions:
    delete, update, append.

    Usage:
        api = APIManager(api1_url, api2_url, placeholders=("visual", "electrical"))
        result = api.process_barcode("12345")
        if result["action_required"]:
            api.execute_action("delete", barcode="12345")
    """

    def __init__(self, api1_url: str, api2_url: str, placeholders: Tuple[str, str]):
        self.api1_url = api1_url
        self.api2_url = api2_url
        self.placeholders = placeholders  # e.g. ("visual", "electrical")
        self.pending_actions: Dict[str, Dict[str, Any]] = {}  # store future update/append payloads

    # ---------------------------------------------------
    #  Internal API caller helper
    # ---------------------------------------------------
    def _call_api(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 5,
    ) -> Tuple[bool, Optional[Any]]:
        try:
            method = method.lower()
            if method == "get":
                response = requests.get(url, timeout=timeout)
            elif method == "post":
                response = requests.post(url, json=payload, timeout=timeout)
            elif method == "put":
                response = requests.put(url, json=payload, timeout=timeout)
            elif method == "delete":
                response = requests.delete(url, json=payload, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code not in (200, 201, 204):
                return False, None

            try:
                return True, response.json()
            except ValueError:
                return True, None

        except requests.exceptions.ConnectionError:
            return False, None
        except Exception as e:
            print(f"[APIManager] Error calling {url} ({method}): {e}")
            return False, None

    # ---------------------------------------------------
    #  Main process logic
    # ---------------------------------------------------
    def process_barcode(self, barcode: str) -> Dict[str, Any]:
        """
        Main logic orchestrating both APIs.
        Returns structured dict for GUI.
        """

        msg = {
            "status": "error",
            "message": "",
            "buttons": [],
            "data": None,
            "action_required": False,
        }

        ok1, result1 = self._call_api("post", self.api1_url, {"barcode": barcode})
        ok2, result2 = self._call_api("post", self.api2_url, {"barcode": barcode})

        # ---- Server availability ----
        if not ok1 and not ok2:
            msg["message"] = "Can't proceed — both servers are not running."
            return msg
        elif not ok1:
            msg["message"] = "Can't proceed — Server 1 not running."
            return msg
        elif not ok2:
            msg["message"] = "Can't proceed — Server 2 not running."
            return msg

        # ---- API1 None ----
        if result1 in (None, "", {}, []):
            msg["message"] = (
                f"Barcode was not tested in previous {self.placeholders[0]} inspection, can’t proceed."
            )
            return msg

        # ---- API1 True ----
        if result1 is True:
            # API2 None → proceed silently
            if result2 in (None, "", {}, []):
                return {
                    "status": "success",
                    "message": "Proceed with inspection.",
                    "buttons": [],
                    "data": None,
                    "action_required": False,
                }

            # API2 contains duplicate → ask user
            if isinstance(result2, dict) and len(result2) > 0:
                msg.update(
                    {
                        "status": "warning",
                        "message": f"Barcode already scanned in {self.placeholders[1]} — duplicate record. Do you want to proceed?",
                        "buttons": ["Delete", "Update", "Append"],
                        "data": result2,
                        "action_required": True,
                    }
                )
                return msg

        msg["message"] = "Unexpected API response."
        return msg

    # ---------------------------------------------------
    #  Action handlers (delete, update, append)
    # ---------------------------------------------------
    def execute_action(self, action: str, barcode: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute user-chosen action:
          - delete: immediate DELETE call to API2
          - update/append: store payload for later POST/PUT
        """
        result = {"status": "error", "message": "", "data": None}

        action = action.lower().strip()

        if action == "delete":
            ok, resp = self._call_api("delete", self.api2_url, {"barcode": barcode})
            if ok:
                result["status"] = "success"
                result["message"] = f"Barcode {barcode} deleted successfully."
                result["data"] = resp
            else:
                result["message"] = f"Failed to delete barcode {barcode}."
            return result

        elif action in ("update", "append"):
            # save for later execution
            self.pending_actions[barcode] = {"action": action, "data": data}
            result["status"] = "pending"
            result["message"] = f"Action '{action}' recorded for barcode {barcode}. Will execute after inspection."
            return result

        else:
            result["message"] = f"Invalid action '{action}'."
            return result

    # ---------------------------------------------------
    #  Trigger pending actions after inspection
    # ---------------------------------------------------
    def commit_pending_actions(self) -> Dict[str, Any]:
        """
        Execute all stored update/append actions.
        Returns summary.
        """
        summary = {"executed": 0, "failed": 0}

        for barcode, action_info in list(self.pending_actions.items()):
            action = action_info["action"]
            data = action_info["data"]

            if action == "update":
                ok, _ = self._call_api("put", self.api2_url, {"barcode": barcode, "data": data})
            elif action == "append":
                ok, _ = self._call_api("post", self.api2_url, {"barcode": barcode, "data": data})
            else:
                ok = False

            if ok:
                summary["executed"] += 1
                del self.pending_actions[barcode]
            else:
                summary["failed"] += 1

        return summary

#from api_manager import APIManager

#api = APIManager(
#    api1_url="http://localhost:5001/check_previous",
#    api2_url="http://localhost:5002/check_duplicate",
#    placeholders=("visual", "electrical")
#)

## --- Validate barcode ---
#response = api.process_barcode("ABC123")

#if response["status"] == "warning":
#    # GUI asks user for Delete / Update / Append
#    user_action = "delete"
#    action_result = api.execute_action(user_action, "ABC123")
#    print(action_result)

#elif response["status"] == "success":
#    print("Proceed to inspection...")

## --- Later (after inspection data collected) ---
#final = api.commit_pending_actions()
#print("Pending updates summary:", final)
