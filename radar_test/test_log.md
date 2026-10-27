# Furuno radar tests: log

Every test run on 25 and 26 Oct 2026, in order. Readings are the peak at the SM200B input unless stated.
Times are Pacific (UTC−7), taken from the time stamps of Sorin's messages; "≈" means worked out from the messages around it.
"Sorin" = Sorin read it or said it; "Spike" = Claude read a Spike screenshot; "I/Q" = Claude's own Python capture.
The same tests grouped by wiring, with Sorin's exact words: Radar tab → "Power readings by test".
"3 MHz" means Spike or I/Q at a bandwidth wide enough to hold the 0.68 µs pulse (close to the true pulse peak);
"100 kHz" readings are 15 to 25 dB lower than the true peak for this pulse.

Radar: Furuno 1722C, long pulse (24 nm range), 2.2 kW peak rating. Supply 12 V 4.64 A on standby (Sorin, 11:59), 12.15 V 4.5 A setting (Sorin, 13:38), 12.1 V 6.35 A transmitting.
Distances are radar to Vivaldi. 11.3 m = 37 ft (Sorin); on 26 Oct Sorin gave the same spot as 11 to 11.5 m. "Pads" are the fixed 8 GHz attenuators in front of the SM200B.

## 25 Oct

| # | Time | Distance | Path to the SM200B | Pads | Foam on radar | Reading | Notes |
|---|---|---|---|---|---|---|---|
| 1 | 11:44 | — | Vivaldi, radar off (background) | 14 dB + manual 50 dB | — | noise −66 dBm (100 kHz) | safe-start reference |
| 2 | 12:15 | 11.3 m (37 ft) | Vivaldi pointed away, whiteboard between, manual attenuator 50 dB | 14 dB | on | −38.8 dBm (I/Q, 10 MHz, one pulse caught); −47.7 dBm (100 kHz). Sorin on Spike (12:26): peak −80, sometimes −70 on Power/Average; −60 to −50 on Log, Min/Max | first sight of the radar, 9.407 GHz |
| 3 | 12:20 | 11.3 m | Vivaldi facing the radar, whiteboard in | 14 dB + manual 50 dB | on | about −44 dBm (Spike 100 kHz, from the grid) | |
| 4 | 12:45 | 11.3 m | Whiteboard out, manual attenuator 0 dB (Sorin, 12:44); Sorin: "we're measuring about -20 dBm" | 14 dB | on | −40.7 dBm (Spike 100 kHz); **−21.5 dBm (Spike 3 MHz)**; −22.2 dBm (I/Q, 50 MS/s) | manual attenuator (rated to 2.5 GHz) gives almost nothing at 9.4 GHz |
| 5 | 12:58–13:10 | 11.3 m | same as 4 | 14 dB | on | pulse 680 ns, rise 40–120 ns, 16 staggered spacings 1606.5–1706.5 µs, 604 pulses/s, rotation 2.5885 s, carrier 9402.6 MHz, bandwidth 1.3 / 2.2 / 7.8 MHz at −3/−10/−20 dB | I/Q captures; full write-up on the Radar tab |
| 6 | 13:15 | 11.3 m | same as 4 (your Spike exports) | 14 dB | on | −44.7 dBm (100 kHz) at 9403.008 MHz; **−20.5 dBm (3 MHz)** at 9403.594 MHz | `data/Furino Characterization/*.csv` |
| 7 | 13:41 | 11.3 m | Vivaldi → pads, manual attenuator removed | 29 dB (3+6+10+10) | **off** | **−20.3 dBm** (Spike 3 MHz) at 9.4078 GHz | foam was worth about 17 dB (later shown to be mixed with leakage) |
| 8 | ≈14:15 | 11.3 m | Vivaldi → limiter → pads | 29 dB | off | **−20 dBm (Sorin)**; −22.9 dBm (Spike 3 MHz screenshot); −46.7 dBm (Spike 100 kHz) | limiter output +9 dBm (Sorin) / +6.1 dBm; within 0.3–2.6 dB of test 7 |
| 9 | ≈14:50 | 11.3 m | bare SMA cable, no Vivaldi, no limiter → pads | 29 dB | off | about −17 dBm (your reading) | **first sign of leakage**: the cable alone picked up more than the antenna |
| 10 | ≈14:55 | 11.3 m | cable → LNA ZX60-5123LN+ (6 V, 0.08 A) → pads | 29 dB | off | nothing seen | Spike had lost the SM200B (USB dropout), not a fault in the LNA |
| 11 | 16:29 | 11.3 m | Vivaldi → pads | 29 dB | off | −29.4 dBm (I/Q) | 9 dB below test 7; cause not found |
| 12 | ≈16:35 | 11.3 m | Vivaldi → limiter → pads | 29 dB | off | −30.2 dBm (I/Q) | **limiter loss 0.8 dB** vs test 11 (datasheet 0.5 typ, 1.5 max) |
| 13 | 16:44 | **3.96 m (13 ft)** | Vivaldi → limiter → pads | 29 dB | off | **−12.9 dBm** (I/Q 6 s), −12.6 dBm (I/Q 50 MS/s) | limiter output +16.2 dBm (datasheet flat leakage +13 to +17); no leading-edge spike at 20 ns resolution |
| 14 | 16:45 | 3.96 m | Vivaldi → limiter → pads (same as 13), Spike ref −20 dBm (may be compressed) | 29 dB | off | −15.27 dBm (Sorin's Spike screenshot) | limiter output +13.7 dBm; reads low because of the reference level |
| 15 | 16:49 | 3.96 m | Vivaldi → pads, limiter out | 29 dB | off | −25.9 dBm (Spike 3 MHz) | lower than WITH the limiter: impossible unless something other than the antenna dominates |
| 16 | 16:52 | 3.96 m | **50 Ω load → pads** (no Vivaldi, no cable) | 29 dB | off | **−20.5 dBm** (Spike 3 MHz) | **leak confirmed**: more than with the antenna |
| 17 | 16:55 | 3.96 m | 50 Ω load on a cable, no pads | 0 | off | **−15.7 dBm** (Spike 3 MHz) | cable and joints add to the leak |

## 26 Oct

| # | Time | Distance | Path to the SM200B | Pads | Foam on radar | Reading | Notes |
|---|---|---|---|---|---|---|---|
| 18 | 17:37 | 3.96 m | Vivaldi (short cable) → limiter → LNA **unpowered** → pads | 29 dB | off | about −10 dBm (your reading) | not safe to power the LNA as wired: limiter output up to +17 dBm vs LNA max input +15 dBm; plan: add a 10 dB pad before the LNA |
| 19 | 18:13 | 3.96 m | 50 Ω load (Mini-Circuits ANNE-50L+, s/n 3-1909) → pads | 29 dB | off | live trace about −90 dBm, persistence −78 dBm (Average detector) | Average detector hides the pulse peaks; do not use for leakage |
| 20 | 18:16 | 3.96 m | 50 Ω load → pads | 29 dB | off | **−22.9 dBm** (Spike 3 MHz, Min/Max, Max Hold) | same leak as test 16 |
| 21 | 18:19 | 3.96 m | **50 Ω load directly on the SM200B input** | 0 | off | **−22.5 dBm** | leak enters the SM200B itself, not only the pads |
| 22 | 18:22 | 3.96 m | load directly on input, **SM200B wrapped in AN-72** (front exposed) | 0 | off | −25.7 dBm (Spike Max Hold); "around -30" (Sorin, live trace) | foam on the box helps about 3 dB |
| 23 | 18:26 | 3.96 m | load directly on input, wrapped, **whiteboard between radar and SM200B** | 0 | off | −19.43 dBm (Sorin) | metal sheet in a reflective room does not shadow reliably |
| 24 | 18:33 | 3.96 m | load directly on input vs load → pads | 0 vs 29 dB | off | −19 dBm vs −25 dBm | about −25 dBm enters the SM200B whatever is on its input; about −20 dBm more enters at the load and adapter when they are directly on the input |
| 25a | 18:40 | **11.5 m** | 50 Ω load → pads (no antenna), whiteboard between | 29 dB | off | −34 to −32 dBm (your reading) | leak floor at the long distance, whiteboard in |
| 25b | 18:40 | 11.5 m | 50 Ω load → pads, **whiteboard out** | 29 dB | off | **−31.2 dBm** (Spike 3 MHz, Min/Max, Max Hold) | whiteboard changes the leak by only about 1–3 dB here. Test 7 (−20.3) was 11 dB above this; tests 11 (−29.4) and 12 (−30.2) were AT it, so the 0.8 dB limiter loss is not trustworthy |
| 26a | 18:43 | 11.5 m | 50 Ω load → limiter → 10 dB pad → LNA **unpowered** → 29 dB pads (10+10+6+3), whiteboard out | 10 before LNA + 29 after | off | **about −31 dBm** (your reading) | same as the load alone (25b): the limiter and LNA add no pickup of their own |
| 26b | 18:43 | 11.5 m | same, LNA **powered** (6 V) | 10 + 29 dB | off | **−28 dBm** (your reading) | +3 dB over 26a: pickup between the load and the LNA input (limiter, 10 dB pad, joints), amplified 22 dB, about equals the leak entering after the LNA. Leak floor for test 27 is −28 dBm |
| 26c | 18:48 | 11.5 m | 50 Ω load → limiter → 20 dB (10+10) → LNA powered → 19 dB (10+6+3) | 20 + 19 dB | off | **−24.06 dBm** (your reading) | leak floor for the test-27 wiring; 4 dB above 26b because 10 dB less padding after the LNA |
| 27 | 18:50 | 11.5 m | Vivaldi → limiter → 20 dB → LNA (6 V) → 19 dB → SM200B, whiteboard out | 20 + 19 dB | off | **−7.94 dBm** at 9.4047 GHz (Spike 3 MHz, Min/Max, Max Hold 20 s, ref +10 dBm); −11.4 dBm at ref −20 was clipped | 16 dB above the 26c floor (−24.06). LNA output about +11.1 dBm; with the input estimated from test 7 (+8.7 − 0.8 − 20 = −12.1 dBm) the LNA gain is about 23 dB (datasheet about 22) |
| 28 | 18:52 | 11.5 m | same as 27, LNA **unpowered** | 20 + 19 dB | off | **−25.85 dBm** at 9.4047 GHz (Spike 3 MHz, ref +10) | 17.9 dB below 27. This is near the leak floor (−24 to −31), so it is leak plus whatever leaks through the off LNA, not a clean off-state loss; on/off difference is a lower bound on the gain |

## What the tests show

1. **Radar signal (tests 4–6):** fully characterized; leakage does not change these figures.
2. **SM200B safety:** the highest reading in any test was −7.94 dBm (test 27), 28 dB under the +20 dBm limit.
3. **Leakage (tests 9, 15–24):** the radar gets into the SM200B directly at about −20 to −25 dBm at 13 ft. Power levels in tests 8–18 are mixed with it and are not reliable as antenna levels; test 7 is 11 dB above the 11.5 m floor and mostly signal.
4. **Limiter:** the 0.8 dB loss from tests 11–12 was measured at the leak floor (test 25b) and is not trustworthy. Output +16.2 dBm at 13 ft (test 13), within its rated clamping level, but the input level for that test is not known, so clamping is not yet shown.
5. **Leak floor at 11.5 m (tests 25–26):** −31 dBm with a load on the pads, whiteboard in or out; −28 dBm with the LNA powered and a load on the limiter input; −24 dBm with 20 dB before and 19 dB after the LNA.
6. **LNA (tests 27–28):** Vivaldi → limiter → 20 dB → LNA → 19 dB read −7.94 dBm with the LNA on, 16 dB above the floor, and −25.85 dBm with it off. With the LNA input estimated from test 7 (about −12 dBm), the gain is about 23 dB (datasheet about 22). The on/off difference (17.9 dB) is limited by the leak.

## Lessons

- The JFW manual attenuator is rated DC–2.5 GHz and does almost nothing at 9.4 GHz.
- Spike's Average detector reads far below a radar pulse peak; use Min/Max, Log, 3 MHz RBW, Max Hold.
- Spike resets to defaults after every SM200B reconnect; check settings each time.
- Only one Spike window at a time.
- Repeat the load test at the start of every setup: the leak must be 20 dB below the reading being trusted.
