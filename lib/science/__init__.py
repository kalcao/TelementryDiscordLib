import time
import asyncio
import struct
import base64
import random
import math
import uuid
from datetime import datetime

class Client_UUID(object): # thanks to discum!
    __slots__ = ['userID', 'randomPrefix', 'creationTime', 'UUID']
    def __init__(self, userID, creationTime="now"):
        self.userID = int(userID)
        num = int(4294967296 * random.random())
        self.randomPrefix = num if num <= 2147483647 else num - 4294967296
        self.creationTime = int(time.mktime(datetime.now().timetuple()) * 1000) if creationTime == "now" else creationTime
        self.UUID = ""

    def calculate(self, event_sequence_number, userID="default"):
        if userID == "default":
            userID = self.userID
        else:
            userID = int(userID)

        buf = bytearray(struct.pack('24x'))
        buf[0:4] = struct.pack("<i", userID % 4294967296 if userID % 4294967296 <= 2147483647 else userID % 4294967296 - 4294967296)
        buf[4:8] = struct.pack("<i", userID >> 32 if (userID >> 32) <= 2147483647 else (userID >> 32) - 4294967296)
        buf[8:12] = struct.pack("<i", self.randomPrefix)
        buf[12:16] = struct.pack("<i", self.creationTime % 4294967296 if self.creationTime % 4294967296 <= 2147483647 else self.creationTime % 4294967296 - 4294967296)
        buf[16:20] = struct.pack("<i", self.creationTime >> 32 if (self.creationTime >> 32) <= 2147483647 else (self.creationTime >> 32) - 4294967296)
        buf[20:24] = struct.pack("<i", event_sequence_number if event_sequence_number <= 2147483647 else event_sequence_number - 4294967296)

        self.UUID = base64.b64encode(buf).decode('ascii')
        return self.UUID

    def refresh(self, event_sequence_number):
        num = int(4294967296 * random.random())
        self.randomPrefix = num if num <= 2147483647 else num - 4294967296
        self.creationTime = int(time.mktime(datetime.now().timetuple()) * 1000)
        return self.calculate(event_sequence_number=event_sequence_number, userID="default")

    @staticmethod
    def parse(client_uuid):
        decoded_client_uuid = base64.b64decode(client_uuid)
        unpacked = []
        for i in range(6):
            unpacked.append(struct.unpack('<i', decoded_client_uuid[4*i:4*i+4])[0])
        UUIDdata = {}
        userIDguess = ((unpacked[1] if unpacked[1] >= 0 else unpacked[1] + 4294967296) << 32) + (unpacked[0] if unpacked[0] >= 0 else unpacked[0] + 4294967296)
        UUIDdata['userID'] = str(userIDguess)
        UUIDdata['randomPrefix'] = unpacked[2] if unpacked[2] >= 0 else unpacked[2] + 4294967296
        creationTimeGuess = ((unpacked[4] if unpacked[4] >= 0 else unpacked[4] + 4294967296) << 32) + (unpacked[3] if unpacked[3] >= 0 else unpacked[3] + 4294967296)
        UUIDdata['creationTime'] = creationTimeGuess
        UUIDdata['eventNum'] = unpacked[5] if unpacked[5] >= 0 else unpacked[5] + 4294967296
        return UUIDdata

