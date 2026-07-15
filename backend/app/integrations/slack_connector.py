"""
AION Slack Connector — ingests messages, threads, and shared knowledge
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.integrations.base_connector import BaseConnector, RawDocument
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from slack_sdk.web.async_client import AsyncWebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


class SlackConnector(BaseConnector):
    source_name = "slack"

    def __init__(self, org_id: str, credentials: dict[str, Any]) -> None:
        super().__init__(org_id, credentials)
        self._client = None
        self._channels: list[dict] = []

    async def authenticate(self) -> bool:
        if not SLACK_AVAILABLE:
            logger.warning("slack_sdk not installed, Slack connector disabled")
            return False
        token = self.credentials.get("bot_token")
        if not token:
            return False
        self._client = AsyncWebClient(token=token)
        try:
            resp = await self._client.auth_test()
            self._authenticated = resp.get("ok", False)
            logger.info("Slack authenticated", workspace=resp.get("team"))
            return self._authenticated
        except Exception as e:
            logger.warning("Slack auth failed", error=str(e))
            return False

    async def _list_channels(self) -> list[dict]:
        if not self._client:
            return []
        result = await self._client.conversations_list(types="public_channel,private_channel")
        return result.get("channels", [])

    async def fetch_recent(self, since_hours: int = 6) -> list[RawDocument]:
        if not self._client:
            return []
        docs = []
        oldest = str((datetime.now(timezone.utc) - timedelta(hours=since_hours)).timestamp())
        channels = await self._list_channels()
        for ch in channels[:50]:  # cap at 50 channels
            try:
                history = await self._client.conversations_history(
                    channel=ch["id"], oldest=oldest, limit=200
                )
                for msg in history.get("messages", []):
                    if not msg.get("text") or msg.get("subtype"):
                        continue
                    docs.append(self._make_doc(
                        external_id=f"{ch['id']}_{msg['ts']}",
                        title=f"Slack message in #{ch.get('name', 'unknown')}",
                        content=msg["text"],
                        created_at=datetime.fromtimestamp(float(msg["ts"]), tz=timezone.utc),
                        doc_type="message",
                        metadata={
                            "channel_id": ch["id"],
                            "channel_name": ch.get("name"),
                            "thread_ts": msg.get("thread_ts"),
                            "reply_count": msg.get("reply_count", 0),
                        },
                    ))
            except Exception as e:
                logger.debug("Failed to fetch Slack channel", channel=ch.get("name"), error=str(e))
        return docs

    async def fetch_all(self, limit: int = 1000) -> list[RawDocument]:
        return await self.fetch_recent(since_hours=24 * 30)  # last 30 days
