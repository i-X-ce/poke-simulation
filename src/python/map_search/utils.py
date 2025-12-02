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