"""Utilitarios para ler e alterar dados da ROM do Fire Emblem 1 (NES, mapper MMC4).

Banco N (0-14) aparece em $8000-$BFFF; o banco 15 e fixo em $C000-$FFFF.
O arquivo .nes tem 16 bytes de cabecalho antes dos bancos de 16 KB.
"""

HEADER = 16
BANK = 0x4000


def file_offset(bank, addr):
    if bank == 15:
        assert 0xC000 <= addr <= 0xFFFF
        return HEADER + 15 * BANK + (addr - 0xC000)
    assert 0x8000 <= addr <= 0xBFFF
    return HEADER + bank * BANK + (addr - 0x8000)


class Rom:
    def __init__(self, path):
        self.data = bytearray(open(path, "rb").read())

    def read(self, bank, addr, n):
        o = file_offset(bank, addr)
        return bytes(self.data[o:o + n])

    def write(self, bank, addr, payload):
        o = file_offset(bank, addr)
        self.data[o:o + len(payload)] = bytes(payload)

    def word(self, bank, addr):
        b = self.read(bank, addr, 2)
        return b[0] | (b[1] << 8)

    def save(self, path):
        open(path, "wb").write(self.data)

    # ---- mapas (bancos 2 e 9; mapas 1-13 no banco 2, 14+ no banco 9)
    @staticmethod
    def map_bank(n):
        return (2, n) if n < 14 else (9, n - 13)

    def map_info(self, n):
        bank, k = self.map_bank(n)
        ptr = self.word(bank, 0x8000 + 2 * (k - 1))
        h, w, cx, cy = self.read(bank, ptr, 4)
        return dict(bank=bank, ptr=ptr, rows=h + 1, cols=w + 1, cam=(cx, cy), cells_addr=ptr + 4)

    def get_map(self, n):
        i = self.map_info(n)
        raw = self.read(i["bank"], i["cells_addr"], i["rows"] * i["cols"])
        return [list(raw[r * i["cols"]:(r + 1) * i["cols"]]) for r in range(i["rows"])]

    def set_map(self, n, grid, cam=None):
        i = self.map_info(n)
        assert len(grid) == i["rows"] and all(len(r) == i["cols"] for r in grid), \
            f"o mapa {n} tem {i['rows']}x{i['cols']}; recebi {len(grid)}x{len(grid[0])}"
        self.write(i["bank"], i["cells_addr"], [c for row in grid for c in row])
        if cam is not None:
            self.write(i["bank"], i["ptr"] + 2, cam)
