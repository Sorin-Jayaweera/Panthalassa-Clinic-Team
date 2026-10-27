"""Radar tab, top section: every over-the-air power reading of 25 and 26 Oct 2026, grouped by what was on the SM200B input.

Each test is one sentence that expands. Inside: Sorin's own words and numbers (quoted from the session transcript; times are
Pacific, UTC-7), the setup, then a collapsed "AI analysis" with derived numbers. The same tests in one table:
radar_test/test_log.md. Who read each number: "Sorin" = Sorin read it off Spike or said it; "Spike" = Claude read a
Spike screenshot; "I/Q" = Claude's own Python capture from the SM200B."""
from content import item, table, ul, p, h, fig

# The radar: Furuno 1722C/NT, long pulse (24 nm range), 9402.6 MHz, 0.68 us pulses, 604 pulses/s, 2.2 kW peak (spec).
# Pads: fixed 8 GHz-rated SMA attenuators. "29 dB" = 3 + 6 + 10 + 10. "14 dB" = 10 + 2 + 2.

T = {}


def t(n, date, time, dist, chain, cond, sm, who, far, sorin, setup, ai):
    T[n] = dict(n=n, date=date, time=time, dist=dist, chain=chain, cond=cond, sm=sm, who=who, far=far, sorin=sorin, setup=setup, ai=ai)


LEAK = "no source in the chain; this is radar leaking straight into the SM200B, cables and pads"

# ------------------------------------------------------------------ A. 50 ohm load
t("16", "25 Oct", "16:52", "3.96 m (13 ft)", "50 &Omega; load &rarr; 29 dB pads &rarr; SM200B", "foam off",
  "&minus;20.5 dBm", "Spike", LEAK,
  ["&ldquo;I unplugged the vivaldi and long cable it was connected to, and put a 50 ohm termination&rdquo; (16:51)."],
  ["Load in place of the Vivaldi and its long cable; the 29 dB of pads stayed on the SM200B."],
  ["More than the Vivaldi read in the same place a few minutes earlier (test 15, &minus;25.9 dBm). First proof that most of what the SM200B saw at 13 ft did not come through the antenna.",
   "A 50 &Omega; load cannot receive anything, so every dBm here is leakage: through the SM200B case and leads, the pads, the joints."])
t("17", "25 Oct", "16:55", "3.96 m (13 ft)", "50 &Omega; load directly on the SM200B input (no pads)", "foam off",
  "&minus;15.7 dBm", "Spike", LEAK,
  ["&ldquo;terminator is on the signal hound input now, no pads. Just 50 ohm term to a line to the signal hound&rdquo; (16:54)."],
  ["The 29 dB of pads removed; the 50 &Omega; termination screwed straight onto the SM200B input. No cable."],
  ["5 dB more than the load through 29 dB of pads (test 16) a few minutes earlier: adding 29 dB took off only 5 dB, so most of the leak enters the SM200B itself, not through its input.",
   "Same wiring as test 21 the next day (&minus;22.5 dBm); the 7 dB difference is the radar and SM200B not being in exactly the same places and the cables around them.",
   "SM200B safety: 35 dB under its +20 dBm limit."])
t("20", "26 Oct", "18:13&ndash;18:16", "3.96 m (13 ft)", "50 &Omega; load (ANNE-50L+) &rarr; 29 dB pads &rarr; SM200B", "foam off",
  "&minus;22.9 dBm", "Spike", LEAK,
  ["&ldquo;Can I use a DC-12 gigahertz MCLANNE-50L plus serial number 3-1909 50 ohm load? I'm going to put it after all the attenuators, so I'll still have 29 dB.&rdquo; (18:12)",
   "&ldquo;spike is open, radar is on. Look at the screen. This is with the 29 dB attenuators and then the 50 ohm load.&rdquo; (18:13)"],
  ["Load: Mini-Circuits ANNE-50L+ (DC&ndash;12 GHz), serial 3-1909, screwed onto the last pad.",
   "First read with Spike on its default Average detector (live trace about &minus;90 dBm, persistence &minus;78 dBm), then with Min/Max, Log, 3 MHz RBW, Max Hold: &minus;22.9 dBm."],
  ["The Average-detector numbers are not peak readings: they average a 0.68 &micro;s pulse with 1.6 ms of silence. Claude first called that a &minus;90 dBm leak; it was wrong and corrected 3 minutes later.",
   "Same wiring as test 16 the day before (&minus;20.5): the leak at 13 ft with 29 dB of pads is about &minus;21 to &minus;23 dBm."])
