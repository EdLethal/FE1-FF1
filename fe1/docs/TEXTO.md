# Texto do FE1 (ROM em ingles) — o que ja foi descoberto

Descoberto por busca relativa de palavras conhecidas na ROM (nao esta no disassembly original).

## Codificacao (uma das tabelas de caracteres)
- `$00-$19` = A-Z (maiusculas)
- `$1A-$33` = a-z (minusculas)
- `$EF`, `$ED`, `$84` aparecem como separadores entre palavras/entradas (significado exato ainda nao confirmado)
- outros codigos (`$50`, `$51`, `$52`, `$39`) sao pontuacao/letras especiais ainda nao mapeadas (ex.: `Gharne<51>` = Gharnef)
- existe uma segunda tabela para a fonte de janelas (A = `$1A` ... para `STRENGTH` em `$34DA5`), ainda nao mapeada por completo

## Locais encontrados (offset no arquivo .nes, sem cabecalho de 16 bytes)
| Offset no arquivo | Conteudo |
|---|---|
| `$3EF00` | lista de nomes de personagens (Mars, Jeigan, Kain, Abel, Doga, Gordon, Rickrd, Wry?, Saji, Maji, Bartz, Kashim, Oguma, Darros, Julian, Marich, Navarr, Hardin...) |
| `$3F5E0`, `$3F640` | nomes de lugares (Talis, Garda, Devil Mountain, Orleans, Warren, Diel, Akaneia, Pales castle, Menidy, Khadein, Aritia...) |
| `$3DDB0` | lista de palavras de dialogo (here, castle, Gharnef, Hahaha, don't, Sable, Order, human, army, strong, again, come, Princess, Aritia, Nyna, want...), parece um dicionario de palavras |

## Hipotese ainda nao confirmada
Os dialogos provavelmente sao guardados como sequencias de indices dessa lista de palavras. Falta achar o ponteiro de roteiro do capitulo 1 e a rotina que monta as frases.
