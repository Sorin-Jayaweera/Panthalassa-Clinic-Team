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
