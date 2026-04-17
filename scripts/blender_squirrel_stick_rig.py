import math
from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT_ROOT / "output" / "squirrel-blender-stick-rig-v3-visible-4s.mp4"
IMG_PATH = PROJECT_ROOT / "images" / "stills" / "character-squirrel-02.jpg"
CUTOUT_PATH = PROJECT_ROOT / "output" / "assets" / "character-squirrel-cutout.png"


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 48  # 4s at 12 fps for quick validation
    scene.render.fps = 12
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 8
        scene.eevee.taa_samples = 8

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(OUT_PATH)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def add_camera_and_light() -> None:
    scene = bpy.context.scene

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 6.8
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -8.0, 1.15)
    cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    scene.camera = cam_obj

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 4.0
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (0.0, -2.0, 6.0)
    sun_obj.rotation_euler = (math.radians(35), math.radians(0), math.radians(20))

    # Simple floor/backdrop.
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.02))
    floor = bpy.context.object
    floor.name = "Floor"
    mat = bpy.data.materials.new("FloorMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.74, 0.92, 0.75, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    floor.data.materials.append(mat)

    # Soft backdrop so the subject is clearly visible.
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 4.0, 2.2))
    back = bpy.context.object
    back.name = "Backdrop"
    back.rotation_euler = (math.radians(90), 0.0, 0.0)
    bmat = bpy.data.materials.new("BackdropMat")
    bmat.use_nodes = True
    bbsdf = bmat.node_tree.nodes["Principled BSDF"]
    bbsdf.inputs["Base Color"].default_value = (0.80, 0.93, 1.00, 1.0)
    bbsdf.inputs["Roughness"].default_value = 0.9
    back.data.materials.append(bmat)


def add_reference_image() -> None:
    if not IMG_PATH.exists():
        return
    img = bpy.data.images.load(str(IMG_PATH))
    ref = bpy.data.objects.new("SquirrelRef", None)
    ref.empty_display_type = "IMAGE"
    ref.data = img
    ref.empty_image_side = "FRONT"
    ref.location = (-2.2, 0.01, 1.05)
    ref.scale = (1.6, 1.6, 1.6)
    ref.show_in_front = True
    bpy.context.collection.objects.link(ref)


def add_squirrel_card(arm_obj: bpy.types.Object) -> bpy.types.Object | None:
    source = CUTOUT_PATH if CUTOUT_PATH.exists() else IMG_PATH
    if not source.exists():
        return None

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 1.0))
    card = bpy.context.object
    card.name = "SquirrelCard"
    card.scale = (1.45, 2.15, 1.0)
    card.rotation_euler = (math.radians(90), 0.0, 0.0)

    mat = bpy.data.materials.new("SquirrelCardMatV3")
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    mat.use_backface_culling = False
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transp = nodes.new("ShaderNodeBsdfTransparent")
    emiss = nodes.new("ShaderNodeEmission")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(source))
    tex.interpolation = "Smart"
    links.new(tex.outputs["Color"], emiss.inputs["Color"])
    emiss.inputs["Strength"].default_value = 1.2
    if "Alpha" in tex.outputs:
        links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix.inputs[1])
    links.new(emiss.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    card.data.materials.append(mat)
    card.show_in_front = True

    # Attach card to rig hips so it follows dance.
    card.parent = arm_obj
    card.parent_type = "BONE"
    card.parent_bone = "hips"
    card.location = (0.0, 0.08, 1.00)
    return card


def create_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("SquirrelRigData")
    arm_obj = bpy.data.objects.new("SquirrelRig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    arm_obj.show_in_front = True
    arm_data.display_type = "STICK"

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    eb = arm_data.edit_bones

    def bone(name, head, tail, parent=None, use_connect=False):
        b = eb.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = eb[parent]
            b.use_connect = use_connect
        return b

    bone("hips", (0.0, 0.0, 0.82), (0.0, 0.0, 1.14))
    bone("spine", (0.0, 0.0, 1.14), (0.0, 0.0, 1.48), parent="hips", use_connect=True)
    bone("head", (0.0, 0.0, 1.48), (0.0, 0.0, 1.84), parent="spine", use_connect=True)

    bone("upper_arm.L", (-0.04, 0.0, 1.42), (-0.34, 0.0, 1.32), parent="spine")
    bone("forearm.L", (-0.34, 0.0, 1.32), (-0.58, 0.0, 1.12), parent="upper_arm.L", use_connect=True)
    bone("upper_arm.R", (0.04, 0.0, 1.42), (0.34, 0.0, 1.32), parent="spine")
    bone("forearm.R", (0.34, 0.0, 1.32), (0.58, 0.0, 1.12), parent="upper_arm.R", use_connect=True)

    bone("thigh.L", (-0.10, 0.0, 0.82), (-0.16, 0.0, 0.46), parent="hips")
    bone("shin.L", (-0.16, 0.0, 0.46), (-0.10, 0.0, 0.09), parent="thigh.L", use_connect=True)
    bone("thigh.R", (0.10, 0.0, 0.82), (0.16, 0.0, 0.46), parent="hips")
    bone("shin.R", (0.16, 0.0, 0.46), (0.10, 0.0, 0.09), parent="thigh.R", use_connect=True)

    bone("tail.1", (0.06, 0.0, 0.96), (0.42, 0.0, 0.92), parent="hips")
    bone("tail.2", (0.42, 0.0, 0.92), (0.76, 0.0, 0.84), parent="tail.1", use_connect=True)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def create_stick_meshes(arm_obj: bpy.types.Object) -> None:
    rig_mat = bpy.data.materials.new("RigMat")
    rig_mat.use_nodes = True
    bsdf = rig_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.07, 0.07, 0.08, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5

    joint_mat = bpy.data.materials.new("JointMat")
    joint_mat.use_nodes = True
    jbsdf = joint_mat.node_tree.nodes["Principled BSDF"]
    jbsdf.inputs["Base Color"].default_value = (0.95, 0.53, 0.22, 1.0)
    jbsdf.inputs["Roughness"].default_value = 0.45

    for b in arm_obj.data.bones:
        length = max(0.06, float(b.length))

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.03,
            depth=length,
            location=(0, 0, 0),
        )
        seg = bpy.context.object
        seg.name = f"stick_{b.name}"
        seg.rotation_euler = (math.radians(90), 0, 0)  # align cylinder with bone local Y
        seg.parent = arm_obj
        seg.parent_type = "BONE"
        seg.parent_bone = b.name
        seg.location = (0, length * 0.5, 0)
        seg.data.materials.append(rig_mat)

        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0, 0, 0), segments=12, ring_count=6)
        joint = bpy.context.object
        joint.name = f"joint_{b.name}"
        joint.parent = arm_obj
        joint.parent_type = "BONE"
        joint.parent_bone = b.name
        joint.location = (0, 0, 0)
        joint.data.materials.append(joint_mat)