t("21", "26 Oct", "18:19", "3.96 m (13 ft)", "50 &Omega; load directly on the SM200B input", "foam off",
  "&minus;22.5 dBm", "Spike", LEAK,
  ["&ldquo;Is the 50 ohm load going directly into the +20 dBm max port? Is it okay for me to turn on the radar?&rdquo; (18:18)"],
  ["Pads removed; the ANNE-50L+ load screwed straight onto the SM200B&rsquo;s Type N input (through its SMA adapter)."],
  ["Same as with 29 dB of pads in front (test 20). So the leak is not coming through the pads: it gets into the SM200B itself."])
t("22", "26 Oct", "18:22", "3.96 m (13 ft)", "50 &Omega; load directly on the input, SM200B wrapped in AN-72 foam", "foam off the radar",
  "&minus;25.7 dBm (Max Hold)", "Spike", LEAK,
  ["&ldquo;So I just wrapped most of the outside of the signal found in the AN72 foam board. The front is still exposed, and it's not like tight around it, but it is around it fairly strongly. I'm going to test again the exact same setup where it's 50 ohm low directly into the plus 20 dBm max port.&rdquo; (18:22)",
   "&ldquo;Radar is now on. It is at around -30.&rdquo; (18:22)"],
  ["AN-72 absorber around the SM200B case, front panel and connector exposed."],
  ["Sorin saw about &minus;30 dBm on the live trace; Max Hold over the run caught &minus;25.7 dBm. The foam on the box takes about 3 dB off the leak."])
t("23", "26 Oct", "18:26", "3.96 m (13 ft)", "50 &Omega; load directly on the input, SM200B wrapped, whiteboard between the radar and the SM200B", "foam off the radar",
  "&minus;19.43 dBm", "Sorin", LEAK,
  ["&ldquo;Holy shit. I put the whiteboard in between the SM200B and the radar, and I got negative 19.43 dBm immediately when I turned it on. So we got much stronger values than before. My understanding of metal as Faraday cages might be wrong, because this is a solid block of metal instead of having holes. [&hellip;] Is the whiteboard acting like a transmitting antenna?&rdquo; (18:26)",
   "&ldquo;I forgot that we don't have the attenuators on right now.&rdquo; (18:31)"],
  ["Whiteboard (metal sheet) standing between the radar and the SM200B; no pads."],
  ["6 dB more than without the board (test 22). The board is not transmitting: it reflects. In a room, a metal sheet sends energy round its edges and off the walls, and the 2.6 s rotation means the beam sweeps across many paths. A sheet only shadows well when it is much bigger than the beam and nothing reflects behind it."])
t("24", "26 Oct", "18:33", "3.96 m (13 ft)", "50 &Omega; load &rarr; 29 dB pads &rarr; SM200B", "SM200B wrapped in AN-72, whiteboard between, foam off the radar",
  "&minus;25 dBm", "Sorin", LEAK,
  ["&ldquo;when I put in the attenuators, I go from -19 dBm to -25 dBm. Which means a lot of it is still coupling to the front end and only a little bit is coupling to the end and then going through the attenuators.&rdquo; (18:33)"],
  ["Test 23&rsquo;s setup (&minus;19 dBm) with the 29 dB of pads put back between the load and the SM200B."],
  ["Adding 29 dB took off only 6 dB. About &minus;25 dBm gets into the SM200B whatever is on its input (case, front panel, USB and power leads); the extra 6 dB entered at the load and adapter when they sat directly on the input.",
   "Rule from this: a reading must be at least 20 dB above the load reading for the same wiring before it can be called signal."])
t("25a", "26 Oct", "18:40", "11.3&ndash;11.5 m (37 ft)", "50 &Omega; load &rarr; 29 dB pads &rarr; SM200B", "whiteboard in, foam off",
  "&minus;34 to &minus;32 dBm", "Sorin", LEAK,
  ["&ldquo;The radar is now 11 meters away. The whiteboard is still in the way. It's just the 50 ohm and then attenuators. I'm turning it on.&rdquo; (18:39)",
   "&ldquo;Right now it's transmitting the direct path from radar at 11.5 meters away to the SM200B with just the 50 ohm load and attenuators.&rdquo;",
   "&ldquo;I measure a background of negative 34 to negative 32 dBm. I'm now moving the whiteboard out of the way to measure.&rdquo; (18:40)"],
  ["Radar moved back to the 25 Oct position."],
  ["About 10 dB less leak than at 13 ft, as expected for 2.9&times; the distance (20 log 2.9 = 9.3 dB)."])
