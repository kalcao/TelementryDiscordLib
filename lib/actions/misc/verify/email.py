from solver_client import Solver
import uuid
import tls_client

class EmailVerify:
    def __init__(self, client):
        self.client = client
        self.locked = False

    async def add(self, email: str, password: str): # password can be none if unclaimed token
        password = password or self.client.password
        client_heartbeat_session_id = self.client.client_identity['client_heartbeat_session_id']

        self.client.science.add('settings_pane_viewed', external_properties={
            "client_heartbeat_session_id": client_heartbeat_session_id,
            "settings_type": "user",
            "origin_pane": None,
            "destination_pane": "My Account",
            "location_stack": [],
            "source": None,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720
        })
        await self.client.science.submit()
        
        self.client.science.add("impression_modal_root_legacy", {
            "client_heartbeat_session_id": client_heartbeat_session_id,
            "impression_type": "page",
            "variant": "ClaimAccountModal",
            "location": "impression_modal_root_legacy",
            "location_page": "impression_modal_root_legacy",
            "accessibility_features": 524544,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720
        })
        await self.client.science.submit()
        
        add_res = await self.client._make_request("PATCH", f"https://discord.com/api/v9/users/@me", json={"email":email,"password":password})
        if add_res.status_code == 200:
            await self.client.close()
            self.client.token = (add_res.json()['token'])
            self.client.email = email
            self.client.password = password
            await self.client.init()
            await self.client.ws.is_ready.wait()

            return {"success": True, "email": email, "password": password, "new_token": add_res.json()['token'], "res": add_res}
        
        return {"success": False, "email": email, "password": password, "new_token": None, "res": add_res}

    async def verify(self, verifyToken=None, verifyUrl=None):
        if not verifyToken:
            response = await self.client._make_request("GET", verifyUrl)
            verifyToken = response.headers['Location'].split('#token=')[1]

        client_heartbeat_session_id = self.client.client_identity['client_heartbeat_session_id']

        res = await self.client._make_request("POST", "https://discord.com/api/v9/auth/verify", json={"token": verifyToken})

        # Handle captcha if required
        if res.json().get('captcha_sitekey'):
            solver = Solver(
                url="https://discord.com/register",
                sitekey=res.json()['captcha_sitekey'],
                rqdata=res.json()['captcha_rqdata'],
                user_agent=self.client.session.headers['user-agent'],
                proxy=self.client.proxy
            )   
            if self.client.proxy:
                solver.proxy = self.client.proxy

            token, cookie = solver.solve()
            headers = {
                "x-captcha-key": token,
                "x-captcha-rqtoken": res.json()['captcha_rqtoken'],
                "x-captcha-session-id": res.json()['captcha_session_id']
            }
            res = await self.client._make_request("POST", "https://discord.com/api/v9/auth/verify", json={"token": verifyToken}, headers=headers)

        if res.status_code != 200:
            return {"success": False, "verifyToken": verifyToken, "verifyUrl": verifyUrl, "res": res.json()}
        
        new_token = res.json().get("token")
        if new_token:
            return {"success": True, "verifyToken": verifyToken, "verifyUrl": verifyUrl, "new_token": new_token, "res": res.json()}

        return {"success": True, "verifyToken": verifyToken, "verifyUrl": verifyUrl, "res": res.json()}