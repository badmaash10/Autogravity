
import sys
import os
import uiautomation as auto
import time

def inspect_window(title_pattern):
    print(f"Searching for window containing: '{title_pattern}'...")
    window = auto.WindowControl(searchDepth=1, Name=title_pattern, SubName=title_pattern, RegexName=title_pattern)
    
    if not window.Exists(maxSearchSeconds=2):
        # Try finding *any* window that contains the string in its name
        found = False
        for win in auto.GetRootControl().GetChildren():
            if title_pattern.lower() in win.Name.lower():
                window = win
                found = True
                break
        
        if not found:
            print("Window not found!")
            return

    print(f"Found window: {window.Name}")
    print("Inspecting UI hierarchy (this may take a moment)...")

    # Walk the tree and print relevant text nodes
    def walk(control, depth=0):
        if depth > 10:  # Limit depth
            return
            
        try:
            name = control.Name
            control_type = control.ControlTypeName
            
            # Print if it has interesting text
            indent = "  " * depth
            if name and len(name) > 1 and not name.isspace():
                print(f"{indent}[{control_type}] {name[:100]}")
            
            for child in control.GetChildren():
                walk(child, depth + 1)
        except Exception:
            pass

    walk(window)

if __name__ == "__main__":
    target = "AntiGravity"  # Default title
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    inspect_window(target)
