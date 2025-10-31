# TelementryDiscordLib

[![GitHub stars](https://img.shields.io/github/stars/kalcao/TelementryDiscordLib?style=social)](https://github.com/kalcao/TelementryDiscordLib)
[![GitHub license](https://img.shields.io/github/license/kalcao/TelementryDiscordLib)](https://github.com/kalcao/TelementryDiscordLib)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

**TelementryDiscordLib** sends telementry data to discord in order to avoid being flagged.

Supports: presence updates, profile edits, guild joins, and member scraping.

> **Disclaimer**: Only for research/education only. I'm not responsible for any misuse, consequences, or account actions resulting from your use of this library.

## Risky Actions

| Action             | Safe |
|--------------------|------------|
| **Presence Updates** | ✅ |
| **Profile Edits**  | ✅ |
| **Guild Joins**    | ✅ |
| **Member Scraping**| ✅ |
| **Add Friend**     | ❌ |

## Usage

```python
from lib.client import DiscordClient

async def main():
    client = DiscordClient("your_token")
    await client.init()

    # Presence
    await client.actions.appearance.change_presence(
        status="dnd",
        activities=[{"type": 0, "name": "Python"}]
    )

    # Profile
    await client.actions.appearance.change_profile(
        global_name="NewName",
        bio="Bio here"
    )

    # Guild
    await client.actions.guild.join("invite_code")
    members = await client.actions.guild.scrape("guild_id", "channel_id")

    await client.close()

asyncio.run(main())
```

## Contributing

Fork → Branch → PR. Issues are welcome

## License

[MIT](LICENSE)

**[Star on GitHub](https://github.com/kalcao/TelementryDiscordLib)**
