"""Le as tabelas ItemInfo.* de dois item-data.asm e mostra a tabela de itens
e as diferencas entre eles.

Uso: python3 -I item_tables.py <item-data.asm da sua ROM> [<item-data.asm original para comparar>]
Cada tabela e indexada pelo id do item (iid), a partir de 0.
"""
import re
import sys
from pathlib import Path

COLS = ["might", "weapon_level", "weight", "hit", "crit", "cost", "uses"]
NAMES = {7: "Mercurius", 8: "Levin Sword", 9: "Devil's Sword", 10: "Falchion", 14: "Javelin", 29: "Devil Axe"}


def parse(path):
    tables, cur = {}, None
    for line in Path(path).read_text().split("\n"):
        m = re.match(r"^ItemInfo\.(\w+):", line)
        if m:
            cur = m.group(1)
            tables[cur] = []
            continue
        if cur and ".db" in line and not line.strip().startswith(";"):
            body = line.split(".db", 1)[1].split(";")[0]
            tables[cur] += [int(t.strip()[1:], 16) for t in body.split(",") if t.strip().startswith("$")]
    return tables


mine = parse(sys.argv[1])
print("Tamanhos das tabelas:", {k: len(v) for k, v in mine.items() if k in COLS})
print()
print("iid | nome | " + " | ".join(COLS))
for i in range(len(mine["might"])):
    row = [mine[c][i] if i < len(mine[c]) else None for c in COLS]
    if all(v in (0, None) for v in row):
        continue
    print(f"{i:02X}  | {NAMES.get(i, '')} | " + " | ".join("-" if v is None else str(v) for v in row))

if len(sys.argv) > 2:
    orig = parse(sys.argv[2])
    print("\nDIFERENCAS (original -> sua ROM):")
    n = 0
    for c in COLS + ["effectiveness", "effect"]:
        a, b = orig.get(c, []), mine.get(c, [])
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                n += 1
                print(f"  {c}[iid {i:02X}]: {a[i]} -> {b[i]}")
    print("total de diferencas:", n)
