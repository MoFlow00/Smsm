import asyncio
import csv
import os
import re
import subprocess
from datetime import datetime
from playwright.async_api import async_playwright

SITE_KEY = "6LfMkZUsAAAAAPalgTg0oLOFS1z3H6FBgGeMtk4c"
# إنشاء اسم ملف جديد لكل جلسة بناءً على الوقت الحالي
OUTPUT_CSV = f"data/channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SEEN_FILE = "seen_usernames.txt"
QUEUE_FILE = "queue.txt"
VISITED_FILE = "visited_queries.txt"

# التأكد من وجود مجلد data
if not os.path.exists("data"):
    os.makedirs("data")

# ... (بقية المتغيرات والدوال كما هي)

def save_channel(item):
    global total_collected
    username = item.get("username")
    if not username or username in seen_usernames:
        return
    seen_usernames.add(username)
    save_seen(username)
    total_collected += 1

    # الكتابة في ملف الجلسة الحالي
    file_exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["username", "kind", "name", "user_count", "bio"])
        writer.writerow([
            username, item.get("kind", ""), item.get("name", ""),
            item.get("user_count", ""), (item.get("bio") or "").replace("\n", " ")
        ])

# عدّل دالة الرفع لترفع كل الملفات الجديدة
def git_push_changes():
    try:
        subprocess.run(["git", "add", "data/"], check=True) # يرفع ملفات الـ CSV فقط
        subprocess.run(["git", "add", SEEN_FILE, QUEUE_FILE, VISITED_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-save session {OUTPUT_CSV}"], check=True)
        subprocess.run(["git", "push"], check=True)
    except Exception as e:
        print(f"Git push failed: {e}")

# في دالة main، استدعِ git_push_changes عند انتهاء الجلسة
# ...
