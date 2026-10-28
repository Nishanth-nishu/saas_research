import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leadpilot.config import load_settings  # noqa: E402
from leadpilot.db import connect, init_db  # noqa: E402
from leadpilot.services import orgs  # noqa: E402

T0 = datetime(2026, 10, 28, 6, 0, tzinfo=timezone.utc)


@pytest.fixture
def settings(tmp_path):
    return load_settings(db_path=str(tmp_path / "test.db"), secret_key="test-secret", tick_seconds=0,
                         anthropic_key="", wa_access_token="", wa_verify_token="verify-me", wa_app_secret="")


@pytest.fixture
def conn(settings):
    c = connect(settings.db_path)
    init_db(c)
    return c


@pytest.fixture
def org(conn):
    org_id, admin_id = orgs.create_org(conn, "Sky Overseas", "Asha Admin", "asha@sky.test", "password123")
    c1 = orgs.add_user(conn, org_id, "Ravi", "ravi@sky.test", "password123")
    c2 = orgs.add_user(conn, org_id, "Meena", "meena@sky.test", "password123")
    return {"id": org_id, "admin": admin_id, "c1": c1, "c2": c2}


@pytest.fixture
def client(settings):
    from fastapi.testclient import TestClient
    from leadpilot.web import create_app
    with TestClient(create_app(settings)) as c:
        yield c


def csrf_of(html: str) -> str:
    m = re.search(r'name="csrf" value="([^"]+)"', html)
    assert m, "no csrf token on page"
    return m.group(1)
