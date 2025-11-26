import json, base64, uuid, re
import asyncio
import tls_client
from browserforge.fingerprints import FingerprintGenerator
from dataclasses import asdict
from lib.ws import DiscordWS
from lib.actions import ActionsContainer
from lib.science import SciencePayload, Client_UUID

class DiscordClient:
    def __init__(self, token: str, email="", password="", device_prop={"browser": "firefox", "os": "macos", "client_build_number": 459631}, proxy=None):
        self.token, self.device_prop = token, device_prop
        self.proxy = proxy

        self.email = email
        self.password = password

        self.client_identity = {k: str(uuid.uuid4()) for k in ["client_launch_id", "launch_signature", "client_heartbeat_session_id"]}
        self.fingerprint = asdict(FingerprintGenerator().generate(browser=device_prop['browser'], os=device_prop['os']))
        user_agent = self.fingerprint['navigator']['userAgent']
        self.browser_version = (self.fingerprint['navigator']['userAgentData']['brands'][-1]['version']
                                if self.fingerprint['navigator'].get('userAgentData')
                                else re.search(r'Firefox/([\d\.]+)', user_agent) and re.search(r'Firefox/([\d\.]+)', user_agent).group(1) or "0")
        self.session = tls_client.Session(client_identifier="firefox", random_tls_extension_order=True)
        self.session.headers = {**self.fingerprint['headers'], "Authorization": self.token, "x-debug-options": "bugReporterEnabled", 
                        "x-discord-locale": "en-US"}
        
        self.me = self.session.get('https://discord.com/api/v9/users/@me')
        if self.me.status_code != 200:
            raise Exception("Invalid token. -> " + json.dumps(self.me.json()))

        user_info = self.me.json()
        locale = user_info.get('locale', 'en')
        self.session.headers['x-discord-locale'] = locale

        self.properties = {
            "os": device_prop['os'], "browser": device_prop['browser'], "device": "", "system_locale": locale, "has_client_mods": True,
            "browser_user_agent": user_agent, "browser_version": self.browser_version, "os_version": "10", "referrer": "", "referring_domain": "",
            "referrer_current": "", "referring_domain_current": "", "release_channel": "stable", "client_build_number": device_prop['client_build_number'],
            "client_event_source": None, **self.client_identity, "client_app_state": "focused"
        }
        self.session.headers['X-Super-Properties'] = base64.b64encode(json.dumps(self.properties).encode()).decode()

        self.ws = DiscordWS(token, device_prop, self.fingerprint, self.browser_version, self.client_identity, self.properties, client=self)
        self.science = SciencePayload(self)
        
        self.actions = ActionsContainer(self)        
        self._make_request = lambda method, url, **kwargs: asyncio.to_thread(lambda: getattr(self.session, method.lower())(url, headers={**kwargs.pop('headers', {})}, proxy=proxy, **kwargs))

    @property
    def ws_connected(self): return self.ws.ws_connected if self.ws else False
    @property
    def ws_data(self): return getattr(self.ws, 'ws_data', {}) if self.ws else {}

    async def init(self):
        await self.ws.connect()
        await self.ws.connected_event.wait()

    async def send_custom_data(self, data): await self.ws.send_custom_data(data)

    async def close(self):
        if hasattr(self, 'ws') and self.ws:
            await self.ws.close()

    def run(self): import asyncio; asyncio.run(self.init())

def on_message(func):
    func.is_message_handler = True
    return func