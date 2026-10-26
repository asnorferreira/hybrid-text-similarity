# Prompts por sessão — roteiro integrado para continuidade

<!-- S4-CLOSURE-CURRENT -->
## Estado vigente — fechamento dirigido S4, 2026-10-25

S4 encerrada para construção/entrega operacional com curadoria de extração `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`: 59 fontes/grupos, splits 41/9/9; 783 pares, 665 conteúdos, 6093 sentenças, 132 formatos sobre 44 conteúdos. Avaliação IA do próprio gerador, sem independência: 66 pares selecionados; demais não avaliados em conteúdo. Humano não realizado; sentenças apenas estruturalmente validadas; semantic_training_ready=false. IDF de treino: 41 documentos, 13673 termos; identidade `9ddb353e50c050f58cc3417f8a41763867550730e7c18c56851d4f6dd74680c6`.

Histórico `ee13c978…` e seus dados/evidências preservados. [Relatório vigente](../TCC/evidencias/codex-s4-fechamento-01/relatorio-final.md), [contratos e condições H1–H3](../TCC/evidencias/codex-s4-fechamento-01/contratos.md), [curadoria](../TCC/evidencias/codex-s4-fechamento-01/politica-curadoria.md) e [checkpoint](../TCC/evidencias/codex-s4-fechamento-01/checkpoint.md). Os relatos anteriores abaixo são históricos; prompts futuros permanecem sujeitos às condições vigentes. O mínimo permanece1 por célula, sem suficiência estatística; revisão/validação não são equivalência semântica. Curadoria usa raw fixado, templates limitados e exclusões registradas; não certifica toda afirmação da fonte. Defeitos originais de linguagem e apresentação contextual árabe permanecem delimitados no datasheet; clean_text_corpus_ready=false; não usar como corpus universal de texto limpo. IDF reconstruído somente de treino e separado do IDF da aplicação. Não migrar a aplicação automaticamente. H1 exige mapeamento/gabarito avaliativo; H2 construto/unidade/anotação independente/protocolo; H3 meta/carga/hardware/protocolo. São propostas científicas pendentes, sem aprovação presumida. Não iniciar S5, treinar, calibrar ou medir desempenho no teste. CI histórico é separado das verificações locais; gatilhos preservados.
<!-- /S4-CLOSURE-CURRENT -->

## Estado de entrada atualizado após a S4

Versão operacional congelada ee13c978fc9ad9397dcb7bbce2c4085bf0de928c5e1bedd3eea0cf14f122c702:59 fontes/grupos, splits41/9/9,735 pares/617 conteúdos/5.709 sentenças,132 formatos/44 conteúdos. IA dependente do gerador, sem revisão humana; semantic_training_ready=false. IDF treino41/14.588 separado da aplicação. Datasheet/relatório/matriz/receita/kit privados acompanham a entrega em TCC/evidencias/codex-s4-complemento-01/retomada-01/.

5A deve primeiro verificar finalidade/tarefa/gabarito e resolver H2 antes de treino semântico. 5B depende de pacote futuro autorizado e apto, sem assumir GPU. 5C depende de mapeamento H1, alvo/protocolo H2 e meta/carga H3; protocolo/métricas/seeds/repetições/política do teste antes de avaliação. 5D deve manter limites, amostragem, exposição e receita explícitos. Nenhuma dessas etapas foi iniciada pela S4. Não reexecutar geração válida nem transformar aceites IA/r/classes de construção em gabarito independente.

Plano histórico de 5 dias (guia, seção 0.4), sem reinício do prazo na retomada. Cada sessão tem um bloco de prompt e uma linha "Pronto quando". A regra de veracidade do CLAUDE.md vale para todas.

## Regras comuns — integração de 2026-10-24

