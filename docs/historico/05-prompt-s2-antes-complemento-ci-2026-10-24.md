# Sessão 2 — prompt autorizado em 2026-10-24

Q5-V2 adotada explicitamente pelo autor no pedido de implementação. A edição anterior foi preservada em [histórico](historico/05-prompt-sessao2-antes-implementacao-2026-10-24.md). Estado e evidências de execução: [checkpoint](../TCC/00-indice.md) e TCC/evidencias/codex-s2/. Autorização não é evidência de execução, desempenho ou validação científica. Não iniciar S3 automaticamente.

SESSÃO 2 — IMPLEMENTAÇÃO DO NÚCLEO HÍBRIDO, ALINHAMENTO, ÍNDICE E INTEGRAÇÃO

Execute a Sessão 2 do projeto hybrid-text-similarity até concluir os requisitos autorizados e verificáveis abaixo. Não avance para a Sessão 3.

Esta instrução autoriza:
- adotar Q5-V2 como baseline provisória, nos termos definidos abaixo;
- registrar essa decisão e atualizar os prompts afetados;
- implementar e testar a Sessão 2.

A adoção é uma decisão de desenvolvimento do projeto. Não comprova desempenho, reprodução integral dos artigos, aprovação do orientador ou validade das hipóteses científicas.

CONTEXTO ACADÊMICO

Tema do TCC:
“Desenvolvimento de sistema de comparação de conteúdo de textos.”
Objetivo:
“Buscar as inter-relações entre dois arquivos, buscando o índice de correlação.”

O sistema compara dois arquivos em PT-BR e apresenta relações textuais, escores e explicações. O índice definido pelo projeto é um índice de similaridade, não um coeficiente estatístico de correlação nem prova conclusiva de plágio.

Priorize implementação simples, correta, rastreável e reproduzível. Não acrescente complexidade sem necessidade demonstrada.

1. REGRAS OBRIGATÓRIAS

- Não executar commit, push, tag, merge, rebase, reset, clean, PR, publicação ou release.
- Não apagar volumes, dados, evidências ou alterações existentes.
- Não alterar as exclusões de arquivos privados para facilitar versionamento.
- Não abrir, imprimir ou copiar segredos de .env.
- Não inventar métricas, resultados, fontes, citações, versões, aprovações ou arquivos ausentes.
- Não apresentar execução planejada ou histórica como execução atual.
- Não alterar esperado, tolerância, prazo de teste ou regra científica apenas para obter aprovação.
- Não executar treinamento, calibração, geração do dataset final ou avaliação no conjunto final de teste.
- Não apresentar exemplos de desenvolvimento como resultados da pesquisa.
- Não iniciar telas da S3 ou tarefas de S4/S5.
- Não repetir perguntas já respondidas. Resolva escolhas rotineiras de implementação dentro destes contratos.
- Se uma decisão científica nova for indispensável, apresente a dúvida específica e continue o trabalho independente dela.

2. RETOMADA E PRESERVAÇÃO

Leia antes de editar:
- AGENTS.md e CLAUDE.md;
- docs/01-guia-base-teorica-e-arquitetura.md;
- docs/02-mapa-formulas-e-arquiteturas.md;
- docs/03-prompts-por-etapa.md;
- docs/05-prompt-sessao2.md;
- TCC/00-indice.md;
- TCC/01-decisoes.md;
- TCC/02-metodologia.md;
- TCC/03-formulas-e-calculos.md;
- TCC/04-parsing.md;
- TCC/05-core.md;
- TCC/07-backend.md;
- TCC/09-banco-e-seeds.md;
- TCC/10-docker.md;
- TCC/11-testes.md;
- TCC/14-pendencias.md;
- evidências de encerramento documental da S1 e preparação da S2;
- decisoes-s2.md e proposta-classes-v2.md dessa entrega.

O escopo explicitamente autorizado neste prompt resolve Q5-V2 e prevalece sobre registros anteriores que ainda a indiquem como não respondida. Preserve esses registros como históricos.

Confirme a raiz e registre:
- estado atual do Git, incluindo staged, modificados e novos;
- versões realmente utilizadas;
- hashes dos arquivos relevantes;
- diferenças em relação à entrega técnica anterior.

Crie uma pasta nova em TCC/evidencias/ para esta execução. Preserve logs anteriores.

