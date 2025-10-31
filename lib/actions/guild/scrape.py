import json, asyncio, time, random
from typing import Dict, List, Optional

class GuildScraper:
    def __init__(self, client):
        self.client = client
        self.guild_id = self.channel_id = None
        self.blacklisted_ids = {""}
        self.end_scraping = False
        self.guilds = self.members = {}
        self.ranges = [[0, 0]]
        self.last_range = 0
        self.started = self.completed_printed = self.handlers_registered = False
        self.consecutive_empty_responses = 0

    @staticmethod
    def get_ranges(index, multiplier, member_count):
        initial_num = int(index * multiplier)
        ranges = [[initial_num, initial_num + 99]]
        if member_count > initial_num + 99:
            ranges.append([initial_num + 100, initial_num + 199])
        if [0, 99] not in ranges:
            ranges.insert(0, [0, 99])
        return ranges

    async def process_members(self, updates):
        for item in updates:
            if not isinstance(item, dict):
                continue
            
            member = item.get("member")
            if not isinstance(member, dict):
                continue
            
            user = member.get("user", {})
            if not isinstance(user, dict):
                continue

            user_id = user.get("id")
            if not user_id or user_id in self.blacklisted_ids or user.get("bot"):
                continue

            member_data = {
                "id": user_id,
                "tag": user.get("global_name", user.get("username", "")),
                "username": user.get("username", ""),
                "discriminator": user.get("discriminator", "0"),
                "avatar": user.get("avatar"),
                "avatar_decoration_data": user.get("avatar_decoration_data"),
                "public_flags": user.get("public_flags", 0),
                "roles": member.get("roles", []),
                "joined_at": member.get("joined_at"),
                "premium_since": member.get("premium_since"),
                "nick": member.get("nick"),
                "flags": member.get("flags", 0),
            }

            if user.get("collectibles"):
                member_data["collectibles"] = user["collectibles"]
            

            if user.get("primary_guild"):
                member_data["primary_guild"] = user["primary_guild"]
            
            if member.get("presence"):
                presence = member["presence"]
                member_data["presence"] = {
                    "status": presence.get("status"),
                    "activities": presence.get("activities", []),
                    "client_status": presence.get("client_status", {})
                }
            
            if member.get("banner"):
                member_data["banner"] = member["banner"]
            
            if user_id in self.members:
                self.members[user_id].update(member_data)
            else:
                self.members[user_id] = member_data
            
            print(f"{member_data['tag']} ({user_id})")

    async def handle_ready(self, message: Dict):
        for guild in message.get("d", {}).get("guilds", []):
            self.guilds[guild["id"]] = {"member_count": guild.get("member_count")}

    async def handle_guild_member_list_update(self, message: Dict):
        try:
            data = message["d"]
            if data["guild_id"] != self.guild_id:
                return
            
            ops = data["ops"]
            types = [op["op"] for op in ops]
            updates_list = []
            
            for chunk in ops:
                op_type = chunk["op"]
                if op_type in {"SYNC", "INVALIDATE"}:
                    updates_list.append(chunk["items"] if op_type == "SYNC" else [])
                elif op_type in {"INSERT", "UPDATE", "DELETE"}:
                    updates_list.append(chunk["item"] if op_type != "DELETE" else [])
            
            if any(t in {"SYNC", "UPDATE", "INSERT"} for t in types):
                has_content = False
                for i, update_type in enumerate(types):
                    updates = updates_list[i]
                    if update_type in {"SYNC", "UPDATE", "INSERT"}:
                        if updates or (update_type == "INSERT" and isinstance(updates, dict)):
                            await self.process_members(updates if update_type != "INSERT" else [updates])
                            self.consecutive_empty_responses = 0
                            has_content = True
                        elif update_type == "SYNC":
                            self.consecutive_empty_responses += 1
                
                if has_content or self.consecutive_empty_responses < 5:
                    self.last_range += 1
                    member_count = self.guilds.get(self.guild_id, {}).get("member_count", self.last_range * 100 + 200)
                    self.ranges = self.get_ranges(self.last_range, 100, member_count)
                    current_start = self.ranges[0][0] if self.ranges else 0
                    expected_count = self.guilds.get(self.guild_id, {}).get("member_count", 10000)
                    
                    if current_start > expected_count + 1000:
                        self.end_scraping = True
                    else:
                        await self.scrape_users()
                else:
                    self.end_scraping = True
            
            if self.end_scraping and not self.completed_printed:
                print(f"Scraping completed. Found {len(self.members)} members.")
                self.completed_printed = True
                
        except KeyError as e:
            print(f"KeyError in parsing: {e}")
        except Exception as e:
            print(f"Error processing updates: {e}")
            import traceback
            traceback.print_exc()

    async def scrape_users(self):
        if not self.end_scraping:
            custom_data = {
                "op": 14,
                "d": {
                    "guild_id": self.guild_id,
                    "typing": True,
                    "activities": True,
                    "threads": True,
                    "channels": {self.channel_id: self.ranges}
                }
            }
            try:
                await self.client.send_custom_data(custom_data)
            except Exception as e:
                print(f"Error sending scrape request: {e}")

    async def on_ready_supplemental(self, message: Dict):
        if self.guild_id in self.guilds:
            self.ranges = self.get_ranges(0, 100, self.guilds[self.guild_id]["member_count"])
            await self.scrape_users()
            self.started = True
        else:
            print(f"Guild {self.guild_id} not found in READY data")
            print(f"Available guilds: {list(self.guilds.keys())}")
            self.end_scraping = True

    async def scrape(self, guild_id: str, channel_id: str) -> Dict:
        self.guild_id, self.channel_id = guild_id, channel_id
        self.end_scraping = self.started = False
        self.members = {}
        self.last_range = 0

        if hasattr(self.client, 'ws') and not self.handlers_registered:
            self.client.ws.add_message_handler("GUILD_MEMBER_LIST_UPDATE", self.handle_guild_member_list_update)
            self.client.ws.add_message_handler("READY", self.handle_ready)
            self.client.ws.add_message_handler("READY_SUPPLEMENTAL", self.on_ready_supplemental)
            self.handlers_registered = True

        while not self.started and not self.end_scraping:
            await asyncio.sleep(0.1)

        while not self.end_scraping:
            await asyncio.sleep(0.1)

        if hasattr(self.client, 'ws'):
            self.client.ws.remove_message_handler("GUILD_MEMBER_LIST_UPDATE", self.handle_guild_member_list_update)
            self.client.ws.remove_message_handler("READY_SUPPLEMENTAL", self.on_ready_supplemental)
            self.client.ws.remove_message_handler("READY", self.handle_ready)

        return self.members