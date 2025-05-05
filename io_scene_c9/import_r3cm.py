import os
import bpy
import bmesh
from mathutils import *
from bpy_extras import node_shader_utils, image_utils

from .binares_lib import BinaryReader


class TextureData():
	def __init__(self, diffuse=None, specular=None, normal=None):
		self.diffuse = diffuse
		self.specular = specular
		self.normal = normal
		self.USE_TEXTURE_NAME = True

class Mesh():
	def __init__(self):
		self.name: str = 'Mesh'
		self.numberVertices: int = 0
		self.numberIdices: int = 0
		self.vertices: list[tuple[float, float, float]] = []
		self.uv: list[tuple[float, float]] = []
		self.normals: list[tuple[float, float, float]] = []
		self.indices: list[int] = []
		self.triangles: list[tuple[int, int, int]] = []
		self.bone_indices: list[int] = []
		self.bone_weights: list[float] = []

		self.mesh: bpy.types.Mesh = None
		self.object: bpy.types.Object = None
		self.texture_data: TextureData = None

	def indices_to_triangles(self):
		for m in range(0, len(self.indices), 3):
			self.triangles.append(self.indices[m:m+3])

	def create(self):
		self.mesh = bpy.data.meshes.new(self.name)
		self.mesh.from_pydata(self.vertices, [], self.triangles)

		self.mesh.update(calc_edges=True)
		# self.mesh.validate(verbose=not self.is_batch)

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

	def add_uv(self): 
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
				loop[uv_layer].uv = Vector(self.uv[loop.vert.index])

		# update the BMesh to the mesh
		bm.to_mesh(self.mesh)
		bm.free()

	def find_texture_file(self, filepath: str):
		if filepath is None:
			return None
		
		dirname = os.path.dirname(filepath)
		filename = os.path.basename(filepath)
		files = os.listdir(dirname)
		for file in files:
			if file.lower() == filename.lower():
				return dirname + os.sep + file
			
		return None

	def add_material(self):
		mat_name = f'{self.name}_mat'

		# create material
		blend_mat = bpy.data.materials.new(name=mat_name)
		mat_wrap = node_shader_utils.PrincipledBSDFWrapper(blend_mat, is_readonly=False, use_nodes=True)
	
		if self.texture_data:
			# diffuse
			diffuse = self.find_texture_file(self.texture_data.diffuse) 
			if self.texture_data.diffuse is not None and diffuse is not None:
				mat_wrap.base_color_texture.image = image_utils.load_image(diffuse)
			# specular
			specular = self.find_texture_file(self.texture_data.specular)
			if self.texture_data.specular is not None and specular is not None:
				mat_wrap.specular_texture.image = image_utils.load_image(specular)
			# normal
			normal = self.find_texture_file(self.texture_data.normal)
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

	def draw(self):
		self.indices_to_triangles()
		self.create()

		# add vertex uv
		if len(self.triangles) > 0:	
			if len(self.uv) > 0:
				self.add_uv()
		
		# # add material
		self.add_material()

