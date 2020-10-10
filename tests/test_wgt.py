#!/usr/bin/env python

"""Tests for `wgt` package."""

from decimal import Decimal

import pytest

from wgt import lueftungsanlage


@pytest.fixture
def wgt_instance():
    ip = "127.0.0.1"
    version = "1.06"
    return lueftungsanlage.WGT(ip=ip, version=version)


def test_init(wgt_instance):
    """Sample pytest test function."""
    # Shouldn't be connected yet
    assert not wgt_instance.client.is_socket_open()
    # Provided in fixture
    assert wgt_instance.ip == "127.0.0.1"
    assert float(wgt_instance.version) == 1.06
    assert wgt_instance.version == Decimal("1.06")
    # Default
    assert wgt_instance.port == 502


if __name__ == "__main__":
    pytest.main()
