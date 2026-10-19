import httpx
import pytest

from novo_f1.config.settings import Settings, load_settings
from novo_f1.ingestion.client import OpenF1Client

BASE = "https://api.test/v1"


def make_client(handler, **overrides):
    settings = Settings(
        base_url=BASE, max_retries=2, min_request_interval=0, **overrides
    )
    sleeps: list[float] = []
    client = OpenF1Client(
        settings,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=sleeps.append,
    )
    return client, sleeps


def test_get_builds_url_with_operators_and_returns_records():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=[{"lap_number": 8}])

    client, _ = make_client(handler)

    result = client.get("laps", {"session_key": 9161, "lap_number>=": 8})

    assert result == [{"lap_number": 8}]
    # O httpx percent-encoda o operador; a OpenF1 aceita as duas formas.
    assert seen == [f"{BASE}/laps?session_key=9161&lap_number%3E=8"]


def test_build_url_without_filters():
    client, _ = make_client(lambda request: httpx.Response(200, json=[]))

    assert client.build_url("/meetings/", {}) == f"{BASE}/meetings"


def test_get_returns_empty_list_on_404():
    client, _ = make_client(
        lambda request: httpx.Response(404, json={"detail": "No results found."})
    )

    assert client.get("laps", {"session_key": 1}) == []


def test_get_wraps_single_object_in_list():
    client, _ = make_client(lambda request: httpx.Response(200, json={"a": 1}))

    assert client.get("x") == [{"a": 1}]


def test_get_retries_on_429_and_5xx_with_exponential_backoff():
    responses = iter(
        [httpx.Response(429), httpx.Response(503), httpx.Response(200, json=[{}])]
    )
    client, sleeps = make_client(lambda request: next(responses))

    assert client.get("laps") == [{}]
    assert sleeps == [1.0, 2.0]
    assert client.request_count == 3


def test_get_honours_retry_after_header():
    responses = iter(
        [
            httpx.Response(429, headers={"Retry-After": "5"}),
            httpx.Response(200, json=[]),
        ]
    )
    client, sleeps = make_client(lambda request: next(responses))

    client.get("laps")

    assert sleeps == [5.0]


def test_get_raises_after_exhausting_retries():
    client, sleeps = make_client(lambda request: httpx.Response(500))

    with pytest.raises(httpx.HTTPStatusError):
        client.get("laps")
    assert len(sleeps) == 2


def test_get_does_not_retry_client_errors():
    client, sleeps = make_client(lambda request: httpx.Response(400))

    with pytest.raises(httpx.HTTPStatusError):
        client.get("laps")
    assert sleeps == []


def test_get_retries_transport_errors_then_raises():
    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    client, sleeps = make_client(handler)

    with pytest.raises(httpx.ConnectError):
        client.get("laps")
    assert len(sleeps) == 2


def test_token_header_only_when_configured():
    headers: list[str | None] = []

    def handler(request):
        headers.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=[])

    anonymous, _ = make_client(handler)
    authed, _ = make_client(handler, api_token="segredo-ficticio")

    anonymous.get("laps")
    authed.get("laps")

    assert headers == [None, "Bearer segredo-ficticio"]


def test_throttle_waits_minimum_interval():
    sleeps: list[float] = []
    ticks = iter([0.0, 0.1, 0.6])
    client = OpenF1Client(
        Settings(base_url=BASE, min_request_interval=0.5),
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
        ),
        sleep=sleeps.append,
        clock=lambda: next(ticks),
    )

    client.get("a")
    client.get("b")
    client.close()

    assert sleeps == [pytest.approx(0.4)]


def test_load_settings_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENF1_BASE_URL", "https://example.test/v1/")
    monkeypatch.setenv("OPENF1_API_TOKEN", "")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MAX_RETRIES", "5")

    settings = load_settings()

    assert settings.base_url == "https://example.test/v1"
    assert settings.api_token is None
    assert settings.data_dir == tmp_path
    assert settings.max_retries == 5
