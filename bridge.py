"""
AntiGravity Discord Bridge
===========================
This script bridges Discord messages to the AntiGravity Agent running in an IDE.

Input Flow:  Discord Message -> Paste to IDE Chat
Output Flow: Agent writes to outbox/ -> Bot sends to Discord
"""

import asyncio
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands, tasks
import pyautogui
import pyperclip
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables from .env file
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# Configuration from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
IDE_WINDOW_TITLE = os.getenv("IDE_WINDOW_TITLE", "AntiGravity")
OUTBOX_PATH = Path(os.getenv("OUTBOX_PATH", "./outbox"))
PASTE_DELAY = float(os.getenv("PASTE_DELAY_SECONDS", "0.5"))

# Ensure outbox exists
OUTBOX_PATH.mkdir(parents=True, exist_ok=True)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ----- GUI Automation with Visual Anchoring -----
ANCHORS_PATH = Path(__file__).parent / "anchors"
CHAT_INPUT_ANCHOR = ANCHORS_PATH / "chat_input.png"
SEND_BUTTON_ANCHOR = ANCHORS_PATH / "send_button.png"

# Ensure anchors directory exists
ANCHORS_PATH.mkdir(parents=True, exist_ok=True)


def find_and_focus_ide_window() -> bool:
    """
    Finds the IDE window by title and brings it to focus.
    Returns True if successful, False otherwise.
    """
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(IDE_WINDOW_TITLE)
        if windows:
            win = windows[0]
            win.activate()
            time.sleep(0.3)  # Give it time to focus
            return True
        else:
            print(f"[WARN] Could not find window with title: {IDE_WINDOW_TITLE}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to focus window: {e}")
        return False


def locate_chat_input() -> tuple:
    """
    Locates the chat input box on screen using image matching.
    Returns (x, y) center coordinates if found, None otherwise.
    """
    if not CHAT_INPUT_ANCHOR.exists():
        print(f"[WARN] Anchor image not found: {CHAT_INPUT_ANCHOR}")
        print("[INFO] Run calibration first: python bridge.py --calibrate")
        return None
    
    try:
        # Search for the anchor image on screen
        # confidence=0.8 allows for slight visual differences
        location = pyautogui.locateOnScreen(
            str(CHAT_INPUT_ANCHOR), 
            confidence=0.8,
            grayscale=True  # More robust to color changes
        )
        
        if location:
            # Get center of the found region
            center_x, center_y = pyautogui.center(location)
            print(f"[INFO] Found chat input at ({center_x}, {center_y})")
            return (center_x, center_y)
        else:
            print("[WARN] Could not locate chat input anchor on screen")
            return None
    except Exception as e:
        print(f"[ERROR] Image matching failed: {e}")
        return None


def click_chat_input() -> bool:
    """
    Locates and clicks on the chat input box.
    Returns True if successful, False otherwise.
    """
    coords = locate_chat_input()
    if coords:
        pyautogui.click(coords[0], coords[1])
        time.sleep(0.2)
        return True
    return False


def paste_to_ide(text: str) -> bool:
    """
    Pastes the given text into the IDE chat input.
    1. Focus the IDE window
    2. Locate chat input using visual anchor (or fall back to blind mode)
    3. Click on chat input
    4. Copy text to clipboard
    5. Simulate Ctrl+V
    6. Press Enter to submit
    """
    if not find_and_focus_ide_window():
        return False

    try:
        # Try to locate and click on chat input using visual anchor
        if CHAT_INPUT_ANCHOR.exists():
            if not click_chat_input():
                print("[WARN] Visual anchor failed, falling back to blind paste")
        else:
            print("[INFO] No anchor image, using blind paste mode")
        
        time.sleep(PASTE_DELAY)
        
        # Copy text to clipboard
        pyperclip.copy(text)
        time.sleep(PASTE_DELAY)

        # Paste (Ctrl+V)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(PASTE_DELAY)

        print(f"[INFO] Pasted message to IDE: {text[:50]}...")
        
        # Try to submit using send button (more reliable) or fall back to Enter
        submitted = False
        
        # Option 1: Click the send button if calibrated
        if SEND_BUTTON_ANCHOR.exists():
            try:
                location = pyautogui.locateOnScreen(
                    str(SEND_BUTTON_ANCHOR),
                    confidence=0.7,
                    grayscale=True
                )
                if location:
                    center = pyautogui.center(location)
                    pyautogui.click(center.x, center.y)
                    submitted = True
                    print("[INFO] Clicked send button")
            except Exception:
                pass
        
        # Option 2: Fall back to Enter key
        if not submitted:
            # Re-click chat input to ensure focus
            if CHAT_INPUT_ANCHOR.exists():
                click_chat_input()
                time.sleep(0.2)
            
            pyautogui.press("enter")
            time.sleep(0.1)
            pyautogui.press("enter")
            print("[INFO] Pressed Enter to submit")
        
        time.sleep(0.2)

        return True
    except Exception as e:
        print(f"[ERROR] Failed to paste to IDE: {e}")
        return False


