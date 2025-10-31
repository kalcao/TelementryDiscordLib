import json
import asyncio

class StatusHandler:
    def __init__(self, client):
        self.client = client
        self.presence = {
            'status': 'online', 
            'custom_status': None, 
            'activity_type': None, 
            'name': None, 
            'url': None,
            'activities': None
        }

    async def change_presence(
        self, 
        status: str = None, 
        custom_status: str = None, 
        activity_type: int = None, 
        name: str = None, 
        url: str = None,
        activities: list = None
    ):
        if status in {"online", "idle", "dnd"}:
            self.presence['status'] = status
        
        if activities is not None:
            self.presence['activities'] = activities
            
            if not self.client.ws.ws_connected or not self.client.ws.ws:
                return

            presence_update = {
                "op": 3, 
                "d": {
                    "since": 0, 
                    "activities": activities, 
                    "status": self.presence['status'], 
                    "afk": False
                }
            }
            await self.client.ws.ws.send(json.dumps(presence_update))
            return
        
        if custom_status is not None:
            self.presence['custom_status'] = custom_status
        if activity_type is not None:
            self.presence['activity_type'] = activity_type
        if name is not None:
            self.presence['name'] = name
        if url is not None:
            self.presence['url'] = url

        activity = {
            "type": self.presence.get('activity_type', 0), 
            "name": self.presence.get('name', "")
        }
        if self.presence.get('url') and activity['type'] == 1:
            activity['url'] = self.presence['url']

        activities_list = []
        if self.presence.get('custom_status'):
            activities_list.append({
                "type": 4, 
                "state": self.presence['custom_status'], 
                "name": "Custom Status", 
                "id": "custom"
            })
        if self.presence.get('activity_type') is not None:
            activities_list.append(activity)

        if not self.client.ws.ws_connected or not self.client.ws.ws:
            return

        presence_update = {
            "op": 3, 
            "d": {
                "since": 0, 
                "activities": activities_list, 
                "status": self.presence['status'], 
                "afk": False
            }
        }
        await self.client.ws.ws.send(json.dumps(presence_update))