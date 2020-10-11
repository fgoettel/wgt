"""Lese und modifizieren die Informationen einer Schwörer WGT."""

import logging
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from typing import Generator, Optional, Union

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
    HeizKuehl,
    Luftstufe,
    Meldung,
    Prozent,
    Status,
    Vorheizregister,
    Waermepumpe,
)


class WGT:
    """Representing a Schwörer WGT.

    Die WGT wird via Modbus TCP angebunden und präsentiert ihren
    Status.
    Mit jeder Abfrage eines Attributes wird dass entsprechende
    Attribut der WGT gelesen.

    Veränderbare Attribute können gesetzt werden.

    """

    # pylint: disable=R0904

    def __init__(self, ip: str, version: str):
        """Initialisiere die WGT.

        Parameters
        ----------
        ip
            IP der WGT

        version
            Version des Bedienteils.

        """
        # Save given parameters
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
        self.logger.info("Created Modbus TCP client for %s", self.ip)
        self.client = ModbusClient(host=self.ip, port=self.port)

    def __enter__(self) -> "WGT":
        """Kontext Eintritt. Create a client. Return self."""
        self.client.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Kontext Exit. Schliesse client."""
        self.logger.info("Closing modbus tcp client.")
        self.client.close()

    def _read_register(self, addr: int) -> int:
        """Read one word of specified register.

        Parameters
        ----------
        addr
            The address of the registers

        Returns
        -------
        int
            Value of the register.

        Exceptions
        ----------
            Raises an exception if the value couldn't be read properly.

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
    ) -> bool:
        """Write value to a register.

        Parameters
        ----------
        addr
            The address of the register
        value_raw
            The value to write. Either Enum, Prozent or Celsius

        Returns
        -------
        bool
            True if the write was succesful

        """

        # Convert to format
        if isinstance(value_raw, (Enum, Prozent)):
            value = int(value_raw.value)
        elif isinstance(value_raw, Celsius):
            value = int(value_raw.value * 10)
        else:
            raise TypeError("Invalid input type.")

        # Write and check response
        self.logger.debug("Writing %i to %i.", value, addr)
        response = self.client.write_registers(addr, value)
        return not bool(response.isError())

    def _read_temperature(self, addr: int) -> Celsius:
        """Read temperature."""
        return Celsius(self._read_register(addr) / 10.0)

    def _write_temperature(self, addr: int, value: Celsius) -> bool:
        """Write temperature."""
        if not isinstance(value, Celsius):
            raise TypeError
        return self._write_register(addr, value)

    @property
    def betriebsart(self) -> Betriebsart:
        """Betriebsart der WGT."""
        return Betriebsart(self._read_register(100))

    @betriebsart.setter
    def betriebsart(self, value: Betriebsart) -> bool:
        """Setze Betriebsart."""
        return self._write_register(100, value)

    @property
    def luftstufe_manuell(self) -> Luftstufe:
        """Zuletzt manuell ausgewählte Lüftungsstufe."""
        return Luftstufe(self._read_register(101))

    @luftstufe_manuell.setter
    def luftstufe_manuell(self, value: Luftstufe) -> bool:
        """Setze die Lüftungsstufe manuell."""
        return self._write_register(101, value)

    @property
    def luftstufe_aktuell(self) -> Luftstufe:
        """Aktuelle Lüftungsstufe."""
        return Luftstufe(self._read_register(102))

    @property
    def luftleistung_linear_manuell(self) -> Prozent:
        """Luftlesitung in Prozent - manuell Einstellung."""
        return Prozent(self._read_register(103))

    @luftleistung_linear_manuell.setter
    def luftleistung_linear_manuell(self, value: Prozent) -> bool:
        """Setze die Luftleistung auf einen Prozentwert."""
        if not isinstance(value, Prozent):
            raise TypeError

        if not 30 <= value.value <= 100:
            raise ValueError("Luftleistung out of range.")

        return self._write_register(103, value)

    @property
    def luftstufe_ueberschreibung(self) -> Status:
        """Ist die aktuelle Luftsufe überschrieben."""
        return Status(self._read_register(104))

    @property
    def luftstufe_zeitprogramm_basis(self) -> Luftstufe:
        """Lüftungsstufe nach Zeitprogram."""
        return Luftstufe(self._read_register(110))

    @property
    def stosslueftung(self) -> Status:
        """Stosslueftung aktiv oder nicht."""
        return Status(self._read_register(111))

    @stosslueftung.setter
    def stosslueftung(self, value: Status) -> bool:
        """De-/aktiviere die Stosslueftung."""

        if not isinstance(value, Status):
            raise TypeError

        return self._write_register(111, value)

    @property
    def stosslueftung_restlaufzeit(self) -> timedelta:
        """Restlaufzeit der aktuellen stosslueftung."""
        return timedelta(minutes=self._read_register(112))

    @property
    def waermepumpe(self) -> Waermepumpe:
        """Status der Wärmepumpe."""
        return Waermepumpe(self._read_register(114))

    @property
    def nachheizregister(self) -> Status:
        """Status des Nachheizregisters."""
        return Status(self._read_register(116))

    @property
    def geblaese_zuluft(self) -> Geblaese:
        """Status des Zuluft Gebläses."""
        return Geblaese(self._read_register(117))

    @property
    def geblaese_abluft(self) -> Geblaese:
        """Staus des Abluft Gebläses."""
        return Geblaese(self._read_register(118))

    @property
    def erdwaermetauscher(self) -> Erdwaermetauscher:
        """Status des Erdwärmetauschers.

        Defaults to 0 if no EWT.
        """
        return Erdwaermetauscher(self._read_register(121))

    @property
    def bypass(self) -> Bypass:
        """Status des bypasses."""
        return Bypass(self._read_register(123))

    @property
    def aussenklappe(self) -> Aussenklappe:
        """Status der Aussenklappe."""
        return Aussenklappe(self._read_register(131))

    @property
    def vorheizregister(self) -> Vorheizregister:
        """Status des Vorheizregisters."""
        return Vorheizregister(self._read_register(133))

    @property
    def luftstufe_zeitprogramm(self) -> Luftstufe:
        """Die Luftstufe nach Zeitprogramm."""
        return Luftstufe(self._read_register(140))

    @property
    def luftstufe_sensoren(self) -> Luftstufe:
        """Die Luftstufe nach Sensorenlage."""
        return Luftstufe(self._read_register(141))

    @property
    def luftleistung_aktuell_zuluft(self) -> Optional[Prozent]:
        """Luftleistung aktuell der zuluft."""
        if self.version <= 1.06:
            self.logger.info("Zuluft Luftleistung not supported in this version.")
            return None
        return Prozent(self._read_register(142))

    @property
    def luftleistung_aktuell_abluft(self) -> Optional[Prozent]:
        """Luftleistung aktuell der Abluft."""
        if self.version <= 1.06:
            self.logger.info("Abluft Luftleistung not supported in this version.")
            return None
        return Prozent(self._read_register(143))

    @property
    def drehzahl_aktuell_abluft(self) -> Optional[Drehzahl]:
        """Drehzahl des Abluft ventilators."""
        if self.version <= 1.06:
            self.logger.info("Zuluft Drehzahl not supported in this version.")
            return None
        return Drehzahl(self._read_register(144))

    @property
    def drehzahl_aktuell_zuluft(self) -> Optional[Drehzahl]:
        """Drehzahl des Zuluft ventilators."""
        if self.version <= 1.06:
            self.logger.info("Abluft Drehzahl not supported in this version.")
            return None
        return Drehzahl(self._read_register(145))

    @property
    def t1_nach_erdwaermetauscher(self) -> Celsius:
        """Temperatur Erdwärmetauscher."""
        return self._read_temperature(200)

    @property
    def t2_nach_vorheizregister(self) -> Celsius:
        """Temperatur Vorheizregister."""
        return self._read_temperature(201)

    @property
    def t3_vor_nacherwaermung(self) -> Celsius:
        """Temperatur vor Nacherwärmung."""
        return self._read_temperature(202)

    @property
    def t4_nach_nacherwaermung(self) -> Celsius:
        """Temperatur nach Nacherwärmung."""
        return self._read_temperature(203)

    @property
    def t5_abluft(self) -> Celsius:
        """Temperatur Abluft."""
        return self._read_temperature(204)

    @property
    def t6_waermetauscher(self) -> Celsius:
        """Temperatur Wärmetauscher."""
        return self._read_temperature(205)

    @property
    def t7_verdampfer(self) -> Celsius:
        """Temperatur Verdampfer."""
        return self._read_temperature(206)

    @property
    def t8_kondensator(self) -> Celsius:
        """Temperatur Kondensator."""
        return self._read_temperature(207)

    @property
    def t10_aussen(self) -> Celsius:
        """Temperatur Aussen."""
        return self._read_temperature(209)

    @property
    def heizen_kuehlen(self) -> HeizKuehl:
        """Heizen oder Kühl modus."""
        return HeizKuehl(self._read_register(230))

    @heizen_kuehlen.setter
    def heizen_kuehlen(self, value: HeizKuehl) -> bool:
        """Setze Heiz/Kühl Modus."""
        if not isinstance(value, HeizKuehl):
            raise TypeError
        return self._write_register(230, value)

    @property
    def waermepumpe_heizen(self) -> Freigabe:
        """Ist die waermepumpe zu heizen freigegeben."""
        return Freigabe(self._read_register(231))

    @waermepumpe_heizen.setter
    def waermepumpe_heizen(self, value: Freigabe) -> bool:
        """Setze Freigabe der Heiz Wärmepumpe."""
        if not isinstance(value, Freigabe):
            raise TypeError

        return self._write_register(231, value)

    @property
    def waermepumpe_kuehlen(self) -> Freigabe:
        """Ist die Waermepumpe zum kühlen freigegeben."""
        return Freigabe(self._read_register(232))

    @waermepumpe_kuehlen.setter
    def waermepumpe_kuehlen(self, value: Freigabe) -> bool:
        """Setze Freigabe der Kühl Wärmepumpe."""
        if not isinstance(value, Freigabe):
            raise TypeError

        return self._write_register(232, value)

    @property
    def zusatzheizung_haus(self) -> Freigabe:
        """Ist die Zusatzheizung auf Haus Ebene freigegeben."""
        return Freigabe(self._read_register(234))

    @zusatzheizung_haus.setter
    def zusatzheizung_haus(self, value: Freigabe) -> bool:
        """Setze Freigabe der Zusatzheizung fürs Haus."""
        if not isinstance(value, Freigabe):
            raise TypeError
        return self._write_register(234, value)

    @property
    def fehler(self) -> Fehler:
        """Liegt ein Fehler vor."""
        return Fehler(self._read_register(240))

    @property
    def druckwaechter(self) -> Meldung:
        """Gibt es eine meldung des druckwächters."""
        return Meldung(self._read_register(242))

    @property
    def evu_sperre(self) -> Meldung:
        """Gibt es eine Sperrung durch das energie versorgungs unternehmen."""
        return Meldung(self._read_register(243))

    @property
    def tuer_offen(self) -> Meldung:
        """Ist die Tuer der WGT geöffnet."""
        return Meldung(self._read_register(244))

    @property
    def geraetefilter_verschmutzt(self) -> Meldung:
        """Ist der Gerätefilter verschmutzt."""
        return Meldung(self._read_register(245))

    @property
    def geraetefilter_vorgelagert_verschmutzt(self) -> Meldung:
        """Ist der vorgelagerte gerätefilter verschmutzt."""
        return Meldung(self._read_register(246))

    @property
    def niedertarif_abgeschaltet(self) -> Meldung:
        """Ist der niedertarif des EVU abgeschalten."""
        return Meldung(self._read_register(247))

    @property
    def versorgungsspannung_abgeschaltet(self) -> Meldung:
        """Ist die Versorgungsspannung abgeschalten."""
        return Meldung(self._read_register(248))

    @property
    def pressostat(self) -> Meldung:
        """Meldung bzgl. pressostat."""
        return Meldung(self._read_register(250))

    @property
    def evu_sperre_extern(self) -> Meldung:
        """EVU sperre von extern."""
        return Meldung(self._read_register(251))

    @property
    def heizmodul_testbetrieb(self) -> Meldung:
        """Heizmodul im Testbetrieb."""
        return Meldung(self._read_register(252))

    @property
    def notbetrieb(self) -> Meldung:
        """Anlage im Notbetrieb."""
        return Meldung(self._read_register(253))

    @property
    def zuluft_zu_kalt(self) -> Meldung:
        """Zuluft ist zu kalt. Gefahr der Vereisung."""
        return Meldung(self._read_register(254))

    @property
    def geraetefilter_restlaufzeit(self) -> timedelta:
        """Tage bis der Gerätefilter getauscht werden muss."""
        return timedelta(days=self._read_register(265))

    @property
    def geraetefilter_vorgelagert_restlaufzeit(self) -> timedelta:
        """Tage bis der vorgelagerte Gerätefilter getauscht werden muss."""
        return timedelta(days=self._read_register(263))

    @property
    def temperatur_raum1_ist(self) -> Celsius:
        """Ist temperatur raum 1."""
        return self._read_temperature(360)

    @property
    def temperatur_raum1_soll(self) -> Celsius:
        """Soll temperatur raum 1."""
        return self._read_temperature(400)

    @temperatur_raum1_soll.setter
    def temperatur_raum1_soll(self, value: Celsius) -> Optional[bool]:
        """Setze soll temperatur für raum 1."""
        return self._write_temperature(400, value)

    @property
    def temperatur_raum1_basis(self) -> Celsius:
        """Lese Basis temperatur für Raum 1."""
        return self._read_temperature(420)

    @temperatur_raum1_basis.setter
    def temperatur_raum1_basis(self, value: Celsius) -> Optional[bool]:
        """Setze Basis Temperatur für Raum 1."""
        return self._write_temperature(420, value)

    @property
    def zusatzheizung_raum1_freigabe(self) -> Freigabe:
        """Zusatzheizung in raum 1 (nicht) freigegeben."""
        return Freigabe(self._read_register(440))

    @zusatzheizung_raum1_freigabe.setter
    def zusatzheizung_raum1_freigabe(self, value: Freigabe) -> bool:
        """Sperre/Freigabe der Zusatzheizung in raum 1."""
        if not isinstance(value, Freigabe):
            raise TypeError

        return self._write_register(440, value)

    @property
    def zusatzheizung_raum1_aktiv(self) -> Status:
        """Ist die ZH in raum 1 aktiv."""
        return Status(self._read_register(460))

    @zusatzheizung_raum1_aktiv.setter
    def zusatzheizung_raum1_aktiv(self, value: Status) -> bool:
        """De-Aktiviere ZH in raum 1."""
        if not isinstance(value, Status):
            raise TypeError

        return self._write_register(460, value)

    @property
    def zeitprogramm_heizen_raum1(self) -> Freigabe:
        """Zeitprogram für heizen Raum 1 freigeben."""
        return Freigabe(self._read_register(500))

    @zeitprogramm_heizen_raum1.setter
    def zeitprogramm_heizen_raum1(self, value: Freigabe) -> bool:
        """De-Aktiviere Zeitprogramm für Raum 1."""
        if not isinstance(value, Freigabe):
            raise TypeError
        return self._write_register(500, value)

    @property
    def betriebsstunden_luefter_gesamt(self) -> timedelta:
        """Gesamt Betriebsstunden der Lüfter."""
        return timedelta(hours=self._read_register(800))

    @property
    def betriebsstunden_luefter_stufe1(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 1."""
        return timedelta(hours=self._read_register(801))

    @property
    def betriebsstunden_luefter_stufe2(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 2."""
        return timedelta(hours=self._read_register(802))

    @property
    def betriebsstunden_luefter_stufe3(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 3."""
        return timedelta(hours=self._read_register(803))

    @property
    def betriebsstunden_luefter_stufe4(self) -> timedelta:
        """Lüfter betriebsstunden auf stufe 4."""
        return timedelta(hours=self._read_register(804))

    @property
    def betriebsstunden_waermepumpe_gesamt(self) -> timedelta:
        """Gesamt Betriebsstunden der Wärmepumpe."""
        return timedelta(hours=self._read_register(805))

    @property
    def betriebsstunden_waermepumpe_kuehlen(self) -> timedelta:
        """Betriebsstunden der waermepumpe im kühlmodus."""
        return timedelta(hours=self._read_register(806))

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
        return timedelta(hours=self._read_register(809))

    @property
    def betriebsstunden_zusatzheizung(self) -> timedelta:
        """Betriebsstunden der Zusatzheizung."""
        return timedelta(hours=self._read_register(810))

    @property
    def betriebsstunden_erdwaermetauscher(self) -> timedelta:
        """Betriebsstunden des Erdärmetauschers."""
        return timedelta(hours=self._read_register(813))

    @property
    def meldungen_gesamt(self) -> Meldung:
        """Check if any meldung exists. True means all clear."""
        for attr in (
            self.druckwaechter,
            self.evu_sperre,
            self.tuer_offen,
            self.geraetefilter_verschmutzt,
            self.geraetefilter_vorgelagert_verschmutzt,
            self.niedertarif_abgeschaltet,
            self.versorgungsspannung_abgeschaltet,
            self.pressostat,
            self.evu_sperre_extern,
            self.heizmodul_testbetrieb,
            self.notbetrieb,
            self.zuluft_zu_kalt,
        ):
            if attr == Meldung.Meldung:
                return Meldung.Meldung
        return Meldung.Inaktiv

    @classmethod
    def get_all_attributes(cls) -> Generator[str, None, None]:
        """Return all attributes of the WGT."""

        excludes = (
            "get_all_attributes",
            "read_all",
        )
        for attr in dir(cls):
            if attr.startswith("_") or (attr in excludes):
                continue
            yield attr

    def read_all(self) -> None:
        """Read and logger.info all properties."""

        self.logger.info("Reading all information from WGT")
        for attr in self.get_all_attributes():

            value = getattr(self, attr)

            self.logger.info("%s:\n\t%s", attr, value)


def read_all() -> None:
    """Create a WGT instance and readout all properties."""

    with WGT("10.1.1.29", version="1.06") as wgt:
        wgt.read_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    read_all()
