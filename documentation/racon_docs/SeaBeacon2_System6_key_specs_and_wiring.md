# SeaBeacon 2 System 6 racon — key specs and wiring

Unit on the bench: **Tideland Signal SeaBeacon 2 System 6**, FCC ID **FAZSBCN2SYS6A**, racon serial 7684,
label reads "INPUT VOLTAGE 9 to 36 V, NOMINAL 12 V". Tideland Signal is now **Orga Signal**.

## Sources (all quotes below are verbatim from these)

| What | Where |
|---|---|
| Installation Manual, P.N. 011.1181-00, Rev 00 (Nov 2002), 56 pages — the FCC-filed copy | <https://manuals.plus/m/bb63d237b745dc16b28dc7c44d595897eacc49555b69045349d4a33bff22609e> (mirror of usermanual.wiki / fccid.io doc 390776) |
| FCC grant page for this exact FCC ID | <https://fccid.io/FAZSBCN2SYS6A> (Cloudflare-gated in a script; opens fine in a normal browser) |
| Datasheet (Orga Signal, rev. 15 Sep 2022) | <https://www.tidelandsignal.com/wp-content/uploads/2021/12/seabeacon-2-datasheet-2.pdf> — saved here as `SeaBeacon2_datasheet_tidelandsignal.pdf` |
| Product page | <https://www.tidelandsignal.com/racons/seabeacon-2/> |

## Power

From the datasheet (page 2):

| Parameter | Value |
|---|---|
| Power supply input voltage, GMU version | **9 – 36 V, nominal 12 VDC** |
| Power supply input voltage, Ex version | 18 – 32 V, nominal 24 VDC |
| Quiescent power consumption | **0.24 W** |
| Nominal power consumption, light traffic | **0.75 W** |
| Nominal power consumption, heavy traffic | **1.0 W** |
| Lightning / surge protection | 1 millisecond at 3000 volts |
| Output power to antenna | 1.0 W (30 dBm) |
| X-band frequency | 9.3 to 9.5 GHz |
| System sensitivity | −50 dBm |
| Antenna gain / ERP (X-band) | 6 dBi / 4.0 W |

From the installation manual, section 1.1.3:

> "The SeaBeacon 2 System 6 racon requires an input voltage of 9 to 36 volts DC ... Under all conditions,
> the effective source impedance of the voltage supply must be less than 0.05 Ohm."

From section 2.5.1 (this is the number that sizes the supply and wiring):

> "The SeaBeacon 2 System 6 racon must have a minimum 9 VDC input at the connector terminals in the racon
> base housing to operate properly."

> 12 V system: "Assuming a worst case **peak instantaneous current of 15A** in the cable, and a loaded
> battery voltage of 11.0 VDC ... the design loss in all of the copper wiring must be limited to 1.7 VDC at 15A."

> 24 V system: "At 18 VDC, the worst case **peak instantaneous current in the cable is 10A**."

So: average draw is under a watt, but the transmitter pulses draw amps. The supply has to be stiff
(< 0.05 Ω source impedance) — a battery, or a bench supply with local bulk capacitance and short fat leads.

Cable: Tideland's own cable is #12 AWG for the power conductors, 4.5 m (15 ft), P.N. 510.1235-00.
Junction/distribution boxes accept up to #10 AWG / 6 mm².

## The cable: 9 conductors

Table 2.4, TB-1 connections (JB-5R junction box) — the standard Tideland power and data cable,
P.N. 510.1235-00:

| Wire colour | Signal | JB-5R terminal |
|---|---|---|
| Green | Earth Ground | screw into box |
| **Red** | **(+) Battery Terminal** | 1 |
| **Black** | **(−) Battery Terminal** | 2 |
| Yellow | Rx data (RS-232) | 3 |
| White | Tx data (RS-232) | 4 |
| Brown | Inhibit (+) | 5 |
| Blue | Inhibit (−) | 6 |
| Purple | GO/NO GO (+) | 7 |
| Orange | GO/NO GO (−) | 8 |

Table 2.5, TB-1 connections (DB-5P distribution box) uses the same colours but numbers them 1–9:
Red 1, Black 2, Green 3, Yellow 4, White 5, Brown 6, Blue 7, Purple 8, Orange 9.

### What the non-power pairs do

* **Inhibit (+/−)** — blanking input. "The blanking circuit in the racon uses a high speed optocoupler."
  Drive it from a fixed radar's trigger to stop the racon responding to that radar.
* **GO/NO GO (+/−)** — status output, an isolated transistor. "The circuit can switch an outside current
  source of 1.5 mA or less." "The optoisolator is normally turned on only if there is a racon malfunction."
  In the DB-5P box this drives a form C relay contact "rated at 1 Amp/120 Volt maximum AC or DC".
* **Rx / Tx data** — RS-232C port, used with a hand-held keypad or a PC terminal to program the Morse code
  character, quiescent/active periods, response length, seasonal inhibit, etc.

Also: "The power input to the racon is completely protected internally from reverse polarity, high voltage,
power surges, lightning, and AC ripple", and the ground strap must reach earth ground at under 1 Ω.

## Identifying a custom 4-wire pigtail

If the flying leads are not Tideland's colours, do **not** guess. With the racon unpowered, a meter on
diode/resistance across candidate pairs distinguishes them:

| Pair | What you should see |
|---|---|
| Inhibit (+) / Inhibit (−) | a diode: roughly 1.0–1.3 V one way, open the other (optocoupler LED) |
| GO/NO GO (+) / (−) | open both directions (isolated transistor, off until powered and faulted) |
| Battery + / − | not a clean diode; input filter and protection, some capacitance (meter reading drifts) |
| Rx / Tx data | referenced to the (−)/ground, not isolated |

Confirm the power pair against the housing ground stud before applying any voltage.