- Ler AGENTS.md, CLAUDE.md, guia/mapa, TCC/00/01/02/14 e os registros/evidências pertinentes. Fonte científica é o PDF original; escopo segue decisão explícita do autor. TCC/02 contém propostas de protocolo ainda a ratificar e contratos Q1–Q6 adotados no alcance da S2; separar os estados e não atribuir decisões do projeto ao orientador.
- Executar somente o pedido vigente. Retomar pelo checkpoint e validar o que mudou; não reiniciar sessões, recriar estruturas ou repetir verificações íntegras sem necessidade. A autorização vigente desta edição é somente S4, preservando S1–S3/Q5-V2; estados anteriores de bloqueio são históricos. Incluir comandos no prompt não comprova execução; consulte os logs da etapa.
- Proibidos commit, push, tag, merge, rebase, cherry-pick, revert, reset/clean, PR, release e publicação por qualquer ferramenta/API/script; não apagar volumes nem descartar alterações. Preservar .env/segredos e privacidade de docs/TCC/regras. LICENSE oficial permanece intacta; autoria confirmada em NOTICE e licenças externas separadas, sem parecer jurídico automático.
- Separar publicado/PDF/página, recálculo independente, decisão/proposta/aprovação, resultado executado/comando/artefato e não verificado. Esperado não vem da função testada; não afrouxar tolerância. Fonte ausente/ambígua permanece pendência; continuar o trabalho independente. Skips/xfails explícitos; não fabricar aprovação humana. Seeds/fumaça não são resultados científicos.
- Usar propriedades por função/domínio; nomear OSA e distinguir da irrestrita, E2 adaptado de Textract/IQ e índice simétrico de r. Não prometer detecção conclusiva de plágio. A6/91,7% é exercício de média, não acurácia global reconstruída.
- Preservar Python 3.11.9/uv.lock como baseline; candidato 3.11.17 em ambiente separado, lock congelado e runtime conferido. Promoção depende de validação real Windows/Docker, imports/CLI/referências/suíte e tag/digest confirmados. Node 24 LTS é candidato S2/S3 com patch a verificar; Node 20+ não garante suporte. S2 autoriza integração web/API, sem telas S3; Python não foi migrado. Node 24.22.1 LTS foi consultado na fonte oficial, com verificação e execuções próprias em TCC/evidencias/codex-s2/.
- Dependências por etapa: S1 é a lista de parsing/NLP/cálculos; S2 acrescenta API/semântico/alinhamento; S3 interface/segurança. **S4 usa candidatos da sessão Codex com cache; google-genai deixa de ser obrigatório por complemento explícito do autor.** Grupo dataset somente para persistência do core; llm-api é opcional/histórico e não autoriza custo/chamada. Treino adicional é S5. Perfis opcionais exigem necessidade/versão, sem upgrades em bloco ou autofix automático.
- Métricas de tempo/memória exigem protocolo: delta RSS não é pico nem consumo exclusivo; tracemalloc não mede toda memória nativa/GPU; zero medido não é consumo zero. Fumaça verifica execução/formatos/valores finitos/backprop/artefatos quando implementados, sem obrigação de queda de perda.
- S2 depende dos contratos de escores, indisponíveis, vazios, identidade, correspondência/alinhamento, classes e fusão fixa. Alvos de treino/fusão aprendida e calibração/avaliação dependem de suas etapas próprias, sem bloquear artificialmente S2. Split por fonte/grupo antes de pares, todas as fontes no mesmo split; IDF só nas fontes de treino. Protocolo e repetições congelados antes do teste final, sem escolher a melhor execução.
- Ao fechar cada tarefa: atualizar checkpoint/TCC; distinguir núcleo S1 verificado, adaptações/limites de fonte, decisões que bloqueiam S2 e pendências futuras. Usar vereditos separados, sem declarar nova execução por reutilizar log. Conferência humana só é registrada no alcance efetivamente informado pelo autor; a confirmação visual de cinco amostras não conclui outros itens de revisão.

Roteiro revisado recebido: [docs/04](04-roteiro-revisado-s1.md). Cópia anterior exata deste arquivo: [histórico identificado](historico/03-prompts-por-etapa-antes-2026-10-24-reconstrucao.md). A numeração S0–S5/5A–5D e o plano histórico foram preservados; não representam uma contagem regressiva nova.

## Nota de auditoria — 2026-10-24

