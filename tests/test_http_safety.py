"""Credential logging and redirect safety, with all HTTP sessions mocked."""

import logging
import traceback
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import parse_qs, urlsplit

import pytest
from aiohttp import ClientConnectionError, ContentTypeError

from pyopenweathermap import RequestError, TooManyRequestsError, UnauthorizedError
from pyopenweathermap.http_client import HttpClient


def stub_session(monkeypatch, status=200, body=None):
    response = MagicMock(status=status)
    response.json = AsyncMock(return_value={} if body is None else body)
    response.__aenter__.return_value = response
    session = MagicMock()
    session.__aenter__.return_value = session
    session.get.return_value = response
    monkeypatch.setattr("pyopenweathermap.http_client.ClientSession", MagicMock(return_value=session))
    return session, response


@pytest.mark.asyncio
async def test_debug_logs_redact_every_appid_but_request_keeps_original_url(monkeypatch, caplog):
    session, _ = stub_session(monkeypatch, body={"data": []})
    url = ("https://api.openweathermap.org/data/4.0/onecall/current?"
           "lat=51.5&appid=secret-one&lon=-0.1&appid=secret%2Btwo&units=imperial&lang=fr")
    with caplog.at_level(logging.DEBUG, logger="pyopenweathermap.http_client"):
        assert await HttpClient(request_timeout=7).request(url) == {"data": []}
    session.get.assert_called_once_with(url=url, timeout=7, allow_redirects=False)
    assert "secret-one" not in caplog.text
    assert "secret%2Btwo" not in caplog.text
    assert "secret+two" not in caplog.text
    request_logs = [record.getMessage() for record in caplog.records if "Requesting url:" in record.getMessage()]
    assert len(request_logs) == 1
    logged_url = request_logs[0].split("Requesting url: ", 1)[1]
    query = parse_qs(urlsplit(logged_url).query)
    assert query["appid"] == ["[redacted]", "[redacted]"]
    assert query["units"] == ["imperial"]
    assert query["lang"] == ["fr"]


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.asyncio
async def test_redirects_are_disabled_and_never_treated_as_success(monkeypatch, status):
    session, response = stub_session(monkeypatch, status=status)
    response.headers = {"Location": "https://example.invalid/collect-key"}
    url = "https://api.openweathermap.org/data/4.0/onecall/current?appid=synthetic-key"
    with pytest.raises(RequestError):
        await HttpClient().request(url)
    session.get.assert_called_once_with(url=url, timeout=20, allow_redirects=False)


@pytest.mark.asyncio
async def test_timeout_is_mapped_to_request_error(monkeypatch):
    _, response = stub_session(monkeypatch)
    response.__aenter__.side_effect = TimeoutError()
    with pytest.raises(RequestError, match="Request timeout"):
        await HttpClient().request("https://example.invalid/offline")


@pytest.mark.parametrize("failure_kind", ["invalid-json", "content-type"])
@pytest.mark.parametrize("status,error_type", [
    (200, RequestError), (400, RequestError), (401, UnauthorizedError),
    (404, RequestError), (429, TooManyRequestsError), (500, RequestError),
])
@pytest.mark.asyncio
async def test_non_json_responses_keep_status_mapping_without_leaking_credentials(
        monkeypatch, failure_kind, status, error_type):
    _, response = stub_session(monkeypatch, status=status)
    secret = "synthetic-private-key"
    url = "https://example.invalid/offline?appid=" + secret
    failure = (ValueError("Invalid JSON at " + url) if failure_kind == "invalid-json"
               else ContentTypeError(SimpleNamespace(real_url=url), (),
                                     status=status, message="Unexpected mimetype"))
    response.json.side_effect = failure
    with pytest.raises(error_type) as error:
        await HttpClient().request(url)
    assert type(error.value) is error_type
    assert secret not in str(error.value)
    assert secret not in "".join(traceback.format_exception(error.value))
    if status == 200:
        assert str(error.value) == "Invalid JSON response"
    else:
        assert str(status) in str(error.value)


@pytest.mark.parametrize("body", [None, [], "bad gateway", {"unrelated": "value"}])
@pytest.mark.parametrize("status,error_type", [(401, UnauthorizedError), (429, TooManyRequestsError), (503, RequestError)])
@pytest.mark.asyncio
async def test_http_error_without_message_keeps_status_mapping(monkeypatch, body, status, error_type):
    _, response = stub_session(monkeypatch, status=status)
    response.json.return_value = body
    with pytest.raises(error_type) as error:
        await HttpClient().request("https://example.invalid/offline")
    assert type(error.value) is error_type
    assert str(status) in str(error.value)


@pytest.mark.parametrize("error_type", [TimeoutError, ClientConnectionError, RuntimeError])
@pytest.mark.asyncio
async def test_transport_exception_text_and_chain_do_not_expose_key(monkeypatch, error_type, caplog):
    session, _ = stub_session(monkeypatch)
    secret = "synthetic-transport-secret"
    url = "https://example.invalid/offline?appid=" + secret
    session.get.side_effect = error_type("Request failed for " + url)
    with caplog.at_level(logging.DEBUG, logger="pyopenweathermap.http_client"):
        with pytest.raises(RequestError) as error:
            await HttpClient().request(url)
    assert secret not in str(error.value)
    assert secret not in "".join(traceback.format_exception(error.value))
    assert secret not in caplog.text
    session.get.assert_called_once_with(url=url, timeout=20, allow_redirects=False)
