#!/usr/bin/env python3

"""Tests for `wgt` types."""

import pytest

from wgt import types


@pytest.fixture
def fixed_celsius():
    return types.Celsius(42.2)


def test_celsisus(fixed_celsius):
    """Test celsisus as representative of units."""
    value = 42.2
    assert fixed_celsius.value == value
    assert fixed_celsius.unit == "°C"
    assert fixed_celsius.name == str(value)
    assert str(fixed_celsius) == str(fixed_celsius.value) + fixed_celsius.unit


if __name__ == "__main__":
    pytest.main()
