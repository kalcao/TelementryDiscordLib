import json
import asyncio

class VCJoin:
    def __init__(self, client):
        self.client = client

    async def join(self, guild_id: str | int, channel_id: str | int):
        await self.client.ws.ws.send(json.dumps({
            "op": 4,
            "d": {
                "guild_id": str(guild_id),
                "channel_id": str(channel_id),
                "self_mute": False,
                "self_deaf": False,
                "self_video": True,
                "flags": 2
            }
        }))
        return {"success": True, "guild_id": guild_id, "channel_id": channel_id}

    async def leave(self):
        await self.client.ws.ws.send(json.dumps({
            "op": 4,
            "d": {
                "guild_id": None,
                "channel_id": None,
                "self_mute": True,
                "self_deaf": False,
                "self_video": False,
                "flags": 2
            }
        }))
        return {"success": True}