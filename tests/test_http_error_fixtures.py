"""HTTP status mapping without credentials, sessions, or network requests."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyopenweathermap import RequestError, TooManyRequestsError, UnauthorizedError
from pyopenweathermap.http_client import HttpClient

CASES = json.loads((Path(__file__).parent / "fixtures" / "onecall_contract" /
                    "http_errors_synthetic.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda case: str(case["status"]))
@pytest.mark.asyncio
async def test_http_error_status_from_fixture(monkeypatch, case):
    response = MagicMock(status=case["status"])
    response.json = AsyncMock(return_value=case["body"])
    response.__aenter__.return_value = response
    session = MagicMock()
    session.__aenter__.return_value = session
    session.get.return_value = response
    constructor = MagicMock(return_value=session)
    monkeypatch.setattr("pyopenweathermap.http_client.ClientSession", constructor)
    expected = {400: RequestError, 401: UnauthorizedError,
                404: RequestError, 429: TooManyRequestsError}[case["status"]]

    with pytest.raises(expected) as error:
        await HttpClient().request("https://example.invalid/offline-fixture")

    assert type(error.value) is expected
    assert str(error.value) == case["body"]["message"]
    session.get.assert_called_once_with(
        url="https://example.invalid/offline-fixture", timeout=20, allow_redirects=False)
    response.json.assert_awaited_once()
