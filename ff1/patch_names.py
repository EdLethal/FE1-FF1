"""Teste 1 do lado FF1: troca nomes de classes e de inimigos por nomes do Fire Emblem.

Uso: python3 -I ff1/patch_names.py <FinalFantasy_USA.nes> <saida.nes>
So dados de texto sao alterados; nenhum codigo muda.
"""
import sys

HEADER = 16
BANK = 0x4000
TBL = {}
# tabela de texto do FF1: 80-89 = 0-9, 8A-A3 = A-Z, A4-BD = a-z (ver table_standard.tbl do disassembly)
for i in range(10):
    TBL[str(i)] = 0x80 + i
for i in range(26):
    TBL[chr(65 + i)] = 0x8A + i
    TBL[chr(97 + i)] = 0xA4 + i
TBL[" "] = 0xFF
TBL["."] = 0xC5
INV = {v: k for k, v in TBL.items()}


def enc(s):
    return bytes(TBL[c] for c in s)


def off(bank, addr):
    return HEADER + bank * BANK + (addr - 0x8000)


# classes: 12 entradas de 8 bytes (7 letras + $00) a partir de $BF43 no banco $0A
CLASS_NAMES = ["FIGHTER", "THIEF", "Bl.BELT", "RedMAGE", "Wh.MAGE", "Bl.MAGE",
               "KNIGHT", "NINJA", "MASTER", "RedWiz", "Wh.Wiz", "Bl.Wiz"]
NEW_CLASSES = {0: "LORD", 1: "PIRATE", 2: "HUNTER", 5: "MAGE"}

# inimigos: tabela de ponteiros em $94E0 (banco $0B), 128 entradas, textos terminados em $00
ENEMY_BASE = 0x94E0
ENEMY_SIZE = 1136
NEW_ENEMIES = {105: "GAZZAK", 0: "THIEF"}  # 105 = GARLAND


def main(src, dst):
    rom = bytearray(open(src, "rb").read())

    for idx, name in NEW_CLASSES.items():
        assert len(name) <= 7
        o = off(0x0A, 0xBF43) + idx * 8
        rom[o:o + 8] = enc(name.ljust(7)) + b"\x00"

    o = off(0x0B, ENEMY_BASE)
    blob = rom[o:o + ENEMY_SIZE]
    n = (blob[0] | blob[1] << 8) - ENEMY_BASE
    n //= 2
    names = []
    for i in range(n):
        p = (blob[2 * i] | blob[2 * i + 1] << 8) - ENEMY_BASE
        q = blob.index(0, p)
        names.append(bytes(blob[p:q]))
    for i, nm in NEW_ENEMIES.items():
        names[i] = enc(nm)
    out = bytearray(2 * n)
    ptrs = []
    for nm in names:
        ptrs.append(ENEMY_BASE + len(out))
        out += nm + b"\x00"
    for i, p in enumerate(ptrs):
        out[2 * i] = p & 255
        out[2 * i + 1] = p >> 8
    assert len(out) <= ENEMY_SIZE, f"nomes de inimigos passaram do limite: {len(out)} > {ENEMY_SIZE}"
    rom[o:o + len(out)] = out
    open(dst, "wb").write(rom)
    print("ok:", dst, "| bytes de nomes:", len(out), "de", ENEMY_SIZE)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
