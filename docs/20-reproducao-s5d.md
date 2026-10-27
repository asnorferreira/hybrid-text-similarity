# Reprodução privada S5D em Docker/CPU

Esta receita consome o pacote privado `s5d-private.tar.gz` fornecido pelo autor,
na revisão identificada pelo recibo e pelo manifesto SHA-256 que o acompanha.
Um clone público contém código/locks, mas não dados, pesos, respostas humanas ou
evidências. O pacote é uma exportação com hash da árvore de trabalho, incluindo
alterações locais; não é um clone do commit publicado. Seu manifesto identifica
cada arquivo. O pacote conserva o claim P10: não executar `experiment evaluate`,
`training run`, calibração ou geração de novos dados para reproduzir resultados.
Conferir as métricas a partir das predições salvas.

## Pré-requisitos e restauração

Docker Engine com Compose v2 e CPU x86_64; rede somente no build inicial das
imagens/dependências. Nenhuma API paga, conta externa ou GPU. Python 3.11.9,
uv 0.9.5 e Node 24.22.1 vêm das imagens; dependências dos locks. O ambiente
completo inclui editor/host: o limite de 2 GB vale para o core, não para a stack.
Nesta máquina de 6,6 GiB, executar suíte, build e navegador sequencialmente;
parar os serviços antes de testes pesados. Não executar H3 com outras cargas.

Na raiz do código recebido, use uma imagem de preparação construída do Dockerfile
versionado (o preparo não requer os recursos privados):

```bash
docker build -f core/Dockerfile -t hts-s5d-prepare:local .
# Colocar somente o pacote recebido em /CAMINHO/DO/PACOTE.
# /CAMINHO/DESTINO é uma pasta nova/vazia, diferente do projeto original.
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/scripts:/tools:ro" \
  -v /CAMINHO/DO/PACOTE:/bundle:ro \
  -v /CAMINHO/DESTINO:/target \
  hts-s5d-prepare:local python /tools/reproduction.py restore \
  --bundle /bundle/s5d-private.tar.gz --target /target
cd /CAMINHO/DESTINO
```

A restauração recusa sobrescrita e arquivos sem entrada no manifesto; confere
tamanho e SHA-256 de todos os arquivos. Não execute comandos no projeto original.
O pacote contém modelo-base, checkpoints/exports, IDFs, corpus raw fixado,
fixtures, dataset, anotações científicas, claims, referência/P10 e evidências
selecionadas P0–P11 e da correção do CI. A identidade pré-P10 do código está preservada na P9;
ela não deve ser confundida com a integração posterior.

## Build e verificações sem serviços

Após restaurar e entrar na pasta nova, a execução recomendada é:

```bash
bash scripts/check_reproduction.sh
```

Para outra tentativa, restaure novamente em um destino vazio e selecione um
projeto Compose novo, preservando a cópia e o volume anteriores:

```bash
HTS_REPRODUCTION_PROJECT=hts_s5d02 bash scripts/check_reproduction.sh
```

O pacote conserva todos os arquivos dos diretórios privados explícitos,
inclusive caches históricos referenciados pelos selos. A integridade dos selos
deve ser conferida na cópia restaurada antes das suítes e novamente na entrega.

O script executa sequencialmente build, suíte Core, Web/tipos, recarga dos seis
sistemas H1/Platt/H2 em validação, recálculo P10, stack, seeds/integração,
segurança, persistência/retomada, E2E ativos e três indisponibilidades reais.
Cada comando, código de saída, XML e log fica em
`core/artifacts/ci/results/s5d/`. Recusa reutilizar essa pasta. Se falhar,
preservar a cópia e investigar o log; não continuar chamando a tentativa de
aprovada. Não executar o script sobre serviços S5D já ativos.

Os comandos abaixo detalham a mesma receita para execução manual alternativa;
não devem ser repetidos depois da via automatizada na mesma cópia.

Todos os comandos seguintes partem da raiz restaurada. A variável shell `dc`
abaixo é uma função local, não uma instalação no host:

```bash
dc() { docker compose -p hts_s5d -f docker-compose.ci.yml -f docker-compose.reproduction.yml "$@"; }
dc config --quiet
dc build core
dc build web
dc build browser
mkdir -p core/artifacts/ci/results/s5d

dc run --rm --no-deps \
  -e HTS_RG01_OBSERVED=/results/s5d/rg01-observado.json \
  core python -m pytest -q -o cache_dir=/tmp/pytest-cache \
  --junitxml=/results/s5d/core.xml

dc run --rm --no-deps web sh -c 'npm test && npm run typecheck'
```

O override usa Mongo 7.0.45-jammy por digest e **volume próprio** devido à
incompatibilidade Mongo 8.0.34/kernel Linux ≥6.19. Não reutiliza/converte volumes
Mongo 8. Core 2 CPUs/2.000.000.000 bytes/swap zero; web 1 CPU/1.000.000.000 bytes;
Mongo 1 CPU/700.000.000 bytes; navegador 1 CPU/700.000.000 bytes. Os mounts
`core/artifacts/ci/raw` e `core/models/<revisão>` são recursos obrigatórios.

