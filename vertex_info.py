#+
# This Blender addon displays information about a selected mesh vertex,
# which can be handy for debugging mesh-creation code, e.g. in another
# addon.
#-

import bpy

bl_info = \
    {
        "name" : "Vertex Info",
        "author" : "Lawrence D'Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 1),
        "blender" : (2, 7, 8),
        "location" : "View 3D > Edit Mode > Properties Shelf",
        "description" :
            "Shows some basic info about a selected mesh vertex--its index,"
            " and the indices of the polygons that contain it.",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Development",
    }

class DummyUpdater(bpy.types.Operator) :
    # needed because panel will not automatically be redrawn by Blender
    # when selection changes.
    bl_idname = "mesh.vertex_info_dummy_updater"
    bl_label = "Update"

    def execute(self, context) :
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return \
            {"FINISHED"}
    #end execute

#end DummyUpdater

class MeshInfoPanel(bpy.types.Panel) :
    bl_idname = "mesh.vertex_info"
    bl_label = "Vertex Info"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(celf, context) :
        obj = context.object
        return \
            (obj != None) and type(obj.data) == bpy.types.Mesh and context.mode == "EDIT_MESH"
    #end poll

    def draw(self, context) :
        obj = context.object
        layout = self.layout
        box = layout.box()
        msg1 = None
        msg2 = ""
        if (obj != None) and type(obj.data) == bpy.types.Mesh and context.mode == "EDIT_MESH" :
            mesh = obj.data
            selected = list(v.index for v in mesh.vertices if v.select)
            if len(selected) == 1 :
                selected = selected[0]
                in_polygons = list(p.index for p in mesh.polygons if selected in p.vertices)
                msg1 = "Vertex %d" % selected
                msg2 = \
                    (
                            "%s %s"
                        %
                            (
                                ("no", "polygon", "polygons")[min(len(in_polygons), 2)],
                                (
                                    lambda : "polygons",
                                    lambda : ", ".join("%d" % p for p in in_polygons)
                                )[len(in_polygons) != 0](),
                            )
                    )
            #end if
        #end if
        if msg1 == None :
            msg1 = "Select a single vertex."
        #end if
        box.label(msg1, icon = "INFO")
        box.label(msg2)
        box.operator("mesh.vertex_info_dummy_updater", text = "Refresh")
    #end draw

#end MeshInfoPanel

def register():
    bpy.utils.register_class(MeshInfoPanel)
    bpy.utils.register_class(DummyUpdater)
#end register

def unregister() :
    bpy.utils.unregister_class(DummyUpdater)
    bpy.utils.unregister_class(MeshInfoPanel)
#end unregister

if __name__ == "__main__" :
    register()
#end if
