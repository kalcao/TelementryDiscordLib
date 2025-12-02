import json
import asyncio
from curl_cffi import AsyncSession

class DiscordWS:
    def __init__(self, token, device_prop, fingerprint, browser_version, client_identity, properties, client=None):
        self.token = token
        self.client = client
        self.ws_data = {'session_id': None, 'analytics_token': None, 'heartbeat_interval': None}
        self.ws_connected = False
        self.ws = None
        self.async_session = None
        self.heartbeat_task = None
        self.packets_recv = 0
        self._closing = False
        self.connected_event = asyncio.Event()
        self.is_ready = asyncio.Event()  # Event for when client is ready (READY event received)
        self.message_handlers = {}
        self.handle_task = None

    async def connect(self):
        browser = self.client.device_prop['browser']
        version = self.client.browser_version.split('.')[0]
        impersonate = f"{browser}"
        self.async_session = AsyncSession(impersonate=impersonate)
        self.ws = await self.async_session.ws_connect("wss://gateway.discord.gg/?v=9&encoding=json")
        self.ws_connected = True
        self.handle_task = asyncio.create_task(self.handle_messages())

    async def handle_messages(self):
        try:
            async for message in self.ws:
                await self.handle_message(message)
        except Exception as e:
            print(f"WebSocket closed or error: {e}")

    async def handle_message(self, message):
        try:
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            d = json.loads(message)
            await self.process_message(d)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON: {message}")
        except Exception as e:
            print(f"Error processing message: {e}")

    async def process_message(self, d):
        op = d.get('op')

        if op == 10:  # Hello
            self.ws_data['heartbeat_interval'] = d['d']['heartbeat_interval']
            auth = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "capabilities": 1734653,
                    "properties": {
                        "os": self.client.properties["os"],
                        "browser": self.client.properties["browser"],
                        "device": self.client.properties["device"],
                        "system_locale": self.client.properties["system_locale"],
                        "has_client_mods": self.client.properties["has_client_mods"],
                        "browser_user_agent": self.client.properties["browser_user_agent"],
                        "browser_version": self.client.properties["browser_version"],
                        "os_version": self.client.properties["os_version"],
                        "referrer": self.client.properties["referrer"],
                        "referring_domain": self.client.properties["referring_domain"],
                        "referrer_current": self.client.properties["referrer_current"],
                        "referring_domain_current": self.client.properties["referring_domain_current"],
                        "release_channel": self.client.properties["release_channel"],
                        "client_build_number": self.client.properties["client_build_number"],
                        "client_event_source": self.client.properties["client_event_source"],
                        "client_launch_id": self.client.client_identity["client_launch_id"],
                        "launch_signature": self.client.client_identity["launch_signature"],
                        "client_app_state": self.client.properties["client_app_state"],
                        "is_fast_connect": False,
                        "gateway_connect_reasons": "AppSkeleton"
                    },
                    "presence": {
                        "status": "unknown",
                        "since": 0,
                        "activities": [],
                        "afk": False
                    },
                    "compress": False,
                    "client_state": {
                        "guild_versions": {}
                    }
                }
            }
            await self.ws.send_str(json.dumps(auth))
            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            self.connected_event.set()

        elif op == 11: # Heartbeat ACK
            pass

        elif d.get('t') == 'READY':
            self.ws_data.update({
                "session_id": d['d']['session_id'],
                "analytics_token": d['d']['analytics_token'],
                "private_channels": d['d']['private_channels']
            })
            # Set the ready event when READY event is received
            self.is_ready.set()

            self.client.science.analytics_token = self.ws_data.get('analytics_token')
            self.client.science.reset()
            if self.client.science.analytics_token is not None and self.client.science.analytics_token != '':
                await self.client.science.submit()

        if d.get('t') in self.message_handlers:
            for handler in self.message_handlers[d['t']][:]:
                try:
                    await handler(d)
                except Exception as e:
                    print(f"Error in message handler for {d['t']}: {e}")
        
        try:
            with open('data.txt', "a", encoding="utf-8") as f:
                f.write(json.dumps(d) + "\n\n")
        except Exception as e:
            print(f"Error writing to data.txt: {e}")

    async def heartbeat(self):
        while self.ws_connected and not self._closing:
            try:
                await asyncio.sleep(self.ws_data['heartbeat_interval'] / 1000)
                if self.ws and not self._closing:
                    await self.ws.send_str(json.dumps({"op": 1, "d": self.packets_recv}))
                    self.packets_recv += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in heartbeat: {e}")
                break

    async def send_custom_data(self, data):
        if self.ws and self.ws_connected and not self._closing:
            try:
                await self.ws.send_str(json.dumps(data) if isinstance(data, (dict, list)) else data)
            except Exception as e:
                print(f"Error sending custom data: {e}")
        else:
            raise ConnectionError("Websocket is not connected")

    def add_message_handler(self, event_type, handler):
        if event_type not in self.message_handlers:
            self.message_handlers[event_type] = []
        if handler not in self.message_handlers[event_type]:
            self.message_handlers[event_type].append(handler)

    def remove_message_handler(self, event_type, handler):
        if event_type in self.message_handlers and handler in self.message_handlers[event_type]:
            self.message_handlers[event_type].remove(handler)
            if not self.message_handlers[event_type]:
                del self.message_handlers[event_type]

    async def close(self):
        if self._closing:
            return
        self._closing = True
        self.ws_connected = False
        
        # Cancel heartbeat task
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await asyncio.wait_for(self.heartbeat_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Stop message handler before tearing down transports to avoid orphaned readers.
        if self.handle_task and not self.handle_task.done():
            self.handle_task.cancel()
            try:
                await asyncio.wait_for(self.handle_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Close WebSocket connection
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                print(f"Error closing websocket: {e}")

        if self.async_session:
            acurl = getattr(self.async_session, "_acurl", None)
            try:
                if acurl is not None:
                    await self.async_session.close()
                else:
                    # Session never instantiated AsyncCurl, so avoid creating one during shutdown.
                    self.async_session._closed = True
            except Exception as e:
                print(f"Error closing async session: {e}")