t("25b", "26 Oct", "18:40", "11.3&ndash;11.5 m (37 ft)", "50 &Omega; load &rarr; 29 dB pads &rarr; SM200B", "whiteboard out, foam off",
  "&minus;31.2 dBm", "Spike (Sorin confirmed)", LEAK,
  ["&ldquo;with the whiteboard out of hte way I got the -31.2 dBm&rdquo;"],
  ["Spike: 3 MHz RBW, Min/Max, Max Hold, 9.40625 GHz. Screenshot: <code>radar_test/spike_screens/test25b_leak_50ohm_load_29dB_pads_11p5m_whiteboard_out_rbw3MHz.jpg</code>."],
  ["<b>The leak floor at 11.5 m.</b> The whiteboard changes it by only 1&ndash;3 dB at this distance.",
   "What it means for 25 Oct: test 7 (Vivaldi, &minus;20.3 dBm) was 11 dB above this, so mostly signal. Tests 11 and 12 (&minus;29.4, &minus;30.2) were at this floor, so they were mostly leak and the 0.8 dB limiter loss taken from them cannot be trusted."])
t("26a", "26 Oct", "18:43", "11.5 m", "50 &Omega; load &rarr; limiter &rarr; 10 dB &rarr; LNA (off) &rarr; 10 + 10 + 6 + 3 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;31 dBm", "Sorin", LEAK,
  ["&ldquo;Okay, it's now 50 ohm load, then power limiter, then the amplifier, which is currently turned off, and then the attenuators to the signal mount.&rdquo; (18:42)",
   "&ldquo;We got the same negative 31 dBm.&rdquo; (18:43)",
   "&ldquo;The setup as it is right now is power limiter, then 10 dB, then amplifier, and then 10 dB, then 10 dB, then 6 dB, then 3 dB attenuators. This is how it has been&rdquo; (18:46)"],
  ["Load on the limiter input (where the antenna goes). 10 dB before the LNA, 29 dB after."],
  ["Same as the load alone (25b): the limiter, the extra pad and the unpowered LNA add no pickup of their own."])
t("26b", "26 Oct", "18:43", "11.5 m", "50 &Omega; load &rarr; limiter &rarr; 10 dB &rarr; LNA (on, 6 V) &rarr; 29 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;28 dBm", "Sorin", LEAK,
  ["&ldquo;I'm going to turn on the amplifier. Amplifier is on.&rdquo; &ldquo;With the amplifier on, we get -28 dBm.&rdquo; (18:43)"],
  ["As 26a with the LNA powered at 6 V."],
  ["+3 dB over 26a. A 3 dB rise means a second leak of the same size has been added: pickup between the load and the LNA input (limiter, pad, joints), amplified 22 dB, about equals the leak that enters after the LNA. The LNA is not oscillating (that would raise the whole span or show a line away from 9.4 GHz)."])
t("26c", "26 Oct", "18:48", "11.5 m", "50 &Omega; load &rarr; limiter &rarr; 10 + 10 dB &rarr; LNA (on) &rarr; 10 + 6 + 3 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;24.06 dBm", "Sorin", LEAK,
  ["&ldquo;Instead of this now, the 50 ohm load, then the power limiter, then 2 10 dB attenuators, then the amplifier, and then 10 dB, 6 dB, 3 dB, then signal hound.&rdquo; (18:48)",
   "&ldquo;I'm turning on the amplifier and turning on the radar. I read -24.06 dBm at the peak.&rdquo; (18:48)"],
  ["One 10 dB pad moved from after the LNA to before it, so the LNA stays linear when the antenna goes back on (test 27)."],
  ["<b>The leak floor for tests 27 and 28.</b> 4 dB above 26b because there is 10 dB less padding after the LNA."])

# ------------------------------------------------------------------ B. Vivaldi
t("1", "25 Oct", "11:44", "11.3 m (37 ft)", "Vivaldi &rarr; JFW manual attenuator at 50 dB &rarr; 10 + 2 dB &rarr; SM200B", "radar off",
  "noise &minus;66 dBm (100 kHz RBW)", "I/Q", "radar off: background only",
  ["&ldquo;I have a 10 dBm 8G attenuator, a 2 dBm 8G attenuator, then going to a manual attenuator. [&hellip;] model 50DR-046SMA, serial 803383-2225, made by JFW Industries&rdquo; (11:11)",
   "&ldquo;It is 37 feet away. [&hellip;] The Vivaldi is really bad at picking up stuff. It's noisy. It's also pointed away. And I put [&hellip;] a whiteboard in between the direct line of sight path. Plus there's the foam on the radar. Plus I have all the attenuators.&rdquo; (12:03)",
   "&ldquo;To assuage your fears, I added another 2 dB at 8G attenuator.&rdquo; (12:06) &rarr; 10 + 2 + 2 = 14 dB.",
   "Radar supply: &ldquo;I see 12 volts, 4.64 amps. The radar is not spinning, but I see the screen on.&rdquo; (11:59)"],
  ["Safe-start reference before the radar transmitted."],
  ["The JFW 50DR-046 is rated DC&ndash;2.5 GHz. At 9.4 GHz it gives almost no attenuation whatever the dial says, so it is not counted in any later number."])
