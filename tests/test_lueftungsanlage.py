"""Unit tests and mocks for wgt.lueftungsanlage."""
# pylint: disable=too-few-public-methods,redefined-outer-name,unused-argument

from datetime import timedelta
from decimal import Decimal

import pytest

from wgt import WGT
from wgt.types import Betriebsart, Meldung, Prozent

WGT_IP = "127.0.0.1"
WGT_VERSION = "1.10"


@pytest.fixture
def pymodbus_mocked(mocker):
    """Patch pymodbus to deliver results."""

    class ResponseContent:
        """Fake a response."""

        registers = [0]

    class WriteStatus:
        """Mock a successful response."""

        @staticmethod
        def isError():
            # pylint: disable=invalid-name,missing-function-docstring
            return False

    # Patch connection function
    mocker.patch("pymodbus.client.sync.ModbusTcpClient.connect")
    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.read_holding_registers",
        return_value=ResponseContent,
    )
    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.write_registers", return_value=WriteStatus
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


def test_write_error(pymodbus_mocked, mocker):
    """Ensure that we detect an error on writing."""

    class Failure:
        """Mock a failing response."""

        @staticmethod
        def isError():
            # pylint: disable=invalid-name,missing-function-docstring
            return True

    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.write_registers", return_value=Failure
    )

    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        with pytest.raises(RuntimeError):
            wgt.betriebsart = Betriebsart(0)


def test_read_errors(pymodbus_mocked, mocker):
    """Excercise errors on reading."""

    class ResponseContent:
        """Fake a response."""

        registers = ["foo"]

    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.read_holding_registers",
        return_value=ResponseContent,
    )
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        with pytest.raises(ValueError):
            assert wgt.betriebsart

    mocker.patch(
        "pymodbus.client.sync.ModbusTcpClient.read_holding_registers",
        return_value=None,
    )
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        with pytest.raises(AttributeError):
            assert wgt.betriebsart


def test_older_version(pymodbus_mocked):
    """Trigger errors on unavailable attributes in older versions."""

    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        assert wgt.luftleistung_aktuell_abluft is not None
        assert wgt.luftleistung_aktuell_zuluft is not None
        assert wgt.drehzahl_aktuell_abluft is not None
        assert wgt.drehzahl_aktuell_zuluft is not None

    with WGT(ip=WGT_IP, version="1.06") as wgt:
        assert wgt.luftleistung_aktuell_abluft is None
        assert wgt.luftleistung_aktuell_zuluft is None
        assert wgt.drehzahl_aktuell_abluft is None
        assert wgt.drehzahl_aktuell_zuluft is None


@pytest.mark.parametrize("value", (30, 42, 100))
def test_luftstufe_prozent_range_ok(pymodbus_mocked, value):
    """Set valid lufstufe percentage."""

    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        wgt.luftleistung_linear_manuell = Prozent(value)


@pytest.mark.parametrize("value", (-10, 0, 29.9, 100.1, 1e6))
def test_luftstufe_prozent_range_nok(pymodbus_mocked, value):
    """Set invalid lufstufe percentage."""
    # Values not in range
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        with pytest.raises(ValueError):
            wgt.luftleistung_linear_manuell = Prozent(value)


def test_meldung_any(pymodbus_mocked, mocker):
    """Trigger one failing Meldung."""
    mocker.patch("pymodbus.client.sync.ModbusTcpClient.read_holding_registers")
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        assert wgt.meldung_any == Meldung.Meldung


if __name__ == "__main__":
    pytest.main()
