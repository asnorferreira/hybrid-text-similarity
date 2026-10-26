# Sessão 3 — prompt completo atualizado em 2026-10-24

Pedido explícito vigente abaixo autoriza S3. Versão anterior preservada em historico/s3-2026-10-24/06-prompt-sessao3.md; roteiro anterior também preservado. Retomar pelo checkpoint TCC/00 e evidencias/codex-s3; não repetir trabalho íntegro nem iniciar S4. Os critérios seguintes são instruções, não afirmação de aprovação dos testes.

## Contratos concretizados nesta implementação

- Auth scrypt N32768/r8/p3; sessão aleatória32bytes, hash SHA256 no Mongo, expiração8h e cookie HttpOnly/SameSiteStrict. Origin exato/header customizado/CSRF HMAC; sem localStorage. HTTP só loopback ou exceção interna CI explícita, Secure em HTTPS. Não expor senha/token/cookie nos logs.
- Namespace novo hts_s3_development; CI hts_ci_s3. Proprietário obtido da sessão em todas as rotas, sem migração implícita do legado. Seeds exigem conta autenticada. Rate limit Mongo compartilhado; concorrência máxima2 apenas por processo web.
- Dois arquivos até5MiB ou textos convertidos para TXT UTF-8; corpo contado no servidor. DOCX preflight ZIP/XML limitado, sem DTD/entidades/resolução de rede. Texto HTML é conteúdo literal, não markup confiável. Regressões Type1/TXT/segmentação e oráculos S1 preservados.
- Pipeline S2/fórmulas/V2/modelo/IDF preservados. lexical chama core lexical; semântico/híbrido/todos chamam uma vez core hybrid e exibem os componentes identificados. Caracteres só nos melhores pares; E2 diagnóstico e OSA restrita. Não gerar novos escores documentais por conveniência.
- Core mantém JSON1.0, com headers opcionais Server-Timing/RSS/diagnóstico de limpeza. Web devolve envelope próprio com proprietário implícito, documentos, data/modo/engenharia. Não atribuir tempo/memória individual aos algoritmos. IDF observado não vira atestação retroativa.
- Fixtures v2 fixam ZIP create_system=3 e acrescentam DOCX inválido; preservar hashes Linux anteriores e evidências Windows anteriores. Não alterar expected/tolerâncias/deadlines para aprovação.
- Testes reais de navegador com dois usuários, estados normais/modelo ausente/core parado, impressão e isolamento. Auditorias registram distribuições não cobertas. Carga via script Node (sem dependência k6) com protocolo anterior, tentativas completas e percentis nearest-rank; não valida H3. Sem traces/cookies/credenciais nos artifacts.
- CI mantém eventos e permissões já autorizados. Execução40118062459 é histórica S2; só URL/SHA/conclusão consultados sustentam afirmação remota. Push em PR2 já aberto não cria opened; não alterar política para contornar.
- Retenção de evidências: sanitizar também anexos automáticos text/JSON do Playwright, inclusive error-context.md; trace off e JUnit redigido isoladamente não bastam. Regressão com I/O e sonda de origem incorreta verificaram o caminho real; recusa deliberada da sonda é separada das suítes funcionais. Preservar ledger redigido e invalidar somente credencial de teste afetada, sem ler/alterar contas do autor.

## Pedido integral autorizado e critérios

SESSÃO 3 — INTERFACE INTEGRADA, AUTENTICAÇÃO, AUTORIZAÇÃO E TESTES DE SISTEMA

Execute somente a Sessão 3 do projeto hybrid-text-similarity, conforme o escopo autorizado abaixo. Conclua o trabalho verificável e registre impedimentos reais. Não avance para geração do dataset, treinamento, calibração ou avaliação científica das sessões seguintes.

CONTEXTO E AUTORIZAÇÃO

Tema do TCC:
“Desenvolvimento de sistema de comparação de conteúdo de textos.”
Objetivo:
“Buscar as inter-relações entre dois arquivos, buscando o índice de correlação.”

A S1 foi encerrada no escopo verificado. A S2 implementou núcleo híbrido, alinhamento, classificação V2, API e integração web/Mongo.

A execução GitHub Actions 40118062459 foi consultada e terminou com conclusão success para o commit:
ecb14086dde926576e9563df32befc9a74e04bcc

URL:
https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40118062459