def calibrate_anchor():
    """
    Interactive calibration: captures a screenshot region to use as visual anchor.
    User selects the chat input area on screen.
    """
    print("\n" + "=" * 50)
    print("  VISUAL ANCHOR CALIBRATION")
    print("=" * 50)
    print("""
This will capture a reference image of the chat input box.
The bot will use this image to find and click the chat input.

Instructions:
1. Make sure the IDE window is visible on screen
2. Position the chat input area so it's clearly visible
3. Press ENTER when ready...
""")
    input()
    
    print("Taking screenshot in 3 seconds...")
    print("Move your mouse to the TOP-LEFT corner of the chat input box...")
    time.sleep(3)
    
    import pyautogui
    top_left = pyautogui.position()
    print(f"Top-left captured: {top_left}")
    
    print("\nNow move your mouse to the BOTTOM-RIGHT corner of the chat input box...")
    print("You have 3 seconds...")
    time.sleep(3)
    
    bottom_right = pyautogui.position()
    print(f"Bottom-right captured: {bottom_right}")
    
    # Calculate region
    left = min(top_left[0], bottom_right[0])
    top = min(top_left[1], bottom_right[1])
    width = abs(bottom_right[0] - top_left[0])
    height = abs(bottom_right[1] - top_left[1])
    
    if width < 10 or height < 10:
        print("[ERROR] Region too small. Please try again.")
        return
    
    # Capture the region
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot.save(str(CHAT_INPUT_ANCHOR))
    
    print(f"\n✅ Anchor saved to: {CHAT_INPUT_ANCHOR}")
    print(f"   Region: {width}x{height} pixels")
    print("\nThe bridge will now use this image to locate the chat input!")


# ----- Voice Transcription -----
async def transcribe_voice_message(attachment: discord.Attachment) -> str:
    """
    Downloads a voice message and transcribes it using SpeechRecognition.
    Returns the transcribed text or an error message.
    """
    try:
        import speech_recognition as sr
        from pydub import AudioSegment

        # Download the voice file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
            await attachment.save(tmp_ogg.name)
            tmp_ogg_path = tmp_ogg.name

        # Convert to WAV for SpeechRecognition
        tmp_wav_path = tmp_ogg_path.replace(".ogg", ".wav")
        audio = AudioSegment.from_ogg(tmp_ogg_path)
        audio.export(tmp_wav_path, format="wav")

        # Transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        # Cleanup
        os.unlink(tmp_ogg_path)
        os.unlink(tmp_wav_path)

        return text
    except Exception as e:
        return f"[Transcription Error: {e}]"


