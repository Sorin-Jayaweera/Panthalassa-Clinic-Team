# ADF5355 synthesizer box (AliExpress, bought 2021-05)

Black box, three SMA outputs: Out A+ and Out A− (54 MHz–6.8 GHz) and Out B (6.8–13.6 GHz, the VCO doubled). USB cable.
Hand-written sticker: "2021-05 microwave synthesizer 5+MHz – 13.6 GHz, 180 bucks AliExpress".

## What is known (26 Oct 2026)

- On USB the box is a Prolific PL2303 USB-serial adapter ("USB-Serial Controller D", driver 3.9.6.0), COM13 on Sorin's laptop.
- It sends nothing on its own, and gives no boot text when DTR/RTS are toggled (4800–115200 baud).
- No reply to `\r\n`, `?`, `*IDN?`, `help`, `AT` at 9600–115200 baud.
- No reply to a full register set (R12…R0, both outputs OFF) sent as raw 4-byte words (MSB or LSB first) or as hex text lines, at 9600, 57600 and 115200 baud. If one of those formats was accepted, the box now has both outputs off.
- The seller's control program and command format are unknown. Nothing in github.com/gallicchio mentions it.

## Output levels (ADF5355 datasheet Rev. D, page 5)

RFoutB +1 dBm typical at 6.8 GHz, −1 dBm at 13.6 GHz, ±4 dB over the band. RFoutA up to +8 dBm at 1 GHz.
So into the SM200B (+20 dBm max) through 19 dB of pads the worst case is about −11 dBm.

## Register calculator

`adf5355_regs.py` ports Analog Devices' no-OS driver (drivers/frequency/adf5355/adf5355.c).

    python adf5355_regs.py 8300e6 --ref 100e6 --out B

8.3 GHz on Out B with a 100 MHz reference: R = 2, PFD 50 MHz, VCO 4150 MHz, INT 83, no fraction (integer mode, fewest spurs).
R12…R0 = 0001041C 0061300B 00C01F7A 15153CC9 102D0428 12000067 15018836 00800025 30014984 00000003 00000012 00000001 00300530.
The reference frequency of this box is not known; with 25 MHz, INT = 166.

## Next

1. Watch the lock LED (if the box has one) while sending register sets: a change shows a format was accepted.
2. Or open the box and drive the ADF5355's SPI pins (CLK, DATA, LE, CE) from a Pico/Arduino with these register words.
3. Or find the seller's PC program; capture its bytes on COM13.

## First look on the SM200B (26 Oct 2026, 19:51)

Out B → SMA cable → 10 + 6 + 3 dB pads (19 dB) → SM200B. Spike full span 100 kHz–20.1 GHz, RBW 300 kHz, ref −20 dBm.
The box was already putting out a signal at power-up; none of the register formats sent earlier had switched it off.

| Line | Frequency | At the SM200B | Relative to 8 GHz | Likely source |
|---|---|---|---|---|
| 1 | 8.000002 GHz | −26.98 dBm | 0 dB | wanted output (VCO 4 GHz doubled) |
| 2 | 4.000002 GHz | −33.55 dBm | −6.6 dB | VCO fundamental leaking through the doubler |
| 3 | 2.000002 GHz | −40.65 dBm | −13.7 dB | VCO ÷ 2 (the Out A path) |
| 4 | 11.999905 GHz | −53.53 dBm | −26.5 dB | 3 × VCO |
| 5 | 5.999954 GHz | −62.72 dBm | −35.7 dB | 3 × (VCO ÷ 2) |

Out B level ≈ −26.98 + 19 = **−8 dBm** (cable and pad loss at 8 GHz not taken out; the "8G" pads are rated only to 8 GHz).
Datasheet typical is about +1 dBm, so either the cable and pads lose several dB at 8 GHz or the box is set to a lower power.
For the mixer's +10 dBm LO, −8 dBm + 12 dB (ZX60-14012L-S+) ≈ +4 dBm is not enough; the VCO line at 4 GHz (−6.6 dBc) also needs filtering before the mixer.
After Spike reconnected, COM13 (the box's USB-serial) was no longer listed in Windows.
Screen: `spike_screens/adf5355_outB_powerup_default_full_span_19dB_pads.jpg`.

## Second try at the USB commands (26 Oct 2026, 19:35–19:40 PC clock), watched live in Spike

Box re-enumerated as COM14. Spike at 8.15 GHz centre, 1 GHz span; box sitting at 8.000 GHz, −27.3 dBm.
`probe_formats.py` sent "go to 8.3 GHz on Out B" in 13 formats at 4800, 9600, 19200, 38400, 57600 and 115200 baud:
raw 4-byte register words (100 and 25 MHz reference), hex text lines, `0x` hex lines, `8300`, `8300.000`, `8300000000`,
`F8300`, `f8300`, `FREQ 8300MHz`, `:FREQ 8.3GHz`, `SET 8300`. No reply to any, and the line never left 8.000 GHz.
Conclusion: the box needs the seller's own (probably framed binary) protocol, or direct SPI access inside the box.
