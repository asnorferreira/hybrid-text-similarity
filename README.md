# hybrid-text-similarity

Comparação local de textos PT-BR por sentenças, com TF-IDF, SBERT multilíngue,
fusão fixa Q5-V2, cadastro, histórico por proprietário e impressão. Aceita PDF
com texto, DOCX, TXT e texto colado. O índice de 0 a 100 não é correlação nem
prova de plágio. Não há OCR, busca online, acervo/FAISS ou deploy automático.

## Estado científico e evidências

P9/P10 concluídas em 2026-10-27: dois códigos de anotador, independência humana
**declarada**, identidade não autenticada. Referência parcial de 96 pares;
95 H1 e 82 H2 elegíveis. Avaliação científica única preservada, sem retreino,
recalibração, escolha posterior ou repetição de inferência:

| Hipótese | Resultado na referência parcial | Interpretação |
| --- | --- | --- |
| H1 | Fusão macro-F1 0,4104104104; lexical 0,4173913043; semântico 0,4090909091 | Não sustentada |
| H2 | Spearman siamês 0,1823451914; SBERT 0,8166448555 | Não sustentada |
| P1 | Platt piorou Brier/log-loss; ECE menor | Não demonstra ganho global de calibração |

Conjunto finito dependente, sem inferência populacional ou bootstrap de linhas.
P1 usa ancestralidade sintética dos 96 pares selecionados, não notas semânticas
humanas nem todo o split. Textos/formatos derivados não são observações
independentes. A3 tem adaptação lexical, OSA é Damerau–Levenshtein restrita,
A7 usa encoder congelado e cabeça MLP revisada; não alegar reprodução integral
dos artigos. Detalhes no [plano 16](docs/16-plano-conclusao-e-testes.md).

Integração P11 e reprodução P12 concluídas localmente, com E2E-01–09,
suítes e recargas aprovadas. H3 não sustentada em todos os cenários obrigatórios.
[Matriz final e evidências](TCC/evidencias/codex-p12-02/matriz-testes.md).
CI remoto da revisão publicada `153238e` aprovado no
[run 40512937738](https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40512937738),
após a correção de inicialização do MongoDB. O [registro do CI](TCC/evidencias/codex-ci-40512937738-01/relatorio.md)
preserva logs e artefatos. Checklist do plano16 concluído no alcance aprovado;
isso não altera os resultados negativos de H1/H2/H3. Fine-tuning integral do
encoder não integra o protocolo D2 adotado.


Reprodução final vigente: P12 tentativa02. O empacotador conserva também
arquivos históricos de cache exigidos pelos selos; a cópia nova conferiu
os selos antes/depois e repetiu todas as suítes. A tentativa anterior
e a falha de integridade da primeira entrega foram preservadas.

## Reprodução em Docker/CPU

Estudo posterior de engenharia autorizado: caches limitados ao HTTP e fila
FIFO Web, preservando índice e caminhos científicos. Nova H3 completa:
12 cenários, zero falhas e 7/8 metas obrigatórias atendidas. Com 120 sentenças,
cinco usuários e modelos ativos, p95 de 12,523 s para meta de 10 s;
hipótese posterior não sustentada integralmente. Entradas repetidas após
aquecimento favorecem cache; não extrapolar para textos inéditos.
[Protocolo próprio](docs/h3-serving-protocol.json), com fontes congeladas e
[evidências separadas](TCC/evidencias/codex-h3-melhoria-01/relatorio.md).
O CI aprovado e o pacote P12 abaixo descrevem a revisão histórica; não passam
a incluir automaticamente essas alterações locais.

A base experimental permite redigir um TCC com os resultados negativos
registrados. A prontidão para depósito ainda depende da monografia final e
do manual institucional, não localizados na inspeção. Consulte o
[parecer acadêmico](docs/17-prontidao-tcc.md) e o
[roteiro opcional de nova pesquisa H1/H2](docs/18-novo-estudo-h1-h2.md).

Siga a [receita S5D](docs/20-reproducao-s5d.md) para restaurar o pacote privado
verificado, construir as imagens, rodar as suítes, carregar seeds e percorrer os
cenários E2E. Código, configurações e locks estão no Git; dados, modelos,
respostas humanas e evidências TCC são entregues separadamente. A receita
conserva os claims científicos e recalcula as métricas das predições salvas.
Não executar novamente `training run`, `experiment evaluate` ou calibração.

