"""
build_jacon.py  -  generates the LTspice model of the JACON racon draft design
(racon_draft_design01b_drawing.pdf).

Outputs (all in this folder):
    JACON_system.asc      top-level schematic: every function is its own block,
                          grouped in labelled boxes [0]..[9], one TEST switch
    jacon_blocks.inc      behavioral sub-circuit for every block + derived params
    jacon_*.asy           block symbols (must sit next to the .asc)
    filters_ac.cir        small-signal AC check of the filters / amps

    %USERPROFILE%\\radioconda\\python.exe build_jacon.py

NOTE: re-running this OVERWRITES JACON_system.asc. If you tweak parameters
inside LTspice, copy them into PARAMS below (or just stop regenerating).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


# =============================================================================
#  PARAMETERS  (name, value, comment)  - grouped exactly like the schematic
# =============================================================================
TESTS = [
    # n, name, TSTOP, TMAX, description
    (0, "FULL SYSTEM", "2.1u", "2.5p", "radar pulse in -> detect -> measure f -> hold -> VCO -> Morse '. - .' out at the radar frequency"),
    (1, "RX FRONT END", "40n", "2.5p", "CW 9.4 GHz power ramp P1_START..P1_STOP through limiter + LNA (compression / protection)"),
    (2, "LO CHAIN", "5n", "1p", "8.3 GHz PLL -> buffer -> splitter: LO drive levels at both mixers"),
    (3, "RX DOWNCONVERSION", "20n", "2.5p", "CW radar -> LNA -> mixer -> IF amp: 1.1 GHz IF, 17.7 GHz sum, LO leak"),
    (4, "PULSE DETECTION", "650n", "20p", "IF pulses of rising power -> envelope detector -> comparator vs DAC threshold"),
    (5, "LIMITING AMP", "60n", "10p", "IF CW ramp P5_START..P5_STOP -> 3-stage limiter: output amplitude flattens"),
    (6, "DELAY-LINE DISCRIMINATOR", "176n", "10p", "IF staircase 1.00..1.20 GHz (first step held twice to settle) -> limiter -> splitter -> delay lines -> phase detector (calibration)"),
    (7, "SAMPLE/HOLD + OP-AMP", "4u", "0.5n", "ideal phase-detector levels + detect pulses -> S&H -> scaling op-amp (settling)"),
    (8, "VCO", "50n", "10p", "tune-voltage ramp VT8_START..VT8_STOP -> VCO frequency"),
    (9, "TX CHAIN", "460n", "2.5p", "VCO @ VT_CENTER keyed '. - .' -> up-mixer -> image-reject HPF -> PA"),
    (10, "RX->TX FREQUENCY TRANSFER", "300n", "2.5p", "pulse in, measure settled VCO f (use .step param F_RADAR ...; op-amp made fast)"),
]

PARAM_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("[0] RADAR ECHO STIMULUS", [
        ("F_RADAR", "9.4e9", "radar frequency (9.3-9.5 GHz)"),
        ("P_RADAR", "-30", "echo power at RX antenna port, dBm (-50 distant .. -10 close)"),
        ("T_PULSE_ON", "20n", "pulse start"),
        ("PW_RADAR", "150n", "pulse width (real radars 50 ns - 1.2 us)"),
        ("T_RISE", "1n", "pulse edge time constant"),
        ("P1_START", "-60", "TEST 1 ramp start (dBm)"),
        ("P1_STOP", "20", "TEST 1 ramp stop (dBm)"),
    ]),
    ("[1] RX RF FRONT END", [
        ("LIM_PMAX", "17", "power limiter flat leakage, dBm (Aaronia SMA limiter: 17 dBm @ 10 GHz)"),
        ("LIM_IL", "0.5", "limiter insertion loss, dB (assumed)"),
        ("ATT_RX", "0", "optional in-line attenuator to keep LNA < +15 dBm, dB"),
        ("LNA_G", "22", "ZX60-5123LN+ gain, dB"),
        ("LNA_P1DB", "17", "ZX60-5123LN+ output P1dB, dBm"),
    ]),
    ("[2] LO GENERATION", [
        ("F_LO", "8.3e9", "ADF5355 frequency"),
        ("P_PLL", "3", "ADF5355 output power at 8.3 GHz, dBm (VERIFY on your module)"),
        ("LOBUF_G", "12", "ZX60-14012L-S+ gain, dB"),
        ("LOBUF_P1DB", "14", "ZX60-14012L-S+ output P1dB, dBm (assumed - check datasheet)"),
        ("LOSPLIT_IL", "0.7", "ZX10-2-1252-S+ excess loss, dB (on top of 3 dB split)"),
    ]),
    ("[1][8] MIXERS (ZX05-14LH-S+)", [
        ("MIX_CL", "6.7", "conversion loss, dB"),
        ("MIX_LO_NOM", "10", "LO level the loss is quoted at, dBm (LH = +10)"),
        ("MIX_IFBW", "4e9", "IF port bandwidth (DC-4 GHz)"),
        ("MIX_LOIF_ISO", "25", "LO->IF isolation, dB (assumed)"),
        ("MIX_LORF_ISO", "30", "LO->RF isolation, dB (assumed)"),
    ]),
    ("[3] IF CHAIN", [
        ("IFA_G", "22.5", "ZX60-P162LN+ gain, dB"),
        ("IFA_P1DB", "18", "ZX60-P162LN+ output P1dB, dBm (assumed - check)"),
        ("IFA_FHP", "300e6", "IF amp low corner (1-pole model)"),
        ("IFA_FLP", "2.5e9", "IF amp high roll-off (3rd-order model)"),
        ("F_IF_NOM", "1.1e9", "nominal IF used to normalise gains"),
    ]),
    ("[4] PULSE DETECTION", [
        ("ENV_BW", "130e6", "ADL5511 envelope bandwidth"),
        ("ENV_K", "1", "envelope out per volt of IF peak (idealised - check ADL5511 slope)"),
        ("ENV_OFS", "0", "envelope output offset, V (ADL5511 real part has ~VREF offset)"),
        ("VTH_DAC", "15m", "nanoDAC comparator threshold, V"),
        ("COMP_VOD", "0.5m", "ADCMP600 overdrive for full swing, V"),
        ("COMP_TPD", "3.5n", "ADCMP600 propagation delay"),
    ]),
    ("[5] LIMITING AMP", [
        ("LIMA_G", "17", "gain per stage, dB (GALI-52+ / ERA-33SM+ class)"),
        ("LIMA_P1DB", "12", "output P1dB per stage, dBm"),
        ("LIMA_FLP", "1.6e9", "harmonic clean-up low-pass after the limiter"),
    ]),
    ("[6] DELAY-LINE DISCRIMINATOR", [
        ("VF", "0.70", "coax velocity factor (PTFE ~0.70, foam ~0.8x, air 1.0)"),
        ("L_REF_IN", "6", "reference arm length, inches"),
        ("DL_IN", "4.5", "EXTRA length of delayed arm, inches  <-- design variable"),
        ("COAX_DB_FT", "0.4", "coax loss at ~1.1 GHz, dB/ft (RG-316 ~0.4)"),
        ("MIXMODE", "1", "phase detector: 0 = ideal multiplier, 1 = double-balanced mixer"),
        ("PD_CL", "6", "ZX05-30W-S+ conversion loss, dB"),
        ("PD_LO_NOM", "7", "ZX05-30W-S+ LO level, dBm (Level 7)"),
        ("PD_FLP", "100e6", "phase-detector output low-pass (removes 2f)"),
    ]),
    ("[7] SAMPLE/HOLD + SCALING", [
        ("SH_DLY", "40n", "FPGA: sample starts this long after detect"),
        ("SH_WIDTH", "40n", "FPGA: sample window length"),
        ("SH_RON", "120", "ADG1211 on-resistance, ohm (check datasheet)"),
        ("SH_ROFF", "1G", "ADG1211 off-resistance"),
        ("SH_C", "100p", "C0G hold capacitor"),
        ("PD_V0", "-0.3372", "phase-detector volts at F_IF_NOM  (from TEST 6 calibration; redo if you change [5]/[6])"),
        ("OPA_GAIN", "19.46", "op-amp gain, V/V  (from TEST 6 calibration; redo if you change [5]/[6]/VCO)"),
        ("VT_CENTER", "7.75", "VCO tune voltage for F_IF_NOM"),
        ("OPA_VMIN", "0", "op-amp output low rail, V"),
        ("OPA_VMAX", "11.5", "op-amp output high rail, V"),
        ("OPA_GBW", "8e6", "ADA4622 gain-bandwidth, Hz (check) - sets tune settling"),
    ]),
    ("[9] VCO + MORSE KEYING", [
        ("VCO_V1", "6", "CVCO55BE tune point 1, V"),
        ("VCO_F1", "1.0e9", "... frequency at VCO_V1"),
        ("VCO_V2", "9.5", "CVCO55BE tune point 2, V"),
        ("VCO_F2", "1.2e9", "... frequency at VCO_V2"),
        ("VCO_FMIN", "0.8e9", "VCO lower limit"),
        ("VCO_FMAX", "1.6e9", "VCO upper limit"),
        ("P_VCO", "3", "VCO output power, dBm (check datasheet)"),
        ("MORSE_UNIT", "60n", "Morse dot length (SHORTENED for simulation; real racon ~us)"),
        ("MORSE_HOLDOFF", "1.6u", "FPGA delay from detection to first dot"),
        ("KEY_TR", "2n", "ADG901 switching time constant"),
        ("KEY_ISO", "40", "ADG901 off isolation at 1 GHz, dB (check)"),
        ("KEY_IL", "1", "ADG901 insertion loss, dB"),
    ]),
    ("[8] TX RF CHAIN", [
        ("IRF_FC", "8.2e9", "image-reject HPF ripple corner (9th-order 0.5 dB Chebyshev ~ VHF-8400+)"),
        ("IRF_IL", "1.0", "image-reject filter extra loss, dB"),
        ("PA_G", "30", "power amp gain, dB (ZVE-143-S+ class - check)"),
        ("PA_P1DB", "30", "power amp output P1dB, dBm (~1 W)"),
    ]),
    ("TEST-BENCH STIMULI", [
        ("F_IF_TEST", "1.1e9", "IF test tone (tests 4, 5)"),
        ("P4_START", "-35", "TEST 4: first pulse power at IF splitter input, dBm"),
        ("P4_STEP", "10", "TEST 4: power step per pulse, dB"),
        ("T4_PER", "150n", "TEST 4: pulse period"),
        ("T4_PW", "60n", "TEST 4: pulse width"),
        ("P5_START", "-50", "TEST 5: ramp start at limiter input, dBm"),
        ("P5_STOP", "5", "TEST 5: ramp stop, dBm"),
        ("P6", "-20", "TEST 6: tone power at limiter input, dBm"),
        ("F6_START", "1.0e9", "TEST 6: staircase start"),
        ("F6_STEP", "10e6", "TEST 6: staircase step"),
        ("T6_STEP", "8n", "TEST 6: time per step"),
        ("T7_PER", "1u", "TEST 7: sample period"),
        ("T7_PW", "100n", "TEST 7: detect pulse width"),
        ("T7_DV", "0.05", "TEST 7: phase-detector level step, V"),
        ("VT8_START", "5", "TEST 8: tune ramp start, V"),
        ("VT8_STOP", "10.5", "TEST 8: tune ramp stop, V"),
    ]),
]


# =============================================================================
#  math helpers used to pre-compute constants for the netlist
# =============================================================================
def c1_tanh(a: float) -> float:
    """1st Fourier coefficient of tanh(a*cos(th)) -> mixer switching gain."""
    th = np.linspace(0, 2 * np.pi, 200001)[:-1]
    return float(2 * np.mean(np.tanh(a * np.cos(th)) * np.cos(th)))


def cheby_g(n: int, ripple_db: float) -> list[float]:
    beta = math.log(1 / math.tanh(ripple_db / 17.37))
    gam = math.sinh(beta / (2 * n))
    a = [math.sin((2 * k - 1) * math.pi / (2 * n)) for k in range(1, n + 1)]
    b = [gam ** 2 + math.sin(k * math.pi / n) ** 2 for k in range(1, n + 1)]
    g = [2 * a[0] / gam]
    for k in range(2, n + 1):
        g.append(4 * a[k - 2] * a[k - 1] / (b[k - 2] * g[-1]))
    return g


C1_TANH4 = c1_tanh(4.0)
G_IRF = cheby_g(9, 0.5)


# =============================================================================
#  SUB-CIRCUIT LIBRARY
#  Convention: node voltage = incident wave amplitude in a 50 ohm system
#  (P_dBm = 10log10(V^2/(2*50)/1mW)). Every RF block input is terminated in
#  50 ohm; every RF output is a 50 ohm Thevenin source (2*V behind 50 ohm).
# =============================================================================
def build_library() -> str:
    tests_on = lambda ns: "{" + "|".join(f"(TEST=={n})" for n in ns) + "}"  # noqa: E731
    irf = []
    nodes = ["in", "n2", "n4", "n6", "n8"]
    # HPF from LPF prototype: shunt C(g odd) -> shunt L ; series L(g even) -> series C
    for i, g in enumerate(G_IRF, start=1):
        if i % 2 == 1:
            nd = nodes[(i - 1) // 2]
            irf.append(f"L{i} {nd} 0 {{50/(2*pi*IRF_FC*{g:.6f})}} Rser=0")
        else:
            a, b = nodes[(i - 2) // 2], nodes[i // 2]
            irf.append(f"C{i} {a} {b} {{1/(2*pi*IRF_FC*{g:.6f}*50)}}")
    irf_txt = "\n".join(irf)

    morse = lambda tau: (  # noqa: E731
        f"(u({tau})-u({tau}-U) + u({tau}-2*U)-u({tau}-5*U) + u({tau}-6*U)-u({tau}-7*U))"
    )
    tau = "(time*1e9-TAU0)"

    return f"""* =============================================================================
