# hybrid-text-similarity

## Estado atual e entrega científica

Plano [16](docs/16-plano-conclusao-e-testes.md) auditado em 2026-10-27. H1 e H2
foram treinadas em train/validation com referência automatizada dependente. H2
completou 8 épocas/56 passos no teto de 2 GB, swap zero; selecionado recarregado
com as mesmas 13 predições. Na validação, Spearman do siamês 0,3212 e do SBERT
0,8660. Esses números não são avaliação do teste nem confirmação das hipóteses.

A entrega integral ainda requer PH2/referência humana D5, S5C, integração dos
modelos no app, H3/D6 e reprodução limpa S5D. Os modelos científicos não são
ativados automaticamente. CI local corrigida; CI remoto da revisão publicada
continua a cargo do autor. Dados, modelos e evidências científicos são privados,
entregues separadamente; um clone público não contém esses artefatos.

Linux com Docker Engine: o procedimento de recursos está em
[19](docs/19-h2-limite-2gb.md), e a ambientação do editor em
[17](docs/17-ambiente-editor.md). O executor [H2](core/scripts/run_h2_2gb.sh) é
exclusivo do orçamento de treino; não limita a RAM total do host/stack/editor.
**Não executar um novo `run` científico:** a tentativa H2 autorizada já foi
consumida. Readiness e recarga não autorizam retreino nem abertura do teste.

Os registros seguintes preservam o histórico de cada etapa; frases antigas como
“S5 não iniciada” e comandos Windows pertencem àquelas execuções. Estado vigente,
critérios de aceite e próximos passos estão no plano 16.

<!-- S5B-CURRENT -->
## Histórico — estado após P7, 2026-10-26

O bloqueio H2 deste registro foi superado pela P8 r4 em 2026-10-27. O estado atual está no início deste README e no plano 16; o claim H2 já foi consumido.

P0–P7 concluídas no alcance local, Docker Engine; CI remoto pendente de publicação manual. Autor aprovou D1–D4 e um reinício técnico H1, registrado antes do ajuste. H1 completa: quatro logísticas e dois baselines, 32 train/17 validation, exports recarregados com predições iguais. Platt P1 ajustado em 4.560 pares únicos de validation e recarregado com erro zero; avaliação independente indisponível por haver um único componente de dependência. Métricas de ajuste são ressubstituição. H2 ainda só fixture: P8 bloqueada com 2,38 GiB disponíveis para o mínimo de 4 GiB, sem consumir tentativa; não há garantia de suficiência por congelar o encoder. D5/D6/PH2 pendentes e teste científico fechado.

Ambiente do editor instalado e configurado; Python standard sem erros/avisos em 123 arquivos, 819 testes core e 12 web aprovados. Serviços parados, volumes e artefatos preservados; sem commit/push/publicação. Os registros anteriores de S4/S5A abaixo são históricos.

[Plano e evidências](docs/16-plano-conclusao-e-testes.md) · [H1 e calibração](TCC/evidencias/codex-p07-04/relatorio.md) · [Ambiente do editor](docs/17-ambiente-editor.md).
<!-- /S5B-CURRENT -->

<!-- S5A-HISTORICAL -->
## Registro histórico — complemento S5A, 2026-10-25

Complemento técnico S5A concluído no alcance independente: protocolo, vínculo IDF e importação corrigidos e verificados. S4 permanece encerrada operacionalmente; nenhum treinamento, calibração, carga ou avaliação preditiva do teste. Contratos científicos candidatos não significam liberação de treinamento.

Schemas de preparação corrigidos; protocolo original preservado e suplemento candidato vinculado. Seguir o protocolo e a matriz vigentes, sem início automático de S5B.

[protocolo](docs/08-protocolo-s5a.md) | [relatório](TCC/evidencias/codex-s5a-complemento-01/relatorio-final.md) | [matriz](TCC/evidencias/codex-s5a-complemento-01/matriz-prontidao.md) | [checkpoint](TCC/evidencias/codex-s5a-complemento-01/checkpoint.md) | [S5B](docs/09-prompt-s5b.md)

S5A original preservada como histórica em documentacao-anterior.zip na pasta de evidências do complemento e nas evidências codex-s5a-01. Registros abaixo são históricos das suas execuções; não atribuir a eles as correções atuais. Entrega S4: kit base e adendo-retomada-final-02.zip definitivo, com dataset separado; adendo01 é tentativa anterior preservada. ZIPs antigos não foram regenerados.
<!-- /S5A-HISTORICAL -->

<!-- S4-CLOSURE-CURRENT -->
## Registro histórico — fechamento dirigido S4, 2026-10-25

