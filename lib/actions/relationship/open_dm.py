import json, uuid, base64, asyncio, time
import requests
from lib.science import SciencePayload

class OpenChannel:
    def __init__(self, client):
        self.client = client
        self.science = client.science

    async def open_dm(self, user_id: str):
        """
        Opens a direct message channel with a user
        """
        profile_session_id = str(uuid.uuid4())
        await self.client.ws.is_ready.wait()
        
        popup_res = await self.client._make_request(
            "GET",
            f"https://discord.com/api/v9/users/{user_id}/profile?type=modal&with_mutual_guilds=True&with_mutual_friends=False&with_mutual_friends_count=True",
        )
        popup_data = popup_res.json()
        profile_badges = []
        for badge in popup_data.get("badges", []):
            profile_badges.append(badge.get("id"))

        user_profile_action = {}
        try:
            user_profile_action["avatar_decoration_sku_id"] = popup_data["user"]["avatar_decoration_data"]["sku_id"]
        except: pass

        self.science.add('dm_list_viewed', external_properties={
            "num_users_visible": 1,
            "num_users_visible_with_mobile_indicator": 0,
            "guild_id": "1433177992208584784",
            "guild_size_total": 57,
            "guild_num_channels": 2,
            "guild_num_text_channels": 1,
            "guild_num_voice_channels": 1,
            "guild_num_roles": 1,
            "guild_member_num_roles": 0,
            "guild_member_perms": "2248473465835073",
            "guild_is_vip": False,
            "is_member": True,
            "num_voice_channels_active": 0,
            "channel_id": "1433177992871411895",
            "channel_type": 0,
            "channel_size_total": 0,
            "channel_member_perms": "2248473465835073",
            "channel_hidden": False,
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "rendered_locale": "pt-BR",
            "accessibility_support_enabled": False
        })

        self.science.add('channel_opened', external_properties={
            "channel_is_nsfw": False,
            "can_send_message": False,
            "channel_id": "1437826441520615535",
            "channel_type": 1,
            "channel_size_total": 1,
            "channel_member_perms": "0",
            "channel_hidden": False,
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "accessibility_support_enabled": False
        })

        self.science.add('dismissible_content_shown', external_properties={
            "type": "NAGBAR_NOTICE_DOWNLOAD",
            "content_count": 0,
            "fatigable_content_count": 0,
            "bypass_fatigue": False,
            "guild_id": None,
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "accessibility_support_enabled": False
        })

        await self.science.submit()

        self.science.add('open_modal', external_properties={
            "type": "Guild Join Captcha",
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "rendered_locale": "pt-BR",
            "accessibility_support_enabled": False
        })

        await self.science.submit()
        res = await self.client._make_request("POST", 'https://discord.com/api/v9/users/@me/channels', 
                                            json={"recipient_id": user_id})

        return res.json()
