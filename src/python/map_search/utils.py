def read_byte(rom_data: bytes, address: int) -> int:
    bank = (address & 0xFF0000) >> 16
    offset = address if bank == 0 else (address & 0x00FFFF - 0x4000)
    return rom_data[bank * 0x4000 + offset]

def read_word(rom_data: bytes, address: int) -> int:
    low_byte = read_byte(rom_data, address)
    high_byte = read_byte(rom_data, address + 1)
    return (high_byte << 8) | low_byte

def read_bytes(rom_data: bytes, address: int, length: int) -> bytes:
    bank = (address & 0xFF0000) >> 16
    offset = address if bank == 0 else (address & 0x00FFFF - 0x4000)
    start = bank * 0x4000 + offset
    return rom_data[start:start + length]

def join_bank_address(bank: int, address: int) -> int:
    return (bank << 16) | address

def bytes2word(data: bytes) -> int:
    return int.from_bytes(data, byteorder="little")

def get_cd7c_index(address: int):
    tile_map_backup2 = 0xcd7c
    return (address - tile_map_backup2)

def get_cd7c_tile(tile_array, address):
    tile_map_backup2 = 0xcd7c
    index = address - tile_map_backup2
    tile_array = tile_array.flatten()
    return tile_array[index]

def search_tile(tile_array, tile_id, start_index, end_index):
    """
    フラット化したタイル配列から、特定のタイルIDが存在するか検索する  
    start_indexから  
    end_indexは含まない
    """
    tile_array = tile_array.flatten()
    tile_array = tile_array[start_index:end_index]
    return tile_id in tile_array

def is_displayable_map(map_id):
    """表示可能なマップか判定する"""
    undisputable_map_ids = [
        0x0b, 0x69, 0x6a, 0x6b, 0x6d, 0x6e, 0x6f, 0x70, 
        0x72, 0x73, 0x74, 0x75, 0xe7, 0xed, 0xee, 0xf1, 
        0xf2, 0xf3, 0xf4, 0xf8, 0xf9, 0xfa, 0xfb, 0xfe, 
        0xff
    ]
    return not map_id in undisputable_map_ids

def is_normal_pokemon(pokemon_id):
    """通常のポケモンか判定する"""
    if pokemon_id >= 0xbf:
        return False
    abnormal_pokemon_ids =[
        0x00, 0x1f, 0x20, 0x32, 0x34, 0x38, 0x3d, 0x3e, 
        0x3f, 0x43, 0x44, 0x45, 0x4f, 0x50, 0x51, 0x56, 
        0x57, 0x5e, 0x5f, 0x73, 0x79, 0x7a, 0x7f, 0x86, 
        0x87, 0x89, 0x92, 0x9c, 0x9f, 0xa0, 0xa1, 0xa2, 
        0xac, 0xae, 0xaf, 0xb5, 0xb6, 0xb7, 
    ]
    return not pokemon_id in abnormal_pokemon_ids