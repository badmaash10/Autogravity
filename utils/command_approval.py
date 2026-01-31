"""
Command Approval Watcher
========================
Monitors the screen for CLI command approval dialogs and allows
remote approval/rejection from Discord.

This uses visual anchoring (image matching) to detect when a command
approval dialog appears on screen.
"""

import time
import asyncio
from pathlib import Path
from datetime import datetime

import pyautogui
import discord


# Anchor image for the approval dialog
ANCHORS_PATH = Path(__file__).parent.parent / "anchors"
APPROVAL_DIALOG_ANCHOR = ANCHORS_PATH / "approval_dialog.png"
APPROVE_BUTTON_ANCHOR = ANCHORS_PATH / "approve_button.png"
REJECT_BUTTON_ANCHOR = ANCHORS_PATH / "reject_button.png"


class CommandApprovalWatcher:
    """
    Watches the screen for command approval dialogs and allows remote approval.
    """
    
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.pending_approval = False
        self.last_screenshot_path = None
        self.watching = False
    
    def detect_approval_dialog(self) -> bool:
        """
        Check if an approval dialog is visible on screen.
        Returns True if found.
        """
        if not APPROVAL_DIALOG_ANCHOR.exists():
            # Silently return False if not calibrated
            return False
        
        try:
            location = pyautogui.locateOnScreen(
                str(APPROVAL_DIALOG_ANCHOR),
                confidence=0.7,
                grayscale=True
            )
            return location is not None
        except Exception:
            # Silently fail - image matching can fail for many reasons
            return False
    
    def click_approve(self) -> bool:
        """Click the approve button."""
        if not APPROVE_BUTTON_ANCHOR.exists():
            # Fallback: press Enter (often approves)
            pyautogui.press("enter")
            return True
        
        try:
            location = pyautogui.locateOnScreen(
                str(APPROVE_BUTTON_ANCHOR),
                confidence=0.8
            )
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                return True
        except Exception:
            pass
        
        # Fallback
        pyautogui.press("enter")
        return True
    
    def click_reject(self) -> bool:
        """Click the reject button."""
        if not REJECT_BUTTON_ANCHOR.exists():
            # Fallback: press Escape
            pyautogui.press("escape")
            return True
        
        try:
            location = pyautogui.locateOnScreen(
                str(REJECT_BUTTON_ANCHOR),
                confidence=0.8
            )
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y)
                return True
        except Exception:
            pass
        
        # Fallback
        pyautogui.press("escape")
        return True
    
    async def take_screenshot_and_notify(self):
        """Take a screenshot and send to Discord for approval."""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_path = ANCHORS_PATH.parent / "outbox" / f"approval_{datetime.now().strftime('%H%M%S')}.png"
            screenshot.save(str(screenshot_path))
            self.last_screenshot_path = screenshot_path
            
            await channel.send(
                "🔐 **Command Approval Required!**\n"
                "A command is waiting for approval. Reply with:\n"
                "• `!approve` or `!yes` - to approve\n"
                "• `!reject` or `!no` - to reject",
                file=discord.File(screenshot_path)
            )
            
            self.pending_approval = True
            
        except Exception as e:
            print(f"[APPROVAL] Notification error: {e}")
    
    async def handle_response(self, approved: bool):
        """Handle the user's approval/rejection response."""
        if not self.pending_approval:
            return
        
        if approved:
            self.click_approve()
            print("[APPROVAL] Command approved via Discord")
        else:
            self.click_reject()
            print("[APPROVAL] Command rejected via Discord")
        
        self.pending_approval = False
        
        # Clean up screenshot
        if self.last_screenshot_path and self.last_screenshot_path.exists():
            try:
                self.last_screenshot_path.unlink()
            except:
                pass


def calibrate_approval_dialog():
    """Interactive calibration for approval dialog detection."""
    print("\n" + "=" * 50)
    print("  APPROVAL DIALOG CALIBRATION")
    print("=" * 50)
    print("""
This will capture reference images for detecting command approval dialogs.

You need to trigger a command that requires approval first, then:
1. Capture the approval dialog area
2. Capture the approve button
3. Capture the reject button

Press ENTER when you have an approval dialog visible...
""")
    input()
    
    print("\n[Step 1/3] Capturing APPROVAL DIALOG area...")
    print("Move mouse to TOP-LEFT of the dialog, you have 3 seconds...")
    time.sleep(3)
    top_left = pyautogui.position()
    print(f"Top-left: {top_left}")
    
    print("Move mouse to BOTTOM-RIGHT of the dialog, you have 3 seconds...")
    time.sleep(3)
    bottom_right = pyautogui.position()
    print(f"Bottom-right: {bottom_right}")
    
    # Capture dialog
    left = min(top_left[0], bottom_right[0])
    top = min(top_left[1], bottom_right[1])
    width = abs(bottom_right[0] - top_left[0])
    height = abs(bottom_right[1] - top_left[1])
    
    if width > 10 and height > 10:
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot.save(str(APPROVAL_DIALOG_ANCHOR))
        print(f"✅ Saved: {APPROVAL_DIALOG_ANCHOR}")
    
    print("\n[Step 2/3] Capturing APPROVE BUTTON...")
    print("Move mouse to the approve/run button, you have 3 seconds...")
    time.sleep(3)
    btn_pos = pyautogui.position()
    
    # Capture small region around button
    screenshot = pyautogui.screenshot(region=(btn_pos[0]-30, btn_pos[1]-10, 60, 20))
    screenshot.save(str(APPROVE_BUTTON_ANCHOR))
    print(f"✅ Saved: {APPROVE_BUTTON_ANCHOR}")
    
    print("\n[Step 3/3] Capturing REJECT BUTTON...")
    print("Move mouse to the reject/cancel button, you have 3 seconds...")
    time.sleep(3)
    btn_pos = pyautogui.position()
    
    screenshot = pyautogui.screenshot(region=(btn_pos[0]-30, btn_pos[1]-10, 60, 20))
    screenshot.save(str(REJECT_BUTTON_ANCHOR))
    print(f"✅ Saved: {REJECT_BUTTON_ANCHOR}")
    
    print("\n✅ Calibration complete! The bridge can now detect approval dialogs.")


if __name__ == "__main__":
    calibrate_approval_dialog()
