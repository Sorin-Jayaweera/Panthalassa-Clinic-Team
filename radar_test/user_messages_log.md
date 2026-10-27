# Sorin's messages during the radar tests

Every message Sorin sends during bench work, in order, so each test can be worked out from the instructions.
Entries before 26 Oct 18:35 are rebuilt from the session summary and are close paraphrases, not exact quotes; entries after that are verbatim.

## 25 Oct (paraphrased)

- Radar setup questions: draw the setup; is it safe; tee removal; foam; power supply 12 V at 4.64 A; range settings; 37 ft; added 2 dB; Spike usage; RBW; "How much time is between each of the pulses?"; "How do I place a trace in a delta trace?"
- "spike is closed, measure this all yourself"; "also check temperature"; "take all the data and measurements you can, and write them to the github page"
- Asked for spectrograms, FFT slices, marker labels, what each pulse looks like, what to expect for the limiter, LNA and mix-down.
- Asked for the power table: dBm and mW, whiteboard in/out, minus 14 dB, EIRP, centre frequency, span, pulses per second, revolutions per second, pulses per cycle, peak and average, as CSV.
- "plot my furino CSVs and put them on the radar tab."
- "I put a 10, 10, and 3 dB 8G attenuator." Foam off, 3 + 10 + 10 to the Vivaldi. Later: "I made it 3 dB, then 6 dB, and then 2 10 dBs." "I turned on persistance".
- Limiter connected (3, 6, 10, 10 dB, then limiter, long cable to the Vivaldi). "I'm turning on the radar. Give me the go/nogo." "transmitting". "the sm200b disconnected, I just reconnected".
- About −20 dBm; about −17 dBm from just the SMA cable; plugged in the LNA at 6 V, 0.08 A, no longer read anything. "Help me debug this. I am scared."
- "right now I only have the vivaldi to the 10+10+3+6 db attenuators. Turning on the radar"; "radar is on"; "try again, radar is on and transmitting".
- "radar on standby, i put in just the power limiter. Is the EVAL HLM 20 P directional?"; "radar is back on with the power limiter in"; "it should be around 30 dBm".
- "the radar is 13 feet from the antenna, and about 26 from me." "I moved it closer to test the power limiter like you said. Can I turn on the radar?" "on".
- Spike at −15.27 dBm. "can I turn off the radar? Do we have enough close range data?" "so I should remove the limiter and just have the vivaldi into the attenuators, right?" "it is connected. Transmitting now."
- "I unplugged the vivaldi and long cable... put a 50 ohm termination." "terminator is on the signal hound input now, no pads..."

## 26 Oct (paraphrased up to 18:35)

- "I have -10 dBm measured (vivaldi with much less cable, close distance, power limiter, amplifier but not powered on, 29 db)... is it safe to power on the amplifier?" "I'll just add in another 10..."
- "I don't really see an effect from having the antenna plugged in versus not... test where we just have the SM200B capped off." "I'll put a 50 ohm termination?"
- "spike is open, radar is on. Look at the screen. This is with the 29 dB attenuators and then the 50 ohm load."
- "Is the 50 ohm load going directly into the +20 dBm max port? Is it okay for me to turn on the radar?" "I just turned it off."
- "I just wrapped most of the outside of the signal hound in the AN72 foam board..." "Radar is now on. It is at around -30."
- "I put the whiteboard in between... -19.43 dBm... Is the whiteboard acting like a transmitting antenna?" "I forgot that we don't have the attenuators on right now." "when I put in the attenuators, I go from -19 dBm to -25 dBm..."
- "My main goal with this was to understand the quality of the power limiter and the amplifier, and also just what the spectrum of the radar actually looked like."
- "I'm going to move the radar back to the original position. That's about 11.3 meters. And then leaving the 50 ohm and then the 29 dB attenuators, I'll measure, and then I'll add on the antenna."

## 26 Oct (verbatim from here)