*  jacon_blocks.inc  -  JACON behavioral block library   (generated by build_jacon.py)
*  Signal convention: node voltage = RF amplitude in a 50 ohm system
*        P(dBm) = 10*log10( Vpk^2 / 100m )        dbm2v(p) = Vpk
*  Every RF input is 50 ohm terminated; every RF output is a 50 ohm Thevenin.
* =============================================================================

* ---------- helper functions ----------
.func dbm2v(p) {{sqrt(0.1*10**(p/10))}}
* Rapp AM/AM model, smoothness p=3: linear for |x|<<1, output clamps at 1.
.func rapp(x) {{x/(1+abs(x)**6)**(0.16666667)}}
.func padr1(db) {{50*(10**(max(db,1m)/20)-1)/(10**(max(db,1m)/20)+1)}}
.func padr2(db) {{100*10**(max(db,1m)/20)/(10**(max(db,1m)/10)-1)}}

* ---------- which sources are active in which TEST ----------
.param RADAR_ON={tests_on([0, 1, 3, 10])[1:-1]}
.param PULSED={tests_on([0, 10])[1:-1]}
.param LO_ON={tests_on([0, 2, 3, 9, 10])[1:-1]}
.param VCO_ON={tests_on([0, 8, 9, 10])[1:-1]}

