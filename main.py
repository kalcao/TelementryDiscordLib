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
