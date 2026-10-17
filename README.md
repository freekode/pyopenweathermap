# pyopenweathermap

Python library for OpenWeatherMap API for Home Assistant.

## One Call API

Use `create_owm_client(api_key, 'v3.0')` for the combined One Call 3.0
endpoint, or `create_owm_client(api_key, 'v4.0')` for the separate One Call 4.0
endpoints. Both accept `units` (default `metric`) and `lang` (default `en`),
and expose `await client.get_weather(lat, lon)` returning a `WeatherReport`.
The current/forecast 2.5 and air-pollution clients remain available.

The 4.0 adapter requests `current`, `timeline/1min`, `timeline/1h`, and
`timeline/1day`, then converts their `data` arrays to the existing report
models. It returns up to 60 minute records, 48 hourly records, and 8 daily
records. Missing optional weather fields keep the existing converter defaults;
empty data arrays produce empty report sections. Malformed envelopes/records
raise `RequestError`, and a failed endpoint/page fails the report rather than
silently returning partially refreshed weather.

### Pagination and request budget

A typical complete 4.0 report uses **six HTTP requests**: current, minutely,
three hourly pages (20 + 20 + 8 returned records), and daily. Each page is a
separate API call; check account entitlement and budget before enabling 4.0.
Short pages can require additional requests. The adapter follows `next` only
while it needs records within the requested count/time horizon, stops on an
empty page, removes overlapping records, and rejects repeated links or pages
that make no progress. Daily records are capped at eight; it does not fetch the
full longer-range 4.0 outlook. Requests are sequential and stop at the first
error. No automatic retry is performed.

Only HTTPS pagination links to the same OpenWeather host and timeline endpoint
are accepted. Client coordinates, key, units, and language are preserved on
all pages. HTTP redirects are not followed, and request URL debug logs redact
`appid`. `validate_key()` uses one 4.0 current request (or the legacy 3.0 key
validation call); authorization errors return `False`, and other request errors
are propagated.

### Daily precipitation caveat

The [migration guide](https://openweathermap.org/api/one-call-3-migration#daily)
describes 4.0 daily `rain` and `snow` as scalar daily totals in mm, while the
[reference](https://openweathermap.org/api/one-call-4#daily_parameter) also lists
hourly-shaped `rain.1h` and `snow.1h` objects. This adapter accepts nonnegative
numeric daily totals and defaults absent fields to zero. It raises a descriptive
`RequestError` for an object or other unsupported value. An hourly rate cannot
safely be labeled or multiplied into a daily total. The 3.0 converter behavior
is unchanged. Confirm this ambiguity with a sanitized live response before
claiming production validation.

Reference: [One Call 4.0 endpoints and pagination](https://openweathermap.org/api/one-call-4).
Weather alerts and 15-minute forecasts are outside the existing report model.

## Development and testing

Use Python 3.11+ and Poetry (`poetry install`). The project uses `poetry.lock`.
The default suite and CI are offline and do not require an API key:

```sh
poetry run pytest
poetry run pytest -m 'not network'
poetry build
```

Fixtures are synthetic, source-labeled contract examples, not recordings of
successful authenticated calls. Unmarked tests block socket connections and
DNS. Run credentialed smoke tests only when you have approved account access,
4.0 entitlement, and a request budget; they are explicitly opt-in:

```sh
# Supply OWM_API_KEY through your local environment, not source control.
poetry run pytest -m network
```

The existing skipped legacy smoke tests remain skipped. Offline tests establish
adapter behavior against the published contract; they do not verify an account's
entitlement, actual provider responses, Home Assistant integration, or deployment.
