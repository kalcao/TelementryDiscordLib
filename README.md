# TelementryDiscordLib

[![GitHub stars](https://img.shields.io/github/stars/kalcao/TelementryDiscordLib?style=social)](https://github.com/kalcao/TelementryDiscordLib)
[![GitHub license](https://img.shields.io/github/license/kalcao/TelementryDiscordLib)](https://github.com/kalcao/TelementryDiscordLib)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

[![한글 버전](https://img.shields.io/badge/%ED%95%9C%EA%B8%80%20%EB%B2%84%EC%A0%84-%EB%B3%B4%EA%B8%B0-brightgreen)](README_ko.md)

**TelementryDiscordLib** sends telementry data to discord in order to avoid being flagged.

Please ⭐ this repo so I get motivated working on this project! Otherwise I'll stop patching 😊

```diff
- hCaptcha updated in 25-11-16. I've applied a fix but please open issue if your token gets banned after request solving captcha.
```

> **Disclaimer**: Only for research/education only. **The author assumes no responsibility for any misuse, consequences, or account actions resulting from your use of this library.**

> Don't sell this open-source project. Shame on you if you do.

## Video Demonstration
Presence change - https://streamable.com/pw0t1h

Server joining - https://streamable.com/w42n0l

Sending DM - https://streamable.com/l65heg

VC Joining & Playing Soundboard - https://streamable.com/szxmll

## Risky Actions

| Actions                              | Is Safe |
|----------------------------------------|------|
| **Presence Updates**                    | ✅ |
| **Profile Edits**                       | ✅ |
| **Guild Joins**                         | ✅ |
| **Member Scraping**                     | ✅ |
| **Add Friend**                          | ✅ |
| **Sending DMs**                         | ✅ |
| **Joining VC & Playing Soundboard**     | ✅ |
| **Verifying Tokens with phone numbers** | ✅ |


## Usage

### Starting Solver
```bash
python3 solver.py
```

### Your first automation with TDLib
```python
import asyncio
from lib.client import DiscordClient


TOKEN = """Your
Tokens
Here""".splitlines()


async def worker(token, index):
    print(f"[{index}] {token[:8]}****")
    client = None
    try:
        client = DiscordClient(token)
        await client.init()
        await client.ws.is_ready.wait()

        # Presence
        await client.actions.appearance.change_presence(
            status="dnd",
            activities=[{"type": 0, "name": "Hi from TDLib!"}]
        )
        
        # Guild
        await client.actions.guild.join("fEvY9J7W")
        await client.actions.guild.join_vc("Guild Id", "Voice channel ID")

        await client.actions.guild.play_soundboard("Channel Id", 2, "🔊") # Play soundboard
        await client.actions.guild.leave_vc()

        users = await client.actions.guild.scrape("Guild ID", "Channel ID")

        # Fetch message from channel and print 50 latest messages
        channels = await client.actions.misc.fetch_channels("Guild ID")
        print(await client.actions.misc.fetch_message("Guild ID", channels[0]['id'], limit=50))

        # Adding user
        await client.actions.relationship.add(users[0]['id']) # user id, "not username" !!
        
        # Sending DM to a user
        channel_id = await client.actions.relationship.open_dm("1234567890123456789")['id']
        await client.actions.misc.send_message(channel_id, "Hi <@1234567890123456789>! This is automated DM from TDLib :)")

        # Profile
        await client.actions.appearance.change_profile(
            global_name="NewName",
            bio=":wave: Hello :)",
            pronouns="bot/bots"
        )

        # Verifying token with phone number
        phone_number = input("Phone number >")
        print(await client.actions.misc.verify.phone.add(phone_number))

        code = input("code> ")
        pw = input("password >")
        
        print(await client.actions.misc.verify.phone.verify(phone_number, code, pw))
        
    except Exception as e:
        print(f"[{index}] {e}")
    finally:
        if client and hasattr(client, 'close'):
            try:
                await client.close()
            except Exception as close_error:
                print(f"{close_error}")

async def main():
    await asyncio.gather(*(worker(t, i) for i, t in enumerate(TOKEN, 1)))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
```

## Updates
<details>
<summary>View update history</summary>

<details>
<summary>2025-11-19</summary>
    
```diff
+ Solver update
+ Proxy support
+ Opening channel & Sending DM
+ Joining VC & Playing Soundboard
+ Phone verifying
````

</details>

<details>
<summary>2025-11-17</summary>
    
```diff
+ Applied fix for hCaptcha update
````

</details>


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
