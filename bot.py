#!/usr/bin/env python3
"""
Automation QA flow:
1) open .app
2) click Start (image recognition if available)
3) wait skill menu -> press Enter
4) wait controls menu -> press Enter
5) wait gameplay -> perform movements and screenshots
"""
import os
import time
import subprocess
from datetime import datetime
import pyautogui
import cv2
import numpy as np

# =========================
# CONFIG
# =========================
GAME_PATH = "/Users/miko/Applications/CrossOver/Steam/Rising Hell - Prologue.app"

TEMPLATES = {
    "start": "start_button.png",
    "skill": "skill_menu.png",
    "controls": "controls_menu.png",
    "gameplay": "gameplay_marker.png",
}

THRESHOLD = 0.78      # template match threshold (0..1). Turunkan kalau susah ketemu.
INITIAL_WAIT = 12     # waktu tunggu awal setelah membuka app (detik)
STEP_TIMEOUT = 18     # timeout menunggu setiap screen (detik)
POLL_INTERVAL = 1.0   # berapa lama antara pengecekan template (detik)
ENTER_RETRIES = 3     # fallback: berapa kali menekan Enter jika template tidak ditemukan
ENTER_DELAY = 0.8     # jeda antar Enter saat fallback
SCREENSHOT_DIR = "screenshots"
LOG_FILE = "automation_log.txt"

# =========================
# HELPERS
# =========================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def save_screenshot(name_prefix="screenshot"):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{name_prefix}_{ts}.png")
    pyautogui.screenshot(path)
    log(f"Saved screenshot: {path}")
    return path


def take_cv_screenshot():
    """Return current screen as BGR image for OpenCV"""
    img_pil = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img


def try_find_template_once(template_path, threshold=THRESHOLD):
    """Return (center_x, center_y, score) if found, else (None, None, max_val)."""
    if not os.path.exists(template_path):
        return None, None, 0.0

    screen = take_cv_screenshot()
    template = cv2.imread(template_path)
    if template is None:
        return None, None, 0.0

    th, tw = template.shape[:2]
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        top_left = max_loc
        center_x = top_left[0] + tw // 2
        center_y = top_left[1] + th // 2
        return center_x, center_y, float(max_val)
    else:
        return None, None, float(max_val)


def wait_for_template(template_path, timeout=STEP_TIMEOUT, threshold=THRESHOLD, poll=POLL_INTERVAL):
    """Poll screen until template found or timeout. Return (x,y,score) or (None,None,score)."""
    start = time.time()
    best_val = 0.0
    while time.time() - start < timeout:
        x, y, val = try_find_template_once(template_path, threshold)
        if val > best_val:
            best_val = val
        if x is not None:
            return x, y, val
        time.sleep(poll)
    return None, None, best_val


def click_at(x, y, duration=0.15):
    pyautogui.moveTo(x, y, duration=duration)
    pyautogui.click()


def click_template_or_fallback(template_key):
    """Try to find template and click it. If template missing/not found -> click center screen as fallback."""
    tpl = TEMPLATES.get(template_key)
    if tpl and os.path.exists(tpl):
        log(f"Mencari template '{tpl}' untuk '{template_key}'...")
        x, y, score = wait_for_template(tpl)
        if x is not None:
            log(f"Template '{tpl}' ditemukan (score={score:.3f}). Klik di {x},{y}")
            click_at(x, y)
            save_screenshot(f"clicked_{template_key}")
            return True
        else:
            log(f"Template '{tpl}' TIDAK ditemukan (best score={score:.3f}) -> fallback klik tengah layar.")
    else:
        log(f"Template untuk '{template_key}' tidak ada, fallback klik tengah layar.")

    # fallback: klik tengah layar
    w, h = pyautogui.size()
    cx, cy = w // 2, h // 2
    click_at(cx, cy)
    save_screenshot(f"fallback_click_{template_key}")
    return False


def press_enter_with_fallback(expect_next_template_key=None):
    """Press Enter up to ENTER_RETRIES times, after each press check if next template appears (if provided)."""
    for attempt in range(1, ENTER_RETRIES + 1):
        log(f"Fallback: menekan Enter (attempt {attempt}/{ENTER_RETRIES})")
        pyautogui.press("enter")
        time.sleep(ENTER_DELAY)

        if expect_next_template_key:
            tpl = TEMPLATES.get(expect_next_template_key)
            if tpl and os.path.exists(tpl):
                x, y, val = try_find_template_once(tpl)
                if x is not None:
                    log(f"Setelah Enter, template '{tpl}' terdeteksi (score={val:.3f}). Lanjut.")
                    return True
            # jika tidak ada template atau belum terdeteksi, loop lanjut, coba Enter lagi
    return False


