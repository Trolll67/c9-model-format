import os
import bpy
import bmesh
from mathutils import Vector
from bpy_extras import node_shader_utils, image_utils

from .binares_lib import BinaryReader


class TextureData():
	def __init__(self, diffuse=None, specular=None, normal=None):
		self.diffuse = diffuse
		self.specular = specular
		self.normal = normal
		
		self.USE_TEXTURE_NAME = False

class MeshData():
	def __init__(self, is_batch: bool=False):
		self.is_batch = is_batch
		self.numberVertices: int = 0
		self.numberIndices: int = 0
		self.verticesStart: int = 0
		self.indicesStart: int = 0

		self.verticesPositions: list[tuple[float, float, float]] = []
		self.verticesNormals: list[tuple[float, float, float]] = []
		self.verticesUVs: list[tuple[float, float]] = []
		self.indices: list[int] = []
		self.triangles: list[tuple[int, int, int]] = []

		self.mesh: bpy.types.Mesh = None
		self.object: bpy.types.Object = None
		self.texture_data: TextureData = None

	def indices_to_triangles(self):
		for m in range(0, len(self.indices), 3):
			self.triangles.append(self.indices[m:m+3])

	def findTextureFile(self, filepath: str):
		if filepath is None:
			return None
		
		dirname = os.path.dirname(filepath)
		filename = os.path.basename(filepath)
		files = os.listdir(dirname)
		for file in files:
			if file.lower() == filename.lower():
				return dirname + os.sep + file
			
		return None

	def addMaterial(self):
		mat_name = f'{self.name}_mat'

		# create material
		blend_mat = bpy.data.materials.new(name=mat_name)
		mat_wrap = node_shader_utils.PrincipledBSDFWrapper(blend_mat, is_readonly=False, use_nodes=True)
	
		if self.texture_data:
			# diffuse
			diffuse = self.findTextureFile(self.texture_data.diffuse) 
			if self.texture_data.diffuse is not None and diffuse is not None:
				mat_wrap.base_color_texture.image = image_utils.load_image(diffuse)
			# specular
			specular = self.findTextureFile(self.texture_data.specular)
			if self.texture_data.specular is not None and specular is not None:
				mat_wrap.specular_texture.image = image_utils.load_image(specular)
			# normal
			normal = self.findTextureFile(self.texture_data.normal)
			if self.texture_data.normal is not None and normal is not None:
				mat_wrap.normalmap_texture.image = image_utils.load_image(normal)

			# set material name
			if self.texture_data.USE_TEXTURE_NAME and diffuse is not None:
				mat_name = os.path.basename(diffuse).split('.')[0]
				blend_mat.name = f'{mat_name}__{self.name}_mat'

		# build material
		mat_wrap.update()

		nodes = blend_mat.node_tree.nodes

		# add uvmap
		texture_node = nodes.get('Image Texture')
		if texture_node is not None:
			uvmap_node = nodes.new('ShaderNodeUVMap')
			blend_mat.node_tree.links.new(texture_node.inputs['Vector'], uvmap_node.outputs['UV'])

		# setup emission
		node_principled = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
		if texture_node is not None:
			emission_input = node_principled.inputs.get('Emission')
			# support blender 4.0
			if emission_input is None:
				emission_input = node_principled.inputs.get('Emission Color')

			if emission_input is not None:
				blend_mat.node_tree.links.new(emission_input, texture_node.outputs['Color'])
			else:
				print('WARNING: Emission input not found')

		# add material to mesh
		self.mesh.materials.append(blend_mat)

	def addVertexUV(self): 
		# create new layer for UV coordinates
		uv_layer = self.mesh.uv_layers.new()
		bm = bmesh.new()
		bm.from_mesh(self.mesh)

		bm.faces.ensure_lookup_table()
		bm.loops.layers.uv.verify()

		uv_layer = bm.loops.layers.uv.active

		# set the UV coordinates of the loops
		for face in bm.faces:
			for loop in face.loops:
				loop[uv_layer].uv = Vector(self.verticesUVs[loop.vert.index])

		# Update the BMesh to the mesh
		bm.to_mesh(self.mesh)
		bm.free()

	def addMesh(self):
		self.mesh = bpy.data.meshes.new(self.name)
		self.mesh.from_pydata(self.verticesPositions, [], self.triangles)

		self.mesh.update(calc_edges=True)
		self.mesh.validate(verbose=not self.is_batch)

		# add to scene
		self.object = bpy.data.objects.new(self.name, self.mesh)
		bpy.context.collection.objects.link(self.object)

		# set name if empty
		if self.name == '':
			self.name = self.object.name

		# Select and make active
		bpy.context.view_layer.objects.active = self.object
		self.object.select_set(True)

		# Smooth shading
		bpy.ops.object.shade_smooth()

	def draw(self):
		# calculte triangles
		self.indices_to_triangles()
		# add mesh
		self.addMesh()
		# add vertex uv
		if len(self.triangles) > 0:	
			if len(self.verticesUVs) > 0:
				self.addVertexUV()
		# add material
		self.addMaterial()