Isso é evidência de validação técnica daquele estado, não prova de acurácia, ausência universal de defeitos ou validação das hipóteses do TCC.

Rodadas Linux anteriores tiveram falhas de deadline e preparação semântica. Preserve seus registros; a execução remota posterior aprovada não demonstra retroativamente a causa dessas falhas.

Esta instrução autoriza implementar a S3. Não exige repetir toda a S2 ou fazer merge para começar.

1. REGRAS PERMANENTES

- Não executar commit, push, tag, merge, rebase, reset/clean, abertura de PR, publicação ou deploy.
- Não apagar volumes, dados, alterações existentes ou evidências anteriores.
- Não expor .env, credenciais, senhas, tokens, cookies ou segredos.
- Não publicar docs/, TCC/, pesos, caches ou documentos privados.
- Não inventar dados, resultados, métricas, fontes ou aprovações.
- Não apresentar execução histórica como nova.
- Não alterar esperado, tolerância, configuração ou teste apenas para produzir aprovação.
- Não executar o conjunto final de teste da pesquisa.
- Não gerar dataset final, treinar, calibrar limiares ou alterar hipóteses.
- Não apresentar resultados de desenvolvimento como resultados científicos.
- Não transformar revisão do agente em conferência humana do autor ou aprovação do orientador.
- Não interromper por escolhas rotineiras já cobertas pelo escopo. Resolva-as com justificativa.
- Se surgir decisão científica indispensável ainda não autorizada, apresente a questão específica e continue o trabalho independente dela.

Priorize implementação simples, correta e explicável. Não acrescente funcionalidades apenas porque os artigos as mencionam.

2. LEITURA, ESTADO E PRESERVAÇÃO

Leia:
- AGENTS.md e CLAUDE.md;
- docs/01-guia-base-teorica-e-arquitetura.md;
- docs/02-mapa-formulas-e-arquiteturas.md;
- docs/03-prompts-por-etapa.md;
- docs/05-prompt-sessao2.md;
- docs/06-prompt-sessao3.md, se existir;
- TCC/00, 01, 02, 04, 05, 07, 08, 09, 10, 11 e 14;
- relatórios, matrizes e comandos de codex-s2 e codex-s2-ci;
- contratos e configurações atuais de core e web;
- workflow publicado e evidências disponíveis da execução aprovada.

Se um caminho estiver ausente, procure o correspondente e registre a ausência. Não invente o conteúdo.

Confirme:
- raiz e branch atuais;
- SHA base;
- alterações locais staged, unstaged e não rastreadas;
- correspondência do código com o estado validado;
- versões e configuração efetivamente usadas.

Não faça checkout que sobrescreva alterações. Se houver mudanças posteriores ao SHA validado, identifique-as.

Crie uma pasta nova em TCC/evidencias/ para a S3. Preserve snapshots e evidências anteriores.

Registre a execução remota aprovada com link, evento, SHA e artifacts disponíveis. Não reproduza contagens de testes sem conferir a respectiva saída.

Execute baseline apropriada antes de editar. Não reinstale tudo ou repita escolhas resolvidas sem necessidade.

3. ESCOPO DA S3

Implementar uma aplicação local utilizável, ligada aos serviços reais:

- cadastro, login e logout;
- sessão segura e autorização por proprietário;
- envio de dois arquivos e texto colado;
- comparação usando a implementação S2;
- estados reais de processamento e falha;
- resultado com índice, direções, correspondências, classes e explicações;
- visualização dos textos lado a lado;
- lista de sentenças e mapa de calor;
- seleção dos métodos efetivamente implementados;
- comparação dos métodos no alcance disponível;
- histórico e consulta de resultados próprios;
- relatório pela impressão do navegador;
- testes de sistema, segurança e carga exploratória;
- documentação e prompts atualizados.

Fora desta sessão:
- busca na internet ou em base externa de documentos;
- FAISS;
- OCR;
- inferência de autoria ou conclusão automática de plágio;
- siamês treinado e fusão aprendida;
- geração do dataset final;
- calibração ou resultados finais de pesquisa;
- deploy;
- implementação fictícia de “trecho inserido”.

4. CONTRATOS CIENTÍFICOS A PRESERVAR

Não altere silenciosamente:
- modelo e revisão;
- tokenizador, janelas e pooling;
- IDF/corpus;
- pré-processamento;
- pesos;
- limiares;
- unidade sentença;
- seleção dos pares;
- fórmulas e agregações.