# ----- Outbox Watcher -----
class OutboxHandler(FileSystemEventHandler):
    """Watches the outbox directory for new files and queues them for Discord."""

    def __init__(self, bot_instance, channel_id):
        super().__init__()
        self.bot = bot_instance
        self.channel_id = channel_id
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Avoid processing the same file twice
        if str(file_path) in self.processed_files:
            return
        self.processed_files.add(str(file_path))

        # Schedule the async send
        asyncio.run_coroutine_threadsafe(
            self.send_file_to_discord(file_path),
            self.bot.loop
        )

    async def send_file_to_discord(self, file_path: Path):
        """Reads the file and sends its content to Discord."""
        try:
            # Wait a moment to ensure the file is fully written
            await asyncio.sleep(1)
            
            # Skip already-sent files and temp files
            if ".sent_" in str(file_path) or file_path.suffix.startswith(".sent"):
                return
            
            # Check if file still exists (might have been moved/deleted)
            if not file_path.exists():
                return

            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                print(f"[ERROR] Could not find channel {self.channel_id}")
                return

            # Check file extension to determine how to send
            image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
            
            if file_path.suffix.lower() in image_extensions:
                # Send image files directly as attachments
                await channel.send(
                    f"📷 **Image from Agent:**",
                    file=discord.File(file_path)
                )
            else:
                # Read text file content
                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Binary file - send as attachment
                    await channel.send(
                        f"📎 **File from Agent:** `{file_path.name}`",
                        file=discord.File(file_path)
                    )
                    content = None
                
                if content:
                    # Handle large messages
                    if len(content) > 1900:
                        await channel.send(
                            f"📄 **Agent Response** (from `{file_path.name}`):",
                            file=discord.File(file_path)
                        )
                    else:
                        await channel.send(f"🤖 **Agent Response:**\n```\n{content}\n```")

            # Archive the file (rename instead of delete)
            try:
                archive_path = file_path.with_suffix(f".sent_{datetime.now().strftime('%H%M%S')}")
                file_path.rename(archive_path)
                print(f"[INFO] Sent and archived: {file_path.name}")
            except FileNotFoundError:
                # File was already moved/deleted - that's OK
                pass

        except Exception as e:
            print(f"[ERROR] Failed to send file to Discord: {e}")


# Global observer instance
observer = None


# ----- Discord Events -----
@bot.event
async def on_ready():
    global observer, approval_watcher
    print(f"[INFO] Bot connected as {bot.user}")
    print(f"[INFO] Listening for messages in channel ID: {DISCORD_CHANNEL_ID}")
    print(f"[INFO] Watching outbox: {OUTBOX_PATH}")

    # Start the file watcher
    handler = OutboxHandler(bot, DISCORD_CHANNEL_ID)
    observer = Observer()
    observer.schedule(handler, str(OUTBOX_PATH), recursive=False)
    observer.start()
    print("[INFO] Outbox watcher started.")
    
    # Initialize command approval watcher
    try:
        from utils.command_approval import CommandApprovalWatcher
        approval_watcher = CommandApprovalWatcher(bot, DISCORD_CHANNEL_ID)
        check_for_approval_dialogs.start()
        print("[INFO] Command approval watcher started.")
    except Exception as e:
        print(f"[WARN] Could not start approval watcher: {e}")


