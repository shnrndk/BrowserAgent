from playwright.sync_api import sync_playwright
import time

def test():
    print("Starting Playwright test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--proxy-bypass-list=<-loopback>"])
        page = browser.new_page()
        print("Navigating to URL...")
        try:
            page.goto("http://127.0.0.1:22015/content/wikipedia_en_all_maxi_2022-05/A/User%3AThe_other_Kiwix_guy/Landing", timeout=15000)
            print("Page loaded successfully!")
            print("Title:", page.title())
        except Exception as e:
            print("Error during navigation:", e)
        
        browser.close()

if __name__ == "__main__":
    test()
