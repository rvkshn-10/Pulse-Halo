import math, os
import adsk.core, adsk.fusion

REPO = r"C:\Users\ravip\Documents\Codex\2026-10-27\okw\work\Pulse-Halo"
PCB_STEP = os.path.join(REPO, "manufacturing", "Pulse-Halo-board.step")
OUTPUT_DIR = os.path.join(REPO, "hardware", "fusion")
SCREENSHOT_DIR = os.path.join(REPO, "docs", "screenshots", "phase-2")

def mm(v): return v / 10.0
def vi(v): return adsk.core.ValueInput.createByString(f"{v} mm")
def pt(x, y, z=0): return adsk.core.Point3D.create(x, y, z)

def plane_at(comp, z, name):
    i = comp.constructionPlanes.createInput()
    i.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(z))
    p = comp.constructionPlanes.add(i); p.name = name
    return p

def rounded_rect(sk, cx, cy, w, h, r):
    x1,x2,y1,y2 = cx-w/2,cx+w/2,cy-h/2,cy+h/2
    l,a = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    l.addByTwoPoints(pt(x1+r,y2),pt(x2-r,y2)); l.addByTwoPoints(pt(x2,y2-r),pt(x2,y1+r))
    l.addByTwoPoints(pt(x2-r,y1),pt(x1+r,y1)); l.addByTwoPoints(pt(x1,y1+r),pt(x1,y2-r))
    a.addByCenterStartSweep(pt(x2-r,y2-r),pt(x2,y2-r),math.pi/2)
    a.addByCenterStartSweep(pt(x1+r,y2-r),pt(x1+r,y2),math.pi/2)
    a.addByCenterStartSweep(pt(x1+r,y1+r),pt(x1,y1+r),math.pi/2)
    a.addByCenterStartSweep(pt(x2-r,y1+r),pt(x2-r,y1),math.pi/2)

def extrude(comp, profiles, distance, operation, name):
    i = comp.features.extrudeFeatures.createInput(profiles, operation)
    i.setDistanceExtent(False, vi(distance))
    f = comp.features.extrudeFeatures.add(i); f.name = name
    return f

def circles(comp, plane, specs, name):
    sk = comp.sketches.add(plane); sk.name = name
    for x,y,d in specs: sk.sketchCurves.sketchCircles.addByCenterRadius(pt(x,y),mm(d/2))
    ps = adsk.core.ObjectCollection.create()
    for n in range(sk.profiles.count): ps.add(sk.profiles.item(n))
    return ps

def ring(comp, plane, cx, cy, od, id_, name):
    sk=comp.sketches.add(plane); sk.name=name
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx,cy),mm(od/2))
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx,cy),mm(id_/2))
    return min((sk.profiles.item(n) for n in range(sk.profiles.count)),key=lambda p:p.areaProperties().area)

def shot(app, number, slug, orient):
    vp=app.activeViewport; cam=vp.camera; cam.isSmoothTransition=False
    cam.viewOrientation=orient; cam.isFitView=True; vp.camera=cam; adsk.doEvents()
    if not vp.saveAsImageFile(os.path.join(SCREENSHOT_DIR,f"{number:02d}-{slug}.png"),1600,1000):
        raise RuntimeError("Screenshot failed")

