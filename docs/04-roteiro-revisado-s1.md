# Roteiro revisado recebido — integrado em 2026-10-24

Texto recebido do autor, preservado abaixo. Nesta execução, só reconstrução e integração documental estão autorizadas. Comandos operacionais, testes novos, candidato de patch, Docker e experimentos deste roteiro permanecem para execução própria, sem sucesso presumido. Regras comuns vigentes em docs/03; contrato científico proposto em TCC/02. A menção a testes externos Linux/3.11.17 é relato recebido, sem log local identificado nesta reconstrução.

---

Conclua e valide a Sessão 1 do hybrid-text-similarity. Preserve tudo que já foi implementado e comprovado. Não reinicie o projeto e não implemente a Sessão 2.

Tema do TCC: sistema de comparação do conteúdo de dois arquivos, buscando suas inter-relações e um índice de correlação. Este é um projeto de pesquisa: correção, evidência e metodologia têm prioridade sobre quantidade de funcionalidades.

1. REGRAS INEGOCIÁVEIS
- Proibidos commit, push, tag, merge, rebase, cherry-pick, revert, PR, release e publicação, inclusive por APIs/scripts. Não descartar alterações, executar reset/clean, apagar volumes ou contornar restrições. Commits e pushes são exclusivamente do autor.
- Não inventar números, fontes, páginas, saídas, testes, resultados ou aprovações. Distinguir publicado, recálculo independente, decisão, resultado executado e não verificado.
- Esperados não vêm da implementação testada. Não afrouxar tolerância para passar. Correção de referência exige PDF, antes/depois e justificativa. Skips/xfails explícitos. Não preencher conferência humana.
- Segredos e .env real não entram em saídas/pacotes. Preservar evidências antigas. Seeds/fumaça não são resultados de pesquisa.

2. RECONSTRUA O ESTADO
Leia AGENTS/CLAUDE aplicáveis, docs/01, docs/02, o roteiro revisado, TCC/00/01/02/03/04/05/10/11/14 e evidências recentes. Consulte os PDFs necessários para cada referência científica.
Inspecione Git, código, testes, pyproject, lock, Dockerfile, Compose, corpus e scripts antes de editar. Arquivo ausente é pendência, não licença para inventá-lo.
Crie checkpoint em TCC/00: item, status, arquivos, evidência, próximo passo. Atualize após cada item. Ao retomar, valide o que mudou e não refaça trabalho comprovado sem necessidade.
O último pacote analisado teve 164 passes/1 xfail em Linux/Python 3.11.9 e também 3.11.17; essa contagem é referência histórica, não meta a forçar. Execute a suíte atual e guarde a linha de base real.

3. AMBIENTE E DEPENDÊNCIAS
Preserve o ambiente 3.11.9 e o lock como baseline reproduzível. Avalie Python 3.11.17 em ambiente separado e lock congelado; confirme disponibilidade e suporte nas fontes oficiais atuais. Não migre para outra família sem motivo demonstrado.
Execute em candidato: imports, suíte completa, testes de referência e comandos CLI pertinentes. Confirme patch no runtime, não apenas em .python-version. Compare resultados, não tempos de testes como resultado científico.
Se a promoção do patch for bem-sucedida no Windows local e no Docker, alinhe seletor, Dockerfile, documentação e comandos; confira tag/digest disponível, faça build e teste real. Não adivinhe tag. Se estiver bloqueado, preserve baseline e registre o que falta, sem declarar migração concluída.
Audite dependências diretas/transitivas e ferramentas. S1 já usa pdfplumber, python-docx, spaCy/modelo PT, NumPy, PyYAML, mwparserfromhell; dev usa pytest, Hypothesis, RapidFuzz e ReportLab. Verifique licenças e versões como fatos documentados, sem parecer jurídico.
Não instale toda a pilha futura: Flask/Pydantic/SciPy/Sentence-Transformers/torch/transformers são de S2, google-genai de S4 e aprendizado adicional de S5. Dependências opcionais ficam separadas por grupo/perfil. Ruff/pip-audit podem ser adicionados ao dev com necessidade e versões registradas; não executar autofix ou upgrades em bloco.
Não iniciar a web. Registre Node 24 LTS como candidato para S2/S3, com patch a verificar; o requisito antigo Node 20+ deve ser revisto pelo ciclo oficial de suporte.

