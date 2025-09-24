from __future__ import annotations

"""
Pluggable virus scanning service. Default: no-op or HTTP AV API.
"""

from typing import Optional

import httpx


class VirusScanResult:
    def __init__(self, infected: bool, reason: Optional[str] = None) -> None:
        self.infected = infected
        self.reason = reason


class VirusScanner:
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.api_url = api_url
        self.api_key = api_key

    async def scan_bytes(self, content: bytes) -> VirusScanResult:
        if not self.api_url:
            return VirusScanResult(infected=False)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.api_url, headers=headers, files={"file": ("upload.bin", content)})
            resp.raise_for_status()
            data = resp.json()
            infected = bool(data.get("infected", False))
            reason = data.get("reason")
            return VirusScanResult(infected=infected, reason=reason)


