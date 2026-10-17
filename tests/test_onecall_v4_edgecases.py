"""Offline edge cases for the v4 adapter using synthetic, non-live records."""

from copy import deepcopy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from pyopenweathermap import (
    RequestError, TooManyRequestsError, UnauthorizedError, create_owm_client,
)

FIXTURES = Path(__file__).parent / "fixtures" / "onecall_contract"
BASE = "https://api.openweathermap.org/data/4.0/onecall/"
KEY = "synthetic key &+only"
LAT, LON = 51.5, -0.1
FORECASTS = [
    ("timeline/1min", "minutely_forecast", "v4_minutely_synthetic.json", 60, 60),
    ("timeline/1h", "hourly_forecast", "v4_hourly_page1_synthetic.json", 48, 3600),
    ("timeline/1day", "daily_forecast", "v4_daily_synthetic.json", 8, 86400),
]
ENDPOINTS = ["current", *(case[0] for case in FORECASTS)]


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def row_for(endpoint):
    name = ("v4_current_synthetic.json" if endpoint == "current" else
            next(case[2] for case in FORECASTS if case[0] == endpoint))
    return fixture(name)["data"][0]


def rows_for(endpoint, offsets, interval):
    template = row_for(endpoint)
    return [dict(deepcopy(template), dt=template["dt"] + i * interval)
            for i in offsets]


def stub_api(monkeypatch, pages=None, version="v4.0"):
    """Unexpected requests fail instead of returning an endlessly reusable page."""
    pages = pages or {}
    client = create_owm_client(KEY, version, units="imperial", lang="fr")
    calls = []
    used = {}

    async def request(url):
        calls.append(url)
        path = urlsplit(url).path
        if version == "v3.0":
            endpoint = "combined"
            assert path == "/data/3.0/onecall"
        else:
            prefix = "/data/4.0/onecall/"
            assert path.startswith(prefix)
            endpoint = path[len(prefix):]
            assert endpoint in ENDPOINTS
        index = used.get(endpoint, 0)
        used[endpoint] = index + 1
        available = pages.get(endpoint, [{"data": []}])
        assert index < len(available), f"Unexpected extra request to {endpoint}"
        payload = available[index]
        if isinstance(payload, Exception):
            raise payload
        return deepcopy(payload)

    monkeypatch.setattr(client.http_client, "request", request)
    return client, calls


def endpoint_calls(calls, endpoint):
    return [url for url in calls if urlsplit(url).path.endswith("/" + endpoint)]


UNSAFE_NEXT = [
    "http://api.openweathermap.org/data/4.0/onecall/timeline/1h?start=1",
    "//api.openweathermap.org/data/4.0/onecall/timeline/1h?start=1",
    "/data/4.0/onecall/timeline/1h?start=1",
    "?start=1",
    "https://example.invalid/data/4.0/onecall/timeline/1h?start=1",
    "https://api.openweathermap.org.example.invalid/data/4.0/onecall/timeline/1h",
    "https://api.openweathermap.org@example.invalid/data/4.0/onecall/timeline/1h",
    "https://user@api.openweathermap.org/data/4.0/onecall/timeline/1h",
    "https://api.openweathermap.org:8443/data/4.0/onecall/timeline/1h",
    BASE + "current?start=1",
    BASE + "timeline/1min?start=1",
    BASE + "timeline/1h/../1day?start=1",
    BASE + "timeline/1h%2f..%2f1day?start=1",
    BASE + "timeline/1h?start=1#fragment",
    "https://[malformed/data/4.0/onecall/timeline/1h",
    42, False, [], {},
]


@pytest.mark.parametrize("next_link", UNSAFE_NEXT)
@pytest.mark.asyncio
async def test_unsafe_or_malformed_next_is_rejected_before_request(monkeypatch, next_link):
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")], "next": next_link},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(endpoint_calls(calls, "timeline/1h")) == 1
    assert not endpoint_calls(calls, "timeline/1day")
    assert all(urlsplit(url).netloc == "api.openweathermap.org" for url in calls)