- Sessão 0.5 não tem um prompt próprio neste arquivo. Esse nome identifica a revisão documental e as treze decisões registradas em TCC/01; não se inventou um prompt ausente.
- Propriedades são por função e domínio: distâncias têm identidade zero; similaridades de caracteres normalizadas têm identidade um; cosseno de vetores não negativos e não nulos está em [0,1], mas o cosseno geral pode ser negativo. Norma zero segue política explícita do projeto; 1+cos tem intervalo [0,2] nos vetores não nulos.
- O código atual usa OSA, variante restrita da família Damerau-Levenshtein; A4 não fornece recorrência nem informa essa restrição. Não declarar equivalência com a variante irrestrita. Teste discriminante em TCC/03; autor adotou OSA operacionalmente no complemento S1, sem afirmar variante publicada pelo A4.
- Valores publicados exigem PDF/página; recálculos exigem método independente; parâmetros exigem justificativa/status; resultados obtidos exigem execução e evidência. O mapa não substitui os PDFs.
- Preservar LICENSE oficial e usar NOTICE para atribuição confirmada. Menções históricas justificadas a PyMuPDF permanecem válidas; o parser do projeto é pdfplumber.
- Registro de uma resposta não comprova aprovação, implementação nem validação. A evidência de cada dimensão fica separada no inventário da reauditoria.

## Sessão 0 (Dia 1, ~30 min): leitura e plano

```
Leia o CLAUDE.md e o TCC/00-indice.md. Depois leia a seção 0 inteira do guia (0.4 prevalece sobre a seção 12) e as seções 4.4, 4.5, 5.3, 5.4, 6, 6.1, 6.2, 10, 11 e 12, e no mapa (docs/02) "Valores de referência para testes" e "Definições do projeto que mudam como as fórmulas são usadas". Não escreva código nem reinicie etapas concluídas. Reconstrua objetivo, estado e evidências; entregue matriz objetivo→método→implementação→teste→avaliação, árvore real e inventário de decisões com origem/proposta/aprovação/validação separadas. Responda: o que o sistema entrega e o que ficou de fora (0.1 com os cortes da 0.4); a árvore de pastas (core Python/Flask com domain, application, adapters, cli, tests; web Next.js/TypeScript/Tailwind com src/modules; docker-compose.yml na raiz); o plano das Sessões 1 a 5 com os testes de cada uma; e os pontos ambíguos, conflitantes ou impossíveis no prazo, registrados em TCC/14. Não faça commit nem push.
```

Pronto quando: o resumo, a árvore e o plano batem com as seções 0.1 e 0.4, e as dúvidas estão em TCC/14.

## Sessão 1 (Dia 1): núcleo de cálculo

```
Somente em manutenção S1 explicitamente pedida: leia o CLAUDE.md e o TCC/00-indice.md. Confira a estrutura existente (4.4 e 4.5), core/uv/lock/Docker/corpus e evidências antes de editar. Preserve baseline e trabalho já comprovado; complete apenas requisitos pendentes de S1 autorizados para a execução. A lista de cobertura é: parsing (pdfplumber, python-docx, TXT; junção de palavras quebradas no fim da linha, troca do hífen suave 0xad, segmentação em sentenças); os dois perfis de pré-processamento (lexical e semântico); IDF, TF-IDF e cosseno (fórmula do A1 para os testes; IDF suavizado de corpus de referência provisório para o sistema, 0.3); os 7 algoritmos do A4; o E2 (termos salientes e assinatura com hash estável); e as métricas da seção 6. Testes de referência do mapa, conferidos no PDF antes do uso: A1 idf 0,60206 / 0,30103 / 0; cos(u,d2) = 0,0365; Jaro-Winkler = Jaro com l = 0; 1 + cos = 2,00; matrizes do A5. Propriedades com hypothesis por função/domínio conforme as Regras comuns; não impor simetria/[0,1]/identidade um universalmente. A lista numérica anterior é candidata de conferência, não licença para mudar esperado: distinguir precisão publicada e recálculo, com fonte/entradas/obtido/tolerância/evidência. Preservar regressões de segmentação/TXT e a correção Type1 já executada; xfail antigo foi retirado após correção real e passagem sem sua proteção, com mesmo esperado. Não reiniciar S1 concluída sem pedido de manutenção ou divergência relevante. E2 é adaptação; OSA deve ser nomeada. Identidade IDF: proposta complementar sem migração/rebuild silenciosos. Mostre a saída real dos testes. Atualize TCC/01, TCC/03, TCC/04, TCC/05, TCC/10 e TCC/00. Não faça commit nem push.
```

