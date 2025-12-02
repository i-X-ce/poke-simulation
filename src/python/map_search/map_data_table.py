# -----
# ROMごとのデータアドレスを管理するテーブル
# -----

from abc import ABCMeta, abstractmethod


class MapDataTable(metaclass=ABCMeta):
    @property
    @abstractmethod
    def map_header_banks(self) -> int:
        """マップバンクのアドレスを返す"""
        pass

    @property
    @abstractmethod
    def map_header_pointers(self) -> int:
        """マップヘッダポインタのアドレスを返す"""
        pass

    @property
    @abstractmethod
    def tile_sets(self) -> int:
        """タイルセットのアドレスを返す"""
        pass

    @property
    @abstractmethod
    def sprite_sheet_pointers(self) -> int:
        """スプライトシートポインタのアドレスを返す"""
        pass


class R0MapDataTable(MapDataTable):
    def __init__(self):
        self.map_header_banks_addr = 0x034883
        self.map_header_pointers_addr = 0x001bcb
        self.tile_sets_addr = 0x034df7
        self.sprite_sheet_pointers_addr = 0x057b0c

    @property
    def map_header_banks(self) -> int:
        return self.map_header_banks_addr

    @property
    def map_header_pointers(self) -> int:
        return self.map_header_pointers_addr

    @property
    def tile_sets(self) -> int:
        return self.tile_sets_addr

    @property
    def sprite_sheet_pointers(self) -> int:
        return self.sprite_sheet_pointers_addr

class R1MapDataTable(MapDataTable):
    def __init__(self):
        self.map_header_banks_addr = 0x034883
        self.map_header_pointers_addr = 0x001bb9
        self.tile_sets_addr = 0x034df7
        self.sprite_sheet_pointers_addr = 0x057b0c

    @property
    def map_header_banks(self) -> int:
        return self.map_header_banks_addr

    @property
    def map_header_pointers(self) -> int:
        return self.map_header_pointers_addr

    @property
    def tile_sets(self) -> int:
        return self.tile_sets_addr

    @property
    def sprite_sheet_pointers(self) -> int:
        return self.sprite_sheet_pointers_addr
    
class G0MapDataTable(MapDataTable):
    def __init__(self):
        self.map_header_banks_addr = 0x034883
        self.map_header_pointers_addr = 0x001bcb
        self.tile_sets_addr = 0x034df7
        self.sprite_sheet_pointers_addr = 0x057b0c

    @property
    def map_header_banks(self) -> int:
        return self.map_header_banks_addr

    @property
    def map_header_pointers(self) -> int:
        return self.map_header_pointers_addr

    @property
    def tile_sets(self) -> int:
        return self.tile_sets_addr

    @property
    def sprite_sheet_pointers(self) -> int:
        return self.sprite_sheet_pointers_addr

class G1MapDataTable(MapDataTable):
    def __init__(self):
        self.map_header_banks_addr = 0x034883
        self.map_header_pointers_addr = 0x001bb9
        self.tile_sets_addr = 0x034df7
        self.sprite_sheet_pointers_addr = 0x057b0c

    @property
    def map_header_banks(self) -> int:
        return self.map_header_banks_addr

    @property
    def map_header_pointers(self) -> int:
        return self.map_header_pointers_addr

    @property
    def tile_sets(self) -> int:
        return self.tile_sets_addr

    @property
    def sprite_sheet_pointers(self) -> int:
        return self.sprite_sheet_pointers_addr
    
class BMapDataTable(MapDataTable):
    def __init__(self):
        self.map_header_banks_addr = 0x034275
        self.map_header_pointers_addr = 0x000167
        self.tile_sets_addr = 0x0347e9
        self.sprite_sheet_pointers_addr = 0x057b27

    @property
    def map_header_banks(self) -> int:
        return self.map_header_banks_addr

    @property
    def map_header_pointers(self) -> int:
        return self.map_header_pointers_addr

    @property
    def tile_sets(self) -> int:
        return self.tile_sets_addr

    @property
    def sprite_sheet_pointers(self) -> int:
        return self.sprite_sheet_pointers_addr
