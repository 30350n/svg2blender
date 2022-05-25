import bpy
from mathutils import Vector

from .custom_node_utils import setup_node_tree

M_TO_MM = 1e-3

def setup_panel_material(node_tree: bpy.types.NodeTree, size, image_front, image_back):
    node_tree.nodes.clear()
    
    nodes = {
        "tex_coord": ("ShaderNodeTexCoord", {"location": (-900, 0)}, {}),
        "separate_position": ("ShaderNodeSeparateXYZ", {"location": (-700, 0)},
            {"Vector": ("tex_coord", "Object")}),
        "is_bottom_layer": ("ShaderNodeMapRange", {"location": (-500, 0)}, {
            "From Min": -1e-4, "From Max": 1e-4, "To Min": 1.0, "To Max": 0.0,
            "Value": ("separate_position", "Z")}),

        "tex_coord_mapped": ("ShaderNodeMapping", {"location": (-700, -200)}, {
            "Scale": Vector((1.0 / size[0], 1.0 / size[1], 1.0)) / M_TO_MM,
            "Vector": ("tex_coord", "Object")}),
        "front": ("ShaderNodeTexImage",
            {"location": (-500, -300), "interpolation": "Cubic", "image": image_front},
            {"Vector": ("tex_coord_mapped", 0)}),
        "back":  ("ShaderNodeTexImage",
            {"location": (-500, -600), "interpolation": "Cubic", "image": image_back },
            {"Vector": ("tex_coord_mapped", 0)}),
        "color": ("ShaderNodeMixRGB", {"location": (-200, 0)}, {
            "Color1": ("front", "Color"), "Color2": ("back", "Color"),
            "Fac": ("is_bottom_layer", 0)}),

        "roughness": ("ShaderNodeMapRange", {"location": (-200, -200)},
            {"To Min": 0.65, "To Max": 0.85, "Value": ("color", 0)}),
        "bump": ("ShaderNodeBump", {"location": (-200, -480)},
            {"Strength": 0.2, "Distance": 1e-4, "Height": ("color", 0)}),
        "bevel": ("ShaderNodeBevel", {"location": (-200, -700)},
            {"Radius": 1e-4, "Normal": ("bump", 0)}),
        "shader": ("ShaderNodeBsdfPrincipled", {"location": (0, 0)}, {
            "Base Color": ("color", 0), "Roughness": ("roughness", 0), "Normal": ("bevel", 0),
            "Metallic": 1.0, "Clearcoat": 1.0, "Clearcoat Roughness": 0.6}),
        "output": ("ShaderNodeOutputMaterial", {"location": (300, 0)},
            {"Surface": ("shader", 0)}),
    }

    setup_node_tree(node_tree, nodes)