Pronto quando: requisitos atuais passam ou têm limitação de escopo explicitamente aceita; evidências correspondem ao código/runtime atuais; referências têm procedência e adaptações nomeadas. Docker config, build e suíte na imagem são checagens distintas; Mongo saudável não prova CRUD. Identificar decisões bloqueadoras de S2 separadas de pendências futuras. Xfail não é sucesso nem contagem é meta a forçar.

## Sessão 2 (Dia 2): motores semânticos, fusão, API e integração

**Prompt completo atualizado:** [05-prompt-sessao2.md](05-prompt-sessao2.md). Estado em 2026-10-24: **implementação explicitamente autorizada; Q5-V2 adotada como baseline provisória**. A proposta anterior não aprovada permanece no histórico. Evidências reais e veredito no checkpoint TCC/00 e entrega codex-s2; autorização não equivale a execução aprovada.

Condições de entrada: pedido explícito de implementação (recebido), S1 concluída/evidências atuais íntegras e contratos científicos decididos no alcance de S2 (Q5-V2 agora adotada). Não bloquear S2 por treino/dataset/calibração final/GPU futuros. Não omitir classes da entrega para declarar conclusão. Pronto quando: critérios completos do prompt, incluindo E3/E4/fusão/índice/classes no alcance aprovado, contrato web↔core com negativos, fluxo real de dois arquivos/API/persistência, seeds por dono e verificações reais com evidências. Passar testes de desenvolvimento não valida hipóteses científicas.

## Sessão 3 (Dia 3): frontend integrado e testes de sistema

Prompt completo atualizado: [06-prompt-sessao3.md](06-prompt-sessao3.md). O pedido atual autoriza S3; não autoriza S4. A execução remota S2 [40118062459](https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40118062459) terminou success no head ecb14086 e checkout 028737cf, com árvores equivalentes conferidas. Isso não prova a causa das falhas Linux anteriores nem valida o código S3 atual. A execução remota S3 continua separada da verificação local; consulte TCC/00 e evidencias/codex-s3.

Retomar código e evidências existentes, sem reiniciar sessões. Preservar fórmulas, Q5-V2, E2 adaptado, OSA restrita, modelo/revisão, perfis, corpus e IDF. Core JSON1.0 matemático preservado; headers opcionais de engenharia e envelope web com proprietário, documentos e durações. Web é dono de users/sessions/rate_limits/documents/comparisons/reports; core sem persistência de comparações. Dados antigos sem dono não são atribuídos nem expostos automaticamente.

Escopo: auth local real/CSRF/expiração/logout, autorização de todas as rotas, dois arquivos ou textos colados, uma execução híbrida compartilhada no modo todos, apresentação explicável, mapa por índices, histórico próprio e impressão. Desenvolvimento HTTP loopback; serviços internos sem portas públicas. Playwright com dois usuários, negativas reais de core/modelo, testes de segurança e auditorias. Carga exploratória por script Node versionado é alternativa justificada ao k6: registrar protocolo antes, todas as observações, p50/p95/p99 empíricos e falhas; não valida H3. Não inventar memória/tempo por algoritmo compartilhado. CI mantém exclusivamente push main e PR/main opened, sem disparo por publicação pelo agente.

Pronto quando: todos os critérios do prompt completo possuem evidência atual ou impedimento explícito. Contagem de testes não é meta; aprovação isolada não prova encerramento. Limitações de auditoria, memória, impressão e carga são declaradas. S3 concluída somente no escopo efetivamente verificado; sem dataset, treino, calibração, teste científico final ou avanço automático para S4.

## Sessão 4 (Dia 4): dataset sintético

