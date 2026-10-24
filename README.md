# hybrid-text-similarity

Comparação local de dois arquivos PT-BR (PDF com texto, DOCX, TXT), por sentenças. O índice de similaridade do projeto vai de 0 a 100; não é Pearson/Spearman nem prova de plágio. A S2 oferece API e persistência de desenvolvimento. Telas e autenticação pertencem à S3, ainda não implementada.

Python 3.11.9, uv 0.9.5, Node 24.22.1 LTS. Dependências efetivas nos locks. Código Apache-2.0; corpus/modelos têm atribuições/licenças próprias. Não redistribuir pesos ou dados como se fossem abrangidos pela licença do código.

Na raiz, com `.env` local já configurado (nomes em `.env.example`), prepare explicitamente o modelo; o build e a comparação não baixam pesos:

```powershell
$env:PYTHONPATH = (Resolve-Path core/src).Path
cd core
uv sync --frozen --group dev
python scripts/prepare_model.py
cd ..
docker compose config --quiet
docker compose build
docker compose up -d
```

Use o Python de `core/.venv/Scripts/python.exe` quando houver outro interpretador no PATH. O cache fica em `core/models/`, fora do Git; a revisão fixa consta no adaptador e em `hts-model.json`. A inferência do container fica offline. Alterar a revisão exige decisão registrada.

O web atende somente em `http://127.0.0.1:3000`, com POST multipart em `/api/comparisons`: `source` e `suspect` são arquivos, `contract_version=1.0`, `mode=hybrid` ou `lexical`. A resposta inclui `id` para GET `/api/comparisons/{id}`. O core fica na rede interna; não expor estas rotas de desenvolvimento à rede externa. Sem modelo, o híbrido fica indisponível e a comparação lexical é identificada separadamente.

```powershell
docker compose exec -T core python -m pytest -q
docker compose exec -T web npm test
docker compose exec -T web npm run typecheck
core/.venv/Scripts/python.exe scripts/seed-development.py
```

O coordenador chama o web, único dono das coleções `documents`, `comparisons` e `reports` necessárias agora. Seeds fixos são idempotentes e não apagam registros. O namespace é `hts_s2_development`; mudanças de política/identidade exigem versão nova do seed, preservando a anterior. Persistência usa inserções idempotentes sem transação; em falha parcial, a API informa indisponibilidade e não apresenta salvamento como concluído.

Fusão: `F = 0.6*max(0,C) + 0.4*L`; C bruto preservado. O índice usa máximos por sentença, ponderados por palavras nos dois sentidos. O húngaro maximiza outra grandeza (soma não ponderada de F), somente para explicar correspondências. Classes usam o melhor F por sentença do suspeito, com reutilização da fonte; igualdade textual, edição estrutural, corte e sinal semântico seguem Q5-V2 provisória. Igualdade de textos não significa igualdade dos arquivos e não força nota 100. “Trecho inserido”, siamês e fusão aprendida estão indisponíveis.

Limites e limiares em `core/configs/comparison.json`; o hash de configuração inclui os arquivos de implementação. O IDF provisório permanece congelado, com versão histórica e descritor observado de tabela/pipeline/modelo; não é atestação retroativa de construção. No futuro experimental, ajustar IDF só no treino.

Testes e seeds são desenvolvimento, sem validação de hipóteses ou desempenho científico. Não há OCR, busca online, acervo/FAISS ou deploy. Evidências privadas em TCC; não executar operações Git de publicação automaticamente.
