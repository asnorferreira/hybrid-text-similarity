# Snapshot Q5-V2 — RG-01

O [snapshot](q5v2-snapshot.json) congela os 32 casos NFo do produto cartesiano
formato × modo × relação, baseados nos quatro pares escritos à mão de
[equivalência](../equivalence/README.md). Não é avaliação científica e não lê
treino, validação ou teste da pesquisa.

Cada caso registra índice, matrizes, classes disponíveis, sentenças, alinhamento
e resumo. Campos de tempo e hashes de implementação ficam fora da projeção
comportamental. A comparação é recursiva: números têm tolerância **absoluta
1e-9, relativa zero**; classes, tipos, chaves e demais valores são exatos.
No modo lexical, classes e matrizes semânticas permanecem indisponíveis conforme
o contrato; não se inventa um rótulo.

O envelope registra commit e árvore suja (hashes de fontes, diff e git status),
gerador, manifesto das 24 fixtures, modelo com revisão e identidade, IDF da
aplicação e configuração de política. O IDF científico de treino não é usado.
O teste verifica a identidade dos recursos e lê o arquivo congelado, sem
recalculá-lo como esperado. A procedência da implementação é histórica e não
impede a comparação de futuras implementações com os mesmos recursos.

Geração inicial somente em Docker, usando a imagem core preparada e a montagem
do modelo verificado; a orquestração exata e a proveniência estão nas
[evidências P3](../../../../TCC/evidencias/codex-p03-01/).

```sh
python scripts/generate_q5v2_snapshot.py --provenance /provenance.json --out /snapshot/q5v2-snapshot.json
python -m pytest -q tests/test_q5v2_regression.py
```

O gerador recusa qualquer arquivo já existente. Não regenerar o snapshot para
acomodar uma regressão; uma mudança deliberada exige justificativa e novo
artefato, preservando o anterior. As duas execuções de P3 mantêm o mesmo hash e
comparam com o mesmo arquivo. Logs/JUnit têm durações próprias, sem exigir
igualdade de seus bytes.
