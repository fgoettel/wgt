"""Read and set properties of a Schwörer ventilation System a.k.a. WGT."""

import logging
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from types import TracebackType
from typing import Any, List, Optional, Union, get_type_hints

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

from wgt.types import (
    Aussenklappe,
    Betriebsart,
    Bypass,
    Celsius,
    Drehzahl,
    Erdwaermetauscher,
    Fehler,
    Freigabe,
    Geblaese,
    HeizenKuehlenSteuerung,
    Luftstufe,
    Meldung,
    Prozent,
    Status,
    Unit,
    Vorheizregister,
    Waermepumpe,
)


class WGT:
    """Representing a WGT.

    The vent system will be connected via Modbus TCP and represents
    it's states.

    Every property is actually read via Modbus before a value is
    returned.

    The WGT is intended to be used in with context.

    """

    # pylint: disable=too-many-public-methods
    # Define register addresses
    _addr_betriebsart = 100
    _addr_luftstufe_manuell = 101
    _addr_luftstufe_aktuell = 102
    _addr_luftleistung_linear_manuell = 103
    _addr_luftstufe_ueberschreibung = 104
    _addr_luftstufe_zeitprogramm_basis = 110
    _addr_stosslueftung = 111
    _addr_stosslueftung_restlaufzeit = 112
    _addr_waermepumpe = 114
    _addr_nachheizregister = 116
    _addr_geblaese_zuluft = 117
    _addr_geblaese_abluft = 118
    _addr_erdwaermetauscher = 121
    _addr_bypass = 123
    _addr_aussenklappe = 131
    _addr_vorheizregister = 133
    _addr_luftstufe_zeitprogramm = 140
    _addr_luftstufe_sensoren = 141
    _addr_luftleistung_aktuell_zuluft = 142
    _addr_luftleistung_aktuell_abluft = 143
    _addr_drehzahl_aktuell_zuluft = 144
    _addr_drehzahl_aktuell_abluft = 145
    _addr_t1_nach_erdwaermetauscher = 200
    _addr_t2_nach_vorheizregister = 201
    _addr_t3_vor_nacherwaermung = 202
    _addr_t4_nach_nacherwaermung = 203
    _addr_t5_abluft = 204
    _addr_t6_waermetauscher = 205
    _addr_t7_verdampfer = 206
    _addr_t8_kondensator = 207
    _addr_t10_aussen = 209
    _addr_heizen_kuehlen = 230
    _addr_waermepumpe_heizen = 231
    _addr_waermepumpe_kuehlen = 232
    _addr_zusatzheizung_haus = 234
    _addr_fehler = 240
    _addr_druckwaechter = 242
    _addr_evu_sperre = 243
    _addr_tuer_offen = 244
    _addr_geraetefilter_verschmutzt = 245
    _addr_geraetefilter_vorgelagert_verschmutzt = 246
    _addr_niedertarif_abgeschaltet = 247
    _addr_versorgungsspannung_abgeschaltet = 248
    _addr_pressostat = 250
    _addr_evu_sperre_extern = 251
    _addr_heizmodul_testbetrieb = 252
    _addr_notbetrieb = 253
    _addr_zuluft_zu_kalt = 254
    _addr_geraetefilter_vorgelagert_restlaufzeit = 263
    _addr_geraetefilter_restlaufzeit = 265
    _addr_temperatur_raum1_ist = 360
    _addr_temperatur_raum1_soll = 400
    _addr_temperatur_raum1_basis = 420
    _addr_zusatzheizung_raum1_freigabe = 440
    _addr_zusatzheizung_raum1_aktiv = 460
    _addr_zeitprogramm_heizen_raum1 = 500
    _addr_betriebsstunden_luefter_gesamt = 800
    _addr_betriebsstunden_luefter_stufe1 = 801
    _addr_betriebsstunden_luefter_stufe2 = 802
    _addr_betriebsstunden_luefter_stufe3 = 803
    _addr_betriebsstunden_luefter_stufe4 = 804
    _addr_betriebsstunden_waermepumpe_gesamt = 805
    _addr_betriebsstunden_waermepumpe_kuehlen = 806
    _addr_betriebsstunden_vorheizregister = 809
    _addr_betriebsstunden_zusatzheizung = 810
    _addr_betriebsstunden_erdwaermetauscher = 813

    def __init__(self, ip: str, version: str):
        """Initialize the WGT.

        Parameters
        ----------
        ip
            IP of the WGT

        version
            Version of the control panel

        Raises
        ------
        EnvironmentError
            In case the version is too old

        """
        # Assign parameter arguments
        self.ip = ip
        self.version = Decimal(version)

        # Default parameters
        self.port = 502

        # Setup logger
        self.logger = logging.getLogger(__name__)

        # Ensure that we have a version that supports modbus
        if self.version <= 1.05:
            self.logger.error("This version doesn't support modbus.")
            raise EnvironmentError
        self.logger.info("Detected version %01.2f", self.version)

        # Create modbus client
        self.logger.info("Created Modbus TCP client for %s:%i", self.ip, self.port)
        self.client = ModbusClient(host=self.ip, port=self.port)

    def __enter__(self) -> "WGT":
        """Enter context. Modbus client get's connected and self is returned."""
        self.logger.info("Connecting modbus tcp client.")
        self.client.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[BaseException],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Leave context. Close tcp client."""
        self.logger.debug("Closing modbus tcp client.")
        self.client.close()

    def _read_register(self, addr: int) -> int:
        """Read one word of specified register.

        Parameters
        ----------
        addr
            The register address.

        Returns
        -------
        int
            Value of the register.

        Raises
        ------
        AttributeError
            If the register couldn't be read.
        ValueError
            If the value couldn't be transformed to an integer.

        """

        # Get response
        response = self.client.read_holding_registers(addr, 1)

        # Extract value
        try:
            value = int(response.registers[0])
        except AttributeError as err:
            self.logger.debug(err)
            self.logger.warning("Couldn't get register from %i.", addr)
            raise
        except ValueError as err:
            self.logger.debug(err)
            self.logger.warning("Couldn't translate register response to int.")
            raise

        return value

    def _write_register(
        self, addr: int, value_raw: Union[Enum, Prozent, Celsius]
    ) -> None:
        """Write value to a register.

        Parameters
        ----------
        addr
            The address of the register
        value_raw
            An enum, or other strongly typed type is expected.
            Other allowed types: Inherited from wgt.types.unit

        Raises
        ------
        TypeError
            If the given type is not valid.
        RunimeError
            If the register couldn't be set.

        """

        # Convert to format
        if isinstance(value_raw, Celsius):
            value = int(value_raw.value * 10)
        elif isinstance(value_raw, (Enum, Unit)):
            value = int(value_raw.value)
        else:
            raise TypeError("Invalid input type.")

        # Write
        self.logger.debug("Writing %i to %i.", value, addr)
        response = self.client.write_registers(addr, value)

        # Raise an excpetion if write was not succesful
        if response.isError():
            raise RuntimeError("Could not write to WGT")

    def _read_temperature(self, addr: int) -> Celsius:
        """Read temperature."""
        return Celsius(self._read_register(addr) / 10.0)

    def _write_temperature(self, addr: int, value: Celsius) -> None:
        """Write temperature."""
        self._write_register(addr, value)

    @property
    def betriebsart(self) -> Betriebsart:
        """Betriebsart der WGT."""
        return Betriebsart(self._read_register(self._addr_betriebsart))

    @betriebsart.setter
    def betriebsart(self, value: Betriebsart) -> None:
        """Setze Betriebsart."""
        self._write_register(self._addr_betriebsart, value)

    @property
    def luftstufe_manuell(self) -> Luftstufe:
        """Zuletzt manuell ausgewählte Lüftungsstufe."""
        return Luftstufe(self._read_register(self._addr_luftstufe_manuell))

    @luftstufe_manuell.setter
    def luftstufe_manuell(self, value: Luftstufe) -> None:
        """Setze die Lüftungsstufe manuell."""
        self._write_register(self._addr_luftstufe_manuell, value)

    @property
    def luftstufe_aktuell(self) -> Luftstufe:
        """Aktuelle Lüftungsstufe."""
        return Luftstufe(self._read_register(self._addr_luftstufe_aktuell))

    @property
    def luftleistung_linear_manuell(self) -> Prozent:
        """Luftleistung in Prozent - manuell Einstellung."""
        return Prozent(self._read_register(self._addr_luftleistung_linear_manuell))

    @luftleistung_linear_manuell.setter
    def luftleistung_linear_manuell(self, value: Prozent) -> None:
        """Setze die Luftleistung auf einen Prozentwert.

        Raises
        ------
        TypeError
            If type is not wgt.types.Prozent
        ValueError
            If types is outside bounds [30, 100]

        """
        if not isinstance(value, Prozent):
            raise TypeError

        if not 30 <= value.value <= 100:
            raise ValueError("Luftleistung out of range.")

        self._write_register(self._addr_luftleistung_linear_manuell, value)

    @property
    def luftstufe_ueberschreibung(self) -> Status:
        """Ist die aktuelle Luftsufe überschrieben."""
        return Status(self._read_register(self._addr_luftstufe_ueberschreibung))

    @property
    def luftstufe_zeitprogramm_basis(self) -> Luftstufe:
        """Lüftungsstufe nach Zeitprogram."""
        return Luftstufe(self._read_register(self._addr_luftstufe_zeitprogramm_basis))

    @property
    def stosslueftung(self) -> Status:
        """Stosslueftung aktiv oder nicht."""
        return Status(self._read_register(self._addr_stosslueftung))

    @stosslueftung.setter
    def stosslueftung(self, value: Status) -> None:
        """De-/aktiviere die Stosslueftung.

        Raises
        ------
        TypeError
            If type is not Status

        """
        if not isinstance(value, Status):
            raise TypeError
        self._write_register(self._addr_stosslueftung, value)

    @property
    def stosslueftung_restlaufzeit(self) -> timedelta:
        """Restlaufzeit der aktuellen stosslueftung."""
        return timedelta(
            minutes=self._read_register(self._addr_stosslueftung_restlaufzeit)
        )

    @property
    def waermepumpe(self) -> Waermepumpe:
        """Status der Wärmepumpe."""
        return Waermepumpe(self._read_register(self._addr_waermepumpe))

    @property
    def nachheizregister(self) -> Status:
        """Status des Nachheizregisters."""
        return Status(self._read_register(self._addr_nachheizregister))

    @property
    def geblaese_zuluft(self) -> Geblaese:
        """Status des Zuluft Gebläses."""
        return Geblaese(self._read_register(self._addr_geblaese_zuluft))

    @property
    def geblaese_abluft(self) -> Geblaese:
        """Staus des Abluft Gebläses."""
        return Geblaese(self._read_register(self._addr_geblaese_abluft))

    @property
    def erdwaermetauscher(self) -> Erdwaermetauscher:
        """Status des Erdwärmetauschers.

        Defaults to 0 if no EWT.
        """
        return Erdwaermetauscher(self._read_register(self._addr_erdwaermetauscher))

    @property
    def bypass(self) -> Bypass:
        """Status des bypasses."""
        return Bypass(self._read_register(self._addr_bypass))

    @property
    def aussenklappe(self) -> Aussenklappe:
        """Status der Aussenklappe."""
        return Aussenklappe(self._read_register(self._addr_aussenklappe))

    @property
    def vorheizregister(self) -> Vorheizregister:
        """Status des Vorheizregisters."""
        return Vorheizregister(self._read_register(self._addr_vorheizregister))

    @property
    def luftstufe_zeitprogramm(self) -> Luftstufe:
        """Die Luftstufe nach Zeitprogramm."""
        return Luftstufe(self._read_register(self._addr_luftstufe_zeitprogramm))

    @property
    def luftstufe_sensoren(self) -> Luftstufe:
        """Die Luftstufe nach Sensorenlage."""
        return Luftstufe(self._read_register(self._addr_luftstufe_sensoren))

    @property
    def luftleistung_aktuell_zuluft(self) -> Optional[Prozent]:
        """Luftleistung aktuell der zuluft."""
        if self.version <= 1.06:
            self.logger.info("Zuluft Luftleistung not supported in this version.")
            return None
        return Prozent(self._read_register(self._addr_luftleistung_aktuell_zuluft))

    @property
    def luftleistung_aktuell_abluft(self) -> Optional[Prozent]:
        """Luftleistung aktuell der Abluft."""
        if self.version <= 1.06:
            self.logger.info("Abluft Luftleistung not supported in this version.")
            return None
        return Prozent(self._read_register(self._addr_luftleistung_aktuell_abluft))

    @property
    def drehzahl_aktuell_abluft(self) -> Optional[Drehzahl]:
        """Drehzahl des Abluft ventilators."""
        if self.version <= 1.06:
            self.logger.info("Zuluft Drehzahl not supported in this version.")
            return None
        return Drehzahl(self._read_register(self._addr_drehzahl_aktuell_abluft))

    @property
    def drehzahl_aktuell_zuluft(self) -> Optional[Drehzahl]:
        """Drehzahl des Zuluft ventilators."""
        if self.version <= 1.06:
            self.logger.info("Abluft Drehzahl not supported in this version.")
            return None
        return Drehzahl(self._read_register(self._addr_drehzahl_aktuell_zuluft))

    @property
    def t1_nach_erdwaermetauscher(self) -> Celsius:
        """Temperatur Erdwärmetauscher."""
        return self._read_temperature(self._addr_t1_nach_erdwaermetauscher)

    @property
    def t2_nach_vorheizregister(self) -> Celsius:
        """Temperatur Vorheizregister."""
        return self._read_temperature(self._addr_t2_nach_vorheizregister)

    @property
    def t3_vor_nacherwaermung(self) -> Celsius:
        """Temperatur vor Nacherwärmung."""
        return self._read_temperature(self._addr_t3_vor_nacherwaermung)

    @property
    def t4_nach_nacherwaermung(self) -> Celsius:
        """Temperatur nach Nacherwärmung."""
        return self._read_temperature(self._addr_t4_nach_nacherwaermung)

    @property
    def t5_abluft(self) -> Celsius:
        """Temperatur Abluft."""
        return self._read_temperature(self._addr_t5_abluft)

    @property
    def t6_waermetauscher(self) -> Celsius:
        """Temperatur Wärmetauscher."""
        return self._read_temperature(self._addr_t6_waermetauscher)

    @property
    def t7_verdampfer(self) -> Celsius:
        """Temperatur Verdampfer."""
        return self._read_temperature(self._addr_t7_verdampfer)

    @property
    def t8_kondensator(self) -> Celsius:
        """Temperatur Kondensator."""
        return self._read_temperature(self._addr_t8_kondensator)

    @property
    def t10_aussen(self) -> Celsius:
        """Temperatur Aussen."""
        return self._read_temperature(self._addr_t10_aussen)

    @property
    def heizen_kuehlen(self) -> HeizenKuehlenSteuerung:
        """Heizen oder Kühl modus."""
        return HeizenKuehlenSteuerung(self._read_register(self._addr_heizen_kuehlen))

    @heizen_kuehlen.setter
    def heizen_kuehlen(self, value: HeizenKuehlenSteuerung) -> None:
        """Setze Heiz/Kühl Modus."""
        if not isinstance(value, HeizenKuehlenSteuerung):
            raise TypeError
        self._write_register(self._addr_heizen_kuehlen, value)

    @property
    def waermepumpe_heizen(self) -> Freigabe:
        """Ist die waermepumpe zu heizen freigegeben."""
        return Freigabe(self._read_register(self._addr_waermepumpe_heizen))

    @waermepumpe_heizen.setter
    def waermepumpe_heizen(self, value: Freigabe) -> None:
        """Setze Freigabe der Heiz Wärmepumpe."""
        if not isinstance(value, Freigabe):
            raise TypeError
        self._write_register(self._addr_waermepumpe_heizen, value)

    @property
    def waermepumpe_kuehlen(self) -> Freigabe:
        """Ist die Waermepumpe zum kühlen freigegeben."""
        return Freigabe(self._read_register(self._addr_waermepumpe_kuehlen))

    @waermepumpe_kuehlen.setter
    def waermepumpe_kuehlen(self, value: Freigabe) -> None:
        """Setze Freigabe der Kühl Wärmepumpe."""
        if not isinstance(value, Freigabe):
            raise TypeError
        self._write_register(self._addr_waermepumpe_kuehlen, value)

    @property
    def zusatzheizung_haus(self) -> Freigabe:
        """Ist die Zusatzheizung auf Haus Ebene freigegeben."""
        return Freigabe(self._read_register(self._addr_zusatzheizung_haus))

    @zusatzheizung_haus.setter
    def zusatzheizung_haus(self, value: Freigabe) -> None:
        """Setze Freigabe der Zusatzheizung fürs Haus."""
        if not isinstance(value, Freigabe):
            raise TypeError
        self._write_register(self._addr_zusatzheizung_haus, value)

    @property
    def fehler(self) -> Fehler:
        """Liegt ein Fehler vor."""
        return Fehler(self._read_register(self._addr_fehler))

    @property
    def druckwaechter(self) -> Meldung:
        """Gibt es eine meldung des druckwächters."""
        return Meldung(self._read_register(self._addr_druckwaechter))

    @property
    def evu_sperre(self) -> Meldung:
        """Gibt es eine Sperrung durch das energie versorgungs unternehmen."""
        return Meldung(self._read_register(self._addr_evu_sperre))

    @property
    def tuer_offen(self) -> Meldung:
        """Ist die Tuer der WGT geöffnet."""
        return Meldung(self._read_register(self._addr_tuer_offen))

    @property
    def geraetefilter_verschmutzt(self) -> Meldung:
        """Ist der Gerätefilter verschmutzt."""
        return Meldung(self._read_register(self._addr_geraetefilter_verschmutzt))

    @property
    def geraetefilter_vorgelagert_verschmutzt(self) -> Meldung:
        """Ist der vorgelagerte gerätefilter verschmutzt."""
        return Meldung(
            self._read_register(self._addr_geraetefilter_vorgelagert_verschmutzt)
        )

    @property
    def niedertarif_abgeschaltet(self) -> Meldung:
        """Ist der niedertarif des EVU abgeschalten."""
        return Meldung(self._read_register(self._addr_niedertarif_abgeschaltet))

    @property
    def versorgungsspannung_abgeschaltet(self) -> Meldung:
        """Ist die Versorgungsspannung abgeschalten."""
        return Meldung(self._read_register(self._addr_versorgungsspannung_abgeschaltet))

    @property
    def pressostat(self) -> Meldung:
        """Meldung bzgl. pressostat."""
        return Meldung(self._read_register(self._addr_pressostat))

    @property
    def evu_sperre_extern(self) -> Meldung:
        """EVU sperre von extern."""
        return Meldung(self._read_register(self._addr_evu_sperre_extern))

    @property
    def heizmodul_testbetrieb(self) -> Meldung:
        """Heizmodul im Testbetrieb."""
        return Meldung(self._read_register(self._addr_heizmodul_testbetrieb))

    @property
    def notbetrieb(self) -> Meldung:
        """Anlage im Notbetrieb."""
        return Meldung(self._read_register(self._addr_notbetrieb))

    @property
    def zuluft_zu_kalt(self) -> Meldung:
        """Zuluft ist zu kalt. Gefahr der Vereisung."""
        return Meldung(self._read_register(self._addr_zuluft_zu_kalt))

    @property
    def geraetefilter_restlaufzeit(self) -> timedelta:
        """Tage bis der Gerätefilter getauscht werden muss."""
        return timedelta(
            days=self._read_register(self._addr_geraetefilter_restlaufzeit)
        )

    @property
    def geraetefilter_vorgelagert_restlaufzeit(self) -> timedelta:
        """Tage bis der vorgelagerte Gerätefilter getauscht werden muss."""
        return timedelta(
            days=self._read_register(self._addr_geraetefilter_vorgelagert_restlaufzeit)
        )

    @property
    def temperatur_raum1_ist(self) -> Celsius:
        """Ist temperatur raum 1."""
        return self._read_temperature(self._addr_temperatur_raum1_ist)

    @property
    def temperatur_raum1_soll(self) -> Celsius:
        """Soll temperatur raum 1."""
        return self._read_temperature(self._addr_temperatur_raum1_soll)

    @temperatur_raum1_soll.setter
    def temperatur_raum1_soll(self, value: Celsius) -> None:
        """Setze soll temperatur für raum 1."""
        self._write_temperature(self._addr_temperatur_raum1_soll, value)

    @property
    def temperatur_raum1_basis(self) -> Celsius:
        """Lese Basis temperatur für Raum 1."""
        return self._read_temperature(self._addr_temperatur_raum1_basis)

    @temperatur_raum1_basis.setter
    def temperatur_raum1_basis(self, value: Celsius) -> None:
        """Setze Basis Temperatur für Raum 1."""
        self._write_temperature(self._addr_temperatur_raum1_basis, value)

    @property
    def zusatzheizung_raum1_freigabe(self) -> Freigabe:
        """Zusatzheizung in raum 1 (nicht) freigegeben."""
        return Freigabe(self._read_register(self._addr_zusatzheizung_raum1_freigabe))

    @zusatzheizung_raum1_freigabe.setter
    def zusatzheizung_raum1_freigabe(self, value: Freigabe) -> None:
        """Sperre/Freigabe der Zusatzheizung in raum 1."""
        if not isinstance(value, Freigabe):
            raise TypeError
        self._write_register(self._addr_zusatzheizung_raum1_freigabe, value)

    @property
    def zusatzheizung_raum1_aktiv(self) -> Status:
        """Ist die ZH in raum 1 aktiv."""
        return Status(self._read_register(self._addr_zusatzheizung_raum1_aktiv))

    @zusatzheizung_raum1_aktiv.setter
    def zusatzheizung_raum1_aktiv(self, value: Status) -> None:
        """De-Aktiviere ZH in raum 1."""
        if not isinstance(value, Status):
            raise TypeError
        self._write_register(self._addr_zusatzheizung_raum1_aktiv, value)

    @property
    def zeitprogramm_heizen_raum1(self) -> Freigabe:
        """Zeitprogram für heizen Raum 1 freigeben."""
        return Freigabe(self._read_register(self._addr_zeitprogramm_heizen_raum1))

    @zeitprogramm_heizen_raum1.setter
    def zeitprogramm_heizen_raum1(self, value: Freigabe) -> None:
        """De-Aktiviere Zeitprogramm für Raum 1."""
        if not isinstance(value, Freigabe):
            raise TypeError
        self._write_register(self._addr_zeitprogramm_heizen_raum1, value)

    @property
    def betriebsstunden_luefter_gesamt(self) -> timedelta:
        """Gesamt Betriebsstunden der Lüfter."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_luefter_gesamt)
        )

    @property
    def betriebsstunden_luefter_stufe1(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 1."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_luefter_stufe1)
        )

    @property
    def betriebsstunden_luefter_stufe2(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 2."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_luefter_stufe2)
        )

    @property
    def betriebsstunden_luefter_stufe3(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 3."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_luefter_stufe3)
        )

    @property
    def betriebsstunden_luefter_stufe4(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 4."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_luefter_stufe4)
        )

    @property
    def betriebsstunden_waermepumpe_gesamt(self) -> timedelta:
        """Gesamt Betriebsstunden der Wärmepumpe."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_waermepumpe_gesamt)
        )

    @property
    def betriebsstunden_waermepumpe_kuehlen(self) -> timedelta:
        """Betriebsstunden der waermepumpe im kühlmodus."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_waermepumpe_kuehlen)
        )

    @property
    def betriebsstunden_waermepumpe_heizen(self) -> timedelta:
        """Betriebsstunden der waermepumpe im Heizmodus (errechnet)."""
        return (
            self.betriebsstunden_waermepumpe_gesamt
            - self.betriebsstunden_waermepumpe_kuehlen
        )

    @property
    def betriebsstunden_vorheizregister(self) -> timedelta:
        """Betriebsstunden des Vorheizregisters."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_vorheizregister)
        )

    @property
    def betriebsstunden_zusatzheizung(self) -> timedelta:
        """Betriebsstunden der Zusatzheizung."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_zusatzheizung)
        )

    @property
    def betriebsstunden_erdwaermetauscher(self) -> timedelta:
        """Betriebsstunden des Erdärmetauschers."""
        return timedelta(
            hours=self._read_register(self._addr_betriebsstunden_erdwaermetauscher)
        )

    @property
    def meldung_any(self) -> Meldung:
        """Check if any meldung exists. True means all clear."""
        # Identify all meldung, remove ourselves
        meldungen_all = [
            _ for _ in self.properties_get() if self.property_type(_) == Meldung
        ]
        meldungen_all.remove("meldung_any")

        for meldung in meldungen_all:
            if getattr(self, meldung) == Meldung.Meldung:
                return Meldung.Meldung
        return Meldung.Inaktiv

    @classmethod
    def properties_get(cls) -> List[str]:
        """Return all properties."""
        return [n for n in dir(cls) if isinstance(getattr(cls, n), property)]

    @classmethod
    def properties_set(cls) -> List[str]:
        """Return all properties that can be set."""
        properties = cls.properties_get()
        return [n for n in properties if callable(getattr(cls, n).fset)]

    @classmethod
    def property_type(cls, property_name: str) -> Any:
        """Return type of given property."""
        return get_type_hints(getattr(cls, property_name).fget)["return"]

    def read_all(self) -> None:
        """Read and logger.info all properties."""

        self.logger.info("Reading all information from WGT")
        for attr in sorted(self.properties_get()):
            value = getattr(self, attr)
            self.logger.info("%s:\n\t%s", attr, value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with WGT("10.1.1.29", version="1.06") as wgt:
        wgt.read_all()