class SciencePayload:
    def __init__(self, client):
        self.client = client
        self.ws = client.ws
        # Try to get analytics token from ws_data first (which is where it's stored after WebSocket connection)
        self.analytics_token = self.ws.ws_data.get('analytics_token')
        self.client_heartbeat_session_id = self.client.client_identity['client_heartbeat_session_id']
        self.launch_signature = self.client.client_identity['launch_signature']
        self.user_info = self.client.me.json() if hasattr(self.client.me, 'json') else self.client.me
        self.user_id = self.user_info.get('id', '0')
        self.locale = self.user_info.get('locale', 'en')
        self.uuid_gen = Client_UUID(self.user_id)
        self.events = {'token': self.analytics_token, 'events': []}
        self.event_sequence_number = 5 # libdiscore_loaded마다 초기화됨

    def reset(self):
        self.analytics_token = self.ws.ws_data.get('analytics_token')
        self.event_sequence_number = 5 # Reset event sequence number
        visible_user_ids = []
        private_channels = self.client.ws.ws_data.get('private_channels', [])
        for channel in private_channels:
            for recipient in channel.get('recipients', []):
                user_id = recipient.get('id')
                if user_id and user_id not in visible_user_ids:
                    visible_user_ids.append(user_id)

        self.events['events'] = [{
            "type":"libdiscore_loaded",
            "properties":{
                "client_track_timestamp":int(time.time() * 1000),
                "client_heartbeat_session_id": self.client_heartbeat_session_id,
                "event_sequence_number":1,
                "success":True,
                "experimental_features":[],
                "client_performance_memory":0,
                "accessibility_features":256,
                "rendered_locale":self.locale,
                "uptime_app":0,
                "launch_signature": self.launch_signature,
            }
            },{
            "type":"session_start_client",
            "properties":{
                "client_track_timestamp":int(time.time() * 1000),
                "client_heartbeat_session_id": self.client_heartbeat_session_id,
                "event_sequence_number":2,
                "client_performance_memory":0,
                "accessibility_features":256,
                "rendered_locale":self.locale,
                "uptime_app":1,
                "launch_signature": self.launch_signature,
                "client_rtc_state":"DISCONNECTED",
                "client_app_state":"unfocused",
                "client_viewport_width":1280,
                "client_viewport_height":720,
            }
            },
            {
            "type":"app_ui_viewed",
            "properties":{
                "client_track_timestamp":int(time.time() * 1000),
                "client_heartbeat_session_id":self.client_heartbeat_session_id,
                "event_sequence_number":3,
                "total_compressed_byte_size":11149616,
                "total_uncompressed_byte_size":53463101,
                "total_transfer_byte_size":0,
                "js_compressed_byte_size":7349364,
                "js_uncompressed_byte_size":36652103,
                "js_transfer_byte_size":0,
                "css_compressed_byte_size":667380,
                "css_uncompressed_byte_size":4550726,
                "css_transfer_byte_size":0,
                "load_id":str(uuid.uuid4()),
                "screen_name":"friends",
                "duration_ms_since_app_opened":2833,
                "app_hardware_acceleration_enabled":True,
                "client_performance_memory":0,
                "accessibility_features":256,
                "rendered_locale":self.locale,
                "uptime_app":1,
                "launch_signature":self.launch_signature,
                "client_rtc_state":"DISCONNECTED",
                "client_app_state":"unfocused",
                "client_viewport_width":1280,
                "client_viewport_height":720,
            }
        },
        {
            "type":"ready_payload_received",
            "properties":{
                "client_track_timestamp":int(time.time() * 1000),
                "client_heartbeat_session_id":self.client_heartbeat_session_id,
                "event_sequence_number":4,
                "compressed_byte_size":13378,
                "uncompressed_byte_size":53363,
                "compression_algorithm":"zlib-stream",
                "packing_algorithm":"json",
                "unpack_duration_ms":1,
                "identify_total_server_duration_ms":336,
                "identify_api_duration_ms":260,
                "identify_guilds_duration_ms":0,
                "num_guilds":1,
                "num_guild_channels":4,
                "num_guild_category_channels":2,
                "presences_size":2,
                "users_size":296,
                "read_states_size":334,
                "private_channels_size":2,
                "user_settings_size":170,
                "experiments_size":29303,
                "user_guild_settings_size":15418,
                "relationships_size":2,
                "remaining_data_size":4727,
                "guild_channels_size":782,
                "guild_members_size":244,
                "guild_presences_size":2,
                "guild_roles_size":284,
                "guild_emojis_size":4,
                "guild_threads_size":4,
                "guild_stickers_size":329,
                "guild_events_size":4,
                "guild_features_size":16,
                "guild_remaining_data_size":3528,
                "size_metrics_duration_ms":0,
                "duration_ms_since_identify_start":int("-"+str(int(time.time() * 1000))),
                "duration_ms_since_connection_start":int("-"+str(int(time.time() * 1000))),
                "duration_ms_since_emit_start":int(time.time() * 1000),
                "is_reconnect":False,
                "is_fast_connect":False,
                "did_force_clear_guild_hashes":False,
                "identify_uncompressed_byte_size":985,
                "identify_compressed_byte_size":606,
                "had_cache_at_startup":False,
                "used_cache_at_startup":False,
                "client_performance_memory":0,
                "accessibility_features":256,
                "rendered_locale":self.locale,
                "uptime_app":2,
                "launch_signature":self.launch_signature,
                "client_rtc_state":"DISCONNECTED",
                "client_app_state":"unfocused",
                "client_viewport_width":1280,
                "client_viewport_height":720,
                "client_uuid":self.uuid_gen.calculate(event_sequence_number=4),
            }
        },
        {
            "type": "dm_list_viewed",
            "properties": {
                "accessibility_features": 524544,
                "accessibility_support_enabled": False,
                "client_performance_memory": 0,
                "client_track_timestamp":int(time.time() * 1000),
                "client_uuid": self.uuid_gen.calculate(event_sequence_number=5),
                "num_users_visible": len(visible_user_ids),
                "num_users_visible_with_mobile_indicator": 0,
                "rendered_locale": self.locale
            }
        }
    ]

    def add(self, type, external_properties={}):
        U = time.perf_counter()
        self.event_sequence_number += 1
        event = {
            'type': type,
            'properties': {
                'client_track_timestamp': int(time.time() * 1000),
                'client_heartbeat_session_id': self.client_heartbeat_session_id,
                'event_sequence_number': self.event_sequence_number,
                'success': True,
                'experimental_features': [],
                'client_performance_memory': 0,
                'accessibility_features': 256, # 다크모드 https://docs.discord.food/reference#accessibility-feature-flags
                'rendered_locale': self.locale,
                'uptime_app': math.floor((time.perf_counter() - U)),
                'client_uuid': self.uuid_gen.calculate(event_sequence_number=self.event_sequence_number),
                'launch_signature': self.launch_signature,
                ** external_properties
            },
        }
        self.events['events'].append(event)

    async def submit(self):
        timestamp = int(time.time() * 1000)
        # Update the analytics token just before submitting, in case it became available
        # after SciencePayload was initialized
        latest_token = self.ws.ws_data.get('analytics_token', getattr(self.ws, 'analytics_token', getattr(self.client, 'analytics_token', 'default_token')))
        self.analytics_token = latest_token
        self.events['token'] = self.analytics_token if self.analytics_token is not None else 'default_token'  # Update token in events
        
        for event in self.events['events']:
            event['properties']['client_send_timestamp'] = timestamp
        
        # Only submit if we have a valid token
        if self.analytics_token is not None and self.analytics_token != 'default_token':
            try:
                # Access the async request from the client object through ws
                print(self.events)
                await self.client._make_request(
                    "POST",
                    "https://discord.com/api/v9/science", 
                    json=self.events
                )
                # print(self.events)
                # print("\n\n\n\n")
            except Exception as e:
                print(f"Error submitting to /science: {e}")
            finally:
                self.events['events'] = []
        else:
            print("Skipping science submission due to missing analytics token")
            self.events['events'] = []  # Clear events even if not submitted