Python 3.11.9, uv 0.9.5, Node 24.22.1; versões efetivas nos locks. Nenhuma API
paga, assinatura de geração ou GPU. Rede pode ser necessária no build inicial.
Core 2 CPUs/2 GB/swap zero; o limite não inclui host, editor, Mongo e web.
Executar verificações pesadas sequencialmente nesta máquina de 6,6 GiB.
Mongo 7.0.45-jammy por digest/volume próprio é a alternativa medida à
incompatibilidade Mongo 8.0.34/kernel Linux ≥6.19; não converter volumes.

Para preparar somente os recursos de desenvolvimento em um destino novo,
use o Dockerfile/Compose CI: `restaurar-corpus`, `scripts/prepare_model.py` e
`scripts/gerar_fixtures_ci.py`. O modelo e o corpus raw são conferidos por hash;
não reconstruir o IDF histórico para restaurar a aplicação. O pacote privado
S5D já fornece os recursos fixados e as fixtures. Os comandos completos e
mounts obrigatórios estão na receita acima.

## Modelos treinados opcionais

[trained_models.json](core/configs/trained_models.json) vem com `enabled=false`.
Restaure os artefatos privados, copie a configuração alterando somente a flag e
use `HTS_TRAINED_MODELS_CONFIG`, conforme a receita. O
[override opcional](docker-compose.models.yml) monta os recursos. Os hashes
não devem ser atualizados para aceitar outros pesos.

Os melhores pares Q5-V2 recebem H1, H2 e **probabilidade de derivação** em campos
próprios, com nome/versão/hash e avisos sobre os resultados negativos. O índice,
as matrizes e as classes Q5-V2 permanecem iguais. O IDF científico é exclusivo
da H1; o app conserva seu IDF. Artefato ativo ausente/incompatível retorna 503
explícito, sem índice inventado; lexical dispensa os modelos opcionais.
H2 conserva o WindowEncoder do treino: média das janelas ponderada pelos tokens
e L2 final. O SBERT do app normaliza cada janela antes da média; em entradas
multijanela essa comparação não constitui uma ablação isolada da cabeça.

A fusão é `F = 0.6*max(0,C) + 0.4*L`; cosseno bruto preservado. O índice usa
máximos ponderados por palavras nos dois sentidos. O húngaro maximiza a soma
não ponderada de F, apenas para explicar correspondências. Classes são por
melhor par de cada sentença do suspeito, permitindo reutilizar a fonte; regras
provisórias em [comparison.json](core/configs/comparison.json). Probabilidade
de classe não se converte em índice. Trecho inserido continua indisponível.

## Aplicação e segurança

Web é dona das coleções de usuários, sessões, limites, documentos, comparações
e relatórios. Core/Mongo ficam na rede interna. Conta local com senha de 12 a
128 unidades UTF-16, sem e-mail verificado/recuperação. Sessão de até oito horas,
cookie HttpOnly/SameSite Strict e Secure em HTTPS; HTTP só para desenvolvimento
local. Não há sessão em localStorage. Mutações exigem Origin exato, header
customizado e CSRF; leituras/comparações respeitam o proprietário.

Limites: 5 MiB por arquivo, multipart 10 MiB + 64 KiB, 30.000 caracteres,
120 sentenças, 4.000 caracteres/sentença; tokenização completa com limite
explícito. DOCX tem preflight ZIP/XML, expansão limitada e DTD recusada. HTML é
exibido como texto. Comparações: 10 por usuário/minuto e duas simultâneas por
processo web. Timeout no cliente não confirma cancelamento no servidor.
Retentativa conserva o ID e rejeita alteração de entrada/configuração.
Persistência parcial não é publicada; retomada é idempotente e não apaga dados.

Seeds são de desenvolvimento, por proprietário/versão; não migram dados antigos
sem dono. `npm run integration` verifica seeds idempotentes em namespace CI.
O coordenador [seed-development.py](scripts/seed-development.py) exige credenciais
de conta existente no ambiente, nunca em logs ou argumentos. A impressão inclui
data, versões e melhores pares; não anota o PDF original. RSS é pico de vida do
processo inteiro, sem atribuição por algoritmo ou GPU. H3 segue o
[protocolo congelado](docs/h3-protocol.json).

## Licenças e citação

Código [Apache-2.0](LICENSE), [NOTICE](NOTICE), [CITATION.cff](CITATION.cff).
Dados, pesos e artigos mantêm licenças próprias; a licença do código não os
relicencia. Modelo-base fixado em
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisão
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, metadado Apache-2.0 e model card no
pacote. Wikipédia PT CC BY-SA 4.0: fontes, revisões e atribuições no
[manifesto](core/data/refcorpus/manifest.json). Dados S4 conservam inventários e
limitações no pacote privado. Não publicar respostas humanas ou recursos
privados automaticamente. Commit, push, PR e publicação são manuais do autor.
