# Prompts por sessão — roteiro integrado para continuidade

<!-- S5B-CURRENT -->
## Estado vigente — S5B, 2026-10-25

S5B foi explicitamente autorizada pelo pedido atual e executada no alcance descrito no protocolo separado; não repetir S4/S5A nem usar vetos históricos como bloqueios vigentes. Treino real depende da reserva de memória adotada; S5C não iniciada.

[Protocolo S5B](10-protocolo-s5b.md). Registros anteriores mantidos como históricos.
<!-- /S5B-CURRENT -->

<!-- S5A-HISTORICAL -->
## Registro histórico — complemento S5A, 2026-10-25

Complemento técnico S5A concluído no alcance independente: protocolo, vínculo IDF e importação corrigidos e verificados. S4 permanece encerrada operacionalmente; nenhum treinamento, calibração, carga ou avaliação preditiva do teste. Contratos científicos candidatos não significam liberação de treinamento.

Schemas de preparação corrigidos; protocolo original preservado e suplemento candidato vinculado. Seguir o protocolo e a matriz vigentes, sem início automático de S5B.

[protocolo](08-protocolo-s5a.md) | [relatório](../TCC/evidencias/codex-s5a-complemento-01/relatorio-final.md) | [matriz](../TCC/evidencias/codex-s5a-complemento-01/matriz-prontidao.md) | [checkpoint](../TCC/evidencias/codex-s5a-complemento-01/checkpoint.md) | [S5B](09-prompt-s5b.md)

S5A original preservada como histórica em documentacao-anterior.zip na pasta de evidências do complemento e nas evidências codex-s5a-01. Registros abaixo são históricos das suas execuções; não atribuir a eles as correções atuais. Entrega S4: kit base e adendo-retomada-final-02.zip definitivo, com dataset separado; adendo01 é tentativa anterior preservada. ZIPs antigos não foram regenerados.
<!-- /S5A-HISTORICAL -->

<!-- S4-CLOSURE-CURRENT -->
## Registro histórico — fechamento dirigido S4, 2026-10-25

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

## Sessão 5 — continuidade revisada após S5A

O roteiro anterior integral está preservado no [histórico anterior à S5A](historico/03-prompts-antes-s5a-2026-10-25.md). A divisão atual não autoriza executar etapas seguintes automaticamente.

### 5A — contratos, protocolo e preparação

Escopo executado: transição S4, hipóteses originais, contratos candidatos, importador de anotações, métricas, carregadores, checkpoints, instrumentação artificial e proteção do teste. Sem treino/calibração/carga ou desempenho no teste. [Protocolo](08-protocolo-s5a.md) e [configuração](../core/configs/experiment_s5a.json).

### 5B — continuidade condicionada por tarefa

Usar o [prompt S5B atualizado](09-prompt-s5b.md). Não está liberado treino H1/H2: faltam contratos/anotações/arquitetura/orçamento e desenho de incerteza. Não assumirKaggle, GPU, upload ou rótulo semântico por construção. Primeiro concluir as condições concretas da matriz S5A, somente sob novo pedido autorizado.

### 5C — execução científica futura

Pedido futuro próprio deve identificar protocolo liberado, tarefa, alvo, unidade, dataset, modelos, configs, métricas, seeds, orçamento e repetições. Treino somente em train, seleção em validation; test permanece fechado até autorização da etapa e controles vinculados. Comparação comum e falhas preservadas; nenhuma probabilidade vira índice contínuo por conveniência. Não usar bootstrap ingênuo diante da dependência multiorigem. Não iniciar esta etapa na S5A.

### 5D — fechamento futuro

Auditar execuções e recursos realmente produzidos, reprodução no alcance testado e números deTCC/13 gerados de métricas reais. Hipóteses não confirmadas continuam não confirmadas; sem resultados inventados/publicação. Não iniciar automaticamente.
