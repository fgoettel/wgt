#!/usr/bin/env python3

"""Tests for `wgt` types."""

import pytest

from wgt import types


def test_celsius():
    """Test celsisus as representative of units."""
    expected = 42.42
    celsius = types.Celsius(expected)
    assert celsius.value == expected
    assert celsius.unit == "°C"
    assert celsius.name == str(expected)
    assert str(celsius) == str(celsius.value) + celsius.unit


if __name__ == "__main__":
    pytest.main()
