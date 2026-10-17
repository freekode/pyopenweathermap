"""Offline regression tests for the documented One Call 3.0/4.0 contracts."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest

from pyopenweathermap import create_owm_client
from pyopenweathermap.data_converter import DataConverter

FIXTURES = Path(__file__).parent / "fixtures" / "onecall_contract"
KEY = "fixture-not-a-key"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


def stub_client(monkeypatch, payload, version="v4.0"):
    client = create_owm_client(KEY, version)
    request = AsyncMock(return_value=payload)
    monkeypatch.setattr(client.http_client, "request", request)
    return client, request


@pytest.mark.parametrize("version", ["v3.0", "v4.0"])
def test_existing_url_preserves_request_options(version):
    client = create_owm_client(KEY, version, units="imperial", lang="fr")
    url = urlsplit(client._get_url(51.5, -0.1))
    assert url.scheme == "https"
    assert url.netloc == "api.openweathermap.org"
    suffix = "/current" if version == "v4.0" else ""
    assert url.path == f"/data/{version[1:]}/onecall{suffix}"
    assert parse_qs(url.query) == {
        "lat": ["51.5"], "lon": ["-0.1"], "appid": [KEY],
        "units": ["imperial"], "lang": ["fr"],
    }


@pytest.mark.asyncio
async def test_legacy_combined_envelope_regression(monkeypatch):
    payload = load_fixture("v3_combined_synthetic.json")
    client, request = stub_client(monkeypatch, payload, "v3.0")
    report = await client.get_weather(51.5, -0.1)
    request.assert_awaited_once_with(client._get_url(51.5, -0.1))
    assert report.current.date_time == datetime.fromtimestamp(1780300800, tz=UTC)
    assert report.current.temperature == 12.5
    assert report.current.rain == {"1h": 0.4}
    assert report.current.wind_gust is None
    assert report.current.snow is None
    assert report.minutely_forecast[0].precipitation == 0.4
    assert report.hourly_forecast[0].precipitation_probability == 0.6
    assert report.hourly_forecast[0].wind_gust == 5.0
    assert report.daily_forecast[0].temperature.min == 8.0
    assert report.daily_forecast[0].feels_like.min is None
    assert report.daily_forecast[0].summary is None
    assert report.daily_forecast[0].rain == 2.4
    assert report.daily_forecast[0].snow == 0


@pytest.mark.asyncio
async def test_missing_legacy_sections_remain_optional(monkeypatch):
    client, _ = stub_client(monkeypatch, {"current": None}, "v3.0")
    report = await client.get_weather(51.5, -0.1)
    assert report.current is None
    assert report.minutely_forecast == []
    assert report.hourly_forecast == []
    assert report.daily_forecast == []


@pytest.mark.parametrize("fixture,converter,field,expected", [
    ("v4_current_synthetic.json", DataConverter.onecall_to_current_weather,
     "temperature", 12.5),
    ("v4_minutely_synthetic.json", DataConverter.onecall_to_minutely_weather_forecast,
     "precipitation", 0.4),
    ("v4_hourly_page1_synthetic.json", DataConverter.onecall_to_hourly_weather_forecast,
     "precipitation_probability", 0.6),
    ("v4_daily_synthetic.json", DataConverter.onecall_to_daily_weather_forecast,
     "rain", 2.4),
])
def test_individual_records_can_reuse_converters(fixture, converter, field, expected):
    """The row-level field mappings remain compatible with legacy converters."""
    row = load_fixture(fixture)["data"][0]
    converted = converter(row)
    assert getattr(converted, field) == expected
    assert converted.date_time == datetime.fromtimestamp(row["dt"], tz=UTC)


def test_pagination_fixture_has_complete_48_hour_window():
    pages = [load_fixture(f"v4_hourly_page{n}_synthetic.json") for n in (1, 2, 3)]
    assert [len(page["data"]) for page in pages] == [20, 20, 8]
    rows = [row for page in pages for row in page["data"]]
    times = [row["dt"] for row in rows]
    assert len(set(times)) == 48
    assert all(b - a == 3600 for a, b in zip(times, times[1:]))
    for page, following in zip(pages, pages[1:]):
        assert int(parse_qs(urlsplit(page["next"]).query)["start"][0]) == following["data"][0]["dt"]
    assert "next" not in pages[-1]


def stub_documented_api(monkeypatch):
    """Serve separate endpoints and all three synthetic hourly pages."""
    client = create_owm_client(KEY, "v4.0")
    prefix = "/data/4.0/onecall"
    pages = [load_fixture(f"v4_hourly_page{n}_synthetic.json") for n in (1, 2, 3)]
    by_path = {
        prefix + "/current": load_fixture("v4_current_synthetic.json"),
        prefix + "/timeline/1min": load_fixture("v4_minutely_synthetic.json"),
        prefix + "/timeline/1h": pages[0],
        prefix + "/timeline/1day": load_fixture("v4_daily_synthetic.json"),
    }
    following_pages = {pages[0]["next"]: pages[1], pages[1]["next"]: pages[2]}
    calls = []

    async def request(url):
        calls.append(url)
        if url in following_pages:
            return following_pages[url]
        # An undocumented route must fail the test.
        return by_path[urlsplit(url).path]

    monkeypatch.setattr(client.http_client, "request", request)
    return client, calls, pages


@pytest.mark.asyncio
async def test_required_v4_current_envelope_parsing(monkeypatch):
    client, _, _ = stub_documented_api(monkeypatch)
    report = await client.get_weather(51.5, -0.1)
    assert report.current is not None
    assert report.current.temperature == 12.5


@pytest.mark.parametrize("attribute,count", [
    ("minutely_forecast", 3), ("hourly_forecast", 48), ("daily_forecast", 8),
])
@pytest.mark.asyncio
async def test_required_v4_forecast_envelope_parsing(monkeypatch, attribute, count):
    client, _, _ = stub_documented_api(monkeypatch)
    report = await client.get_weather(51.5, -0.1)
    assert len(getattr(report, attribute)) == count


@pytest.mark.asyncio
async def test_required_v4_endpoints_and_complete_forecast_horizon(monkeypatch):
    """Acceptance target: keep the legacy 48-hour/8-day WeatherReport contract."""
    client, calls, pages = stub_documented_api(monkeypatch)
    prefix = "/data/4.0/onecall"
    report = await client.get_weather(51.5, -0.1)
    assert {urlsplit(url).path for url in calls} == {
        prefix + "/current", prefix + "/timeline/1min",
        prefix + "/timeline/1h", prefix + "/timeline/1day",
    }
    assert report.current.temperature == 12.5
    assert len(report.minutely_forecast) == 3
    assert len(report.hourly_forecast) == 48
    assert len(report.daily_forecast) == 8
    assert pages[0]["next"] in calls
    assert pages[1]["next"] in calls
    assert len(calls) == 6
