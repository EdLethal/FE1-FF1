"""Roda a ROM de demo sem tela, passa pela abertura do capitulo 1 e salva screenshots.

Uso: python3 -I demo/run_demo.py <rom.nes> <core fceumm_libretro.so> <pasta_de_saida> [toques_em_A]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from nesrun import Emu  # noqa: E402


def to_map(e, dialog_taps=110):
    e.run(1200)
    e.tap("start"); e.run(60)       # abertura -> menu
    e.tap("start"); e.run(60)       # menu -> arquivos
    e.tap("a"); e.run(90)           # escolhe o arquivo
    e.tap("a"); e.run(150)          # inicia o capitulo
    for _ in range(dialog_taps):    # passa os dialogos de abertura
        e.tap("a", hold=5, wait=40)
    e.run(60)


if __name__ == "__main__":
    rom, core, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    taps = int(sys.argv[4]) if len(sys.argv) > 4 else 110
    out.mkdir(parents=True, exist_ok=True)
    e = Emu(core, rom)
    to_map(e, taps)
    e.screenshot(str(out / "mapa_inicio.png"), scale=2)
    print("screenshot salvo em", out / "mapa_inicio.png")
