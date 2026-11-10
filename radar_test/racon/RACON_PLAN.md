# Racon recording plan: Furuno 1722C/NT + SeaBeacon 2 racon, received by our RX front end and the SM200B

Goal: a reference for the JACON. Record exactly what a real racon sends back to a real radar: frequency, Morse timing,
delay, frequency stability, and how loud each source is, then compare our system against it.

## What gets measured

| Question | How |
|---|---|
| What frequency does the racon reply on? Does it follow the radar? | phase slope over each element vs the radar pulse it answers; survey sweep 9.0-10.0 GHz for anything off the radar's frequency |
| Dot, dash, gap durations; whole reply length; the letter | half-power edges of each element; dots and dashes split by duration (2-means), decoded |
| Delay from radar pulse to reply | start of first racon element minus start of the radar pulse, every reply |
| Frequency wobble and chirp inside an element; scatter between replies | instantaneous frequency (phase derivative) inside each element |
| Does the racon keep phase from one element to the next? | phase carried forward with the element frequency, compared with the next element (R = 1 means one continuous oscillator) |
| Rise and fall times | 10-90 % of each element's level |
| How loud at our antenna; how loud at the source (EIRP); antenna gain | SM200B level minus chain gain = antenna port; plus free-space loss minus Vivaldi gain = EIRP; minus datasheet TX power = antenna gain |
| How often it answers; does it go quiet (on/off cycle) | 30 s stream: every event's time and level |
| Radar for comparison | pulse width, PRI, rotation, frequency, pulse-to-pulse scatter, beam pattern over a rotation |
| Does the racon reply louder when hit harder? | reply level vs radar pulse level, per interaction |

## Before plugging in

1. Edit `racon_setup.py`: the chain (each part and its gain), distances antenna to antenna (radar to our Vivaldi, racon to our Vivaldi, radar to racon), foam on/off.
2. Close Spike (one program owns the SM200B). SM200B straight into a USB 3 port, not the dongle.
3. Racon on 12 V from a stiff supply (it pulls up to 15 A peaks; source under 0.05 ohm, short fat leads, bulk capacitance).

## Level budget (check it against the setup on the day)

| Source | EIRP | At our antenna (8 dBi Vivaldi) | At LNA input (1 dB cable, 0.8 dB limiter, 20 dB pad) | At SM200B (+23 dB LNA, 19 dB pads) |
|---|---|---|---|---|
| Racon at 1 m | +36 dBm (spec) | -8 dBm | -30 dBm | -26 dBm |
| Racon at 3 m | +36 dBm | -17.5 dBm | -39 dBm | -35 dBm |
| Furuno at 11.3 m, foam on | about +57 dBm (25 Oct) | -8 dBm | -30 dBm | -26 dBm |
| Furuno at 11.3 m, foam off | about +74 dBm (25 Oct) | +9 dBm | -13 dBm | -9 dBm |

Everything stays well under the SM200B's +20 dBm. **Foam off puts about -13 dBm into the LNA and +10 dBm out of it: check the LNA's
compression point before taking the foam off.** `check` stops the run if anything comes within 10 dB of +20 dBm at the SM200B.

## On the day (one pass per setup)

1. **Load test first** (the radar leaks straight into the SM200B at -20 to -25 dBm at 13 ft): Vivaldi replaced by a 50 ohm load, radar and racon on.
   `python racon_capture.py go --tag load` → shows what leaks in without the antenna. It must be 20 dB under the levels we trust.
2. **Antenna back on**, aimed between the radar and the racon. `python racon_capture.py go`
   - `check` (3 s): peak level, headroom, noise; sets the reference level for the rest.
   - `survey` (10 s): 9.0-10.0 GHz max hold plus every sweep as a waterfall. If the racon shows up away from the radar's frequency, rerun the rest with `--center`.
   - `seg` (8 captures of 250 snippets, about 3.5 s): 250 MS/s, 160 MHz wide, video-triggered, 3 us before to 50 us after each trigger. The fine detail.
   - `stream` (30 s, at least 11 rotations): 50 MS/s, 41.5 MHz wide, every event timed. The statistics, rotation and the racon's on/off cycle.
   - Plots appear in `plots/` straight away; summary in `data/<run>_summary.json`, every element in `data/<run>_elements.csv`.
3. Optional, same setup: racon off → `go --tag radar_only`; radar's beam stopped pointing at the racon if the radar allows it.

Time: about 1.5 min of recording per `go`, plus 1-2 min of analysis.

## Plots made for every run (each with the wiring strip)

| File | What |
|---|---|
| `_chain.png` | one whole interaction: envelope with every part labelled, STFT, instantaneous frequency, raw I and Q |
| `_parts.png` | each part on its own: radar pulse, dot, dash, dot; envelope, STFT, frequency inside it |
| `_replies.png` | every trigger as one row of a waterfall, and the raw I of 40 interactions stacked |
| `_stats.png` | durations, gaps, delay, racon minus radar frequency, frequency over time, wobble, power over time, reply vs radar level, codes |
| `_loudness.png` | SM200B, antenna port, EIRP measured vs spec for both sources; implied antenna gains; the racon's trigger range for this radar |
| `_timeline.png` (stream) | every event's level over 30 s, and the time between events |
| `_survey.png` | 9.0-10.0 GHz max hold and waterfall |

## Limits of the numbers

- EIRP and implied antenna gains assume 8 dBi for the Vivaldi (not measured). Every dB it is off moves them 1 dB the other way.
  A two-antenna Friis measurement (two identical Vivaldis, the ADF5355 at 9.4 GHz, SM200B) would pin it to about 1 dB.
- Pads and cable are nominal unless measured on the VNA; the chain gain is only as good as `racon_setup.py`.
- The SM200B removes the carrier: the I/Q is the signal relative to the centre frequency. Real 9.4 GHz cycles are not recorded.
- Multipath off the bench, walls and people changes levels by several dB; note what is nearby.

Tested before the bench on synthetic data (`make_synthetic.py`, files named `synthetic_*`) and on the 25 Oct radar recording.