t("2", "25 Oct", "12:15", "11.3 m (37 ft)", "Vivaldi pointed away &rarr; manual attenuator 50 dB &rarr; 14 dB &rarr; SM200B", "whiteboard in, AN-72 foam on the radar",
  "&minus;38.8 dBm (one pulse, 10 MHz)", "I/Q", "not worked out (antenna pointed away)",
  ["&ldquo;The radar is on.&rdquo; (12:13) &ldquo;it does show lp.&rdquo; (12:18, long pulse)",
   "&ldquo;I did set ref level to 0, so now you see the peak at like negative 80, sometimes going up to like negative 70, and div is 10 dB per division. [&hellip;] when I change to log power and min max, I see the noise floor and I see the spike going up to like 60, negative 60, negative 50 ish [&hellip;] Before I was looking at it on power with average, and average power was the thing that was like negative 60.&rdquo; (12:26)"],
  ["First sight of the radar, 9.407 GHz. Radar range set to 24 nm (long pulse)."],
  ["&minus;47.7 dBm at 100 kHz RBW. Sorin&rsquo;s &minus;80/&minus;70 dBm readings were on Spike&rsquo;s default Average detector and Power units, which read far below a pulse peak; Min/Max showed &minus;60 to &minus;50 dBm."])
t("3", "25 Oct", "12:20", "11.3 m (37 ft)", "Vivaldi facing the radar &rarr; manual attenuator 50 dB &rarr; 14 dB &rarr; SM200B", "whiteboard in, foam on",
  "about &minus;44 dBm (100 kHz RBW)", "Spike", "not worked out (100 kHz only)",
  ["&ldquo;it does show lp. I am turning the vivaldi to face now (10 seconds)&rdquo; (12:18)"],
  ["Spike, 100 kHz RBW, read from the grid."],
  ["Only a 100 kHz reading, which is 15&ndash;25 dB under the true pulse peak for a 0.68 &micro;s pulse."])
t("4", "25 Oct", "12:45&ndash;13:15", "11.3 m (37 ft)", "Vivaldi facing &rarr; manual attenuator 0 dB &rarr; 14 dB &rarr; SM200B", "whiteboard out, foam on",
  "&minus;21.5 dBm (Spike 3 MHz); &minus;20.5 dBm in Sorin&rsquo;s export; &minus;22 dBm I/Q", "Spike, Sorin, I/Q", "&asymp; &minus;7 dBm at the Vivaldi output",
  ["&ldquo;The whiteboard is out of the way, and I set the manual attenuator to 0 dB.&rdquo; (12:44)",
   "&ldquo;How much time is between each of the pulses? I see it on the spectrogram. I just don't see labels.&rdquo; (12:51)",
   "&ldquo;spike is closed, measure this all yourself.&rdquo; (12:57)",
   "&ldquo;Given that we're measuring about -20 dBm and that we have 14 dB of attenuation that's at that range, what is the actual power level that we are receiving from the furino to the Vivaldi?&rdquo; (13:06)",
   "Sorin&rsquo;s Spike exports: <code>data/Furino Characterization/14db8G_11meters_100khzrbw.csv</code> and <code>14db8G_11meters_3mhzrbw.csv</code>."],
  ["One setup, read three ways: Spike 100 kHz RBW &minus;40.7 dBm and 3 MHz RBW &minus;21.5 dBm (Claude, screenshots); Sorin&rsquo;s exports 100 kHz &minus;44.7 dBm at 9403.008 MHz and 3 MHz &minus;20.5 dBm at 9403.594 MHz; Claude&rsquo;s I/Q captures (6.25 and 50 MS/s) &minus;22 dBm."],
  ["Vivaldi output &asymp; &minus;21 + 14 = &minus;7 dBm (cable loss not included). EIRP through the foam (8 dBi Vivaldi assumed): &minus;6.5 &minus; 8 + 72.97 = +58.5 dBm.",
   "Pulse and timing from the I/Q captures: 680 ns at half power; rise 40 ns (20&ndash;120); carrier 9402.6 MHz; bandwidth 1.3 / 2.2 / 7.8 MHz at &minus;3 / &minus;10 / &minus;20 dB; 16 staggered spacings 1606.5&ndash;1706.5 &micro;s (mean 1655 &micro;s, 604 pulses/s); rotation 2.5885 s; second harmonic not seen. Leakage does not change these. Full plots further down this tab.",
   "Leak check was not done that day. With only 14 dB of pads the leak could be up to about 15 dB above the &minus;31 dBm seen with 29 dB (test 25b), so this power reading may include a few dB of leak."])
