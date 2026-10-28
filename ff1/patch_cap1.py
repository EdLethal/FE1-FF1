"""FF1 com cara do capitulo 1 do FE: classes dos 4 herois e inimigos renomeados (so dados de texto).

Uso: python3 -I ff1/patch_cap1.py <FinalFantasy_USA.nes> <saida.nes>

Classes (a mecanica por baixo continua a do FF1):
  Fighter -> LORD (Mars) | Thief -> CAVALRY (Kain) | Black Belt -> PEGASUS (Sheeda)
  Red Mage -> PALADIN (Jeigan) | White Mage -> PRIEST (Wryf) | Black Mage -> MAGE
Inimigos: IMP -> PIRATE, GrIMP -> THIEF, WOLF -> HUNTER, GARLAND -> GAZZAK (chefe)
"""
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from patch_names import enc, off  # noqa: E402

CLASSES = {0: "LORD", 1: "CAVALRY", 2: "PEGASUS", 3: "PALADIN", 4: "PRIEST", 5: "MAGE"}
ENEMIES = {0: "PIRATE", 1: "THIEF", 2: "HUNTER", 105: "GAZZAK"}
ENEMY_BASE, ENEMY_SIZE = 0x94E0, 1136


def main(src, dst):
    rom = bytearray(open(src, "rb").read())
    for idx, name in CLASSES.items():
        assert len(name) <= 7
        o = off(0x0A, 0xBF43) + idx * 8
        rom[o:o + 8] = enc(name.ljust(7)) + b"\x00"

    o = off(0x0B, ENEMY_BASE)
    blob = rom[o:o + ENEMY_SIZE]
    n = ((blob[0] | blob[1] << 8) - ENEMY_BASE) // 2
    names = []
    for i in range(n):
        p = (blob[2 * i] | blob[2 * i + 1] << 8) - ENEMY_BASE
        names.append(bytes(blob[p:blob.index(0, p)]))
    for i, nm in ENEMIES.items():
        names[i] = enc(nm)
    out = bytearray(2 * n)
    ptrs = []
    for nm in names:
        ptrs.append(ENEMY_BASE + len(out))
        out += nm + b"\x00"
    for i, p in enumerate(ptrs):
        out[2 * i], out[2 * i + 1] = p & 255, p >> 8
    assert len(out) <= ENEMY_SIZE, f"nomes de inimigos passaram do limite: {len(out)} > {ENEMY_SIZE}"
    rom[o:o + len(out)] = out
    open(dst, "wb").write(rom)
    print("ok:", dst, "| bytes de nomes:", len(out), "de", ENEMY_SIZE)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