* ---------- derived parameters ----------
.param C0=299792458
.param TD_REF={{L_REF_IN*0.0254/(VF*C0)}}
.param TD_DLY={{(L_REF_IN+DL_IN)*0.0254/(VF*C0)}}
.param DT_DELAY={{DL_IN*0.0254/(VF*C0)}}
.param LOSS_REF={{COAX_DB_FT*L_REF_IN/12}}
.param LOSS_DLY={{COAX_DB_FT*(L_REF_IN+DL_IN)/12}}
.param VSAT_LIM={{dbm2v(LIM_PMAX)}}
.param VSAT_LIMA={{dbm2v(LIMA_P1DB)/0.891}}
.param VSAT_IFA={{dbm2v(IFA_P1DB)/0.891}}
* mixer: tanh LO switch; C1_TANH4 = 1st Fourier coeff of tanh(4cos) = {C1_TANH4:.6f}
.param C1_TANH4={C1_TANH4:.6f}
.param VSW_MIX={{dbm2v(MIX_LO_NOM)/4}}
.param KMIX={{2*10**(-MIX_CL/20)/C1_TANH4}}
.param VSW_PD={{dbm2v(PD_LO_NOM)/4}}
.param KPD={{2*10**(-PD_CL/20)/C1_TANH4}}
.param IFA_NORM={{1/sqrt(1+(IFA_FHP/F_IF_NOM)**2)/sqrt(1+(F_IF_NOM/IFA_FLP)**6)}}
.param U={{MORSE_UNIT*1e9}}

* =============================================================================
*  generic building blocks
* =============================================================================
* 3rd-order Butterworth low-pass, 50 ohm doubly terminated (caller terminates)
.subckt LPF3 in out params: FC=1e9
C1 in 0 {{1/(2*pi*FC*50)}}
L2 in out {{2*50/(2*pi*FC)}} Rser=0
C3 out 0 {{1/(2*pi*FC*50)}}
.ends LPF3

* amplifier with gain G (dB) and output P1dB P1 (dBm), Rapp compression
.subckt AMP in out params: G=10 P1=10
.param VS={{dbm2v(P1)/0.891}}
R_in in 0 50
B1 o 0 V=2*VS*rapp(10**(G/20)*V(in)/VS)
R_o o out 50
.ends AMP

* =============================================================================
*  [0] TEST BENCH
* =============================================================================
* echo arriving at the RX antenna port
.subckt RADAR_SRC out
B1 o 0 V=2*RADAR_ON*dbm2v(if(TEST==1, P1_START+(P1_STOP-P1_START)*time/TSTOP, P_RADAR))
+ *if(PULSED, 0.5*(tanh((time-T_PULSE_ON)/T_RISE)-tanh((time-T_PULSE_ON-PW_RADAR)/T_RISE)), 1)
+ *sin(2*pi*F_RADAR*time)
R1 o out 50
.ends RADAR_SRC

* stimuli injected by the TSEL switches for the per-block tests
.subckt TESTBENCH stim_if stim_pd stim_det stim_vtune
* IF tone phase in cycles (TEST 6 = frequency staircase)
B_PH ph 0 V=idt(if(TEST==6, F6_START+F6_STEP*max(0,floor(time/T6_STEP)-1), F_IF_TEST))
B_A amp 0 V=if(TEST==4, dbm2v(P4_START+P4_STEP*floor(time/T4_PER))
+ *0.5*(tanh((time-T4_PER*floor(time/T4_PER)-20n)/0.5n)-tanh((time-T4_PER*floor(time/T4_PER)-20n-T4_PW)/0.5n)),
+ if(TEST==5, dbm2v(P5_START+(P5_STOP-P5_START)*time/TSTOP),
+ if(TEST==6, dbm2v(P6), 0)))
B_IF stim_if 0 V=V(amp)*sin(2*pi*V(ph))
* TEST 7: phase-detector levels step by T7_DV around PD_V0 every T7_PER
B_PD stim_pd 0 V=PD_V0+T7_DV*(floor(time/T7_PER)-1.5)
B_DET stim_det 0 V=0.5*(tanh((time-T7_PER*floor(time/T7_PER)-100n)/0.3n)
+ -tanh((time-T7_PER*floor(time/T7_PER)-100n-T7_PW)/0.3n))
B_VT stim_vtune 0 V=if(TEST==8, VT8_START+(VT8_STOP-VT8_START)*time/TSTOP, VT_CENTER)
.ends TESTBENCH

