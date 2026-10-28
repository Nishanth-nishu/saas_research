import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from common import RAW_COLUMNS  # noqa: E402


@pytest.fixture
def make_row():
    def _make(**kw):
        row = {c: "" for c in RAW_COLUMNS}
        row.update(company_name="Acme Freight Pvt Ltd", website="https://www.acmefreight.in/",
                   country="India", segment="B_documents_logistics", niche="freight forwarder",
                   fit_evidence="Freight forwarding services page", fit_evidence_url="https://acmefreight.in/services",
                   verification_status="verified")
        row.update(kw)
        return row
    return _make


@pytest.fixture
def frame(make_row):
    def _frame(*rows):
        return pd.DataFrame(list(rows))
    return _frame
