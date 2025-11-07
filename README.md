# TelementryDiscordLib

[![GitHub stars](https://img.shields.io/github/stars/kalcao/TelementryDiscordLib?style=social)](https://github.com/kalcao/TelementryDiscordLib)
[![GitHub license](https://img.shields.io/github/license/kalcao/TelementryDiscordLib)](https://github.com/kalcao/TelementryDiscordLib)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

[![한글 버전](https://img.shields.io/badge/%ED%95%9C%EA%B8%80%20%EB%B2%84%EC%A0%84-%EB%B3%B4%EA%B8%B0-brightgreen)](README_ko.md)

**TelementryDiscordLib** sends telementry data to discord in order to avoid being flagged.

Please ⭐ this repo so I get motivated working on this project! Otherwise I'll stop patching 😊

> **Disclaimer**: Only for research/education only. **The author assumes no responsibility for any misuse, consequences, or account actions resulting from your use of this library.**

> Don't sell this open-source project. Shame on you if you do.

## Video Demonstration
Presence change - https://streamable.com/pw0t1h
Account Creation - https://streamable.com/t3mc84 (SOON! ⭐ please <3)
Server joining - https://streamable.com/w42n0l

## Risky Actions

| Action             | Safe |
|--------------------|------|
| **Presence Updates** | ✅ |
| **Profile Edits**  | ✅ |
| **Guild Joins**    | ✅ |
| **Member Scraping**| ✅ |
| **Add Friend**     | ✅ |

## Usage

### Starting Solver
```bash
python3 solver.py
```

### Your first automation with TDLib
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
    await client.actions.relationship.add("1234567890123456789") # user id, "not username" !!
    # Profile
    await client.actions.appearance.change_profile(
        global_name="NewName",
        bio="Bio here"
    )

    # Guild
    await client.actions.guild.join("invite_code")
    members = await client.actions.guild.scrape("guild_id", "channel_id")

    # Raw Request
    res = await client._make_request("POST", f"https://discord.com/api/v9/channels/{i}/messages",json={"mobile_network_type": "unknown", "content": "i like animals, but my favorite one is a dog", "tts": False, "flags": 0})
    await client.close()

asyncio.run(main())
```

## Updates
<details>
<summary>View update history</summary>


<details>
<summary>2025-11-03</summary>
    
```diff
+ Intergrated Solver
+ Fixed actions.relationship.add() being flagged and will disable token.
- RazorCap was deprecated due to flag issue

p.s. I don't like solver. 100 browsers will be launched if 100 tokens faces captcha
````

</details>

<details>
<summary>2025-11-01</summary>

```diff
+ Released TelementryDiscordLib
````

</details>

</details>

## Contributing

Fork → Branch → PR. Issues are welcome

Contact: `@inxtagram` on discord

## License

[MIT](LICENSE)

## Thanks to

https://luna.gitlab.io/discord-unofficial-docs/

https://github.com/Merubokkusu/Discord-S.C.U.M

http://discord.food/

https://github.com/RazorCap/RazorCap
