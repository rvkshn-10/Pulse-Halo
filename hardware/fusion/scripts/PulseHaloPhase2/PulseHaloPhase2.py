import adsk.core
import adsk.fusion
import adsk.cam
import os
import traceback


REPO = r"C:\Users\ravip\Documents\Codex\2026-10-27\okw\work\Pulse-Halo"
PCB_STEP = os.path.join(REPO, "manufacturing", "Pulse-Halo-board.step")
OUTPUT_DIR = os.path.join(REPO, "hardware", "fusion")
SCREENSHOT_DIR = os.path.join(REPO, "docs", "screenshots", "phase-2")


def mm(value):
    return value / 10.0


def value_mm(value):
    return adsk.core.ValueInput.createByString(f"{value} mm")


def point(x_mm, y_mm, z_mm=0):
    return adsk.core.Point3D.create(mm(x_mm), mm(y_mm), mm(z_mm))


def add_offset_plane(component, base_plane, offset_mm, name):
    plane_input = component.constructionPlanes.createInput()
    plane_input.setByOffset(base_plane, value_mm(offset_mm))
    plane = component.constructionPlanes.add(plane_input)
    plane.name = name
    return plane


def rectangle_profile(component, plane, x1, y1, x2, y2, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x1, y1), point(x2, y2))
    return sketch, sketch.profiles.item(0)


def circle_profiles(component, plane, circles, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    for x, y, diameter in circles:
        sketch.sketchCurves.sketchCircles.addByCenterRadius(point(x, y), mm(diameter / 2.0))
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    return sketch, profiles


def extrude(component, profiles, distance_mm, operation, name, symmetric=False):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profiles, operation)
    extrude_input.setDistanceExtent(symmetric, value_mm(distance_mm))
    feature = extrudes.add(extrude_input)
    feature.name = name
    return feature


def cut_usb_slot(component):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "USB Access Slot"
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-7, -36), point(7, -32))
    extrude(component, sketch.profiles.item(0), 20, adsk.fusion.FeatureOperations.CutFeatureOperation, "USB and Cable Access")


def capture(app, number, slug, orientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation):
    adsk.doEvents()
    viewport = app.activeViewport
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.isFitView = True
    camera.viewOrientation = orientation
    viewport.camera = camera
    adsk.doEvents()
    path = os.path.join(SCREENSHOT_DIR, f"{number:02d}-{slug}.png")
    if not viewport.saveAsImageFile(path, 1600, 1000):
        raise RuntimeError(f"Could not save screenshot: {path}")


def import_and_center_pcb(app, root):
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occurrence.component.name = "Pulse Halo PCB Assembly"
    options = app.importManager.createSTEPImportOptions(PCB_STEP)
    app.importManager.importToTarget(options, occurrence.component)
    adsk.doEvents()

    bounds = occurrence.boundingBox
    center_x = (bounds.minPoint.x + bounds.maxPoint.x) / 2.0
    center_y = (bounds.minPoint.y + bounds.maxPoint.y) / 2.0
    min_z = bounds.minPoint.z
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(-center_x, -center_y, mm(7) - min_z)
    occurrence.transform2 = transform
    return occurrence


def save_and_export(app, document, design):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    archive_path = os.path.join(OUTPUT_DIR, "Pulse-Halo-Enclosure.f3d")
    step_path = os.path.join(OUTPUT_DIR, "Pulse-Halo-Enclosure.step")

    export_manager = design.exportManager
    archive_options = export_manager.createFusionArchiveExportOptions(archive_path)
    if not export_manager.execute(archive_options):
        raise RuntimeError("Fusion archive export failed")

    step_options = export_manager.createSTEPExportOptions(step_path, design.rootComponent)
    if not export_manager.execute(step_options):
        raise RuntimeError("STEP export failed")

    try:
        root_folder = app.data.activeProject.rootFolder
        phase_folder = root_folder.dataFolders.itemByName("Pulse Halo")
        if not phase_folder:
            phase_folder = root_folder.dataFolders.add("Pulse Halo")
        if not document.isSaved:
            document.saveAs("Pulse Halo Enclosure - Phase 2", phase_folder, "Desktop visualizer enclosure with installed PCB", "")
        else:
            document.save("Phase 2 enclosure complete")
    except:
        # The local F3D archive above remains the authoritative saved deliverable
        pass


