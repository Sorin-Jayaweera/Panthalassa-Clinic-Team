# AN-72 foam enclosure around the 41" rotor

Envelope: 48" W x 48" D x 12" H. Foam on **top, back, left, right**. **Front and bottom open.**
Stock: Laird ECCOSORB AN-72, 24" x 24" x 0.236" (6 mm), Laird PN 78082099 / DigiKey 903-1517-ND.

Model: `foam_enclosure.SLDPRT` (rebuild with `python build_foam_enclosure.py` while SolidWorks is open).
Renders: `iso.jpg`, `front.jpg`, `top.jpg`.
Shop drawings: `foam_enclosure_drawings.pdf` (sheet 1 cut plan, sheet 2 assembly views + details + exploded view);
PNG copies `sheet1_cut_plan.png`, `sheet2_assembly.png`. Regenerate with `python make_drawings.py`.

## Boards: 7

| Board | Cut | Becomes |
|---|---|---|
| 1-4 | none | Top, 2 x 2 grid of full 24 x 24 sheets |
| 5 | rip into two 24 x 11.764 strips | Left wall (front + rear halves) |
| 6 | rip into two 24 x 11.764 strips | Right wall (front + rear halves) |
| 7 | rip into two strips, trim each to 23.764 x 11.764 | Back wall, fits between the side walls |

Walls are 12 - 0.236 = 11.764" tall so the top sheets sit on them; the leftover is a 24 x 0.47" sliver per wall board.
Interior clearance: 47.53" between side walls vs. the 41" rotor sweep, ~3.3" each side; 11.76" height vs. the 5" rotor.

Buy 8 if you want a spare.