- ~18:38 "The radar is now 11 meters away. The whiteboard is still in the way. It's just the 50 ohm and then attenuators. I'm turning it on."
- ~18:39 "Also keep a list of every message that I send so that you can figure out any test that I do from my instructions to you."
- ~18:40 "Right now it's transmitting the direct path from radar at 11.5 meters away to the SM200B with just the 50 ohm load and attenuators."
- ~18:43 "I measure a background of negative 34 to negative 32 dBm. I'm now moving the whiteboard out of the way to measure."
- ~18:46 "with the whiteboard out of hte way I got the -31.2 dBm"
- ~18:48 "And now adding on to the end, instead of the 50 ohm load, I'm going to have the amplifier and the power limiter. So it's power limiter, then amplifier, then attenuators. And I think I'm going to put the 50 ohm load at the end of the power amplifier, just so that we see what we read here for random coupling stuff."
- ~18:52 "Okay, it's now 50 ohm load, then power limiter, then the amplifier, which is currently turned off, and then the attenuators to the signal mount. I'm going to turn on the radar with the amplifier off. We'll take data, and then we'll turn the amplifier on, and then we can go to having the antenna."
- ~18:53 "Yes, you can. Bye. Bye."
- ~18:56 "We got the same negative 31 dBm. I'm going to turn on the amplifier. Amplifier is on."
- ~18:58 "With the amplifier on, we get -28 dBm."
- ~19:00 "I forgot to say, for this setup, it is the power limiter, then 10 dB of HE attenuation, then the amplifier, and then the rest of the attenuators. This is how it has been every time in the past couple of messages that I've tested with the amplifier."
- ~19:01 "You don't need to give such long responses. Just say okay or next test or suggest something or say something is wrong."
- ~19:02 "The setup as it is right now is power limiter, then 10 dB, then amplifier, and then 10 dB, then 10 dB, then 6 dB, then 3 dB attenuators. This is how it has been"
- ~19:04 "Instead of this now, the 50 ohm load, then the power limiter, then 2 10 dB attenuators, then the amplifier, and then 10 dB, 6 dB, 3 dB, then signal hound."
- ~19:06 "I'm turning on the amplifier and turning on the radar. I read -24.06 dBm at the peak."
- ~19:08 "Vivaldi is in, radar transmitting"
- ~19:10 "look at the screen yourself, I'm holding the radar. Give me a \"done\" message when you are done collecting data"
- ~19:12 "amplifier is off now, radar transmitting"
- ~19:14 "radar is off, update the github page"
- ~19:20 (with racon_draft_design01b_drawing.pdf) "look at the JCon specs. What is the next thing that I should test? We've seen that we can receive, we know the frequency spectrum, we know the pulses, we know characterizations of the radar itself, we know the amplification from this amplifier and the power limiter. I'm assuming that you have good data from. I want you to explain that to me. We've used the signal spectrum analyzer. I'm curious about using the spectrum analyzer as a SDR, but I think maybe we can go to PLL and shifting down frequency and then doing frequency identification at the same time."
- ~19:25 "the LNA has 6V in on the datasheet"
- ~19:30 "I have plugged you into the ADF5355 through the USB port and I've applied power. I want you to teach me how I would normally program and use the ADF5355."
- ~19:08 PC clock "I have connected out B, which is 6.8 to 13.6 gigahertz through an SMA cable to the attenuators. I right now have a 10 dB attenuator, a 6 dB attenuator, and a 3 dB attenuator. Is this safe? Show me documentation."
- ~19:20 PC clock: asked to reorganise the Radar section: power levels by condition, grouped 50 ohm load vs antenna, then by signal chain; each test a one-sentence summary that expands; top line = max power at the spectrum analyzer and the power at the farthest point of the chain; every number Sorin said must appear; other analysis hidden as "AI analysis"; amplifier results under ZX60-5123LN+, limiter results under its part; documented for a year from now.
- ~19:30 PC clock "I have plugged in the ADF five-three-five-five only and not the spectrum analyzer. It is not plugged in. It's just what you have, so make sure you don't transmit because it would destroy the thing. But you can program it."
- ~19:33 PC clock "keep writing the documentation at the same time that you're working on this ADF 5355."
- ~19:34 PC clock "I just plugged in the spectrum analyzer in addition to the ADF."
- ~19:36 PC clock "it's connected to the SignalHound SM200B."
- ~19:40 PC clock "It is a black box with three output ports, out A plus, out A minus, out B, from AliExpress."
- ~19:44 PC clock "try this: https://github.com/analogdevicesinc/no-OS/blob/main/drivers/frequency/adf5355/adf5355.c. I also just plugged the ADF 5355 into the 10+6+3 db attenuators in the SM200B."
- ~19:50 PC clock "the sticker is hand written from someone in my lab, it says 2021-05 microwave synthesizer 5+MHZ - 13.66 Hz, 180 bucks ali express with the Out A+ and out A- at 54 M-6.8 GHz, and out B at 13.smth GHz"
- ~19:55 PC clock "check https://github.com/gallicchio/"
- ~19:58 PC clock "the SM200B is plugged in"
- ~20:05 PC clock "the spectrum analyzer was getting hot, I just unplugged it. Do what you can with the ADF5355."
