"""
Screen utility functions for proper display handling on different platforms
Including Raspberry Pi specific optimizations
"""

import sys
import platform
import os
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import Qt


class ScreenManager:
    """Manages screen display and fullscreen modes across different platforms"""
    
    def __init__(self):
        self.is_raspberry_pi = self._detect_raspberry_pi()
        self.display_server = self._detect_display_server()
        self.screen_info = None
        self._get_screen_info()
    
    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi"""
        try:
            # Check for Raspberry Pi specific files/hardware
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    return True
        except:
            pass
        
        # Alternative checks
        if platform.machine().startswith('arm'):
            return True
        
        return False
    
    def _detect_display_server(self) -> str:
        """Detect the display server (X11/Wayland)"""
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'x11'
        else:
            return 'unknown'
    
    def _get_screen_info(self):
        """Get current screen information"""
        try:
            app = QApplication.instance()
            if app is None:
                # If no app instance, we'll get info later
                return
            
            desktop = app.desktop()
            screen_geometry = desktop.screenGeometry()
            available_geometry = desktop.availableGeometry()
            
            self.screen_info = {
                'total_width': screen_geometry.width(),
                'total_height': screen_geometry.height(),
                'available_width': available_geometry.width(),
                'available_height': available_geometry.height(),
                'available_x': available_geometry.x(),
                'available_y': available_geometry.y()
            }
            
            print(f"🖥️  Screen detected: {self.screen_info['total_width']}x{self.screen_info['total_height']}")
            if self.is_raspberry_pi:
                print(f"🥧 Raspberry Pi detected - using optimized display mode ({self.display_server})")
            else:
                print(f"🖥️  Desktop platform detected ({self.display_server})")
                
        except Exception as e:
            print(f"⚠️  Could not detect screen info: {e}")
    
    def apply_fullscreen(self, window):
        """Apply the best fullscreen method for the current platform"""
        try:
            if self.screen_info is None:
                self._get_screen_info()
            
            if self.is_raspberry_pi:
                # Raspberry Pi specific fullscreen handling
                self._apply_raspberry_pi_fullscreen(window)
            else:
                # Standard fullscreen for other platforms
                self._apply_standard_fullscreen(window)
                
        except Exception as e:
            print(f"❌ Error applying fullscreen: {e}")
            # Fallback to basic fullscreen
            window.showFullScreen()
    
    def apply_fullscreen_with_margin(self, window, bottom_margin_percent=5):
        """Apply fullscreen with bottom margin (for better UI spacing)"""
        try:
            if self.screen_info:
                # Calculate dimensions with bottom margin
                target_width = self.screen_info['total_width']
                target_height = int(self.screen_info['total_height'] * (100 - bottom_margin_percent) / 100)
                
                print(f"🔧 Applying fullscreen with {bottom_margin_percent}% bottom margin: {target_width}x{target_height}")
                
                if self.is_raspberry_pi:
                    self._apply_raspberry_pi_fullscreen_with_margin(window, target_width, target_height)
                else:
                    self._apply_standard_fullscreen_with_margin(window, target_width, target_height)
            else:
                # Fallback to regular fullscreen
                self.apply_fullscreen(window)
                
        except Exception as e:
            print(f"❌ Error applying fullscreen with margin: {e}")
            self.apply_fullscreen(window)  # Fallback
    
    def _apply_raspberry_pi_fullscreen_with_margin(self, window, width, height):
        """Apply Raspberry Pi optimized fullscreen with margin"""
        try:
            print(f"🔧 Applying Pi fullscreen with margin: {width}x{height}")
            
            # Enhanced window flags for Raspberry Pi
            flags = Qt.Window | Qt.FramelessWindowHint
            
            # Add additional flags for Wayland/X11 compatibility
            if self.display_server == 'wayland':
                flags |= Qt.WindowStaysOnTopHint
            else:
                flags |= Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint
            
            window.setWindowFlags(flags)
            
            # Set geometry to cover screen width but not full height
            window.setGeometry(0, 0, width, height)
            
            # Set size constraints
            window.setMinimumSize(width, height)
            window.setMaximumSize(width, height)
            
            # Apply window attributes
            window.setAttribute(Qt.WA_ShowWithoutActivating, False)
            window.setAttribute(Qt.WA_OpaquePaintEvent, True)
            
            if self.display_server != 'wayland':
                window.setAttribute(Qt.WA_X11DoNotAcceptFocus, False)
            
            # Show and position
            window.show()
            
            # Multiple geometry applications for reliability
            for i in range(3):
                window.setGeometry(0, 0, width, height)
                if i < 2:
                    import time
                    time.sleep(0.01)
            
            window.raise_()
            window.activateWindow()
            
            print(f"✅ Pi fullscreen with margin applied: {width}x{height}")
            print(f"   Bottom margin: {self.screen_info['total_height'] - height}px")
            
        except Exception as e:
            print(f"⚠️  Pi fullscreen with margin failed: {e}")
            window.setGeometry(0, 0, width, height)
            window.show()
    
    def _apply_standard_fullscreen_with_margin(self, window, width, height):
        """Apply standard fullscreen with margin for desktop platforms"""
        window.setGeometry(0, 0, width, height)
        window.show()
    
    def _apply_raspberry_pi_fullscreen(self, window):
        """Apply Raspberry Pi optimized fullscreen with multiple fallback methods"""
        try:
            if self.screen_info:
                print(f"🔧 Applying Pi fullscreen: {self.screen_info['total_width']}x{self.screen_info['total_height']}")
                
                # Method 1: Enhanced window flags for Raspberry Pi
                flags = Qt.Window | Qt.FramelessWindowHint
                
                # Add additional flags for Wayland/X11 compatibility
                if self.display_server == 'wayland':
                    flags |= Qt.WindowStaysOnTopHint
                else:
                    flags |= Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint
                
                window.setWindowFlags(flags)
                
                # Method 2: Force window to cover entire screen
                window.setGeometry(0, 0, self.screen_info['total_width'], self.screen_info['total_height'])
                
                # Method 3: Set minimum and maximum size to screen size
                window.setMinimumSize(self.screen_info['total_width'], self.screen_info['total_height'])
                window.setMaximumSize(self.screen_info['total_width'], self.screen_info['total_height'])
                
                # Method 4: Apply window attributes for Pi optimization
                window.setAttribute(Qt.WA_ShowWithoutActivating, False)
                window.setAttribute(Qt.WA_AlwaysShowToolTips, False)
                window.setAttribute(Qt.WA_OpaquePaintEvent, True)
                
                if self.display_server != 'wayland':
                    window.setAttribute(Qt.WA_X11DoNotAcceptFocus, False)
                
                # Method 5: Show and force positioning
                window.show()
                
                # Method 6: Multiple geometry applications (Pi sometimes needs repetition)
                for i in range(3):
                    window.setGeometry(0, 0, self.screen_info['total_width'], self.screen_info['total_height'])
                    if i < 2:  # Small delay between attempts
                        import time
                        time.sleep(0.01)
                
                # Method 7: Final activation and positioning
                window.raise_()
                window.activateWindow()
                window.setFocus()
                
                print(f"✅ Raspberry Pi fullscreen applied: {self.screen_info['total_width']}x{self.screen_info['total_height']}")
                print(f"   Display server: {self.display_server}")
                print(f"   Window geometry: {window.geometry().width()}x{window.geometry().height()}")
                
            else:
                # Enhanced fallback for Pi without screen info
                print("⚠️  No screen info, using enhanced Pi fallback")
                window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                window.showMaximized()
                window.raise_()
                window.activateWindow()
                
        except Exception as e:
            print(f"⚠️  Pi fullscreen failed, using basic method: {e}")
            try:
                window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
                window.showMaximized()
            except:
                window.showFullScreen()
    
    def _apply_standard_fullscreen(self, window):
        """Apply standard fullscreen for desktop platforms"""
        window.showFullScreen()
    
    def get_optimal_window_size(self):
        """Get optimal window size for the current screen"""
        if self.screen_info:
            return (self.screen_info['available_width'], self.screen_info['available_height'])
        else:
            # Default fallback sizes
            return (1440, 900) if self.is_raspberry_pi else (1200, 800)
    
    def center_window(self, window, width=None, height=None):
        """Center window on screen with specified size"""
        if self.screen_info is None:
            self._get_screen_info()
            
        if self.screen_info:
            if width is None or height is None:
                width, height = self.get_optimal_window_size()
                
            # Calculate center position
            x = (self.screen_info['total_width'] - width) // 2
            y = (self.screen_info['total_height'] - height) // 2
            
            window.setGeometry(x, y, width, height)
        else:
            # Fallback centering
            window.resize(width or 1200, height or 800)
    
    def force_fullscreen_refresh(self, window, bottom_margin_percent=0):
        """Force a fullscreen refresh - simple maximize approach"""
        try:
            if self.is_raspberry_pi and self.screen_info:
                print("🔄 Forcing fullscreen refresh...")
                
                # Simple maximize and activate
                window.showMaximized()
                window.raise_()
                window.activateWindow()
                
                print(f"✅ Fullscreen refresh completed")
                
        except Exception as e:
            print(f"⚠️  Fullscreen refresh failed: {e}")


def force_fullscreen_refresh(window, bottom_margin_percent=0):
    """Convenience function to force fullscreen refresh"""
    screen_manager.force_fullscreen_refresh(window, bottom_margin_percent)


# Global instance
screen_manager = ScreenManager()


def apply_fullscreen_to_window(window, force_fullscreen=None, bottom_margin_percent=0):
    """
    Convenience function to apply fullscreen to any window
    
    Args:
        window: The window to apply fullscreen to
        force_fullscreen: Force fullscreen mode (True/False) or None for config default
        bottom_margin_percent: Percentage of screen height to leave as bottom margin (0-20)
    """
    try:
        print(f"🔧 apply_fullscreen_to_window called with margin: {bottom_margin_percent}%")
        
        # Try to get GUI config to check fullscreen preference
        should_fullscreen = True  # Default
        
        if force_fullscreen is not None:
            should_fullscreen = force_fullscreen
        else:
            # Try to read from config if available
            try:
                import sys
                import os
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
                if config_path not in sys.path:
                    sys.path.insert(0, config_path)
                
                from config import config_manager
                config = config_manager.load_config()
                should_fullscreen = getattr(config.gui, 'fullscreen_mode', True)
                
                # Check if Pi optimization is enabled
                pi_optimized = getattr(config.gui, 'raspberry_pi_optimized', True)
                if screen_manager.is_raspberry_pi and not pi_optimized:
                    print("📱 Raspberry Pi optimization disabled in config")
                    should_fullscreen = False
                    
            except Exception as e:
                # Config not available, use default
                pass
        
        if should_fullscreen:
            if bottom_margin_percent > 0:
                print(f"📏 Using margin mode: {bottom_margin_percent}%")
                screen_manager.apply_fullscreen_with_margin(window, bottom_margin_percent)
            else:
                print("📏 Using full screen mode")
                screen_manager.apply_fullscreen(window)
        else:
            # Use windowed mode with optimal size
            width, height = screen_manager.get_optimal_window_size()
            if bottom_margin_percent > 0:
                height = int(height * (100 - bottom_margin_percent) / 100)
            screen_manager.center_window(window, width, height)
            window.show()
            
    except Exception as e:
        print(f"⚠️  Fullscreen application failed: {e}")
        window.showMaximized()  # Fallback


def get_screen_info():
    """Get current screen information"""
    return screen_manager.screen_info


def is_raspberry_pi():
    """Check if running on Raspberry Pi"""
    return screen_manager.is_raspberry_pi