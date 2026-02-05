"""
Screen Recorder Module
======================
Records the right half of the screen (where the chat is).
Creates lightweight videos for Discord sharing.
"""

import cv2
import numpy as np
import pyautogui
import threading
import time
from pathlib import Path
from datetime import datetime


class ScreenRecorder:
    """Records a portion of the screen to a video file."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.recording = False
        self.output_path = None
        self.thread = None
        
        # Recording settings
        self.fps = 10  # Lower FPS for smaller files
        self.scale = 0.5  # Scale down for smaller files
        
    def start_recording(self, duration: int = 30, region: str = "right"):
        """
        Start recording the screen.
        
        Args:
            duration: Max recording duration in seconds
            region: "right" (right half), "left" (left half), or "full"
        """
        if self.recording:
            return None
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Calculate region to capture
        if region == "right":
            x, y = screen_width // 2, 0
            w, h = screen_width // 2, screen_height
        elif region == "left":
            x, y = 0, 0
            w, h = screen_width // 2, screen_height
        else:  # full
            x, y = 0, 0
            w, h = screen_width, screen_height
        
        self.region = (x, y, w, h)
        self.duration = duration
        
        # Output file
        timestamp = datetime.now().strftime('%H%M%S')
        self.output_path = self.output_dir / f"recording_{timestamp}.mp4"
        
        # Start recording in background thread
        self.recording = True
        self.thread = threading.Thread(target=self._record)
        self.thread.start()
        
        return self.output_path
    
    def stop_recording(self) -> Path:
        """Stop recording and return the output file path."""
        self.recording = False
        if self.thread:
            self.thread.join(timeout=5)
        return self.output_path
    
    def _record(self):
        """Internal recording loop."""
        x, y, w, h = self.region
        
        # Calculate output dimensions (scaled down)
        out_w = int(w * self.scale)
        out_h = int(h * self.scale)
        
        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            (out_w, out_h)
        )
        
        start_time = time.time()
        frame_interval = 1.0 / self.fps
        
        try:
            while self.recording and (time.time() - start_time) < self.duration:
                frame_start = time.time()
                
                # Capture screen region
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
                frame = np.array(screenshot)
                
                # Convert RGB to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Resize for smaller file
                frame = cv2.resize(frame, (out_w, out_h))
                
                # Write frame
                out.write(frame)
                
                # Maintain FPS
                elapsed = time.time() - frame_start
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                    
        finally:
            out.release()
            self.recording = False


# Global recorder instance
_recorder = None


def get_recorder(output_dir: Path) -> ScreenRecorder:
    """Get or create the global recorder instance."""
    global _recorder
    if _recorder is None:
        _recorder = ScreenRecorder(output_dir)
    return _recorder
