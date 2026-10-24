# hybrid-text-similarity

Comparação local de dois arquivos PT-BR (PDF com texto, DOCX, TXT), por sentenças. O índice de similaridade do projeto vai de 0 a 100; não é Pearson/Spearman nem prova de plágio. A S3 acrescenta cadastro/login local, autorização por proprietário, interface integrada, histórico próprio e impressão do relatório. Testes de desenvolvimento não validam hipóteses científicas.

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

Abra `http://127.0.0.1:3000` usando esse endereço exato, crie uma conta de desenvolvimento (senha de 12 a 128 unidades UTF-16) e envie os dois arquivos ou cole dois textos. Sem verificação de e-mail, recuperação de senha ou provedor externo. A sessão dura até oito horas, com cookie HttpOnly/SameSite Strict; Secure em HTTPS. HTTP é exceção local restrita. Não há sessão em localStorage.

As rotas `/api/comparisons` e `/api/comparisons/{id}` exigem autenticação; mutações também exigem Origin exato, header customizado e CSRF da sessão. Proprietário vem do servidor. O formulário aceita `source`/`suspect` ou `source_text`/`suspect_text`, `contract_version=1.0`, modo `lexical`, `semantic`, `hybrid` ou `all`, e ID opcional para retentativa idempotente. Semântico/todos compartilham uma chamada híbrida, exibindo os componentes separados. Core e Mongo ficam em rede interna sem portas publicadas. `MONGO_PORT` antigo não controla mais uma porta pública. Sem modelo, o híbrido fica indisponível e o lexical continua identificado separadamente.

```powershell
docker compose exec -T core python -m pytest -q
docker compose exec -T web npm test
docker compose exec -T web npm run typecheck
```

Web é o único dono das coleções `users`, `sessions`, `rate_limits`, `documents`, `comparisons` e `reports`. O namespace atual é `hts_s3_development`; dados anteriores S2/sem dono são preservados, sem atribuição automática nem exposição no histórico. Seeds são fixos por proprietário e versão, idempotentes e não apagam registros. O coordenador `scripts/seed-development.py` exige `HTS_SEED_EMAIL` e `HTS_SEED_PASSWORD` de conta existente no ambiente do comando; não colocar valores em logs/linha de comando ou evidências. Persistência usa inserções idempotentes sem transação; em falha parcial, a API informa indisponibilidade e não apresenta salvamento como concluído.

Limites operacionais: 5 MiB por arquivo, corpo multipart até 10 MiB + 64 KiB; demais limites no core. DOCX passa por preflight ZIP/XML com expansão limitada e DTD recusada. Rate limiting usa Mongo: autenticação 60 tentativas globais/15 minutos e 10 por conta/15 minutos, comparações 10 por usuário/minuto, leituras 120 por usuário/minuto. Concorrência máxima de duas comparações é por processo web. Timeout do cliente não confirma cancelamento do servidor; a interface preserva o ID para retentativa da mesma entrada.

Textos e nomes são apresentados como texto, sem HTML confiável. O mapa usa índices reais de sentença e distingue melhores pares de alinhamento exclusivo. Impressão mostra a janela identificada do mapa e a lista completa de melhores pares; não anota o PDF original. Tempos são de engenharia, com etapas compartilhadas; RSS é pico de vida do processo inteiro, sem atribuição individual a algoritmos ou GPU.

Fusão: `F = 0.6*max(0,C) + 0.4*L`; C bruto preservado. O índice usa máximos por sentença, ponderados por palavras nos dois sentidos. O húngaro maximiza outra grandeza (soma não ponderada de F), somente para explicar correspondências. Classes usam o melhor F por sentença do suspeito, com reutilização da fonte; igualdade textual, edição estrutural, corte e sinal semântico seguem Q5-V2 provisória. Igualdade de textos não significa igualdade dos arquivos e não força nota 100. “Trecho inserido”, siamês e fusão aprendida estão indisponíveis.

Limites e limiares em `core/configs/comparison.json`; o hash de configuração inclui os arquivos de implementação. O IDF provisório permanece congelado, com versão histórica e descritor observado de tabela/pipeline/modelo; não é atestação retroativa de construção. No futuro experimental, ajustar IDF só no treino.

Testes e seeds são desenvolvimento, sem validação de hipóteses ou desempenho científico. Não há OCR, busca online, acervo/FAISS ou deploy. Evidências privadas em TCC; não executar operações Git de publicação automaticamente.

## Validação S3 e CI

