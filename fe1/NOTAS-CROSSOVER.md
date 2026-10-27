# Notas do projeto crossover (FE1)

Base: repositório StanHash/fe1 (disassembly do Fire Emblem 1 de NES).

## ROM base usada

Este projeto foi ajustado para montar a **ROM em inglês** (arquivo "Fire Emblem Shadow Dragon and the Blade of Light English v1.4.1"),
e não a ROM japonesa original que o repositório espera.

- Coloque a sua ROM nesta pasta com o nome `fe1-base.nes`.
- `make compare` confere o resultado contra `fe1.sha1`, que agora guarda o hash da ROM em inglês
  (`14ac03026819133693873f737cc224d1f18f2a7b`). O hash original está em `fe1.sha1.original`.
- Se a montagem gerar esse hash, a ROM saiu idêntica byte a byte.

## O que foi mudado em relação ao repositório original

A ROM traduzida difere da original em 3.286 bytes, todos no banco 15 (a parte fixa da ROM).
Foram ajustados para refletir a ROM traduzida:

- `data/item-data.asm`: valores da tabela de itens e os ponteiros de `EffectivenessInfo` ($D937).
- `data/data-0F-DA1F.asm`, `data/data-0F-E5F1.asm`, `data/data-0F-EDB5.asm`, `data/data-0F-F807.asm`: blocos de dados.
- `code/home/code-E65C.asm`: em `$E6A6` o original fazia `sta sUnk7934`; a tradução usa `jmp $FCF0`,
  uma rotina própria no espaço livre do banco (esse trecho em `$FCF0` ainda não foi desmontado).

Script usado: `scripts/sync_home_data.py` (copia os bytes da ROM base para as linhas `.db` dos arquivos de dados).
Atenção: ele confia no endereço escrito no comentário de cada linha; no arquivo `data-0F-ECF6.asm` um comentário
estava errado e foi corrigido à mão.

## Como montar

1. `bash tools/install-wla-dx.sh` (uma vez; precisa de CMake e compilador C++)
2. `make compare`
