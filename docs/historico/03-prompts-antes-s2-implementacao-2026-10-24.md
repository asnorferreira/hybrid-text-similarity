# Prompts por sessão — roteiro integrado para continuidade

Plano histórico de 5 dias (guia, seção 0.4), sem reinício do prazo na retomada. Cada sessão tem um bloco de prompt e uma linha "Pronto quando". A regra de veracidade do CLAUDE.md vale para todas.

## Regras comuns — integração de 2026-10-24

- Ler AGENTS.md, CLAUDE.md, guia/mapa, TCC/00/01/02/14 e os registros/evidências pertinentes. Fonte científica é o PDF original; escopo segue decisão explícita do autor. Contrato científico em TCC/02 é proposta a ratificar, não orientação comprovada do orientador.
- Executar somente o pedido vigente. Retomar pelo checkpoint e validar o que mudou; não reiniciar sessões, recriar estruturas ou repetir verificações íntegras sem necessidade. Esta edição faz somente finalização documental S1 e preparação S2; os comandos operacionais dos prompts não foram executados por sua inclusão.
- Proibidos commit, push, tag, merge, rebase, cherry-pick, revert, reset/clean, PR, release e publicação por qualquer ferramenta/API/script; não apagar volumes nem descartar alterações. Preservar .env/segredos e privacidade de docs/TCC/regras. LICENSE oficial permanece intacta; autoria confirmada em NOTICE e licenças externas separadas, sem parecer jurídico automático.
- Separar publicado/PDF/página, recálculo independente, decisão/proposta/aprovação, resultado executado/comando/artefato e não verificado. Esperado não vem da função testada; não afrouxar tolerância. Fonte ausente/ambígua permanece pendência; continuar o trabalho independente. Skips/xfails explícitos; não fabricar aprovação humana. Seeds/fumaça não são resultados científicos.
- Usar propriedades por função/domínio; nomear OSA e distinguir da irrestrita, E2 adaptado de Textract/IQ e índice simétrico de r. Não prometer detecção conclusiva de plágio. A6/91,7% é exercício de média, não acurácia global reconstruída.
- Preservar Python 3.11.9/uv.lock como baseline; candidato 3.11.17 em ambiente separado, lock congelado e runtime conferido. Promoção depende de validação real Windows/Docker, imports/CLI/referências/suíte e tag/digest confirmados. Node 24 LTS é candidato S2/S3 com patch a verificar; Node 20+ não garante suporte. Não iniciar web nem migrar ambiente nesta revisão documental.
- Dependências por etapa: S1 é a lista atual de pyproject/lock (pdfplumber, python-docx, spaCy/modelo PT, NumPy, PyYAML, mwparserfromhell; dev pytest/Hypothesis/RapidFuzz/ReportLab); S2 acrescenta apenas o necessário a API/semântico/alinhamento; google-genai é S4; treino adicional é S5. Perfis opcionais/ferramentas novas exigem necessidade e versão, sem upgrades em bloco ou autofix automático.
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

**Prompt completo atualizado:** [05-prompt-sessao2.md](05-prompt-sessao2.md). Estado em 2026-10-24: **preparado, ainda não liberado — Q5-V2 depende de resposta**. Q1–Q4 e Q6 respondidas; contrato de classes anterior não aprovado. Esta entrada é preparação documental, não execução.

Condições de entrada: pedido futuro explícito de implementação, S1 concluída/evidências atuais íntegras e contrato dependente de classes decidido. Não bloquear S2 por treino/dataset/calibração final/GPU futuros. Não omitir classes da entrega para declarar conclusão. Pronto quando: critérios completos do prompt, incluindo E3/E4/fusão/índice/classes no alcance aprovado, contrato web↔core com negativos, fluxo real de dois arquivos/API/persistência, seeds por dono e verificações reais com evidências. Passar testes de desenvolvimento não valida hipóteses científicas.

## Sessão 3 (Dia 3): frontend integrado e testes de sistema

```
Leia o CLAUDE.md e o TCC/00-indice.md. Implemente o frontend da seção 6.1 já ligado ao backend: autenticação local (hash forte de senha, cookie httpOnly, acesso só aos próprios documentos), envio, estados (enviando, processando com indicador indeterminado, concluído, erro), tela de resultado (índice, lado a lado com cores, lista de sentenças, mapa de calor, tabela por algoritmo com tempo e memória definidos pelo protocolo e limitações visíveis, modo "rodar todos"), histórico e PDF pela impressão do navegador. Testes: Playwright no fluxo login → envio → resultado → histórico → impressão; k6 com p50/p95/p99 (linha de base, não resultado); segurança: tipo real do arquivo, limite de tamanho, limite de requisições, npm audit e pip-audit. Atualize TCC/08, TCC/11 e TCC/00. Não faça commit nem push.
```

Pronto quando: o Playwright passa no fluxo completo, a linha de base do k6 está registrada como não resultado e os testes de segurança passam.

## Sessão 4 (Dia 4): dataset sintético

