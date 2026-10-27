# JACON racon: bench tests, data and engineering notes

Harvey Mudd College clinic project. This repository holds the bench measurements, the scripts that took and
analysed them, and the engineering notes website.

## The website

- Source: `phase_detector_calibration/site/`
- Built copy served by GitHub Pages: `docs/index.html` (plots in `docs/img/`)
- One-file copy with every plot inside it: `JACON_notes_backup.html` (open it in a browser, no internet needed)

GitHub Pages is turned on in the repository settings: Settings, Pages, "Deploy from a branch", branch `main`, folder `/docs`.

### How to change the website

1. Edit the text in `phase_detector_calibration/site/`:
   - `content.py`: part table, VCO, splitter, phase detector, test gear, tests to run, errors
   - `content_parts.py`: LNA, RX mixer, IF amp, VCO, splitter and phase detector tabs
   - `content_more.py`: LO buffer and image filter tabs
   - `content_pluto.py`: Pluto tab (its tables are filled from `pluto_characterization/summary.json`)
   - `content_env.py`: Envelope detector and Comparator tabs
   - `build_site.py`: the schematic, the look up tables, and the list of tabs
   - `parts/style.css`, `parts/app.js`: appearance and page behaviour
2. Put new plots in `phase_detector_calibration/site/img/`.
3. Rebuild: `cd phase_detector_calibration/site` then `python build_site.py`. Needs Python 3 with `numpy`.
   This rewrites `index.html`, `docs/index.html`, `docs/img/` and `JACON_notes_backup.html`.
4. Commit and push. GitHub Pages updates in about a minute.

With Claude Code: open this repository and ask for the change. The rule the site follows is on the page itself:
one tab per part, and each part has Specs, Expected behavior, Test plan and Results. Numbers and how they were
calculated, no filler.

Every part tab follows `part_tab(title, subtitle, id, specs, expected, plan, results)` in `content_parts.py`.

## Review notes: marking text as validated or under question, and commenting

On the GitHub Pages site, press **Edit**, select some text, and choose Validated, Under question, Comment or Suggest a change.
GitHub opens a new issue with the quote filled in; submit it with your own GitHub account. The page then highlights that text
for everyone, and lists the note under the "Review notes" tab. A GitHub Action copies all notes into the `review/` folder
(`validated.md`, `under_question.md`, `comments.md`, `suggested_changes.md`, `resolved.md`) within about a minute.
Close the issue to withdraw or resolve a note.

Because the Action commits to `main`, run `git pull --rebase` before you push.

## Folders

| Folder | What is in it |
|---|---|
| `phase_detector_calibration/` | VCO tuning curve, splitter and mixer (phase detector) calibration, step response, noise, drift, deconvolution. Data, scripts, plots, and the website source in `site/`. |
| `vco_rise_time/` | VCO step response with the Syscomp CGR-201 and the oscilloscope. Drivers `cgr201.py` and `sds.py`. Raw captures in `data/`. |
| `lo_buffer_test/` | LO buffer amp ZX60-14012L-S+: gain, compression, output with no input. |
| `envelope_detector/` | Envelope detector ADL5511 (and comparator ADCMP604) bench test: `ed_sweep.py` steps the Pluto and reads VENV on the CGR-201 scope, `plot_ed_sweep.py`, data in `data/`, part limits, procedure, results and wiring drawings. |
| `pluto_characterization/` | ADALM-Pluto TX output measured straight into the spectrum analyzer: level against attenuation setting, frequency, tone scale; spectra; drift. `pluto_tx_calibration.csv` is the setting-to-dBm table. |
| `sdr/` | `pluto_cw.py`: Pluto tone control with a hard power limit. `pluto_safe_tx.grc`: GNU Radio flowgraph with the same limit. |
| `signal_hound/` | Python wrapper for the Signal Hound SM200B. |
| `documentation/` | Block diagrams, component power ratings, datasheet excerpts. |
| `measurements/` | Earlier hand measurements of the VCO. |
| `simulations/` | LTspice and GNU Radio simulations. |
| `animations/` | Racon Morse animation. |
| `datasheets/` | Datasheet PDFs for the parts. `build_site.py` copies them to `docs/datasheets/` so the website can link to them. |
| `review/` | Review notes copied from the GitHub issues. Generated; do not edit by hand. |
| `tools/` | `build_review.py`, which builds `review/` from the issues. |
| `docs/` | Built website for GitHub Pages. Do not edit by hand; it is overwritten by `build_site.py`. |

## Instruments the scripts talk to

| Instrument | Connection |
|---|---|
| Siglent SSA3021X spectrum analyzer | USB, VISA (`pyvisa`) |
| Siglent SDS1104X-E oscilloscope | USB, VISA (`pyvisa`) |
| Syscomp CGR-201 | USB serial, 115200 baud (`pyserial`; `envelope_detector/ed_sweep.py` uses the built-in `termios` and also reads its scope) |
| ADALM-Pluto | USB network, `ip:192.168.2.1`, `iio_attr` from libiio |
| Signal Hound SM200B | USB 3, Signal Hound SM API |

## Not in this repository

- LTspice `.raw` waveform files (up to 235 MB each, over GitHub's file limit). Re-run the simulation to get them.
- Signal Hound `sm_api.dll` and `sm_api.lib`. Install the Signal Hound SDK and copy them into `signal_hound/smdevice/`.
- Dated older copies of the website (`site_backups/`).

## Safety limits built into the scripts

`sdr/pluto_cw.py` refuses any Pluto attenuation below 31 dB, which keeps its output under -20 dBm. Change
`P_LIMIT_DBM` on purpose before testing a part with a lower limit (the ZX60-2534MA-S+ needs -35 dBm).