A S1 está concluída no escopo implementado e verificado. O autor confirmou somente a correspondência visual das cinco amostras indicadas. Não atribua a ele auditoria do código, execução de comandos, revisão integral dos artigos ou validação Docker.

Os 177 testes Windows e 177 Docker são resultados históricos documentados. Não são contagem obrigatória nem resultado novo da S2.

Execute uma baseline apropriada antes das alterações. Se houver divergência real que comprometa a S2, investigue e registre. Não reinicie toda a S1 sem justificativa.

3. BASE DA S1 A PRESERVAR

Preserve:
- parsers PDF, DOCX e TXT;
- correção Type1/WinAnsi 173 no gerenciador por PDF;
- respeito a ToUnicode e Differences explícitos;
- isolamento dos mapas entre documentos e threads;
- tratamento de U+00AD, espaços e hífens reais;
- erros explícitos para PDF protegido, corrompido, vazio ou sem texto;
- TXT UTF-8/cp1252 estritos, sem substituição silenciosa;
- segmentação de domínios, URLs, e-mails, versões, decimais, iniciais, abreviações e pontuação;
- junções múltiplas e política documentada de compostos;
- perfis lexical e semântico existentes;
- fórmulas e referências matemáticas conferidas.

Não introduza OCR, correção por dicionário ou LLM para reconstruir caracteres.

TF-IDF:
- fórmula exata do A1 continua nos testes de referência;
- o sistema usa o IDF suavizado do corpus de referência provisório identificado;
- não ajustar IDF aos dois arquivos comparados;
- não reconstruir, substituir ou migrar corpus/identidade silenciosamente;
- descritor observado do pipeline não é atestação retroativa da construção histórica.

E2:
- adaptação top-k/TF-IDF/conjunto/BLAKE2b64/soma modular;
- parâmetros provisórios permanecem identificados;
- assinatura igual não comprova identidade textual ou semântica;
- não usar o inteiro do hash como feature contínua;
- não pular motores por igualdade de assinatura;
- manter diagnóstico/triagem separado da fusão fixa.

OSA:
- identificar como Damerau–Levenshtein restrita / Optimal String Alignment;
- preservar custos, normalização e contratos existentes;
- não substituir pela variante irrestrita;
- não atribuir ao A4 uma escolha de variante não demonstrada.

A3:
- preservar direções explícitas, tamanho externo e erros para casos indefinidos;
- manter adaptação por contagem separada;
- não inventar listas, unidades ou entradas ausentes;
- não alegar reprodução integral de Textract/IQ ou das tabelas.

4. AMBIENTE E DEPENDÊNCIAS

Inspecione pyproject, lock, seletor Python, Dockerfile, Compose e configuração web antes de instalar.

Não atualize tudo preventivamente. Preserve a baseline quando compatível e acrescente apenas dependências necessárias à S2.

Para cada dependência nova ou atualização necessária, registre:
- finalidade;
- versão efetiva;
- compatibilidade com Python/Node e demais pacotes;
- fonte oficial e licença pertinente;
- alteração no lock;
- testes executados.

Confira documentação oficial atual ao usar APIs ou escolher versões. Não copie implementação de terceiros.

Não migre Python apenas porque existe versão mais nova. Se uma migração for realmente necessária, documente a causa e valide ambiente local e Docker sem apagar o ambiente anterior.

Para o módulo web, confira a versão Node LTS suportada e o patch efetivo nas fontes oficiais. Fixe as versões pertinentes.

Não instale antecipadamente ferramentas de geração de dataset, treino ou experimentação futura.

5. CONTRATO DOS DADOS E FRONTEIRAS

Entrada:
- dois arquivos PT-BR PDF/DOCX/TXT ou textos, conforme os contratos existentes;
- unidade de comparação: sentença;
- limites operacionais explícitos e configuráveis;
- identificação inequívoca de fonte e suspeito para as saídas direcionais.

O índice global é simétrico. A classificação das sentenças e o resumo documental são direcionais, tomando o suspeito como documento analisado.

Reutilize o parsing existente na fronteira apropriada. Não implemente os mesmos algoritmos novamente em JavaScript.

O core não persiste a comparação. O web é o dono dessa persistência.

Não aceite r, classe sintética, origem do gabarito ou metadados de geração como entrada das features, seleção de pares ou inferência. IDs servem à rastreabilidade, não ao cálculo.

