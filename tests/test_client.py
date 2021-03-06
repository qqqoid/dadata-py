import pytest
from requests import HTTPError
from dadata.client import Dadata

dadata = Dadata("token", "secret")


def test_init():
    client = Dadata("token")
    assert client.session.headers["Authorization"] == "Token token"


def test_init_with_secret():
    client = Dadata("token", "secret")
    assert client.session.headers["Authorization"] == "Token token"
    assert client.session.headers["X-Secret"] == "secret"


def test_clean(requests_mock):
    expected = {"source": "Сережа", "result": "Сергей", "qc": 1}
    requests_mock.post("/api/v1/clean/name", json=[expected])
    actual = dadata.clean("name", "Сережа")
    assert actual == expected


def test_geolocate(requests_mock):
    expected = [
        {"value": "г Москва, ул Сухонская, д 11", "data": {"kladr_id": "7700000000028360004"}}
    ]
    requests_mock.post("/suggestions/api/4_1/rs/geolocate/address", json={"suggestions": expected})
    actual = dadata.geolocate(lat=55.8782557, lon=37.65372)
    assert actual == expected


def test_geolocate_params(requests_mock):
    def match_params(request):
        return (
            request.body == '{"lat": 55.8782557, "lon": 37.65372, "radius_meters": 200, "count": 5}'
        )

    requests_mock.post(
        "/suggestions/api/4_1/rs/geolocate/address",
        json={"suggestions": []},
        additional_matcher=match_params,
    )
    dadata.geolocate(lat=55.8782557, lon=37.65372, radius_meters=200, count=5)


def test_geolocate_not_found(requests_mock):
    expected = []
    requests_mock.post("/suggestions/api/4_1/rs/geolocate/address", json={"suggestions": expected})
    actual = dadata.geolocate(lat=1, lon=1)
    assert actual == expected


def test_iplocate(requests_mock):
    expected = {
        "value": "г Москва",
        "data": {"kladr_id": "7700000000000"},
    }
    requests_mock.get("/suggestions/api/4_1/rs/iplocate/address", json={"location": expected})
    actual = dadata.iplocate("212.45.30.108")
    assert actual == expected


def test_iplocate_not_found(requests_mock):
    requests_mock.get("/suggestions/api/4_1/rs/iplocate/address", json={"location": None})
    actual = dadata.iplocate("1.1.1.1")
    assert actual is None


def test_suggest(requests_mock):
    expected = [
        {"value": "г Москва, ул Сухонская", "data": {"kladr_id": "77000000000283600"}},
        {"value": "г Москва, ул Сухонская, д 1", "data": {"kladr_id": "7700000000028360009"}},
    ]
    requests_mock.post("/suggestions/api/4_1/rs/suggest/address", json={"suggestions": expected})
    actual = dadata.suggest("address", "мск сухонская")
    assert actual == expected


def test_suggest_params(requests_mock):
    def match_params(request):
        return request.body == '{"query": "samara", "count": 10, "to_bound": {"value": "city"}}'

    requests_mock.post(
        "/suggestions/api/4_1/rs/suggest/address",
        json={"suggestions": []},
        additional_matcher=match_params,
    )
    dadata.suggest("address", "samara", params={"to_bound": {"value": "city"}})


def test_suggest_not_found(requests_mock):
    expected = []
    requests_mock.post("/suggestions/api/4_1/rs/suggest/address", json={"suggestions": expected})
    actual = dadata.suggest("address", "whatever")
    assert actual == expected


def test_find_by_id(requests_mock):
    expected = [
        {"value": "ООО МОТОРИКА", "data": {"inn": "7719402047"}},
    ]
    requests_mock.post("/suggestions/api/4_1/rs/findById/party", json={"suggestions": expected})
    actual = dadata.find_by_id("party", "7719402047")
    assert actual == expected


def test_find_by_id_params(requests_mock):
    def match_params(request):
        return request.body == '{"query": "7719402047", "count": 5}'

    requests_mock.post(
        "/suggestions/api/4_1/rs/findById/party",
        json={"suggestions": []},
        additional_matcher=match_params,
    )
    dadata.find_by_id("party", "7719402047", count=5)


def test_find_by_id_not_found(requests_mock):
    expected = []
    requests_mock.post("/suggestions/api/4_1/rs/findById/party", json={"suggestions": expected})
    actual = dadata.find_by_id("party", "1234567890")
    assert actual == expected


def test_find_affiliated(requests_mock):
    expected = [
        {"value": "ООО ДЗЕН.ПЛАТФОРМА", "data": {"inn": "7704431373"}},
        {"value": "ООО ЕДАДИЛ", "data": {"inn": "7728237907"}},
    ]
    requests_mock.post(
        "/suggestions/api/4_1/rs/findAffiliated/party", json={"suggestions": expected}
    )
    actual = dadata.find_affiliated("7736207543")
    assert actual == expected


def test_find_affiliated_params(requests_mock):
    def match_params(request):
        return request.body == '{"query": "7736207543", "count": 5}'

    requests_mock.post(
        "/suggestions/api/4_1/rs/findAffiliated/party",
        json={"suggestions": []},
        additional_matcher=match_params,
    )
    dadata.find_affiliated("7736207543", count=5)


def test_find_affiliated_not_found(requests_mock):
    expected = []
    requests_mock.post(
        "/suggestions/api/4_1/rs/findAffiliated/party", json={"suggestions": expected}
    )
    actual = dadata.find_affiliated("1234567890")
    assert actual == expected


def test_request_failed(requests_mock):
    requests_mock.post("/api/v1/clean/name", status_code=504)
    with pytest.raises(HTTPError):
        dadata.clean("name", "Сережа")
