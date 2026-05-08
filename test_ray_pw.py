import ray
import asyncio
import uvloop
from playwright.sync_api import sync_playwright

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
ray.init()

@ray.remote
class PlaywrightActor:
    def test(self):
        print("Calling test in actor...")
        # Force standard asyncio loop to replace uvloop in the worker
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Now try sync_playwright
        try:
            import nest_asyncio
            nest_asyncio.apply()
            print("Starting playwright...")
            p = sync_playwright().start()
            print("Playwright started!")
            b = p.chromium.launch(headless=True)
            print("Browser launched!")
            b.close()
            p.stop()
            return "Success"
        except Exception as e:
            return f"Error: {e}"

actor = PlaywrightActor.remote()
try:
    print("Result:", ray.get(actor.test.remote(), timeout=15))
except Exception as e:
    print("Timed out or error:", e)

ray.shutdown()