import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def run_scraper():
    async with async_playwright() as p:
        # تشغيل المتصفح مع إعدادات تجنب الكشف
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # تفعيل تقنية التخفي لتجنب حظر الـ Bot
        await stealth_async(page)

        # الانتقال للموقع
        await page.goto("URL_الموقع_هنا")

        # الانتظار الذكي: ننتظر توفر كائن grecaptcha قبل التنفيذ
        # هذا يمنع ظهور الخطأ الظاهر في Screenshot_20260621_184934_Chrome.png
        try:
            await page.wait_for_function("typeof grecaptcha !== 'undefined' && typeof grecaptcha.execute === 'function'", timeout=30000)
            
            # تنفيذ الدالة بعد التأكد من وجودها
            await page.evaluate("grecaptcha.execute()")
            print("reCAPTCHA executed successfully.")
            
        except Exception as e:
            print(f"Failed to execute reCAPTCHA: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
