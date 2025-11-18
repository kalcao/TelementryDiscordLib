import asyncio
import base64
import json
import random
import time
import uuid
from typing import Dict, Optional

import requests
from solver_client import Solver


def generate_nonce() -> str:
    """
    Replicates Discord's snowflake-based nonce generation.
    """
    timestamp = int(time.time() * 1000) - 1420070400000
    return str(timestamp << 22)


class SendMessage:
    def __init__(self, client):
        self.client = client
        self.science = self.client.science

    async def send_messages(self, channel_id: str, content: str, guild_id: Optional[str] = None):
        """
        Send a message to the specified channel. If Discord responds with an hCaptcha
        challenge, reuse the local solver (http://localhost:5001) just like the join flow,
        then retry with the captcha headers appended.
        """

        await self._track_channel_open(guild_id, channel_id)

        context_headers = self._build_context_headers(guild_id, channel_id)
        response = await self._send(channel_id, content, headers=context_headers)
        if response.status_code in (200, 201):
            return response.json()

        captcha_payload = self._safe_json(response)
        if (
            response.status_code == 400
            and isinstance(captcha_payload, dict)
            and captcha_payload.get("captcha_key")
        ):
            captcha_token = await self._solve_captcha(captcha_payload)
            if not captcha_token:
                raise Exception("Captcha required but solver did not return a token")

            retry_headers = {
                **context_headers,
                **self._build_captcha_headers(captcha_payload, captcha_token),
            }
            retry_response = await self._send(channel_id, content, headers=retry_headers)
            if retry_response.status_code in (200, 201):
                return retry_response.json()

            raise Exception(
                f"Failed to send message even after captcha (HTTP {retry_response.status_code}) - "
                f"{getattr(retry_response, 'text', '')}"
            )

        raise Exception(
            f"Failed to send message (HTTP {response.status_code}) - {getattr(response, 'text', '')}"
        )

    async def _track_channel_open(self, guild_id: Optional[str], channel_id: str):
        self.science.add('channel_opened', external_properties={
            "channel_is_nsfw": False,
            "can_send_message": False,
            "channel_id": channel_id,
            "channel_type": 1,
            "channel_size_total": 1,
            "channel_member_perms": "0",
            "channel_hidden": False,
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "accessibility_support_enabled": False
        })
        await self.science.submit()

    async def _send(self, channel_id: str, content: str, headers: Optional[Dict[str, str]] = None):
        payload = {
            "mobile_network_type": "unknown",
            "content": content,
            "nonce": generate_nonce(),
            "tts": False,
            "flags": 0,
        }
        merged_headers = dict(headers or {})
        res = await self.client._make_request(
            "POST",
            f"https://discord.com/api/v9/channels/{channel_id}/messages",
            json=payload,
            headers=merged_headers,
        )
        self.science.add('friends_list_viewed', external_properties={
            "tab_opened": "ADD_FRIEND",
            "client_performance_memory": 0,
            "accessibility_features": 524544,
            "accessibility_support_enabled": False
        })
        await self.science.submit()
        for i in range(5):
            self.science.add('premium_feature_tutorial_steps', external_properties={
                "location_stack": [
                    "guild header"
                ],
                "tutorial_step": "server_boost_tutorial_started",
                "client_performance_memory": 0,
                "accessibility_features": 524544,
                "accessibility_support_enabled": False
            })

            self.science.add('dm_list_viewed', external_properties={
                "num_users_visible": 1,
                "num_users_visible_with_mobile_indicator": 0,
                "channel_id": channel_id,
                "channel_type": 1,
                "channel_size_total": 1,
                "channel_member_perms": "0",
                "channel_hidden": False,
                "client_performance_memory": 0,
                "accessibility_features": 524544,
                "rendered_locale": "en-US",
                "accessibility_support_enabled": False
            })

            await self.science.submit()
            await asyncio.sleep(0.3)
        return res

    async def _solve_captcha(self, captcha_payload: Dict) -> str:
        captcha_sitekey = captcha_payload.get("captcha_sitekey")
        captcha_rqdata = captcha_payload.get("captcha_rqdata")
        captcha_rqtoken = captcha_payload.get("captcha_rqtoken")

        if not all([captcha_sitekey, captcha_rqdata, captcha_rqtoken]):
            return ""

        # Mirror join.py analytics so Discord sees a consistent captcha flow
        self.science.add("open_modal", {"type": "Guild Join Captcha"})
        self.science.add("captcha_modal", {"type": "Captcha Modal"})
        self.science.add(
            "captcha_event",
            {
                "captcha_event_name": "initial-load",
                "captcha_flow_key": uuid.uuid4().hex,
                "captcha_service": "hcaptcha",
            },
        )
        await self.science.submit()

        solver = Solver(
            url="https://discord.com/",
            sitekey=captcha_sitekey,
            rqdata=captcha_rqdata,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        )
        token, _ = solver.solve()

        if token:
            self.science.add(
                "captcha_event",
                {
                    "captcha_event_name": "solved",
                    "captcha_flow_key": captcha_payload.get("captcha_rqtoken"),
                    "captcha_service": captcha_payload.get("captcha_service", "hcaptcha"),
                },
            )
            await self.science.submit()

        return token or ""

    @staticmethod
    def _build_captcha_headers(captcha_payload: Dict, captcha_key: str) -> Dict[str, str]:
        return {
            "X-Captcha-Key": captcha_key,
            "X-Captcha-Rqtoken": captcha_payload.get("captcha_rqtoken", ""),
            "X-Captcha-Rqdata": captcha_payload.get("captcha_rqdata", ""),
            "X-Captcha-Session-Id": captcha_payload.get("captcha_session_id", ""),
        }

    @staticmethod
    def _build_context_headers(guild_id: Optional[str], channel_id: str) -> Dict[str, str]:
        context = {
            "location": "chat_input",
            "location_guild_id": guild_id,
            "location_channel_id": channel_id,
            "location_channel_type": 0 if guild_id else 1,
        }
        filtered = {k: v for k, v in context.items() if v is not None}
        if not filtered:
            return {}
        encoded = base64.b64encode(json.dumps(filtered).encode()).decode()
        return {"X-Context-Properties": encoded}

    @staticmethod
    def _safe_json(response):
        try:
            return response.json()
        except Exception:
            return None
