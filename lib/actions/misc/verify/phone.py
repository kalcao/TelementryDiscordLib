from solver_client import Solver
import uuid
import tls_client

class PhoneVerify:
    def __init__(self, client):
        self.client = client
        self.locked = False

    async def add(self, phone_number: str):
        client_heartbeat_session_id = self.client.client_identity['client_heartbeat_session_id']
        phone_number = "+"+phone_number
        locked_res = (await self.client._make_request("GET", "https://discord.com/api/v9/content-inventory/users/@me?for_game_profile=false&feature=inbox")).status_code
        if locked_res == 403: self.locked = True 
        else: self.locked = False

        add_res = await self.client._make_request("POST", f"https://discord.com/api/v9/users/@me/phone", json={
            "phone":phone_number,
            "change_phone_reason":"user_action_required" if self.locked else "user_settings_update"
        })
        print(add_res)
        if add_res.status_code == 204:
            return {"success": True, "phone": phone_number, "res": add_res}
        

        self.client.science.add('open_modal', external_properties={
            "type": "Guild Join Captcha",
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720
        })

        self.client.science.add('open_modal', external_properties={
            "type": "Captcha Modal",
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720
        })

        self.client.science.add('captcha_event', external_properties={
            "captcha_event_name": "initial-load",
            "captcha_service": "hcaptcha",
            "sitekey": add_res.json().get("captcha_sitekey"),
            "captcha_flow_key": str(uuid.uuid4()),
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720
        })

        await self.client.science.submit()
        print(self.client.proxy)
        solver = Solver(
            url="https://discord.com/channels/@me",
            sitekey=add_res.json().get("captcha_sitekey"),
            rqdata=add_res.json().get("captcha_rqdata"),
            user_agent=self.client.properties["browser_user_agent"],
            proxy=self.client.proxy if self.client.proxy else None
        )
        token, cookikes = solver.solve()
        
        add_res = await self.client._make_request("POST", f"https://discord.com/api/v9/users/@me/phone", json={
            "phone": phone_number,
            "change_phone_reason": "user_action_required" if self.locked else "user_settings_update"
        }, headers={
            'X-Captcha-Key': token,
            "X-Captcha-Rqtoken": add_res.json().get("captcha_rqtoken"),
            'X-Captcha-Session-Id': add_res.json().get("captcha_session_id")
        })
        print(add_res.status_code)
        print(add_res.text)
        if(add_res.status_code != 204): 
            return {"success": False, "phone": phone_number, "res": add_res.json()}
        
        return {"success": True, "phone": phone_number, "res": add_res}
    async def verify(self, phone_number: str, code: str, password: str):
        phone_number = "+"+phone_number
        client_heartbeat_session_id = self.client.client_identity['client_heartbeat_session_id']

        verify_token_res = await self.client._make_request("POST", "https://discord.com/api/v9/phone-verifications/verify", json={
            "phone":phone_number,
            "code":code
        })
        
        if verify_token_res.status_code != 200:
            return {"success": False, "phone": phone_number, "code": code, "res": verify_token_res.json()}
        
        verify_token = verify_token_res.json()['token']

        self.client.science.add("network_action_user_verify_phone", {
            "client_heartbeat_session_id": client_heartbeat_session_id,
            "status_code": verify_token_res.status_code,
            "url": "/phone-verifications/verify",
            "request_method": "post",
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "client_rtc_state": "DISCONNECTED",
            "client_app_state": "focused",
            "client_viewport_width": 1280,
            "client_viewport_height": 720,
        })
        await self.client.science.submit()

        final_phone_res = await self.client._make_request("POST", "https://discord.com/api/v9/users/@me/phone", json={
            "phone_token": verify_token,
            "password": password,
            "change_phone_reason": "user_action_required" if self.locked else "user_settings_update"
        })

        if final_phone_res.status_code != 204:
            return {"success": False, "phone": phone_number, "code": code, "password": password, "res": final_phone_res.json()}
    

        return {"success": True, "phone": phone_number, "code": code, "password": password, "res": None}