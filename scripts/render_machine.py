"""Run with Blender, not system Python. Procedural, independently editable machine."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT/'src/timing.json').read_text())
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x=C['width']; scene.render.resolution_y=C['height']; scene.render.resolution_percentage=100
scene.render.fps=C['fps']; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
sh=scene.display.shading
sh.light='STUDIO'; sh.studiolight_rotate_z=0.6; sh.color_type='MATERIAL'
sh.show_shadows=True; sh.show_cavity=True; sh.cavity_type='BOTH'; sh.curvature_ridge_factor=1.3; sh.curvature_valley_factor=1.1
sh.show_specular_highlight=True; sh.background_type='WORLD'
scene.display.render_aa='16'
scene.view_settings.view_transform='Standard'
def material(name,color,metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metallic; m.roughness=.25; return m
black=material('Graphite enamel',(.026,.032,.042),.7)
silver=material('Brushed silver',(.64,.69,.75),.85)
red=material('ACE red enamel',(.72,.008,.025),.65)
glass=material('Smoked front panel',(.04,.065,.085),.5)
white=material('Edge light',(.85,.9,1),.2)
root=bpy.data.objects.new('Machine rotation control',None); scene.collection.objects.link(root)
def box(name,loc,size,mat,parent=root,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,0)); o=bpy.context.object; o.name=name
    o.parent=parent; o.location=loc; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('Machined edges','BEVEL'); m.width=bevel; m.segments=3
        o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    return o
# Front points toward negative Y; cabinet has a visible red right-hand side.
box('Cabinet', (0,0,0), (2.1,.85,3.8),black,bevel=.14)
box('Red side shell',(1.055,.04,0),(.13,.78,3.66),red,bevel=.06)
box('Interior recess',(0,-.446,0),(1.83,.08,3.46),glass)
for z in [-.67,.12,.91]:
    box('Product shelf',(0,-.60,z-.28),(1.55,.37,.045),silver,bevel=.008)
    for i,x in enumerate([-.54,-.18,.18,.54]):
        box('Product carton',(x,-.57,z),(.23,.19,.39),[red,silver,black,silver][i],bevel=.022)
        box('Product label',(x,-.675,z+.02),(.15,.015,.11),white,bevel=.005)
box('Interior light',(-.85,-.54,.1),(.025,.025,2.82),white,bevel=.005)
hinge=bpy.data.objects.new('Door hinge control',None); scene.collection.objects.link(hinge); hinge.parent=root; hinge.location=(-1.04,-.5,0)
# Door aperture is actual open geometry, leaving the products visible.
for name,loc,size,mat in [
 ('Left frame',(.095,-.04,0),(.19,.18,3.7),silver),
 ('Right frame',(1.98,-.04,0),(.19,.18,3.7),silver),
 ('Top frame',(1.04,-.04,1.76),(1.8,.18,.2),silver),
 ('Door lower panel',(1.04,-.04,-1.3),(1.8,.18,1.02),black),
 ('Cross bar',(1.04,-.08,-.73),(1.8,.16,.12),silver),
 ('Control panel',(1.78,-.16,.1),(.22,.12,1.32),black),
 ('Payment display',(1.78,-.23,.48),(.14,.025,.22),red),
 ('Handle',(1.9,-.22,-.15),(.055,.1,.43),silver),
 ('Dispensing slot',(.99,-.15,-1.22),(1.1,.04,.3),glass),
 ('Slot lower lip',(.99,-.23,-1.38),(1.14,.18,.04),silver),
 ('Header red accent',(1.04,-.16,1.75),(1.34,.025,.025),red)]: box(name,loc,size,mat,hinge,.025)
for z in [.1,-.08]: box('Selection key',(1.78,-.24,z),(.11,.025,.06),silver,hinge,.01)
for x in [-.73,.73]: box('Recessed foot',(x,.06,-1.94),(.28,.48,.12),black)
bpy.ops.object.camera_add(location=(0,-10,1.05)); cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=4.9; scene.camera=cam
scene.world.color=(.08,.08,.08)
def smooth(v): return v*v*(3-2*v)
def progress(t,a,b): return max(0,min(1,(t-a)/(b-a)))
def pose(t):
    p=progress(t,C['door_close_start'],C['door_close_end'])
    # Ease gently into the heavy close, then a restrained latch settle.
    angle=-48*(1-smooth(p))
    if C['door_close_end'] <= t < C['rotation_start']:
        q=(t-C['door_close_end'])/(C['rotation_start']-C['door_close_end'])
        angle=-.8*math.sin(q*math.pi)*math.exp(-3*q)
    hinge.rotation_euler.z=math.radians(angle)
    r=smooth(progress(t,C['rotation_start'],C['rotation_end']))
    root.rotation_euler.z=math.radians(-8+188*r)
    root.location.z=0
scene.render.filepath=str(ROOT/'.build/machine/0000.png')
(ROOT/'.build/machine').mkdir(parents=True,exist_ok=True)
pose(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.build/ace-machine.blend'))
# Only render while machine contributes to the composite.
for i in range(math.ceil(C['handoff_end']*C['fps'])+1):
    pose(i/C['fps']); scene.render.filepath=str(ROOT/'.build/machine'/f'{i:04}.png'); bpy.ops.render.render(write_still=True)