O workflow atual prepara ambientes fixos, restaura recursos rastreáveis e executa core, testes/tipos web, integração/persistência, negativas de segurança e Playwright com serviços reais, incluindo modelo ausente e core parado. Browser usa Playwright1.64.1/Chromium fixado; Tailwind/PostCSS4.3.3 estão no lock. Auditorias npm/pip consultam avisos conhecidos; pacotes fora do índice podem não ser cobertos e precisam de avaliação explícita. Ausência de alertas não prova ausência de vulnerabilidades.

O [run40118062459](https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40118062459) foi consultado: success para o estado **S2** head `ecb14086dde926576e9563df32befc9a74e04bcc`, checkout merge `028737cfd50a8b04494571bc1be3e076a1b8a02e`, árvores equivalentes conferidas. Não valida as alterações S3. **Workflow S3 preparado; execução remota S3 não realizada nesta tarefa.**

Gatilhos continuam exclusivamente push em `main` e PR destinado à `main` com `types: [opened]`. Push posterior no PR já aberto não dispara nova execução; não fechar/reabrir PR nem ampliar gatilhos automaticamente. Publicação e conferência remota ficam a cargo do autor, após revisão. Não houve commit/push/publicação pelo agente.

CI usa banco isolado `hts_ci_s3`, sem `.env` do autor ou arquivos privados, e fixtures determinísticas do gerador v2. Artifacts permitidos: JUnit sanitizado, versões/identidades e auditorias; sem documentos, senhas, cookies, traces ou banco. O reporter também redige anexos automáticos de texto/JSON, inclusive snapshots de erro; trace off sozinho não impede retenção de valores de formulário. Carga exploratória é comando separado `npm run load`, com protocolo/ambiente/saídas próprios; não é teste determinístico ou resultado H3. Não executá-la contra dados ou serviços de terceiros.

## Histórico — preparação anterior da CI S2 em 2026-10-24

Os parágrafos abaixo registram o estado anterior à consulta remota e à S3. Suas pendências históricas não substituem a seção atual acima; falhas preservadas não têm causa retroativamente demonstrada pelo run posterior aprovado.

Workflow preparado; validação no GitHub ainda não executada.

`.github/workflows/validation.yml` executa em push na `main` e abertura (`opened`) de PR destinado à `main`. Push em outra branch, criação de branch e commits posteriores num PR aberto não disparam execução. Essa política é intencional: um resultado antigo não valida automaticamente commits novos. O workflow precisa estar na branch antes da abertura do PR que o executará. Se o PR já existir, publicar a atualização não cria esse evento; não ampliar gatilhos ou fechar/reabrir PR automaticamente.

As actions estão fixadas por SHA, com `contents: read` e checkout sem credenciais persistidas. A validação usa um único job Ubuntu e os ambientes Docker fixados (Python3.11.9/uv0.9.5 e Node24.22.1), `uv sync --frozen` e `npm ci`, evitando instalar outra pilha nos jobs. O build web executa `npm run build`; depois rodam testes/typecheck e integração real.

`docker-compose.ci.yml` é independente do Compose de desenvolvimento: Mongo interno sem porta publicada, namespace `hts_ci_s2`, sem banco externo/credenciais do autor. Recursos ficam em `core/artifacts/ci/`, fora do Git. O CI parte sem `.env`, corpus raw, ambientes ou pesos: restaura as revisões congeladas, verifica hashes sem reconstruir IDF, instala spaCy pelo lock e prepara explicitamente o modelo fixo antes da inferência offline. Falhas nesses passos impedem aprovação; JUnit vazio, com falha ou skip/xfail é rejeitado.

As fixtures PDF/DOCX são geradas por `core/scripts/gerar_fixtures_ci.py`, com conteúdo de desenvolvimento declarado e bytes determinísticos, sem amostras privadas. O script real de integração verifica parsing, APIs, persistência/leitura e seed duplicado. `integration-failure.ts` restringe-se ao Mongo/namespace CI, provoca rejeição de um relatório, verifica falha explícita/registros parciais não apresentados como concluídos e restaura o validador antes do retry idempotente. Não exclui dados.

Artifacts limitam-se a JUnit e identificação técnica de versões/evento/SHAs; não incluem documentos privados, banco, caches ou pesos. Downloads e tempos de CI não são resultados científicos. A autenticação/interface da S3 ainda não foi implementada.

Na revisão local, o checkout público isolado passou em 220 testes Linux e no fluxo integrado antes do último reforço dos schemas. Após esse reforço, Windows passou em 220 testes e web em quatro; a repetição Linux registrou duas falhas de deadline e dois erros de inicialização semântica, durante uma rodada em que a API do Docker Desktop passou a responder 500. Causa não determinada; não se alteraram deadlines/testes para aprovar. Revalidar sequencialmente o estado final quando o Docker estiver operacional. Isso permanece separado da execução futura no GitHub.