Preserve:
- cosseno semântico bruto;
- C_op=max(0,C);
- F=0,6*C_op+0,4*L;
- índice simétrico por médias direcionais dos máximos de F, ponderadas por palavras;
- alinhamento húngaro explicativo separado do índice;
- classificação por melhor par, permitindo reutilização da fonte;
- Q5-V2 e seus motivos;
- E2 como adaptação diagnóstica;
- OSA explicitamente restrita;
- limitações dos artigos e da reprodução.

Interpretação obrigatória:
- índice não é Pearson/Spearman, probabilidade ou percentual comprovado de plágio;
- “exata” significa igualdade textual após limpeza;
- “editada” e “paráfrase” são rótulos operacionais provisórios;
- “sem correspondência detectada” não comprova originalidade;
- ausência de recurso não é escore zero ou evidência negativa;
- igualdade textual não força índice 100;
- r e metadados do gabarito não entram na inferência.

Não expor campo que permita ao usuário fornecer gabarito como feature.

5. ARQUITETURA E DEPENDÊNCIAS

Reutilize:
- rotas existentes;
- schemas Pydantic/Zod;
- cliente do core;
- caso de uso;
- repositório;
- política de erros;
- contratos compartilhados.

Não reimplemente algoritmos em JavaScript ou em componentes de interface.

Mantenha:
- domínio puro;
- adaptadores para I/O;
- um dono por coleção;
- web responsável pelas comparações/documentos/relatórios;
- core sem persistência duplicada da comparação.

Não crie um segundo sistema de autenticação, upload ou acesso a dados em paralelo ao necessário.

Inspecione dependências antes de acrescentar bibliotecas. Consulte documentação oficial atual para APIs e compatibilidade. Registre finalidade, versão, licença pertinente e alteração no lock.

Adicione somente ferramentas necessárias à S3, por exemplo biblioteca de hash de senha, interface, testes de navegador, auditoria e carga.

Não migre Python/Node/Next ou atualize toda a pilha por conveniência. Se necessário, demonstre a razão e valide a mudança.

Não introduza serviços externos de autenticação, analytics, armazenamento ou IA sem necessidade e autorização.

6. AUTENTICAÇÃO LOCAL

Implemente cadastro, login e logout reais, sem contas ou sucessos simulados.

Senhas:
- hash apropriado para senhas, com salt e parâmetros registrados;
- nunca armazenar texto puro ou hash rápido genérico;
- não registrar senha ou hash em logs;
- limite de entrada documentado, sem truncamento silencioso;
- bibliotecas e configuração fundamentadas em documentação oficial.

Sessões:
- token imprevisível;
- armazenamento e expiração definidos;
- cookie HttpOnly;
- SameSite adequado ao fluxo;
- Secure quando houver HTTPS;
- exceção de desenvolvimento HTTP restrita e documentada;
- invalidação no logout;
- rotação ao autenticar, quando pertinente;
- nenhuma sessão sensível em localStorage.

A arquitetura da sessão deve ser simples e testável. Se escolher sessão persistida no banco, armazene o identificador de forma que um vazamento da coleção não exponha diretamente sessões utilizáveis.

Não adicionar “lembrar de mim”, recuperação de senha por e-mail ou fluxos externos não solicitados. Informe claramente funcionalidades ausentes.

Proteja operações mutáveis contra CSRF conforme a arquitetura escolhida. SameSite isoladamente não deve ser tratado como prova universal de proteção.

Use respostas que não exponham dados sensíveis ou detalhes internos desnecessários.

7. AUTORIZAÇÃO E PROPRIEDADE DOS DADOS

Toda operação de documento, comparação, histórico ou relatório deve verificar o usuário autenticado e a propriedade no servidor.

- Não confiar em user_id enviado pelo navegador.
- Não usar filtro apenas na interface.
- Não permitir consulta por ID de outro usuário.
- Não expor contagens, títulos ou conteúdo de terceiros.
- Aplicar autorização às rotas existentes da S2, não somente às novas telas.
- Não deixar uma rota alternativa antiga sem proteção.

Dados anteriores da S2 sem proprietário:
- não atribuí-los automaticamente ao primeiro usuário;
- preservar e identificar como dados legados/de desenvolvimento;
- restringir sua exposição;
- se houver migração, torná-la explícita, idempotente e não destrutiva;
- não vincular documentos globalmente por hash de modo que revele dados de outro usuário.

