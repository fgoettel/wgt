"""Define types for the different stati of the WGT."""

from dataclasses import dataclass
from enum import Enum, unique


@dataclass
class Prozent:
    """Prozent."""

    value: float
    unit_str: str = "%"

    def __str__(self):
        """Nice representation."""
        return f"{self.value}{self.unit_str}"


@dataclass
class Celsius:
    """Degree Celsius."""

    value: float
    unit_str: str = "°C"

    def __str__(self):
        """Nice representation."""
        return f"{self.value}{self.unit_str}"


@dataclass
class Drehzahl:
    """Drehzahl."""

    value: float
    unit_str: str = "rpm"

    def __str__(self):
        """Nice repesentation."""
        return f"{self.value}{self.unit_str}"


@unique
class Betriebsart(Enum):
    """Betriebsart der WGT."""

    Aus = 0
    Handbetrieb = 1
    Winterbetrieb = 2
    Sommerbetrieb = 3
    Sommer_Abluft = 4


@unique
class Luftstufe(Enum):
    """Lüftungsstufe."""

    Aus = 0
    Stufe_1 = 1
    Stufe_2 = 2
    Stufe_3 = 3
    Stufe_4 = 4
    Automatik = 5  # Optional
    Linearbetrieb = 6


@unique
class Waermepumpe(Enum):
    """Betriebsart der Wärmepumpe."""

    Aus = 0
    Heizen = 5
    Kühlen = 49


@unique
class Fehler(Enum):
    """Fehlerstatus der WGT."""

    Kein = 0
    DrehzahlZuluftFehlt = 257
    DrehzahlAbluftFehlt = 258
    VentilatorZuluftDrehzahlNichtErreicht = 259
    VentilatorAbluftDrehzahlNichtErreicht = 260
    VentilatorZuluftDrehzahlUeberschritten = 261
    VentilatorAbluftDrehzahlUeberschritten = 262
    KommunikationsFehlerBedieneinheit = 513
    KommunikationsFehlerNebenBedieneinheit = 514
    KommunikationsFehlerHeizmodul = 515
    KommunikationsFehlerSensor = 516
    KommunikationsFehlerSensorAdapter = 517
    KommunikationEmpfaenger = 518
    FehlerSensorelementT1 = 770
    FehlerSensorelementT2 = 771
    FehlerSensorelementT3 = 772
    FehlerSensorelementT4 = 773
    FehlerSensorelementT5 = 774
    FehlerSensorelementT6 = 775
    FehlerSensorelementT7 = 776
    FehlerSensorelementT8 = 777
    FehlerSensorelementT9 = 778
    FehlerSensorelementT10 = 779
    FehlerParameterspeicher = 1025
    FehlerSystemBus = 1026
    WpHochdruck = 1281
    WpNiederdruck = 1282
    MaxAbtauzeit = 1283
    WpNiederdruckKuehlbetrieb = 1284


@unique
class Geblaese(Enum):
    """Betriebsart Gebläse."""

    Deaktiviert = 0
    Anlaufphase = 1
    Aktiv = 2
    Standby = 5
    Fehler = 6


@unique
class Erdwaermetauscher(Enum):
    """Betriebsart Erdwärmetauscher.

    Default: Aus / 0 wenn kein EWT verbaut ist.
    """

    Aus = 0
    Heizbetrieb = 1
    Kuehlbetrieb = 2


@unique
class Bypass(Enum):
    """Betriebsart Bypass."""

    Geschlossen = 0
    OffenKuehlen = 1
    OffenHeizen = 2


@unique
class Aussenklappe(Enum):
    """Betriebsart Aussenklappe."""

    Geschlossen = 0
    Offen = 1


@unique
class Vorheizregister(Enum):
    """Betriebsart Vorheizregister."""

    Aus = 0
    Vhr1_aktiv = 1
    Vhr2_aktiv = 2
    Vhr1_Vhr2_aktiv = 3


@unique
class HeizKuehl(Enum):
    """Regelungsinformationen zur HeizKühl Funktion der Wärmepumpe."""

    Aus = 0
    Heizen = 1
    Kuehlen = 2
    Auto_TAussen = 3
    Auto_DigitalerEingang = 4


@unique
class Freigabe(Enum):
    """Objekt gesperrt oder freigegeben."""

    Gesperrt = 0
    Frei = 1


@unique
class Status(Enum):
    """Objekt inaktiv oder aktiv."""

    Inaktiv = 0
    Aktiv = 1


@unique
class Meldung(Enum):
    """Meldung inaktiv oder meldung."""

    Inaktiv = 0
    Meldung = 1
