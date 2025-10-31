import tls_client, re, json, asyncio, inspect
import hashlib

from time import time
from groq import AsyncGroq
from datetime import datetime

from logger import logger
from hsw import hsw
from motion import motion_data

session = tls_client.Session(client_identifier="firefox_120", random_tls_extension_order=True)

api_js = session.get('https://hcaptcha.com/1/api.js?render=explicit&onload=hcaptchaOnLoad').text
version = re.findall(r'v1\/([A-Za-z0-9]+)\/static', api_js)[0]  # Changed to [0] to avoid index error if only one match

client = AsyncGroq(api_key="put your groq key here")
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
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
}

class hcaptcha:
    def __init__(self, sitekey: str, host: str, proxy: str = None, rqdata: str = None) -> None:
        logger.info(f"Solving for: {sitekey} - {host}")
        self.sitekey = sitekey
        self.host = host.split("//")[-1].split("/")[0]

        self.rqdata = rqdata
        self.motion = motion_data(session.headers["user-agent"], f"https://{host}")

        self.motiondata = self.motion.get_captcha()
        self.answers = {}

    @classmethod
    async def create(cls, sitekey: str, host: str, proxy: str = None, rqdata: str = None):
        self = cls(sitekey, host, proxy, rqdata)
        self.siteconfig = await self.get_siteconfig()
        self.captcha1 = await self.get_captcha1()
        self.captcha2 = await self.get_captcha2()
        return self

    async def get_siteconfig(self) -> dict:
        def _get():
            s = time()
            siteconfig = session.post(f"https://api2.hcaptcha.com/checksiteconfig", params={
                'v': version,
                'sitekey': self.sitekey,
                'host': self.host,
                'sc': '1', 
                'swa': '1', 
                'spst': '1'
            })
            return siteconfig.json()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get)

    async def get_captcha1(self) -> dict:
        s = time()
        n = await hsw(self.siteconfig['c']['req'], self.host, self.sitekey)
        data = {
            'v': version,
            'sitekey': self.sitekey,
            'host': self.host,
            'hl': 'de',
            'motionData': json.dumps(self.motiondata),
            'pdc':  {"s": round(datetime.now().timestamp() * 1000), "n":0, "p":0, "gcs":10},
            'n': n,
            'c': json.dumps(self.siteconfig['c']),
            'pst': False
        }

        if self.rqdata is not None: data['rqdata'] = self.rqdata

        def _post():
            getcaptcha = session.post(f"https://api.hcaptcha.com/getcaptcha/{self.sitekey}", data=data)
            return getcaptcha.json()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _post)
    
    async def get_captcha2(self) -> dict:
        s = time()
        n = await hsw(self.captcha1['c']['req'], self.host, self.sitekey)
        data = {
            'v': version,
            'sitekey': self.sitekey,
            'host': self.host,
            'hl': 'de',
            'a11y_tfe': 'true',
            'action': 'challenge-refresh',
            'old_ekey'  : self.captcha1['key'],
            'extraData': self.captcha1,
            'motionData': json.dumps(self.motiondata),
            'pdc':  {"s": round(datetime.now().timestamp() * 1000), "n":0, "p":0, "gcs":10},
            'n': n,
            'c': json.dumps(self.captcha1['c']),
            'pst': False
        }
        if self.rqdata is not None: data['rqdata'] = self.rqdata

        def _post():
            getcaptcha2 = session.post(f"https://api.hcaptcha.com/getcaptcha/{self.sitekey}", data=data)
            return getcaptcha2.json()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _post)

    async def text(self, task: dict) -> tuple:
        s, q = time(), task["datapoint_text"]["de"]    
        hashed_q = hashlib.sha1(q.encode()).hexdigest() 
        print(q)
        response = await client.chat.completions.create(
            messages=[
                {"role": "user", 
                 "content": f"Srictly respond to the following question with only and only one single word, number, or phrase. Make sure its lowercase:  Question: {q}"}
                 ],
                 model="moonshotai/kimi-k2-instruct-0905",
                 temperature=0.95,
                 max_tokens=128,
        )
    
        
        if response:
            response = response.choices[0].message.content
            self.answers[hashed_q] = response
            print(response)
            return task['task_key'], {'text': response}
        
        return "ja"

    async def solve(self) -> str:
        s = time()
        try:
            cap = self.captcha2
            results = await asyncio.gather(*(self.text(task) for task in cap['tasklist']))
            answers = {key: value for key, value in results}
            n = await hsw(cap['c']['req'], self.host, self.sitekey)

            def _submit():
                submit = session.post(
                    f"https://api.hcaptcha.com/checkcaptcha/{self.sitekey}/{cap['key']}",
                    json={
                        'answers': answers,
                        'c': json.dumps(cap['c']),
                        'job_mode': cap['request_type'],
                        'motionData': json.dumps(self.motion.check_captcha()),
                        'n': n,
                        'serverdomain': self.host,
                        'sitekey': self.sitekey,
                        'v': version,
                    })
                return submit

            loop = asyncio.get_running_loop()
            submit = await loop.run_in_executor(None, _submit)
            if 'UUID' in submit.text:
                logger.info(f"Solved hCaptcha {submit.json()['generated_pass_UUID'][:150]}..")
                return submit.json()['generated_pass_UUID']
            
            logger.critical(f"Failed To Solve hCaptcha")
            return None
        except Exception as e:
            line = inspect.currentframe().f_back.f_lineno
            logger.critical(f"Error at line {line}: {e}")
