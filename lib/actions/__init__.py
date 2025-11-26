from typing import Optional


class ActionsContainer:
    def __init__(self, client):
        # Group actions by category
        self.appearance = AppearanceActions(client)
        self.guild = GuildActions(client)
        self.relationship = RelationshipActions(client)
        self.misc = MiscActions(client)


class AppearanceActions:
    def __init__(self, client):
        from lib.actions.appearance.status import StatusHandler
        from lib.actions.appearance.profile import ProfileChanger
        self._status_handler = StatusHandler(client)
        self._profile_changer = ProfileChanger(client)

    async def change_presence(self, **kwargs):
        return await self._status_handler.change_presence(**kwargs)

    async def change_profile(self, avatar=None, global_name=None, bio=None, pronouns=None, accent_color=None):
        return await self._profile_changer.change_profile(
            avatar=avatar, global_name=global_name, bio=bio, pronouns=pronouns, accent_color=accent_color
        )


class GuildActions:
    def __init__(self, client):
        from lib.actions.guild.join import JoinHandler
        from lib.actions.guild.scrape import GuildScraper
        from lib.actions.guild.leave import Leave
        from lib.actions.guild.vc.join import VCJoin
        from lib.actions.guild.vc.soundboard import VCSoundBoard
        self._join_handler = JoinHandler(client)
        self._scrape_handler = GuildScraper(client)
        self._leave_handler = Leave(client)
        self._vc_join_handler = VCJoin(client)
        self._vc_soundboard_handler = VCSoundBoard(client)

    async def join(self, invite_code: str):
        return await self._join_handler.join_guild(invite_code)

    async def scrape(self, guild_id: str, channel_id: str):
        return await self._scrape_handler.scrape(guild_id, channel_id)

    async def leave(self, guild_id: str):
        return await self._leave_handler.leave_guild(guild_id)

    async def join_vc(self, guild_id: str | int, channel_id: str | int):
        return await self._vc_join_handler.join(guild_id, channel_id)

    async def leave_vc(self):
        return await self._vc_join_handler.leave()

    async def play_soundboard(self, channel_id: str | int, sound_id: str | int, emoji_name: str):
        return await self._vc_soundboard_handler.play(channel_id, sound_id, emoji_name)


class RelationshipActions:
    def __init__(self, client):
        from lib.actions.relationship.add import AddFriend
        from lib.actions.relationship.open_dm import OpenChannel
        self._add_friend_handler = AddFriend(client)
        self._open_channel_handler = OpenChannel(client)

    async def add(self, username: str):
        return await self._add_friend_handler.add(username)

    async def open_dm(self, user_id: str):
        return await self._open_channel_handler.open_dm(user_id)


class MiscActions:
    def __init__(self, client):
        from lib.actions.misc.fetch_message import FetchMessage
        from lib.actions.misc.fetch_channels import FetchChannels
        from lib.actions.misc.send import SendMessage
        from lib.actions.misc.verify import VerifyActions
        self._fetch_message_handler = FetchMessage(client)
        self._fetch_channels_handler = FetchChannels(client)
        self._send_message_handler = SendMessage(client)
        self.verify = VerifyActions(client)

    async def fetch_message(self, guild_id: str, channel_id: str, last_message_id: Optional[str] = None, limit: int = 50):
        return await self._fetch_message_handler.fetch_messages(
            guild_id=guild_id,
            channel_id=channel_id,
            last_message_id=last_message_id,
            limit=limit,
        )

    async def fetch_channels(
        self,
        guild_id: str,
    ):
        return await self._fetch_channels_handler.fetch_channels(
            guild_id=guild_id,
        )

    async def send_message(
        self,
        channel_id: str,
        content: str,
        guild_id=None,
        reply=None,
    ):
        return await self._send_message_handler.send_messages(
            guild_id=guild_id,
            channel_id=channel_id,
            content=content,
            reply=reply,
        )
