import csv
import datetime
import os

from map_search import MapSearch
from utils import get_cd7c_index, get_cd7c_tile, is_displayable_map, search_tile



def save_csv(hits, filename: str):
    print(f"Saving results to {filename}...")
    with open(filename, "w", newline="") as f:
        csv_writer = csv.DictWriter(f, fieldnames=["mapId", "Y", "X", "value"])
        csv_writer.writeheader()
        for hit in hits:
            csv_writer.writerow({
                "mapId": hit[0],
                "Y": hit[1],
                "X": hit[2],
                "value": hit[3],
            })
            # f.flush()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    map_search = MapSearch("../../ROM/pokemonBlue.gb")

    # 釣り検索
    def fishing_search(tile_array):
        if search_tile(tile_array, 0x50, 0, get_cd7c_index(0xce59)):
            return False
        return search_tile(tile_array, 0x50, get_cd7c_index(0xce5a), get_cd7c_index(0xce64))

    def fishing_get_tile(tile_array):
        return get_cd7c_tile(tile_array, 0xce59)

    hits = []
    for i in range(0x100):
        if not is_displayable_map(i):
            continue
        print(f"Searching map ID: {i:02X}...")
        map_search.draw_map_array(i)
        result = map_search.search_data(fishing_search, fishing_get_tile, print_info=False)
        if result:
            result = [(i, y, x, value) for (y, x, value) in result]
        hits += result
    save_csv(hits, f"fishing_map_search_results_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")

    # 新バグ検索
    def new_bug_search(tile_array):
        if search_tile(tile_array, 0x50, 0, get_cd7c_index(0xcde2)):
            return False
        return search_tile(tile_array, 0x50, get_cd7c_index(0xcde3), get_cd7c_index(0xce58))

    def new_bug_get_tile(tile_array):
        return get_cd7c_tile(tile_array, 0xcde2)
    
    hits = []
    for i in range(0x100):
        if not is_displayable_map(i):
            continue
        print(f"Searching map ID: {i:02X}...")
        map_search.draw_map_array(i)
        result = map_search.search_data(new_bug_search, new_bug_get_tile, print_info=False)
        if result:
            result = [(i, y, x, value) for (y, x, value) in result]
        hits += result
    save_csv(hits, f"new_bug_map_search_results_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