class ImportR3CM():
	def __init__(self, operator, mode, file_dirname=None):
		self.operator = operator
		self.last_error = None
		self.mode = mode
		self.file_dirname: str = file_dirname

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
	
	def parse(self, filename: str, reader: BinaryReader):	
		ret = {'FINISHED'}
		
		# header
		id = reader.read_string(limit=4)
		unk1 = reader.read_int32()
		unk2 = reader.read_int32()
		unk3 = reader.read_int32()
		unk4 = reader.read_float32()
		unk5 = reader.read_float32()
		unk6 = reader.read_float32()
		unk7 = reader.read_int32()

		# print header
		print('Header:')
		print(f'\tid: {id}')
		print(f'\tunk1: {unk1}')
		print(f'\tunk2: {unk2}')
		print(f'\tunk3: {unk3}')
		print(f'\tunk4: {unk4}')
		print(f'\tunk5: {unk5}')
		print(f'\tunk6: {unk6}')
		print(f'\tunk7: {unk7}')

		# data offset
		offset = 1024 - reader.tell()
		unk1 = reader.read_unknown(offset)

		# get texture path
		# prefs = bpy.context.preferences.addons[__package__].preferences
		# texture_path = prefs.tex_filepath
	
		texture_dir = os.path.join(self.file_dirname, 'textures')
		if not os.path.exists(texture_dir):
			texture_dir = self.file_dirname		

		# read textures
		textures: list[TextureData] = []
		print(f'\nTextures:')
		for i in range(1): # TODO: texture_count
			texture = TextureData()
			# texture.USE_TEXTURE_NAME = True
			texture_name = reader.read_string(256)

			# get texture file name
			texture_name = os.path.basename(texture_name)

			# get texture path
			texture_path = os.path.join(texture_dir, texture_name)
			texture.diffuse = texture_path

			print(f'\tTexture {i}:')
			print(f'\t\tDiffuse: {texture_path}')

			# get specular texture
			specular_path = self.get_specific_texture(texture_path, '_sp')
			if specular_path is not None:
				texture.specular = specular_path
				print(f'\t\tSpecular: {specular_path}')

			# get normal texture
			normal_path = self.get_specific_texture(texture_path, '_n')
			if normal_path is not None:
				texture.normal = normal_path
				print(f'\t\tNormal: {normal_path}')

			textures.append(texture)

		# read mesh
		mesh = Mesh()
		mesh.name = filename
		mesh.texture_data = textures[0]
		mesh.numberVertices = reader.read_int32()
		mesh.numberIdices = reader.read_int32()

		print(f'Vertices: {mesh.numberVertices}')
		print(f'Indices: {mesh.numberIdices}')

		# read vertices
		for i in range(mesh.numberVertices):
			x = reader.read_float32()
			y = reader.read_float32()
			z = reader.read_float32()
			mesh.vertices.append((x, y, z))

			uvx = reader.read_float32()
			uvy = reader.read_float32()
			mesh.uv.append((uvx, -uvy))

			nx = reader.read_float32()
			ny = reader.read_float32()
			nz = reader.read_float32()
			mesh.normals.append((nx, ny, nz))

			bone_idx_1 = reader.read_uint8()
			bone_idx_2 = reader.read_uint8()
			bone_idx_3 = reader.read_uint8()
			bone_idx_4 = reader.read_uint8()
			mesh.bone_indices.append((bone_idx_1, bone_idx_2, bone_idx_3, bone_idx_4))

			bone_weight_1: float = reader.read_uint8() / 255.0
			bone_weight_2: float = reader.read_uint8() / 255.0
			bone_weight_3: float = reader.read_uint8() / 255.0
			bone_weight_4: float = reader.read_uint8() / 255.0
			mesh.bone_weights.append((bone_weight_1, bone_weight_2, bone_weight_3, bone_weight_4))

		# read indices
		for i in range(mesh.numberIdices):
			mesh.indices.append(reader.read_uint16())

		mesh.draw()

		self.enable_shading()

		return ret

def log(operator, message, mode, type='INFO'):
	if mode.upper() != 'BATCH':
		operator.report({type}, message)

def load(operator, context, filepath="",
		axis_forward='-Z',
		axis_up='Y',
		**kwargs
		):
	
	ret = {'FINISHED'}
	mode = kwargs.get('mode', 'DEBUG')
	log(operator, f'Importing R3CM file: {filepath}', mode)
	
	basename = os.path.basename(filepath)
	filename, extension = os.path.splitext(basename)
	file_dirname = os.path.dirname(filepath)

	if extension == '.r3cm':
		file = open(filepath, 'rb')
		reader = BinaryReader(file)			
		importer = ImportR3CM(operator, mode, file_dirname)
		ret = importer.parse(filename, reader)
		file.close()

		if ret == {'FINISHED'}:
			log(operator, f'Import R3CM completed!', mode)
		else:
			if importer.last_error is not None:
				log(operator, f'Import R3CM failed: {importer.last_error}', mode, 'ERROR')
			else:
				log(operator, f'Import R3CM failed!', mode, 'ERROR')
	else:
		log(operator, f'Unsupported file extension: {extension}', mode, 'ERROR')
		ret = {'CANCELLED'}
	
	return ret