def animate(arm_obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")

    p = arm_obj.pose.bones
    for pb in p:
        pb.rotation_mode = "XYZ"

    scene = bpy.context.scene
    key_step = 3
    cycle = 48.0

    for f in range(scene.frame_start, scene.frame_end + 1, key_step):
        scene.frame_set(f)
        t = 2.0 * math.pi * ((f - 1) % cycle) / cycle

        # Smoother grounded groove.
        s = math.sin(t)
        c = math.cos(t)
        p["hips"].location = (0.13 * math.sin(t * 0.5), 0.0, 0.010 * math.sin(2.0 * t))
        p["hips"].rotation_euler = (0.0, 0.0, math.radians(4.0 * math.sin(2.0 * t)))
        p["spine"].rotation_euler = (0.0, 0.0, math.radians(10.0 * s))
        p["head"].rotation_euler = (0.0, 0.0, math.radians(8.0 * math.sin(t + 0.35)))

        p["upper_arm.L"].rotation_euler = (0.0, 0.0, math.radians(24.0 * s + 10.0 * c))
        p["forearm.L"].rotation_euler = (0.0, 0.0, math.radians(-15.0 + 14.0 * math.sin(t + 0.8)))
        p["upper_arm.R"].rotation_euler = (0.0, 0.0, math.radians(-24.0 * s - 10.0 * c))
        p["forearm.R"].rotation_euler = (0.0, 0.0, math.radians(15.0 - 14.0 * math.sin(t + 0.8)))

        p["thigh.L"].rotation_euler = (0.0, 0.0, math.radians(-12.0 * math.sin(t + math.pi)))
        p["shin.L"].rotation_euler = (0.0, 0.0, math.radians(8.0 + 10.0 * max(0.0, math.sin(t + math.pi * 0.55))))
        p["thigh.R"].rotation_euler = (0.0, 0.0, math.radians(12.0 * math.sin(t + math.pi)))
        p["shin.R"].rotation_euler = (0.0, 0.0, math.radians(-8.0 - 10.0 * max(0.0, math.sin(t + math.pi * 1.55))))

        p["tail.1"].rotation_euler = (0.0, 0.0, math.radians(16.0 * math.sin(t + 1.0)))
        p["tail.2"].rotation_euler = (0.0, 0.0, math.radians(12.0 * math.sin(t + 1.7)))

        for name in [
            "hips",
            "spine",
            "head",
            "upper_arm.L",
            "forearm.L",
            "upper_arm.R",
            "forearm.R",
            "thigh.L",
            "shin.L",
            "thigh.R",
            "shin.R",
            "tail.1",
            "tail.2",
        ]:
            p[name].keyframe_insert(data_path="rotation_euler", frame=f)
        p["hips"].keyframe_insert(data_path="location", frame=f)

    action = arm_obj.animation_data.action
    for fc in action.fcurves:
        c = fc.modifiers.new(type="CYCLES")
        c.mode_before = "REPEAT"
        c.mode_after = "REPEAT"

    bpy.ops.object.mode_set(mode="OBJECT")


def main() -> None:
    reset_scene()
    add_camera_and_light()
    add_reference_image()
    arm = create_armature()
    create_stick_meshes(arm)
    add_squirrel_card(arm)
    animate(arm)
    bpy.context.scene.frame_set(1)
    bpy.ops.render.render(animation=True)
    print(f"Rendered: {OUT_PATH}")


if __name__ == "__main__":
    main()
