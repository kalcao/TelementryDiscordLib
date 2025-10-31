import tls_client, re, jwt, asyncio

from flask import Flask, request

from playwright.async_api import async_playwright

session = tls_client.Session(client_identifier="firefox_120", random_tls_extension_order=True)

session.headers = {
    'accept': '*/*',
    'accept-language': 'de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'referer': 'https://discord.com/',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'script',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
}

params = {
    'render': 'explicit',
    'onload': 'hcaptchaOnLoad',
    'recaptchacompat': 'off',
}


async def hsw(req: str, site: str, sitekey: str) -> str:
    pw = await async_playwright().start()
    browser = await pw.chromium.launch()
    page = await browser.new_page()
    await page.route(f"https://{site}/", lambda r: r.fulfill(status=200, content_type="text/html",))
    await page.goto(f"https://{site}/")

    await page.wait_for_load_state('domcontentloaded')


    js = session.get('https://js.hcaptcha.com/1/api.js', params=params).text

    version = re.findall(r'v1\/([A-Za-z0-9]+)\/static', js)[1]

    token = session.post('https://api2.hcaptcha.com/checksiteconfig', params={
        'v': version,
        'host': f'{site}',
        'sitekey': f'{sitekey}',
        'sc': '1',
        'swa': '1',
        'spst': 's',
    }).json()["c"]["req"]

    url: str = "https://newassets.hcaptcha.com" + jwt.decode(token, options={"verify_signature": False})["l"] + "/hsw.js"

    version = url.split("/c/")[1].split("/")[0]

    hsw_js = session.get(f"{url}").text
    await page.add_script_tag(content="Object.defineProperty(navigator, \"webdriver\", {\"get\": () => false})")
    await page.add_script_tag(content=hsw_js)

    result = await page.evaluate(f"hsw('{req}')")

    await browser.close()
    return result
