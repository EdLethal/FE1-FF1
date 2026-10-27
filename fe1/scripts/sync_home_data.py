"""Atualiza os arquivos .asm de dados do banco 15 (home) para refletir a ROM base.

Uso: python3 -I sync_home_data.py <pasta_do_projeto_fe1>

Cada linha de dados tem o formato:
    /* D657 ...      */ .db $0C, $05, ...
O script le o endereco do comentario e troca os bytes pelos que estao na
ROM base (fe1-base.nes). Linhas que nao sejam apenas '.db $XX, ...' ficam intactas.
"""
import re
import sys
from pathlib import Path

proj = Path(sys.argv[1])
rom = (proj / "fe1-base.nes").read_bytes()

HOME_BANK_FILE_OFFSET = 16 + 15 * 0x4000  # inicio do banco 15 no arquivo .nes
FILES = [
    "data/item-data.asm",
    "data/data-0F-DA1F.asm",
    "data/data-0F-E5F1.asm",
    "data/data-0F-E828.asm",
    "data/data-0F-ECF6.asm",
    "data/data-0F-EDB5.asm",
    "data/data-0F-F1BF.asm",
    "data/data-0F-F807.asm",
    "data/job/stats.asm",
    "data/map-rows.asm",
]

LINE = re.compile(r"^(\s*/\* ([0-9A-Fa-f]{4}) \.\.\.\s*\*/ \.db )((?:\$[0-9A-Fa-f]{2})(?:,\s*\$[0-9A-Fa-f]{2})*)\s*$")

total_changed = 0
for rel in FILES:
    path = proj / rel
    if not path.exists():
        print(f"  (nao existe) {rel}")
        continue
    out = []
    changed = 0
    for line in path.read_text().split("\n"):
        m = LINE.match(line)
        if not m:
            out.append(line)
            continue
        addr = int(m.group(2), 16)
        old = [int(t[1:], 16) for t in re.split(r",\s*", m.group(3))]
        off = HOME_BANK_FILE_OFFSET + (addr - 0xC000)
        new = list(rom[off:off + len(old)])
        if new != old:
            changed += sum(1 for x, y in zip(old, new) if x != y)
            line = m.group(1) + ", ".join(f"${b:02X}" for b in new)
        out.append(line)
    if changed:
        path.write_text("\n".join(out))
    print(f"{rel}: {changed} bytes atualizados")
    total_changed += changed
print("total:", total_changed)