@pytest.mark.parametrize("next_query", [
    "start=1780304400",
    "start=1780304400&units=standard&lang=de&lat=0&lon=0&appid=wrong&appid=other",
])
@pytest.mark.asyncio
async def test_next_preserves_caller_location_key_units_and_language(monkeypatch, next_query):
    rows = rows_for("timeline/1h", range(2), 3600)
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": rows[:1], "next": BASE + "timeline/1h?" + next_query},
        {"data": rows[1:]},
    ]})
    report = await client.get_weather(LAT, LON)
    assert len(report.hourly_forecast) == 2
    assert len(endpoint_calls(calls, "timeline/1h")) == 2
    for url in calls:
        query = parse_qs(urlsplit(url).query)
        assert {name: query[name] for name in ("lat", "lon", "appid", "units", "lang")} == {
            "lat": [str(LAT)], "lon": [str(LON)], "appid": [KEY],
            "units": ["imperial"], "lang": ["fr"],
        }
    assert parse_qs(urlsplit(endpoint_calls(calls, "timeline/1h")[1]).query)["start"] == ["1780304400"]


@pytest.mark.parametrize("endpoint,attribute,name,count,interval", FORECASTS)
@pytest.mark.parametrize("next_value", [None, ""])
@pytest.mark.asyncio
async def test_short_pages_return_available_rows(monkeypatch, endpoint, attribute, name,
                                                count, interval, next_value):
    client, calls = stub_api(monkeypatch, {endpoint: [
        {"data": rows_for(endpoint, range(2), interval), "next": next_value},
    ]})
    report = await client.get_weather(LAT, LON)
    assert len(getattr(report, attribute)) == 2
    assert len(endpoint_calls(calls, endpoint)) == 1


@pytest.mark.asyncio
async def test_missing_next_finishes_without_inventing_another_page(monkeypatch):
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")]},
    ]})
    report = await client.get_weather(LAT, LON)
    assert len(report.hourly_forecast) == 1
    assert len(calls) == 4


@pytest.mark.asyncio
async def test_empty_envelopes_are_optional_and_do_not_follow_next(monkeypatch):
    client, calls = stub_api(monkeypatch, {
        endpoint: [{"data": [], "next": BASE + endpoint + "?start=1"}]
        for endpoint in ENDPOINTS
    })
    report = await client.get_weather(LAT, LON)
    assert report.current is None
    assert report.minutely_forecast == report.hourly_forecast == report.daily_forecast == []
    assert len(calls) == 4


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("payload", [
    None, [], {}, {"data": None}, {"data": {}}, {"data": "bad"},
    {"data": [None]}, {"data": [[]]}, {"data": ["bad"]}, {"data": [{}]},
])
@pytest.mark.asyncio
async def test_malformed_envelope_or_record_raises_request_error(monkeypatch, endpoint, payload):
    client, calls = stub_api(monkeypatch, {endpoint: [payload]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(calls) == ENDPOINTS.index(endpoint) + 1


@pytest.mark.parametrize("endpoint,attribute,name,count,interval", FORECASTS)
@pytest.mark.parametrize("timestamp", [None, True, False, 1780300800.5, "1780300800", []])
@pytest.mark.asyncio
async def test_invalid_forecast_timestamps_raise_request_error(
        monkeypatch, endpoint, attribute, name, count, interval, timestamp):
    row = row_for(endpoint)
    row["dt"] = timestamp
    client, _ = stub_api(monkeypatch, {endpoint: [{"data": [row]}]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)


@pytest.mark.asyncio
async def test_malformed_following_page_is_not_silently_returned_as_partial_report(monkeypatch):
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")], "next": BASE + "timeline/1h?start=2"},
        {"unexpected": []},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(endpoint_calls(calls, "timeline/1h")) == 2


@pytest.mark.asyncio
async def test_overlapping_and_duplicate_rows_are_deduplicated_in_time_order(monkeypatch):
    rows = rows_for("timeline/1h", range(4), 3600)
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [rows[0], rows[0], rows[1]], "next": BASE + "timeline/1h?start=2"},
        {"data": [rows[0], rows[1], rows[2], rows[2], rows[3]]},
    ]})
    report = await client.get_weather(LAT, LON)
    assert [int(row.date_time.timestamp()) for row in report.hourly_forecast] == [row["dt"] for row in rows]
    assert len(endpoint_calls(calls, "timeline/1h")) == 2