t("7", "25 Oct", "13:41", "11.3 m (37 ft)", "Vivaldi &rarr; 3 + 6 + 10 + 10 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;20.3 dBm", "Spike", "&asymp; +8.7 dBm at the Vivaldi output",
  ["&ldquo;I'm removing the manual attenuator because that was useless.&rdquo; (13:27)",
   "&ldquo;I have 3 dB and then two 10 dB 8G attenuators going straight to the Vivaldi. [&hellip;] I put 12.15 volts and 4.5 amps right now into the Farino&rdquo; (13:38)",
   "&ldquo;Because I was worried, I made it 3 dB, then 6 dB, and then 2 10 dBs. I'm going to start transmitting now.&rdquo; (13:41) &ldquo;I turned on persistance&rdquo;"],
  ["Foam taken off the radar. 9.4078 GHz. Screenshot: <code>radar_test/spike_screens/step1_no_limiter_foam_off_29dB_pads_11m_rbw3MHz.jpg</code>."],
  ["Vivaldi output = &minus;20.3 + 29 = +8.7 dBm. EIRP (AI, 8 dBi Vivaldi assumed): +73.7 dBm.",
   "11 dB above the leak floor measured later at the same distance (test 25b, &minus;31.2 dBm), so mostly signal; the leak could add up to about 0.3 dB.",
   "Compared with test 4 (foam on, 14 dB): +15 dB more at the antenna with the foam off. Earlier pages called the foam worth 17 dB; with leak in both readings, &ldquo;about 15 dB&rdquo; is the safer figure."])
t("11", "25 Oct", "16:29", "11.3 m (37 ft)", "Vivaldi &rarr; 29 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;29.4 dBm", "I/Q", "&asymp; &minus;0.4 dBm at the Vivaldi (unreliable)",
  ["&ldquo;right now I only have the vivaldi to the 10+10+3+6 db attenuators. Turning on the radar&rdquo; (16:24)"],
  ["Same wiring as test 7, three hours later."],
  ["9 dB below test 7 with nothing obviously changed. It sits at the leak floor (25b, &minus;31.2), so it is mostly leak. Cause of the drop not found: antenna or cable position is the likely reason."])
t("15", "25 Oct", "16:49", "3.96 m (13 ft)", "Vivaldi &rarr; 29 dB &rarr; SM200B (limiter removed)", "foam off",
  "&minus;25.9 dBm", "Spike", "not valid (below the leak)",
  ["&ldquo;so I should remove the limiter and just have the vivaldi into the attenuators, right?&rdquo; &ldquo;it is connected. Transmitting now. Spike is closed.&rdquo; (16:48)"],
  ["Limiter taken out of the test 13 wiring."],
  ["Lower than with the limiter in (test 13). A limiter cannot add power, so something other than the antenna dominated: this is what led to the load tests (16 onward)."])

t("8", "25 Oct", "&asymp; 14:15", "11.3 m (37 ft)", "Vivaldi &rarr; limiter &rarr; 3 + 6 + 10 + 10 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;20 dBm (Sorin); &minus;22.9 dBm (Spike screenshot)", "Sorin and Spike", "&asymp; +9 dBm at the limiter output",
  ["&ldquo;With the 10+10+3+6 dB 8G attenuators and no foam on with the furuno 11.3 meters away, I plugged in the power limiter. I measured -20 dBm.&rdquo; (14:59)"],
  ["Marki EVAL-HLM-20P, input side toward the antenna. Spike 100 kHz RBW at the same time: &minus;46.7 dBm."],
  ["Limiter output = &minus;20 + 29 = +9 dBm (Sorin&rsquo;s reading) or +6.1 dBm (screenshot). Both below the +13 to +17 dBm clamp level, so the limiter should only be passing the signal with its 0.5&ndash;0.7 dB loss.",
   "Compared with test 7 (no limiter): within 0.3 to 2.6 dB, so consistent with a small loss, but the leak at this distance (about &minus;31 dBm) is only 9&ndash;11 dB below."])
