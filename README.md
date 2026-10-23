# CacaZoo

Triagem automática de três projetos do Zooniverse que dão crédito de descoberta:
Backyard Worlds (anãs marrons), Active Asteroids (asteroides com cauda) e Kilonova Seekers (transientes).

    python3 caca.py --n 40            # todos os projetos
    python3 caca.py --n 80 --projeto aa
    python3 caca.py --reusar          # reavalia o último resultado sem baixar de novo
    open report.html

Baixa os objetos da fila pela API pública (sem login), dá uma nota por análise de imagem
e gera report.html ordenado, com links para classificar e para o Talk. Quem classifica é você.

Validação (rode de novo depois de mexer nos detectores):

    python3 testes/injecao_byw.py   # anãs marrons sintéticas em imagens reais
    python3 testes/injecao_aa.py    # caudas sintéticas em asteroides reais
    python3 testes/treino_kn.py     # 51 objetos rotulados pela equipe do Kilonova Seekers

Estado em 22/10/2026 (40 objetos por projeto):

| Projeto | Detector | Resultado |
|---|---|---|
| Backyard Worlds | mediana do 1º terço das 14 épocas contra a do último terço; par claro/escuro; estrelas fixas e saturadas mascaradas (limiar relativo ao fundo) | recupera 88–90% dos movers sintéticos acima do p95 dos limpos; nota máx. sem injeção 4.6 |
| Active Asteroids | deslocamento do centro de luz da mancha central, penalidade para estrela grudada, mediana dos 5 quadros | recupera 30/50/65% das caudas fraca/média/forte |
| Kilonova Seekers | log(pico no painel ciência) + log(pico no painel diferença) | AUC 0.84 nos 51 de treino (o s2n do projeto sozinho dá 0.59) |

Limitações: amostras pequenas (40–51), caudas e movers sintéticos são idealizados,
e os detectores não substituem olhar — servem para pôr os promissores no topo.

Checagem de catálogo (Backyard Worlds, nota ≥ 6): converte o pixel do candidato em RA/Dec e
consulta CatWISE2020 (pm > 0.05"/ano e > 5σ) e Gaia DR3 (pm > 50 mas/ano) no VizieR.
"NADA ... se movendo aqui" = nenhum objeto conhecido em movimento: aí vale abrir no WiseView e postar no Talk.

Varredura de 22/10/2026 (300 objetos do Backyard Worlds): 12 candidatos fortes, os 12 são
objetos reais em movimento já catalogados (ex.: CWISE J100733.72-455515.8 a 1.96"/ano).
Nenhuma descoberta nova, mas confirma que o detector acha movers de verdade.
