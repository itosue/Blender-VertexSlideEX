import bpy, bmesh, mathutils.bvhtree, bpy_extras.view3d_utils

bl_info = {
	'name' : "Vert Slide EX",
	'author' : "saidenka",
	'version' : (1, 0),
	'blender' : (2, 7, 8),
	'location' : "Mesh Edit Mode > Shift+V",
	'description' : "",
	'warning' : "",
	'wiki_url' : "",
	'tracker_url' : "",
	'category' : "Mesh"
}

class vert_slide_ex(bpy.types.Operator):
	bl_idname = 'transform.vert_slide_ex'
	bl_label = "Vertex Slide EX"
	bl_description = ""
	bl_options = {'REGISTER', 'UNDO'}
	
	mouse_region_position = [0, 0]
	
	@classmethod
	def poll(cls, context):
		try:
			ob = context.active_object
			if ob.type != 'MESH': return False
			if ob.mode != 'EDIT': return False
		except: return False
		return True
	
	def get_bvhtree(self, context):
		ob = context.active_object
		me = ob.data
		
		bm = bmesh.from_edit_mesh(me)
		
		selected_verts = [v for v in bm.verts if v.select]
		self.target_vert_index = selected_verts[0].index
		self.target_vert_pre_co = selected_verts[0].co.copy()
		
		verts_dict = {}
		for face in selected_verts[0].link_faces:
			for vert in face.verts:
				verts_dict[vert.index] = vert
		
		verts_list = []
		for key in sorted(verts_dict.keys()):
			co = ob.matrix_world * verts_dict[key].co
			verts_list.append(co[:])
		
		faces_list = []
		for face in selected_verts[0].link_faces:
			vert_indices = []
			for vert in face.verts:
				vert_indices.append(sorted(verts_dict.keys()).index(vert.index))
			faces_list.append(vert_indices)
		
		return mathutils.bvhtree.BVHTree.FromPolygons(verts_list, faces_list)
	
	def invoke(self, context, event):
		ob = context.active_object
		me = ob.data
		
		bm = bmesh.from_edit_mesh(me)
		selected_verts = [v for v in bm.verts if v.select]
		if len(selected_verts) != 1:
			self.report({'INFO'}, "CANCELLED")
			return {'CANCELLED'}
		
		self.bvhtree = self.get_bvhtree(context)
		
		context.area.header_text_set(text="Running \"Vertex Slide EX\"")
		context.window_manager.modal_handler_add(self)
		return {'RUNNING_MODAL'}
	
	def ray_cast(self, context):
		region = context.region
		rv3d = context.space_data.region_3d
		coord = self.mouse_region_position
		
		direction = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
		origin = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
		
		location, normal, index, distance = self.bvhtree.ray_cast(origin, direction)
		if location:
			self.move_target_vert(context, location)
		else:
			vert_co = context.active_object.matrix_world * self.target_vert_pre_co
			distance = (vert_co - origin).length
			co = origin + (direction * distance)
			location, normal, index, distance = self.bvhtree.find_nearest(co)
			if location: self.move_target_vert(context, location)
	
	def move_target_vert(self, context, new_co):
		ob = context.active_object
		me = ob.data
		bm = bmesh.from_edit_mesh(me)
		bm.verts.ensure_lookup_table()
		bm.verts[self.target_vert_index].co = ob.matrix_world.inverted() * new_co
		bmesh.update_edit_mesh(me)
	
	def modal(self, context, event):
		if event.type == 'MOUSEMOVE':
			self.mouse_region_position = (event.mouse_region_x, event.mouse_region_y)
			self.ray_cast(context)
			
		elif event.type == 'LEFTMOUSE':
			self.mouse_region_position = (event.mouse_region_x, event.mouse_region_y)
			self.ray_cast(context)
			
			context.area.header_text_set()
			return {'FINISHED'}
			
		elif event.type in {'RIGHTMOUSE', 'ESC'}:
			self.move_target_vert(context, self.target_vert_pre_co)
			context.area.header_text_set()
			return {'CANCELLED'}
		
		return {'RUNNING_MODAL'}

addon_keymaps = []

def append_keymap_item():
	kc = bpy.context.window_manager.keyconfigs.addon
	if kc:
		km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
		kmi = km.keymap_items.new('transform.vert_slide_ex', 'V', 'PRESS', shift=True)
		addon_keymaps.append((km, kmi))

def remove_keymap_item():
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()

def register():
	bpy.utils.register_module(__name__)
	append_keymap_item()

def unregister():
	bpy.utils.unregister_module(__name__)
	remove_keymap_item()

if __name__ == '__main__':
	register()