Proteja o core como serviço interno:
- não confiar apenas na ausência de link na interface;
- revisar exposição de portas no Compose;
- impedir acesso indevido às funções internas pela configuração apropriada;
- preservar o fluxo autorizado web→core.

8. INTERFACE E EXPERIÊNCIA DE USO

Construa uma interface sóbria, clara, em PT-BR e adequada à apresentação acadêmica.

Não depender de um design elaborado para completar o fluxo.

Inclua:
- navegação consistente;
- estados vazios e de erro;
- rótulos acessíveis;
- foco visível e uso por teclado;
- contraste adequado;
- layout responsivo;
- informação transmitida também por texto, não apenas por cor.

Não invente notificações, histórico, escores, tempos, usuários ou gráficos para preencher a tela.

Use mocks somente em testes ou demonstrações explicitamente identificadas. O fluxo principal deve consumir dados reais.

9. ENTRADA E PROCESSAMENTO

Permita:
- selecionar dois arquivos suportados;
- identificar fonte e documento analisado;
- alternativa de texto colado;
- seleção do método/modo implementado.

Valide no servidor:
- tamanho;
- conteúdo real e formato;
- extensão quando pertinente ao contrato;
- texto útil;
- limites de caracteres, sentenças e tokens;
- requisições inválidas ou incompletas.

Não confiar apenas em MIME ou extensão fornecidos pelo cliente.

Para DOCX/ZIP e parsing:
- limitar tamanho e expansão de forma apropriada;
- investigar estruturas inválidas sem inventar suporte;
- não permitir caminhos de arquivo arbitrários;
- não executar conteúdo do documento;
- tratar nomes de arquivo como dados não confiáveis;
- preservar a regressão de XML inválido;
- avaliar comportamento do parser quanto a entidades externas conforme a configuração real.

Para PDF:
- preservar a correção Type1 e seus controles;
- não tentar OCR;
- comunicar proteção, corrupção ou ausência de texto de forma compreensível.

Estados da interface:
- aguardando entrada;
- enviando, com progresso real somente se mensurável;
- processando, com indicador indeterminado;
- concluído;
- falha;
- resultado parcial ou modo separado somente conforme contrato.

Não inventar porcentagem de processamento, cancelar apenas visualmente uma operação ou afirmar conclusão antes da resposta real.

Se houver timeout, diferencie perda de resposta de cancelamento efetivo no servidor. Não prometa cancelamento que não foi implementado.

10. RESULTADO E EXPLICAÇÕES

Apresente separadamente:

A. Índice híbrido
- valor em 0–100;
- nome “índice de similaridade”;
- componentes direcionais;
- método/configuração;
- limitações e estado de disponibilidade.

B. Correspondências
- sentença de origem e do documento analisado;
- escores lexical, semântico bruto, operacional e fundido;
- classe e motivo;
- identificação do par usado na classificação;
- distinção do par exclusivo do alinhamento.

C. Textos lado a lado
- conteúdo extraído/limpo identificado;
- destaque coerente com os resultados;
- legenda acessível;
- indicação de alterações feitas pelo parsing.

Não prometer marcação fiel sobre o PDF original se existem somente textos extraídos.

Use índices/offsets reais da representação comparada. Não localizar sentenças repetidas com uma busca textual ingênua que destaque a ocorrência errada.

Se forem necessários offsets adicionais, acrescente-os de modo compatível, testado e sem alterar fórmulas/segmentação.

D. Mapa de calor
- matriz identificada;
- eixos fonte × documento analisado;
- escala e legenda;
- valores reais;
- navegação/seleção dos pares;
- tratamento utilizável de matrizes maiores;
- ausência de representação enganosa de recurso indisponível.

E. Resumo documental
- distribuição por contagem de sentenças;
- denominador explícito;
- empate sem predominância;
- rótulos operacionais;
- “trecho inserido” indisponível;
- nenhuma conversão automática em declaração de plágio ou originalidade.

Arredonde somente na apresentação, segundo a regra registrada. Preserve a precisão do resultado persistido.

Não apresentar acurácia, F1, confiança ou probabilidade calibrada nesta tela sem resultado experimental correspondente.

11. SELETOR DE MÉTODOS E MODO “RODAR TODOS”

