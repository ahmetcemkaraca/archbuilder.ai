from __future__ import annotations

"""
Storage service for temp/persistent file handling and chunked uploads.
"""

import os
from pathlib import Path
from typing import BinaryIO


class StorageService:
    def __init__(self, temp_dir: str = "./.tmp", data_dir: str = "./data", max_size_mb: int = 200, allowed_types: tuple[str, ...] = ("application/pdf", "application/octet-stream")) -> None:
        self.temp_dir = Path(temp_dir)
        self.data_dir = Path(data_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.allowed_types = allowed_types

    def write_chunk(self, upload_id: str, chunk_index: int, content: bytes) -> Path:
        folder = self.temp_dir / upload_id
        folder.mkdir(parents=True, exist_ok=True)
        part = folder / f"part-{chunk_index:05d}.bin"
        part.write_bytes(content)
        return part

    def assemble(self, upload_id: str, filename: str) -> Path:
        folder = self.temp_dir / upload_id
        if not folder.exists():
            raise FileNotFoundError("Upload not found")
        target = self.data_dir / filename
        with target.open("wb") as out:
            for part in sorted(folder.glob("part-*.bin")):
                out.write(part.read_bytes())
        # Size validation (MB)
        if target.stat().st_size > self.max_size_mb * 1024 * 1024:
            target.unlink(missing_ok=True)
            raise ValueError("File exceeds size limit")
        # Optionally cleanup
        for part in folder.glob("part-*.bin"):
            try:
                part.unlink()
            except OSError:
                pass
        try:
            folder.rmdir()
        except OSError:
            pass
        return target