Domain permanece puro:
- sem I/O, HTTP, banco ou acesso a arquivos;
- sem imports de torch, transformers ou Sentence-Transformers;
- cálculos recebem valores e vetores dos adaptadores.

6. E3 — MOTOR SEMÂNTICO REAL E REPRODUZÍVEL

Modelo escolhido:
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Revisão registrada na preparação:
e8f8c211226b894fcb81acc59f3b34ba3efd5f42

Confira a existência da revisão, licença, configuração, tokenizador e limite efetivo antes do uso. O registro documental anterior não significa que os pesos já estejam disponíveis ou testados.

Não substituir por main flutuante ou outro modelo silenciosamente. Se a revisão estiver indisponível, registre o impedimento e proponha a substituição fundamentada antes de aplicá-la.

Implemente:
- preparação explícita do cache separada do build da aplicação;
- modelo/configuração/tokenizador fixados na revisão;
- inferência local, sem serviço externo de embeddings;
- modo de avaliação, sem gradientes;
- versões, configuração, hashes e identidade do modelo rastreáveis;
- uso do cache após preparo;
- ausência de modelo com estado explícito;
- pesos e cache fora do Git e de exportações comuns.

Sentenças longas:
- usar janelas internas completas e não sobrepostas;
- respeitar a capacidade efetiva, incluindo tokens especiais;
- cobrir todos os tokens de conteúdo;
- não truncar silenciosamente;
- não perder conteúdo por retokenização;
- normalizar o embedding de cada janela;
- calcular média ponderada pelo número de tokens de conteúdo;
- normalizar o vetor agregado por L2;
- média/vetor nulo é indisponibilidade explícita.

A sentença continua sendo a unidade. Janelas não viram novas sentenças ou parágrafos.

Documente o pooling como adaptação do projeto, ainda sem desempenho validado. Para uma janela, preserve equivalência com a mesma política de normalização.

7. MATRIZES, COSSENO E FUSÃO

Produza antes de selecionar correspondências:
- L: matriz lexical;
- C: matriz de cossenos semânticos brutos;
- C_op: matriz semântica operacional;
- F: matriz fundida.

Cosseno:
C_op = max(0, C), para C válido em [-1,1].

Preserve C bruto para auditoria.
- Zero não vira 0,5.
- Não finitos e violações reais do intervalo são erros.
- Eventual correção de arredondamento deve ter tolerância pequena, justificada e testada.
- Vetor de norma zero não recebe cosseno inventado.

Fusão:
F_ij = 0,6 * C_op_ij + 0,4 * L_ij

Pesos fixos nesta etapa. Não renormalizar por disponibilidade.

Casos degenerados:
- documento sem texto, sem sentenças ou sem peso útil: erro explícito, sem nota;
- texto válido sem representação lexical: L=0 com flag;
- falha de carregamento do IDF não é vetor lexical nulo válido;
- modelo semântico ausente: híbrido indisponível;
- lexical pode funcionar em modo separado, claramente identificado;
- indisponibilidade não é zero, classe negativa ou originalidade.

Igualdade textual pode ser informada separadamente. Não forçar F ou I a 100 por igualdade.

8. ÍNDICE DE SIMILARIDADE

Use w_i como número de palavras segundo word_count da S1.

M(A→B) = soma_i(w_i * max_j(F_ij)) / soma_i(w_i)

Calcule também M(B→A).

I = 100 * [M(A→B) + M(B→A)] / 2

Requisitos:
- usar a matriz completa;
- permitir reutilização de correspondências;
- preservar valores sem arredondamento intermediário;
- arredondar somente na apresentação;
- documentar regra de arredondamento;
- expor os dois componentes direcionais;
- não usar a soma do alinhamento húngaro como índice;
- não identificar I com 100*r;
- não alegar correlação empírica com r sem avaliação posterior.

Pearson/Spearman são métricas de avaliação futura, não esta função.

9. E4 — ALINHAMENTO EXPLICATIVO

Implemente atribuição um a um pelo algoritmo húngaro para maximizar a soma não ponderada de F.

- Trate matrizes retangulares.
- Pares de ganho zero ficam sem correspondência.
- Permita nós fictícios de ganho zero quando necessários.
- Exponha sentenças não pareadas.
- Defina desempate determinístico sem alterar o valor ótimo.
- Preserve índices e rastreabilidade das sentenças.

