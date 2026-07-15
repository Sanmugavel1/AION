"""
AION GitHub Connector — ingests commits, PRs, issues, code reviews
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.base_connector import BaseConnector, RawDocument
from app.core.logging import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubConnector(BaseConnector):
    source_name = "github"

    def __init__(self, org_id: str, credentials: dict[str, Any]) -> None:
        super().__init__(org_id, credentials)
        self._token = credentials.get("token")
        self._org = credentials.get("github_org")
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def authenticate(self) -> bool:
        if not self._token:
            return False
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{GITHUB_API}/user", headers=self._headers)
            self._authenticated = resp.status_code == 200
            return self._authenticated

    async def fetch_recent(self, since_hours: int = 6) -> list[RawDocument]:
        since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        docs = []
        async with httpx.AsyncClient(timeout=30) as client:
            # Fetch PRs
            docs += await self._fetch_prs(client, since)
            # Fetch issues
            docs += await self._fetch_issues(client, since)
        return docs

    async def _fetch_prs(self, client: httpx.AsyncClient, since: str) -> list[RawDocument]:
        docs = []
        if not self._org:
            return docs
        try:
            resp = await client.get(
                f"{GITHUB_API}/orgs/{self._org}/repos",
                headers=self._headers,
                params={"per_page": 50},
            )
            repos = resp.json() if resp.status_code == 200 else []
            for repo in repos[:20]:
                pr_resp = await client.get(
                    f"{GITHUB_API}/repos/{self._org}/{repo['name']}/pulls",
                    headers=self._headers,
                    params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 20},
                )
                if pr_resp.status_code != 200:
                    continue
                for pr in pr_resp.json():
                    if pr.get("updated_at", "") < since:
                        continue
                    docs.append(self._make_doc(
                        external_id=f"pr_{pr['id']}",
                        title=f"PR: {pr['title']}",
                        content=pr.get("body") or pr["title"],
                        author_name=pr["user"]["login"],
                        created_at=datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")),
                        url=pr["html_url"],
                        doc_type="pr",
                        tags=[repo["name"], "pull_request"],
                        metadata={"repo": repo["name"], "state": pr["state"], "number": pr["number"]},
                    ))
        except Exception as e:
            logger.warning("GitHub PR fetch failed", error=str(e))
        return docs

    async def _fetch_issues(self, client: httpx.AsyncClient, since: str) -> list[RawDocument]:
        docs = []
        if not self._org:
            return docs
        try:
            resp = await client.get(
                f"{GITHUB_API}/orgs/{self._org}/issues",
                headers=self._headers,
                params={"filter": "all", "state": "all", "since": since, "per_page": 50},
            )
            if resp.status_code != 200:
                return docs
            for issue in resp.json():
                if "pull_request" in issue:
                    continue  # skip PRs listed as issues
                docs.append(self._make_doc(
                    external_id=f"issue_{issue['id']}",
                    title=f"Issue: {issue['title']}",
                    content=issue.get("body") or issue["title"],
                    author_name=issue["user"]["login"],
                    created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")),
                    url=issue["html_url"],
                    doc_type="ticket",
                    tags=["github", "issue"],
                    metadata={"state": issue["state"], "labels": [l["name"] for l in issue.get("labels", [])]},
                ))
        except Exception as e:
            logger.warning("GitHub issue fetch failed", error=str(e))
        return docs

    async def fetch_all(self, limit: int = 1000) -> list[RawDocument]:
        return await self.fetch_recent(since_hours=24 * 90)