**Prompt completo vigente:** [07-prompt-sessao4.md](07-prompt-sessao4.md), complemento integral do autor. Histórico anterior exato em historico/s4-complemento-01/. Não reiniciar S1–S3 nem executar S5. As passagens antigas do guia5.3/5.4 sobre Gemini obrigatório, r como alvo semântico, revisão humana presumida e depósito não representam o contrato vigente.

Executar as correções cache–fonte/resposta–ancestrais/raw–structured/retrotradução; validação compartilhada de revisão/seleção/IDs/cobertura; congelamento por finalidade; auditabilidade de formatos/IDF/Mongo/CLI e reprodução isolada. Preservar versões antigas e logs antes/depois. Cobertura e limites vêm da especificação operacional registrada antes da geração. C3 é composição fixa; C6 é reescrita guiada com derivação conhecida e sem classe semântica automática. E2 adaptado, OSA restrita e contratos V2 permanecem preservados.

Usar saídas reais da sessão Codex com entradas/prompts/intermediários/cache, sem API paga, contratação ou credenciais de assinatura. Avaliação IA é identificada e dependente do mesmo gerador. Pacote humano anterior permanece não realizado; não preencher autor/segundo revisor/κ ou atribuir aprovação do orientador. Validação estrutural, avaliação de conteúdo, revisão humana, semântica, prontidão de aplicação e treinamento têm estados separados.

Manter59 fontes e grupos/splits existentes se cobrirem o desenho operacional, sem alegar poder estatístico; ampliar somente lacunas demonstradas, com plano prévio e sem predições no teste. IDF apenas treino, sem migração automática da aplicação. Distinguir A: engenharia; B: versão congelada operacional para derivação/robustez; C: gabarito e protocolo aptos a treino/avaliação semântica. A/B não implicam C ou H2 pronta.

Pronto quando: matriz do complemento identifica evidências executadas e veredito por finalidade, falhas/rejeições preservadas, reprodução raw/cache e export/import verificadas, modalidades/limites no manifesto/datasheet e ausência de execução S5. Pendência científica não bloqueia artificialmente A/B; lacuna técnica não pode ser escondida para encerrá-las.

## Sessão 5 (Dia 5): experimentos e fechamento

Dividida em quatro partes para separar preparação, execução pelo autor, registro e fechamento. Alegações antigas sobre MX570/Kaggle são históricas, sem inspeção atual de hardware/conta; capacidade e disponibilidade devem ser verificadas antes do treino, sem afirmar impossibilidade universal.

Condições futuras S5: usar versões/hashes congelados e mesma política de agregação nos baselines; definir alvos/unidade/métricas antes de treinar. Instrumentação S3 é engenharia compartilhada: RSS de vida do processo não é memória por algoritmo; carga exploratória não operacionaliza H3. Planejar medição isolada e meta/hardware antes de avaliação. Preservar H1–H3 literalmente, não convertê-las em resultados ou aprovações humanas. Não usar documentos/histórico de usuários no teste final nem ajustar limiares pelo teste.

### 5A (Claude Code): pacote de treino do siamês

<!-- S4-S5-GATE-A -->

Referência operacional atual: `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`, contrato assessment_v2, avaliação IA por amostra e gerador dependente, humano não realizado. Curadoria de extração não certifica prosa/fatos/gabarito semântico. Receber a versão pelo manifesto e conferir os limites/datasheet; resolver as condições científicas aplicáveis antes desta etapa futura. Nenhuma autorização automática para treino/calibração/teste ou inícioS5.

<!-- /S4-S5-GATE-A -->

Condição de entrada: autorização futura específica e versão apta à tarefa. `frozen_operational_derivation` autoriza apenas derivação/robustez explicitadas no manifesto, não treino semântico/H2. Alvo, unidade, origem/validade do gabarito e protocolo H2 permanecem decisões científicas; autoavaliação do gerador não é anotação independente. Não usar r documental por sentença, 1−taxa, C5=1, C0=0 ou alinhamento preferido do modelo como gabarito automático. Revisão humana não realizada deve permanecer assim; não pedir ao autor certificação técnica fictícia. Cache permite reconstrução sem assinatura Codex ou API; não promete nova geração idêntica. Nenhum treino nesta S4.