O alinhamento é uma explicação separada. Não limita as correspondências usadas pelo índice ou pelas classes.

Classificação:
- para cada sentença do suspeito, selecione o melhor par por F;
- permita reutilizar uma sentença da fonte;
- defina desempate determinístico;
- calcule algoritmos de caracteres nos pares selecionados após a seleção;
- caracteres não retroagem à matriz que escolheu o par.

Evite dependência circular entre matriz, alinhamento e motores.

Identifique essa arquitetura como adaptação do projeto, sem alegar reprodução integral do alinhamento de palavras do A9.

10. Q5-V2 — CLASSIFICAÇÃO PROVISÓRIA AUTORIZADA

Registre a adoção atual em TCC/01, TCC/02, TCC/14 e no prompt S2, preservando a proposta anterior e a data real da decisão.

A regra abaixo é uma baseline de desenvolvimento. Limiares são provisórios, configuráveis e versionados. Não calibrar nesta sessão.

Entradas do par selecionado:
- L: cosseno lexical;
- C_op: cosseno semântico operacional;
- D: similaridade de Levenshtein;
- S = max(L, C_op).

D = 1 - distância_Levenshtein / max(comprimentos)

Calcule D sobre os textos limpos no perfil semântico S1, sensível a maiúsculas, conforme a V2. Defina explicitamente o contrato dos casos vazios sem usar o caso 0/0.

Ordem obrigatória:

0. Entrada ou componente obrigatório inválido/indisponível:
   retornar estado técnico explícito; não atribuir classe negativa.

1. Textos do par não vazios e iguais após limpeza/perfil semântico:
   classe operacional “cópia exata”.

2. Sem igualdade e D >= 0,80:
   classe operacional “cópia editada”.
   Essa regra tem prioridade sobre paráfrase e sobre o corte abaixo.

3. Sem edição detectada e S <= 0,30:
   “sem correspondência detectada”;
   motivo: escores baixos sem evidência estrutural.

4. Nos demais pares, C_op > 0,75:
   classe operacional “paráfrase”.

5. Demais casos:
   “sem correspondência detectada”;
   motivo: evidência insuficiente pelas regras.

Requisitos de interpretação:
- TF-IDF alto sozinho não determina “editada”.
- O limiar lexical 0,85 pode permanecer como diagnóstico provisório, sem gatilho de classe.
- O corte 0,30 distingue motivos de ausência de correspondência nesta hierarquia; não inventar efeito adicional.
- “Exata” significa igualdade da representação textual, não dos arquivos.
- “Editada” indica semelhança estrutural conforme a regra, sem provar derivação.
- “Paráfrase” é um rótulo operacional, sem provar intenção ou equivalência semântica.
- “Sem correspondência detectada” não comprova originalidade.
- Estados técnicos indisponíveis permanecem separados.

Preserve escores e motivos para permitir inspecionar a decisão.

F e I não incluem D. Portanto, classe estrutural e nota híbrida podem divergir. Mostre a divergência sem alterar silenciosamente a fórmula.

Resumo documental:
- distribuição por contagem das sentenças do suspeito;
- proporções e denominador explícitos;
- predominância identificada como resumo das regras;
- empate: “sem predominância”;
- não atribuir ao documento os tipos sintéticos C0–C7;
- “trecho inserido”: explicitamente indisponível nesta etapa.

A indisponibilidade de “trecho inserido” está autorizada para a S2; permanece pendência do escopo global, sem regra fictícia e sem exclusão silenciosa do projeto.

11. API /v1 E CONTRATO CORE↔WEB

Implemente a API Flask interna e o módulo comparison do web no alcance definido nos documentos.

Inclua:
- schemas Pydantic no core;
- schemas Zod no web;
- contrato explícito de requisição, resposta, erros e limites;
- cliente, caso de uso e persistência pelo dono correto;
- identificação de método, configuração, modelo, IDF e versão da política;
- escores brutos, operacionais, pares, estados e flags pertinentes.

Não devolva probabilidade ou confiança calibrada sem modelo/avaliação que a sustente.

Rejeite campos de gabarito quando forem enviados indevidamente à inferência. Não ignore silenciosamente contratos incompatíveis.