* test multiplexer, 50 ohm RF version: output = stim when TEST==N1 or N2
.subckt TSEL_RF norm stim out params: N1=-99 N2=-99
R_n norm 0 50
B1 a 0 V=2*if((TEST==N1)|(TEST==N2), V(stim), V(norm))
R1 a out 50
.ends TSEL_RF

* test multiplexer, voltage (baseband / logic) version
.subckt TSEL_V norm stim out params: N1=-99 N2=-99
B1 out 0 V=if((TEST==N1)|(TEST==N2), V(stim), V(norm))
.ends TSEL_V

* =============================================================================
*  [1] RX RF FRONT END
* =============================================================================
.subckt LIMITER in out
R_in in 0 50
B1 o 0 V=2*10**(-(LIM_IL+ATT_RX)/20)*VSAT_LIM*rapp(V(in)/VSAT_LIM)
R_o o out 50
.ends LIMITER

.subckt LNA in out
X1 in out AMP G={{LNA_G}} P1={{LNA_P1DB}}
.ends LNA

* down-converting double-balanced mixer (RF, LO -> IF), IF port DC..MIX_IFBW
.subckt MIX_DOWN rf lo if
R_rf rf 0 50
R_lo lo 0 50
B1 a 0 V=2*(KMIX*V(rf)*tanh(V(lo)/VSW_MIX) + 10**(-MIX_LOIF_ISO/20)*V(lo))
R1 a f 50
XF f g LPF3 FC={{MIX_IFBW}}
R_L g 0 50
B2 b 0 V=2*V(g)
R2 b if 50
.ends MIX_DOWN

* =============================================================================
*  [2] LO GENERATION
* =============================================================================
.subckt PLL_LO out
B1 o 0 V=2*LO_ON*dbm2v(P_PLL)*sin(2*pi*F_LO*time)
R1 o out 50
.ends PLL_LO

.subckt LO_BUF in out
X1 in out AMP G={{LOBUF_G}} P1={{LOBUF_P1DB}}
.ends LO_BUF

.subckt SPLIT_LO in o1 o2
R_in in 0 50
B1 a 0 V=2*10**(-(3.0103+LOSPLIT_IL)/20)*V(in)
R1 a o1 50
B2 b 0 V=2*10**(-(3.0103+LOSPLIT_IL)/20)*V(in)
R2 b o2 50
.ends SPLIT_LO

* =============================================================================
*  [3] IF CHAIN
* =============================================================================
.subckt IF_AMP in out
R_in in 0 50
B1 a 0 V=VSAT_IFA*rapp(10**(IFA_G/20)*V(in)/VSAT_IFA)
C1 a b {{1/(2*pi*IFA_FHP*1k)}}
R1 b 0 1k
B2 c 0 V=2*V(b)
R2 c d 50
XF d e LPF3 FC={{IFA_FLP}}
R_L e 0 50
B3 o 0 V=2*V(e)/IFA_NORM
R3 o out 50
.ends IF_AMP

* ZFRSC-42-S+ resistive 2-way splitter (real resistor star, 6 dB)
.subckt SPLIT_RES in o1 o2
R1 in c 16.6667
R2 c o1 16.6667
R3 c o2 16.6667
.ends SPLIT_RES

* =============================================================================
*  [4] PULSE DETECTION
* =============================================================================
.subckt ENV_DET in out
R_in in 0 50
B1 a 0 V=abs(V(in))*pi/2
R1 a b 1k
C1 b 0 {{1/(2*pi*1.554*ENV_BW*1k)}}
B2 c 0 V=V(b)
R2 c d 1k
C2 d 0 {{1/(2*pi*1.554*ENV_BW*1k)}}
B3 out 0 V=ENV_K*V(d)+ENV_OFS
.ends ENV_DET

.subckt DAC out
V1 out 0 {{VTH_DAC}}
.ends DAC

* logic output 0..1 V
.subckt COMPARATOR inp inn out
B1 a 0 V=0.5+0.5*tanh((V(inp)-V(inn))/COMP_VOD)
R1 a b 1k
C1 b 0 {{COMP_TPD/0.693/1k}}
B2 out 0 V=V(b)
.ends COMPARATOR

* =============================================================================
*  [5] LIMITING AMPLIFIER  (3 cascaded gain blocks + harmonic LPF)
* =============================================================================
.subckt LIM_AMP in out
R_in in 0 50
B1 a 0 V=VSAT_LIMA*rapp(10**(LIMA_G/20)*V(in)/VSAT_LIMA)
B2 b 0 V=VSAT_LIMA*rapp(10**(LIMA_G/20)*V(a)/VSAT_LIMA)
B3 c 0 V=2*VSAT_LIMA*rapp(10**(LIMA_G/20)*V(b)/VSAT_LIMA)
R3 c f 50
XF f g LPF3 FC={{LIMA_FLP}}
R_L g 0 50
B4 o 0 V=2*V(g)
R4 o out 50
.ends LIM_AMP

* =============================================================================
*  [6] DELAY-LINE DISCRIMINATOR
* =============================================================================
* coax = ideal delay + matched T-pad for loss. Load (50 ohm) is the mixer port.
.subckt COAX_REF in out
T1 in 0 m 0 Td={{TD_REF}} Z0=50
R1 m x {{padr1(LOSS_REF)}}
R2 x out {{padr1(LOSS_REF)}}
R3 x 0 {{padr2(LOSS_REF)}}
.ends COAX_REF

.subckt COAX_DLY in out
T1 in 0 m 0 Td={{TD_DLY}} Z0=50
R1 m x {{padr1(LOSS_DLY)}}
R2 x out {{padr1(LOSS_DLY)}}
R3 x 0 {{padr2(LOSS_DLY)}}
.ends COAX_DLY

* ZX05-30W-S+ as phase detector. DC out = K*cos(2*pi*f*dt); 2f removed by LPF
.subckt PHASE_DET rf lo out
R_rf rf 0 50
R_lo lo 0 50
B1 a 0 V=2*if(MIXMODE==0, V(rf)*V(lo), KPD*V(rf)*tanh(V(lo)/VSW_PD))
R1 a f 50
XF f g LPF3 FC={{PD_FLP}}
R_L g 0 50
B2 out 0 V=V(g)
.ends PHASE_DET

