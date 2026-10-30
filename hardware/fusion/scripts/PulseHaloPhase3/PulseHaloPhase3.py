import math
import os

import adsk.core
import adsk.fusion


REPO = r"C:\Users\ravip\Documents\Codex\2026-10-27\okw\work\Pulse-Halo"
PCB_STEP = os.path.join(REPO, "manufacturing", "Pulse-Halo-board.step")
OUTPUT_DIR = os.path.join(REPO, "hardware", "fusion")
SCREENSHOT_DIR = os.path.join(REPO, "docs", "screenshots", "phase-3")


def mm(value):
    return value / 10.0


def value_mm(value):
    return adsk.core.ValueInput.createByString(f"{value} mm")


def point(x, y, z=0):
    return adsk.core.Point3D.create(x, y, z)


def offset_plane(component, offset_cm, name):
    plane_input = component.constructionPlanes.createInput()
    plane_input.setByOffset(
        component.xYConstructionPlane,
        adsk.core.ValueInput.createByReal(offset_cm),
    )
    plane = component.constructionPlanes.add(plane_input)
    plane.name = name
    return plane


def extrude(component, profiles, distance_mm, operation, name):
    feature_input = component.features.extrudeFeatures.createInput(profiles, operation)
    feature_input.setDistanceExtent(False, value_mm(distance_mm))
    feature = component.features.extrudeFeatures.add(feature_input)
    feature.name = name
    return feature


def circle_profiles(component, plane, specs, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    for x, y, diameter_mm in specs:
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            point(x, y), mm(diameter_mm / 2)
        )
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    return profiles


def annular_profile(component, plane, cx, cy, outer_mm, inner_mm, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(cx, cy), mm(outer_mm / 2)
    )
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(cx, cy), mm(inner_mm / 2)
    )
    return min(
        (sketch.profiles.item(index) for index in range(sketch.profiles.count)),
        key=lambda profile: profile.areaProperties().area,
    )


def rectangle_profile(component, plane, x1, y1, x2, y2, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        point(x1, y1), point(x2, y2)
    )
    return sketch.profiles.item(0)


def capture(app, number, slug, direction):
    viewport = app.activeViewport
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.viewOrientation = direction
    camera.isFitView = True
    viewport.camera = camera
    adsk.doEvents()
    path = os.path.join(SCREENSHOT_DIR, f"{number:02d}-{slug}.png")
    if not viewport.saveAsImageFile(path, 1600, 1000):
        raise RuntimeError(f"Could not save {path}")


def set_visible(base_body, pcb, pedestal, lid, base_on, pcb_on, pedestal_on, lid_on):
    base_body.isVisible = base_on
    pcb.isLightBulbOn = pcb_on
    pedestal.isLightBulbOn = pedestal_on
    lid.isLightBulbOn = lid_on