@bot.event
async def on_message(message: discord.Message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Only listen to the configured channel
    if message.channel.id != DISCORD_CHANNEL_ID:
        return

    # Check if it's a command - if so, don't paste it, let the command handler take over
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    text_to_paste = ""

    # Handle voice messages (audio attachments)
    for attachment in message.attachments:
        if attachment.content_type and "audio" in attachment.content_type:
            await message.add_reaction("🎤")
            transcribed = await transcribe_voice_message(attachment)
            text_to_paste += f"[Voice Message from {message.author.name}]: {transcribed}\n"
            await message.channel.send(f"📝 Transcribed: *{transcribed}*")

    # Handle text content
    if message.content:
        text_to_paste += f"[{message.author.name}]: {message.content}"

    # Paste to IDE
    if text_to_paste.strip():
        success = paste_to_ide(text_to_paste.strip())
        if success:
            await message.add_reaction("✅")
            
            # Start auto-recording if enabled
            if auto_recording_enabled:
                global auto_recorder
                try:
                    auto_recorder = get_auto_recorder(OUTBOX_PATH)
                    auto_recorder.on_complete = on_auto_recording_complete
                    auto_recorder.start()
                    await message.channel.send("🔴 Recording response...")
                except Exception as e:
                    print(f"[WARN] Auto-recording failed to start: {e}")
        else:
            await message.add_reaction("❌")
            await message.channel.send("⚠️ Failed to paste to IDE. Is the window open?")


@bot.command(name="status")
async def status_command(ctx):
    """Check the bridge status."""
    await ctx.send(f"✅ Bridge is running!\n"
                   f"📁 Watching: `{OUTBOX_PATH}`\n"
                   f"🖥️ IDE Window: `{IDE_WINDOW_TITLE}`")


@bot.command(name="ping")
async def ping_command(ctx):
    """Simple ping test."""
    await ctx.send("🏓 Pong!")


@bot.command(name="screenshot")
async def screenshot_command(ctx):
    """Take a screenshot of the desktop and send it."""
    try:
        await ctx.send("📸 Taking screenshot...")
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Save to temp file
        screenshot_path = OUTBOX_PATH / f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
        screenshot.save(str(screenshot_path))
        
        # Send to Discord
        await ctx.send("🖥️ Current desktop:", file=discord.File(screenshot_path))
        
        # Clean up
        screenshot_path.unlink()
        
    except Exception as e:
        await ctx.send(f"❌ Screenshot failed: {e}")


# ----- Screen Recording -----
from utils.screen_recorder import get_recorder, ScreenRecorder
from utils.auto_recorder import get_auto_recorder, AutoRecorder

# Global recorders
screen_recorder: ScreenRecorder = None
auto_recorder: AutoRecorder = None
auto_recording_enabled = True  # Enable/disable auto-recording


@bot.command(name="record")
async def record_command(ctx, duration: int = 30):
    """
    Start recording the right half of the screen (chat area).
    Usage: !record [duration_seconds] - default is 30 seconds
    """
    global screen_recorder
    
    try:
        if screen_recorder and screen_recorder.recording:
            await ctx.send("⚠️ Already recording! Use `!stoprecord` to stop.")
            return
        
        screen_recorder = get_recorder(OUTBOX_PATH)
        
        await ctx.send(f"🔴 Recording started for {duration}s... (right half of screen)")
        
        output_path = screen_recorder.start_recording(duration=duration, region="right")
        
        # Wait for recording to finish
        await asyncio.sleep(duration + 1)
        
        # Recording auto-stopped, send the file
        if output_path and output_path.exists():
            await ctx.send("📹 Recording complete:", file=discord.File(output_path))
            await asyncio.sleep(1)
            try:
                output_path.unlink()
            except Exception:
                pass
        else:
            await ctx.send("❌ Recording file not found")
            
    except Exception as e:
        await ctx.send(f"❌ Recording failed: {e}")


@bot.command(name="stoprecord")
async def stoprecord_command(ctx):
    """Stop the current recording and send the video."""
    global screen_recorder
    
    try:
        if not screen_recorder or not screen_recorder.recording:
            await ctx.send("⚠️ Not currently recording.")
            return
        
        await ctx.send("⏹️ Stopping recording...")
        
        output_path = screen_recorder.stop_recording()
        await asyncio.sleep(1)
        
        if output_path and output_path.exists():
            await ctx.send("📹 Recording:", file=discord.File(output_path))
            await asyncio.sleep(1)
            try:
                output_path.unlink()
            except Exception:
                pass
        else:
            await ctx.send("❌ Recording file not found")
            
    except Exception as e:
        await ctx.send(f"❌ Stop recording failed: {e}")


# Pending video to send (set by auto_recorder callback)
pending_video_path = None


async def send_pending_video():
    """Send pending auto-recorded video to Discord."""
    global pending_video_path
    
    if pending_video_path and pending_video_path.exists():
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("📹 **Response Recording:**", file=discord.File(pending_video_path))
            await asyncio.sleep(1)
            try:
                pending_video_path.unlink()
            except Exception:
                pass
        pending_video_path = None


def on_auto_recording_complete(video_path):
    """Callback when auto-recording completes."""
    global pending_video_path
    pending_video_path = video_path
    
    # Schedule sending the video
    asyncio.run_coroutine_threadsafe(send_pending_video(), bot.loop)


@bot.command(name="autorecord")
async def autorecord_command(ctx, state: str = None):
    """
    Toggle auto-recording on/off.
    Usage: !autorecord on/off or just !autorecord to see status
    """
    global auto_recording_enabled
    
    if state is None:
        status = "ON ✅" if auto_recording_enabled else "OFF ❌"
        await ctx.send(f"🎥 Auto-recording is currently: **{status}**")
        return
    
    if state.lower() in ("on", "true", "1", "enable"):
        auto_recording_enabled = True
        await ctx.send("✅ Auto-recording **enabled**. Responses will be recorded automatically!")
    elif state.lower() in ("off", "false", "0", "disable"):
        auto_recording_enabled = False
        await ctx.send("❌ Auto-recording **disabled**.")
    else:
        await ctx.send("Usage: `!autorecord on` or `!autorecord off`")


@bot.command(name="fullshot")
async def fullshot_command(ctx, pages: int = 3):
    """
    Capture full chat by scrolling and taking multiple screenshots.
    Usage: !fullshot [pages] - default is 3 pages
    """
    try:
        await ctx.send(f"📸 Capturing {pages} pages of chat...")
        
        # Focus IDE window first
        if not find_and_focus_ide_window():
            await ctx.send("❌ IDE window not found")
            return
        
        time.sleep(0.5)
        
        # Click on chat area (using anchor)
        chat_x, chat_y = None, None
        if CHAT_INPUT_ANCHOR.exists():
            location = pyautogui.locateOnScreen(
                str(CHAT_INPUT_ANCHOR), confidence=0.7, grayscale=True
            )
            if location:
                center = pyautogui.center(location)
                chat_x, chat_y = center.x, center.y - 200
                pyautogui.click(chat_x, chat_y)
                time.sleep(0.3)
        
        # Scroll to bottom first using mouse wheel
        if chat_x and chat_y:
            pyautogui.moveTo(chat_x, chat_y)
            pyautogui.scroll(-20)  # Scroll down to bottom
            time.sleep(0.5)
        
        screenshots = []
        timestamp = datetime.now().strftime('%H%M%S')
        
        for i in range(pages):
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_path = OUTBOX_PATH / f"fullshot_{timestamp}_{i}.png"
            screenshot.save(str(screenshot_path))
            screenshots.append(screenshot_path)
            
            if i < pages - 1:
                # Scroll up using mouse wheel (more reliable than pageup)
                if chat_x and chat_y:
                    pyautogui.moveTo(chat_x, chat_y)
                    pyautogui.scroll(10)  # Scroll up
                time.sleep(0.6)
        
        # Send all screenshots (oldest first for reading order)
        screenshots.reverse()
        
        for i, path in enumerate(screenshots):
            await ctx.send(
                f"📄 Page {i+1}/{pages}:",
                file=discord.File(path)
            )
            await asyncio.sleep(0.5)  # Wait for Discord to finish with file
        
        # Clean up files after all sent
        await asyncio.sleep(1)
        for path in screenshots:
            try:
                path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        
        await ctx.send("✅ Full chat captured!")
        
    except Exception as e:
        await ctx.send(f"❌ Fullshot failed: {e}")


@bot.command(name="scroll")
async def scroll_command(ctx, direction: str = "up", amount: int = 3):
    """
    Scroll the chat and take a screenshot.
    Usage: !scroll up 5 or !scroll down 2
    """
    try:
        if not find_and_focus_ide_window():
            await ctx.send("❌ IDE window not found")
            return
        
        time.sleep(0.3)
        
        # Click on chat area
        if CHAT_INPUT_ANCHOR.exists():
            location = pyautogui.locateOnScreen(
                str(CHAT_INPUT_ANCHOR), confidence=0.7, grayscale=True
            )
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center.x, center.y - 200)
                time.sleep(0.2)
        
        # Scroll
        key = "pageup" if direction.lower() == "up" else "pagedown"
        for _ in range(amount):
            pyautogui.press(key)
            time.sleep(0.2)
        
        time.sleep(0.3)
        
        # Screenshot
        screenshot = pyautogui.screenshot()
        screenshot_path = OUTBOX_PATH / f"scroll_{datetime.now().strftime('%H%M%S')}.png"
        screenshot.save(str(screenshot_path))
        
        await ctx.send(
            f"📸 After scrolling {direction} {amount}x:",
            file=discord.File(screenshot_path)
        )
        screenshot_path.unlink()
        
    except Exception as e:
        await ctx.send(f"❌ Scroll failed: {e}")


