"""Shared test fixtures for CLI tests."""

import asyncio
import os
import random
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from balatrobot.cli.client import BalatroClient
from balatrobot.config import ENV_MAP, Config
from balatrobot.manager import BalatroInstance

# ============================================================================
# Constants
# ============================================================================

HOST = "127.0.0.1"

# Files that contain tests requiring a real Balatro instance.
INTEGRATION_FILES = {
    "test_client.py",
    "test_api_cmd.py",
    "test_integration.py",
}


# ============================================================================
# Pytest Hooks for Integration Marking
# ============================================================================


def pytest_collection_modifyitems(items):
    """Mark integration test files automatically."""
    current_dir = Path(__file__).parent

    for item in items:
        # Only process items in this directory
        if (
            current_dir not in Path(item.path).parents
            and Path(item.path).parent != current_dir
        ):
            continue

        # Mark files that need Balatro as integration tests
        if item.path.name in INTEGRATION_FILES:
            item.add_marker(pytest.mark.integration)


# ============================================================================
# Session-scoped Fixtures for Integration Tests
# ============================================================================


@pytest.fixture(scope="session")
def cli_instance(worker_id):
    """Start a Balatro instance only for tests that request CLI API access.

    Previously this conftest started Balatro in pytest_configure for every
    tests/cli invocation, including pure unit tests such as test_play_helpers.py.
    Keeping startup behind this fixture lets non-integration CLI tests collect
    and run without a local game process.
    """
    port = random.randint(20000, 30000)
    os.environ["BALATROBOT_CLI_PORTS"] = str(port)

    base_config = Config.from_env()
    instance = BalatroInstance(base_config, port=port)

    async def start():
        await instance.start()

    async def stop():
        await instance.stop()

    try:
        asyncio.run(start())
        print(f"CLI test Balatro instance started on port: {port} ({worker_id})")
        yield instance
    finally:
        try:
            asyncio.run(stop())
        except Exception as e:
            print(f"Error stopping Balatro instance on port {port}: {e}")


@pytest.fixture(scope="session")
def cli_port(cli_instance) -> int:
    """Get the port for the lazily-started CLI Balatro instance."""
    return cli_instance.port


@pytest.fixture
def balatro_client(cli_port: int) -> BalatroClient:
    """Create BalatroClient connected to test server."""
    return BalatroClient(host=HOST, port=cli_port)


# ============================================================================
# Existing Fixtures (Mocks)
# ============================================================================


@pytest.fixture
def clean_env(monkeypatch):
    """Clear all BALATROBOT_* env vars for clean tests."""
    for env_var in ENV_MAP.values():
        monkeypatch.delenv(env_var, raising=False)
    yield


@pytest.fixture
def mock_popen(monkeypatch):
    """Mock subprocess.Popen for lifecycle tests."""
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.terminate = MagicMock()
    mock_process.kill = MagicMock()
    mock_process.wait = MagicMock(return_value=0)

    mock_popen_cls = MagicMock(return_value=mock_process)
    monkeypatch.setattr("subprocess.Popen", mock_popen_cls)

    return mock_process


@pytest.fixture
def mock_httpx_success(monkeypatch):
    """Mock httpx.AsyncClient returning successful health response."""

    async def mock_post(*args, **kwargs):
        response = MagicMock()
        response.json.return_value = {"result": {"status": "ok"}}
        return response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    mock_async_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

    return mock_client


@pytest.fixture
def mock_httpx_fail(monkeypatch):
    """Mock httpx.AsyncClient always raising ConnectionError."""
    import httpx

    async def mock_post(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    mock_async_client = MagicMock(return_value=mock_client)
    monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

    return mock_client
