"""Teste 2 do lado FF1: muda os atributos iniciais de uma classe (so dados).

Uso: python3 -I ff1/patch_stats.py <entrada.nes> <saida.nes>
Tabela: banco $00, enderecos $B040, 16 bytes por classe:
  [0]=id (nao usado) [1]=HP [2]=forca [3]=agilidade [4]=inteligencia [5]=vitalidade [6]=sorte
  [7]=dano [8]=acerto [9]=esquiva [10]=defesa magica
"""
import sys

BASE = 16 + 0 * 0x4000 + (0xB040 - 0x8000)
LORD = 0  # classe 0 (antiga Fighter)
NEW = {1: 99, 2: 40, 5: 30}  # HP 99, forca 40, vitalidade 30


def main(src, dst):
    rom = bytearray(open(src, "rb").read())
    for k, v in NEW.items():
        rom[BASE + LORD * 16 + k] = v
    open(dst, "wb").write(rom)
    print("ok:", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
