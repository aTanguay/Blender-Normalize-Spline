bl_info = {
    "name": "Normalized Spline",
    "author": "OpenAI",
    "version": (1, 0),
    "blender": (2, 91, 0),
    "location": "View3D > Right Click",
    "description": "Creates a normalized spline from the active curve",
    "warning": "",
    "doc_url": "",
    "category": "Add Curve",
}

#This variant works with the right click menu and hides the source

import bpy
import math
from mathutils import Vector

# Calculate the length of the spline segment
def calc_length(spline):
    wps = spline.bezier_points
    lengths = []
    for i in range(len(wps)-1):
        p0 = wps[i].co
        handle1 = wps[i].handle_right
        handle2 = wps[i+1].handle_left
        p3 = wps[i+1].co

        # 10,000 is the number of points to sample along the curve to estimate the length
        length = 0
        for j in range(10000):
            t = j / 10000
            p = (1-t)**3*p0 + 3*(1-t)**2*t*handle1 + 3*(1-t)*t**2*handle2 + t**3*p3
            if j > 0:
                length += (p - p_old).length
            p_old = p
        lengths.append(length)
    return lengths

# Function to get the coordinate at a t value on the bezier spline
def interpolate_bezier(t, p0, p1, p2, p3):
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3

# Function to create a new spline from points
def create_spline_from_points(points, name='new_spline', location=(0,0,0), bevel_depth=0.0):
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2
    curve_data.bevel_depth = bevel_depth

    polyline = curve_data.splines.new('BEZIER')
    polyline.bezier_points.add(len(points)-1)

    for i, point in enumerate(points):
        polyline.bezier_points[i].co = point
        polyline.bezier_points[i].handle_left_type = 'VECTOR'
        polyline.bezier_points[i].handle_right_type = 'VECTOR'

    curve_obj = bpy.data.objects.new(name, curve_data)
    curve_obj.location = location
    bpy.context.collection.objects.link(curve_obj)

class OBJECT_OT_normalized_spline(bpy.types.Operator):
    bl_idname = "object.normalized_spline"
    bl_label = "Create Normalized Spline"
    bl_options = {'REGISTER', 'UNDO'}

    length_divider: bpy.props.FloatProperty(
        name="Length Divider",
        description="Determines the spacing of the new points",
        default=10.0,
        min=0.001
    )

    def execute(self, context):
        obj = context.active_object
        if obj.type == 'CURVE':
            for i, spline in enumerate(obj.data.splines):
                lengths = calc_length(spline)

                # Create evenly spaced points along the length of the spline
                wps = spline.bezier_points
                points = []
                for l, length in enumerate(lengths):
                    # Number of points based on the length
                    number_of_points = max(2, math.ceil(length / self.length_divider))
                    for i in range(number_of_points):
                        t = i / (number_of_points - 1)
                        p0 = wps[l].co
                        p1 = wps[l].handle_right
                        p2 = wps[l+1].handle_left
                        p3 = wps[l+1].co
                        point = interpolate_bezier(t, p0, p1, p2, p3)
                        points.append(point)

                create_spline_from_points(points, name=f'new_spline_{i}', location=obj.location, bevel_depth=obj.data.bevel_depth)
            # Hide the original object in the viewport after creating the new splines
            obj.hide_viewport = True
        else:
            self.report({'WARNING'}, "Active object is not a curve!")
            return {'CANCELLED'}

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_normalized_spline.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_normalized_spline)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_normalized_spline)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)

if __name__ == "__main__":
    register()
