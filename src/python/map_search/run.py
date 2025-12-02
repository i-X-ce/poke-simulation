import os

from map_search import MapSearch
from utils import get_cd7c_index, get_cd7c_tile, search_tile

# 釣り検索
def fishing_search(tile_array):
    if search_tile(tile_array, 0x50, 0, get_cd7c_index(0xce59)):
        return False
    return search_tile(tile_array, 0x50, get_cd7c_index(0xce5a), get_cd7c_index(0xce64))

def fishing_get_tile(tile_array):
    return get_cd7c_tile(tile_array, 0xce59)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    map_search = MapSearch("../../ROM/pokemonGreen1.1.gb")
    map_search.draw_map_array(0x7b)
    hits = map_search.search_data(fishing_search, fishing_get_tile, print_info=False)
    for hit in hits:
        print(f"Fishing spot found at Map Coordinates: ({hit[0]}, {hit[1]}), Tile Data: {hit[2]}")