import asyncio
import random, string
import requests
from flask import Flask, request
import threading
import platform
import time
from camoufox.async_api import AsyncCamoufox
# from playwright.async_api import async_playwright
# from playwright_stealth import stealth_async

tasks = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>hCaptcha Example</title>
  <script src="https://js.hcaptcha.com/1/api.js?onload=hcaptchaOnLoad" async defer></script>
</head>
<body>
  <div class="h-captcha" data-sitekey="사이트키"></div>
</body>
</html>
"""

# async def randomized_type(selector, text):
#     for char in text:
#         await asyncio.sleep(random.randint(50, 200) / 1000)
#         await selector.press_sequentially(char)

async def ask(direction, query):
    try:
        print(direction)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer api_key_here',
        }
        json_data = {
            'messages': [
                {
                    'role': 'user',
                    'content': f'"Only Strictly respond with "네", "아니요" with no any explanation: "{query}"'
                },
            ],
            # 'model': 'qwen/qwen3-32b',
            'model': 'moonshotai/kimi-k2-instruct-0905',
            'temperature': 1,
            'max_completion_tokens': 7168,
            'top_p': 1,
            'stream': False,
            'stop': None,
        }
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=json_data)
        try:
            return response.json()['choices'][0]["message"]["content"].replace(".","")
        except: return "아니요"
    except Exception as e: print(response.json())
    # trans = requests.get(f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&dj=1&source=input&q={query}').json()['sentences'][0]['trans']

    # response = requests.post("http://localhost:11434/api/chat", json={
    #     "model": "qwen3:4b-instruct-2507-q4_K_M",
    #     "messages": [
    #         {"role": "user", "content": f"Strictly only respond with \"yes\" or \"no\" to the given question: \"{trans}\""}
    #     ],
    #     "stream": False
    # })
    # ans = response.json()['message']['content']

    # response = requests.post("http://localhost:1234/v1/chat/completions", headers={ "Content-Type": "application/json" }, json={

    #         "model": "liquid/lfm2-1.2b",
    #         "messages": [
    #             {"role": "user", "content": f"*Strictly ONLY* respond in \"yes\" or \"no\" to the given question precisly: \"{trans}\""}
    #         ],
    #         "temperature": 0
    #     })
    # ans = response.json()['choices'][0]['message']['content']
    if "yes" in ans.lower(): # ?_?
        return "네" # 메가가 짱짱일경우 메가가 짱짱입니까?
    elif "no" in ans.lower():
        return '아니요' #메가가 좆밥일경우
    else:
        return "아니요"#메가가 좆밥일경우

async def monitor_token(page, taskid, browser, context):
    while True:
        try:
            token = await page.evaluate('() => document.querySelector("iframe[data-hcaptcha-response]")?.getAttribute("data-hcaptcha-response")')
            if token and "_" in token:
                cookies = await context.cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                tasks[taskid] = {"status": "success", "uuid": token, "cookies": cookie_dict}
                print(f"{token[:50]}...")
                try:
                    await browser.close()
                    print(f"Browser closed for task {taskid}")
                except Exception as e:
                    print(f"Error closing browser for task {taskid}: {e}")
                return token
        except Exception as e:
            print(f"Error in monitor_token: {e}")
        await asyncio.sleep(1)

async def solve_hcaptcha_async(taskid, sitekey, url, user_agent = None, rqdata = None, proxy_config=None):
    print(f"{taskid}: {url}")
    start_time = time.time()
    browser = None
    
    try:
        print(f"init: {taskid}")
        browser_config = {
            "headless": False,
            "humanize": False,
            "block_webrtc": False,
            "geoip":True,
            "os": "macos"
        }
        if proxy_config:
            browser_config["proxy"] = proxy_config
            print(f"Using proxy for task {taskid}: {proxy_config['server']}")

        browser = await AsyncCamoufox(**browser_config).start()

        # playwright = await async_playwright().start()
        # browser = await playwright.chromium.launch(headless=False)

        print(f"Browser started for task {taskid}")
        if user_agent: context = await browser.new_context(locale='ko-KR', user_agent=user_agent.replace("%20", " "))
        else: context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()
        # await stealth_async(page)
        async def template_route(route):
            await route.fulfill(
                status=200,
                content_type='text/html',
                body=HTML_TEMPLATE.replace("사이트키", sitekey)
            )

        async def hcaptcha_html_route(route):
            hcap_html = open("hcaptcha.html", "r", encoding="utf-8").read()
            if(rqdata):
                hcap_html = hcap_html.replace("Zr = t", f'Zr = "{rqdata}"')
            await route.fulfill(
                status=200,
                content_type='text/html',
                body=hcap_html
            )
        async def apijs_route(route):
            hcap_html = open("api.js", "r", encoding="utf-8").read()
            await route.fulfill(
                status=200,
                content_type='application/javascript',
                body=hcap_html
            )
        await page.route(url, template_route)
        await page.route("**/static/hcaptcha.html", hcaptcha_html_route)
        await page.route("**/api.js**", apijs_route)

        await page.goto(url, wait_until="commit")
        await asyncio.sleep(2)
        
        iframe = await page.query_selector("body > div.h-captcha > iframe")
        if not iframe:
            input()
            raise ValueError("hCaptcha iframe not found")
        frame = await iframe.content_frame()
        
        await frame.locator("#checkbox").click()
        
        token_task = asyncio.create_task(monitor_token(page, taskid, browser, context))
        
        try:
            puzzle_element = await page.query_selector("body > div:nth-child(2) > div:nth-child(1) > iframe")
            if puzzle_element:
                puzzle_ifr = await puzzle_element.content_frame()
                await puzzle_ifr.locator("#menu-info").click()
                await puzzle_ifr.locator("#text_challenge").click()
                
                last_q = ""
                attempts = 0
                while attempts < 30:
                    try:
                        direction = await puzzle_ifr.locator(".prompt-text > span:nth-child(1)").text_content()
                        q = await puzzle_ifr.locator("#prompt-text > span").text_content()
                        if last_q != q:
                            last_q = q
                            a = await ask(direction, q)
                            await puzzle_ifr.locator("body > div > div.challenge-container > div > div > div.challenge-input > input").click()
                            await puzzle_ifr.type("body > div > div.challenge-container > div > div > div.challenge-input > input", a)
                            await puzzle_ifr.locator(".button-submit").click()
                        else: 
                            await page.wait_for_timeout(500)
                        attempts += 1
                    except Exception as e:
                        if "Target page, context or browser" in str(e):
                            return
                        else:
                            print(f"Puzzle loop error for task {taskid}: {e}")
                            attempts += 1
                            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Puzzle setup error for task {taskid}: {e}")

        try:
            uuid_result = await asyncio.wait_for(token_task, timeout=120)
        except asyncio.TimeoutError:
            print(f"timeout {taskid}")
            tasks[taskid] = {"status": "error", "uuid": None, "cookies": {}}
            uuid_result = None

    except Exception as e:
        print(f"Error in solve_hcaptcha_async for task {taskid}: {e}")
        import traceback
        traceback.print_exc()
        tasks[taskid] = {"status": "error", "uuid": None, "cookies": {}}
        uuid_result = None
    finally:
        if browser and tasks[taskid]["status"] != "success":
            try:
                await browser.close()
                print(f"Browser closed for task {taskid} (cleanup)")
            except Exception as e:
                print(f"Error closing browser for task {taskid}: {e}")
    
    duration = time.time() - start_time
    print(f"✓ Solving completed. Task ID: {taskid}, UUID: {uuid_result is not None}, Duration: {duration:.2f}s")
    return uuid_result, duration

app = Flask(__name__)
loop = None

def run_event_loop():
    global loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except Exception as e:
        print(f"Error in event loop: {e}")

threading.Thread(target=run_event_loop, daemon=True).start()

@app.route('/solve', methods=['GET'])
def solve():
    url = request.args.get('url')
    if not url:
        return {"error": "URL parameter is required"}, 400
    
    proxy_config = None
    srv = request.args.get('srv')
    usr = request.args.get('usr')
    pw = request.args.get('pw')
    user_agent = request.args.get("user_agent")
    rqdata = request.args.get("rqdata").replace(" ","+")
    sitekey = request.args.get("sitekey").replace(" ","+")
    
    if srv:
        proxy_config = {"server": f"http://{srv}"}
        if usr and pw:
            proxy_config["username"] = usr
            proxy_config["password"] = pw
    
    taskid = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
    tasks[taskid] = {"status": "not_ready", "uuid": None, "cookies": {}}
    
    max_wait = 50
    wait_count = 0
    while (loop is None or not loop.is_running()) and wait_count < max_wait:
        print("Waiting for event loop to start")
        time.sleep(0.1)
        wait_count += 1
    
    if loop is None or not loop.is_running():
        print(f"Event loop failed to start for task {taskid}")
        tasks[taskid] = {"status": "error", "uuid": None, "cookies": {}}
        return {"taskid": taskid, "error": "Event loop not available"}
    
    try:
        asyncio.run_coroutine_threadsafe(solve_hcaptcha_async(taskid, sitekey, url, rqdata=rqdata, user_agent=user_agent, proxy_config=proxy_config), loop)
    except Exception as e:
        print(f"Error scheduling task {taskid}: {e}")
        tasks[taskid] = {"status": "error", "uuid": None, "cookies": {}}
    return {"taskid": taskid}

@app.route('/task/<taskid>', methods=['GET'])
def check_task(taskid):
    return tasks.get(taskid, {"status": "not_found", "uuid": None, "cookies": {}})

def run_flask():
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(run_flask())
    else:
        run_flask()