t("12", "25 Oct", "16:35", "11.3 m (37 ft)", "Vivaldi &rarr; limiter &rarr; 29 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;30.2 dBm", "I/Q", "&asymp; &minus;1.2 dBm at the limiter output (unreliable)",
  ["&ldquo;radar on standby, i put in just the power limiter. Is the EVAL HLM 20 P directional? Does it matter which side is in vs out?&rdquo; (16:33)",
   "&ldquo;radar is back on with the power limiter in&rdquo;; &ldquo;spike closed&rdquo;; &ldquo;it should be around 30 dBm&rdquo; (between 16:35 and 16:42; what it referred to was not written down)."],
  ["Limiter added to the test 11 wiring."],
  ["0.8 dB below test 11. That was reported as the limiter&rsquo;s loss (datasheet 0.5 typical, 1.5 max), but both readings sit at the leak floor (25b), so <b>the 0.8 dB is not a trustworthy measurement</b>."])
t("13", "25 Oct", "16:44", "3.96 m (13 ft)", "Vivaldi &rarr; limiter &rarr; 29 dB &rarr; SM200B", "foam off",
  "&minus;12.9 dBm (I/Q); &minus;15.27 dBm (Sorin&rsquo;s Spike screenshot)", "I/Q, Sorin", "&asymp; +16.2 dBm at the limiter output",
  ["&ldquo;the radar is 13 feet from the antenna, and about 26 from me.&rdquo; (16:42)",
   "&ldquo;I moved it closer to test the power limiter like you said. Can I turn on the radar?&rdquo; (16:43)"],
  ["Radar moved to 13 ft to push the limiter into clamping. Read two ways: Claude&rsquo;s I/Q (&minus;12.9 dBm over 6 s, &minus;12.6 at 50 MS/s) and Sorin&rsquo;s Spike screenshot at 16:45 (&minus;15.27 dBm, reference level &minus;20 dBm).", "&ldquo;remember to try to use spike instead of your own measurements&rdquo; (16:46). &ldquo;can I turn off the radar? Do we have enough close range data?&rdquo; (16:46)"],
  ["Limiter output = &minus;12.9 + 29 = +16.1 dBm, inside the datasheet flat-leakage range (+13 to +17 dBm). No leading-edge spike was seen at 20 ns resolution.",
   "<b>But clamping is not proven</b>: the input to the limiter was not measured (test 15, meant to be the no-limiter reference, was swamped by leak), and the leak at 13 ft (about &minus;21 to &minus;23 dBm) is only 8&ndash;10 dB below this reading.",
   "Spike&rsquo;s &minus;15.27 dBm was with the reference level at &minus;20 dBm, so a &minus;13 to &minus;15 dBm peak sat above the top of the screen and could be compressed; it agrees with the I/Q within 2.4 dB."])

t("18", "26 Oct", "17:37", "3.96 m (13 ft)", "Vivaldi (short cable) &rarr; limiter &rarr; LNA (off) &rarr; 29 dB &rarr; SM200B", "foam off",
  "&minus;10 dBm", "Sorin", "not worked out (unpowered LNA)",
  ["&ldquo;I have -10 dBm measured, (vivaldi with much less cable, the close distance to the furuno, power limiter, amplifier but not powered on, and then 29 db attenuation to the signal hound). is it safe to power on the amplifier?&rdquo; (17:37)",
   "&ldquo;I'll just add in another 10. So it'll be Vivaldi to power limiter to 10 dB attenuation to the amplifier and then to the 29 dB attenuation.&rdquo; (17:58)",
   "&ldquo;I don't really see an effect from having the antenna plugged in versus not plugged in. So let's do a test where we just have the SM200B capped off and see what we read.&rdquo; (18:09)",
   "&ldquo;what is the loss in a shielded sma cabel per meter? I had about 2 meters of cable, which is probably really bad for 10 GHz&rdquo; (16:28)"],
  ["About 2 m of cable from 25 Oct replaced with a short one. The highest reading of all the tests."],
  ["Not powered: limiter output can be up to +17 dBm and the LNA&rsquo;s absolute maximum input is +15 dBm, so a 10 dB pad was added before the LNA. The SM200B saw &minus;10 dBm, 30 dB under its limit.",
   "Sorin then saw no difference with the antenna in or out: at 13 ft the leak was as big as the signal. That started the 26 Oct load tests."])
