import bpy
from mathutils import Vector

bl_info = {
    "name": "Lock Normals",
    "blender": (4, 5, 0),
    "version": (1, 1),
    'location': 'View 3D > Object',
    'category': '3D View',
    "author": "Starfelll",
    "url": "https://github.com/Starfelll/blender_lock_normals"
}


def _is_locked(custom_normal: bpy.types.Attribute):
    if custom_normal != None:
        if custom_normal.data_type == "FLOAT_VECTOR":
            if custom_normal.domain == "CORNER":
                return True
    return False


class OP_LockNormals(bpy.types.Operator):
    bl_idname = "starfelll.lock_normals"
    bl_label = "Lock Normals"
    bl_description = "禁用网格物体的法线自动计算，可以提高网格物体的场景性能"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        report_num = 0
        mesh_num = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            mesh: bpy.types.Mesh = obj.data
            mesh_num += 1

            attribute = mesh.attributes.get("custom_normal")
            if _is_locked(attribute):
                continue
            
            split_normals = []
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    normal = mesh.loops[loop_index].normal.copy()
                    split_normals.append(normal)
            
            if attribute != None:
                mesh.attributes.remove(attribute)

            attribute = mesh.attributes.new(
                name="custom_normal", 
                type="FLOAT_VECTOR",
                domain="CORNER"
            )
            for loop_index in range(len(split_normals)):
                attribute.data[loop_index].vector = split_normals[loop_index]
            
            report_num += 1

        self.report({'INFO'}, f"已锁定{report_num}/{mesh_num}个网格的法线")
        return {'FINISHED'}


class OP_UnlockNormals(bpy.types.Operator):
    bl_idname = "starfelll.unlock_normals"
    bl_label = "Unlock Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        report_num = 0
        mesh_num = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            mesh: bpy.types.Mesh = obj.data
            mesh_num += 1
            
            custom_normal = mesh.attributes.get("custom_normal")

            if not _is_locked(custom_normal):
                continue

            split_normals = []
            for data in custom_normal.data:
                normal = data.vector
                split_normals.append(Vector([normal[0], normal[1], normal[2]]))
            mesh.attributes.remove(custom_normal)
            mesh.normals_split_custom_set(split_normals)
            report_num += 1

        self.report({'INFO'}, f"已解锁{report_num}/{mesh_num}个网格的法线")
        return {'FINISHED'}


def draw_menu(this: bpy.types.Menu, context: bpy.types.Context):
    if context.active_object.type != "MESH":
        return
    this.layout.separator()
    mesh: bpy.types.Mesh = context.active_object.data
    if _is_locked(mesh.attributes.get("custom_normal")):
        this.layout.operator(OP_UnlockNormals.bl_idname, icon="UNLOCKED")
    else:
        this.layout.operator(OP_LockNormals.bl_idname, icon="LOCKED")

def register():
   bpy.utils.register_class(OP_LockNormals)
   bpy.utils.register_class(OP_UnlockNormals)
   bpy.types.VIEW3D_MT_object_context_menu.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_menu)
    bpy.utils.unregister_class(OP_LockNormals)
    bpy.utils.unregister_class(OP_UnlockNormals)

if __name__ == "__main__":
    register()