Diferencie:
- entrada inválida;
- formato não suportado;
- extração falhou;
- documento sem conteúdo útil;
- recurso obrigatório indisponível;
- resultado calculado.

A S2 inclui integração funcional, não telas completas da S3. Não crie interface simulada para fingir integração.

Siamês e fusão aprendida continuam indisponíveis até suas etapas próprias.

12. PERSISTÊNCIA E SEEDS

Respeite um dono por coleção:
- web persiste os documentos, comparações e relatórios pertinentes;
- core não duplica a persistência da comparação;
- coleções de dataset/experimentos só entram quando efetivamente necessárias nas etapas futuras.

Implemente somente persistência necessária ao fluxo autorizado.

Seeds:
- fixos e identificados como desenvolvimento;
- comando coordenador chama cada dono;
- execução idempotente;
- não apagar dados existentes;
- não confundir dados de desenvolvimento com dataset da pesquisa.

Use namespace de desenvolvimento isolado para testes. Registre criação e uso sem atingir dados do usuário.

Comparação síncrona e progresso indeterminado. Não criar fila sem medição que justifique.

13. TESTES MATEMÁTICOS E DE CONTRATO

Esperados devem vir de conta independente, propriedade matemática ou referência conferida. Não usar a própria função testada para gerar seu esperado.

Doubles podem testar fronteiras, indisponibilidade e erros. Não substituem integração com modelo/API/banco reais.

Inclua:

A. Cosseno
- [1,0] contra [1,0], [0,1] e [-1,0]: 1, 0 e -1;
- transformação operacional: 1, 0 e 0;
- vetor nulo e não finitos com estado explícito.

B. Fusão
- L=1/2 e C_op=3/4:
  F=13/20=0,65;
- componente indisponível não vira zero nem altera pesos.

C. Índice
- F=[1,0], uma sentença contra duas, pesos iguais:
  M(A→B)=1;
  M(B→A)=1/2;
  I=75;
- simetria do índice;
- componentes direcionais distintos;
- pesos e entradas degeneradas;
- igualdade textual com L=0 e C_op=1:
  F=0,6, sem forçar 100.

D. Alinhamento
- F=[[0,90;0,80],[0,85;0]]:
  ótimo cruzado com soma 1,65;
  índice por máximos e pesos iguais: 86,25;
- conferir o ótimo por enumeração independente;
- matrizes retangulares, empates, zeros e sentenças não pareadas;
- repetição que reutiliza a mesma fonte na classificação, mas não no húngaro.

E. Classificação V2
- igualdade após limpeza;
- diferença entre igualdade textual e identidade dos arquivos;
- D exatamente 0,80 e valores imediatamente abaixo;
- C_op exatamente 0,75 e acima;
- S exatamente 0,30;
- prioridade de edição sobre paráfrase;
- edição com escores lexical/semântico baixos;
- TF-IDF alto isolado;
- flags e motivos dos casos negativos;
- indisponibilidade separada das classes;
- distribuição, predominância e empate;
- ausência de inferência fictícia de “trecho inserido”.

F. Janelas e modelo
- cobertura de tokens incluindo conteúdo significativo no final;
- tokens especiais dentro do limite;
- ausência de truncamento oculto;
- pooling com vetores conhecidos e oráculo independente;
- caso de uma janela;
- média nula;
- integração real com revisão fixa e cache;
- dimensões e valores finitos;
- execução sem acesso remoto após preparar o cache.

Não fixe escores inventados para frases reais. Não exija que qualquer paráfrase tenha nota maior que qualquer frase aleatória. Exemplos linguísticos ilustrativos não validam o modelo.

G. Contrato e integração
- fixtures compartilhadas core↔web;
- campos ausentes, tipos errados e versões incompatíveis;
- demonstração de rejeição em ambos os lados;
- fluxo real de dois arquivos → parsing → API → resultado → persistência → leitura;
- modo lexical separado quando semântico indisponível;
- ausência de gabarito nas features;
- seeds idempotentes.

Preserve todos os testes relevantes da S1, especialmente Type1 e seus controles negativos.

14. DOCKER E EXECUÇÃO REAL

Adapte os serviços necessários à API e à integração S2.

- Preserve volumes e dados.
- Preserve COPY scripts e demais recursos exigidos pelos testes.
- Separe preparo do modelo e inicialização da aplicação.
- Não esconder downloads de pesos no atendimento de uma comparação.
- Use cache e configuração explícitos.
- Não imprimir configuração expandida com segredos.

