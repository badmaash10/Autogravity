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


# Anchor images for permission dialogs
ANCHORS_PATH = Path(__file__).parent.parent / "anchors"

# File access approval (existing)
APPROVAL_DIALOG_ANCHOR = ANCHORS_PATH / "approval_dialog.png"
APPROVE_BUTTON_ANCHOR = ANCHORS_PATH / "approve_button.png"
REJECT_BUTTON_ANCHOR = ANCHORS_PATH / "reject_button.png"

# CLI command execution approval (new)
CLI_COMMAND_ANCHOR = ANCHORS_PATH / "cli_command_dialog.png"
CLI_APPROVE_BUTTON_ANCHOR = ANCHORS_PATH / "cli_approve_button.png"
CLI_REJECT_BUTTON_ANCHOR = ANCHORS_PATH / "cli_reject_button.png"


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
        self.dialog_type = None  # 'file_access' or 'cli_command'
    
    def detect_approval_dialog(self) -> bool:
        """
        Check if a file access approval dialog is visible on screen.
        Returns True if found.
        """
        if not APPROVAL_DIALOG_ANCHOR.exists():
            return False
        
        try:
            location = pyautogui.locateOnScreen(
                str(APPROVAL_DIALOG_ANCHOR),
                confidence=0.7,
                grayscale=True
            )
            if location is not None:
                self.dialog_type = 'file_access'
                return True
            return False
        except Exception:
            return False
    
    def detect_cli_command_dialog(self) -> bool:
        """
        Check if a CLI command execution dialog is visible on screen.
        Returns True if found.
        """
        if not CLI_COMMAND_ANCHOR.exists():
            return False
        
        try:
            location = pyautogui.locateOnScreen(
                str(CLI_COMMAND_ANCHOR),
                confidence=0.7,
                grayscale=True
            )
            if location is not None:
                self.dialog_type = 'cli_command'
                return True
            return False
        except Exception:
            return False
    
    def detect_any_dialog(self) -> bool:
        """
        Check for any type of approval dialog.
        Returns True if any dialog is found.
        """
        return self.detect_approval_dialog() or self.detect_cli_command_dialog()
    
    def click_approve(self) -> bool:
        """Click the approve button based on dialog type."""
        # Select appropriate anchor based on dialog type
        if self.dialog_type == 'cli_command':
            anchor = CLI_APPROVE_BUTTON_ANCHOR
        else:
            anchor = APPROVE_BUTTON_ANCHOR
        
        if not anchor.exists():
            # Fallback: press Enter (often approves)
            pyautogui.press("enter")
            return True
        
        try:
            location = pyautogui.locateOnScreen(
                str(anchor),
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
        """Click the reject button based on dialog type."""
        # Select appropriate anchor based on dialog type
        if self.dialog_type == 'cli_command':
            anchor = CLI_REJECT_BUTTON_ANCHOR
        else:
            anchor = REJECT_BUTTON_ANCHOR
        
        if not anchor.exists():
            # Fallback: press Escape
            pyautogui.press("escape")
            return True
        
        try:
            location = pyautogui.locateOnScreen(
                str(anchor),
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
            
            # Different messages for different dialog types
            if self.dialog_type == 'cli_command':
                title = "⚡ **CLI Command Execution Request!**"
                description = "A terminal command is waiting for approval."
            else:
                title = "📁 **File Access Request!**"
                description = "A file operation is waiting for approval."
            
            await channel.send(
                f"{title}\n"
                f"{description} Reply with:\n"
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


def calibrate_file_access_dialog():
    """Interactive calibration for file access approval dialog detection."""
    print("\n" + "=" * 50)
    print("  FILE ACCESS APPROVAL CALIBRATION")
    print("=" * 50)
    print("""
This will capture reference images for detecting FILE ACCESS dialogs.

You need to trigger a file operation that requires approval first, then:
1. Capture the file access dialog area
2. Capture the approve button
3. Capture the reject button

Press ENTER when you have a FILE ACCESS dialog visible...
""")
    input()
    
    print("\n[Step 1/3] Capturing FILE ACCESS DIALOG area...")
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
    
    print("\n✅ File access calibration complete!")


# Alias for backwards compatibility
def calibrate_approval_dialog():
    """Alias for calibrate_file_access_dialog (backwards compatibility)."""
    calibrate_file_access_dialog()


def calibrate_cli_command_dialog():
    """Interactive calibration for CLI command execution dialog detection."""
    print("\n" + "=" * 50)
    print("  CLI COMMAND EXECUTION CALIBRATION")
    print("=" * 50)
    print("""
This will capture reference images for detecting CLI COMMAND dialogs.

You need to trigger a terminal command that requires approval first, then:
1. Capture the CLI command dialog area
2. Capture the approve button
3. Capture the reject button

Press ENTER when you have a CLI COMMAND dialog visible...
""")
    input()
    
    print("\n[Step 1/3] Capturing CLI COMMAND DIALOG area...")
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
        screenshot.save(str(CLI_COMMAND_ANCHOR))
        print(f"✅ Saved: {CLI_COMMAND_ANCHOR}")
    
    print("\n[Step 2/3] Capturing APPROVE BUTTON (Run Command)...")
    print("Move mouse to the approve/run button, you have 3 seconds...")
    time.sleep(3)
    btn_pos = pyautogui.position()
    
    screenshot = pyautogui.screenshot(region=(btn_pos[0]-30, btn_pos[1]-10, 60, 20))
    screenshot.save(str(CLI_APPROVE_BUTTON_ANCHOR))
    print(f"✅ Saved: {CLI_APPROVE_BUTTON_ANCHOR}")
    
    print("\n[Step 3/3] Capturing REJECT BUTTON (Cancel)...")
    print("Move mouse to the reject/cancel button, you have 3 seconds...")
    time.sleep(3)
    btn_pos = pyautogui.position()
    
    screenshot = pyautogui.screenshot(region=(btn_pos[0]-30, btn_pos[1]-10, 60, 20))
    screenshot.save(str(CLI_REJECT_BUTTON_ANCHOR))
    print(f"✅ Saved: {CLI_REJECT_BUTTON_ANCHOR}")
    
    print("\n✅ CLI command calibration complete!")


if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv:
        calibrate_cli_command_dialog()
    else:
        calibrate_file_access_dialog()

