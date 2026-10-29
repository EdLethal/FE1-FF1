"""Leitura e escrita dos dialogos do FF1 (banco $0A): ponteiros em $8000 (256 x 2 bytes), textos com compressao DTE.

Codigos: $00 = fim do texto, $01 = quebra de linha. Os demais vem de table_standard.tbl e table_dte.tbl
do disassembly (aqui replicados pela tabela do proprio disassembly, passada no carregamento).
"""
HEADER, BANK = 16, 0x4000
BANK_ID = 0x0A


def load_tables(std_path, dte_path):
    std, dte = {}, {}
    for path, tgt in ((std_path, std), (dte_path, dte)):
        for line in open(path):
            line = line.rstrip("\n")
            if "=" in line and len(line) >= 3:
                k, v = line.split("=", 1)
                tgt[int(k, 16)] = v
    return std, dte


class Dialogue:
    def __init__(self, rom, std, dte):
        self.rom, self.std, self.dte = rom, std, dte
        self.base = HEADER + BANK_ID * BANK - 0x8000
        # na tabela DTE a quebra de linha ($05) vem escrita como "\\n"; aqui usamos a quebra real
        self.std = std
        self.dte = {k: ("\n" if v == "\\n" else v) for k, v in dte.items()}
        self.inv_std = {v: k for k, v in std.items() if len(v) == 1}
        self.inv_std["\n"] = 0x05
        self.inv_dte = {v: k for k, v in self.dte.items() if len(v) == 2}

    def ptr(self, i):
        o = self.base + 0x8000 + 2 * i
        return self.rom[o] | self.rom[o + 1] << 8

    def raw(self, i):
        p = self.base + self.ptr(i)
        e = self.rom.index(0, p)
        return bytes(self.rom[p:e])

    def decode(self, i):
        out = ""
        for x in self.raw(i):
            out += self.dte.get(x) or self.std.get(x) or "<%02X>" % x
        return out

    def encode(self, text):
        out, k = bytearray(), 0
        while k < len(text):
            pair = text[k:k + 2]
            if len(pair) == 2 and pair in self.inv_dte:
                out.append(self.inv_dte[pair]); k += 2; continue
            out.append(self.inv_std[text[k]]); k += 1
        return bytes(out)

    def replace_in_place(self, i, text):
        """Troca o texto no mesmo lugar. O novo texto (comprimido) precisa caber no espaco do antigo."""
        old_len = len(self.raw(i))
        new = self.encode(text)
        assert len(new) <= old_len, f"dialogo {i}: {len(new)} bytes > {old_len} disponiveis"
        p = self.base + self.ptr(i)
        self.rom[p:p + len(new) + 1] = new + b"\x00"
        return old_len, len(new)
