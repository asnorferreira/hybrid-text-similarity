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

## CI — preparação em 2026-10-24

Workflow preparado; validação no GitHub ainda não executada.

`.github/workflows/validation.yml` executa em push na `main` e abertura (`opened`) de PR destinado à `main`. Push em outra branch, criação de branch e commits posteriores num PR aberto não disparam execução. Essa política é intencional: um resultado antigo não valida automaticamente commits novos. O workflow precisa estar na branch antes da abertura do PR que o executará. Se o PR já existir, publicar a atualização não cria esse evento; não ampliar gatilhos ou fechar/reabrir PR automaticamente.

As actions estão fixadas por SHA, com `contents: read` e checkout sem credenciais persistidas. A validação usa um único job Ubuntu e os ambientes Docker fixados (Python3.11.9/uv0.9.5 e Node24.22.1), `uv sync --frozen` e `npm ci`, evitando instalar outra pilha nos jobs. O build web executa `npm run build`; depois rodam testes/typecheck e integração real.

`docker-compose.ci.yml` é independente do Compose de desenvolvimento: Mongo interno sem porta publicada, namespace `hts_ci_s2`, sem banco externo/credenciais do autor. Recursos ficam em `core/artifacts/ci/`, fora do Git. O CI parte sem `.env`, corpus raw, ambientes ou pesos: restaura as revisões congeladas, verifica hashes sem reconstruir IDF, instala spaCy pelo lock e prepara explicitamente o modelo fixo antes da inferência offline. Falhas nesses passos impedem aprovação; JUnit vazio, com falha ou skip/xfail é rejeitado.

As fixtures PDF/DOCX são geradas por `core/scripts/gerar_fixtures_ci.py`, com conteúdo de desenvolvimento declarado e bytes determinísticos, sem amostras privadas. O script real de integração verifica parsing, APIs, persistência/leitura e seed duplicado. `integration-failure.ts` restringe-se ao Mongo/namespace CI, provoca rejeição de um relatório, verifica falha explícita/registros parciais não apresentados como concluídos e restaura o validador antes do retry idempotente. Não exclui dados.

Artifacts limitam-se a JUnit e identificação técnica de versões/evento/SHAs; não incluem documentos privados, banco, caches ou pesos. Downloads e tempos de CI não são resultados científicos. A autenticação/interface da S3 ainda não foi implementada.

Na revisão local, o checkout público isolado passou em 220 testes Linux e no fluxo integrado antes do último reforço dos schemas. Após esse reforço, Windows passou em 220 testes e web em quatro; a repetição Linux registrou duas falhas de deadline e dois erros de inicialização semântica, durante uma rodada em que a API do Docker Desktop passou a responder 500. Causa não determinada; não se alteraram deadlines/testes para aprovar. Revalidar sequencialmente o estado final quando o Docker estiver operacional. Isso permanece separado da execução futura no GitHub.
