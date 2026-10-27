# Fire Emblem 1 (NES): mecânicas lidas direto do código

Tudo aqui foi lido do assembly deste projeto (arquivos `code/home/battle.asm`, `code/load-units.asm`,
`include/structs/unit.asm`, `data/job/stats.asm`). Onde eu **deduzi** em vez de ler, está marcado.
Tabelas completas de classes e itens: `CLASSES-E-ITENS.md`.

## 0. O que a sua ROM tem de diferente do original japonês

O projeto monta a ROM em inglês (v1.4.1). Comparando com o disassembly (que descreve a ROM japonesa):

- **Idêntico ao original:** tabela de classes, tabelas de terreno, código de combate.
- **Diferente: tabelas de itens.** Seis posições que estavam vazias no original (iid `1F`, `20`, `24`, `26`, `27`, `28`)
  têm armas completas na sua ROM, e alguns itens existentes mudaram de números (ex.: iid `29` caiu de força 20 para 5,
  iid `0C` subiu de 5 para 7). Lista exata em `CLASSES-E-ITENS.md`, coluna "Mudou vs. original".
- **Diferente: textos e nomes** (esperado, é a tradução) e um desvio de código em `$E6A6` (`jmp $FCF0`) para uma rotina
  própria da tradução que ainda não desmontei.

Não sei dizer se as mudanças nos itens são balanceamento intencional do patch ou outra coisa. Para fidelidade de
"mesmas mecânicas do original", a ROM japonesa limpa seria a referência.

## 1. A unidade (27 bytes)

| Offset | Campo | Offset | Campo |
|---|---|---|---|
| +00 | pid (personagem) | +0D | mov (movimento) |
| +01 | jid (classe, começa em 1) | +0E | desconhecido |
| +02 | nível | +0F | resistência |
| +03 | HP atual | +10 | y |
| +04 | HP máximo | +11 | x |
| +05 | experiência | +12 | desconhecido (as buscas de unidade pulam quem tem `$FF` ou `$F0` aqui; provavelmente "inativa") |
| +06 | cell (índice das tabelas de terreno) | +13 | 4 itens |
| +07 | força | +17 | 4 contadores de usos |
| +08 | perícia | | |
| +09 | nível de arma | | |
| +0A | velocidade | | |
| +0B | sorte | | |
| +0C | defesa | | |

Cada unidade guarda apenas 4 itens. Inimigos têm 2.

## 2. Tabela de classes e como o status é montado

Cada classe tem **9 bytes**: força, perícia, nível de arma, velocidade, sorte, defesa, movimento, HP base, exp base.
(O comentário original do arquivo lista só 8 colunas; a 9ª, experiência, eu confirmei pelo código que a copia.)

Regra de criação de **unidade inimiga** (`EnemyInfoToUnit`, lido do código):

- `bônus = (nível − 1) ÷ 2` (divisão inteira)
- força, perícia, nível de arma, velocidade e defesa = valor da classe + bônus
- **sorte e movimento não recebem bônus**
- HP = HP base + 3 × bônus
- experiência = exp base + nível − 1 (aproximado)

Ou seja, inimigos escalam de forma fixa e linear com o nível, sem crescimento aleatório.
O banco 3 tem uma cópia dessa lógica (`$92C5`), provavelmente para outro tipo de unidade; não verifiquei.

**Ainda não sei:** de onde vêm os status dos personagens do jogador (Marth etc.) nem a resistência (+0F),
que não está na tabela de classes.

## 3. Combate

Cada lutador (0 e 1) tem os valores calculados abaixo. "Oponente" = o outro lutador.
Magias são os itens com id ≥ `2A`, mais a Levin Sword (`08`).

1. **Velocidade de ataque** = velocidade − peso da arma (mínimo 0).
2. **Esquiva** = sorte.
3. **Acerto (arma física)** = perícia + acerto da arma − (velocidade de ataque do oponente + `wUnk0310` do oponente),
   limitado entre 0 e 100. `wUnk0310` não identifiquei; **provavelmente bônus de terreno** (dedução).
4. **Acerto (magia)** = acerto da magia − esquiva (sorte) do oponente, mínimo 0. Não usa perícia.
5. **Defesa usada** = resistência do alvo se o atacante usa magia; senão defesa.
6. **Dano físico** = força + força da arma − defesa usada (mínimo 0).
   Se a arma tem "efetividade" e o alvo é do tipo, a força da arma conta **3 vezes** no total.
7. **Dano mágico** = força da magia − resistência do alvo (mínimo 0). **A força do usuário não entra.**
8. **Teto de dano = 40**, exceto com a Falchion. Observação de leitura: a checagem da Falchion olha sempre o
   lutador 0, para os dois lados.
9. **Crítico** = ((perícia + sorte) ÷ 2 + crítico da arma) ÷ 2.
10. **Ataque duplo:** quem tem velocidade de ataque **estritamente maior** ataca de novo. Não há margem mínima
    (diferença de 1 ponto já basta). Existe uma condição extra (`wUnk0358`) que bloqueia o segundo golpe do
    atacante e que não identifiquei.
11. **Rolagem:** uma rolagem por golpe, calculada como (número de 0 a 255 × 10) ÷ 25, ou seja, de **0 a 102**.
    Acerta se o resultado ≤ acerto. Não é média de duas rolagens. Crítico é rolado do mesmo jeito.
    Consequência: com acerto 100, sair 101 ou 102 ainda erra. São 3 dos 256 valores possíveis (cerca de 1,2%),
    se o gerador for uniforme. O gerador soma 55 a cada chamada (módulo 256); não verifiquei se outra parte do
    código o altera, então não afirmo o quão previsível ele é na prática.

Observação de leitura (não afeta o jogo, só curiosidade): em `ComputeFightHit` há uma checagem de magia que nunca
é alcançada, porque o caso já foi tratado antes.

## 4. Movimento

O que li: a rotina `$8AE8` percorre um mapa de movimento por célula em que os 6 bits baixos parecem ser o custo
de entrar na célula (0 = bloqueado) e os 2 bits altos uma direção, descontando o custo do movimento da unidade.
Isso é **dedução de uma rotina só**.

**Ainda não achei:** o custo por tipo de terreno e por classe. As tabelas `Cell2TerrainBlue/Red` ($E828/$E8F8)
mapeiam célula para tipo de terreno (`$0E` = aliado, `$1F` = inimigo), não para custo.
Esse é o próximo ponto a investigar, porque é a peça central para uma versão em grade.

## 5. Resumo para o crossover

- Os números de combate do FE1 são simples e tabelados: dá para reproduzir em outro motor sem ambiguidade.
- O que falta para o FF1 virar tático: custos de movimento por terreno e a origem dos status dos personagens fixos.