S4 encerrada para construção/entrega operacional com curadoria de extração `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`: 59 fontes/grupos, splits 41/9/9; 783 pares, 665 conteúdos, 6093 sentenças, 132 formatos sobre 44 conteúdos. Avaliação IA do próprio gerador, sem independência: 66 pares selecionados; demais não avaliados em conteúdo. Humano não realizado; sentenças apenas estruturalmente validadas; semantic_training_ready=false. IDF de treino: 41 documentos, 13673 termos; identidade `9ddb353e50c050f58cc3417f8a41763867550730e7c18c56851d4f6dd74680c6`.

Histórico `ee13c978…` e seus dados/evidências preservados. [Relatório S4 da época](TCC/evidencias/codex-s4-fechamento-01/relatorio-final.md), [contratos e condições H1–H3](TCC/evidencias/codex-s4-fechamento-01/contratos.md), [curadoria](TCC/evidencias/codex-s4-fechamento-01/politica-curadoria.md) e [checkpoint](TCC/evidencias/codex-s4-fechamento-01/checkpoint.md). Os relatos anteriores abaixo são históricos; prompts futuros permanecem sujeitos às condições vigentes. O mínimo permanece1 por célula, sem suficiência estatística; revisão/validação não são equivalência semântica. Curadoria usa raw fixado, templates limitados e exclusões registradas; não certifica toda afirmação da fonte. Defeitos originais de linguagem e apresentação contextual árabe permanecem delimitados no datasheet; clean_text_corpus_ready=false; não usar como corpus universal de texto limpo. IDF reconstruído somente de treino e separado do IDF da aplicação. Não migrar a aplicação automaticamente. H1 exige mapeamento/gabarito avaliativo; H2 construto/unidade/anotação independente/protocolo; H3 meta/carga/hardware/protocolo. São propostas científicas pendentes, sem aprovação presumida. Não iniciar S5, treinar, calibrar ou medir desempenho no teste. CI histórico é separado das verificações locais; gatilhos preservados.
Os ZIPs do dataset e do kit são entregas locais privadas. O clone público não contém esses dados, cache ou documentação TCC; obtenha o pacote local e siga o inventário/instruções de restauração. Nenhuma contratação de IA é necessária para consumir as saídas preservadas.

<!-- /S4-CLOSURE-CURRENT -->

## Estado operacional da S4

Versão sintética local congelada para derivação textual e robustez: 59 fontes/grupos, 735 pares e132 variantes de formato sobre44 conteúdos. Avaliação automatizada por IA do próprio gerador, sem revisão humana e com `semantic_training_ready=false`; não comprova plágio nem libera H2/treinamento semântico. Dados/cache/avaliações e instruções completas são entregues separadamente em pacote privado local, fora do Git/CI.

Windows e Linux:337 testes do core aprovados no estado local; fumaça com core/web/Mongo realizada somente com dados de desenvolvimento. Não são resultados científicos nem CI remoto destas alterações. IDF de treino S4 não ativado na aplicação. O pacote inclui restauração, reconstrução por raw/cache fixos e receita produtora explicitamente distinta por duas proteções de imutabilidade posteriores; não exige API/assinatura para reproduzir. Preparo inicial de dependências/modelos pode exigir rede; recursos locais têm inventário/hashes. Não há hardware mínimo medido nem instalação nova offline certificada. S5 não iniciada.

As seções seguintes mantêm contexto e comandos de desenvolvimento; instruções históricas são subordinadas a esta finalidade e às instruções privadas que acompanham a versão entregue.

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

O lexical também exige os raw do corpus provisório, conferidos contra `core/data/refcorpus/manifest.json`. Em uma cópia nova sem esses arquivos, use o recurso local verificado do pacote de entrega ou, com rede, execute a partir de `core/`: `python -m hts_core.cli restaurar-corpus --corpus data/refcorpus`. Esse comando grava raw após conferir revisão/hash; use apenas no destino novo/ausente, preservando arquivos locais existentes. Não execute `construir-idf` para restaurar: a tabela histórica já está versionada. Rede é necessária no preparo de dependências/modelo se os caches não estiverem disponíveis, sem exigir assinatura Codex ou API de geração.

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

## Dataset operacional S4 e CI

A S4 acrescenta pipeline local de dados sintéticos e testes pequenos de desenvolvimento, incluídos na suíte core. O grupo `dataset` instala somente o driver Mongo necessário; geração pela sessão Codex usa saídas preservadas. Gemini/google-genai não é requisito obrigatório. O grupo opcional `llm-api` é histórico/preparado e não é instalado pelo Docker/CI padrão; nenhuma API paga está autorizada.

Comandos de desenvolvimento, a partir de `core/` (usar destinos novos; artefatos existentes não são sobrescritos):

