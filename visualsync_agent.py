import time
import re
import pyautogui
import pyperclip
import easyocr
import numpy as np
import pygetwindow as gw
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = r"C:\Users\kadal\Documents\financial-agent-app"
# Coordinates for the 'Sidebar' where the file list is
SIDEBAR_X = 150 
SIDEBAR_START_Y = 250 

class FinalAgent:
    def __init__(self, root):
        self.root = Path(root)
        self.reader = easyocr.Reader(['en'], gpu=True)
        self.file_map = {p.name.lower(): p for p in self.root.rglob('*') if p.suffix in ['.jsx', '.tsx', '.js', '.css']}
        self.current_y_offset = 0
        print(f"🧠 Brain Ready. {len(self.file_map)} local files mapped.")

    def get_browser_bounds(self):
        wins = [w for w in gw.getAllWindows() if "Chrome" in w.title or "Base 44" in w.title]
        return wins[0] if wins else None

    def sync_one_file(self):
        win = self.get_browser_bounds()
        if not win: return False
        win.activate()
        time.sleep(0.5)

        # 1. VISION: Identify the file from the Breadcrumbs/Tab
        # We look at the top area of the browser window
        shot = pyautogui.screenshot(region=(win.left, win.top, win.width, 200))
        results = self.reader.readtext(np.array(shot), detail=0)
        
        filename = None
        for text in results:
            match = re.search(r"([A-Za-z0-9_.-]+\.(?:jsx|tsx|js|css))", text)
            if match:
                filename = match.group(1).lower()
                break

        if not filename or filename not in self.file_map:
            print(f"⚠️ Could not identify file on screen. OCR saw: {results}")
            return False

        print(f"🎯 Target Identified: {filename}")

        # 2. COPY: Get the WHOLE code perfectly
        # Click the center of the code area
        pyautogui.click(win.left + 500, win.top + 500) 
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        
        code_content = pyperclip.paste()
        if len(code_content) < 10:
            print("❌ Copy failed or file empty.")
            return False

        # 3. PASTE: Move to VS Code
        target_path = self.file_map[filename]
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"✅ Synced {target_path.name}")

        # 4. NEXT: Click the Sidebar for the next file
        # We move the mouse to the sidebar and press 'Down' to select the next one
        pyautogui.click(win.left + SIDEBAR_X, win.top + SIDEBAR_START_Y + self.current_y_offset)
        pyautogui.press('down')
        pyautogui.press('enter')
        
        # Increment offset if needed, or just rely on 'Down' key
        time.sleep(2) # Wait for code to load
        return True

    def run_loop(self):
        print("🔥 AUTOMATION ACTIVE. Press Ctrl+C in this window to stop.")
        try:
            while True:
                success = self.sync_one_file()
                if not success:
                    print("🔄 Retrying in 5s...")
                    time.sleep(5)
                else:
                    print("🚀 Moving to next file in 3s...")
                    time.sleep(3)
        except KeyboardInterrupt:
            print("🛑 Agent Stopped.")

if __name__ == "__main__":
    agent = FinalAgent(BASE_DIR)
    agent.run_loop()