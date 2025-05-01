import bpy
from bpy.props import StringProperty


class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    r3m_filepath: StringProperty(
        name="R3M Folder",
        subtype='FILE_PATH',
    )

    tex_filepath: StringProperty(
        name="R3M Texture Folder",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "r3m_filepath")
        layout.prop(self, "tex_filepath")