t("27", "26 Oct", "18:50", "11.5 m", "Vivaldi &rarr; limiter &rarr; 10 + 10 dB &rarr; LNA (on, 6 V) &rarr; 10 + 6 + 3 dB &rarr; SM200B", "whiteboard out, foam off",
  "&minus;7.94 dBm", "Spike", "&asymp; +9.9 dBm at the Vivaldi output (LNA output +11.1 dBm)",
  ["&ldquo;Vivaldi is in, radar transmitting&rdquo; (18:49)",
   "&ldquo;look at the screen yourself, I'm holding the radar. Give me a &lsquo;done&rsquo; message when you are done collecting data&rdquo; (18:50)"],
  ["Spike 3 MHz RBW, Min/Max, Max Hold 20 s, 9.4047 GHz, reference level raised to +10 dBm. At the default &minus;20 dBm reference it read &minus;11.4 dBm (clipped). Screenshot: <code>radar_test/spike_screens/test27_vivaldi_limiter_20dB_LNA_19dB_11p5m_ref+10_rbw3MHz.jpg</code>."],
  ["16 dB above the leak floor for this wiring (26c, &minus;24.06 dBm), so the leak can add at most about 0.1 dB.",
   "LNA output = &minus;7.94 + 19 = +11.1 dBm. With 22 dB of gain (datasheet) the LNA input is &minus;10.9 dBm; add back the 20 dB pad and about 0.8 dB of limiter loss: &asymp; +9.9 dBm at the Vivaldi. Test 7 got +8.7 dBm at the same spot: agreement within 1.2 dB.",
   "Turned the other way: taking the antenna level from test 7, the LNA input was +8.7 &minus; 0.8 &minus; 20 = &minus;12.1 dBm and the gain is 11.1 + 12.1 &asymp; <b>23 dB</b> (datasheet 22; &plusmn;2 dB because the input was not measured in the same setup).",
   "The LNA was linear: its input was about 7 dB below its own 1 dB compression input (&minus;5 dBm)."])
t("28", "26 Oct", "18:52", "11.5 m", "same as test 27 with the LNA off", "whiteboard out, foam off",
  "&minus;25.85 dBm", "Spike", "not worked out (unpowered LNA)",
  ["&ldquo;amplifier is off now, radar transmitting&rdquo; (18:51) &ldquo;radar is off, update the github page&rdquo; (18:52)"],
  ["Screenshot: <code>radar_test/spike_screens/test28_vivaldi_limiter_20dB_LNA_OFF_19dB_11p5m_ref+10_rbw3MHz.jpg</code>."],
  ["17.9 dB below test 27. This is at the leak floor (&minus;24 to &minus;31 dBm), so it is leak plus whatever passes through the unpowered LNA; the 17.9 dB on/off difference is only a lower bound."])

# ------------------------------------------------------------------ C. bare cable
t("9", "25 Oct", "&asymp; 14:50", "11.3 m (37 ft)", "bare SMA cable (no antenna, nothing on its end) &rarr; 29 dB &rarr; SM200B", "foam off",
  "&minus;17 dBm", "Sorin", LEAK,
  ["&ldquo;When I unplugged the power limiter so that I could add in the low noise amplifier ZX60-5123LN+, I noticed that the reading went up to -17 dBm (from just the SMA cable without the vivaldi or power limiter plugged in!). That SMA cable looks like a better antenna than my real antenna.&rdquo; (14:59)"],
  ["The long (&asymp; 2 m) cable that had fed the limiter, its far end open."],
  ["Higher than the Vivaldi itself (test 7, &minus;20.3). First sign that the radar was getting in somewhere other than the antenna; at 10 GHz an open cable end and an unshielded joint both receive well."])
t("10", "25 Oct", "&asymp; 14:55", "11.3 m (37 ft)", "bare cable &rarr; LNA (on, 6 V) &rarr; 29 dB &rarr; SM200B", "foam off",
  "nothing on screen", "Sorin", "n/a (SM200B had disconnected)",
  ["&ldquo;I then plugged in the LNA and powered it with 6 v, 0.08 amps. Given we were at -20 dBm, the +20 dB should take us to about 0 dBm, or 1 mW. This should still have 100 x safety. For some reason, I now no longer read anything on the signal hound spectrum analyzer! Help me debug this. I am scared.&rdquo; (14:59)"],
  ["LNA ZX60-5123LN+ at 6 V, 0.08 A."],
  ["The blank screen was a USB dropout: Spike had lost the SM200B. Nothing was damaged; the SM200B&rsquo;s noise floor was normal after reconnecting. The LNA&rsquo;s 0.08 A matches its datasheet 80 mA."])

