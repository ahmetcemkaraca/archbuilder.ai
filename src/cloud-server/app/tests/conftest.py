from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI

from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def app() -> FastAPI:
    return create_app()