* =============================================================================
*  [7] SAMPLE / HOLD + SCALING
* =============================================================================
* FPGA timing: sample = det delayed by SH_DLY, lasting SH_WIDTH (ideal delays)
.subckt SH_CTRL det sample
E1 a 0 det 0 1
T1 a 0 b 0 Td={{SH_DLY}} Z0=50
R1 b 0 50
E2 b2 0 b 0 1
T2 b2 0 c 0 Td={{SH_WIDTH}} Z0=50
R2 c 0 50
B1 sample 0 V=limit(V(b),0,1)*(1-limit(V(c),0,1))
.ends SH_CTRL

* ADG1211 switch + hold capacitor, buffered in and out
.subckt SAMPLE_HOLD in ctrl out
E1 a 0 in 0 1
B1 a hold I=(V(a)-V(hold))*(limit(V(ctrl),0,1)/SH_RON + 1/SH_ROFF)
C1 hold 0 {{SH_C}}
R_LEAK hold 0 1e12
E2 out 0 hold 0 1
.ends SAMPLE_HOLD

* ADA4622: Vtune = VT_CENTER + OPA_GAIN*(Vhold - PD_V0), rail clamped, 1-pole GBW
.subckt OPAMP_SCALE in out
B1 a 0 V=limit(VT_CENTER + OPA_GAIN*(V(in)-PD_V0), OPA_VMIN, OPA_VMAX)
R1 a b 1k
C1 b 0 {{max(1,abs(OPA_GAIN))/(2*pi*1k*OPA_GBW)}}
B2 out 0 V=V(b)
.ends OPAMP_SCALE

* =============================================================================
*  [9] VCO + MORSE KEYING
* =============================================================================
* Crystek CVCO55BE: linear tune curve through (VCO_V1,VCO_F1),(VCO_V2,VCO_F2)
* f_GHz pin = instantaneous frequency in GHz (for plotting)
.subckt VCO tune out f_GHz
B0 f_GHz 0 V=limit(VCO_F1+(V(tune)-VCO_V1)*(VCO_F2-VCO_F1)/(VCO_V2-VCO_V1), VCO_FMIN, VCO_FMAX)/1e9
B_PH ph 0 V=idt(1e9*V(f_GHz))
B1 o 0 V=2*VCO_ON*dbm2v(P_VCO)*sin(2*pi*V(ph))
R1 o out 50
.ends VCO

* FPGA: latch the detection, wait MORSE_HOLDOFF, key ". - ." (dot 1U, dash 3U, gaps 1U)
.subckt FPGA_MORSE det key
B_L lo 0 V=if((V(det)>0.5)|(V(lat)>0.5), 1, 0)
R_L lo lat 1k
C_L lat 0 1p
* tdet = detection time in ns (integrates until latched)
B_T tdet 0 V=idt(1e9*(1-V(lat)))
B_T0 t0 0 V=if(TEST==9, 20, V(tdet)+MORSE_HOLDOFF*1e9)
B_EN en 0 V=if(TEST==9, 1, V(lat))
.param TAU0=0
B_M m 0 V=V(en)*{morse("(time*1e9-V(t0))")}
R_M m key 1k
C_M key 0 {{KEY_TR/1k}}
.ends FPGA_MORSE

* ADG901 absorptive SPST switch
.subckt KEY_SW in ctrl out
R_in in 0 50
B1 o 0 V=2*10**(-KEY_IL/20)*V(in)*(10**(-KEY_ISO/20)+(1-10**(-KEY_ISO/20))*limit(V(ctrl),0,1))
R1 o out 50
.ends KEY_SW

* =============================================================================
*  [8] TX RF CHAIN
* =============================================================================
* up-converting mixer (IF, LO -> RF): f_LO +/- f_IF plus LO leakage
.subckt MIX_UP if lo rf
R_if if 0 50
R_lo lo 0 50
B1 a 0 V=2*(KMIX*V(if)*tanh(V(lo)/VSW_MIX) + 10**(-MIX_LORF_ISO/20)*V(lo))
R1 a rf 50
.ends MIX_UP

* VHF-8400+ stand-in: 9th-order 0.5 dB Chebyshev high-pass, corner IRF_FC
.subckt IMG_REJ in out
{irf_txt}
R_L n8 0 50
B1 o 0 V=2*10**(-IRF_IL/20)*V(n8)
R1 o out 50
.ends IMG_REJ

.subckt PA in out
X1 in out AMP G={{PA_G}} P1={{PA_P1DB}}
.ends PA

