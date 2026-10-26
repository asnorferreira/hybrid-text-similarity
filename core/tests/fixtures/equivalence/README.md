# Fixtures de equivalência

Pares R1–R4 escritos à mão para verificar comportamento de software. Não vêm de treino, validação ou teste da pesquisa; não validam H1/H2.

A fonte de verdade é [pairs.json](pairs.json). O gerador [generate_equivalence.py](../../../scripts/generate_equivalence.py) usa `dataset_formats.render` para gravar os mesmos textos em TXT, DOCX e PDF, com manifesto de hashes. Executar somente em Docker:

```bash
python scripts/generate_equivalence.py --out tests/fixtures/equivalence/formats
```

O manifesto declara metadados e hashes; o teste compara todas as extrações e saídas com o texto colado. Critério numérico: diferença absoluta máxima 1e-9, sem tolerância relativa. Os limites NF usam textos artificiais construídos por comprimento/sentenças; tamanhos de contêiner ilustrativos do plano são registrados separadamente dos limites contratuais exatos.
