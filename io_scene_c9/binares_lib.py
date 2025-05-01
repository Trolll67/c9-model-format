from io import BufferedReader, BufferedWriter
import struct
import os

	
class BinaryReader():
	"""General BinaryReader class"""
	def __init__(self, inputFile: BufferedReader):
		self.inputFile: BufferedReader = inputFile
		self.endian = '<'
		self.debug = False
		self.mode = self.inputFile.mode if hasattr(self.inputFile, 'mode') else None
				
	def dirname(self):
		return os.path.dirname(self.inputFile.name)
	
	def basename(self):
		return os.path.basename(self.inputFile.name).split('.')[0]
	
	def ext(self):
		return os.path.basename(self.inputFile.name).split('.')[-1]
		
	def print_log(self, message):
		if self.debug == True:
			print(message)

	def to_hex(self, data) -> str:
		return ' '.join(hex(x) for x in data)

	def size(self) -> int:
		back = self.inputFile.tell()
		self.inputFile.seek(0, 2)
		tell = self.inputFile.tell()
		self.inputFile.seek(back)
		return tell
			
	def tell(self) -> int:
		val = self.inputFile.tell()
		self.print_log(f'current offset is {val}')

		return val
	
	def remains(self) -> int:
		return self.size() - self.tell()
	
	def seek(self, offset: int, whence: int = 0):
		if self.mode != 'rb':
			return
		
		self.inputFile.seek(offset, whence)
		self.print_log(f'skip {offset} bytes')

	def read(self) -> bytes:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read()
		
		self.print_log(f'read {len(data)} bytes')
		return data

	def read_bool(self) -> bool:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(1)
		data = struct.unpack('?', data)[0]

		self.print_log(f'read bool: {data}')
		return data
	
	def read_int8(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(1)
		data = struct.unpack(self.endian+'b', data)[0]

		self.print_log(f'read int8: {data}')
		return data
	
	def read_uint8(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(1)
		data = struct.unpack(self.endian+'B', data)[0]

		self.print_log(f'read uint8: {data}')
		return data
	
	def read_int16(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(2)
		data = struct.unpack(self.endian+'h', data)[0]

		self.print_log(f'read int16: {data}')
		return data
	
	def read_uint16(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(2)
		data = struct.unpack(self.endian+'H', data)[0]

		self.print_log(f'read uint16: {data}')
		return data

	def read_int32(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(4)
		data = struct.unpack(self.endian+'i', data)[0]

		self.print_log(f'read int32: {data}')
		return data
	
	def read_uint32(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(4)
		data = struct.unpack(self.endian+'I', data)[0]

		self.print_log(f'read uint32: {data}')
		return data
	
	def read_int64(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(8)
		data = struct.unpack(self.endian+'q', data)[0]

		self.print_log(f'read int64: {data}')
		return data

	def read_uint64(self) -> int:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(8)
		data = struct.unpack(self.endian+'Q', data)[0]

		self.print_log(f'read uint64: {data}')
		return data
	
	def read_float32(self) -> float:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(4)
		data = struct.unpack(self.endian+'f', data)[0]

		self.print_log(f'read float32: {data}')
		return data
	
	def read_float64(self) -> float:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(8)
		data = struct.unpack(self.endian+'d', data)[0]

		self.print_log(f'read float64: {data}')
		return data
	
	def read_bytes(self, count) -> bytes:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(count)

		self.print_log(f'read bytes: {data}')
		return data
	
	def read_string(self, limit=1000) -> str:
		if self.mode != 'rb':
			return None
		
		completed = False
		data = ''
		for i in range(limit):
			char = struct.unpack('c', self.inputFile.read(1))[0]
			if char == b'\x00' or completed == True:
				completed = True
				continue # not break to set cursor to right position

			data += char.decode('utf-8', errors='ignore')

		self.print_log(f'read string: {data}')
		return data

	def read_matrix4x4(self) -> list[float]:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(16*4)
		data = struct.unpack(self.endian+16*'f', data)

		self.print_log(f'read matrix4x4: {data}')
		return list(data)
	
	def read_matrix3x4(self) -> list[float]:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(12*4)
		data = struct.unpack(self.endian+12*'f', data)

		self.print_log(f'read matrix3x4: {data}')
		return list(data)

	def read_unknown(self, count) -> bytes:
		if self.mode != 'rb':
			return None
		
		data = self.inputFile.read(count)

		self.print_log(f'read unknown {count} bytes')
		return data
		

class BinaryWriter():
	"""General BinaryWriter class"""
	def __init__(self, inputFile: BufferedWriter) -> None:
		self.inputFile: BufferedWriter = inputFile
		self.endian = '<'
		self.debug = False
		self.mode = self.inputFile.mode if hasattr(self.inputFile, 'mode') else 'wb'

	def dirname(self):
		return os.path.dirname(self.inputFile.name)
	
	def basename(self):
		return os.path.basename(self.inputFile.name).split('.')[0]
	
	def ext(self):
		return os.path.basename(self.inputFile.name).split('.')[-1]
	
	def print_log(self, message):
		if self.debug == True:
			print(message)

	def size(self) -> int:
		back = self.inputFile.tell()
		self.inputFile.seek(0, 2)
		tell = self.inputFile.tell()
		self.inputFile.seek(back)
		return tell
			
	def tell(self) -> int:
		val = self.inputFile.tell()
		self.print_log(f'current offset is {val}')

		return val
	
	def seek(self, offset: int, whence: int = 0):
		if self.mode != 'wb':
			return
		
		self.inputFile.seek(offset, whence)
		self.print_log(f'skip {offset} bytes')

	def write_bool(self, data: bool):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, bool)
		self.print_log(f'write bool: {data}')
		data = struct.pack('?', data)
		self.inputFile.write(data)

	def write_int8(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write int8: {data}')
		data = struct.pack(self.endian+'b', data)
		self.inputFile.write(data)

	def write_uint8(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write uint8: {data}')
		data = struct.pack(self.endian+'B', data)
		self.inputFile.write(data)

	def write_int16(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write int16: {data}')
		data = struct.pack(self.endian+'h', data)
		self.inputFile.write(data)

	def write_uint16(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write uint16: {data}')
		data = struct.pack(self.endian+'H', data)
		self.inputFile.write(data)

	def write_int32(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write int32: {data}')
		data = struct.pack(self.endian+'i', data)
		self.inputFile.write(data)

	def write_uint32(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write uint32: {data}')
		data = struct.pack(self.endian+'I', data)
		self.inputFile.write(data)

	def write_int64(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write int64: {data}')
		data = struct.pack(self.endian+'q', data)
		self.inputFile.write(data)
	
	def write_uint64(self, data: int):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, int)
		self.print_log(f'write uint64: {data}')
		data = struct.pack(self.endian+'Q', data)
		self.inputFile.write(data)

	def write_float32(self, data: float):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, float)
		self.print_log(f'write float32: {data}')
		data = struct.pack(self.endian+'f', data)
		self.inputFile.write(data)

	def write_float64(self, data: float):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, float)
		self.print_log(f'write float64: {data}')
		data = struct.pack(self.endian+'d', data)
		self.inputFile.write(data)

	def write_bytes(self, data: bytes):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, bytes)
		self.print_log(f'write bytes: {data}')
		self.inputFile.write(data)

	def write_string(self, data: str):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, str)
		self.print_log(f'write string: {data}')
		data = data.encode('utf-8')
		self.inputFile.write(data)

	def write_matrix4x4(self, data: list[float]):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, list)
		assert len(data) == 16
		self.print_log(f'write matrix4x4: {data}')
		data = struct.pack(self.endian+16*'f', *data)
		self.inputFile.write(data)

	def write_matrix3x4(self, data: list[float]):
		if self.mode != 'wb':
			return
		
		assert isinstance(data, list)
		assert len(data) == 12
		self.print_log(f'write matrix3x4: {data}')
		data = struct.pack(self.endian+12*'f', *data)
		self.inputFile.write(data)

	def write_unknown(self, count: int):
		if self.mode != 'wb':
			return
		
		self.print_log(f'write unknown {count} bytes')
		data = b'\x00' * count
		self.inputFile.write(data)