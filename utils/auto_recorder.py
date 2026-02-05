"""
Automated Response Recorder
===========================
Records the chat automatically when a message is sent.
Features:
- Auto-scroll to bottom every 3 seconds
- Auto-close "Files with changes" panel
- Detect response completion via rating icons (👍👎)
- Auto-stop and send video
"""

import cv2
import numpy as np
import pyautogui
import threading
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


# Anchor paths
ANCHORS_PATH = Path(__file__).parent.parent / "anchors"
FILES_PANEL_CLOSE_ANCHOR = ANCHORS_PATH / "files_panel_close.png"
RESPONSE_COMPLETE_ANCHOR = ANCHORS_PATH / "response_complete.png"  # Thumbs up/down icons
CHAT_INPUT_ANCHOR = ANCHORS_PATH / "chat_input.png"


class AutoRecorder:
    """
    Automated screen recorder that:
    - Starts recording when triggered
    - Scrolls chat to bottom periodically
    - Closes "Files with changes" panel automatically
    - Detects response completion
    - Stops and returns video
    """
    
    def __init__(self, output_dir: Path, on_complete: Optional[Callable] = None):
        self.output_dir = output_dir
        self.on_complete = on_complete  # Callback when recording complete
        
        self.recording = False
        self.output_path = None
        self.thread = None
        
        # Settings
        self.fps = 8
        self.scale = 0.5
        self.max_duration = 120  # Max 2 minutes
        self.scroll_interval = 3  # Scroll every 3 seconds
        self.check_interval = 2  # Check for completion every 2 seconds
        
        # State
        self.last_scroll_time = 0
        self.last_check_time = 0
        self.chat_position = None  # Cached chat area position
        
    def start(self) -> Path:
        """Start automated recording."""
        if self.recording:
            return None
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Record right half
        self.region = (screen_width // 2, 0, screen_width // 2, screen_height)
        
        # Find chat position for scrolling
        self._find_chat_position()
        
        # Output file
        timestamp = datetime.now().strftime('%H%M%S')
        self.output_path = self.output_dir / f"auto_recording_{timestamp}.mp4"
        
        # Start recording thread
        self.recording = True
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()
        
        return self.output_path
    
    def stop(self) -> Path:
        """Stop recording and return file path."""
        self.recording = False
        if self.thread:
            self.thread.join(timeout=5)
        return self.output_path
    
    def _find_chat_position(self):
        """Find the chat area position using anchor."""
        try:
            if CHAT_INPUT_ANCHOR.exists():
                location = pyautogui.locateOnScreen(
                    str(CHAT_INPUT_ANCHOR), confidence=0.7, grayscale=True
                )
                if location:
                    center = pyautogui.center(location)
                    self.chat_position = (center.x, center.y - 200)
        except Exception:
            pass
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        try:
            if self.chat_position:
                pyautogui.moveTo(self.chat_position[0], self.chat_position[1])
                pyautogui.scroll(-10)  # Scroll down
        except Exception:
            pass
    
    def _close_files_panel(self):
        """Close the 'Files with changes' panel using header + offset."""
        try:
            # 1. Look for the static header anchor
            if FILES_PANEL_CLOSE_ANCHOR.exists():
                location = pyautogui.locateOnScreen(
                    str(FILES_PANEL_CLOSE_ANCHOR), confidence=0.7, grayscale=True
                )
                if location:
                    header_center = pyautogui.center(location)
                    
                    # 2. Add offset if available
                    offset_file = ANCHORS_PATH / "files_panel_offset.txt"
                    if offset_file.exists():
                        try:
                            with open(offset_file, "r") as f:
                                offset_x, offset_y = map(int, f.read().strip().split(","))
                            
                            target_x = header_center.x + offset_x
                            target_y = header_center.y + offset_y
                            
                            pyautogui.click(target_x, target_y)
                            time.sleep(0.3)
                            return True
                        except Exception:
                            pass
                            
                    # Fallback: Just click center of anchor (if no offset or legacy anchor)
                    pyautogui.click(header_center.x, header_center.y)
                    time.sleep(0.3)
                    return True
        except Exception:
            pass
        return False
    
    def _check_response_complete(self) -> bool:
        """Check if response is complete by looking for rating icons."""
        try:
            if RESPONSE_COMPLETE_ANCHOR.exists():
                location = pyautogui.locateOnScreen(
                    str(RESPONSE_COMPLETE_ANCHOR), confidence=0.6, grayscale=True
                )
                return location is not None
        except Exception:
            pass
        return False
    
    def _record_loop(self):
        """Main recording loop with automation."""
        x, y, w, h = self.region
        out_w, out_h = int(w * self.scale), int(h * self.scale)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(self.output_path), fourcc, self.fps, (out_w, out_h))
        
        start_time = time.time()
        frame_interval = 1.0 / self.fps
        
        try:
            while self.recording and (time.time() - start_time) < self.max_duration:
                frame_start = time.time()
                current_time = time.time()
                
                # Auto-scroll every 3 seconds
                if current_time - self.last_scroll_time > self.scroll_interval:
                    self._scroll_to_bottom()
                    self.last_scroll_time = current_time
                
                # Check for files panel and response completion every 2 seconds
                if current_time - self.last_check_time > self.check_interval:
                    self._close_files_panel()
                    
                    # Check if response is complete
                    if self._check_response_complete():
                        # Response complete! Record a few more seconds then stop
                        time.sleep(2)
                        self.recording = False
                    
                    self.last_check_time = current_time
                
                # Capture frame
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame = cv2.resize(frame, (out_w, out_h))
                out.write(frame)
                
                # Maintain FPS
                elapsed = time.time() - frame_start
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                    
        finally:
            out.release()
            self.recording = False
            
            # Trigger callback
            if self.on_complete and self.output_path.exists():
                self.on_complete(self.output_path)


# Global instance
_auto_recorder: Optional[AutoRecorder] = None


def get_auto_recorder(output_dir: Path) -> AutoRecorder:
    global _auto_recorder
    if _auto_recorder is None:
        _auto_recorder = AutoRecorder(output_dir)
    return _auto_recorder