```powershell
uv sync --frozen --group dev --group dataset
$env:PYTHONPATH = "src"
uv run --frozen --group dataset python -m hts_core.cli dataset --help
uv run --frozen --group dataset python -m pytest tests/test_dataset_s4.py -q
uv run --frozen --group dataset python -m hts_core.cli dataset piloto --config configs/dataset_pilot.json --corpus data/refcorpus --out artifacts/my-pilot
uv run --frozen --group dataset python -m hts_core.cli dataset validar --dataset artifacts/my-pilot
uv run --frozen --group dataset python -m hts_core.cli dataset revisao --dataset artifacts/my-pilot --seed 20261024 --pilot-count 8 --out artifacts/my-review
```

O corpus provisório já foi exposto no desenvolvimento; esse comando não produz teste experimental. Coleta, preparação de fontes, pares, formatos, cache, revisão e IDF têm artefatos/identidades separados. O validador confere integridade, grupos/splits, proveniência e frações r; não certifica preservação semântica. `r_by_source` conserva numeradores/denominadores e admite multiorigem. PDF/DOCX/TXT do mesmo conteúdo não são observações independentes. Dados/raw/cache/revisão/exports ficam privados em `core/artifacts/`, fora do Git e do contexto Docker. Não enviar ao CI dados finais, chaves ou geração paga.

O novo IDF usa exclusivamente fontes de treino e não substitui o IDF provisório da demonstração. Importação Mongo exige namespace `hts_dataset_`, somente pelo core; não usa coleções de usuários. Idempotência é por versão/ID, conteúdo real e hash; divergências deixam `integrity_conflict`. Falha parcial conserva `importing` e admite retomada, sem transação ou exclusão. Um piloto selado continua sendo desenvolvimento.

O complemento S4 separa congelamento técnico operacional de prontidão científica. `frozen_operational_derivation` destina-se a derivação textual e robustez de transformações, com avaliação IA identificada, dependente do gerador, e `semantic_training_ready=false`. Revisão humana não foi realizada. C6 é reescrita guiada por frase/elementos, sem classe semântica automática. C3 é composição de comprimento fixo, identificador histórico `insert`, sem alegar inserção em documento maior. r é fração de derivação por fonte, não gabarito semântico. Não há treino, calibração ou avaliação preditiva no teste nesta S4; H1–H3 não foram validadas.

O professor recebe separadamente o pacote privado local de dados/cache e seu manifesto; esses arquivos não estão no GitHub. Após restaurar esse pacote, exemplos a partir de `core/`, com `PYTHONPATH=src` e dependências do lock já instaladas:

```powershell
python -m hts_core.cli dataset importar --bundle artifacts/entrega/dataset.zip --out artifacts/restored-01
python -m hts_core.cli dataset cobertura --dataset artifacts/restored-01
python scripts/rebuild_dataset_operational.py --collection artifacts/entrega/inputs/collection --plan artifacts/entrega/inputs/fixed-plan.json --config configs/dataset_operational.json --cache artifacts/entrega/cache --exclusions artifacts/entrega/inputs/content-exclusions.json --out artifacts/rebuilt-01
```

Use o interpretador do ambiente do projeto. Em Linux, definir `export PYTHONPATH=src`; em PowerShell, `$env:PYTHONPATH="src"`. Destinos precisam ser novos. Reconstrução usa raw/cache/configuração e exclusões documentadas, não nova geração LLM, e não exige assinatura Codex ou API. Cache rejeitado fica preservado; exclusão por avaliação gera versão nova e não é erro técnico de cache. Para preparar avaliações, `dataset avaliacao-ia`; para importar respostas reais, `dataset importar-avaliacao-ia`. Congelamento operacional aceita `--reproduction` com o relatório verificado e usa a autorização já registrada; não exige que o autor edite JSON complexo ou certifique código. Pacote humano é separado e permanece não realizado se não preenchido.

Preparo inicial pode exigir rede para dependências, corpus e modelos; inferência usa o modelo local fixado, e a reconstrução do dataset usa o cache entregue. Falta de raw/cache/fonte/modelo/driver exige preparar o recurso indicado, sem substituições silenciosas. Fontes Noto Sans e Noto CJK têm arquivos oficiais OFL separados em `core/assets/fonts/`; símbolos não são removidos para aprovar PDF. Não há requisito mínimo de hardware medido nem garantia de que qualquer máquina basta. Versões, plataformas realmente executadas, contagens, limitações e hashes constam no datasheet privado de cada entrega.

O CI remoto anterior não valida alterações locais deste complemento. Os gatilhos e a política de privacidade permanecem iguais; as execuções locais atuais são registradas nas evidências privadas. Os parágrafos seguintes preservam o contexto histórico da implantação do workflow.