# =========================
# MAIN FLOW
# =========================
def main():
    log("=== Mulai automation QA flow ===")
    log(f"Menjalankan app: {GAME_PATH}")
    try:
        subprocess.Popen(["open", "-a", GAME_PATH])
    except Exception as e:
        log(f"ERROR saat membuka app: {e}")
        return

    log(f"Tunggu {INITIAL_WAIT} detik agar app benar-benar terbuka...")
    time.sleep(INITIAL_WAIT)

    # STEP 1: klik Start
    clicked_start = click_template_or_fallback("start")
    time.sleep(2)

    # STEP 2: skill menu -> harus tekan Enter
    # Jika ada template untuk skill, tunggu muncul lalu tekan Enter; kalau tidak, tekan Enter sebagai fallback
    skill_tpl = TEMPLATES.get("skill")
    if skill_tpl and os.path.exists(skill_tpl):
        log("Menunggu menu skill (template present)...")
        x, y, score = wait_for_template(skill_tpl)
        if x is not None:
            log("Menu skill terdeteksi -> menekan Enter untuk konfirmasi.")
            pyautogui.press("enter")
            save_screenshot("after_skill_enter")
        else:
            log("Menu skill tidak terdeteksi dalam timeout -> lakukan fallback Enter.")
            pressed = press_enter_with_fallback(expect_next_template_key="controls")
            if not pressed:
                log("Fallback Enter untuk skill selesai (tidak ada bukti visual).")
    else:
        log("Template menu skill tidak ada -> langsung menekan Enter beberapa kali sebagai fallback.")
        press_enter_with_fallback(expect_next_template_key="controls")

    time.sleep(1.5)

    # STEP 3: controls menu -> harus tekan Enter
    controls_tpl = TEMPLATES.get("controls")
    if controls_tpl and os.path.exists(controls_tpl):
        log("Menunggu menu controls (template present)...")
        x, y, score = wait_for_template(controls_tpl)
        if x is not None:
            log("Menu controls terdeteksi -> menekan Enter untuk konfirmasi.")
            pyautogui.press("enter")
            save_screenshot("after_controls_enter")
        else:
            log("Menu controls tidak terdeteksi dalam timeout -> fallback Enter.")
            press_enter_with_fallback(expect_next_template_key="gameplay")
    else:
        log("Template menu controls tidak ada -> langsung menekan Enter beberapa kali sebagai fallback.")
        press_enter_with_fallback(expect_next_template_key="gameplay")

    time.sleep(2)

    # STEP 4: tunggu gameplay siap (cari marker atau fallback tunggu fixed time)
    gameplay_tpl = TEMPLATES.get("gameplay")
    if gameplay_tpl and os.path.exists(gameplay_tpl):
        log("Menunggu indikator gameplay (template present)...")
        x, y, score = wait_for_template(gameplay_tpl, timeout=30)
        if x is not None:
            log("Gameplay terdeteksi. Memulai aksi otomatis.")
            save_screenshot("gameplay_ready")
        else:
            log("Gameplay tidak terdeteksi dalam timeout -> lanjut pakai fallback.")
            save_screenshot("gameplay_timeout_fallback")
    else:
        log("Template gameplay tidak ada -> tunggu fixed time 5 detik sebagai fallback.")
        time.sleep(5)
        save_screenshot("gameplay_fallback_wait")

    # === ACTIONS in gameplay: contoh gerak dan screenshot ===
    log("Mulai aksi pemain otomatis: kombinasi gerak dan screenshot.")
    try:
        # contoh gerakan: maju, lompat, kanan, kiri, mundur dalam loop
        for i in range(4):
            pyautogui.press("w")
            time.sleep(0.4)
            pyautogui.press("space")
            time.sleep(0.4)
            pyautogui.press("d")
            time.sleep(0.4)
            pyautogui.press("a")
            time.sleep(0.4)

        # ambil beberapa screenshot gameplay
        save_screenshot("gameplay_1")
        time.sleep(1)
        save_screenshot("gameplay_2")
    except Exception as e:
        log(f"ERROR saat melakukan aksi gameplay: {e}")

    log("=== Automation flow selesai ===")
    with open(LOG_FILE, "a") as f:
        f.write("\n")

if __name__ == "__main__":
    # pastikan delays kecil yang aman
    pyautogui.PAUSE = 0.12
    pyautogui.FAILSAFE = True  # geser mouse ke pojok kiri atas untuk stop script
    main()