.subckt TX_ANT in
R1 in 0 50
.ends TX_ANT
"""


# =============================================================================
#  SYMBOLS + SCHEMATIC
# =============================================================================
class Block:
    def __init__(self, model, title, subtitle, left=(), right=(), bottom=(), width=208, spiceline=""):
        self.model = model
        self.title = title
        self.subtitle = subtitle
        self.left = list(left)
        self.right = list(right)
        self.bottom = list(bottom)
        self.w = width
        rows = max(len(self.left), len(self.right), 1)
        self.h = max(96, 64 + 48 * rows)
        self.spiceline = spiceline

    def pins(self):
        """(name, x, y, side) in symbol coordinates, SpiceOrder = subckt order."""
        out = []
        for i, n in enumerate(self.left):
            out.append((n, 0, 64 + 48 * i, "L"))
        for i, n in enumerate(self.right):
            out.append((n, self.w, 64 + 48 * i, "R"))
        nb = len(self.bottom)
        for i, n in enumerate(self.bottom):
            x = int(round(self.w * (i + 1) / (nb + 1) / 16) * 16)
            out.append((n, x, self.h, "B"))
        return out

    def asy(self, pin_order):
        lines = ["Version 4", "SymbolType CELL",
                 f"RECTANGLE Normal 0 0 {self.w} {self.h}",
                 f"TEXT {self.w // 2} 20 Center 2 {self.title}",
                 f"TEXT {self.w // 2} 44 Center 0 {self.subtitle}",
                 f"WINDOW 0 {self.w // 2} -8 Bottom 2",
                 f"WINDOW 39 {self.w // 2} {self.h + 40} Top 1",
                 "SYMATTR Prefix X",
                 f"SYMATTR SpiceModel {self.model}",
                 f"SYMATTR Description JACON block: {self.title} - {self.subtitle}"]
        pmap = {p[0]: p for p in self.pins()}
        just = {"L": "LEFT", "R": "RIGHT", "B": "BOTTOM"}
        for k, name in enumerate(pin_order, start=1):
            _, x, y, side = pmap[name]
            lines += [f"PIN {x} {y} {just[side]} 8", f"PINATTR PinName {name}", f"PINATTR SpiceOrder {k}"]
        return "\n".join(lines) + "\n"


# model -> (block template, subckt pin order)
B = {
    "RADAR_SRC": (Block("RADAR_SRC", "RADAR ECHO", "9.4 GHz pulse @ RX antenna", right=["out"]), ["out"]),
    "TESTBENCH": (Block("TESTBENCH", "TEST STIMULI", "used by TSEL switches", right=["stim_if", "stim_pd", "stim_det", "stim_vtune"], width=240),
                  ["stim_if", "stim_pd", "stim_det", "stim_vtune"]),
    "TSEL_RF": (Block("TSEL_RF", "TEST SEL (RF)", "stim when TEST=N", left=["norm"], right=["out"], bottom=["stim"], width=176), ["norm", "stim", "out"]),
    "TSEL_V": (Block("TSEL_V", "TEST SEL (V)", "stim when TEST=N", left=["norm"], right=["out"], bottom=["stim"], width=176), ["norm", "stim", "out"]),
    "LIMITER": (Block("LIMITER", "POWER LIMITER", "Aaronia SMA 20GHz", left=["in"], right=["out"]), ["in", "out"]),
    "LNA": (Block("LNA", "LNA", "ZX60-5123LN+ 22dB", left=["in"], right=["out"]), ["in", "out"]),
    "MIX_DOWN": (Block("MIX_DOWN", "RX MIXER", "ZX05-14LH-S+", left=["rf"], right=["if"], bottom=["lo"]), ["rf", "lo", "if"]),
    "PLL_LO": (Block("PLL_LO", "PLL LO", "ADF5355 @ 8.3 GHz", right=["out"]), ["out"]),
    "LO_BUF": (Block("LO_BUF", "LO BUFFER", "ZX60-14012L-S+", left=["in"], right=["out"]), ["in", "out"]),
    "SPLIT_LO": (Block("SPLIT_LO", "LO SPLITTER", "ZX10-2-1252-S+", left=["in"], right=["o1", "o2"]), ["in", "o1", "o2"]),
    "IF_AMP": (Block("IF_AMP", "IF AMP", "ZX60-P162LN+ 22.5dB", left=["in"], right=["out"]), ["in", "out"]),
    "SPLIT_RES": (Block("SPLIT_RES", "50R SPLITTER", "ZFRSC-42-S+ resistive", left=["in"], right=["o1", "o2"]), ["in", "o1", "o2"]),
    "ENV_DET": (Block("ENV_DET", "ENVELOPE DET", "ADL5511", left=["in"], right=["out"]), ["in", "out"]),
    "DAC": (Block("DAC", "THRESHOLD DAC", "nanoDAC", right=["out"], width=176), ["out"]),
    "COMPARATOR": (Block("COMPARATOR", "COMPARATOR", "ADCMP600", left=["inp", "inn"], right=["out"]), ["inp", "inn", "out"]),
    "LIM_AMP": (Block("LIM_AMP", "LIMITING AMP", "3x GALI-52+ + LPF", left=["in"], right=["out"]), ["in", "out"]),
    "COAX_REF": (Block("COAX_REF", "COAX REF ARM", "L_REF_IN", left=["in"], right=["out"]), ["in", "out"]),
    "COAX_DLY": (Block("COAX_DLY", "COAX DELAY ARM", "L_REF_IN + DL_IN", left=["in"], right=["out"]), ["in", "out"]),
    "PHASE_DET": (Block("PHASE_DET", "PHASE DETECTOR", "ZX05-30W-S+ + LPF", left=["rf", "lo"], right=["out"]), ["rf", "lo", "out"]),
    "SH_CTRL": (Block("SH_CTRL", "S/H TIMING", "FPGA: SH_DLY, SH_WIDTH", left=["det"], right=["sample"]), ["det", "sample"]),
    "SAMPLE_HOLD": (Block("SAMPLE_HOLD", "SAMPLE & HOLD", "ADG1211 + 100pF C0G", left=["in"], right=["out"], bottom=["ctrl"]), ["in", "ctrl", "out"]),
    "OPAMP_SCALE": (Block("OPAMP_SCALE", "SHIFT & SCALE", "ADA4622 op-amp", left=["in"], right=["out"]), ["in", "out"]),
    "VCO": (Block("VCO", "VCO", "CVCO55BE 1.0-1.2 GHz", left=["tune"], right=["out", "f_GHz"]), ["tune", "out", "f_GHz"]),
    "FPGA_MORSE": (Block("FPGA_MORSE", "FPGA MORSE", "latch, holdoff, . - .", left=["det"], right=["key"]), ["det", "key"]),
    "KEY_SW": (Block("KEY_SW", "KEYING SWITCH", "ADG901", left=["in"], right=["out"], bottom=["ctrl"]), ["in", "ctrl", "out"]),
    "MIX_UP": (Block("MIX_UP", "TX MIXER", "ZX05-14LH-S+", left=["if"], right=["rf"], bottom=["lo"]), ["if", "lo", "rf"]),
    "IMG_REJ": (Block("IMG_REJ", "IMAGE REJECT HPF", "VHF-8400+", left=["in"], right=["out"]), ["in", "out"]),
    "PA": (Block("PA", "POWER AMP", "ZVE-143-S+ ~1W", left=["in"], right=["out"]), ["in", "out"]),
    "TX_ANT": (Block("TX_ANT", "TX ANTENNA", "50 ohm load", left=["in"], width=176), ["in"]),
}

# (section, instance, model, x, y, {pin: net}, spiceline)
SECTIONS = {
    "S0": ("[0] TEST BENCH STIMULI  (only active in per-block tests)", ),
    "S1": ("[1] RX RF FRONT END   9.3-9.5 GHz", ),
    "S2": ("[2] LO GENERATION   8.3 GHz", ),
    "S3": ("[3] IF CHAIN   1.0-1.2 GHz", ),
    "S4": ("[4] PULSE DETECTION  (is a radar pinging?)", ),
    "S5": ("[5] LIMITING AMP  (remove amplitude info)", ),
    "S6": ("[6] DELAY-LINE DISCRIMINATOR  (frequency -> DC)", ),
    "S7": ("[7] SAMPLE & HOLD + SHIFT/SCALE  (DC -> VCO tune V)", ),
    "S9": ("[9] VCO + FPGA MORSE KEYING", ),
    "S8": ("[8] TX RF CHAIN   back up to the radar frequency", ),
}

X0, DX = 0, 480
R1, R2, R3, R4, R5 = 0, 640, 1280, 1920, 2640
INST = [
    ("S1", "X_RADAR", "RADAR_SRC", X0, R1, {"out": "rf_ant"}, ""),
    ("S1", "X_LIM", "LIMITER", X0 + DX, R1, {"in": "rf_ant", "out": "rf_lim"}, ""),
    ("S1", "X_LNA", "LNA", X0 + 2 * DX, R1, {"in": "rf_lim", "out": "rf_lna"}, ""),
    ("S1", "X_MIXRX", "MIX_DOWN", X0 + 3 * DX, R1, {"rf": "rf_lna", "lo": "lo_rx", "if": "if_mix"}, ""),

    ("S8", "X_MIXTX", "MIX_UP", X0 + 5 * DX, R1, {"if": "if_keyed", "lo": "lo_tx", "rf": "tx_mix"}, ""),
    ("S8", "X_IRF", "IMG_REJ", X0 + 6 * DX, R1, {"in": "tx_mix", "out": "tx_filt"}, ""),
    ("S8", "X_PA", "PA", X0 + 7 * DX, R1, {"in": "tx_filt", "out": "tx_out"}, ""),
    ("S8", "X_TXANT", "TX_ANT", X0 + 8 * DX, R1, {"in": "tx_out"}, ""),

    ("S2", "X_PLL", "PLL_LO", X0 + 3 * DX, R2, {"out": "lo_pll"}, ""),
    ("S2", "X_LOBUF", "LO_BUF", X0 + 4 * DX, R2, {"in": "lo_pll", "out": "lo_buf"}, ""),
    ("S2", "X_LOSPL", "SPLIT_LO", X0 + 5 * DX, R2, {"in": "lo_buf", "o1": "lo_rx", "o2": "lo_tx"}, ""),

    ("S3", "X_IFAMP", "IF_AMP", X0, R3, {"in": "if_mix", "out": "if_amp"}, ""),
    ("S3", "X_S1", "TSEL_RF", X0 + DX, R3, {"norm": "if_amp", "stim": "stim_if", "out": "if_split_in"}, "N1=4"),
    ("S3", "X_IFSPL", "SPLIT_RES", X0 + 2 * DX, R3, {"in": "if_split_in", "o1": "if_to_lim", "o2": "if_to_env"}, ""),

    ("S4", "X_ENV", "ENV_DET", X0 + 3 * DX + 120, R3, {"in": "if_to_env", "out": "env"}, ""),
    ("S4", "X_DAC", "DAC", X0 + 3 * DX + 120, R3 + 240, {"out": "vth"}, ""),
    ("S4", "X_COMP", "COMPARATOR", X0 + 4 * DX + 120, R3, {"inp": "env", "inn": "vth", "out": "det_raw"}, ""),

    ("S0", "X_TB", "TESTBENCH", X0 + 6 * DX, R3, {"stim_if": "stim_if", "stim_pd": "stim_pd", "stim_det": "stim_det", "stim_vtune": "stim_vtune"}, ""),

    ("S5", "X_S2", "TSEL_RF", X0, R4, {"norm": "if_to_lim", "stim": "stim_if", "out": "lim_in"}, "N1=5 N2=6"),
    ("S5", "X_LIMAMP", "LIM_AMP", X0 + DX, R4, {"in": "lim_in", "out": "lim_out"}, ""),

    ("S6", "X_DLSPL", "SPLIT_RES", X0 + 2 * DX + 120, R4, {"in": "lim_out", "o1": "dl_ref_in", "o2": "dl_dly_in"}, ""),
    ("S6", "X_CREF", "COAX_REF", X0 + 3 * DX + 120, R4 - 40, {"in": "dl_ref_in", "out": "pd_rf"}, ""),
    ("S6", "X_CDLY", "COAX_DLY", X0 + 3 * DX + 120, R4 + 200, {"in": "dl_dly_in", "out": "pd_lo"}, ""),
    ("S6", "X_PD", "PHASE_DET", X0 + 4 * DX + 120, R4, {"rf": "pd_rf", "lo": "pd_lo", "out": "pd_out"}, ""),

    ("S7", "X_S3", "TSEL_V", X0, R5, {"norm": "pd_out", "stim": "stim_pd", "out": "sh_in"}, "N1=7"),
    ("S7", "X_S4", "TSEL_V", X0, R5 + 320, {"norm": "det_raw", "stim": "stim_det", "out": "det"}, "N1=7"),
    ("S7", "X_SHC", "SH_CTRL", X0 + DX, R5 + 320, {"det": "det", "sample": "sh_ctrl"}, ""),
    ("S7", "X_SH", "SAMPLE_HOLD", X0 + DX, R5, {"in": "sh_in", "ctrl": "sh_ctrl", "out": "sh_hold"}, ""),
    ("S7", "X_OPA", "OPAMP_SCALE", X0 + 2 * DX, R5, {"in": "sh_hold", "out": "vtune_opa"}, ""),

    ("S9", "X_S5", "TSEL_V", X0 + 3 * DX + 120, R5, {"norm": "vtune_opa", "stim": "stim_vtune", "out": "vtune"}, "N1=8 N2=9"),
    ("S9", "X_VCO", "VCO", X0 + 4 * DX + 120, R5, {"tune": "vtune", "out": "if_vco", "f_GHz": "vco_f_GHz"}, ""),
    ("S9", "X_FPGA", "FPGA_MORSE", X0 + 4 * DX + 120, R5 + 320, {"det": "det", "key": "key"}, ""),
    ("S9", "X_KEY", "KEY_SW", X0 + 5 * DX + 120, R5, {"in": "if_vco", "ctrl": "key", "out": "if_keyed"}, ""),
]


def fmt_param_block(title, items):
    width = max(len(f".param {n}={v}") for n, v, _ in items) + 2
    lines = [f"* ---- {title} ----"]
    for n, v, c in items:
        lines.append(f".param {n}={v}".ljust(width) + f"; {c}")
    return "\\n".join(lines)


def build_schematic() -> str:
    out = ["Version 4", "SHEET 1 6400 4400"]
    boxes: dict[str, list[int]] = {}
    for sec, inst, model, x, y, nets, spl in INST:
        blk, _ = B[model]
        for name, px, py, side in blk.pins():
            ax, ay = x + px, y + py
            if side == "L":
                bx, by = ax - 64, ay
            elif side == "R":
                bx, by = ax + 64, ay
            else:
                bx, by = ax, ay + 64
            out.append(f"WIRE {bx} {by} {ax} {ay}")
            out.append(f"FLAG {bx} {by} {nets[name]}")
        out.append(f"SYMBOL jacon_{model.lower()} {x} {y} R0")
        out.append(f"SYMATTR InstName {inst}")
        if spl:
            out.append(f"SYMATTR SpiceLine {spl}")
        bb = [x - 170, y - 90, x + blk.w + 170, y + blk.h + 120]
        if sec in boxes:
            b = boxes[sec]
            boxes[sec] = [min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3])]
        else:
            boxes[sec] = bb
    for sec, (x1, y1, x2, y2) in boxes.items():
        out.append(f"RECTANGLE Normal {x2} {y2} {x1} {y1} 2")
        out.append(f"TEXT {x1 + 16} {y1 - 16} Left 3 ;{SECTIONS[sec][0]}")

    # ---- title
    out.append("TEXT 0 -360 Left 7 ;JACON  -  Jason's RACON draft design  (LTspice behavioral model)")
    out.append("TEXT 0 -240 Left 3 ;RX 9.3-9.5 GHz radar pulse -> 1.1 GHz IF -> detect + measure frequency with a delay line -> "
               "hold -> VCO -> key Morse '. - .' -> mix back up with the same LO -> TX at the radar frequency.")
    out.append("TEXT 0 -160 Left 2 ;Every net is named: click a label to plot it. Voltages are RF amplitudes in 50 ohm: "
               "P(dBm) = 10*log10(V^2/100m).  Block models: jacon_blocks.inc.  Python plots: run_tests.py")

    # ---- TEST SELECT panel
    px, py = 4400, 0
    tst = [".param TEST=0   ; <<<<<<<<<<<<  CHANGE THIS NUMBER TO PICK WHAT TO SIMULATE  >>>>>>>>>>>>"]
    tst.append(".param TSTOP=table(TEST, " + ", ".join(f"{n},{t}" for n, _, t, _, _ in TESTS) + ")")
    tst.append(".param TMAX=table(TEST, " + ", ".join(f"{n},{m}" for n, _, _, m, _ in TESTS) + ")")
    tst.append(".tran 0 {TSTOP} 0 {TMAX}")
    tst.append(".include jacon_blocks.inc")
    out.append(f"TEXT {px} {py + 120} Left 3 !" + "\\n".join(tst))
    legend = ["TEST  what is exercised                          -> nets worth plotting"]
    probe = {
        0: "rf_ant, env, det, lim_out, pd_out, sh_hold, vtune, vco_f_GHz, key, tx_out",
        1: "rf_ant, rf_lim, rf_lna",
        2: "lo_pll, lo_buf, lo_rx, lo_tx",
        3: "rf_lna, if_mix, if_amp   (View > FFT)",
        4: "if_split_in, env, vth, det_raw",
        5: "lim_in, lim_out",
        6: "lim_out, pd_rf, pd_lo, pd_out",
        7: "sh_in, det, sh_ctrl, sh_hold, vtune_opa",
        8: "vtune, vco_f_GHz, if_vco",
        9: "key, if_keyed, tx_mix, tx_filt, tx_out   (View > FFT)",
        10: "add  .step param F_RADAR list 9.3e9 9.35e9 9.4e9 9.45e9 9.5e9 ; plot vco_f_GHz",
    }
    for n, name, _, _, desc in TESTS:
        legend.append(f"{n:>3}   {name:<26} {desc}")
        legend.append(f"      probe: {probe[n]}")
    out.append(f"TEXT {px} {py + 480} Left 2 ;" + "\\n".join(legend))
    out.append(f"RECTANGLE Normal {px + 2300} {py + 1400} {px - 40} {py - 20} 2")
    out.append(f"TEXT {px} {py - 40} Left 5 ;TEST SELECT")

    # ---- PARAMETERS panel
    y = py + 1600
    out.append(f"TEXT {px} {y - 40} Left 5 ;PARAMETERS  (part values from the drawing; 'check' = assumed)")
    col = 0
    ycol = [y + 40, y + 40]
    for title, items in PARAM_GROUPS:
        xcol = px + col * 1500
        out.append(f"TEXT {xcol} {ycol[col]} Left 1 !" + fmt_param_block(title, items))
        ycol[col] += 40 + 34 * (len(items) + 1)
        col = 1 - col if ycol[1 - col] < ycol[col] else col
    out.append(f"RECTANGLE Normal {px + 3000} {max(ycol) + 40} {px - 40} {y - 90} 2")
    return "\n".join(out) + "\n"


def build_ac_deck() -> str:
    params = []
    for _, items in PARAM_GROUPS:
        for n, v, _ in items:
            params.append(f".param {n}={v}")
    return f"""* filters_ac.cir - small-signal responses of the JACON filters / amplifiers
