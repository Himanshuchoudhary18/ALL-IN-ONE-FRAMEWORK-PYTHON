from urllib.parse import parse_qs, urlsplit

import pytest
from qa_framework.pages.amazon import exact_price_url, has_maximum_price, slider_index


def test_slider_uses_dynamic_index_not_currency():
    assert slider_index({"stepValues": [None, 1200, 1850, 2000, None]}, 2000) == 3


def test_slider_rejects_rounding():
    with pytest.raises(ValueError, match="does not offer exactly"):
        slider_index({"stepValues": [None, 1850, 2150, None]}, 2000)


@pytest.mark.parametrize("query,expected", [
    ("high-price=2000", True),
    ("rh=p_36%3A-200000", True),
    ("rh=p_36%3A10000-200000%2Cp_123%3A123", True),
    ("high-price=200", False),
    ("rh=p_36%3A-2000", False),
    ("k=Shoes", False),
    ("high-price=invalid", False),
])
def test_applied_filter_validation(query, expected):
    assert has_maximum_price(f"https://www.amazon.in/s?{query}", 2000) is expected


def test_fallback_preserves_search_and_other_filters():
    url = exact_price_url("https://www.amazon.in/s?k=Shoes&rh=p_36%3A-150000%2Cp_123%3A123&low-price=50", 2000)
    query = parse_qs(urlsplit(url).query)
    assert query == {"k": ["Shoes"], "rh": ["p_123:123"], "high-price": ["2000"]}


@pytest.mark.parametrize("url,price", [("https://example.com/s", 2000), ("https://www.amazon.in/s", -1)])
def test_fallback_rejects_invalid_inputs(url, price):
    with pytest.raises(ValueError):
        exact_price_url(url, price)
