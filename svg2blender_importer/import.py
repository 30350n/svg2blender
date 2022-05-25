import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import *

import tempfile, random, shutil, struct
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from .materials import M_TO_MM, setup_panel_material

FRONT = "front.png"
BACK = "back.png"
CUTS = "cuts.svg"
SIZE = "size"

REQUIRED_MEMBERS = {FRONT, BACK, CUTS, SIZE}

class SVG2BLENDER_OT_import_fpnl(bpy.types.Operator, ImportHelper):
    """Import a front panel file"""
    bl_idname = "svg2blender.import_fpnl"
    bl_label = "Import .fpnl"
    bl_options = {"PRESET", "UNDO"}

    thickness:       FloatProperty(name="Panel Thickness (mm)", default=2.0, soft_min=0.0, soft_max=5.0)
    bevel_depth:     FloatProperty(name="Bevel Depth (mm)", default=0.05, soft_min=0.0, soft_max=0.25)
    setup_camera:    BoolProperty(name="Setup Orthographic Camera", default=True)

    filter_glob:     StringProperty(default="*.fpnl", options={"HIDDEN"})

    def execute(self, context):
        props = self.properties

        filepath = Path(props.filepath)

        if not filepath.is_file():
            return self.error(f"file \"{filepath}\" does not exist")

        dirname = filepath.name.replace(".", "_") + f"_{random.getrandbits(64)}"
        tempdir = Path(tempfile.gettempdir()) / "svg2blender_tmp" / dirname
        tempdir.mkdir(parents=True, exist_ok=True)

        try:
            with ZipFile(filepath) as file:
                names = set(file.namelist())
                if missing := REQUIRED_MEMBERS.difference(names):
                    return self.error(f"not a valid .fpnl file: missing {str(missing)[1:-1]}")

                try:
                    size = struct.unpack("!ff", file.read(SIZE))
                except struct.error:
                    return self.error("not a valid .fpnl file: size is corrupted")

                file.extract(FRONT, tempdir)
                file.extract(BACK, tempdir)
                file.extract(CUTS, tempdir)
        
        except BadZipFile:
            return self.error("not a valid .fpnl file: not a zip file")

        collections_before = set(bpy.data.collections)
        bpy.ops.import_curve.svg(filepath=str(tempdir / CUTS))
        svg_collection = set(bpy.data.collections).difference(collections_before).pop()

        image_front = bpy.data.images.load(str(tempdir / FRONT))
        image_front.pack()
        image_front.filepath = ""

        image_back  = bpy.data.images.load(str(tempdir / BACK))
        image_back.pack()
        image_back.filepath = ""

        shutil.rmtree(tempdir)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in svg_collection.objects:
            obj.select_set(True)
        
        panel_obj = svg_collection.objects[0]
        panel_curve = panel_obj.data
        panel_obj.name = panel_curve.name = filepath.name.rsplit(".", 1)[0]

        context.view_layer.objects.active = panel_obj
        bpy.ops.object.join()

        bpy.data.collections.remove(svg_collection)
        context.collection.objects.link(panel_obj)
        context.view_layer.objects.active = panel_obj

        dimensions = panel_obj.dimensions

        panel_curve.dimensions = "2D"
        panel_curve.fill_mode = "BOTH"
        panel_curve.extrude = props.thickness * 0.5 * M_TO_MM
        panel_curve.bevel_mode = "ROUND"
        panel_curve.bevel_depth = props.bevel_depth * M_TO_MM

        material = bpy.data.materials.new(panel_obj.name)
        material.use_nodes = True
        setup_panel_material(material.node_tree, size, image_front, image_back)
        panel_curve.materials.append(material)

        if self.setup_camera:
            camera = bpy.data.cameras.new(f"{panel_obj.name}_camera")
            camera_obj = bpy.data.objects.new(camera.name, camera)
            context.collection.objects.link(camera_obj)

            camera.type = "ORTHO"
            camera.ortho_scale = dimensions.y
            camera.display_size = 0.1
            camera.clip_start = 0.01

            camera_obj.location.x = dimensions.x * 0.5
            camera_obj.location.y = dimensions.y * 0.5
            camera_obj.location.z = 0.1
            camera_obj.parent = panel_obj

            context.scene.render.resolution_x = round(dimensions.x * 10000)
            context.scene.render.resolution_y = round(dimensions.y * 10000)
            context.scene.render.resolution_percentage = 250

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "thickness", slider=True)
        layout.prop(self, "bevel_depth", slider=True)
        layout.prop(self, "setup_camera")

    def error(self, msg):
        print(f"error: {msg}")
        self.report({"ERROR"}, msg)
        return {"CANCELLED"}

def menu_func_import_fpnl(self, context):
    self.layout.operator(SVG2BLENDER_OT_import_fpnl.bl_idname, text="Front Panel (.fpnl)")

operators = (SVG2BLENDER_OT_import_fpnl,)

def register():
    for operator in operators:
        bpy.utils.register_class(operator)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_fpnl)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_fpnl)

    for operator in reversed(operators):
        bpy.utils.unregister_class(operator)