class ImportR3M():
	def __init__(self, operator, mode: str):
		self.operator = operator
		self.last_error = None
		self.mode = mode
		self.SCALE_FACTOR: float = 0.01

	def log(self, message, type='INFO'):
		self.operator.report({type}, message)
		if type == 'ERROR':
			self.last_error = message
		else:
			self.last_error = None

	def print_log(self, message):
		if self.mode.upper() == 'DEBUG':
			print(message)

	def is_batch_mode(self) -> bool:
		return self.mode.upper() == 'BATCH'

	def get_active_space_view3d(self, context: bpy.types.Context) -> bpy.types.SpaceView3D:
		if context.space_data and context.space_data.type == 'VIEW_3D':
			space = context.space_data
			if isinstance(space, bpy.types.SpaceView3D):
				if space.type == 'VIEW_3D':
					return space

		for area in context.screen.areas:
			if isinstance(area, bpy.types.Area):
				if area.type == 'VIEW_3D':
					space = area.spaces.active
					if isinstance(space, bpy.types.SpaceView3D):
						if space.type == 'VIEW_3D':
							return space

		return None

	def enable_shading(self):
		space = self.get_active_space_view3d(bpy.context)
		if space:
			space.shading.type = 'MATERIAL'

	def get_specific_texture(self, base_name: str, tex_type: str) -> str:
		filename = base_name.split('.')[0]
		ext = base_name.split('.')[-1]
		filename = filename + tex_type + '.' + ext

		if os.path.exists(filename):
			return filename
		else:
			if not filename.endswith('_sp.' + ext) and not filename.endswith('_n.' + ext):
				print(f'\t[WARNING] Texture not found: {filename}')

			return None

	def group_meshes(self, meshes: list[MeshData], filename: str, combine_meshes: bool) -> bpy.types.Object:
		if len(meshes) == 0:
			return

		# combine meshes into one
		if combine_meshes:
			# deselect all objects
			bpy.ops.object.select_all(action='DESELECT')
			for mesh in meshes:
				mesh.object.select_set(True)
			# set active root object
			root_obj = meshes[0].object
			bpy.context.view_layer.objects.active = root_obj
			if len(meshes) > 1:
				# join meshes
				bpy.ops.object.join()
			# set name
			root_obj.name = filename
			# validate final mesh
			if root_obj.data.validate(verbose=not self.is_batch_mode()):
				self.print_log(f'Validated mesh: {root_obj.name}', 'INFO')

			return root_obj
		else:
			# create group object
			root_obj = bpy.data.objects.new(filename, None)
			bpy.context.collection.objects.link(root_obj)
			# set parent
			for mesh in meshes:
				mesh.object.parent = root_obj
			# set root parent to None
			root_obj.parent = None
			# validate meshes
			for child in root_obj.children:
				if child.type == 'MESH':
					if child.data.validate(verbose=not self.is_batch_mode()):
						self.print_log(f'Validated mesh: {child.name}', 'INFO')
				
			return root_obj
		
	def fix_transform(self, obj: bpy.types.Object):
		if not obj:
			return
		
		print(f'Fixing transform for {obj.name}')

		# select object and children
		obj.select_set(True)
		for child in obj.children:
			child.select_set(True)

		# scale down
		obj.scale *= self.SCALE_FACTOR		
		# rotate x 90
		obj.rotation_euler = (1.5708, 0, 0)
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

		# flip horizontal
		obj.scale.x = -1.0
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

	def flip_faces(self):
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.flip_normals()
		bpy.ops.object.mode_set(mode='OBJECT')

	def parse(self, filename: str, reader: BinaryReader, **kwargs):
		ret = {'FINISHED'}
		print(f'\nStart importing: {filename}')

		# parse arguments
		combine_meshes = kwargs.get('combine_meshes', True)
		self.SCALE_FACTOR = kwargs.get('scale', 0.01)

		# header 36 bytes
		flag = reader.read_int32()
		texture_count = reader.read_int32()
		unknown_1 = reader.read_int32()

		# bounding box
		min_x = reader.read_float32()
		min_y = reader.read_float32()
		min_z = reader.read_float32()
		box_min = (min_x, min_y, min_z)
		max_x = reader.read_float32()
		max_y = reader.read_float32()
		max_z = reader.read_float32()
		box_max = (max_x, max_y, max_z)

		# print header
		self.print_log(f'Header:')
		self.print_log(f'\tflag: {flag}')
		self.print_log(f'\ttexture_count: {texture_count}')
		self.print_log(f'\tunknown_1: {unknown_1}')
		self.print_log(f'\tbox_min: {box_min}')
		self.print_log(f'\tbox_max: {box_max}')

		offset = 1024 - reader.tell() # 1024 - 36 = 988 bytes
		unknown_2 = reader.read_unknown(offset)

		# get texture path
		prefs = bpy.context.preferences.addons[__package__].preferences
		texture_path = prefs.tex_filepath
	
		if texture_path is not None and os.path.exists(texture_path):
			texDir = texture_path
		else:
			texDir = reader.dirname().split('model')[0]+'texture'
			if os.path.exists(texDir) == False:
				texDir = os.path.join(reader.dirname(), 'texture')
				if os.path.exists(texDir) == False:
					texDir = reader.dirname()

		# 256 bytes for each texture
		textures: list[TextureData] = []
		self.print_log(f'\nTextures:')
		for i in range(texture_count):
			texture = TextureData()
			texture.USE_TEXTURE_NAME = True
			texture_name = reader.read_string(256)

			# get texture file name
			texture_name = os.path.basename(texture_name)

			# get texture path
			texture_path = os.path.join(texDir, texture_name)
			texture.diffuse = texture_path

			self.print_log(f'\tTexture {i}:')
			self.print_log(f'\t\tDiffuse: {texture_path}')

			# get specular texture
			specular_path = self.get_specific_texture(texture_path, '_sp')
			if specular_path is not None:
				texture.specular = specular_path
				self.print_log(f'\t\tSpecular: {specular_path}')

			# get normal texture
			normal_path = self.get_specific_texture(texture_path, '_n')
			if normal_path is not None:
				texture.normal = normal_path
				self.print_log(f'\t\tNormal: {normal_path}')

			textures.append(texture)

		# model data
		model_type = reader.read_int32()
		mesh_count = reader.read_int32()

		self.print_log(f'Model type: {model_type}')
		self.print_log(f'Meshes count: {mesh_count}')

		# meshes
		meshes: list[MeshData] = []
		numberVertices = reader.read_int32()
		numberIndices = reader.read_int32()

		self.print_log(f'Vertices: {numberVertices}')
		self.print_log(f'Indices: {numberIndices}')

		UV_FLIP = True

		print(f'Step 1: {reader.tell()}')
		# mesh header
		self.print_log(f'Meshes header:')
		for i in range(mesh_count):
			mesh = MeshData(self.is_batch_mode())
			mesh.numberVertices = reader.read_int32()
			mesh.numberIndices = reader.read_int32()
			mesh.verticesStart = reader.read_int32()
			mesh.indicesStart = reader.read_int32()
			mesh.texture_data = i < len(textures) and textures[i] or None
			meshes.append(mesh)

			self.print_log(f'\tMesh {i}: {mesh.numberVertices} vertices, {mesh.numberIndices} indices')

		# vertices
		verticesBuffer: list[float] = []
		for b in range(numberVertices):
			verticesBuffer.append(reader.read_float32())
			verticesBuffer.append(reader.read_float32())
			verticesBuffer.append(reader.read_float32())

		# normals
		normalsBuffer: list[float] = []
		for b in range(numberVertices):
			normalsBuffer.append(reader.read_float32())
			normalsBuffer.append(reader.read_float32())
			normalsBuffer.append(reader.read_float32())

		# uvs
		uvsBuffer: list[float] = []
		for b in range(numberVertices):
			u = reader.read_float32()
			v = reader.read_float32()
			uvsBuffer.append(u)
			uvsBuffer.append(-v if UV_FLIP else v)

		# unknown data
		reader.read_unknown(numberVertices*12)
		reader.read_unknown(numberVertices*12)

		# indices
		indicesBuffer: list[int] = []
		for b in range(numberIndices):
			indicesBuffer.append(reader.read_uint16())

		# unknown empty data 1284 bytes
		reader.read_unknown(1284) 

		# build meshes
		vBuff: list[float] = []
		nBuff: list[float] = []
		uBuff: list[float] = []
		iBuff: list[int] = []

		self.print_log('Building meshes...')

		for i in range(mesh_count):
			mesh = meshes[i]
			mesh.name = f'mesh_{i}'
			
			try:
				mesh.verticesPositions = [(verticesBuffer[j], verticesBuffer[j+1], verticesBuffer[j+2]) for j in range(mesh.verticesStart*3, mesh.verticesStart*3 + mesh.numberVertices*3, 3)]
				mesh.verticesNormals = [(normalsBuffer[j], normalsBuffer[j+1], normalsBuffer[j+2]) for j in range(mesh.verticesStart*3, mesh.verticesStart*3 + mesh.numberVertices*3, 3)]
				mesh.verticesUVs = [(uvsBuffer[j], uvsBuffer[j+1]) for j in range(mesh.verticesStart*2, mesh.verticesStart*2 + mesh.numberVertices*2, 2)]
				mesh.indices = indicesBuffer[mesh.indicesStart:mesh.indicesStart + mesh.numberIndices]
			except Exception as e:
				self.log(f'Error building mesh {i}: {e}', 'ERROR')
				self.print_log(f'Error building mesh {i}: {e}', 'ERROR')
				import traceback
				traceback.print_exc()
				continue

			mesh.draw()
			print(f'\tMesh {i} built: {mesh.name}')

		# clear meshes buffers data
		del vBuff
		del nBuff
		del uBuff
		del iBuff

		# summary
		remains = reader.remains()
		print(f'\nFile size: {reader.size()}')
		if remains > 0:
			self.print_log(f'\nSummary:')
			self.print_log(f'\tPosition: {reader.tell()}')
			self.print_log(f'\tSize: {reader.size()}')
			self.print_log(f'\tRemains: {remains} bytes')

		# group meshes
		group_obj = self.group_meshes(meshes, filename, combine_meshes)
		if not group_obj:
			self.log('Failed to group meshes!', 'ERROR')
			return {'CANCELLED'}
		
		# flip faces
		self.flip_faces()

		# fix scale and rotation
		if not self.is_batch_mode():
			self.fix_transform(group_obj)
		
		# select object
		if self.is_batch_mode():
			group_obj.select_set(True)
			bpy.context.view_layer.objects.active = group_obj

		# enable shading
		if not self.is_batch_mode():
			self.enable_shading()

		self.print_log(f'\nCompleted importing: {filename}.r3m file!')
		return ret


def log(operator, message, mode: str, type='INFO'):
	if mode.upper() != 'BATCH':
		operator.report({type}, message)

def load(operator, context, filepath="",
		 axis_forward='-Z',
		 axis_up='Y',
		 **kwargs
		):
    
	ret = {'FINISHED'}
	mode = kwargs.get('mode', 'DEBUG')
	log(operator, f'Importing R3M file: {filepath}', mode)

	basename = os.path.basename(filepath)
	filename, extension = os.path.splitext(basename)

	if extension == '.r3m':
		file = open(filepath, 'rb')
		reader = BinaryReader(file)         
		importer = ImportR3M(operator, mode)
		ret = importer.parse(filename, reader, **kwargs)
		file.close()

		if ret == {'FINISHED'}:
			log(operator, f'Imported R3M file: {filepath}', mode)
		else:
			if importer.last_error is not None:
				log(operator, f'Import R3M failed: {importer.last_error}', mode, 'ERROR')
			else:
				log(operator, f'Import R3M failed!', mode, 'ERROR')
	else:
		log(operator, f'Unsupported file extension: {extension}', mode, 'ERROR')
		ret = {'CANCELLED'}
	
	return ret