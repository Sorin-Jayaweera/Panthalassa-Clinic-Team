"""Build a SolidWorks multibody part of the AN-72 foam enclosure around the spinning rotor.

Frame: X = width (48"), Y = up (12"), Z = depth (48"). Origin at floor centre.
Front face (Z = +24") and bottom are open. Top + back + left + right are foam.
Run:  python build_foam_enclosure.py
"""
import os
import pythoncom
import win32com.client

IN = 0.0254  # SolidWorks API works in metres

# ---- parameters (inches) ----
W, D, H = 48.0, 48.0, 12.0     # outer envelope
T = 0.236                      # AN-72 thickness (6 mm)
BOARD = 24.0                   # stock sheet is 24 x 24
ROTOR_L, ROTOR_H, ROTOR_D = 41.0, 5.0, 3.0   # rotor bar (depth is a placeholder)
ROTOR_Y = H / 2                # rotor centred in the height

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PART_PATH = os.path.join(OUT_DIR, "foam_enclosure.SLDPRT")

FOAM_RGB = (0.15, 0.15, 0.15)
ROTOR_RGB = (0.85, 0.45, 0.10)
SWEEP_RGB = (0.20, 0.55, 0.95)


def panels():
    """(name, centre xyz, size xyz) for every foam piece, in inches."""
    wall_h = H - T                       # walls sit under the top sheets
    yc = wall_h / 2
    out = []
    # top: 4 full boards
    for i, x in enumerate((-W / 4, W / 4)):
        for j, z in enumerate((-D / 4, D / 4)):
            out.append((f"Top_{2*i+j+1}", (x, H - T / 2, z), (BOARD, T, BOARD)))
    # left / right walls: full 48" depth, two 24" strips each
    for side, x in (("Left", -W / 2 + T / 2), ("Right", W / 2 - T / 2)):
        for k, z in enumerate((-D / 4, D / 4)):
            out.append((f"{side}_{k+1}", (x, yc, z), (T, wall_h, BOARD)))
    # back wall: fits between the side walls, two strips trimmed to (48-2T)/2
    back_len = (W - 2 * T) / 2
    for k, x in enumerate((-back_len / 2, back_len / 2)):
        out.append((f"Back_{k+1}", (x, yc, -D / 2 + T / 2), (back_len, wall_h, T)))
    return out


def box_body(modeler, centre, size):
    """Axis-aligned box. CreateBodyFromBox3's width/length mapping is not obvious for an
    arbitrary axis, so build along +Y and check/swap against the body's bounding box."""
    cx, cy, cz = (c * IN for c in centre)
    sx, sy, sz = (s * IN for s in size)
    for a, b in ((sx, sz), (sz, sx)):
        data = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                                       [cx, cy - sy / 2, cz, 0, 1, 0, a, b, sy])
        body = modeler.CreateBodyFromBox3(data)
        body._FlagAsMethod("GetBodyBox")
        bb = body.GetBodyBox()
        if abs((bb[3] - bb[0]) - sx) < 1e-6 and abs((bb[5] - bb[2]) - sz) < 1e-6:
            return body
    raise RuntimeError(f"box orientation failed for {centre} {size}")


def cyl_body(modeler, centre, radius, height):
    cx, cy, cz = (c * IN for c in centre)
    data = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                                   [cx, cy - height * IN / 2, cz, 0, 1, 0, radius * IN, height * IN])
    return modeler.CreateBodyFromCyl(data)


def colour(feat, rgb, transparency=0.0):
    props = [rgb[0], rgb[1], rgb[2], 1.0, 1.0, 0.5, 0.4, transparency, 0.0]
    feat.SetMaterialPropertyValues2(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, props), 1, None)


def main():
    import time
    for _ in range(90):  # attach to a running SolidWorks; it can take a while to register
        try:
            sw = win32com.client.GetActiveObject("SldWorks.Application")
            break
        except pythoncom.com_error:
            time.sleep(5)
    else:
        sw = win32com.client.Dispatch("SldWorks.Application")
    sw.Visible = True
    template = sw.GetUserPreferenceStringValue(8)  # swDefaultTemplatePart
    if not template:  # fresh installs may ship only the MBD templates
        template = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2026\templates\MBD\part 1001mm and larger.prtdot"
    model = sw.NewDocument(template, 0, 0, 0)
    part = model
    # late binding mistakes no-arg / VARIANT-arg methods for properties
    sw._FlagAsMethod("GetModeler")
    model._FlagAsMethod("ViewZoomtofit2", "GraphicsRedraw2")
    modeler = sw.GetModeler()
    modeler._FlagAsMethod("CreateBodyFromBox3", "CreateBodyFromCyl")

    # inches for display
    model.Extension.SetUserPreferenceInteger(200, 0, 3)  # swUnitSystem -> IPS

    def add(name, body, rgb, transparency=0.0):
        feat = part.CreateFeatureFromBody3(body, False, 0)
        feat.Name = name
        colour(feat, rgb, transparency)
        return feat

    for name, c, s in panels():
        add(name, box_body(modeler, c, s), FOAM_RGB)

    add("Rotor_bar", box_body(modeler, (0, ROTOR_Y, 0), (ROTOR_L, ROTOR_H, ROTOR_D)), ROTOR_RGB)
    add("Rotor_sweep_41in", cyl_body(modeler, (0, ROTOR_Y, 0), ROTOR_L / 2, ROTOR_H),
        SWEEP_RGB, transparency=0.75)

    model.ShowNamedView2("*Isometric", 7)
    model.ViewZoomtofit2()
    model.GraphicsRedraw2()

    nothing = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
    errs = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warns = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    model.Extension.SaveAs(PART_PATH, 0, 1, nothing, errs, warns)
    for view, fname in (("*Isometric", "iso.jpg"), ("*Front", "front.jpg"), ("*Top", "top.jpg")):
        model.ShowNamedView2(view, -1)
        model.ViewZoomtofit2()
        model.Extension.SaveAs(os.path.join(OUT_DIR, fname), 0, 1, nothing, errs, warns)
    model.ShowNamedView2("*Isometric", 7)
    model.ViewZoomtofit2()
    print("saved", PART_PATH, "errors", errs.value, "warnings", warns.value)


if __name__ == "__main__":
    main()
