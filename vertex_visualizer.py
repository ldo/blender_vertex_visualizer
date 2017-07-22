#+
# This Blender addon displays information about a mesh that
# can be useful in debugging mesh-construction code, namely
# the indexes of the vertices and attached edges and faces.
#-

import sys # debug
import types
import bpy
import bgl
import blf
from bpy_extras import \
    view3d_utils

bl_info = \
    {
        "name" : "Vertex Visualizer",
        "author" : "Lawrence D'Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 2),
        "blender" : (2, 7, 8),
        "location" : "View 3D > Object Mode > Properties Shelf",
        "description" :
            "Shows information about a mesh that can be useful in"
            " debugging mesh-construction code, namely the indexes"
            " of the vertices and attached edges and faces.",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Development",
    }

#+
# Useful stuff
#-

def gen_gl() :
    # Funny thing: the OpenGL specs document all routines and
    # constants *without* “gl” and “GL_” prefixes. It makes
    # sense to add these in a language that does not have
    # namespaces, like C. In Python, it does not. So this
    # routine takes apart the contents of the bgl module
    # into two separate modules, one (called “gl”) containing
    # all the routines and the other (called “GL”) containing
    # all the constants, with those unnecessary prefixes
    # stripped. So instead  of calling bgl.glClear(), say,
    # you can call gl.Clear(). And instead of referring to
    # bgl.GL_ACCUM, you can use GL.ACCUM instead.
    # Much more concise all round.
    gl = types.ModuleType("gl", doc = "OpenGL routines")
    GL = types.ModuleType("GL", doc = "OpenGL constants")
    glu = types.ModuleType("glu", doc = "OpenGL routines")
    for name in dir(bgl) :
        if name.startswith("glu") :
            setattr(glu, name[3:], getattr(bgl, name))
        elif name.startswith("gl") :
            setattr(gl, name[2:], getattr(bgl, name))
        elif name.startswith("GL_") :
            setattr(GL, name[3:], getattr(bgl, name))
        else :
            sys.stderr.write("ignoring bgl.%s\n" % name) # debug
        #end if
    #end for
    return \
        gl, GL, glu
#end gen_gl
gl, GL, glu = gen_gl()
del gen_gl # your work is done

#+
# The panel
#-

def draw_vertex_info(context) :
    obj = context.object
    if (
            context.area.type == "VIEW_3D"
        and
            context.mode == "OBJECT"
              # cannot keep track of edits in edit mode, so restrict to object mode
        and
            obj != None
        and
            type(obj.data) == bpy.types.Mesh
    ) :
        region = context.region
        view3d = context.space_data.region_3d
        pos_2d = lambda v : \
            view3d_utils.location_3d_to_region_2d(region, view3d, obj.matrix_world * v)
        mesh = obj.data
        font_id = 0
        dpi = 72
        gl.Enable(GL.BLEND)
        blf.size(font_id, 12, dpi)
        if context.window_manager.vertex_vis_show_faces :
            gl.Color4f(0.66, 0.75, 0.37, 1)
            for f in mesh.polygons :
                pos = pos_2d(f.center)
                blf.position(font_id, pos.x, pos.y, 0)
                blf.draw(font_id, "f%d" % f.index)
            #end for
        #end if
        if context.window_manager.vertex_vis_show_edges :
            gl.Color4f(0.25, 0.63, 0.75, 1)
            for e in mesh.edges :
                pos = pos_2d((mesh.vertices[e.vertices[0]].co + mesh.vertices[e.vertices[1]].co) / 2)
                blf.position(font_id, pos.x, pos.y, 0)
                blf.draw(font_id, "e%d" % e.index)
            #end for
        #end if
        if context.window_manager.vertex_vis_show_verts :
            gl.Color4f(0.56, 0.75, 0.56, 1)
            for v in mesh.vertices :
                pos = pos_2d(v.co)
                blf.position(font_id, pos.x, pos.y, 0)
                blf.draw(font_id, "v%d" % v.index)
            #end for
        #end if
        gl.Disable(GL.BLEND)
        gl.Color4f(0, 0, 0, 1)
    #end if