## Integração e modelos ativos

```bash
# A cópia ativa é gerada somente no destino restaurado; hashes não mudam.
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/core:/target" hts-s5d-prepare:local python -c \
  'import json,pathlib; p=pathlib.Path("/target"); v=json.loads((p/"configs/trained_models.json").read_text()); v["enabled"]=True; (p/"artifacts/trained_models.active.json").open("x").write(json.dumps(v,indent=2))'
dca() { docker compose -p hts_s5d -f docker-compose.ci.yml -f docker-compose.reproduction.yml -f docker-compose.models.yml "$@"; }
dca up -d --wait --wait-timeout 180 mongo core web
# Integração cria conta de desenvolvimento e verifica seeds idempotentes.
dca exec -T web sh -c 'npm run integration && npx tsx scripts/integration-trained.ts && npm run test:security'
dca run --rm --no-deps \
  -e HTS_E2E_OUTPUT=/results/s5d/e2e-ativos \
  browser npx playwright test e2e/system.spec.ts e2e/equivalence.spec.ts e2e/plan16.spec.ts
```

O índice/matrizes/classes Q5-V2 não mudam. H1/H2/P1 aparecem em campos próprios,
com versões/hashes; "probabilidade de derivação" não é índice semântico.
A configuração separada preserva o hash científico de `comparison.json`.
H2 usa o forward e o pooling nativos do checkpoint (média ponderada seguida de
L2); o app SBERT normaliza cada janela antes da média. Essa diferença impede
interpretar entradas multijanela como ablação isolada da cabeça. O encoder
compartilhado permanece congelado; cache de embeddings nativo limitado a 1 MiB
e 128 entradas, com diagnósticos temporários limpos por requisição.
Recarga dos seis sistemas H1, Platt e H2 utiliza somente train/validation ou
fixtures de desenvolvimento; não repete P10. O verificador e os comandos reais
estão na evidência P12, junto ao recálculo das predições salvas.

```bash
# Executar com a stack parada, antes de subi-la, na via manual.
dc run --rm --no-deps -v "$PWD:/snapshot:ro" core \
  python /snapshot/scripts/check_saved_reproduction.py \
  --root /snapshot --out /results/s5d/reload-models.json
```

Para os cenários reais de ausência, use overrides que mudam **caminhos de
configuração**, preservando todos os arquivos:

```yaml
# optional-missing.yml, criado no destino restaurado
services:
  core:
    environment:
      HTS_TRAINED_MODELS_CONFIG: /app/artifacts/trained_models.missing.json
```

Configuração ativa válida apontando para artefato inexistente é o caso E2E-04.
O runner da evidência P12 cria essa cópia, recria somente o core e executa
`trained-unavailable.spec.ts`. Modelo-base ausente usa `HTS_MODEL_PATH=/missing`
e `unavailable.spec.ts` com `HTS_FAILURE_KIND=model`; core parado usa o mesmo
spec com `HTS_FAILURE_KIND=core`. Cada cenário conserva logs e não deve salvar
resultado fictício. Restaurar a configuração ativa ao terminar.

```bash
dca stop
```

Não usar `down -v`, apagar volumes ou substituir hashes para aceitar outro peso.
Para inspeção manual em `http://127.0.0.1:3000`, configurar o `HTS_APP_ORIGIN`
para esse mesmo endereço e recriar a web; a receita de testes usa `http://web:3000`
internamente. Conta/senha de desenvolvimento são criadas localmente, nunca nos
arquivos de evidência. Seeds não atribuem dados sem dono a outro usuário.

## Licenças e alcance

Código Apache-2.0: [LICENSE](../LICENSE), [NOTICE](../NOTICE),
[CITATION.cff](../CITATION.cff). Modelo-base fixado:
[sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42),
metadado Apache-2.0 em `hts-model.json` e model card incluídos no pacote.
Wikipédia PT: CC BY-SA 4.0, revisões/autores/históricos nos
[manifestos](../core/data/refcorpus/manifest.json). Dados S4 conservam as fontes,
atribuições e limitações no próprio pacote. A licença do código não relicencia
dados, pesos, artigos, respostas humanas nem documentação de terceiros.

H1/H2 não foram sustentadas na referência humana parcial finita/dependente.
P1 piorou Brier/log-loss; as probabilidades são exploratórias. E2 adaptado de A3,
OSA restrita e a adaptação de A7 têm limites explicitados no TCC. Não há OCR,
prova de plágio, inferência populacional ou garantia de latência fora da máquina
medida. H3 segue o [protocolo congelado](h3-protocol.json); repetir carga é uma
nova medição de engenharia, nunca uma nova avaliação científica P10.
Os tempos H3 são da chamada completa à Web, com persistência e modelos ativos.
O campo auxiliar `Server-Timing: compare` cobre somente a comparação Q5-V2 base,
sem o enriquecimento opcional; não permite decompor o custo dos modelos.
