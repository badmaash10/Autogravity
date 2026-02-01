
import pyautogui
import pyperclip
import time
from pathlib import Path

# Load anchor
ANCHOR = Path(__file__).parent.parent / "anchors" / "chat_input.png"

def test_copy():
    print("Locating chat input...")
    location = pyautogui.locateOnScreen(str(ANCHOR), confidence=0.7, grayscale=True)
    
    if not location:
        print("Chat input not found!")
        return

    center = pyautogui.center(location)
    
    # Click 300px ABOVE the input box (into the chat history area)
    # Adjust this value if needed!
    target_y = center.y - 300
    target_x = center.x
    
    print(f"Clicking at ({target_x}, {target_y}) to focus chat log...")
    pyautogui.click(target_x, target_y)
    time.sleep(0.5)
    
    print("Selecting All (Ctrl+A)...")
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.5)
    
    print("Copying (Ctrl+C)...")
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.5)
    
    content = pyperclip.paste()
    print(f"\n--- CLIPBOARD CONTENT ({len(content)} chars) ---\n")
    print(content[-500:]) # Print last 500 chars
    print("\n----------------------------------------------")

if __name__ == "__main__":
    test_copy()
