#!/usr/bin/env python3

"""Tests for `wgt` package."""

from decimal import Decimal

import pytest

from wgt import WGT


@pytest.fixture
def wgt_instance():
    ip = "127.0.0.1"
    version = "1.06"
    return WGT(ip=ip, version=version)


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


def test_init_min_version():
    """Ensure that a too minor version fails."""
    with pytest.raises(EnvironmentError):
        WGT(ip=None, version=1)


@pytest.mark.parametrize("sut", WGT.properties_get())
def test_parameter_addr_get(mocker, sut):
    """Test all parameters.

    Ensure that the correct address is read.
    """
    # Patch connection function
    mocker.patch("pymodbus.client.sync.ModbusTcpClient.connect")
    mocker.patch("pymodbus.client.sync.ModbusTcpClient.read_holding_registers")

    # Calculated properties
    if sut in ("betriebsstunden_waermepumpe_heizen", "meldung_any"):
        return

    # Read attr
    with WGT(ip="10", version="1.1") as wgt:
        mocker.spy(wgt.client, "read_holding_registers")

        if sut in ("fehler", "waermepumpe"):
            # Enums without 1 as valid value
            with pytest.raises(ValueError):
                value = getattr(wgt, sut)
            value = 42
        else:
            value = getattr(wgt, sut)
        assert value

    # Verify address
    expected_addr = getattr(WGT, "_addr_" + sut)
    expected_call_param = (expected_addr, 1)  # only 1 register shall be read
    wgt.client.read_holding_registers.assert_called_once_with(*expected_call_param)


if __name__ == "__main__":
    pytest.main()