Liste apenas métodos realmente implementados e disponíveis.

Identifique:
- lexical;
- semântico;
- híbrido;
- algoritmos de caracteres e sua unidade;
- diagnósticos E2;
- variante OSA.

Não apresentar E2/hash como escore contínuo comparável aos demais.

Para cada método, informe:
- unidade: documento, sentença ou par;
- agregação;
- normalização;
- limites de entrada;
- disponibilidade;
- configuração.

Não misture distância bruta e similaridade percentual sem identificação.

No modo “rodar todos”:
- execute cálculos reais;
- preserve limites computacionais;
- não repetir silenciosamente cálculos caros quando forem compartilháveis;
- não apresentar falha de um método como zero;
- exibir erros e indisponibilidade por método.

Se a API S2 não oferecer dados suficientes para esse modo, implemente a extensão mínima do contrato, com testes core↔web e compatibilidade identificada.

Não modificar o significado do índice híbrido para acomodar o seletor.

12. TEMPO E MEMÓRIA: INSTRUMENTAÇÃO HONESTA

Antes de exibir tempo e memória, defina e registre o protocolo operacional.

Diferencie:
- tempo de preparação/carregamento;
- tempo de parsing;
- pré-processamento;
- embeddings;
- comparação;
- persistência;
- tempo total percebido pelo cliente.

Use relógio monotônico para durações. Identifique compartilhamento de etapas e não atribua o mesmo custo integral a vários algoritmos como se fossem execuções independentes.

Para memória:
- informe o que foi medido: processo, serviço, container ou alocação específica;
- diferencie RSS de alocações Python;
- não apresentar tracemalloc como memória total de bibliotecas nativas;
- não chamar diferença de RSS de pico sem medição correspondente;
- não inventar memória por algoritmo em processo compartilhado;
- sem GPU ativa, não apresentar consumo GPU fictício.

Quando não houver medida defensável por algoritmo, informe “não medido individualmente” e apresente somente a medida realmente disponível, com unidade e escopo.

Essas medições são instrumentação de engenharia/desenvolvimento. Não validam H3 ou substituem os experimentos posteriores.

Não compare tempos de chamadas com cache e sem cache sem identificar a condição.

13. HISTÓRICO E IMPRESSÃO

Histórico:
- somente comparações do usuário autenticado;
- paginação e ordenação determinística;
- estado, data, método e resumo;
- acesso ao resultado persistido;
- indicação de configuração/modelo usados naquela execução;
- resultado antigo não recalculado silenciosamente com configuração nova.

Persistência:
- preserve a sinalização das falhas parciais;
- não exponha comparação incompleta como concluída;
- retentativa idempotente;
- não apagar registros órfãos automaticamente sem política autorizada.

Impressão:
- relatório pelo navegador;
- layout de impressão legível;
- sem controles desnecessários;
- índice, identificação dos documentos, métodos e limitações;
- paginação sem cortes relevantes;
- cabeçalhos de tabelas quando aplicável;
- não incluir tokens ou informações de sessão.

Não apresentar impressão como exportação de um PDF original anotado.

14. SEGURANÇA E LIMITES OPERACIONAIS

Implemente e teste, no alcance local:
- autenticação e autorização;
- rate limiting apropriado, especialmente login e comparação;
- limites de upload e corpo;
- validação de entradas;
- proteção contra XSS ao exibir texto dos documentos;
- proteção contra CSRF conforme a arquitetura;
- consultas Mongo sem operadores controlados pelo usuário;
- erros sanitizados;
- ausência de segredos em responses/logs;
- acesso interno ao core;
- exposição mínima de serviços.

Não renderizar documento do usuário como HTML confiável.

Defina a abrangência do rate limiting: processo único, múltiplos processos ou armazenamento compartilhado. Não afirmar proteção distribuída com contador local.

Execute npm audit e pip-audit, ou ferramentas equivalentes justificadas.

Para achados:
- registrar fonte/data/versão;
- distinguir vulnerabilidade aplicável, dependência transitiva e falso positivo fundamentado;
- corrigir dentro do escopo quando possível;
- não executar atualização forçada em massa;
- não ocultar avisos com ignore genérico;
- não afirmar segurança completa por ausência de alertas.

Não realizar testes ofensivos contra terceiros ou serviços externos.

15. TESTES DE SISTEMA

