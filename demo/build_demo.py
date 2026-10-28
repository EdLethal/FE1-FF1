"""Gera a ROM de demo do "Templo" a partir da ROM base do FE1.

Uso: python3 -I demo/build_demo.py <fe1-base.nes> <saida.nes>

Substitui no capitulo 1 (mapa 1): o mapa, a posicao inicial das unidades do jogador e a lista de inimigos.
Nada de codigo e alterado, so dados. A ROM base nao e modificada.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from fe1rom import Rom  # noqa: E402

MAP_NUMBER = 1

# ---------------------------------------------------------------- unidades
# Jogador: posicoes (linha, coluna) por ordem da lista original do capitulo 1:
# Mars, Jagen, Abel, Cain, Draug, Gordin, Caeda.
PLAYER_POS = [(12, 15), (12, 14), (12, 16), (12, 17), (13, 15), (13, 14), (13, 16)]

# Inimigos: (pid, classe, nivel, item1, item2, linha, coluna, ia_tipo, ia_alvo_linha, ia_alvo_coluna)
# classe 8 = Pirate, 9 = Thief, 12 = Hunter. O chefe usa o mesmo pid do chefe do capitulo 1.
# ia_tipo e alvo foram copiados dos inimigos originais (o alvo e para onde o inimigo caminha).
BOSS = (129, 8, 5, 28, 64, 1, 15, 29, 1, 15)
GUARD_AI = (53, 12, 16)
ENEMIES = [
    BOSS,
    (133, 8, 1, 27, 0, 2, 10, *GUARD_AI),
    (133, 8, 1, 27, 0, 2, 21, *GUARD_AI),
    (133, 8, 1, 27, 0, 4, 12, *GUARD_AI),
    (133, 9, 1, 2, 0, 4, 19, *GUARD_AI),
    (133, 8, 1, 27, 0, 6, 14, *GUARD_AI),
    (133, 12, 1, 17, 0, 8, 10, *GUARD_AI),
    (133, 8, 1, 27, 0, 8, 21, *GUARD_AI),
    (133, 8, 1, 27, 0, 10, 13, *GUARD_AI),
    (133, 8, 1, 27, 0, 10, 18, *GUARD_AI),
]


def parse_map(path):
    text = Path(path).read_text()
    head, grid = text.split("\nmap:\n")
    legend = {}
    for m in re.finditer(r"^\s+(\S) = ([0-9A-Fa-f]{2})\b", head, re.M):
        legend[m.group(1)] = int(m.group(2), 16)
    cam = re.search(r"^camera:\s*(\d+)\s+(\d+)", head, re.M)
    rows = [r for r in grid.split("\n") if r]
    unknown = {c for r in rows for c in r} - set(legend)
    assert not unknown, f"simbolos sem legenda: {unknown}"
    return [[legend[c] for c in r] for r in rows], (int(cam.group(1)), int(cam.group(2)))


def main(base, out):
    rom = Rom(base)
    grid, cam = parse_map(HERE / "temple.txt")
    rom.set_map(MAP_NUMBER, grid, cam=list(cam))

    def list_ptr(table):
        return rom.word(8, table + 2 * (MAP_NUMBER - 1))

    # jogador: so muda y (+16) e x (+17) de cada registro de 27 bytes
    p = list_ptr(0x8490)
    n = 0
    while rom.read(8, p, 1)[0]:
        assert n < len(PLAYER_POS), "mais unidades do jogador que posicoes"
        y, x = PLAYER_POS[n]
        rom.write(8, p + 16, [y, x])
        p += 27
        n += 1
    assert n == len(PLAYER_POS), f"o capitulo tem {n} unidades do jogador"

    # inimigos: registros de 11 bytes; precisa caber no espaco da lista original
    p = list_ptr(0x8AA3)
    old = 0
    while rom.read(8, p + old * 11, 1)[0]:
        old += 1
    assert len(ENEMIES) <= old, f"a lista original tem {old} inimigos; recebi {len(ENEMIES)}"
    for i, (pid, jid, lv, it0, it1, y, x, ai, ty, tx) in enumerate(ENEMIES):
        rom.write(8, p + i * 11, [pid, jid, lv, it0, it1, y, x, ai, 0, ty, tx])
    rom.write(8, p + len(ENEMIES) * 11, [0])  # terminador

    rom.save(out)
    print(f"ROM de demo gravada em {out} | mapa {len(grid)}x{len(grid[0])} | {len(ENEMIES)} inimigos | {n} unidades")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