GROUPS = [
    ("A", "50 &Omega; load, no antenna: what leaks in",
     "A load cannot receive, so these readings are radar power that gets into the SM200B, its cables and the pads directly. Every antenna reading has to be at least 20 dB above the load reading for the same wiring and distance.",
     [("Load directly on the SM200B input (13 ft)", ["17", "21", "22", "23"]),
      ("Load &rarr; 29 dB pads &rarr; SM200B", ["16", "20", "24", "25a", "25b"]),
      ("Load &rarr; limiter &rarr; 10 dB &rarr; LNA &rarr; 29 dB (11.5 m)", ["26a", "26b"]),
      ("Load &rarr; limiter &rarr; 20 dB &rarr; LNA &rarr; 19 dB (11.5 m)", ["26c"])]),
    ("B", "Vivaldi antenna",
     "Readings with the Vivaldi R120 on the front of the chain. The second number in each line is the SM200B reading worked back to the farthest point of the chain (pads added back, LNA gain taken off).",
     [("Vivaldi &rarr; 14 dB (and the useless manual attenuator), foam on the radar", ["1", "2", "3", "4"]),
      ("Vivaldi &rarr; 29 dB, foam off", ["7", "11", "15"]),
      ("Vivaldi &rarr; limiter &rarr; 29 dB", ["8", "12", "13"]),
      ("Vivaldi &rarr; limiter &rarr; LNA unpowered &rarr; 29 dB", ["18"]),
      ("Vivaldi &rarr; limiter &rarr; 20 dB &rarr; LNA &rarr; 19 dB", ["27", "28"])]),
    ("C", "Bare cable, no antenna", "An open SMA cable end on the front of the chain.",
     [("Open cable &rarr; 29 dB", ["9"]), ("Open cable &rarr; LNA &rarr; 29 dB", ["10"])]),
]


def _one(x):
    s = (f"Test {x['n']} &middot; {x['date']} {x['time']} &middot; {x['dist']} &middot; {x['chain']} &middot; {x['cond']} &mdash; "
         f"<b>SM200B: {x['sm']}</b> ({x['who']}) &rarr; {x['far']}")
    body = (h("Sorin's notes") + ul(x["sorin"]) + h("Setup") + ul(x["setup"]) +
            '<details class="item ai"><summary>AI analysis</summary><div class="body">' + ul(x["ai"]) + "</div></details>")
    return f'<details class="item test" id="rad-t{x["n"]}"><summary>{s}</summary><div class="body">{body}</div></details>'


def _overview():
    rows = []
    for g, title, _, subs in GROUPS:
        for sub, ns in subs:
            for n in ns:
                x = T[n]
                rows.append([x["n"], f"{x['date']} {x['time']}", x["dist"], x["chain"], x["cond"], f"<b>{x['sm']}</b>", x["who"], x["far"]])
    return table(["Test", "When", "Distance", "Chain", "Conditions", "Max at the SM200B", "Read by", "At the farthest point"], rows, cls="parts", left=tuple(range(8)))


def section():
    out = [p("Every over-the-air reading of the Furuno radar, 25 and 26 Oct 2026, grouped by what was on the front of the chain. "
             "Each line is one test: the peak the SM200B saw (3 MHz RBW, Min/Max, Max Hold unless noted) and that number worked back to the farthest point of the chain. "
             "Click a line for Sorin&rsquo;s own words and numbers, the setup, and a hidden AI analysis. Times are Pacific. "
             "&ldquo;Read by&rdquo;: Sorin = Sorin read it or said it; Spike = Claude read a Spike screenshot; I/Q = Claude&rsquo;s own Python capture."),
           '<div class="note">Main finding: the radar gets into the SM200B directly, at about &minus;21 to &minus;23 dBm at 13 ft and &minus;31 dBm at 11.5 m with 29 dB of pads (group A). '
           "Readings within 20 dB of that are mostly leak. The trustworthy antenna readings are test 7 (+8.7 dBm at the Vivaldi, 11 dB over the leak) and test 27 (+9.9 dBm at the Vivaldi through the limiter and LNA, 16 dB over the leak).</div>",
           '<details class="item" id="rad-power-all"><summary>All tests in one table</summary><div class="body">' + _overview() + "</div></details>"]
    for g, title, intro, subs in GROUPS:
        inner = [p(intro)]
        for sub, ns in subs:
            inner.append(f'<details class="item" open><summary>{sub}</summary><div class="body">' + "".join(_one(T[n]) for n in ns) + "</div></details>")
        out.append(item(f"rad-power-{g.lower()}", f"{g}. {title}", *inner, open_=True))
    return "".join(out)


POWER = item("rad-power", "Power readings by test: 50 &Omega; load vs antenna, every chain",
             fig("radar_sm200b_reading_load_direct_vs_load_29dB_vs_vivaldi_29dB.png", "Peak at the SM200B: load direct, load through 29 dB, Vivaldi through 29 dB, at 13 ft and 11.5 m"),
             p("Peak at the SM200B (3 MHz RBW, Min/Max, Max Hold). Blue: 50 &Omega; load on the SM200B. Orange: load &rarr; 29 dB pads. Green: Vivaldi &rarr; 29 dB pads. Made by <code>radar_test/plot_load_vs_antenna.py</code>."),
             section(), open_=True)