Acrescente testes significativos, sem substituir o comportamento real por mocks em todo o fluxo.

Unitários/contrato:
- sessão e expiração;
- validação de entrada;
- autorização;
- contratos novos;
- tratamento de indisponibilidade;
- formatação/precisão exibida;
- seleção/destaque de sentenças repetidas;
- distribuição, empate e estados vazios.

Integração:
- autenticação e persistência reais;
- fluxo web→core→Mongo;
- dois arquivos de desenvolvimento;
- consulta do resultado persistido;
- retentativas e falhas parciais;
- separação entre usuários.

Playwright:
1. cadastrar usuário A;
2. autenticar;
3. enviar arquivos públicos/de desenvolvimento;
4. acompanhar estados reais;
5. conferir resultado e correspondências;
6. consultar histórico;
7. abrir resultado persistido;
8. verificar apresentação de impressão;
9. sair e confirmar bloqueio;
10. autenticar usuário B e demonstrar que não acessa dados de A.

Inclua:
- acesso direto por URL/ID;
- requisição sem sessão;
- sessão expirada/inválida;
- arquivo incompatível ou malformado;
- limite excedido;
- core/modelo indisponível;
- texto com conteúdo semelhante a HTML/script, exibido como texto.

Use execução real para o fluxo principal. Identifique mocks nos testes de falha e não os apresente como integração real.

Impressão:
- verificar modo print e conteúdo;
- quando possível gerar um PDF de teste e inspecionar o resultado;
- explicitar o limite de automação do diálogo nativo do navegador;
- não afirmar revisão visual humana que não ocorreu.

Não criar teste que apenas verifica texto fixo ou snapshot sem comportamento relevante.

16. CARGA EXPLORATÓRIA

Execute uma linha de base de engenharia com ferramenta apropriada, como k6.

Antes da execução, registre:
- objetivo;
- cenário;
- ambiente e recursos;
- versões;
- dados de desenvolvimento;
- tamanho dos arquivos e sentenças;
- concorrência;
- duração;
- condição de cache;
- endpoints e autenticação;
- métricas e eventuais critérios operacionais.

Não faça benchmark simultaneamente com build, suíte pesada ou outras tarefas que comprometam a interpretação. Se ocorrer interferência, registre.

Comece com carga pequena e aumente de forma controlada, sem comprometer dados ou serviços de uso pessoal.

Meça, quando aplicável:
- latência p50/p95/p99;
- vazão;
- respostas por status;
- taxa de erro;
- timeouts;
- recursos observáveis.

Interprete percentis considerando o número de observações; não apresentar amostra pequena como estimativa estável.

Não inventar meta de desempenho como se tivesse sido aprovada.
Não escolher somente a melhor rodada.
Não esconder erros ou saturação.
Não executar carga contra o GitHub ou serviços externos.

Essas medições não são teste final da pesquisa nem validação de H3. Registre-as separadamente de TCC/13.

Se a carga revelar falha funcional ou isolamento incorreto, investigue. Baixo desempenho, por si só, deve ser relatado com condições e impacto.

17. CI E GITHUB ACTIONS

Preserve a política autorizada:
- push apenas na main;
- pull_request destinado à main apenas com types: [opened].

Não adicionar synchronize, reopened, workflow_dispatch, schedule ou outro gatilho sem nova autorização.

Não ampliar permissões ou introduzir deploy.

Atualize os jobs/comandos de validação para cobrir as alterações pertinentes da S3, sem duplicar desnecessariamente toda a pilha.

Separe:
- testes determinísticos;
- integração/E2E;
- medições exploratórias de carga.

Não transformar variação de benchmark em teste determinístico artificial. Falhas funcionais e de segurança continuam tratadas como falhas.

Use fixtures públicas ou geradas deterministicamente. O runner não pode depender de docs/TCC privados, banco do autor ou caches locais.

Artifacts:
- somente evidências técnicas necessárias;
- retenção definida;
- sem documentos privados, credenciais, cookies ou banco;
- traces/screenshots apenas com usuários e dados de teste;
- não incluir segredos capturados em requests;
- permitir coleta em falha sem mascarar a falha do job.

Não executar commit/push ou abrir PR para disparar CI. Prepare arquivos e informe os passos manuais ao autor.

Como apenas opened dispara PR, explique que pushes posteriores em PR já aberto não iniciam nova execução.

