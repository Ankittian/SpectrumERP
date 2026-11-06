import os
from pathlib import Path

import pytest

from spectrum_kg.build import build_graph
from spectrum_kg.config import load_settings

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def built(settings):
    return build_graph(settings)


@pytest.fixture(scope="session")
def graph(built):
    return built[0]


@pytest.fixture(scope="session")
def live_client(settings):
    if not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_PASSWORD"):
        pytest.skip("live: NEO4J_URI / NEO4J_PASSWORD not configured in .env")
    from spectrum_kg.queries import KGClient
    client = KGClient(settings)
    try:
        client.driver.verify_connectivity()
    except Exception as ex:  # pragma: no cover
        pytest.skip(f"live: Neo4j not reachable ({ex})")
    yield client
    client.close()