@pytest.mark.asyncio
async def test_out_of_order_page_is_rejected(monkeypatch):
    client, _ = stub_api(monkeypatch, {"timeline/1h": [
        {"data": rows_for("timeline/1h", [1, 0], 3600)},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)


@pytest.mark.asyncio
async def test_reordered_query_cycle_is_detected_before_request(monkeypatch):
    query = {"lang": "fr", "units": "imperial", "appid": KEY, "lon": LON, "lat": LAT}
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")], "next": BASE + "timeline/1h?" + urlencode(query)},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(endpoint_calls(calls, "timeline/1h")) == 1


@pytest.mark.asyncio
async def test_longer_pagination_cycle_is_bounded(monkeypatch):
    rows = rows_for("timeline/1h", range(3), 3600)
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [rows[0]], "next": BASE + "timeline/1h?start=1"},
        {"data": [rows[1]], "next": BASE + "timeline/1h?start=2"},
        {"data": [rows[2]], "next": BASE + "timeline/1h?start=1"},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(endpoint_calls(calls, "timeline/1h")) == 3


@pytest.mark.asyncio
async def test_nonprogressing_page_cannot_keep_requesting_new_links(monkeypatch):
    row = row_for("timeline/1h")
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row], "next": BASE + "timeline/1h?start=1"},
        {"data": [row], "next": BASE + "timeline/1h?start=2"},
    ]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)
    assert len(endpoint_calls(calls, "timeline/1h")) == 2


@pytest.mark.parametrize("endpoint,attribute,name,count,interval", FORECASTS)
@pytest.mark.parametrize("page_size", [1, 100])
@pytest.mark.asyncio
async def test_forecast_count_caps_bound_rows_and_requests(
        monkeypatch, endpoint, attribute, name, count, interval, page_size):
    rows = rows_for(endpoint, range(count + 4), interval)
    pages = [{"data": rows[i:i + page_size], "next": BASE + endpoint + f"?start={i + page_size}"}
             for i in range(0, len(rows), page_size)]
    client, calls = stub_api(monkeypatch, {endpoint: pages})
    report = await client.get_weather(LAT, LON)
    actual = getattr(report, attribute)
    assert len(actual) == count
    assert [int(row.date_time.timestamp()) for row in actual] == [row["dt"] for row in rows[:count]]
    assert len(endpoint_calls(calls, endpoint)) == (count + page_size - 1) // page_size


@pytest.mark.parametrize("endpoint,attribute,name,count,interval", FORECASTS)
@pytest.mark.asyncio
async def test_sparse_forecasts_stop_at_time_horizon_even_before_count_cap(
        monkeypatch, endpoint, attribute, name, count, interval):
    rows = rows_for(endpoint, [0, count - 1, count, count + 1], interval)
    client, calls = stub_api(monkeypatch, {endpoint: [
        {"data": rows[:1], "next": BASE + endpoint + "?start=2"},
        {"data": rows[1:], "next": BASE + endpoint + "?start=3"},
    ]})
    report = await client.get_weather(LAT, LON)
    assert [int(row.date_time.timestamp()) for row in getattr(report, attribute)] == [row["dt"] for row in rows[:2]]
    assert len(endpoint_calls(calls, endpoint)) == 2


@pytest.mark.parametrize("field", ["rain", "snow"])
@pytest.mark.parametrize("value", [0, 2, 0.0, 2.4, 10 ** 400])
@pytest.mark.asyncio
async def test_numeric_daily_precipitation_totals_are_preserved(monkeypatch, field, value):
    row = row_for("timeline/1day")
    row[field] = value
    client, _ = stub_api(monkeypatch, {"timeline/1day": [{"data": [row]}]})
    report = await client.get_weather(LAT, LON)
    assert getattr(report.daily_forecast[0], field) == value


@pytest.mark.asyncio
async def test_absent_daily_precipitation_defaults_to_zero(monkeypatch):
    row = row_for("timeline/1day")
    row.pop("rain", None)
    row.pop("snow", None)
    client, _ = stub_api(monkeypatch, {"timeline/1day": [{"data": [row]}]})
    report = await client.get_weather(LAT, LON)
    assert report.daily_forecast[0].rain == report.daily_forecast[0].snow == 0


