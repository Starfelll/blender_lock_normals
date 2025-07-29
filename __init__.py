import bpy
from mathutils import Vector

bl_info = {
    "name": "Lock Normals",
    "blender": (4, 5, 0),
    "version": (1, 2),
    'location': 'Mesh > Normals',
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


def _set_normals_lock(context: bpy.types.Context, is_lock: bool, op: bpy.types.Operator):
        report_num = 0
        mesh_num = 0
        init_mode = context.mode
        if init_mode == "EDIT_MESH":
            init_mode = "EDIT"
        bpy.ops.object.mode_set(mode="OBJECT")
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            mesh: bpy.types.Mesh = obj.data
            mesh_num += 1

            custom_normal = mesh.attributes.get("custom_normal")
            split_normals = []

            if _is_locked(custom_normal) == is_lock:
                continue

            if is_lock:
                if custom_normal == None and op.only_custom_normal:
                    continue
                    
                for poly in mesh.polygons:
                    for loop_index in poly.loop_indices:
                        split_normals.append(mesh.loops[loop_index].normal.copy())
                
                if custom_normal != None:
                    mesh.attributes.remove(custom_normal)

                custom_normal = mesh.attributes.new(
                    name="custom_normal", 
                    type="FLOAT_VECTOR",
                    domain="CORNER"
                )
                for loop_index in range(len(split_normals)):
                    custom_normal.data[loop_index].vector = split_normals[loop_index]
            else:
                for data in custom_normal.data:
                    normal = data.vector
                    split_normals.append(Vector([normal[0], normal[1], normal[2]]))
                mesh.attributes.remove(custom_normal)
                mesh.normals_split_custom_set(split_normals)
        
            report_num += 1

        bpy.ops.object.mode_set(mode=init_mode)
        if is_lock:
            op.report({'INFO'}, f"Normals locked for {report_num}/{mesh_num} meshes.")
        else:
            op.report({'INFO'}, f"Normals unlocked for {report_num}/{mesh_num} meshes.")
        return {'FINISHED'}


class OP_LockNormals(bpy.types.Operator):
    bl_idname = "starfelll.lock_normals"
    bl_label = "Lock Normals"
    bl_options = {'REGISTER', 'UNDO'}

    only_custom_normal: bpy.props.BoolProperty(name="only custom normal", default=True)

    def execute(self, context: bpy.types.Context):
        return _set_normals_lock(context, True, self)


class OP_UnlockNormals(bpy.types.Operator):
    bl_idname = "starfelll.unlock_normals"
    bl_label = "Unlock Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        return _set_normals_lock(context, False, self)


class OP_BatchClearCustomNormals(bpy.types.Operator):
    bl_idname = "starfelll.batch_clear_custom_normals"
    bl_label = "Clear Custom Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            custom_normal = obj.data.attributes.get("custom_normal")
            if custom_normal:
                obj.data.attributes.remove(custom_normal)

        return {'FINISHED'}
    

class OP_StripUselessCustomNormals(bpy.types.Operator):
    bl_idname = "starfelll.strip_useless_custom_normals"
    bl_label = "Strip Useless Custom Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def _test(self, mesh: bpy.types.Mesh, custom_normals):
        i = 0
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                n1: Vector = mesh.loops[loop_index].normal
                n2: Vector = custom_normals[i]
                if n1 != n2:
                    return False
                i += 1
        return True

    def execute(self, context: bpy.types.Context):
        num_mesh_has_custom_normal = 0
        num_optimized = 0

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            mesh: bpy.types.Mesh = obj.data

            custom_normal = mesh.attributes.get("custom_normal")
            if custom_normal is None:
                continue

            num_mesh_has_custom_normal += 1
            
            custom_normals = []
            obj.update_from_editmode()
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    custom_normals.append(mesh.loops[loop_index].normal.copy())

            custom_normal.name = "####"
            with context.temp_override(active_object=obj, object=obj, selected_objects=[obj]):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
                obj.update_from_editmode()
            
            if self._test(mesh, custom_normals):
                num_optimized += 1
                mesh.attributes.remove(custom_normal)
                custom_normal = None
                print(f"Clear custom normals for: {obj.name}")
            else:
                custom_normal.name = "custom_normal"
            obj.update_from_editmode()

        self.report({"INFO"}, f"{num_optimized}/{num_mesh_has_custom_normal} Mesh.")

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

    this.layout.operator(OP_StripUselessCustomNormals.bl_idname)
    this.layout.operator(OP_BatchClearCustomNormals.bl_idname)


def register():
   bpy.utils.register_class(OP_LockNormals)
   bpy.utils.register_class(OP_UnlockNormals)
   bpy.utils.register_class(OP_BatchClearCustomNormals)
   bpy.utils.register_class(OP_StripUselessCustomNormals)
   bpy.types.VIEW3D_MT_edit_mesh_normals.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_normals.remove(draw_menu)
    bpy.utils.unregister_class(OP_LockNormals)
    bpy.utils.unregister_class(OP_UnlockNormals)
    bpy.utils.unregister_class(OP_BatchClearCustomNormals)
    bpy.utils.unregister_class(OP_StripUselessCustomNormals)

if __name__ == "__main__":
    register()
