import json, uuid, base64, asyncio, time
from lib.science import SciencePayload
from solver import hcaptcha
from lib.science import SciencePayload
from datetime import datetime

class ProfileChanger:
    def __init__(self, client):
        self.client = client
    
    async def change_profile(self, avatar=None, global_name=None, bio=None, pronouns=None, accent_color=None):
        science = SciencePayload(self.client.ws)
        # Prepare the payload for profile update
        at_me = {}
        profile = {}
        if avatar is not None:
            at_me['avatar'] = f"data:image/png;base64,{avatar}"
            at_me['avatar_description'] =  datetime.now().strftime("%B %d, %Y at %I:%M %p")
        if global_name is not None:
            at_me['global_name'] = global_name

        if bio is not None:
            profile['bio'] = bio
        if pronouns is not None:
            profile['pronouns'] = pronouns
        if accent_color is not None:
            profile['accent_color'] = accent_color
            
        science.events['events'] = []
        client_ad_session_id = str(uuid.uuid4())
        heartbeat_init_ts = int(time.time() * 1000)
        science.add('premium_upsell_viewed', external_properties={
            "type": "collectibles_profile_settings_upsell",
            "location_stack": [
                "user settings",
                "user settings user profile",
                "collectibles profile settings upsell"
            ],
            "version": 46
        })
        science.add('premium_feature_try_out', external_properties={
            "feature_name": "preset",
            "feature_tier": "premium-standard"
        })
        science.add('settings_pane_viewed', external_properties={
            "settings_type": "user",
            "origin_pane": "My Account",
            "destination_pane": "Profile Customization",
            "location_stack": [],
            "source": None
        })
        science.add('client_ad_heartbeat', external_properties={
            "client_ad_session_id": client_ad_session_id,
            "client_heartbeat_initialization_timestamp": heartbeat_init_ts,
            "client_heartbeat_version": 2
        })
        science.add('impression_modal_root_legacy', external_properties={
            "impression_type": "page",
            "variant": "SelectImageModal",
            "location": "impression_modal_root_legacy",
            "location_page": "impression_modal_root_legacy"
        })
        science.add('premium_upsell_viewed', external_properties={
            "type": "Upload File or Choose GIF Modal",
            "location_stack": [
                "select image modal"
            ]
        })
        science.add('open_modal', external_properties={
            "type": "Upload File or Choose GIF Modal",
            "location_stack": [
                "select image modal"
            ],
            "upload_type": "AVATAR"
        })
        # science.add('dismissible_content_shown', external_properties={
        #     "type": "BOGO_2025_NITRO_TAB_BADGE",
        #     "content_count": 1,
        #     "fatigable_content_count": 0,
        #     "bypass_fatigue": True,
        #     "guild_id": None
        # })
        # science.add('dismissible_content_shown', external_properties={
        #     "type": "FAMILY_CENTER_NEW_BADGE",
        #     "content_count": 2,
        #     "fatigable_content_count": 0,
        #     "bypass_fatigue": True,
        #     "guild_id": None
        # })
        # science.add('safety_hub_viewed', external_properties={
        #     "account_standing": 100
        # })
        science.add('settings_pane_viewed', external_properties={
            "settings_type": "user",
            "origin_pane": None,
            "destination_pane": "My Account",
            "location_stack": [],
            "source": None,
            "subsection": "PRIVACY_AND_SAFETY_STANDING"
        })
        science.add('premium_upsell_viewed', external_properties={
            "type": "premium_profile_try_it_out",
            "location_stack": [
                "user settings",
                "user settings user profile"
            ],
            "location": "User Settings",
            "location_page": "User Settings"
        })
        if avatar is not None:
            science.add('user_avatar_updated', external_properties={
                "animated": False,
                "is_guild_profile": False,
                "is_edited_recent_avatar": False
            })


        await science.submit()

        print(at_me)
        at_me_res = await self.client._make_request("PATCH", 'https://discord.com/api/v9/users/@me', json=at_me)
        profile_res = await self.client._make_request("PATCH", 'https://discord.com/api/v9/users/@me/profile', json=profile)

        try:
            at_me_json = at_me_res.json()
        except:
            at_me_json = {"error": "Could not parse response"}
        
        try:
            profile_res_json = profile_res.json()
        except:
            profile_res_json = {"error": "Could not parse response"}

        return {'users/@me': {'status_code': at_me_res.status_code, 'res': at_me_json}, 'users/@me/profile': {'status_code': profile_res.status_code, 'res': profile_res_json}}