4. NÚCLEO, PARSING E REGRESSÕES
Verifique domínio sem I/O e sem imports das bordas; combine inspeção de imports com execução de caminhos relevantes, sem chamar isso de prova universal.
Preserve TF-IDF exato do A1 separado do IDF suavizado do sistema; confira TF, log, df, norma zero e termos novos. Verifique sete funções de A4 com variantes e parâmetros nomeados; OSA não equivale automaticamente à irrestrita.
Confira E2 estável entre processos, ordem/repetição segundo contrato, top-k e limites. Assinatura igual não comprova texto idêntico e não pode virar escore por normalização do inteiro do hash.
Verifique as regressões já corrigidas de segmentação: domínio, URL, e-mail simples e Markdown, v1.2, decimais no fim, iniciais, abreviações pontuadas e aspas. Inclua explicitamente:
"Visite exemplo.com. Próxima frase."
"Envie para pessoa@dominio.com. Depois confirme."
"A versão é v1.2. Próxima frase."
Cada exemplo deve produzir duas sentenças conforme a pontuação indicada. Não generalize ponto interno para abreviação. Preserve os casos legítimos e documente ambiguidades restantes.
TXT: UTF-8/BOM e cp1252 válidos preservam caracteres; b"Texto \x81 fim." e BOM UTF-8 inválido devem produzir erro explícito, sem substituição silenciosa e sem inferir caracteres. Verifique o parser público, não só função interna.
PDF/DOCX/TXT: arquivos reais de teste; U+00AD; várias quebras na mesma palavra; hífen legítimo; parágrafos; PDFs protegidos, corrompidos e sem texto. DOCX com tabelas/caixas e layouts complexos precisam de cobertura ou limitação explícita.
Não transforme o xfail Type1 em sucesso por mudar esperado. Explique a perda de informação e as opções de escopo. Se houver aceite explícito do autor, registre a alteração do requisito e mantenha teste de caracterização e positivo Unicode; sem aceite, continua requisito aberto.
Métricas: entradas inválidas e casos indefinidos têm contratos claros; revisar pesos negativos/não finitos e tipos aceitos se puderem atingir usos reais. Testar apenas validações relevantes ao contrato. Propriedades por função, não simetria/[0,1]/identidade=1 universalmente.

5. REFERÊNCIAS E CORPUS
Confronte as referências implementadas com PDFs, incluindo A1, matrizes A5, médias A8/A9, propriedade A4 e exercício A6. Para cada uma: fonte/página, entradas, esperado, obtido, tolerância, natureza da evidência. Reutilize conferência anterior íntegra quando entradas/fontes não mudaram; execute os cálculos atuais.
Mantenha 91,7% do A6 como exercício de média, sem chamá-lo de acurácia global reconstruída. Não inventar dados ausentes de A3/A4 ou modelo/arquitetura integral de A7.
Confira manifesto, vinte fontes provisórias existentes se esse ainda for o estado, revisões, hashes e N/df. Não substitua a lista/corpus nem faça downloads desnecessários. Rebuild só em saída separada, com comparação, sem sobrescrever o IDF histórico.
Inspecione identidade_idf.py: separar corpus, pipeline/configuração/modelo, conteúdo N/df e ambiente. Descritor observado não atesta construção histórica. Testes precisam exercitar mudanças reais relevantes ou delimitar quando só testam a função de hash.
Não migrar a identidade silenciosamente. Entregue proposta, política de portabilidade e passos de migração; se aprovada, preserve alias/histórico e gere o descritor durante uma construção reproduzida. Só fontes de treino poderão ajustar o IDF experimental futuro.

