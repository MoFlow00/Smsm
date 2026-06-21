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

seen_usernames = set()
queue = []
visited_queries = set()
total_collected = 0
session_collected = 0

def load_data():
    global seen_usernames, queue, visited_queries
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf8") as f:
            seen_usernames = set(x.strip() for x in f if x.strip())
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, encoding="utf8") as f:
            visited_queries = set(x.strip() for x in f if x.strip())
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, encoding="utf8") as f:
            queue = [x.strip() for x in f if x.strip()]
    else:
        queue = [chr(i) for i in range(ord('a'), ord('z') + 1)] + \
                [str(i) for i in range(10)] + ["_"]
        save_queue()

def save_queue():
    with open(QUEUE_FILE, "w", encoding="utf8") as f:
        for q in queue:
            f.write(q + "\n")

def save_visited(q):
    with open(VISITED_FILE, "a", encoding="utf8") as f:
        f.write(q + "\n")
    visited_queries.add(q)

def extract_words(item):
    text = f"{item.get('username', '')} {item.get('name', '')} {item.get('bio', '')} {item.get('description', '')}"
    raw_words = re.split(r'[\s_.]+', text.lower())
    return {w for w in raw_words if w.isalnum() and len(w) >= 2}

def save_seen(username):
    with open(SEEN_FILE, "a", encoding="utf8") as f:
        f.write(username + "\n")

def git_push_changes():
    """نسخة محدثة ومستقرة: حفظ، سحب، ثم رفع"""
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        
        # 1. حفظ أي تغييرات محلية فوراً
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-save scraped data"], check=False)
        
        # 2. سحب أي تغييرات تمت في المستودع قبل الرفع لتجنب الـ Reject
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        
        # 3. الرفع
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Successfully synced with GitHub.")
    except Exception as e:
        print(f"Git sync failed: {e}")

async def do_search(page, q):
    token = await page.evaluate(f'grecaptcha.execute("{SITE_KEY}", {{action:"search"}})')
    result = await page.evaluate("""
        async ({q, token}) => {
            const r = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=100`,
                {headers:{"X-Recaptcha-Token":token}});
            return await r.json();
        }
    """, {"q": q, "token": token})
    return result

async def main():
    global total_collected, session_collected
    load_data()
    
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    current_csv = os.path.join(DATA_DIR, f"channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    start_time = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # تقليل استهلاك البيانات والوقت
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] else route.continue_())
        await page.goto("https://semagram.io/")
        await page.wait_for_function("window.grecaptcha !== undefined")

        while queue:
            # الخروج بعد 3 ساعات
            if time.time() - start_time > 10800: break
            q = queue.pop(0)
            if q in visited_queries: continue
            
            try:
                data = await do_search(page, q)
                if not isinstance(data, list): continue
                
                for item in data:
                    if not isinstance(item, dict): continue
                    username = item.get("username")
                    if username and username not in seen_usernames:
                        seen_usernames.add(username)
                        save_seen(username)
                        with open(current_csv, "a", newline="", encoding="utf-8-sig") as f:
                            csv.writer(f).writerow([username, item.get("kind"), item.get("name"), item.get("user_count"), (item.get("bio") or "").replace("\n", " ")])
                        session_collected += 1
                        total_collected += 1
                        
                        # الرفع كل 500 قناة
                        if session_collected >= 500:
                            save_queue()
                            git_push_changes()
                            session_collected = 0
                    
                    for word in extract_words(item):
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