O workflow atual prepara ambientes fixos, restaura recursos rastreáveis e executa core, testes/tipos web, integração/persistência, negativas de segurança e Playwright com serviços reais, incluindo modelo ausente e core parado. Browser usa Playwright1.64.1/Chromium fixado; Tailwind/PostCSS4.3.3 estão no lock. Auditorias npm/pip consultam avisos conhecidos; pacotes fora do índice podem não ser cobertos e precisam de avaliação explícita. Ausência de alertas não prova ausência de vulnerabilidades.

O [run40118062459](https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40118062459) foi consultado: success para o estado **S2** head `ecb14086dde926576e9563df32befc9a74e04bcc`, checkout merge `028737cfd50a8b04494571bc1be3e076a1b8a02e`, árvores equivalentes conferidas. Não valida as alterações S3. **Workflow S3 preparado; execução remota S3 não realizada nesta tarefa.**

Gatilhos continuam exclusivamente push em `main` e PR destinado à `main` com `types: [opened]`. Push posterior no PR já aberto não dispara nova execução; não fechar/reabrir PR nem ampliar gatilhos automaticamente. Publicação e conferência remota ficam a cargo do autor, após revisão. Não houve commit/push/publicação pelo agente.

CI usa banco isolado `hts_ci_s3`, sem `.env` do autor ou arquivos privados, e fixtures determinísticas do gerador v2. Artifacts permitidos: JUnit sanitizado, versões/identidades e auditorias; sem documentos, senhas, cookies, traces ou banco. O reporter também redige anexos automáticos de texto/JSON, inclusive snapshots de erro; trace off sozinho não impede retenção de valores de formulário. Carga exploratória é comando separado `npm run load`, com protocolo/ambiente/saídas próprios; não é teste determinístico ou resultado H3. Não executá-la contra dados ou serviços de terceiros.

## Histórico — preparação anterior da CI S2 em 2026-10-24

Os parágrafos abaixo registram o estado anterior à consulta remota e à S3. Suas pendências históricas não substituem a seção atual acima; falhas preservadas não têm causa retroativamente demonstrada pelo run posterior aprovado.

Workflow preparado; validação no GitHub ainda não executada.

`.github/workflows/validation.yml` executa em push na `main` e abertura (`opened`) de PR destinado à `main`. Push em outra branch, criação de branch e commits posteriores num PR aberto não disparam execução. Essa política é intencional: um resultado antigo não valida automaticamente commits novos. O workflow precisa estar na branch antes da abertura do PR que o executará. Se o PR já existir, publicar a atualização não cria esse evento; não ampliar gatilhos ou fechar/reabrir PR automaticamente.

As actions estão fixadas por SHA, com `contents: read` e checkout sem credenciais persistidas. A validação usa um único job Ubuntu e os ambientes Docker fixados (Python 3.11.9/uv0.9.5 e Node24.22.1), `uv sync --frozen` e `npm ci`, evitando instalar outra pilha nos jobs. O build web executa `npm run build`; depois rodam testes/typecheck e integração real.

`docker-compose.ci.yml` é independente do Compose de desenvolvimento: Mongo interno sem porta publicada, namespace `hts_ci_s2`, sem banco externo/credenciais do autor. Recursos ficam em `core/artifacts/ci/`, fora do Git. O CI parte sem `.env`, corpus raw, ambientes ou pesos: restaura as revisões congeladas, verifica hashes sem reconstruir IDF, instala spaCy pelo lock e prepara explicitamente o modelo fixo antes da inferência offline. Falhas nesses passos impedem aprovação; JUnit vazio, com falha ou skip/xfail é rejeitado.

As fixtures PDF/DOCX são geradas por `core/scripts/gerar_fixtures_ci.py`, com conteúdo de desenvolvimento declarado e bytes determinísticos, sem amostras privadas. O script real de integração verifica parsing, APIs, persistência/leitura e seed duplicado. `integration-failure.ts` restringe-se ao Mongo/namespace CI, provoca rejeição de um relatório, verifica falha explícita/registros parciais não apresentados como concluídos e restaura o validador antes do retry idempotente. Não exclui dados.

Artifacts limitam-se a JUnit e identificação técnica de versões/evento/SHAs; não incluem documentos privados, banco, caches ou pesos. Downloads e tempos de CI não são resultados científicos. A autenticação/interface da S3 ainda não foi implementada.

Na revisão local, o checkout público isolado passou em 220 testes Linux e no fluxo integrado antes do último reforço dos schemas. Após esse reforço, Windows passou em 220 testes e web em quatro; a repetição Linux registrou duas falhas de deadline e dois erros de inicialização semântica, durante uma rodada em que a API do Docker Desktop passou a responder 500. Causa não determinada; não se alteraram deadlines/testes para aprovar. Revalidar sequencialmente o estado final quando o Docker estiver operacional. Isso permanece separado da execução futura no GitHub.