@pytest.mark.parametrize("field", ["rain", "snow"])
@pytest.mark.parametrize("value", [
    {"1h": 0.4}, {}, [], True, False, None, -1, -0.5, "2.4", float("nan"), float("inf"),
])
@pytest.mark.asyncio
async def test_invalid_daily_precipitation_is_not_mislabeled_as_daily_total(
        monkeypatch, field, value):
    row = row_for("timeline/1day")
    row[field] = value
    client, _ = stub_api(monkeypatch, {"timeline/1day": [{"data": [row]}]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)


@pytest.mark.asyncio
async def test_reference_daily_precipitation_object_variant_is_rejected(monkeypatch):
    payload = fixture("v4_daily_precipitation_reference_variant.json")
    client, _ = stub_api(monkeypatch, {"timeline/1day": [payload]})
    with pytest.raises(RequestError):
        await client.get_weather(LAT, LON)


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("error_type", [RequestError, UnauthorizedError, TooManyRequestsError])
@pytest.mark.asyncio
async def test_request_errors_propagate_without_remaining_endpoint_requests(
        monkeypatch, endpoint, error_type):
    expected = error_type("synthetic service failure")
    client, calls = stub_api(monkeypatch, {endpoint: [expected]})
    with pytest.raises(error_type) as error:
        await client.get_weather(LAT, LON)
    assert error.value is expected
    assert len(calls) == ENDPOINTS.index(endpoint) + 1


@pytest.mark.parametrize("version", ["v3.0", "v4.0"])
@pytest.mark.parametrize("failure", [None, UnauthorizedError, RequestError, TooManyRequestsError])
@pytest.mark.asyncio
async def test_validate_key_uses_version_endpoint_and_only_swallows_unauthorized(
        monkeypatch, version, failure):
    endpoint = "current" if version == "v4.0" else "combined"
    response = {} if failure is None else failure("synthetic failure")
    client, calls = stub_api(monkeypatch, {endpoint: [response]}, version=version)
    if failure is None or failure is UnauthorizedError:
        assert await client.validate_key() is (failure is None)
    else:
        with pytest.raises(failure) as error:
            await client.validate_key()
        assert error.value is response
    assert len(calls) == 1
    parts = urlsplit(calls[0])
    expected_path = "/data/4.0/onecall/current" if version == "v4.0" else "/data/3.0/onecall"
    assert parts.path == expected_path
    query = parse_qs(parts.query)
    assert query["appid"] == [KEY]
    assert query["units"] == ["imperial"]
    assert query["lang"] == ["fr"]
    if version == "v4.0":
        assert "exclude" not in query
    else:
        assert query["exclude"] == ["current,minutely,hourly,daily,alerts"]


@pytest.mark.asyncio
async def test_empty_later_page_finishes_with_preceding_records(monkeypatch):
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")], "next": BASE + "timeline/1h?start=2"},
        {"data": [], "next": BASE + "timeline/1h?start=3"},
    ]})
    report = await client.get_weather(LAT, LON)
    assert len(report.hourly_forecast) == 1
    assert len(endpoint_calls(calls, "timeline/1h")) == 2


@pytest.mark.parametrize("error_type", [RequestError, UnauthorizedError, TooManyRequestsError])
@pytest.mark.asyncio
async def test_paginated_request_error_is_propagated_without_partial_success(monkeypatch, error_type):
    expected = error_type("synthetic second-page failure")
    client, calls = stub_api(monkeypatch, {"timeline/1h": [
        {"data": [row_for("timeline/1h")], "next": BASE + "timeline/1h?start=2"},
        expected,
    ]})
    with pytest.raises(error_type) as error:
        await client.get_weather(LAT, LON)
    assert error.value is expected
    assert len(endpoint_calls(calls, "timeline/1h")) == 2
    assert not endpoint_calls(calls, "timeline/1day")


@pytest.mark.parametrize("error_type", [RequestError, UnauthorizedError, TooManyRequestsError])
@pytest.mark.asyncio
async def test_v3_weather_request_errors_still_propagate(monkeypatch, error_type):
    expected = error_type("synthetic v3 failure")
    client, calls = stub_api(monkeypatch, {"combined": [expected]}, version="v3.0")
    with pytest.raises(error_type) as error:
        await client.get_weather(LAT, LON)
    assert error.value is expected
    assert len(calls) == 1
