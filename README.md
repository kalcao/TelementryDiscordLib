# TelementryDiscordLib

[![GitHub stars](https://img.shields.io/github/stars/kalcao/TelementryDiscordLib?style=social)](https://github.com/kalcao/TelementryDiscordLib)
[![GitHub license](https://img.shields.io/github/license/kalcao/TelementryDiscordLib)](https://github.com/kalcao/TelementryDiscordLib)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

[![한글 버전](https://img.shields.io/badge/%ED%95%9C%EA%B8%80%20%EB%B2%84%EC%A0%84-%EB%B3%B4%EA%B8%B0-brightgreen)](README_ko.md)

**TelementryDiscordLib** sends telementry data to discord in order to avoid being flagged.

Supports: presence updates, profile edits, guild joins, and member scraping.

> **Disclaimer**: Only for research/education only. **The author assumes no responsibility for any misuse, consequences, or account actions resulting from your use of this library.**

> Don't sell this open-source project. Shame on you if you do.

## Video Demonstration
https://streamable.com/pw0t1h

https://streamable.com/w42n0l

## Risky Actions

| Action             | Safe |
|--------------------|------|
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

Contact: `@inxtagram`

## License

[MIT](LICENSE)

## Thanks to

https://luna.gitlab.io/discord-unofficial-docs/

https://github.com/Merubokkusu/Discord-S.C.U.M

http://discord.food/

https://github.com/RazorCap/RazorCap