```
Leia o CLAUDE.md e o TCC/00-indice.md. Implemente no core/cli o fluxo da seção 5.4: manifesto das fontes (Wikipédia em português, lista fixa de títulos, licença, data e hash); divisão por fonte/grupo antes de gerar, com proporção histórica 70/15/15 sujeita ao protocolo ratificado e semente fixa; todas as fontes de patchwork/pares/negativos permanecem no mesmo split; classes C0 a C7, com C5 por paráfrase via google-genai em cache (modelo, versão e prompt guardados; o LLM nunca rotula); origem por sentença e r; amostra para revisão humana com planilha de aceito/rejeitado; validação de esquema, vazamento e determinismo; congelamento com hash, datasheet e JSONL; IDF passa a usar só as fontes do split de treino. Registre em TCC/06 e TCC/00. Não faça commit nem push.
```

Pronto quando: mesma semente gera o mesmo hash, a checagem de vazamento passa, a amostra de revisão está pronta para o autor e TCC/06 traz a versão (hash) do dataset.

## Sessão 5 (Dia 5): experimentos e fechamento

Dividida em quatro partes para separar preparação, execução pelo autor, registro e fechamento. Alegações antigas sobre MX570/Kaggle são históricas, sem inspeção atual de hardware/conta; capacidade e disponibilidade devem ser verificadas antes do treino, sem afirmar impossibilidade universal.

### 5A (Claude Code): pacote de treino do siamês

```
Leia o CLAUDE.md e o TCC/00-indice.md. Implemente no core o módulo de treino do siamês (A7: 8 épocas, lr 2e-6, Adam, max 212 tokens, weight decay 1e-5, MSELoss; o que o A7 não informa é proposto e registrado em TCC/01 como decisão do projeto). Unidade = par de sentenças alinhado pelo E4; os alvos históricos (exata 1,0; editada 1 − taxa de edição; paráfrase 1,0; original 0,0) permanecem proposta a ratificar em TCC/02, sem presumir preservação semântica ou equivalência a r documental. Não treinar antes de resolver alvo/unidade/validação da transformação. A7 é adaptação/reprodução parcial identificada, não arquitetura integral presumida. YAML único e semente fixa. Saídas por execução: pesos fora do Git, metrics.json, config, env.txt, log e hash do dataset (aborta se não bater); o conjunto de teste não entra no treino. Gere um notebook "aperta-play" sem lógica própria e o pacote_treino.zip. Quando a etapa de treino estiver autorizada, executar fumaça com configuração declarada (histórico: 1 época, 64 pares, lote 4), sem exigir queda de perda e sem chamar isso de aprendizagem validada ou resultado experimental. Escreva o passo a passo do Kaggle em TCC/12. Não faça commit nem push.
```

Pronto quando: o teste de fumaça roda localmente e está marcado como fumaça, o zip está gerado e o passo a passo do Kaggle está em TCC/12.

### 5B (o autor): treino no Kaggle

Subir o pacote_treino.zip no Kaggle (GPU, telefone verificado), rodar todas as células, só alterar o YAML se precisar e trazer o zip de saídas.

Pronto quando: o zip de saídas, com metrics.json, config, env.txt, log e hash do dataset, está no repositório local (pesos fora do Git).

### 5C (Claude Code): registro e experimentos

```
Leia o CLAUDE.md e o TCC/00-indice.md. Confira os hashes do zip de saídas e registre cada execução em TCC/12, copiando os números do metrics.json. Integre o siamês como motor com inferência em CPU (sem os pesos, o motor fica indisponível sem quebrar o sistema). Somente com alvo/features/saída ratificados, implementar fusão logística; probabilidades de classe não viram índice contínuo automaticamente. Treinar no treino, escolher/calibrar só na validação; congelar protocolo/configurações/repetições e rodar o teste final em uma rodada planejada, registrando todas as execuções. Repetição exige motivo e saídas preservadas. Calcule as métricas por sentença e por documento, com média ± desvio e bootstrap; ablação isolada e removida; eficiência; H1 a H3 com número e teste apenas se estiverem operacionalizadas e houver execução real; caso contrário registrar pendência sem reescrever hipótese. Gere as tabelas de TCC/13 por script. Não faça commit nem push.
```

Pronto quando: cada execução está em TCC/12 com hash conferido, o teste rodou uma vez e as tabelas de TCC/13 são geradas por script.

### 5D (Claude Code): fechamento

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
- Chave da API do Gemini.
- Conta no Kaggle com GPU (telefone verificado).
- Horas do autor no Dia 4 para a revisão humana da amostra.

## Atualização documental de 2026-10-24 — encerramento S1 e preparo S2

Sessão 1 concluída no escopo implementado e verificado, com limitações documentadas. Conferência visual do autor restrita a cinco amostras; logs técnicos anteriores não foram reexecutados nesta tarefa. Regras comuns/S1 foram corrigidas apenas quanto a gates futuros, OSA e Type1 já resolvidos; S2 recebeu prompt completo separado. Demais sessões preservadas. Histórico anterior exato: [cópia identificada](historico/03-prompts-por-etapa-antes-2026-10-24-encerramento-s1.md). docs/04 permanece roteiro recebido/histórico, não fonte de um novo xfail ou nova execução. Estado atual e decisões prevalecem nos registros TCC/00/01/02/14.
