class ActionsContainer:
    def __init__(self, client):
        # Group actions by category
        self.appearance = AppearanceActions(client)
        self.guild = GuildActions(client)
        self.relationship = RelationshipActions(client)
        from lib.actions.appearance.profile import ProfileChanger
        self._profile_changer = ProfileChanger(client)

    async def change_profile(self, avatar=None, global_name=None, bio=None, pronouns=None, accent_color=None):
        return await self._profile_changer.change_profile(
            avatar=avatar, global_name=global_name, bio=bio, pronouns=pronouns, accent_color=accent_color
        )


class AppearanceActions:
    def __init__(self, client):
        from lib.actions.appearance.status import StatusHandler
        self._status_handler = StatusHandler(client)

    async def change_presence(self, **kwargs):
        return await self._status_handler.change_presence(**kwargs)


class GuildActions:
    def __init__(self, client):
        from lib.actions.guild.join import JoinHandler
        from lib.actions.guild.scrape import GuildScraper
        from lib.actions.guild.leave import Leave
        self._join_handler = JoinHandler(client)
        self._scrape_handler = GuildScraper(client)
        self._leave_handler = Leave(client)

    async def join(self, invite_code: str):
        return await self._join_handler.join_guild(invite_code)

    async def scrape(self, guild_id: str, channel_id: str):
        return await self._scrape_handler.scrape(guild_id, channel_id)

    async def leave(self, guild_id: str):
        return await self._leave_handler.leave_guild(guild_id)


class RelationshipActions:
    def __init__(self, client):
        from lib.actions.relationship.add import AddFriend
        self._add_friend_handler = AddFriend(client)

    async def add(self, username: str):
        return await self._add_friend_handler.add(username)