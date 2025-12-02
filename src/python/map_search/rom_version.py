from enum import Enum, auto

from utils import read_byte, read_bytes


class RomVersion(Enum):
    R0 = auto()
    R1 = auto()
    G0 = auto()
    G1 = auto()
    B = auto()

def get_rom_version(rom_data: bytes) -> RomVersion:
    title = read_bytes(rom_data, 0x0134, 16)
    rom_version = read_byte(rom_data, 0x014c)

    if title.startswith(b"POKEMON RED"):
        if rom_version == 0x00:
            return RomVersion.R0
        elif rom_version == 0x01:
            return RomVersion.R1
        else:
            raise ValueError("Unknown ROM version")
    elif title.startswith(b"POKEMON GREEN"):
        if rom_version == 0x00:
            return RomVersion.G0
        elif rom_version == 0x01:
            return RomVersion.G1
        else:
            raise ValueError("Unknown ROM version")
    elif title.startswith(b"POKEMON BLUE"):
        return RomVersion.B
    else:
        raise ValueError("Unknown ROM version")