# ----- Window Control Commands -----
from utils.windows_control import (
    maximize_window, minimize_window, focus_window,
    restore_window, list_open_windows, open_project
)


@bot.command(name="max")
async def max_command(ctx, *, window_title: str = "AntiGravity"):
    """Maximize a window by title."""
    if maximize_window(window_title):
        await ctx.send(f"✅ Maximized: `{window_title}`")
    else:
        await ctx.send(f"❌ Window not found: `{window_title}`")


@bot.command(name="min")
async def min_command(ctx, *, window_title: str = "AntiGravity"):
    """Minimize a window by title."""
    if minimize_window(window_title):
        await ctx.send(f"✅ Minimized: `{window_title}`")
    else:
        await ctx.send(f"❌ Window not found: `{window_title}`")


@bot.command(name="focus")
async def focus_command(ctx, *, window_title: str = "AntiGravity"):
    """Bring a window to the foreground."""
    if focus_window(window_title):
        await ctx.send(f"✅ Focused: `{window_title}`")
    else:
        await ctx.send(f"❌ Window not found: `{window_title}`")


@bot.command(name="restore")
async def restore_command(ctx, *, window_title: str = "AntiGravity"):
    """Restore a minimized window."""
    if restore_window(window_title):
        await ctx.send(f"✅ Restored: `{window_title}`")
    else:
        await ctx.send(f"❌ Window not found: `{window_title}`")


