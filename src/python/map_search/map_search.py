import math

import numpy as np
from map_data_table import BMapDataTable, G0MapDataTable, G1MapDataTable, R0MapDataTable, R1MapDataTable
from utils import bytes2word, join_bank_address, read_byte, read_bytes, read_word
from rom_version import RomVersion, get_rom_version


class MapSearch:
    OVER_WORLD_MAP_ADDR = 0xc6e8

    def __init__(self, path: str):
        try: 
            with open(path, "rb") as f:
                self.rom_data = f.read()
                self.rom_version = get_rom_version(self.rom_data)
                if self.rom_version == RomVersion.R0:
                    self.map_data_table = R0MapDataTable()
                elif self.rom_version == RomVersion.R1:
                    self.map_data_table = R1MapDataTable()
                elif self.rom_version == RomVersion.G0:
                    self.map_data_table = G0MapDataTable()
                elif self.rom_version == RomVersion.G1:
                    self.map_data_table = G1MapDataTable()
                elif self.rom_version == RomVersion.B:
                    self.map_data_table = BMapDataTable()
        except FileNotFoundError:
            raise FileNotFoundError(f"ROM file not found at path: {path}")

    
    def draw_map_array(self, map_id: int, print_info: bool = False):
        """指定されたマップIDのマップ配列を描画する"""
        map_bank = read_byte(self.rom_data, self.map_data_table.map_header_banks + map_id)
        map_header = join_bank_address(map_bank, read_word(self.rom_data, self.map_data_table.map_header_pointers + map_id * 2))

        # データの読み込み
        map_tile_set = read_byte(self.rom_data, map_header)
        map_header += 1
        map_height = read_byte(self.rom_data, map_header)
        map_header += 1
        map_width = read_byte(self.rom_data, map_header)
        map_header += 1
        map_data_pointer = join_bank_address(map_bank, read_word(self.rom_data, map_header))
        map_header += 2
        map_text_pointer = join_bank_address(map_bank, read_word(self.rom_data, map_header))
        map_header += 2
        map_script_pointer = join_bank_address(map_bank, read_word(self.rom_data, map_header))
        map_header += 2
        map_connections = read_byte(self.rom_data, map_header)
        map_header += 1

        if print_info:
            print(f"Map ID: {map_id}"
                f"\nHeader Address: {map_header:06X}"
                f"\nMap Bank: {map_bank:02X}"
                f"\nTile Set: {map_tile_set:02X}"
                f"\nDimensions: {map_width} x {map_height}"
                f"\nMap Data Pointer: {map_data_pointer:06X}"
                f"\nText Pointer: {map_text_pointer:06X}"
                f"\nScript Pointer: {map_script_pointer:06X}"
                f"\nConnections: {map_connections:02X}")

        # つながったマップデータの読み込み
        connection_maps = []
        for i in range(4):
            if map_connections & (1 << i):
                connection_data = read_bytes(self.rom_data, map_header, 11)
                connection_maps.append(ConnectionMapData(self, connection_data))
                map_header += 11
            else:
                connection_maps.append(None)

        # 背景タイルの読み込み
        object_data_pointer = join_bank_address(map_bank, read_word(self.rom_data, map_header))
        map_background_tile = read_byte(self.rom_data, object_data_pointer)
        object_data_pointer += 1

        map_offset = 3
        self.over_world_map_height = map_height + map_offset * 2
        self.over_world_map_width = map_width + map_offset * 2
        over_world_map = [[map_background_tile for _ in range(self.over_world_map_width)] for _ in range(self.over_world_map_height)]
        for y in range(map_height):
            for x in range(map_width):
                tile = read_byte(self.rom_data, map_data_pointer + y * map_width + x)
                over_world_map[y + map_offset][x + map_offset] = tile

        # 隣り合うマップの描画
        for i, connection_map in enumerate(connection_maps):
            if connection_map == None:
                continue
            diff = connection_map.strip_dest - MapSearch.OVER_WORLD_MAP_ADDR
            y = diff // self.over_world_map_width
            x = diff % self.over_world_map_width

            for ci in range(3):
                for cj in range(connection_map.strip_length):
                    if i >= 2:
                        over_world_map[y + ci][x + cj] = read_byte(self.rom_data, connection_map.strip_src + ci * connection_map.strip_length + cj)
                    else:
                        over_world_map[y + cj][x + ci] = read_byte(self.rom_data, connection_map.strip_src + cj * connection_map.strip_length + ci)

        tile_array = [[0 for _ in range(self.over_world_map_width * 4)] for _ in range(self.over_world_map_height * 4)]
        tile_sets_addr = self.map_data_table.tile_sets + map_tile_set * 12
        tile_bank = read_byte(self.rom_data, tile_sets_addr)
        tile_sets_addr += 1
        tile_block_pointer = join_bank_address(tile_bank, read_word(self.rom_data, tile_sets_addr))
        tile_sets_addr += 2

        for y in range(self.over_world_map_height):
            for x in range(self.over_world_map_width):
                block_id = over_world_map[y][x]
                block_addr = tile_block_pointer + block_id * 16
                for ty in range(4):
                    for tx in range(4):
                        tile_array[y * 4 + ty][x * 4 + tx] = read_byte(self.rom_data, block_addr + ty * 4 + tx)
    
        if print_info: 
            for i, row in enumerate(over_world_map):
                print(f"{MapSearch.OVER_WORLD_MAP_ADDR + i * self.over_world_map_width:06X} ", end="")
                for block in row:
                    print(f"{block:02X} ", end="")
                print()
            print(f"tile_array: {tile_array}")

        self.tile_array = np.array(tile_array)

    def search_data(self, search_func, get_tile_func, open_menu: bool=True, print_info: bool=False):
        """
        タイル配列から特定のデータを検索する  
        search_func: タイル配列のスライスを受け取り、条件に合致するかを返す関数  
        get_tile_func: タイル配列のスライスを受け取り、特定のタイルデータを返す関数  
        open_menu: メニューを開いているかどうか(メニューに被るタイルは7Fで埋める)
        """
        np.set_printoptions(linewidth=200, threshold=4000, formatter={'int':lambda x: f"{x:02X}"})
        hits = []
        for y in range(6, self.over_world_map_height * 4 - 18, 2):
            for x in range(6, self.over_world_map_width * 4 - 20, 2):
                slice_tile = self.tile_array[y:y + 18, x:x + 20].copy()
                if open_menu:
                    slice_tile[0:16, -8:] = 0x7f
                if search_func(slice_tile):
                    if print_info:
                        print(slice_tile)
                    my = (y - 6) // 2 
                    mx = (x - 6) // 2 
                    hits.append((mx, my, get_tile_func(slice_tile)))
        return hits



class ConnectionMapData:
    def __init__(self, map_search: MapSearch, data: bytes):
        self.map_id = data[0]
        self.map_bank = read_byte(map_search.rom_data, map_search.map_data_table.map_header_banks + self.map_id)

        self.strip_src = join_bank_address(self.map_bank, bytes2word(data[1:3])) # マップの読み込み元アドレス
        self.strip_dest = bytes2word(data[3:5]) # マップの書き込み先アドレス
        self.strip_length = data[5] 
        self.map_width = data[6]
        self.map_y_alignment = data[7]
        self.map_x_alignment = data[8]
        self.map_view_pointer = bytes2word(data[9:11])

    def __repr__(self):
        return (f"\n(Connected Map ID: {self.map_id:02X}, "
                f"\nStrip Src: {self.strip_src:06X}, "
                f"\nStrip Dest: {self.strip_dest:04X}, "
                f"\nStrip Length: {self.strip_length}, "
                f"\nMap Width: {self.map_width}, "
                f"\nY Alignment: {self.map_y_alignment}, "
                f"\nX Alignment: {self.map_x_alignment}, "
                f"\nMap View Pointer: {self.map_view_pointer:04X})")