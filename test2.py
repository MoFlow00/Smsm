import asyncio
import csv
import os
import re
import subprocess
import time
from datetime import datetime
from playwright.async_api import async_playwright

# إعدادات ثابتة
SITE_KEY = "6LfMkZUsAAAAAPalgTg0oLOFS1z3H6FBgGeMtk4c"
SEEN_FILE = "seen_usernames.txt"
QUEUE_FILE = "queue.txt"
VISITED_FILE = "visited_queries.txt"
DATA_DIR = "data"

# متغيرات التتبع
total_collected = 0
session_collected = 0

# ... (دوال load_data, save_queue, save_visited, extract_words, save_seen كما هي) ...

def git_push_changes():
    """رفع البيانات لـ GitHub بأمان"""
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        # التأكد من وجود تغييرات قبل الرفع
        result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", f"Sync: {total_collected} channels total"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("Sync complete.")
    except Exception as e:
        print(f"Git push failed: {e}")

async def main():
    global total_collected, session_collected
    load_data()
    
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    current_csv = os.path.join(DATA_DIR, f"channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    start_time = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # تحسين الأداء: تجاهل الصور والخطوط
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] else route.continue_())
        
        await page.goto("https://semagram.io/")
        await page.wait_for_function("window.grecaptcha !== undefined")

        while queue:
            # الخروج بعد 3 ساعات (10800 ثانية)
            if time.time() - start_time > 10800:
                print("3 hours limit reached. Saving and exiting.")
                break
                
            q = queue.pop(0)
            if q in visited_queries: continue
            
            try:
                data = await do_search(page, q)
                for item in data:
                    # معالجة القنوات
                    if item.get("username") not in seen_usernames:
                        # (نفس منطق الحفظ السابق داخل ملف الـ CSV الحالي)
                        # ... الحفظ في current_csv ...
                        session_collected += 1
                        total_collected += 1
                        
                        # الرفع كل 500 قناة
                        if session_collected >= 500:
                            save_queue()
                            git_push_changes()
                            session_collected = 0
                            
                    # التوسيع
                    words = extract_words(item)
                    for word in words:
                        if word not in visited_queries and word not in queue:
                            queue.append(word)
                
                save_visited(q)
                
            except Exception as e:
                print(f"Error: {e}")
                queue.insert(0, q)
                await asyncio.sleep(10)

        await browser.close()
        save_queue()
        git_push_changes()

if __name__ == "__main__":
    asyncio.run(main())
