from __future__ import annotations

import aiohttp


def make_session(*, user_agent: str, timeout_seconds: int) -> aiohttp.ClientSession:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    headers = {"User-Agent": user_agent}
    return aiohttp.ClientSession(timeout=timeout, headers=headers)


async def get_json(session: aiohttp.ClientSession, url: str, params: dict | None = None):
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()