def run(_context: str):
    os.makedirs(OUTPUT_DIR,exist_ok=True); os.makedirs(SCREENSHOT_DIR,exist_ok=True)
    app=adsk.core.Application.get(); doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design=adsk.fusion.Design.cast(app.activeProduct); design.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=design.rootComponent

    # Keep the imported STEP in its native location and build around it, preventing child-part drift.
    pcb=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); pcb.component.name="Pulse Halo PCB Assembly"
    app.importManager.importToTarget(app.importManager.createSTEPImportOptions(PCB_STEP),pcb.component); adsk.doEvents()
    b=pcb.boundingBox; cx=(b.minPoint.x+b.maxPoint.x)/2; cy=(b.minPoint.y+b.maxPoint.y)/2
    z0=b.minPoint.z-mm(7); floor=z0+mm(3); top=z0+mm(22)

    # 100 x 94 mm rounded pedestal and rubber-foot pockets make the enclosure genuinely stable.
    stand_occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); stand_occ.component.name="Wide Anti-Tip Desktop Pedestal"
    stand=stand_occ.component; pp=plane_at(stand,z0-mm(5),"Pedestal Bottom Plane")
    sk=stand.sketches.add(pp); sk.name="Rounded Pedestal Footprint"; rounded_rect(sk,cx,cy,mm(100),mm(94),mm(12))
    extrude(stand,sk.profiles.item(0),5,adsk.fusion.FeatureOperations.NewBodyFeatureOperation,"Five Millimeter Anti-Tip Pedestal")
    feet=[(cx-mm(39),cy-mm(36),12),(cx+mm(39),cy-mm(36),12),(cx+mm(39),cy+mm(36),12),(cx-mm(39),cy+mm(36),12)]
    extrude(stand,circles(stand,pp,feet,"Rubber Foot Pockets"),2,adsk.fusion.FeatureOperations.CutFeatureOperation,"Four Rubber Foot Recesses")

    # Rounded 86 x 80 mm shell with a 3 mm floor and 5 mm walls.
    bp=plane_at(root,z0,"Enclosure Bottom Plane"); sk=root.sketches.add(bp); sk.name="Rounded Enclosure Outline"
    rounded_rect(sk,cx,cy,mm(86),mm(80),mm(9))
    base=extrude(root,sk.profiles.item(0),22,adsk.fusion.FeatureOperations.NewBodyFeatureOperation,"Rounded Enclosure Shell")
    base.bodies.item(0).name="Rounded Electronics Housing"
    cp=plane_at(root,floor,"Three Millimeter Floor Plane"); sk=root.sketches.add(cp); sk.name="Rounded Electronics Cavity"
    rounded_rect(sk,cx,cy,mm(76),mm(70),mm(5))
    extrude(root,sk.profiles.item(0),19,adsk.fusion.FeatureOperations.CutFeatureOperation,"Hollow Rounded Electronics Cavity")

    supports=[(cx-mm(25),cy-mm(25),8),(cx+mm(25),cy-mm(25),8),(cx+mm(25),cy+mm(25),8),(cx-mm(25),cy+mm(25),8)]
    extrude(root,circles(root,cp,supports,"PCB Support Posts"),4,adsk.fusion.FeatureOperations.JoinFeatureOperation,"Four PCB Support Posts")

    # Wall-connected M3 heat-set insert towers with 4.2 mm x 7 mm pilot bores.
    inserts=[(cx-mm(34.5),cy-mm(31.5)),(cx+mm(34.5),cy-mm(31.5)),(cx+mm(34.5),cy+mm(31.5)),(cx-mm(34.5),cy+mm(31.5))]
    extrude(root,circles(root,cp,[(x,y,8) for x,y in inserts],"M3 Heat-Set Insert Bosses"),19,adsk.fusion.FeatureOperations.JoinFeatureOperation,"Four Reinforced Insert Towers")
    ip=plane_at(root,top-mm(7),"Heat-Set Insert Depth Plane")
    extrude(root,circles(root,ip,[(x,y,4.2) for x,y in inserts],"M3 Insert Pilot Holes"),7,adsk.fusion.FeatureOperations.CutFeatureOperation,"Seven Millimeter Heat-Set Insert Bores")

    # One rear cable notch; the bottom floor remains intact.
    sk=root.sketches.add(cp); sk.name="Single Rear Cable Exit"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(cx-mm(9),cy+mm(35)),pt(cx+mm(9),cy+mm(40)))
    extrude(root,sk.profiles.item(0),19,adsk.fusion.FeatureOperations.CutFeatureOperation,"Rear Cable Notch")

    # Separate rounded faceplate with M3 clearances, TFT window, controls, and halo bezel.
    lid_occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); lid_occ.component.name="Rounded Display Lid"
    lid=lid_occ.component; lp=plane_at(lid,top,"Lid Bottom Plane"); sk=lid.sketches.add(lp); sk.name="Rounded Lid Outline"
    rounded_rect(sk,cx,cy,mm(86),mm(80),mm(9))
    extrude(lid,sk.profiles.item(0),4,adsk.fusion.FeatureOperations.NewBodyFeatureOperation,"Four Millimeter Rounded Lid")
    extrude(lid,circles(lid,lp,[(cx,cy,45)],"Round TFT Window"),5,adsk.fusion.FeatureOperations.CutFeatureOperation,"Forty-Five Millimeter TFT Opening")
    holes=[(x,y,3.6) for x,y in inserts]+[(cx+mm(30),cy-mm(24),8),(cx-mm(30),cy-mm(25),2.2),(cx-mm(30),cy-mm(21),2.2),(cx-mm(30),cy-mm(17),2.2)]
    extrude(lid,circles(lid,lp,holes,"Controls and M3 Clearances"),5,adsk.fusion.FeatureOperations.CutFeatureOperation,"Controls and Four M3 Screw Clearances")
    tp=plane_at(lid,top+mm(4),"Lid Top Detail Plane")
    extrude(lid,ring(lid,tp,cx,cy,56,49,"Raised Halo Display Bezel"),1.2,adsk.fusion.FeatureOperations.JoinFeatureOperation,"Raised Halo Accent Ring")

    # Keep screenshots 1-9; replace only the final build and assembled views.
    lid_occ.isLightBulbOn=False; pcb.isLightBulbOn=True; stand_occ.isLightBulbOn=True
    shot(app,10,"desktop-stand",adsk.core.ViewOrientations.IsoTopRightViewOrientation)
    pcb.isLightBulbOn=False; lid_occ.isLightBulbOn=True
    shot(app,11,"complete-enclosure",adsk.core.ViewOrientations.IsoTopLeftViewOrientation)

    pcb.isLightBulbOn=True
    em=design.exportManager; f3d=os.path.join(OUTPUT_DIR,"Pulse-Halo-Enclosure.f3d"); step=os.path.join(OUTPUT_DIR,"Pulse-Halo-Enclosure.step")
    if not em.execute(em.createFusionArchiveExportOptions(f3d)): raise RuntimeError("F3D export failed")
    if not em.execute(em.createSTEPExportOptions(step,root)): raise RuntimeError("STEP export failed")
    print("Built the rounded Pulse Halo enclosure with M3 heat-set inserts and a stable pedestal")
