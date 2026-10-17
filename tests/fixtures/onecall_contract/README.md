# One Call contract fixtures

Every JSON file here is **synthetic**. Values, coordinates, timestamps, weather,
IDs, messages, and pagination links are test inputs, not captured API responses.
`fixture-not-a-key` is deliberately nonfunctional. No account or credential was
read and no authenticated OpenWeather call was made to produce these fixtures.

## Provenance and intent

- `v3_combined_synthetic.json`: combined 3.0 section/field contract with one
  current, minute, hour, and day record; regression coverage for legacy parsing.
- `v4_current_synthetic.json`, `v4_minutely_synthetic.json`: dedicated endpoint
  `data` envelopes. Minute data is intentionally a three-record excerpt.
- `v4_hourly_page{1,2,3}_synthetic.json`: 48 consecutive hourly records in pages
  of 20, 20, and 8. Links use `start` and a nonfunctional test key.
- `v4_daily_synthetic.json`: eight days preserving the legacy forecast horizon.
  Scalar daily precipitation follows the migration guide; missing optional
  fields exercise converter defaults.
- `v4_daily_precipitation_reference_variant.json`: follows the conflicting
  reference's daily `rain.1h`/`snow.1h` shape. The v4 adapter deliberately raises
  `RequestError` because an hourly rate cannot be treated as a daily total.
  This does not resolve which shape the live service uses.
- `http_errors_synthetic.json`: 400/401/404/429 bodies in the documented error
  envelope shape, used to exercise local HTTP exception mapping.

## Primary sources (checked 2026-10-13)

- [3.0 combined contract](https://openweathermap.org/api/one-call-3#how)
- [Migration checklist](https://openweathermap.org/api/one-call-3-migration#checklist)
- [Migration field mappings](https://openweathermap.org/api/one-call-3-migration#current)
- [4.0 current response](https://openweathermap.org/api/one-call-4#example)
- [4.0 minute response](https://openweathermap.org/api/one-call-4#min_example)
- [4.0 hourly limit](https://openweathermap.org/api/one-call-4#hourly_example)
- [4.0 daily response/limit](https://openweathermap.org/api/one-call-4#daily_example)
- [4.0 pagination](https://openweathermap.org/api/one-call-4#pagination)
- Conflicting daily precipitation descriptions:
  [migration guide](https://openweathermap.org/api/one-call-3-migration#daily)
  versus [reference fields](https://openweathermap.org/api/one-call-4#daily_parameter)
- [4.0 error structure](https://openweathermap.org/api/one-call-4#errors)

## Run offline

Use Python 3.11+ and the repository's Poetry dependencies:

```sh
poetry install
poetry run pytest
```

Equivalent with test dependencies installed into a virtual environment:

```sh
PYTHONPATH=src python -m pytest -q -m 'not network'
```

The five former strict-xfail acceptance cases now pass without xfail markers.
They cover current/minute/hour/day envelopes and the separate endpoint +
pagination flow. Obsolete characterization assertions for the broken bare
4.0 endpoint have been replaced with working-contract assertions. Edge tests
cover malformed/empty pages, failures, bounded horizons, safe pagination,
optional fields, and explicit rejection of ambiguous daily precipitation.
Default tests and CI are offline; live tests require `-m network` explicitly.
The fixtures establish local behavior only, not authenticated API or Home
Assistant integration evidence.
