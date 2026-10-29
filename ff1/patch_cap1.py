"""FF1 com cara do capitulo 1 do FE: classes dos 4 herois e inimigos renomeados (so dados de texto).

Uso: python3 -I ff1/patch_cap1.py <FinalFantasy_USA.nes> <saida.nes> [pasta do disassembly do FF1 com os .tbl]

Classes (a mecanica por baixo continua a do FF1):
  Fighter -> LORD (Mars) | Thief -> CAVALRY (Kain) | Black Belt -> PEGASUS (Sheeda)
  Red Mage -> PALADIN (Jeigan) | White Mage -> PRIEST (Wryf) | Black Mage -> MAGE
Inimigos: IMP -> PIRATE, GrIMP -> THIEF, WOLF e GrWOLF -> HUNTER, GARLAND -> GAZZAK (chefe)
Encontros do Templo dos Demonios: so piratas ou ladrao + cacadores
"""
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from patch_names import enc, off  # noqa: E402
from ff1text import Dialogue, load_tables  # noqa: E402

CLASSES = {0: "LORD", 1: "CAVALRY", 2: "PEGASUS", 3: "PALADIN", 4: "PRIEST", 5: "MAGE"}
ENEMIES = {0: "PIRATE", 1: "THIEF", 2: "HUNTER", 3: "HUNTER", 105: "GAZZAK"}

# Encontros aleatorios do Templo dos Demonios (mapa 12 -> dominio 64+12 = 76, 8 vagas com pesos 12,12,12,12,6,6,3,1 de 64):
# formacao $00 = 3-5 PIRATE; formacao $02 = THIEF + HUNTER. Nenhuma formacao foi alterada, so quais sao sorteadas.
TEMPLE_MAP = 12
TEMPLE_SLOTS = [0x00, 0x02, 0x00, 0x02, 0x02, 0x00, 0x02, 0x00]
ENEMY_BASE, ENEMY_SIZE = 0x94E0, 1136

# Dialogos (ids do FF1): 1 = rei na abertura (vira o pedido da Sheeda), 2 = rei ao final (vira o final do capitulo),
# 4 = fala do Garland antes da luta (vira a fala do Gazzak, escrita por voce e traduzida para o ingles).
# Falas encurtadas e adaptadas das cenas do cap. 1 do FE; precisam caber no espaco do texto original.
DIALOGUES = {
    1: "Prince Mars! Pirates of\nGarda took Talis castle\nand killed many people.\nPlease protect my father!",
    4: "You have some nerve\ncoming here. Your\njourney ends here.\nDie!!",
    2: "Thank you, Mars. I will\nsend soldiers led by\nCaptain Oguma. Find the\nallies hiding in villages\nor held by the enemy.\nGo on to Orleans!!",
}


def main(src, dst, disasm="/home/claude/ff1-build"):
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
    std, dte = load_tables(disasm + "/table_standard.tbl", disasm + "/table_dte.tbl")
    dlg = Dialogue(rom, std, dte)
    for i, text in DIALOGUES.items():
        old, new = dlg.replace_in_place(i, text)
        print(f"dialogo {i}: {new} de {old} bytes")
    dom = off(0x0B, 0x8000) + (64 + TEMPLE_MAP) * 8
    rom[dom:dom + 8] = bytes(TEMPLE_SLOTS)
    open(dst, "wb").write(rom)
    print("ok:", dst, "| bytes de nomes:", len(out), "de", ENEMY_SIZE)


if __name__ == "__main__":
    main(*sys.argv[1:4])
