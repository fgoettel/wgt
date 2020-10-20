#!/usr/bin/env python3

"""Tests for `wgt` package."""

from decimal import Decimal
from datetime import timedelta

import pytest

from wgt import WGT

WGT_IP = "127.0.0.1"
WGT_VERSION = "1.10"


@pytest.fixture
def pymodbus_mocked(mocker):
    """Patch pymodbus to deliver acceptable results."""

    class Response:
        """Fake a response."""

        registers = [0]

    class Success:
        """Mock a successful response."""

        @staticmethod
        def isError():
            return False

    # Patch connection function
    mocker.patch("pymodbus.client.sync.ModbusTcpClient.connect")
    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.read_holding_registers",
        return_value=Response,
    )
    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.write_registers", return_value=Success()
    )


def test_init():
    """Test the good case of an initialization."""
    wgt = WGT(ip=WGT_IP, version=WGT_VERSION)
    # Shouldn't be connected yet
    assert not wgt.client.is_socket_open()
    # Provided in fixture
    assert wgt.ip == WGT_IP
    assert float(wgt.version) == float(WGT_VERSION)
    assert wgt.version == Decimal(WGT_VERSION)
    # Default
    assert wgt.port == 502


def test_init_min_version():
    """Ensure that a too minor version fails."""
    with pytest.raises(EnvironmentError):
        WGT(ip=None, version=1)


@pytest.mark.parametrize("sut", WGT.properties_get())
def test_parameter_addr_get(pymodbus_mocked, mocker, sut):
    """Test all parameters.

    Ensure that the correct address is read.
    """
    # Calculated properties
    if sut in ("betriebsstunden_waermepumpe_heizen", "meldung_any"):
        return

    # Read attr
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        mocker.spy(wgt.client, "read_holding_registers")

        value = getattr(wgt, sut)
        if isinstance(value, timedelta):
            # Timedelta of 0 is falsely
            value = timedelta(hours=42)
        assert value

    # Verify address
    expected_addr = getattr(WGT, "_addr_" + sut)
    expected_call_param = (expected_addr, 1)  # only 1 register shall be read
    wgt.client.read_holding_registers.assert_called_once_with(*expected_call_param)


@pytest.mark.parametrize("sut", WGT.properties_set())
def test_parameter_addr_set(pymodbus_mocked, mocker, sut):
    """Test all settable parameters.

    Ensure that the correct address is set.
    """
    # Set attr, create type dynamically
    value_plain = 1
    if "luftleistung" in sut:
        value_plain = 42  # needs to be in [30, 100]

    # First try - plain types aren't supported.
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        with pytest.raises(TypeError):
            setattr(wgt, sut, value_plain)

    # Second try - should be ok if we use the correct type
    value = WGT.property_type(sut)(value_plain)
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        mocker.spy(wgt.client, "write_registers")
        setattr(wgt, sut, value)

    # Verify address
    expected_addr = getattr(WGT, "_addr_" + sut)
    expected_value = value_plain
    if "temperatur" in sut:
        # Temperatures are multiplied with 10
        expected_value *= 10

    expected_call_param = (
        expected_addr,
        expected_value,
    )
    wgt.client.write_registers.assert_called_once_with(*expected_call_param)


def test_read_all(pymodbus_mocked, mocker):
    """Test that the read-all functions reads all properties."""

    # Read attr
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        mocker.spy(wgt.client, "read_holding_registers")
        wgt.read_all()

    # Verify call count
    expected_call_count = (
        len(WGT.properties_get()) + 12
    )  # Meldungen are read twice for "any_meldung"
    assert wgt.client.read_holding_registers.call_count == expected_call_count


if __name__ == "__main__":
    pytest.main()
