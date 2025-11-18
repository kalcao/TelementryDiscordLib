class FetchChannels:
    def __init__(self, client):
        self.client = client
        self.science = self.client.science

    async def fetch_channels(self, guild_id: str):
        """
        Fetch the list of channels for the given guild and emit an analytics event that mirrors
        what the client would normally send when opening a guild.
        """

        response = await self.client._make_request("GET", f"https://discord.com/api/v10/guilds/{guild_id}/channels")
        status = getattr(response, "status_code", None)
        if status and status >= 400:
            raise Exception(
                f"[GET] https://discord.com/api/v10/guilds/{guild_id}/channels {status}: {getattr(response, 'text', '')}"
            )

        channels = response.json() if callable(getattr(response, "json", None)) else response
        first_channel_id = channels[0].get("id") if isinstance(channels, list) and channels else None

        self.science.add(
            "guild_viewed",
            {
                "channel_id": first_channel_id,
                "channel_was_unread": False,
                "channel_mention_count": 0,
                "channel_is_muted": False,
                "channel_is_nsfw": False,
                "channel_resolved_unread_setting": 1,
                "channel_preset": "all_messages",
                "guild_id": guild_id,
                "guild_was_unread": False,
                "guild_mention_count": 0,
                "guild_is_muted": False,
                "guild_resolved_unread_setting": 1,
                "guild_preset": "all_messages",
                "parent_id": guild_id,
                "has_pending_member_action": False,
                "can_send_message": True,
                "is_app_dm": False,
                "guild_size_total": 10,
                "guild_num_channels": 4,
                "guild_num_text_channels": 3,
                "guild_num_voice_channels": 1,
                "guild_num_roles": 4,
                "guild_member_num_roles": 0,
                "guild_member_perms": None,
                "guild_is_vip": False,
                "is_member": True,
                "num_voice_channels_active": 0,
                "channel_type": 0,
                "channel_size_total": 0,
                "channel_hidden": False,
                "client_performance_cpu": 5.408199410115926,
                "client_performance_memory": 1821412,
                "cpu_core_count": 12,
                "accessibility_features": 67633408,
                "uptime_process_renderer": 287279,
                "client_rtc_state": "DISCONNECTED",
                "client_app_state": "focused",
                "client_viewport_width": 1280,
                "client_viewport_height": 720,
            },
        )
        await self.science.submit()
        return channels
