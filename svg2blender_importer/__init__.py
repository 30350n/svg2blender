bl_info = {
	"name": "svg2blender importer",
	"description": "Enables Blender to import .fpnl files, exported from Inkscape.",
	"author": "Bobbe",
	"version": (1, 0, 0),
	"blender": (2, 93, 0),
	"location": "File > Import",
	"category": "Import-Export",
	"support": "COMMUNITY",
	"wiki_url": "https://github.com/30350n/svg2blender",
}

import bpy
import importlib

module_names = ("import",)

modules = []
for module_name in module_names:
	if module_name in locals():
		modules.append(importlib.reload(locals()[module_name]))
	else:
		modules.append(importlib.import_module("." + module_name, package=__package__))

def register():
	for module in modules:
		module.register()

def unregister():
	for module in modules:
		module.unregister()
