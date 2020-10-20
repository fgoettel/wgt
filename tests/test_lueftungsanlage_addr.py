#!/usr/bin/env python3

"""Tests for `wgt` addresses package."""


import pytest

from wgt import WGT


def test_addr():
    """Ensure that the addresses re in sync with documentation.

    Doc updated 31.03.2020

    """
    assert WGT._addr_betriebsart == 100
    assert WGT._addr_luftstufe_manuell == 101
    assert WGT._addr_luftstufe_aktuell == 102
    assert WGT._addr_luftleistung_linear_manuell == 103
    assert WGT._addr_luftstufe_ueberschreibung == 104
    assert WGT._addr_luftstufe_zeitprogramm_basis == 110
    assert WGT._addr_stosslueftung == 111
    assert WGT._addr_stosslueftung_restlaufzeit == 112
    assert WGT._addr_waermepumpe == 114
    assert WGT._addr_nachheizregister == 116
    assert WGT._addr_geblaese_zuluft == 117
    assert WGT._addr_geblaese_abluft == 118
    assert WGT._addr_erdwaermetauscher == 121
    assert WGT._addr_bypass == 123
    assert WGT._addr_aussenklappe == 131
    assert WGT._addr_vorheizregister == 133
    assert WGT._addr_luftstufe_zeitprogramm == 140
    assert WGT._addr_luftstufe_sensoren == 141
    assert WGT._addr_luftleistung_aktuell_zuluft == 142
    assert WGT._addr_luftleistung_aktuell_abluft == 143
    assert WGT._addr_drehzahl_aktuell_zuluft == 144
    assert WGT._addr_drehzahl_aktuell_abluft == 145
    assert WGT._addr_t1_nach_erdwaermetauscher == 200
    assert WGT._addr_t2_nach_vorheizregister == 201
    assert WGT._addr_t3_vor_nacherwaermung == 202
    assert WGT._addr_t4_nach_nacherwaermung == 203
    assert WGT._addr_t5_abluft == 204
    assert WGT._addr_t6_waermetauscher == 205
    assert WGT._addr_t7_verdampfer == 206
    assert WGT._addr_t8_kondensator == 207
    assert WGT._addr_t10_aussen == 209
    assert WGT._addr_heizen_kuehlen == 230
    assert WGT._addr_waermepumpe_heizen == 231
    assert WGT._addr_waermepumpe_kuehlen == 232
    assert WGT._addr_zusatzheizung_haus == 234
    assert WGT._addr_druckwaechter == 242
    assert WGT._addr_evu_sperre == 243
    assert WGT._addr_tuer_offen == 244
    assert WGT._addr_geraetefilter_verschmutzt == 245
    assert WGT._addr_geraetefilter_vorgelagert_verschmutzt == 246
    assert WGT._addr_niedertarif_abgeschaltet == 247
    assert WGT._addr_versorgungsspannung_abgeschaltet == 248
    assert WGT._addr_pressostat == 250
    assert WGT._addr_evu_sperre_extern == 251
    assert WGT._addr_heizmodul_testbetrieb == 252
    assert WGT._addr_notbetrieb == 253
    assert WGT._addr_zuluft_zu_kalt == 254
    assert WGT._addr_geraetefilter_restlaufzeit == 265
    assert WGT._addr_geraetefilter_vorgelagert_restlaufzeit == 263
    assert WGT._addr_fehler == 240
    assert WGT._addr_temperatur_raum1_ist == 360
    assert WGT._addr_temperatur_raum1_soll == 400
    assert WGT._addr_temperatur_raum1_basis == 420
    assert WGT._addr_zusatzheizung_raum1_freigabe == 440
    assert WGT._addr_zusatzheizung_raum1_aktiv == 460
    assert WGT._addr_zeitprogramm_heizen_raum1 == 500
    assert WGT._addr_betriebsstunden_luefter_gesamt == 800
    assert WGT._addr_betriebsstunden_luefter_stufe1 == 801
    assert WGT._addr_betriebsstunden_luefter_stufe2 == 802
    assert WGT._addr_betriebsstunden_luefter_stufe3 == 803
    assert WGT._addr_betriebsstunden_luefter_stufe4 == 804
    assert WGT._addr_betriebsstunden_waermepumpe_gesamt == 805
    assert WGT._addr_betriebsstunden_waermepumpe_kuehlen == 806
    assert WGT._addr_betriebsstunden_vorheizregister == 809
    assert WGT._addr_betriebsstunden_zusatzheizung == 810
    assert WGT._addr_betriebsstunden_erdwaermetauscher == 813


if __name__ == "__main__":
    pytest.main()