```
Leia o CLAUDE.md e o TCC/00-indice.md. Somente quando autorizado e resolvidas as condições de entrada, implemente no core o treino do siamês inspirado em A7, com valores publicados conferidos nos PDFs e escolhas ausentes registradas em TCC/01. Unidade/tarefa/alvo e seleção de pares exigem ratificação: não escolher apenas os pares preferidos pelo E4/modelo avaliado, nem transportar r documental para todo par de sentenças. Os alvos históricos (exata1, editada1−taxa, paráfrase1, original0) permanecem propostas históricas, sem preservação semântica presumida. Antes de treinar, exigir versão e gabarito aptos à finalidade, modalidade real de anotação/avaliação, proveniência, IDF somente de treino e protocolo H2 comparável ao baseline; congelamento operacional e avaliação do gerador não suprem essas condições. A7 é adaptação identificada. Fixar YAML/seeds e guardar por execução pesos privados, métricas reais/config/ambiente/log/hashes; teste fora do ajuste. Notebook futuro sem lógica própria; fumaça apenas quando autorizada, sem obrigação de perda cair nem validação científica. S4 não executa esta etapa. Atualize TCC/12; sem commit/push/publicação.
```

Pronto quando: o teste de fumaça roda localmente e está marcado como fumaça, o zip está gerado e o passo a passo do Kaggle está em TCC/12.

### 5B (o autor): treino no Kaggle

<!-- S4-S5-GATE-B -->

Referência operacional atual: `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`, contrato assessment_v2, avaliação IA por amostra e gerador dependente, humano não realizado. Curadoria de extração não certifica prosa/fatos/gabarito semântico. Receber a versão pelo manifesto e conferir os limites/datasheet; resolver as condições científicas aplicáveis antes desta etapa futura. Nenhuma autorização automática para treino/calibração/teste ou inícioS5.

<!-- /S4-S5-GATE-B -->

Executar somente depois de 5A autorizado, dados/gabarito aptos à tarefa, modalidade e alcance reais da anotação/avaliação documentados, hashes e IDF de treino conferidos; não usar o pacote piloto. Hardware/conta disponíveis devem ser verificados, sem assumir GPU. Definir e registrar todas as seeds/repetições; não escolher a melhor execução. Separar fumaça de resultados científicos.

Subir o pacote_treino.zip no Kaggle (GPU, telefone verificado), rodar todas as células, só alterar o YAML se precisar e trazer o zip de saídas.

Pronto quando: o zip de saídas, com metrics.json, config, env.txt, log e hash do dataset, está no repositório local (pesos fora do Git).

### 5C (Claude Code): registro e experimentos

<!-- S4-S5-GATE-C -->

Referência operacional atual: `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`, contrato assessment_v2, avaliação IA por amostra e gerador dependente, humano não realizado. Curadoria de extração não certifica prosa/fatos/gabarito semântico. Receber a versão pelo manifesto e conferir os limites/datasheet; resolver as condições científicas aplicáveis antes desta etapa futura. Nenhuma autorização automática para treino/calibração/teste ou inícioS5.

<!-- /S4-S5-GATE-C -->

O congelamento operacional S4 não libera avaliação semântica/H1–H2. Resolver tarefa/alvo/unidade/anotação e mapeamento avaliativo; não reescrever hipóteses. Antes do teste: congelar protocolo, baselines comparáveis, mapeamento avaliativo C0–C7/saídas V2, unidade/alvo H2, seeds/repetições/métricas e configuração. IDF somente de treino, separado da demonstração. Índice, classe por sentença, r e alvo do siamês têm contratos distintos. Intervalos/reamostragem respeitam fonte/grupo e variantes de formato não são observações independentes. Não executar comparações científicas com o piloto; o guard de teste S4 permanece fechado até autorização/protocolo S5. Preservar todas as rodadas, sem selecionar a melhor nem reformular H1–H3. Ausência de alvo/dataset apto impede a avaliação correspondente, não autoriza nota inventada.

