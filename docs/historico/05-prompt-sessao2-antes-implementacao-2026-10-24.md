# Prompt completo da Sessão 2 — preparado em 2026-10-24

**S2 depende das respostas listadas: resta Q5-V2, classificação.** Q1–Q4 e Q6 foram respondidas e estão consolidadas em TCC/evidencias/codex-encerramento-documental-s1-preparo-s2-2026-10-24/decisoes-s2.md. A primeira proposta de classes foi recusada para revisão; a V2 ainda não foi adotada. Preparação documental não autoriza execução. Mesmo após respostas, aguardar pedido explícito de implementação da S2; a tarefa que criou este prompt termina na entrega documental.

Copiar o bloco abaixo somente para uma execução futura autorizada. Substituições de contrato por novas respostas precisam de registro em TCC/01/02/14 e atualização deste prompt, sem apagar a versão anterior.

```text
Execute somente a Sessão 2 do hybrid-text-similarity, quando explicitamente autorizada e satisfeitas as condições de entrada abaixo. Não reinicie a Sessão 1 concluída e não avance para frontend da S3, dataset S4 ou treino/experimentos S5.

1. REGRAS, ESTADO E CRITÉRIOS DE ENTRADA

Leia AGENTS.md, CLAUDE.md, docs/01 (seção0 prevalece para escopo; 4.4/4.5/6/6.2/10/11/12), docs/02 como índice auxiliar, docs/03, TCC/00/01/02/03/04/05/10/11/14 e a entrega de encerramento documental da S1. Confira o arquivo decisoes-s2.md dessa entrega e as respostas posteriores reais do autor. Reaproveite evidência íntegra; não trate registro de hipótese/proposta como aprovação.

Condições cumulativas para a parte dependente: autorização de execução S2; S1 concluída com evidências correspondentes ao código; contratos Q1–Q6 respondidos e registrados no alcance necessário; modelo/revisão/limite/licença verificáveis antes de uso. Se faltar resposta, apresente a dúvida específica e não implemente a convenção científica pendente. Trabalho independente só dentro do pedido autorizado. Não exigir antes de S2 treino, dataset final, GPU, calibração final, metas H3 ou aprovação fictícia do orientador.

Antes de editar, confirme raiz, git status, staged/unstaged/novos e hashes pertinentes. Crie uma pasta nova de evidências com comandos/diretórios/versões/saídas/códigos de retorno. Preserve logs, snapshots e alterações existentes. Não imprima .env/credenciais ou configuração Compose expandida. Não faça commit, push, tag, merge, rebase, reset/clean, PR, publicação ou release por qualquer ferramenta. Não apague volumes nem arquivos anteriores. Privacidade de docs/TCC/regras/raw/modelos/artefatos permanece.

2. BASE S1 A PRESERVAR

A entrega técnica anterior tem execuções Windows e Docker de 177 testes aprovados, sem skips/xfails; são logs históricos vinculados por hash, não resultado novo desta sessão nem meta de contagem. Baseline Python3.11.9/uv0.9.5 e lock não devem ser promovidos silenciosamente. Dependências adicionais só as necessárias à S2, com versões/compatibilidade/lock e justificativa; não instalar pilha S4/S5 ou atualizar tudo. Node LTS/patch e versões web devem ser conferidos nas fontes oficiais no momento de implementar o módulo web; não promover candidato Python por mera preparação documental.

Parsing: pdfplumber, DOCX e TXT existentes. Preservar a correção Type1/WinAnsi173 no gerenciador por PDF, ToUnicode/Differences explícitos, isolamento das tabelas globais/fontes e limpeza de U+00AD. Preservar negativos de espaços/hífens reais, Unicode, erros de protegido/corrompido/vazio/imagem, TXT UTF-8/cp1252 estritos e BOM malformado. Sem OCR ou adivinhação de caracteres.

Preservar segmentação de domínios, URLs, e-mail simples/Markdown, v1.2, decimais, iniciais, abreviações, pontuação/aspas, junções múltiplas e compostos reconhecidos com sua limitação. Manter os perfis lexical e semântico S1; usar os mesmos na comparação e na geração futura.

TF-IDF exato A1 fica nos testes de reprodução; sistema usa IDF suavizado do corpus provisório identificado, sem ajustar IDF aos dois arquivos. Sem reconstruir/migrar corpus/identidade silenciosamente. Manter normas zero e demais contratos S1.

Nomear Damerau–Levenshtein restrita / Optimal String Alignment, custos/normalização/vazios explícitos. Não trocar pela irrestrita. E2 continua adaptação top-k/TF-IDF/conjunto/BLAKE2b64/soma modular, com parâmetros provisórios e identidade de pipeline/IDF. Hash igual não comprova identidade textual/semântica nem autoriza pular motores; inteiro não é feature contínua de similaridade. A3 mantém duas direções explícitas/tamanho externo/erros e adaptação por contagem separada; não resolver lacunas da fonte inventando entradas. E2 serve de diagnóstico/triagem sem alterar a fusão fixa silenciosamente.

3. CONTRATO CIENTÍFICO QUE JÁ EXISTE

Comparar dois arquivos PT-BR, unidade sentença, expondo relações textuais e índice de similaridade, sem detecção conclusiva de plágio. r/origem/classes de transformação/fonte do gabarito não entram em features, alinhamento ou inferência. IDs de documentos servem à rastreabilidade/persistência, não ao cálculo. Pearson/Spearman são métricas posteriores, não o índice nem a função de comparação.

Produzir matriz lexical L e cosseno semântico bruto C de todos os pares antes da seleção de correspondências. Contrato Q2 respondido: C válido∈[-1,1], preservar bruto e usar C_op=max(0,C) na escala operacional. Zero semântico não vira0,5. Rejeitar não finitos e violações reais do domínio; eventual ajuste mínimo de arredondamento deve ter tolerância explícita/testada. Embedding de norma zero é indisponibilidade explícita, sem similaridade inventada.

Fusão fixa histórica: F_ij=0,6*C_op_ij+0,4*L_ij. Não renormalizar pesos segundo disponibilidade. Corte adaptado S=max(L,C_op) e regras de classe são distintos de F; não usar a nota do documento para classificar cada sentença. Limiares0,30/0,75/0,85 continuam provisórios; escolhas adicionais só conforme resposta Q5, sem atribuí-las ao artigo. Siamês e fusão aprendida permanecem indisponíveis, sem probabilidades fictícias ou substituição do índice.

Índice histórico: w é número de palavras segundo word_count S1. M(A→B)=soma_i(w_i*max_j(F_ij))/soma_i(w_i); calcular também B→A; I=100*(M(A→B)+M(B→A))/2. Preservar valores sem arredondamento no cálculo; arredondar só exibição, com regra registrada. Índice é simétrico, admite reutilização de correspondências e não equivale a100*r. Não alegar associação empírica sem experimento posterior.

Q1 respondida: documentos sem texto/sentenças/peso total útil não recebem nota; erro/indisponibilidade com razão. Texto válido sem representação lexical mantém L=0 sinalizado. Não forçar I=100 por igualdade textual. Igualdade após perfil semântico S1 pode ser saída separada; não confundir igualdade de arquivos, identidade textual e nota fundida. Semântico1/lexical0 permite F=0,6 conforme a fórmula; mostrar a condição degenerada.

Q3 respondida: se faltar modelo semântico ou outro componente obrigatório por falha de recurso, resultado híbrido explicitamente indisponível; lexical pode funcionar em modo separado, rotulado com método/configuração próprios. Ausência não é valor0, não é classe original e não muda pesos escondidamente. Distinguir falha de carregamento do IDF de vetor lexical nulo válido.

Q4 respondida: húngaro é explicação separada, maximiza a soma não ponderada de F, deixando pares zero sem correspondência; pode usar fictícios de ganho0 e mostrar sentenças não pareadas. Classificar cada sentença do suspeito pelo seu melhor par em F, permitindo reutilizar uma sentença da fonte. Índice continua pela matriz completa de máximos, sem usar a soma do húngaro. Caracteres podem ser calculados nesses pares escolhidos à classificação, além dos pares E4 para diagnóstico; não retroagem à seleção. É adaptação do projeto, não reprodução integral do alinhamento de palavras A9.

Q6 respondida: usar sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2. Revisão observada na API oficial e registrada documentalmente: e8f8c211226b894fcb81acc59f3b34ba3efd5f42; fixar essa revisão para modelo/configuração/tokenizador ou registrar motivo de eventual indisponibilidade antes de substituí-la. Ficha declara Apache-2.0 e max_seq_length128, ainda conferir configuração/limite efetivo na revisão ao preparar cache. Nenhum peso/cache/embedding foi preparado nesta finalização documental. Janelas internas completas não sobrepostas, respeitando tokens especiais; normalizar cada embedding de janela, média ponderada por tokens de conteúdo e L2 final. Conferir cobertura de tokens sem perdas por retokenização/truncamento; média nula é indisponibilidade. Sentença continua unidade, sem comparação por parágrafo. Agregação de janelas é escolha do projeto autorizada, sem desempenho validado.

4. ÚNICA DECISÃO AINDA PENDENTE NESTA EDIÇÃO: Q5-V2

O autor já definiu: exata é igualdade após limpeza, sem significar arquivos idênticos; não usar TF-IDF alto sozinho como editada; não chamar todo restante de original; usar sem correspondência detectada quando faltar evidência; manter limiares provisórios; apresentar regra antes de implementar. A classificação anterior foi recusada para revisão, não deve virar código.

Consultar proposta-classes-v2.md da entrega documental: proposta de ordem igualdade→edição por caracteres→corte→semântico→sem correspondência, com edição antes de paráfrase, tau_edição0,80 candidato e sem gatilho automático TF-IDF. A prioridade da edição antes do corte histórico é mudança explicitamente proposta, não aprovada. Exemplos, fronteiras, motivos e limites estão no documento; a nota I/F não muda. Resumo por distribuição/predominância com empate e etiqueta inserido indisponível também aguarda resposta. Não usar r/C0–C7 para preencher inferência nem equiparar sem correspondência a originalidade comprovada.

Não implementar classes/limiar/prioridade/resumo pendentes nem declarar S2 completa omitindo essa parte. Se o autor responder com outra regra, registrar antes/depois e adaptar testes/prompt antes de usá-la. Estados técnicos de indisponibilidade não são classes negativas.

Depois das respostas, registrar antes/depois/motivo e contrato consolidado em TCC/01/02/14 e neste prompt. Não reescrever H1–H3 ou a pergunta de pesquisa como se tivessem sido validadas/aprovadas pelo orientador.

5. IMPLEMENTAÇÃO FUTURA AUTORIZADA APÓS AS ENTRADAS

E3: adaptador local Sentence-Transformers, modelo escolhido/revisão fixa e modo de inferência. Script de preparação do cache separado do build; registrar ID/SHA do modelo/tokenizador/configuração, licença como metadado, hashes, limites efetivos e versões relevantes. Não carregar main flutuante; não copiar pesos ao Git; funcionar do cache após preparo. Ausência/falha tem estado explícito. Domain não importa torch/transformers/Sentence-Transformers/HTTP/banco ou arquivos; receber vetores/valores dos adaptadores e manter cálculos puros.

E4: matriz sentença×sentença, objetivo húngaro e sem par conforme Q4, com desempate determinístico que não altere o ótimo. Retornar índices/valores/estado dos pares e a matriz para explicação. Não criar dependência circular: L/C/F devem existir antes da seleção; escores de caracteres usados só depois nos pares contratados não retroagem à matriz que os escolheu. Diferenciar o alinhamento um a um das melhores correspondências do índice/classes. Não transformar assinatura igual em evidência conclusiva.

Implementar fusão fixa, classes por sentença/resumo documental no alcance de Q5, índice, indisponibilidade e configurações/identidades rastreáveis. Baselines lexical/semântico precisam de método/política de agregação identificados; não misturar mudanças de agregação com ganho de fusão. Nada calculado com seeds de desenvolvimento é resultado de pesquisa.

API Flask interna /v1, schemas Pydantic e módulo comparison do web com Zod/cliente/caso de uso/repositório/testes. Escopo S2 inclui essa integração web, não telas de S3. Core recebe textos e devolve resultados sem persistir a comparação; reutilizar parsing S1 na fronteira apropriada para demonstrar dois arquivos, sem duplicar algoritmos no JavaScript. Especificar requisição/resposta/erros/limites e impedir inputs de gabarito nas features. Decisões de rota/nomes/serialização são rotina dentro desse contrato.

Mongo: web escreve usuários/documentos/comparações/relatórios; core escreve apenas suas coleções de dataset/pares/experimentos/execuções quando de fato usadas, sem antecipar as fases futuras. Não duplicar gravações de comparação nos dois processos. Seeds fixos de desenvolvimento: um comando coordenador chama cada dono; idempotência sem apagar dados existentes. Secrets só ambiente, nunca logs/schemas/documentação com valores reais. Comparação síncrona, sem fila; progresso indeterminado.

Docker: adaptar comandos/serviços pertinentes a API/integração quando autorizados, preservando volumes, corpus e cache. Manter cópia de scripts exigida pelos testes. Registrar config --quiet, build, runtime e execução reais separadamente. Mongo saudável não prova CRUD; testar operações de persistência S2 com namespace de desenvolvimento isolado e sem afetar dados existentes.

6. TESTES E ORÁCULOS

Preservar suite/regressões S1. Número de testes não é critério artificial; executar funções reais, sem mock do próprio cálculo, assert trivial ou esperado calculado pela implementação testada. Usar Fraction/Decimal ou conta manual documentada como oráculo complementar; guardar entradas/procedência/fórmula/tolerância. Doubles são permitidos nas fronteiras para testar HTTP/erros/indisponibilidade, identificados; não substituem teste de integração com modelo/banco reais.

Exemplos independentes planejados para futuros testes, não resultados executados desta preparação:
- Vetores [1,0], [0,1], [-1,0]: cossenos1/0/-1; com Q2 C_op1/0/0. Vetor nulo tem estado explícito, sem falso valor matemático.
- L=1/2 e C_op=3/4: F=13/20. Conferir com Fraction antes de fixar constante. Indisponível não se converte em0 nem altera pesos.
- F=[1,0] de uma sentença contra duas, pesos iguais: M(A→B)=1, M(B→A)=1/2, I=75; r do exemplo sintético pode ser1/2, sem equivalência I=100r. Norma/peso zero e identidade com L0/C1 têm políticas Q1.
- Se Q4 aprovar a proposta, F=[[0,90;0,80],[0,85;0]] distingue escolha gulosa/alinhamento ótimo de máximos direcionais: cruzado soma1,65; índice por máximos e pesos iguais86,25. Demonstrar por enumeração independente das duas combinações, não pelo próprio solver testado. Cobrir matriz retangular, empate, zeros, vazios rejeitados e repetição com vários melhores pares para uma fonte.
- Q5: testar precedência, igualdade, fronteiras exatas dos limiares de fato aprovados, TF-IDF alto isolado, competição entre edição/paráfrase, falta de evidência, distribuição/empate/inserido no alcance decidido; não atribuir classe por r/metadados ou inventar originalidade. Exemplos de V2 são propostas de oráculo, só se tornam testes do contrato após a resposta; esperado não vem da saída do classificador.
- Q6: entrada que exceda limite com conteúdo significativo no final; verificar cobertura integral de tokens/janelas ou erro de rejeição conforme contrato, sem truncamento invisível. Tokens especiais e sentença com uma única janela não devem alterar unidade/offsets. Pooling em vetores conhecidos deve ter oráculo independente.

Testar modelo real fixado/cache e valores/dimensões finitos sem exigir escore inventado para frases PT ou nota de pesquisa. Igualdade matemática de vetor não nulo e propriedades do cosseno podem ser verificadas; não exigir que qualquer paráfrase supere qualquer par aleatório ou que perda caia. Não treinar nesta etapa.

Teste de contrato core↔web: fixtures compartilhadas de requisição/resposta, casos inválidos/incompatíveis; provar que remoção/tipo errado de campo obrigatório é rejeitado por ambos. Não “testar” schemas apenas contra sua própria construção. Integração real deve chamar Flask, processar um par de arquivos de desenvolvimento e persistir pelo dono, com leitura de retorno. Não usar mock do endpoint como prova desse fluxo real.

Ao final, executar suíte core, testes web/contrato/integração criados, checks configurados e Docker pertinente. Registrar comandos/diretórios/runtime/saídas/exits, falhas/skips/xfails e limitações. Rede/modelo/Docker indisponíveis são impedimentos reais; não afirmar testes de integração não executados. Não correr teste final da pesquisa ou gerar métricas de TCC/13.

7. ENCERRAMENTO E ENTREGA

Atualizar TCC/00/01/02/03/05/07/09/10/11/14 conforme efetivamente afetados. Preservar código/evidências S1, histórico de decisões e versões anteriores de prompts. Conferir diff, Git ls-files/check-ignore e ausência de segredos nos artefatos; não versionar/publicar.

Critérios S2: contratos científicos dependentes respondidos; modelo/revisão/configuração identificados e cache real preparado; E3/E4/fusão/índice/classes implementados no alcance aprovado; casos degenerados/indisponíveis explicados; suíte e oráculos pertinentes passam; contrato web↔core inclui negativos; fluxo real com dois arquivos/API/persistência demonstrado; seeds idempotentes por dono; Docker e ambiente pertinentes validados, ou impedimento obrigatório explicitamente aberto. Uma pendência obrigatória impede declarar encerramento; calibração/dataset/treino futuros não são exigidos artificialmente aqui.

Entregar matriz requisito→implementação→teste/evidência→status, configurações/versões, exemplos de entrada/saída reais identificados como desenvolvimento, comandos/saídas, arquivos alterados, falhas/limitações e roteiro manual específico sem preencher aceite humano. Separar executado/verificado, decisões do projeto e pendente. Declarar se S2 foi ou não concluída com justificativa delimitada. Parar sem iniciar S3 automaticamente. Não prometer detecção conclusiva de plágio ou validação de hipótese pela passagem dos testes.
```
