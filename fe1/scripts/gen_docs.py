"""Gera docs/CLASSES-E-ITENS.md a partir dos .asm do projeto.

Uso: python3 -I scripts/gen_docs.py <pasta fe1> <item-data.asm original japones>
"""
import re
import sys
from pathlib import Path

proj = Path(sys.argv[1])
orig_items = Path(sys.argv[2])

COLS = ["might", "weapon_level", "weight", "hit", "crit", "cost", "uses"]
NAMES = {7: "Mercurius", 8: "Levin Sword", 9: "Devil's Sword", 10: "Falchion", 14: "Javelin", 29: "Devil Axe"}


def parse_items(path):
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


def num(t):
    t = t.strip()
    return int(t[1:], 16) if t.startswith("$") else int(t)


# ---- classes
text = (proj / "data/job/stats.asm").read_text()
names = re.findall(r"\.dw @(\w+)Stats ; (\d+)", text)
rows = {}
for m in re.finditer(r"^@(\w+)Stats:\s+\.db\s+(.*)$", text, re.M):
    rows[m.group(1)] = [num(x) for x in m.group(2).split(",")]
classes = []
for name, idx in names:
    classes.append((int(idx) + 1, name, rows[name]))

class_md = ["| jid | Classe | Força | Perícia | Nível arma | Veloc. | Sorte | Defesa | Mov. | HP base | Exp base |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
for jid, name, v in classes:
    class_md.append(f"| {jid} | {name} | " + " | ".join(str(x) for x in v) + " |")

# ---- itens
mine = parse_items(proj / "data/item-data.asm")
orig = parse_items(orig_items)
all_cols = COLS + ["effectiveness", "effect"]
item_md = ["| iid | Nome conhecido | Força | Nível arma | Peso | Acerto | Crítico | Preço | Usos | Mudou vs. original |",
           "|---|---|---|---|---|---|---|---|---|---|"]
for i in range(len(mine["might"])):
    row = [mine[c][i] for c in COLS]
    ch = [f"{c} {orig[c][i]}→{mine[c][i]}" for c in all_cols
          if i < len(orig.get(c, [])) and i < len(mine.get(c, [])) and orig[c][i] != mine[c][i]]
    if all(v == 0 for v in row) and not ch:
        continue
    item_md.append(f"| {i:02X} | {NAMES.get(i, '')} | " + " | ".join(str(v) for v in row) + " | " + "; ".join(ch) + " |")

# ---- custos de movimento (data/data-0F-E828.asm)
mem = {}
for line in (proj / "data/data-0F-E828.asm").read_text().split("\n"):
    m = re.match(r"^\s*/\* ([0-9A-Fa-f]{4}) \.\.\.\s*\*/ \.db (.*)$", line)
    if m:
        a = int(m.group(1), 16)
        for k, t in enumerate(x for x in m.group(2).split(",") if x.strip().startswith("$")):
            mem[a + k] = int(t.strip()[1:], 16)
ptrs = [mem[0xE9C8 + 2 * i] | (mem[0xE9C8 + 2 * i + 1] << 8) for i in range(22)]
move_md = ["| Classe | " + " | ".join(f"T{t}" for t in range(22)) + " |",
           "|---|" + "---|" * 22]
for (jid, name, _), p in zip(classes, ptrs):
    cells = [("·" if mem[p + t] == 0xFF else str(mem[p + t])) for t in range(22)]
    move_md.append(f"| {name} | " + " | ".join(cells) + " |")
bonus = [mem[0xEBD8 + t] for t in range(22)]
bonus_md = "| " + " | ".join(f"T{t}" for t in range(22)) + " |\n|" + "---|" * 22 + "\n| " + " | ".join(str(b) for b in bonus) + " |"

out = proj / "docs/CLASSES-E-ITENS.md"
out.parent.mkdir(exist_ok=True)
out.write_text("<!-- gerado por scripts/gen_docs.py -->\n\n## Classes (22)\n\n" + "\n".join(class_md) +
               "\n\n## Custo de movimento por classe e terreno\n\n"
               "T0 a T21 são os 22 tipos de terreno (só tenho os números, não os nomes). `·` = intransponível ($FF).\n\n"
               + "\n".join(move_md) +
               "\n\n## Valor por terreno usado pela IA (`DAT_EBD8`)\n\n" + bonus_md +
               "\n\n## Itens (por id)\n\n" + "\n".join(item_md) + "\n")
print("escrito:", out, "| classes:", len(classes), "| linhas de item:", len(item_md) - 2, "| matriz:", len(move_md) - 2, "x 22")