@bot.command(name="windows")
async def windows_command(ctx):
    """List all open windows."""
    windows = list_open_windows()
    
    if not windows:
        await ctx.send("No visible windows found.")
        return
    
    lines = ["**Open Windows:**"]
    for title, is_max, is_min in windows[:15]:  # Limit to 15
        state = "🔲" if is_max else ("➖" if is_min else "🪟")
        lines.append(f"{state} `{title[:50]}`")
    
    await ctx.send("\n".join(lines))


@bot.command(name="project")
async def project_command(ctx, *, query: str = None):
    """Open a project in AntiGravity by number or name search."""
    import json
    
    # Load projects from config
    projects_file = Path(__file__).parent / "projects.json"
    if not projects_file.exists():
        await ctx.send("❌ No `projects.json` found. Please create it first.")
        return
    
    with open(projects_file) as f:
        config = json.load(f)
    
    projects = config.get("projects", [])
    
    if not query:
        # Show numbered list
        lines = ["**📂 Available Projects:**\n"]
        for i, proj in enumerate(projects, 1):
            lines.append(f"`{i}.` **{proj['name']}** - {proj.get('description', '')}")
            lines.append(f"    `{proj['path']}`\n")
        lines.append("\n**Usage:** `!project <number>` or `!project <name>`")
        await ctx.send("\n".join(lines))
        return
    
    # Try to match by number
    selected = None
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(projects):
            selected = projects[idx]
    
    # Try to match by name (fuzzy)
    if not selected:
        query_lower = query.lower()
        for proj in projects:
            if query_lower in proj['name'].lower():
                selected = proj
                break
    
    if not selected:
        await ctx.send(f"❌ Project not found: `{query}`\nUse `!project` to see available projects.")
        return
    
    await ctx.send(f"📂 Opening: **{selected['name']}**\n`{selected['path']}`...")
    
    if open_project(selected['path']):
        await ctx.send(f"✅ Project opened!")
    else:
        await ctx.send(f"❌ Failed to open project. Check if path exists.")


# Model selector anchor
MODEL_SELECTOR_ANCHOR = ANCHORS_PATH / "model_selector.png"

# Model mapping (1-indexed for user convenience)
MODELS = {
    1: "Gemini 3 Pro (High)",
    2: "Gemini 3 Pro (Low)",
    3: "Gemini 3 Flash",
    4: "Claude Sonnet 4.5",
    5: "Claude Sonnet 4.5 (Thinking)",
    6: "Claude Opus 4.5 (Thinking)",
    7: "GPT-OSS 120B (Medium)",
}


@bot.command(name="model")
async def model_command(ctx, model_num: int = None):
    """
    Switch the LLM model in the IDE.
    Usage: !model <number>
    Example: !model 3  (selects Gemini 3 Flash)
    """
    if model_num is None:
        model_list = "\n".join([f"  {k}. {v}" for k, v in MODELS.items()])
        await ctx.send(f"**Available Models:**\n```\n{model_list}\n```\nUsage: `!model <number>`")
        return
    
    if model_num not in MODELS:
        await ctx.send(f"❌ Invalid model number. Use 1-{len(MODELS)}")
        return
    
    try:
        # First, focus the IDE window
        if not find_and_focus_ide_window():
            await ctx.send("❌ Could not find IDE window")
            return
        
        model_name = MODELS[model_num]
        await ctx.send(f"🔄 Switching to: `{model_name}`...")
        
        # Try to click on the model selector using visual anchor
        if MODEL_SELECTOR_ANCHOR.exists():
            location = pyautogui.locateOnScreen(
                str(MODEL_SELECTOR_ANCHOR),
                confidence=0.7,
                grayscale=True
            )
            if location:
                center = pyautogui.center(location)
                # Click to open the dropdown
                pyautogui.click(center.x, center.y)
                time.sleep(0.5)
                
                # Click on the model tab - the dropdown appears ABOVE the button
                # Each tab is approximately 30px tall, tabs are stacked upward
                # model_num 1 is at the top, model_num 7 is closest to button
                tab_height = 30  # Approximate height of each tab
                total_models = len(MODELS)
                
                # Calculate Y position: from button, go UP by (total - model_num + 1) * tab_height
                # This puts model 1 at the top and model 7 closest to button
                offset_from_button = (total_models - model_num + 1) * tab_height
                target_y = center.y - offset_from_button
                
                pyautogui.click(center.x, target_y)
                time.sleep(0.3)
                
            else:
                await ctx.send("⚠️ Could not find model selector. Try `--calibrate-model`")
                return
        else:
            await ctx.send("⚠️ Model selector anchor not set. Run `--calibrate-model` first.")
            return
        
        await ctx.send(f"✅ Switched to: `{model_name}`")
        
    except Exception as e:
        await ctx.send(f"❌ Model switch failed: {e}")


