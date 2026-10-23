"""Run against the actual exports. Requires Playwright and local Chromium."""
import functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
url=f'http://127.0.0.1:{server.server_port}/'
results={}
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1280,'height':1100},device_scale_factor=1)
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url)
        page.wait_for_function('document.querySelector("video")?.currentTime > 0.15')
        assert page.locator('video').evaluate('(v) => !v.loop && v.muted && v.playsInline')
        assert page.locator('#asset img').evaluate('(i) => getComputedStyle(i).visibility === "hidden"')
        page.screenshot(path=str(ROOT/'exports/browser-desktop.png'))
        page.wait_for_function('!document.querySelector("video")',timeout=12000)
        assert page.locator('#asset img').evaluate('(i) => i.complete && i.naturalWidth === 768 && getComputedStyle(i).visibility === "visible"')
        results['chromium_playback_completed']=True
        page.wait_for_timeout(250)
        assert page.locator('video').count()==0
        page.locator('#replay').click()
        page.wait_for_function('document.querySelector("video")?.currentTime > 0.1')
        results['explicit_replay']=True
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_function('!document.querySelector("video")')
        results['live_reduced_motion_change']=True
        mobile=browser.new_page(viewport={'width':360,'height':800},reduced_motion='reduce',device_scale_factor=1)
        mobile.goto(url); mobile.wait_for_function('document.querySelector("#asset img")?.complete')
        assert mobile.locator('video').count()==0
        assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
        box=mobile.locator('#asset').bounding_box(); assert abs(box['height']/box['width']-4/3)<.01
        mobile.screenshot(path=str(ROOT/'exports/browser-mobile-reduced-motion.png'),full_page=True)
        results['mobile_reduced_motion_still_and_reserved_layout']=True
        page.emulate_media(reduced_motion='no-preference'); page.reload()
        page.wait_for_function('document.querySelector("video")?.currentTime > 0.1')
        # Simulate ordinary DOM updates outside the mounted player.
        page.locator('h1').evaluate('(h) => h.textContent = "Preview updated"')
        assert page.locator('video').evaluate('(v) => v.currentTime > 0')
        assert not errors, errors
        failed=browser.new_page()
        failures=[]
        def block(route):
            failures.append(route.request.url)
            route.abort()
        failed.route('**/*.webm',block); failed.route('**/*.mp4',block)
        failed.goto(url)
        failed.wait_for_function('!document.querySelector("video") && document.querySelector("#asset img")?.complete')
        assert failures, 'Failure test must attempt a video request'
        assert failed.locator('#asset img').evaluate('(i) => getComputedStyle(i).visibility === "visible" && i.naturalWidth === 768')
        results['failed_video_uses_still']=True
        results['page_errors']=errors
        browser.close()
finally:
    server.shutdown()
(ROOT/'exports/browser-validation.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
