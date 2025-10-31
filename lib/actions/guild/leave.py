import json, uuid
import asyncio, base64
from urllib.parse import quote
from solver import hcaptcha
from lib.science import SciencePayload

class Leave:
    def __init__(self, client):
        self.client = client

    async def leave_guild(self, guild_id): # no need science
        res = await self.client._make_request('DELETE', f'https://discord.com/api/v9/users/@me/guilds/{str(guild_id)}', json={"lurking": False})
        if res.status_code == 200:
            return {"success": True}
        else:
            return {"success": False}
