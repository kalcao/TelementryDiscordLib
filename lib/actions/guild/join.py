import json, uuid
import asyncio, base64
from urllib.parse import quote
import requests  # 추가: Flask 서버에 요청하기 위해
from lib.science import SciencePayload

class JoinHandler:
    def __init__(self, client):
        self.client = client

    async def join_guild(self, invite_code: str):
        await self.client.ws.is_ready.wait()
        science = self.client.science
        if science.analytics_token is not None:
            science.reset()
            await science.submit()

            science.add('impression_guild_add_landing', external_properties={
                "impression_type": "modal",
                "impression_group": "guild_add_flow",
                "location_section": "impression_guild_add_landing",
                "location_stack": [],
                "client_viewport_width": 1280,
                "client_viewport_height": 720
            })
            science.add('impression_modal_root_legacy', external_properties={
                'impression_type': 'page',
                'variant': 'CreateGuildModal',
                "location":"impression_modal_root_legacy",
                "location_page":"impression_modal_root_legacy",
                "location_section":"impression_guild_add_landing",
                "client_app_state":"focused",
                "client_viewport_width": 1280,
                "client_viewport_height": 720,
            })
            science.add('nuo_transition', external_properties={
                "flow_type":"create_guild",
                "from_step":"join_guild",
                "to_step":"guild_templates",
                "seconds_on_from_step":0,
                "client_viewport_width": 1280,
                "client_viewport_height": 720,
            })
            science.add('open_modal', external_properties={
                "type":"Create Guild Templates",
                "location":"Guild List",
                "client_viewport_width": 1280,
                "client_viewport_height": 720
            })
            await science.submit()

            science.reset()
            await science.submit()

            science.add('impression_guild_add_join', external_properties={
                "impression_type": "modal",
                "impression_group": "guild_add_flow",
                "location_stack": [],
                "location_section": "impression_guild_add_join",
                "client_performance_memory": 0,
                "accessibility_features": 524544,
                "rendered_locale": science.locale,
                "uptime_app": 4,
                "client_rtc_state": "DISCONNECTED",
                "client_app_state": "focused",
                "client_viewport_width": 1280,
                "client_viewport_height": 720
            })

            science.add('nuo_transition', external_properties={
                "flow_type": "create_guild",
                "from_step": "guild_templates",
                "to_step": "join_guild",
                "seconds_on_from_step": 0.641,
                "client_performance_memory": 0,
                "accessibility_features": 524544,
                "rendered_locale": science.locale,
                "uptime_app": 4,
                "client_rtc_state": "DISCONNECTED",
                "client_app_state": "focused",
                "client_viewport_width": 1280,
                "client_viewport_height": 720
            })

            science.add('open_modal', external_properties={
                "type": "Join Guild",
                "location": "Guild List",
                "client_performance_memory": 0,
                "accessibility_features": 524544,
                "rendered_locale": science.locale,
                "uptime_app": 4,
                "client_rtc_state": "DISCONNECTED",
                "client_app_state": "focused",
                "client_viewport_width": 1280,
                "client_viewport_height": 720
            })

            await science.submit()
        else:
            print("missing analytics token")

        payload = {
            'session_id': self.client.ws.ws_data['session_id']
        }
        science.add('invite_opened', external_properties={
                "invite_code": invite_code,
                "client_performance_memory": 0,
                "client_rtc_state": "DISCONNECTED",
                "client_app_state": "focused",
            })
        guild_info_res = await self.client._make_request("GET", f'https://discord.com/api/v9/invites/{invite_code}?inputValue={invite_code}&with_counts=true&with_expiration=true&with_permissions=true')
        guild_info = guild_info_res.json()
        print(guild_info)
        context_properties = {
            "location": "Join Guild",
            "location_guild_id": guild_info["guild"]["id"] if "guild" in guild_info else guild_info["guild_id"],
            "location_channel_id": guild_info["channel"]["id"],
            "location_channel_type": 0
        }
        context_properties_b64 = base64.b64encode(json.dumps(context_properties).encode()).decode()
        
        res = await self.client._make_request("POST", f'https://discord.com/api/v9/invites/{invite_code}', json=payload, headers={'X-Context-Properties': context_properties_b64})
        res_text = res.text
        print(res_text)
        
        try:
            data = json.loads(res_text)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid response", "invite_code": invite_code}
        
        if "captcha_key" in data:
            science.add('open_modal', external_properties={
                "type": "Guild Join Captcha"
            })
            science.add('captcha_modal', external_properties={
                "type": "Captcha Modal"
            })

            captcha_sitekey = data.get("captcha_sitekey")
            captcha_rqdata = data.get("captcha_rqdata")
            captcha_rqtoken = data.get("captcha_rqtoken")
            captcha_session_id = data.get("captcha_session_id")
            
            if not all([captcha_sitekey, captcha_rqdata, captcha_rqtoken, captcha_session_id]):
                return {"success": False, "error": "Missing captcha fields", "invite_code": invite_code}
            
            science.add('captcha_event', external_properties={
                "captcha_event_name": "initial-load",
                'captcha_flow_key': uuid.uuid4().hex,
                'captcha_service': 'hcaptcha'
            })
            await science.submit()

            params = {
                "url": "https://discord.com/app",
                "sitekey": captcha_sitekey,
                "rqdata": captcha_rqdata,
                'user_agent': self.client.session.headers['User-Agent']
            }
            if self.client.proxy:
                params['proxy'] = self.client.proxy

            response = requests.get("http://localhost:5001/solve", params=params)
            if response.status_code != 200:
                return {"success": False, "error": "Failed to start solver task", "invite_code": invite_code}
            
            task_data = response.json()
            taskid = task_data.get("taskid")
            if not taskid:
                return {"success": False, "error": "No task ID returned", "invite_code": invite_code}
            
            max_attempts = 60
            attempt = 0
            token = None
            while attempt < max_attempts:
                await asyncio.sleep(1)
                status_res = requests.get(f"http://localhost:5001/task/{taskid}")
                status_data = status_res.json()
                if status_data.get("status") == "success":
                    token = status_data.get("uuid")
                    break
                elif status_data.get("status") == "failed":
                    return {"success": False, "error": "Solver failed", "invite_code": invite_code}
                attempt += 1
            
            if not token:
                return {"success": False, "error": "Failed to solve captcha", "invite_code": invite_code}
            
            context_properties = {
                "location": "Join Guild",
                "location_guild_id": guild_info["guild"]["id"] if "guild" in guild_info else guild_info["guild_id"],
                "location_channel_id": guild_info["channel"]["id"],
                "location_channel_type": 0
            }
            context_properties_b64 = base64.b64encode(json.dumps(context_properties).encode()).decode()
            
            retry_res = await self.client._make_request(
                "POST",
                f'https://discord.com/api/v9/invites/{invite_code}',
                json=payload,
                headers={'X-Context-Properties': context_properties_b64,
                     'X-Captcha-Key': token,
                     'X-Captcha-Rqdata': captcha_rqdata,
                     'X-Captcha-Rqtoken': captcha_rqtoken,
                     'X-Captcha-Session-Id': captcha_session_id
                 }
            )
            retry_text = retry_res.text
                        
            try:
                retry_data = json.loads(retry_text)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid retry response", "invite_code": invite_code}
            
            if retry_res.status_code == 200:
                return {"success": True, "invite_code": invite_code}
            else:
                return {"success": False, "error": retry_data, "invite_code": invite_code}
        

        if res.status_code == 200:
            return {"success": True, "invite_code": invite_code}
        else:
            return {"success": False, "error": data, "invite_code": invite_code}