6. AMBIGUIDADES E CONTRATO CIENTÍFICO DE S2–S5
Entregue inventário completo: questão, origem, resposta, evidência de aprovação, implementação, validação, impacto e próxima ação. Separe resolvido, provisório, não aprovado, bloqueado por fonte e futuro. Não reabra decisões explícitas sem motivo nem aprove detalhes em meu nome.
Documente propostas para A3: duas direções, tamanho/unidade/empate/vazio; E2 como adaptação TF-IDF/top-k/hash; OSA nomeada versus irrestrita; parâmetros não publicados. Ausência de material original não se resolve por votação ou por inventar teste sintético.
Antes de S2, escreva em TCC/02 um contrato proposto, com decisões para o autor, cobrindo:
a) índice 0–100 versus Pearson/Spearman versus reuso r;
b) escore bruto/normalizado, vazios, features indisponíveis e identidade;
c) melhor correspondência versus alinhamento um a um, sentenças sem par e prevenção de circularidade entre motores;
d) classes por sentença e por documento, sem atribuir plágio automaticamente;
e) alvo por sentença do siamês versus r documental; preservação semântica de paráfrases exige validação;
f) alvo/features/saída da fusão logística e sua relação com índice contínuo;
g) arquitetura A7 como reprodução parcial ou adaptação, explicitando diferenças;
h) protocolo de split por fonte, múltiplas fontes, calibração, hipóteses, métricas e teste final.
Inclua contraprovas calculadas: índice simétrico pode dar 75 quando r direcional é 50%; com componente lexical nulo e semântico=1, a fusão fixa 60/40 dá 60, não 100. São casos construídos do projeto, não resultados dos artigos.
Não implemente motores de S2. Proponha soluções e sinalize as escolhas científicas que dependem do autor.

7. TESTES, DOCKER E GIT
Execute testes afetados, suíte completa, referências e checks pertinentes. Separe falhas iniciais, correções e saída final. Não force uma contagem e não esconda skips/xfails. Integrações com modelo/corpus precisam dos recursos reais, não mocks no lugar do cálculo.
No Docker, validar config, build e suíte na imagem atual são etapas distintas. Mongo saudável não prova CRUD. Se não houver daemon, registre a limitação. Não reutilize build antigo como prova do código novo.
Confira Git com status/ls-files/check-ignore: privados, .env e artefatos fora; .env.example, código, lock e manifestos necessários incluíveis. Não execute git add indiscriminado. Não faça commit/push. Confira diff e preserve trabalho alheio.

8. ENTREGA E CRITÉRIO DE FECHAMENTO
Atualize TCC/00/01/02/03/04/05/10/11/14 conforme o conteúdo real. Entregue matriz de requisitos, referências, versões, testes/logs, arquivos alterados, ambiguidades respondidas/não respondidas e roteiro manual com comandos PowerShell, diretórios, páginas e sinais de erro.
Separe: (1) núcleo de S1 tecnicamente verificado; (2) limitações de reprodução/adaptações; (3) decisões que bloqueiam S2; (4) pendências exclusivas de fases futuras. Uma escolha futura de GPU não bloqueia fórmula de S1. Uma limitação de artigo pode ser aceita como adaptação declarada, mas nunca como reprodução fiel.
S1 só fecha quando requisitos atuais passam ou têm limitação de escopo explicitamente aceita, evidências correspondem à versão atual e as decisões necessárias para S2 estão identificadas. Não marcar aceite humano sem resposta. Não declarar validade experimental antes dos experimentos.
Finalize com executado/verificado; decidido/proposto; pendente/bloqueado. Dê vereditos separados: "S1 tecnicamente apta: SIM/NÃO" e "S2 metodologicamente liberada: SIM/NÃO", justificando. Não faça commit nem push.