# ----- Command Approval System -----
# Global approval watcher
approval_watcher = None


@bot.command(name="approve")
async def approve_command(ctx):
    """Approve a pending command."""
    global approval_watcher
    if approval_watcher and approval_watcher.pending_approval:
        await approval_watcher.handle_response(approved=True)
        await ctx.send("✅ Command approved!")
    else:
        await ctx.send("ℹ️ No command pending approval.")


@bot.command(name="yes")
async def yes_command(ctx):
    """Alias for approve."""
    await approve_command(ctx)


@bot.command(name="reject")
async def reject_command(ctx):
    """Reject a pending command."""
    global approval_watcher
    if approval_watcher and approval_watcher.pending_approval:
        await approval_watcher.handle_response(approved=False)
        await ctx.send("❌ Command rejected!")
    else:
        await ctx.send("ℹ️ No command pending approval.")


@bot.command(name="no")
async def no_command(ctx):
    """Alias for reject."""
    await reject_command(ctx)


@tasks.loop(seconds=10)
async def check_for_approval_dialogs():
    """Background task to check for approval dialogs on screen."""
    global approval_watcher
    if approval_watcher is None:
        return
    
    if not approval_watcher.pending_approval:
        # Check for any type of approval dialog (file access or CLI command)
        if approval_watcher.detect_any_dialog():
            await approval_watcher.take_screenshot_and_notify()