def run(_context: str):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("Open the Pulse Halo Fusion design before running Phase 3")

    root = design.rootComponent
    base_body = root.bRepBodies.itemByName("Rounded Electronics Housing")
    pcb = root.occurrences.itemByName("Pulse Halo PCB Assembly:1")
    pedestal = root.occurrences.itemByName("Wide Anti-Tip Desktop Pedestal:1")
    lid_occurrence = root.occurrences.itemByName("Rounded Display Lid:1")
    if not all((base_body, pcb, pedestal, lid_occurrence)):
        raise RuntimeError("The active document is not the saved Pulse Halo enclosure")

    # Restore the real KiCad PCB into the archived assembly when the wrapper is empty.
    if pcb.component.bRepBodies.count == 0 and pcb.childOccurrences.count == 0:
        options = app.importManager.createSTEPImportOptions(PCB_STEP)
        app.importManager.importToTarget(options, pcb.component)
        adsk.doEvents()

    lid = lid_occurrence.component
    stand = pedestal.component
    lid_bounds = lid_occurrence.boundingBox
    base_bounds = base_body.boundingBox
    stand_bounds = pedestal.boundingBox
    cx = (base_bounds.minPoint.x + base_bounds.maxPoint.x) / 2
    cy = (base_bounds.minPoint.y + base_bounds.maxPoint.y) / 2
    lid_top = lid_bounds.maxPoint.z
    floor_top = base_bounds.minPoint.z + mm(3)
    stand_bottom = stand.bRepBodies.item(0).boundingBox.minPoint.z

    lid_top_plane = offset_plane(lid, lid_top, "Phase 3 Lid Top Plane")

    # 1: Twelve light-pipe windows echo the circular spectrum spikes.
    spectrum_windows = []
    for index in range(12):
        angle = math.radians(index * 30)
        spectrum_windows.append(
            (cx + mm(31) * math.cos(angle), cy + mm(31) * math.sin(angle), 2.4)
        )
    extrude(
        lid,
        circle_profiles(lid, lid_top_plane, spectrum_windows, "Circular Spectrum Light Pipes"),
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Twelve Circular Spectrum Windows",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, False, False, False, True)
    capture(app, 1, "spectrum-light-pipes", adsk.core.ViewOrientations.TopViewOrientation)

    # 2: Physical press-and-turn encoder knob for selecting visualizer modes.
    encoder_x = cx + mm(30)
    encoder_y = cy - mm(24)
    knob_feature = extrude(
        lid,
        circle_profiles(lid, lid_top_plane, [(encoder_x, encoder_y, 12)], "Mode Encoder Knob"),
        8,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Press-and-Turn Mode Encoder Knob",
    )
    knob_feature.bodies.item(0).name = "Mode Encoder Knob"
    capture(app, 2, "mode-encoder-knob", adsk.core.ViewOrientations.IsoTopRightViewOrientation)

    # 3: Seven-hole microphone grille supports AGC and clean beat detection.
    mic_x = cx - mm(30)
    mic_y = cy - mm(21)
    mic_holes = [
        (mic_x, mic_y, 2.0),
        (mic_x - mm(4), mic_y, 2.0),
        (mic_x + mm(4), mic_y, 2.0),
        (mic_x - mm(2), mic_y - mm(3.5), 2.0),
        (mic_x + mm(2), mic_y - mm(3.5), 2.0),
        (mic_x - mm(2), mic_y + mm(3.5), 2.0),
        (mic_x + mm(2), mic_y + mm(3.5), 2.0),
    ]
    extrude(
        lid,
        circle_profiles(lid, lid_top_plane, mic_holes, "Microphone Acoustic Grille"),
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Seven-Hole Microphone Grille",
    )
    capture(app, 3, "microphone-grille", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)

    # 4: Recessed NeoPixel channel surrounding the screen bezel.
    led_channel = annular_profile(
        lid, lid_top_plane, cx, cy, 70, 63, "NeoPixel Halo Channel"
    )
    extrude(
        lid,
        led_channel,
        -1.4,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Recessed NeoPixel Ring Channel",
    )
    capture(app, 4, "neopixel-ring-channel", adsk.core.ViewOrientations.IsoTopRightViewOrientation)

    # 5: Raised diffuser-retaining rim for swappable color-theme light pipes.
    diffuser_rim = annular_profile(
        lid, lid_top_plane, cx, cy, 73, 70.5, "Diffuser Retention Rim"
    )
    extrude(
        lid,
        diffuser_rim,
        1.2,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Raised Swappable Diffuser Retainer",
    )
    capture(app, 5, "diffuser-retainer", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)

    # 6: Side glow windows expose beat-triggered RGB light without weakening the base.
    glow_windows = []
    for y_offset in (-18, 0, 18):
        glow_windows.append((cx - mm(38), cy + mm(y_offset), 3.0))
        glow_windows.append((cx + mm(38), cy + mm(y_offset), 3.0))
    extrude(
        lid,
        circle_profiles(lid, lid_top_plane, glow_windows, "Beat Glow Windows"),
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Six Beat-Reactive Side Glow Windows",
    )
    capture(app, 6, "beat-glow-windows", adsk.core.ViewOrientations.TopViewOrientation)

    # 7: CR2032 recess in the pedestal supports a battery-backed ambient clock.
    stand_bottom_plane = offset_plane(stand, stand_bottom, "RTC Battery Pocket Plane")
    rtc_pocket = circle_profiles(
        stand, stand_bottom_plane, [(cx, cy, 24)], "CR2032 Battery Pocket"
    )
    extrude(
        stand,
        rtc_pocket,
        2.6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "CR2032 Clock Backup Pocket",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, False, False, True, False)
    capture(app, 7, "rtc-battery-pocket", adsk.core.ViewOrientations.BottomViewOrientation)

    # 8: Dual posts provide a zip-tie strain relief for power and configuration cables.
    relief_posts = [
        (cx - mm(7), cy + mm(29), 5),
        (cx + mm(7), cy + mm(29), 5),
    ]
    root_floor_plane = offset_plane(root, floor_top, "Cable Strain Relief Plane")
    extrude(
        root,
        circle_profiles(root, root_floor_plane, relief_posts, "Cable Strain Relief Posts"),
        8,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Dual Cable Strain Relief Posts",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, True, False, True, False)
    capture(app, 8, "cable-strain-relief", adsk.core.ViewOrientations.IsoTopRightViewOrientation)

    # 9: Three status windows provide peak-hold and menu feedback LEDs.
    status_windows = [
        (cx - mm(8), cy - mm(33), 2.5),
        (cx, cy - mm(33), 2.5),
        (cx + mm(8), cy - mm(33), 2.5),
    ]
    extrude(
        lid,
        circle_profiles(lid, lid_top_plane, status_windows, "Peak Hold Status Windows"),
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Three Peak-Hold Status Windows",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, False, False, False, True)
    capture(app, 9, "peak-hold-status-windows", adsk.core.ViewOrientations.TopViewOrientation)

    # 10: Top-open USB-C configuration notch aligns with the existing rear cable exit.
    usb_profile = rectangle_profile(
        lid,
        lid_top_plane,
        cx - mm(7),
        cy + mm(35),
        cx + mm(7),
        cy + mm(42),
        "USB-C Configuration Notch",
    )
    extrude(
        lid,
        usb_profile,
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Rear USB-C Configuration Notch",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, True, False, True, True)
    capture(app, 10, "usb-c-configuration-notch", adsk.core.ViewOrientations.BackViewOrientation)

    # 11: Light-sensor aperture enables auto-dimming during clocks and screen savers.
    sensor_hole = [(cx + mm(29), cy + mm(27), 5)]
    extrude(
        lid,
        circle_profiles(lid, lid_top_plane, sensor_hole, "Ambient Light Sensor Aperture"),
        -6,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        "Ambient Light Sensor Window",
    )
    set_visible(base_body, pcb, pedestal, lid_occurrence, True, False, True, True)
    capture(app, 11, "complete-phase-3-features", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)

    # Save local manufacturing/editable artifacts with the full feature set.
    export_manager = design.exportManager
    f3d_path = os.path.join(OUTPUT_DIR, "Pulse-Halo-Enclosure-Phase3.f3d")
    step_path = os.path.join(OUTPUT_DIR, "Pulse-Halo-Enclosure-Phase3.step")
    if not export_manager.execute(export_manager.createFusionArchiveExportOptions(f3d_path)):
        raise RuntimeError("Phase 3 F3D export failed")
    if not export_manager.execute(export_manager.createSTEPExportOptions(step_path, root)):
        raise RuntimeError("Phase 3 STEP export failed")
    print("Implemented 11 Phase 3 CAD provisions and captured 11 screenshots")