def run(context):
    ui = None
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        app = adsk.core.Application.get()
        ui = app.userInterface
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        pcb_occurrence = import_and_center_pcb(app, root)
        capture(app, 1, "pcb-imported")

        pcb_occurrence.isLightBulbOn = False
        _, outer_profile = rectangle_profile(root, root.xYConstructionPlane, -36, -36, 36, 36, "Base Outer Profile")
        base_feature = extrude(root, outer_profile, 20, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Base Outer Shell")
        base_body = base_feature.bodies.item(0)
        base_body.name = "Enclosure Base"
        capture(app, 2, "base-block")

        cavity_plane = add_offset_plane(root, root.xYConstructionPlane, 3, "Cavity Floor Plane")
        _, cavity_profile = rectangle_profile(root, cavity_plane, -32, -32, 32, 32, "Interior Cavity")
        extrude(root, cavity_profile, 17, adsk.fusion.FeatureOperations.CutFeatureOperation, "Hollow Base Cavity")
        capture(app, 3, "base-cavity")

        standoffs = [(-25, -25, 8), (25, -25, 8), (25, 25, 8), (-25, 25, 8)]
        _, standoff_profiles = circle_profiles(root, cavity_plane, standoffs, "PCB Standoffs")
        extrude(root, standoff_profiles, 4, adsk.fusion.FeatureOperations.JoinFeatureOperation, "Four PCB Standoffs")
        holes = [(-25, -25, 3.2), (25, -25, 3.2), (25, 25, 3.2), (-25, 25, 3.2)]
        _, hole_profiles = circle_profiles(root, cavity_plane, holes, "PCB Mounting Holes")
        extrude(root, hole_profiles, 5, adsk.fusion.FeatureOperations.CutFeatureOperation, "Standoff Screw Holes")
        capture(app, 4, "pcb-standoffs")

        pcb_occurrence.isLightBulbOn = True
        capture(app, 5, "pcb-installed")

        cut_usb_slot(root)
        capture(app, 6, "usb-access")

        lid_occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        lid_occurrence.component.name = "Display Bezel and Lid"
        lid_transform = adsk.core.Matrix3D.create()
        lid_transform.translation = adsk.core.Vector3D.create(0, 0, mm(20))
        lid_occurrence.transform2 = lid_transform
        lid = lid_occurrence.component

        _, lid_profile = rectangle_profile(lid, lid.xYConstructionPlane, -36, -36, 36, 36, "Lid Outer Profile")
        lid_feature = extrude(lid, lid_profile, 4, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Front Lid")
        lid_feature.bodies.item(0).name = "Front Display Bezel"
        capture(app, 7, "lid-created")

        _, display_profiles = circle_profiles(lid, lid.xYConstructionPlane, [(0, 0, 45)], "Round Display Opening")
        extrude(lid, display_profiles, 5, adsk.fusion.FeatureOperations.CutFeatureOperation, "GC9A01 Display Window")
        capture(app, 8, "display-opening")

        control_holes = [
            (25, -22, 8),
            (-25, -24, 2.2),
            (-25, -20, 2.2),
            (-25, -16, 2.2),
            (-31, -31, 3.6),
            (31, -31, 3.6),
            (31, 31, 3.6),
            (-31, 31, 3.6),
        ]
        _, control_profiles = circle_profiles(lid, lid.xYConstructionPlane, control_holes, "Encoder Microphone and Lid Holes")
        extrude(lid, control_profiles, 5, adsk.fusion.FeatureOperations.CutFeatureOperation, "Front Controls and Fasteners")
        capture(app, 9, "controls-and-fasteners")

        stand_occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        stand_occurrence.component.name = "Desktop Cradle Stand"
        stand = stand_occurrence.component
        _, foot_profile = rectangle_profile(stand, stand.xYConstructionPlane, -32, 34, 32, 60, "Stand Foot")
        foot = extrude(stand, foot_profile, 4, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Desk Foot")
        foot.bodies.item(0).name = "Stand Foot"
        _, support_profile = rectangle_profile(stand, stand.xYConstructionPlane, -32, 51, 32, 56, "Rear Support")
        support = extrude(stand, support_profile, 34, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Rear Upright")
        support.bodies.item(0).name = "Rear Support"
        capture(app, 10, "desktop-stand")

        lid_occurrence.opacity = 0.35
        capture(app, 11, "complete-enclosure", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)
        lid_occurrence.opacity = 1.0
        save_and_export(app, document, design)
        print("Pulse Halo Phase 2 complete. The Fusion design, STEP export, and 11 screenshots were saved.")
    except:
        raise

