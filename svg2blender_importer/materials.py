import bpy

def create_panel_material(name, size, image_front, image_back):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    
    node_tex_coord = nodes.new("ShaderNodeTexCoord")
    node_tex_coord.location = (0, 0)

    node_separate_xyz = nodes.new("ShaderNodeSeparateXYZ")
    node_separate_xyz.location = (200, 0)

    links.new(node_separate_xyz.inputs["Vector"], node_tex_coord.outputs["Object"])

    node_mapping = nodes.new("ShaderNodeMapping")
    node_mapping.location = (200, -200)
    node_mapping.inputs["Scale"].default_value[0] = 1000 / size[0]
    node_mapping.inputs["Scale"].default_value[1] = 1000 / size[1]

    links.new(node_mapping.inputs["Vector"], node_tex_coord.outputs["Object"])

    node_map_range = nodes.new("ShaderNodeMapRange")
    node_map_range.location = (400, 0)
    node_map_range.inputs["From Min"].default_value = -0.0001
    node_map_range.inputs["From Max"].default_value =  0.0001
    node_map_range.inputs["To Min"].default_value = 1
    node_map_range.inputs["To Max"].default_value = 0

    links.new(node_map_range.inputs["Value"], node_separate_xyz.outputs["Z"])

    node_texture_front = nodes.new("ShaderNodeTexImage")
    node_texture_front.location = (400, -300)
    node_texture_front.image = image_front
    node_texture_front.interpolation = "Cubic"

    links.new(node_texture_front.inputs["Vector"], node_mapping.outputs[0])

    node_texture_back = nodes.new("ShaderNodeTexImage")
    node_texture_back.location = (400, -600)
    node_texture_back.image = image_back
    node_texture_back.interpolation = "Cubic"

    links.new(node_texture_back.inputs["Vector"], node_mapping.outputs[0])

    node_mix_rgb = nodes.new("ShaderNodeMixRGB")
    node_mix_rgb.location = (700, 0)

    links.new(node_mix_rgb.inputs["Fac"], node_map_range.outputs[0])
    links.new(node_mix_rgb.inputs["Color1"], node_texture_front.outputs["Color"])
    links.new(node_mix_rgb.inputs["Color2"], node_texture_back.outputs["Color"])

    node_shader = nodes.new("ShaderNodeBsdfPrincipled")
    node_shader.location = (900, 0)
    node_shader.inputs["Metallic"].default_value = 1.0
    node_shader.inputs["Roughness"].default_value = 0.85

    links.new(node_shader.inputs["Base Color"], node_mix_rgb.outputs[0])

    node_output = nodes.new("ShaderNodeOutputMaterial")
    node_output.location = (1200, 0)

    links.new(node_output.inputs["Surface"], node_shader.outputs[0])

    return material
