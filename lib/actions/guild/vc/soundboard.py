import json
import asyncio

class VCSoundBoard:
    def __init__(self, client):
        self.client = client

    async def play(self, channel_id: str | int, sound_id: str | int, emoji_name: str):
        await self.client._make_request("POST", f"https://discord.com/api/v9/channels/{channel_id}/send-soundboard-sound", json={
            "sound_id":str(sound_id),
            "emoji_id":None,
            "emoji_name":emoji_name})
        return {"success": True, "channel_id": channel_id}
