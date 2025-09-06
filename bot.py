import pyautogui
import subprocess
import time
from datetime import datetime

print("Mulai automation...")

# 1. Jalankan game lewat path .app (macOS style)
game_path = "/Users/miko/Applications/CrossOver/Steam/Rising Hell - Prologue.app"
subprocess.Popen(["open", "-a", game_path])

# 2. Tunggu beberapa detik biar game sempat terbuka
time.sleep(10)

# === TEST 1: Klik tombol Start ===
pyautogui.moveTo(960, 540)
pyautogui.click()
time.sleep(2)

# === TEST 2: Gerakan kombinasi ===
pyautogui.press("w")       # jalan maju
time.sleep(1)
pyautogui.press("d")       # geser kanan
time.sleep(1)
pyautogui.press("space")   # lompat
time.sleep(1)
pyautogui.press("a")       # geser kiri
time.sleep(1)
pyautogui.press("s")       # mundur
time.sleep(1)

# === TEST 3: Loop aksi berulang ===
for i in range(5):
    pyautogui.press("w")
    time.sleep(0.5)
    pyautogui.press("space")
    time.sleep(0.5)

# === TEST 4: Ambil beberapa screenshot ===
for i in range(3):
    filename = f"result_{i+1}.png"
    pyautogui.screenshot(filename)
    print(f"Screenshot disimpan: {filename}")
    time.sleep(1)

# === TEST 5: Logging hasil ===
with open("automation_log.txt", "a") as f:
    f.write(f"[{datetime.now()}] Automation selesai tanpa error.\n")

print("Automation selesai ✅ cek file result_*.png dan automation_log.txt")