* (generated by build_jacon.py)  plot V(*_out) in dB
.param TEST=-1 TSTOP=1
{chr(10).join(params)}
.include jacon_blocks.inc

* image-reject high-pass (TX)
V1 s1 0 AC 2
R1 s1 a1 50
X_IRF a1 irf_out IMG_REJ
R_IRF irf_out 0 50

* RX mixer IF port low-pass (LPF3 @ MIX_IFBW)
V2 s2 0 AC 2
R2 s2 a2 50
X_L2 a2 mixif_out LPF3 FC={{MIX_IFBW}}
R_L2 mixif_out 0 50

* phase detector low-pass
V3 s3 0 AC 2
R3 s3 a3 50
X_L3 a3 pdlpf_out LPF3 FC={{PD_FLP}}
R_L3 pdlpf_out 0 50

* limiter harmonic low-pass
V4 s4 0 AC 2
R4 s4 a4 50
X_L4 a4 limlpf_out LPF3 FC={{LIMA_FLP}}
R_L4 limlpf_out 0 50

* IF amplifier (small signal)
V5 s5 0 AC 2
R5 s5 a5 50
X_IFA a5 ifamp_out IF_AMP
R_IFA ifamp_out 0 50

.ac dec 400 10e6 20e9
.end
"""


def main():
    (HERE / "jacon_blocks.inc").write_text(build_library())
    for model, (blk, order) in B.items():
        (HERE / f"jacon_{model.lower()}.asy").write_text(blk.asy(order))
    (HERE / "JACON_system.asc").write_text(build_schematic())
    (HERE / "filters_ac.cir").write_text(build_ac_deck())
    print(f"C1_TANH4 = {C1_TANH4:.6f}")
    print("Chebyshev g:", ", ".join(f"{g:.4f}" for g in G_IRF))
    print("wrote JACON_system.asc, jacon_blocks.inc, filters_ac.cir and", len(B), "symbols")


if __name__ == "__main__":
    main()