#end draw_vertex_info

class VertexVisControl(bpy.types.Operator) :
    bl_idname = "mesh.vertex_visualizer_control"
    bl_label = "Vertex Visualizer Control"
    bl_description = "Just a place to keep the custom viewport drawing callback"
    bl_space_type = "VIEW_3D"

    _draw_handler = None # keep ref to last-installed draw handler

    @property
    def displaying(self) :
        # only referenced in unused methods
        return \
            self._draw_handler != None
    #end displaying

    def install_draw_handler(self, context) :
        # only referenced in unused method
        type(self)._draw_handler = bpy.types.SpaceView3D.draw_handler_add \
          (
            draw_vertex_info, # func
            (context,), # args
            "WINDOW", # region type
            "POST_PIXEL" # event type
          )
        sys.stderr.write("Vertex Visualizer: draw handler installed.\n") # debug
    #end install_draw_handler

    @classmethod
    def uninstall_draw_handler(celf) :
        if celf._draw_handler != None :
            bpy.types.SpaceView3D.draw_handler_remove(celf._draw_handler, "WINDOW")
            celf._draw_handler = None
        #end if
        sys.stderr.write("Vertex Visualizer: draw handler uninstalled.\n") # debug
    #end uninstall_draw_handler

    @classmethod
    def poll(celf, context) :
        # unneeded?
        return \
            context.area.type == "VIEW_3D" and context.mode == "OBJECT"
    #end poll

    def draw(self, context) :
        # unused
        layout = self.layout
        box = layout.box()
        box.operator \
          (
            "mesh.vertex_visualizer_control",
            text = ("Display Vertex Info", "Hide Vertex Info")[self.displaying]
          )
    #end draw

    def execute(self, context) :
        # unused
        if not self.displaying :
            self.install_draw_handler(context)
        else :
            self.uninstall_draw_handler()
        #end if
        context.area.tag_redraw()
        return \
            {"FINISHED"}
    #end execute

#end VertexVisControl

def add_props(self, context) :
    the_col = self.layout.column(align = True) # gives a nicer grouping of my items
    the_col.label("Vertex Visualizer:")
    for propsuffix in ("verts", "edges", "faces") :
        the_col.prop \
          (
            context.window_manager,
            "vertex_vis_show_%s" % propsuffix,
            "Show %s" % propsuffix.title()
          )
    #end for
    if VertexVisControl._draw_handler == None :
        VertexVisControl._draw_handler = bpy.types.SpaceView3D.draw_handler_add \
          (
            draw_vertex_info, # func
            (context,), # args
            "WINDOW", # region type
            "POST_PIXEL" # event type
          )
        context.area.tag_redraw()
        sys.stderr.write("Vertex Visualizer: draw handler initially installed.\n") # debug
    #end if
#end add_props

def register():
    for propsuffix in ("verts", "edges", "faces") :
        propname = "vertex_vis_show_%s" % propsuffix
        setattr \
          (
            bpy.types.WindowManager,
            propname,
            bpy.props.BoolProperty(name = propname, default = False)
          )
    #end for
    bpy.utils.register_class(VertexVisControl)
    bpy.types.VIEW3D_PT_view3d_display.append(add_props)
#end register

def unregister() :
    bpy.types.VIEW3D_PT_view3d_display.remove(add_props)
    VertexVisControl.uninstall_draw_handler()
    bpy.utils.unregister_class(VertexVisControl)
    for propsuffix in ("verts", "edges", "faces") :
        try :
            delattr(bpy.types.WindowManager, "vertex_vis_show_%s" % propsuffix)
        except AttributeError :
            pass
        #end try
    #end for
#end unregister

if __name__ == "__main__" :
    register()
#end if