```
Leia o CLAUDE.md e o TCC/00-indice.md. Confira os hashes do zip de saídas e registre cada execução em TCC/12, copiando os números do metrics.json. Integre o siamês como motor com inferência em CPU (sem os pesos, o motor fica indisponível sem quebrar o sistema). Somente com alvo/features/saída ratificados, implementar fusão logística; probabilidades de classe não viram índice contínuo automaticamente. Treinar no treino, escolher/calibrar só na validação; congelar protocolo/configurações/repetições e rodar o teste final em uma rodada planejada, registrando todas as execuções. Repetição exige motivo e saídas preservadas. Calcule as métricas por sentença e por documento, com média ± desvio e bootstrap; ablação isolada e removida; eficiência; H1 a H3 com número e teste apenas se estiverem operacionalizadas e houver execução real; caso contrário registrar pendência sem reescrever hipótese. Gere as tabelas de TCC/13 por script. Não faça commit nem push.
```

Pronto quando: cada execução está em TCC/12 com hash conferido, o teste rodou uma vez e as tabelas de TCC/13 são geradas por script.

### 5D (Claude Code): fechamento

<!-- S4-S5-GATE-D -->

Referência operacional atual: `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`, contrato assessment_v2, avaliação IA por amostra e gerador dependente, humano não realizado. Curadoria de extração não certifica prosa/fatos/gabarito semântico. Receber a versão pelo manifesto e conferir os limites/datasheet; resolver as condições científicas aplicáveis antes desta etapa futura. Nenhuma autorização automática para treino/calibração/teste ou inícioS5.

<!-- /S4-S5-GATE-D -->

Separar encerramento técnico, uso operacional e validade científica. Auditar a versão efetivamente congelada e sua finalidade, revisão/amostragem reais, cache e limites de reprodutibilidade. Ausência de geração/avaliação adequada/alvo/protocolo não pode virar resultado ou depósito aprovado; pacote humano vazio e avaliação IA dependente não devem ser chamados de revisão humana. Artefatos permanecem locais; preparar depósito não é publicar. H1–H3 e números de TCC/13 só se sustentados por execuções científicas futuras, nunca pela suíte ou pelo piloto S4.

```
Leia o CLAUDE.md e o TCC/00-indice.md. Escreva o README de execução local (pré-requisitos e versões), rode o teste de reprodução a partir de uma cópia limpa (subir, carregar seeds, rodar testes), prepare localmente CITATION.cff e lista para eventual depósito pelo autor, sem publicar, atualize TCC/14 e confira que todo número de TCC/13 está ligado a uma execução de TCC/12. Não faça commit nem push.
```

Pronto quando: a reprodução a partir da cópia limpa passa e todo número de TCC/13 aponta para uma execução de TCC/12.

## Se atrasar

Cortar nesta ordem (guia, 0.4): repetições do siamês com várias sementes; fusão aprendida (fica a fusão por regras); autenticação e histórico; versão em PDF/DOCX da amostra do dataset. Nunca cortar testes de referência, divisão por documento-fonte nem registros em TCC/.

## Paralelizar

Opcional: worktrees separadas para core e web, só depois que o contrato /v1 estiver fixado.

## O que providenciar

- Corpus PT-BR aberto (lista de títulos da Wikipédia em português).
- 2 ou 3 pares de arquivos reais para demonstração.
- Geração já preservada na sessão Codex; nenhuma chave/API paga exigida para a S4.
- Conta no Kaggle com GPU (telefone verificado).
- Avaliação IA operacional identificada; pacote humano preservado como não realizado, sem bloquear a finalidade autorizada.

## Atualização documental de 2026-10-24 — encerramento S1 e preparo S2

Sessão 1 concluída no escopo implementado e verificado, com limitações documentadas. Conferência visual do autor restrita a cinco amostras; logs técnicos anteriores não foram reexecutados nesta tarefa. Regras comuns/S1 foram corrigidas apenas quanto a gates futuros, OSA e Type1 já resolvidos; S2 recebeu prompt completo separado. Demais sessões preservadas. Histórico anterior exato: [cópia identificada](historico/03-prompts-por-etapa-antes-2026-10-24-encerramento-s1.md). docs/04 permanece roteiro recebido/histórico, não fonte de um novo xfail ou nova execução. Estado atual e decisões prevalecem nos registros TCC/00/01/02/14.