Registre:
- docker compose config --quiet;
- build real;
- imagem e runtime efetivos;
- testes core no container;
- testes web/contrato pertinentes;
- fluxo integrado real;
- saúde dos serviços e operações de persistência exercitadas.

Mongo saudável não prova CRUD ou integração.

Se rede, modelo, Docker ou banco impedirem uma execução obrigatória, registre o impedimento real. Não apresente mock, teste unitário ou log antigo como substituto dessa integração.

15. EVIDÊNCIAS E ATUALIZAÇÃO DOS PROMPTS

Para cada execução relevante, registre:
- comando;
- diretório;
- versão/configuração;
- saída;
- código de retorno;
- arquivos produzidos;
- falhas, skips e limitações.

Preserve tentativas que falharam. Não escolha apenas o melhor resultado.

Atualize conforme efetivamente afetados:
TCC/00, 01, 02, 03, 05, 07, 09, 10, 11 e 14.

Não apresentar validação de H1–H3 nesta etapa. Não preencher TCC/13 com resultados de desenvolvimento.

Após os achados, confira os prompts das próximas sessões:
- incorpore contratos implementados e limitações;
- atualize dependências e testes;
- preserve versões anteriores;
- não reintroduza exigências ou decisões superadas;
- não transforme propostas futuras em aprovações;
- não execute as sessões seguintes.

16. CRITÉRIOS DE ENCERRAMENTO DA S2

A S2 somente pode ser declarada concluída quando:
- contratos deste prompt estiverem registrados;
- E3 usar modelo/revisão/configuração identificados e cache real;
- E4, fusão, índice e classificação V2 estiverem implementados;
- estados degenerados e indisponíveis respeitarem o contrato;
- testes matemáticos e regressões pertinentes passarem;
- contrato core↔web tiver negativos verificados;
- fluxo real com dois arquivos/API/persistência estiver demonstrado;
- seeds necessários forem idempotentes;
- ambiente e Docker pertinentes estiverem validados;
- documentação, evidências e prompts estiverem atualizados.

Não exigir nesta etapa treino, GPU, dataset final, calibração final ou aprovação fictícia do orientador.

“Trecho inserido” continua indisponível por decisão explícita desta etapa e deve aparecer como pendência global. Nenhuma outra entrega obrigatória pode ser omitida silenciosamente.

17. ENTREGA FINAL

Entregue:
- resultado concreto da implementação;
- matriz requisito → arquivo/função → teste/evidência → status;
- comandos e resultados reais;
- versões e identidades de modelo/IDF/política;
- exemplos reais de entrada/saída identificados como desenvolvimento;
- alterações e respectivas justificativas;
- falhas e limitações;
- pendências separadas entre bloqueios S2 e trabalho futuro;
- roteiro manual curto, com arquivos/comandos e comportamento observável;
- situação dos prompts das sessões seguintes.

Diferencie:
1. Executado e verificado.
2. Decisões do projeto.
3. Limitações das fontes e do método.
4. Pendências.

Não solicite que o autor certifique tecnicamente o código. Peça apenas verificações humanas específicas e compreensíveis quando pertinentes.

Finalize com “S2 concluída no escopo verificado” ou “S2 não concluída”, sustentando o veredito com evidências. Pare sem iniciar a Sessão 3.

## Contratos técnicos concretos desta implementação

Flask: POST /v1/extract (multipart file e contract_version=1.0), POST /v1/compare (JSON source.text, suspect.text, mode=hybrid|lexical, contract_version=1.0), GET /v1/health. Next: POST /api/comparisons (multipart source/suspect, version e modo), GET /api/comparisons/[id]. Schemas estritos rejeitam metadados de gabarito; fixtures compartilhadas em contracts/. Limites/política em core/configs/comparison.json; identidade vincula configuração e hashes do código. Cache preparado explicitamente por core/scripts/prepare_model.py; sem download no request/build. Seeds por scripts/seed-development.py, coordenando o web, único dono de coleções necessárias nesta etapa. E2 é diagnóstico separado; OSA é restrita; janelas/agregação/E4/V2 são adaptações do projeto. O IDF mantém versão histórica, com descritor observado complementar sem atestação retroativa.
