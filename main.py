import asyncio
from lib.client import DiscordClient

TOKEN = [""]

async def worker(token, index):
    print(f"[{index}] {token[:8]}****")
    client = DiscordClient(token)
    await client.init()
    try:
        await client.ws.is_ready.wait()
        await client.actions.guild.join('discord-developers')
    except Exception as e:
        print(f"[{index}] ", e)
    finally:
        if hasattr(client, 'close'):
            await client.close()

async def main():
    await asyncio.gather(*(worker(t, i) for i, t in enumerate(TOKEN, 1)))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
