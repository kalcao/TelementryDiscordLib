import json, uuid, base64, asyncio, time
from lib.science import SciencePayload
from solver import hcaptcha

class AddFriend:
    def __init__(self, client):
        self.client = client
    
    async def add(self, username):
        await self.client.ws.is_ready.wait()
        context = base64.b64encode('{"location":"User Profile"}'.encode()).decode()
        science = self.client.science
        science.reset()

        private_channels = self.client.ws.ws_data.get('private_channels', [])
        visible_user_ids = []
        for channel in private_channels:
            for recipient in channel.get('recipients', []):
                user_id = recipient.get('id')
                if user_id and user_id not in visible_user_ids:
                    visible_user_ids.append(user_id)
        num_users_visible = len(visible_user_ids)

        client_ad_session_id = str(uuid.uuid4())
        heartbeat_init_ts = int(time.time() * 1000)

        science.add('open_modal', external_properties={
                    "accessibility_features": 524544,
                    "accessibility_support_enabled": False,
                    "application_id": None,
                    "client_performance_memory": 0,
                    "game_platform": None,
                    "guild_id": None,
                    "has_images": False,
                    "is_friend": False,
                    "location_object": "Context Menu",
                    "other_user_id": "1056074845974188154",
                    "party_platform": None,
                    "profile_has_nitro_customization": False,
                    "profile_user_status": "online-desktop",
                    "sku_id": None,
                    "type": "Profile Modal",
                    "location_stack": [
                        "uri scheme",
                        "user profile modal v2"
                    ],
        })
        await science.submit()

        res = await self.client._make_request("PUT", 'https://discord.com/api/v9/users/@me/relationships/'+username, json={},headers={"X-Context-Properties": context})
        res_json = res.json()
        print(res_json)
        if "captcha_key" in res_json:
            science.events['events'] = []  # Reset for captcha events

            science.add('open_modal', external_properties={
                "type": "Guild Join Captcha"
            })
            await science.submit()

            captcha_sitekey = res_json.get("captcha_sitekey")
            captcha_rqdata = res_json.get("captcha_rqdata")
            captcha_rqtoken = res_json.get("captcha_rqtoken")
            captcha_session_id = res_json.get("captcha_session_id")
            
            if not all([captcha_sitekey, captcha_rqdata, captcha_rqtoken, captcha_session_id]):
                return {"success": False, "error": "Missing captcha fields"}
            
            science.add('captcha_event', external_properties={
                "captcha_event_name": "initial-load",
                "captcha_service": "hcaptcha",
                "sitekey": captcha_sitekey,
                "captcha_flow_key": str(uuid.uuid4())
            })
            await science.submit()
            solver = await hcaptcha.create(captcha_sitekey, "discord.com", "http://127.0.0.1:9080", captcha_rqdata)
            token = await solver.solve()
            
            if not token:
                return {"success": False, "error": "Failed to solve captcha"}
            
            # Retry join with captcha headers
            self.client.session.headers.update({
                'X-Captcha-Key': token,
                'X-Captcha-Rqdata': captcha_rqdata,
                'X-Captcha-Rqtoken': captcha_rqtoken,
                'X-Captcha-Session-Id': captcha_session_id,
            })
            
            retry_res = await self.client._make_request(
                'PUT',
                f'https://discord.com/api/v9/users/@me/relationships/'+ username,
                json={},
                headers={"X-Context-Properties": context}
            )
            retry_text = retry_res.text
            print(retry_text)
            
            try:
                retry_data = json.loads(retry_text)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid retry response"}
            
            if retry_res.status_code == 204:
                return {"success": True}
            else:
                return {"success": False, "error": retry_data}
        
        if res.status_code == 204:
            return {"success": True}
        else:
            return {"success": False, "error": res_json}