# ----- Main Entry -----
def main():
    import sys
    
    # Check for calibration modes
    if "--calibrate" in sys.argv:
        calibrate_anchor()
        return
    
    if "--calibrate-approval" in sys.argv:
        from utils.command_approval import calibrate_file_access_dialog
        calibrate_file_access_dialog()
        return
    
    if "--calibrate-cli" in sys.argv:
        from utils.command_approval import calibrate_cli_command_dialog
        calibrate_cli_command_dialog()
        return
    
    if "--calibrate-model" in sys.argv:
        print("\n" + "=" * 50)
        print("  MODEL SELECTOR CALIBRATION")
        print("=" * 50)
        print("""
This will capture a reference image of the model selector dropdown.

Instructions:
1. Make sure the IDE is visible with the model selector showing
2. The model selector is typically below the chat input
3. Press ENTER when ready...
""")
        input()
        
        print("Move mouse to the MODEL SELECTOR button, you have 3 seconds...")
        time.sleep(3)
        pos = pyautogui.position()
        
        # Capture 80x30 region around the button
        screenshot = pyautogui.screenshot(region=(pos[0]-40, pos[1]-15, 80, 30))
        screenshot.save(str(MODEL_SELECTOR_ANCHOR))
        print(f"\n✅ Model selector anchor saved to: {MODEL_SELECTOR_ANCHOR}")
        return
    
    if "--calibrate-send" in sys.argv:
        print("\n" + "=" * 50)
        print("  SEND BUTTON CALIBRATION")
        print("=" * 50)
        print("""
This will capture a reference image of the send button (arrow icon).

Instructions:
1. Make sure the IDE chat input is visible
2. The send button is typically to the right of the chat input
3. Press ENTER when ready...
""")
        input()
        
        print("Move mouse to the SEND BUTTON (arrow icon), you have 3 seconds...")
        time.sleep(3)
        pos = pyautogui.position()
        
        # Capture 40x40 region around the button
        screenshot = pyautogui.screenshot(region=(pos[0]-20, pos[1]-20, 40, 40))
        screenshot.save(str(SEND_BUTTON_ANCHOR))
        print(f"\n✅ Send button anchor saved to: {SEND_BUTTON_ANCHOR}")
        return
    
    # Calibration for auto-recording anchors
    FILES_PANEL_CLOSE_ANCHOR = ANCHORS_PATH / "files_panel_close.png"
    RESPONSE_COMPLETE_ANCHOR = ANCHORS_PATH / "response_complete.png"
    
    if "--calibrate-files-panel" in sys.argv:
        print("\n" + "=" * 50)
        print("  FILES PANEL CALIBRATION (Header + Offset)")
        print("=" * 50)
        print("""
Step 1: Capture the static HEADER text ("Files with changes").
Instructions:
1. Make sure "Files with changes" panel is OPEN
2. Move mouse to the text "Files with changes" (the static header)
3. Press ENTER...
""")
        input()
        print("Capturing header anchor in 3 seconds...")
        time.sleep(3)
        header_pos = pyautogui.position()
        
        # Capture header anchor
        screenshot = pyautogui.screenshot(region=(header_pos[0]-50, header_pos[1]-15, 100, 30))
        screenshot.save(str(FILES_PANEL_CLOSE_ANCHOR))
        print(f"✅ Header anchor saved.")
        
        print("""
Step 2: Define the Close Button Offset.
Instructions:
1. Move mouse to the CLOSE/BACK button of the panel
2. Press ENTER to save the relative position...
""")
        input()
        button_pos = pyautogui.position()
        
        # Calculate offset: button - header
        offset_x = button_pos[0] - header_pos[0]
        offset_y = button_pos[1] - header_pos[1]
        
        # Save offset to a text file next to the image
        offset_file = ANCHORS_PATH / "files_panel_offset.txt"
        with open(offset_file, "w") as f:
            f.write(f"{offset_x},{offset_y}")
            
        print(f"✅ Offset saved: ({offset_x}, {offset_y})")
        print(f"✅ Calibration complete!")
        return
    
    if "--calibrate-response-complete" in sys.argv:
        print("\n" + "=" * 50)
        print("  RESPONSE COMPLETE INDICATOR CALIBRATION")
        print("=" * 50)
        print("""
This will capture the thumbs up/down rating icons that appear
at the end of each agent response.

Instructions:
1. Wait for an agent response to complete
2. Position mouse over the THUMBS UP icon
3. Press ENTER when ready...
""")
        input()
        
        print("Move mouse to the THUMBS UP/DOWN ICONS, you have 3 seconds...")
        time.sleep(3)
        pos = pyautogui.position()
        
        # Capture a wider region to get both icons
        screenshot = pyautogui.screenshot(region=(pos[0]-40, pos[1]-15, 80, 30))
        screenshot.save(str(RESPONSE_COMPLETE_ANCHOR))
        print(f"\n✅ Response complete anchor saved to: {RESPONSE_COMPLETE_ANCHOR}")
        return
    
    print("=" * 50)
    print("  AntiGravity Discord Bridge")
    print("=" * 50)
    print(f"  Config loaded from: {ENV_PATH}")
    print(f"  Outbox directory: {OUTBOX_PATH}")
    print(f"  IDE Window Title: {IDE_WINDOW_TITLE}")
    
    # Show anchor status
    if CHAT_INPUT_ANCHOR.exists():
        print(f"  ✅ Chat Anchor: {CHAT_INPUT_ANCHOR.name}")
    else:
        print(f"  ⚠️ Chat Anchor: NOT SET (run with --calibrate)")
    
    # Show approval anchor status
    from utils.command_approval import APPROVAL_DIALOG_ANCHOR, CLI_COMMAND_ANCHOR
    if APPROVAL_DIALOG_ANCHOR.exists():
        print(f"  ✅ File Access Anchor: {APPROVAL_DIALOG_ANCHOR.name}")
    else:
        print(f"  ⚠️ File Access Anchor: NOT SET (run with --calibrate-approval)")
    
    # Show CLI command anchor status
    if CLI_COMMAND_ANCHOR.exists():
        print(f"  ✅ CLI Command Anchor: {CLI_COMMAND_ANCHOR.name}")
    else:
        print(f"  ⚠️ CLI Command Anchor: NOT SET (run with --calibrate-cli)")
    
    print("=" * 50)

    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("[ERROR] Please set DISCORD_TOKEN in .env file!")
        return

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        if observer:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    main()

