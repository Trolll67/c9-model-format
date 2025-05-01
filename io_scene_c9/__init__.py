# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# All trademarks mentioned in this software belong to their respective owners.
# The author of this application Trolll67 (https://github.com/Trolll67) does not claim ownership of these trademarks.
# All work done in this application is for educational purposes only.
# The author is not responsible for how this program may be used by others.


bl_info = {
    "name" : "C9 R3M/R3CM format",
    "author" : "Trolll67, https://github.com/Trolll67",
    "version" : (0, 1, 0),
    "blender" : (3, 6, 0),
    "location": "File > Import > C9 Formats",
    "description" : "R3M/R3CM IO meshes, UVs, textures",
    "warning" : "",
    "doc_url": "https://github.com/Trolll67/c9-model-format",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

from .prefs import Preferences

if "bpy" in locals():
    import importlib
    if "import_r3cm" in locals():
        importlib.reload(import_r3cm)
    if "import_r3m" in locals():
        importlib.reload(import_r3m)
else:
    from . import import_r3cm
    from . import import_r3m

import os
import bpy
from bpy.props import (
        EnumProperty,
        StringProperty,
        CollectionProperty,
        BoolProperty
        )
from bpy_extras.io_utils import (
        ImportHelper,
        orientation_helper,
        )


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportR3CM(bpy.types.Operator, ImportHelper):
    """Load a R3CM files"""
    bl_idname = "import_scene.c9_r3cm"
    bl_label = "Import R3CM (C9)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".r3cm"
    filter_glob: StringProperty(
            default="*.r3cm",
            options={'HIDDEN'},
            )
    
    files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )

    ui_tab: EnumProperty(
            items=(('MAIN', "Main", "Main basic settings"),
                   ('ARMATURE', "Armatures", "Armature-related settings"),
                   ),
            name="ui_tab",
            description="Import options categories",
            )
    
    mode: StringProperty(
            name="Mode", 
            default="DEBUG", 
            options={'HIDDEN'}
            )
    
    def draw(self, context):
        pass
    
    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "ui_tab", "filepath", "files"))

        from . import import_r3cm
        import os

        if self.files:
            ret = {'CANCELLED'}
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if import_r3cm.load(self, context, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return import_r3cm.load(self, context, filepath=self.filepath, **keywords)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportR3M(bpy.types.Operator, ImportHelper):
    """Load a R3M files"""
    bl_idname = "import_scene.c9_r3m"
    bl_label = "Import R3M (C9)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".r3m"
    filter_glob: StringProperty(
            default="*.r3m",
            options={'HIDDEN'},
            )
    
    files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )

    ui_tab: EnumProperty(
            items=(('MAIN', "Main", "Main basic settings"),
                   ('ARMATURE', "Armatures", "Armature-related settings"),
                   ),
            name="ui_tab",
            description="Import options categories",
            )
    
    mode: StringProperty(
            name="Mode", 
            default="DEBUG", 
            options={'HIDDEN'}
            )
    
    combine_meshes: BoolProperty(
            name="Combine Meshes",
            description="Combine object meshes into one mesh",
            default=True
            )
    
    scale: bpy.props.FloatProperty(
            name="Scale",
            description="Scale factor",
            default=0.01,
            )
    
    def draw(self, context):
        pass

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "ui_tab", "filepath", "files"))

        if self.files:
            ret = {'CANCELLED'}
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if import_r3m.load(self, context, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return import_r3m.load(self, context, filepath=self.filepath, **keywords)


class R3M_PT_import_transform(bpy.types.Panel):
    bl_label = "Transform"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = 'FILE_PT_operator'
    bl_idname = 'C9_R3M_PT_import_transform'

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_c9_r3m"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "combine_meshes")
        layout.prop(operator, "scale")


class BlenderMenu(bpy.types.Menu):
    bl_idname = 'C9_MT_formats_menu'
    bl_label = "Select"

    def draw(self, context):
        self.layout.operator(ImportR3CM.bl_idname, text='Import R3CM (.r3cm)')
        self.layout.operator(ImportR3M.bl_idname, text='Import R3M (.r3m)')

def blenderMenuDraw(self, context):
    self.layout.menu("C9_MT_formats_menu", text="C9 Formats")


classes = (
    BlenderMenu,
    ImportR3CM,
    ImportR3M, 
    Preferences,
    R3M_PT_import_transform
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(blenderMenuDraw)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(blenderMenuDraw)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()