Não declarar execução remota sem URL, SHA e conclusão realmente consultados.

18. VERIFICAÇÃO E PRESERVAÇÃO FINAL

Execute conforme as alterações:
- testes core;
- testes web;
- typecheck;
- build;
- integração;
- Playwright;
- auditorias;
- carga exploratória;
- Docker pertinente.

Não usar contagem histórica como meta.

Para cada falha, skip ou xfail:
- registrar motivo;
- impacto;
- causa encontrada ou “não determinada”;
- correção ou pendência;
- execução posterior, preservando a anterior.

Diferencie:
- defeito de implementação;
- erro de método;
- incerteza experimental;
- limitação operacional.

Não exigir acurácia perfeita ou resultados favoráveis. Não aceitar defeito conhecido como “margem de erro acadêmica”.

Confirme preservação de:
- fórmulas;
- política V2;
- modelo/revisão;
- corpus/IDF;
- regressões S1;
- contratos S2 não alterados deliberadamente;
- LICENSE/NOTICE;
- exclusões privadas.

19. DOCUMENTAÇÃO E PRÓXIMOS PROMPTS

Atualize conforme afetados:
- TCC/00;
- TCC/01 e TCC/02;
- TCC/07;
- TCC/08;
- TCC/09;
- TCC/10;
- TCC/11;
- TCC/14;
- README público;
- docs/03 e prompt completo S3.

Preserve H1–H3 e o protocolo científico sem reescrevê-los para acomodar resultados de desenvolvimento.

Registre decisões de engenharia separadamente de resultados.

Revise os prompts das sessões seguintes:
- incorpore contratos e limitações atuais;
- ajuste dependências e testes;
- preserve versões anteriores;
- não antecipar implementação S4/S5;
- mantenha pendências científicas antes de seu uso;
- preserve divisão por documento-fonte antes da geração de pares;
- mantenha IDF experimental ajustado somente com fontes permitidas pelo protocolo;
- mantenha congelamento antes do teste final.

Não transforme uma hipótese em aprovação do orientador.

20. CRITÉRIOS DE ENCERRAMENTO

A S3 pode ser declarada concluída no alcance verificado quando:

- autenticação e logout reais funcionarem;
- autorização proteger todas as rotas e dados pertinentes;
- usuário B não acessar dados de A;
- envio/texto colado consumir o fluxo real;
- estados e erros forem compreensíveis;
- resultado preservar o significado dos cálculos;
- textos, correspondências e mapa de calor forem coerentes;
- métodos disponíveis forem identificados corretamente;
- histórico próprio funcionar;
- impressão estiver utilizável;
- instrumentação não inventar tempo/memória;
- testes pertinentes passarem;
- segurança tiver achados tratados ou pendências explicitamente avaliadas;
- carga exploratória estiver registrada ou impedimento obrigatório declarado;
- documentação e evidências estiverem atualizadas.

Não exigir dataset final, treinamento, calibração ou eficácia científica para encerrar a engenharia desta etapa.

Não dispensar silenciosamente requisito obrigatório. Se algo ficar incompleto, indique exatamente o impedimento e declare S3 não concluída no respectivo alcance.

21. ENTREGA

Retorne:

1. O que foi implementado e por quê.
2. Matriz requisito → implementação → teste/evidência → status.
3. Comandos, diretórios, versões, saídas e códigos de retorno.
4. Resultados reais dos testes e auditorias.
5. Medições exploratórias com ambiente e limitações.
6. Alterações de contratos/configuração e sua justificativa.
7. Falhas e tentativas preservadas.
8. Arquivos novos/alterados.
9. Pendências S3 separadas de trabalho futuro.
10. Roteiro manual curto para o autor:
    - endereço local;
    - como preparar usuário de teste;
    - arquivos públicos para comparar;
    - o que observar;
    - como registrar divergência.
11. Situação do workflow e passos manuais para validação remota.
12. Prompts seguintes atualizados quando necessário.

Não peça ao autor que certifique código, fórmulas ou segurança sem competência técnica. Sua conferência deve ser de comportamento observável; a evidência técnica vem das verificações documentadas.

Finalize com:
“S3 concluída no escopo verificado”
ou
“S3 não concluída”,
com justificativa objetiva.

Pare sem iniciar a Sessão 4. Não faça commit, push, merge, publicação ou deploy.
