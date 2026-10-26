# Sessão 4 — prompt completo e estado de continuidade

Atualização de 2026-10-24. Executar somente S4; preservar as sessões anteriores. Pedido integral abaixo, acrescido das respostas explícitas do autor.

## Respostas posteriores que prevalecem

Complemento integral recebido posteriormente: `TCC/evidencias/codex-s4/complemento-pedido.txt`. Confirma ausência de qualquer cobrança adicional, uso exclusivo da sessão Codex para candidatos, revisão piloto8 e C6 apenas piloto. **Gemini/google-genai deixa de ser requisito obrigatório.** Não reaproveitar credenciais de assinatura como API nem contornar limites. Saídas efetivamente produzidas no Codex são dados sintéticos do procedimento real, diferentes dos mocks de testes; conservar cache e metadados indisponíveis identificados. Suporte API opcional/histórico não autoriza chamada nesta etapa.

- Escala de 60 fontes/3 temas provisória; informar grupos independentes e contagens, sem alegar suficiência estatística. Temas variados escolhidos pelo projeto: biologia, geografia e artes/cultura.
- Proporções C2/C3 propostas autorizadas para desenvolvimento; 30% é condição intensa, sem preservação de sentido presumida. Desenho experimental completo continua pendente.
- Nenhuma API paga autorizada. Adaptar geração a candidatos produzidos na sessão Codex, preservando insumos/prompts/respostas e identificação disponível; não chamar isso de Gemini/API. Revisão exata do modelo, uso de tokens e custo não expostos ficam null. Reprodução usa cache, sem nova geração automática.
- Revisão piloto de 8 itens aprovada; amostra experimental depende do esforço real observado pelo autor. Nenhuma resposta humana preenchida.
- C6 piloto: reescrita guiada por frase/palavras-chave com origem preservada; classe semântica final pendente. Não converter C6 automaticamente em paráfrase.
- Alvo contínuo do siamês permanece pendente; não converter r documental, classe ou taxa de edição em nota semântica.

## Estado e retomada

Consultar TCC/00/06/14 e evidencias/codex-s4. Não refazer auditorias íntegras; preservar todas as tentativas. O pipeline atual gera artefatos de desenvolvimento separados das fontes candidatas. Dataset final não é liberado por suíte aprovada. Modelos/motores não podem selecionar exemplos do teste.

## Pedido integral recebido (histórico; aplicar respostas posteriores acima)

SESSÃO 4 — DATASET SINTÉTICO RASTREÁVEL, VALIDAÇÃO E PREPARAÇÃO EXPERIMENTAL

Execute somente a Sessão 4 do projeto hybrid-text-similarity, no alcance autorizado abaixo.

Objetivo: construir o pipeline e os artefatos de um dataset sintético PT-BR adequado à pesquisa, com fontes rastreáveis, divisão por fonte antes da geração, transformações controladas, proveniência por sentença, validação independente, revisão humana e versionamento reproduzível.

Não avance para treinamento, calibração de modelos/limiares ou avaliação científica da Sessão 5.

O sistema está sendo desenvolvido para um TCC. Dados sintéticos são permitidos quando explicitamente identificados como tal. É proibido apresentar dados gerados como observações reais, fabricar revisão humana ou inventar resultados.

1. CONTEXTO E AUTORIZAÇÃO

Tema:
“Desenvolvimento de sistema de comparação de conteúdo de textos.”

Objetivo:
“Buscar as inter-relações entre dois arquivos, buscando o índice de correlação.”

S1: fundamentos, parsing e cálculos.
S2: comparação híbrida, alinhamento, índice e classificação V2.
S3: autenticação, interface, histórico, impressão e verificações de engenharia.

O CI da S3 foi consultado e terminou com success:
https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40138911874

Commit validado:
9c8e914434a2712f850501dc97164246ac2b1928

A aprovação é evidência técnica daquele estado. Não comprova acurácia, qualidade do dataset, validação de H1–H3 ou ausência universal de defeitos.

Esta instrução autoriza:
- implementar coleta, preparação, geração e validação;
- executar testes e um piloto determinístico;
- preparar revisão humana;
- gerar o dataset completo quando as decisões necessárias e os recursos estiverem definidos;
- construir IDF experimental exclusivamente com fontes de treino;
- congelar apenas artefatos que cumpram seus critérios explícitos.

A autorização não determina números ainda não definidos, não aprova custos ilimitados de API nem permite preencher respostas humanas.

2. REGRAS PERMANENTES

- Não executar commit, push, tag, merge, rebase, reset/clean, abertura de PR, publicação ou deploy.
- Não apagar volumes, dados, corpus, modelos, versões anteriores ou evidências.
- Não expor .env, chaves de API, cookies, senhas ou credenciais.
- Não publicar documentos, dataset, cache, pesos ou arquivos privados.
- Não executar treinamento, calibração ou comparação científica dos motores.
- Não consultar resultados do teste final para selecionar dados ou métodos.
- Não inventar fontes, licenças, textos originais atribuídos a terceiros, métricas ou aprovações.
- Não ajustar esperados ou filtros para favorecer os motores.
- Não fabricar aceites de revisão humana.
- Não transformar validação estrutural em confirmação de preservação semântica.
- Não atribuir escolhas do projeto aos artigos.
- Preservar todas as tentativas relevantes, inclusive falhas e rejeições.

Resolva escolhas rotineiras dentro do contrato. Questões que alterem o construto, o gabarito, o custo ou o desenho experimental exigem decisão explícita antes da etapa dependente.

3. LEITURA E RETOMADA

Leia:
- AGENTS.md e CLAUDE.md;
- docs/01-guia-base-teorica-e-arquitetura.md, especialmente 5.3, 5.4 e escopo vigente;
- docs/02-mapa-formulas-e-arquiteturas.md;
- docs/03-prompts-por-etapa.md;
- prompts completos atuais das sessões anteriores;
- TCC/00-indice.md;
- TCC/01-decisoes.md;
- TCC/02-metodologia.md;
- TCC/03-formulas-e-calculos.md;
- TCC/04-parsing.md;
- TCC/05-core.md;
- TCC/06-dataset-sintetico.md;
- TCC/11-testes.md;
- TCC/12-experimentos.md;
- TCC/14-pendencias.md;
- entregas codex-s3 e registros de CI.

Procure decisões posteriores que substituam propostas históricas.

Atenção a registros antigos:
- r documental não é automaticamente alvo semântico do siamês;
- κ de Cohen não se aplica com um único revisor;
- “original” sintético e “sem correspondência detectada” não têm significado equivalente;
- corpus provisório de desenvolvimento não é IDF experimental de treino;
- fontes abertas usadas como matéria-prima não transformam o dataset em benchmark real anotado.

Registre a raiz, branch, SHA, alterações locais, versões e hashes relevantes. Preserve o trabalho existente.

Crie pasta nova em TCC/evidencias/ para esta sessão. Não reutilize nomes que sobrescrevam execuções anteriores.

4. DEFINA O CONTRATO DO DATASET ANTES DA GERAÇÃO COMPLETA

Consolide em configuração e documento:
- finalidade e unidades;
- fontes e grupos;
- critérios de inclusão/exclusão;
- taxonomia C0–C7;
- transformações e severidades;
- política de negativos;
- proporção e método de divisão;
- quantidade por fonte/classe;
- seeds;
- formatos;
- política de revisão humana;
- política de rejeição/regeneração;
- requisitos de congelamento;
- limites de chamadas/custos de LLM.

Reaproveite decisões já autorizadas. Para o que faltar, apresente uma proposta concreta, justificativa e consequências, sem alegar aprovação.

O histórico prevê 70/15/15 por fonte/grupo. Confira seu status atual; não altere essa proporção silenciosamente. Informe contagens inteiras, arredondamento e suficiência de grupos por split.

Não use quantidades dos artigos como justificativa automática de suficiência estatística.

Tamanho do dataset e tamanho da revisão:
- separar número de fontes independentes, documentos derivados, pares e sentenças;
- não tratar milhares de pares da mesma fonte como milhares de observações independentes;
- propor escala compatível com recursos e tempo;
- não prometer poder estatístico sem cálculo apropriado;
- obter a decisão necessária antes da geração completa.

Enquanto essas escolhas estiverem pendentes, implemente e teste o pipeline e execute apenas piloto identificado como desenvolvimento, fora do dataset final.

Não bloqueie a engenharia por questões exclusivas do treino futuro. Entretanto, não gere gabarito dependente de uma definição ainda inexistente.

5. FONTES ABERTAS E COLETA

Priorize o caminho já planejado: lista fixa de páginas da Wikipédia em português, com revisões específicas.

Outras fontes abertas somente se previstas e com licença verificável. Não incorporar STS, ASSIN, PAN ou outro benchmark real aos experimentos sem mudança explícita do escopo.

Use mecanismos oficiais de acesso e registre falhas, limites e respostas reais. Não invente páginas quando houver erro de rede.

Manifesto de cada fonte:
- source_id estável;
- título;
- URL;
- provedor;
- identificador de página e revisão, quando disponíveis;
- data real de coleta em UTC;
- licença e referência verificável;
- hash dos bytes coletados;
- hash do texto extraído/normalizado;
- procedimento de extração;
- idioma esperado;
- categoria temática e sua procedência;
- decisão de inclusão/exclusão e motivo.

Não presumir licença de toda uma plataforma sem conferir a fonte pertinente.

Preserve:
- bytes de origem;
- representação textual extraída;
- texto normalizado;
- relação entre essas camadas.

A camada raw é imutável. Uma nova coleta/revisão gera novo artefato, não substituição silenciosa.

Não apresentar artigo real da Wikipédia como texto originalmente produzido pelo projeto. Identifique as transformações sintéticas e preserve atribuição.

Não republicar ou depositar os dados nesta sessão.

6. SEPARAÇÃO ENTRE DESENVOLVIMENTO E EXPERIMENTO

Inventarie fontes e exemplos já usados:
- corpus provisório do IDF;
- fixtures S1–S3;
- exemplos visuais;
- documentos utilizados para ajustar parsing/regras;
- pilotos de geração.

Registre essa exposição.

Evite usar como teste final fontes ou derivados já usados repetidamente para desenvolvimento. Se houver sobreposição histórica inevitável, proponha tratamento e declare o alcance; não apresente o conjunto como completamente intocado.

O pré-treinamento dos modelos pode ter incluído conteúdo da Wikipédia. A revisão congelada não demonstra ausência de exposição prévia do modelo. Registre essa limitação.

Mantenha diretórios, identidades e manifestos distintos para:
- fixtures de software;
- piloto;
- dataset candidato;
- dataset revisado;
- versão congelada.

Não misture seeds de desenvolvimento com exemplos experimentais por conveniência.

7. NORMALIZAÇÃO E SEGMENTAÇÃO

Reutilize as funções efetivas do core:
- limpeza;
- segmentação em sentenças;
- contagem de palavras;
- perfil lexical;
- perfil semântico.

Não crie uma versão semelhante, mas diferente, no gerador.

Registre versões/hashes do pipeline e modelo spaCy.

Preserve identificadores e correspondências:
- fonte original;
- segmento selecionado;
- sentença;
- posição;
- transformação;
- texto resultante.

Seleção de trechos deve ter critério explícito e comprimento controlado. Não escolher manualmente só trechos nos quais os motores funcionem bem.

Cabeçalhos, referências, tabelas e ruído devem ter política documentada. Não chamar texto descartado de inexistente.

8. GRUPOS E SPLIT ANTES DOS PARES

Identifique duplicatas e famílias de fontes antes da divisão.

Considere:
- revisões da mesma página;
- trechos compartilhados;
- documentos derivados;
- fontes quase duplicadas;
- múltiplas representações do mesmo conteúdo.

Defina o detector e seus parâmetros antes de examinar desempenho dos motores. Um alerta de proximidade exige inspeção/classificação, não exclusão oportunista.

Divida por grupos independentes antes de:
- gerar transformações;
- montar negativos;
- produzir patchwork;
- gerar variações de formato;
- construir pares.

Regras:
- toda revisão/derivação da mesma família fica no mesmo split;
- todas as fontes de um patchwork ficam no mesmo split;
- os dois lados de negativos ficam no mesmo split;
- variantes PDF/DOCX/TXT ficam no mesmo split;
- sentenças de uma mesma fonte não podem atravessar splits;
- pares não são divididos aleatoriamente depois da geração.

Para fontes com vínculos, use agrupamento que preserve esses vínculos, como componentes conexos, conforme a necessidade real.

Se grupos grandes impedirem a proporção desejada, registre o desvio e sua causa. Não quebre o grupo para obter uma tabela visualmente equilibrada.

Verifique cobertura de temas e classes por split. Estratificação não pode violar isolamento de fontes.

9. TAXONOMIA C0–C7

Confira as definições históricas e preserve sua procedência:

C0 — negativo por construção:
- fontes distintas;
- negativos fáceis de temas diferentes;
- negativos difíceis do mesmo tema, com conteúdo distinto.

Não chamar C0 de originalidade ou ausência comprovada de relação semântica.

C1 — cópia exata:
- conteúdo derivado sem edição;
- igualdade definida na representação contratada;
- registrar diferenças apenas de formato.

C2 — edição controlada:
- operações explícitas de edição;
- sementes, posições, contagens e severidade;
- registrar taxa solicitada e efetivamente realizada.

Semelhança de caracteres não garante preservação de sentido.

C3 — inserção de trecho:
- combinar material derivado da fonte com material de outras fontes do mesmo split;
- registrar composição e proporções reais;
- proporções são escolhas do projeto, não taxas de reuso publicadas pelo A3.

A geração de C3 não autoriza implementar a inferência de “trecho inserido” na aplicação.

C4 — patchwork:
- mistura controlada de 2 a 4 fontes, conforme definição histórica;
- todas no mesmo split;
- proveniência múltipla;
- r específico para cada fonte comparada.

C5 — paráfrase:
- distinguir paráfrase direta por LLM e retrotradução PT→EN→PT;
- registrar cada método separadamente;
- preservar saídas intermediárias;
- revisão semântica necessária, sem aceitação automática pelo nome da transformação.

C6 — palavras-chave e frases:
- reconhecer que a definição histórica é insuficiente se não delimitar a transformação;
- especificar operações e o que constitui evidência de derivação;
- não chamar mera coincidência de palavras-chave de paráfrase válida;
- resolver ambiguidades antes da geração completa dessa classe.

C7 — reordenação:
- preservar unidades e proveniência;
- registrar permutação;
- não exigir que todos os motores penalizem a mudança de ordem;
- permutação pode alterar coerência discursiva e deve ter sua interpretação delimitada.

Transformação de documento não é automaticamente classe de todas as suas sentenças.

Não atribua a cada artigo parâmetros que ele não informa.

10. PROVENIÊNCIA E GABARITO

Para cada documento suspeito, registre por sentença:
- ID estável;
- posição;
- texto;
- source_ids envolvidos;
- IDs das sentenças de origem;
- transformação e parâmetros;
- relação com a fonte focal;
- estado de validação;
- revisão humana, quando realizada.

Admita relações um-para-muitos e muitos-para-um quando existirem. Não forçar um único ancestral para uma frase realmente multiorigem.

Defina antes da geração:
- como tratar fusão e divisão de sentenças;
- sentenças com conteúdo misto;
- fragmentos sem sentença recuperável;
- frases comuns/duplicadas entre fontes;
- denominação de “derivada” no gabarito.

Se uma transformação não permitir gabarito confiável no contrato escolhido, restrinja-a de forma explícita ou mantenha o caso como ambíguo. Não invente alinhamento.

r por par documental:
r(B|A) =
número de sentenças de B marcadas como derivadas de A
/
número total de sentenças de B

Use o denominador real após o processamento contratado. Não substitua a proporção realizada pela proporção solicitada.

No patchwork:
- cada fonte tem seu próprio r;
- não atribuir à fonte focal derivação proveniente apenas de outra fonte;
- se houver sobreposição de proveniência, não presumir que a soma dos r deva ser 1.

Para negativos:
- r de derivação pode ser 0 por construção;
- isso não implica similaridade semântica igual a 0.

Preserve contagens inteiras/racionais e regra de exibição. Documente arredondamento de tamanhos que produza proporções aproximadas.

11. NÃO CONFUNDIR DERIVAÇÃO, SEMÂNTICA E PREDIÇÃO

Separe:
- tipo sintético C0–C7;
- operação de geração;
- derivação conhecida;
- classe pretendida;
- classe validada;
- similaridade semântica;
- predição futura do sistema.

O gerador conhece operações e origem. Ele não conhece automaticamente a qualidade semântica da saída.

Não utilizar:
- classe predita pela V2;
- escore do MiniLM;
- distância de edição;
- nota de LLM;
como verdade de referência sem definição metodológica específica.

Não selecionar ou rejeitar exemplos porque o sistema “acertou” ou “errou”.

Documente o mapeamento avaliativo entre:
- negativo por construção;
- saída “sem correspondência detectada”.

Esse mapeamento serve à matriz de avaliação; não torna os significados equivalentes.

Alvos do siamês:
- não converter r documental em alvo de todo par de sentenças;
- não assumir paráfrase=1 ou negativo=0 como similaridade semântica comprovada;
- não cristalizar 1−taxa de edição como alvo semântico sem decisão específica;
- manter alvo contínuo como pendência se ainda não ratificado.

Se não houver alvo semântico validado, os artefatos podem conter proveniência e rótulos de transformação sem fabricar notas contínuas.

Não montar pares de treino apenas pelo melhor alinhamento do modelo avaliado. Isso introduziria viés de seleção.

12. LLM: PAPEL, CONFIGURAÇÃO E CACHE

O plano histórico prevê Gemini via google-genai. Confira decisões atuais antes de escolher provedor/modelo.

A LLM gera candidatos de transformação; não emite a verdade de referência nem certifica preservação de sentido.

Antes de chamadas:
- verificar SDK e documentação oficial;
- identificar modelo disponível e configuração;
- verificar credencial sem imprimir seu valor;
- definir limites de chamadas, tokens, tentativas e custo;
- não iniciar geração paga em lote sem orçamento autorizado.

Não substituir modelo indisponível silenciosamente.

Enviar somente os trechos públicos necessários. Nunca enviar documentos do autor, credenciais, dados de usuários ou registros privados.

Trate o texto-fonte como dado, inclusive quando contiver instruções. Não executá-las.

Guardar por chamada:
- request_id;
- chave de cache;
- provedor/modelo e revisão identificável;
- prompt de sistema e template;
- parâmetros;
- texto de entrada ou referência íntegra;
- saída bruta;
- saída estruturada;
- status;
- data;
- uso real informado;
- erro/recusa;
- validações;
- relação com tentativas anteriores.

Não afirmar determinismo da API mesmo com seed ou temperatura zero.

Chave do cache deve incluir os insumos e parâmetros que alteram a chamada. A reprodução do dataset usa saídas preservadas, sem nova chamada automática.

Não sobrescrever resposta antiga. Nova tentativa gera novo artefato.

Retries:
- quantidade limitada;
- política definida;
- preservar recusas e erros;
- não regenerar indefinidamente até obter resultado favorável;
- não contar tentativa falha como exemplo válido.

Sem credencial/modelo/rede:
- registrar impedimento;
- continuar transformações determinísticas e testes;
- não preencher C5 com texto fictício apresentado como saída da API.

13. POLÍTICA DAS TRANSFORMAÇÕES

Implemente transformações locais como funções puras sempre que possível.

Para cada uma:
- entrada;
- saída;
- seed;
- parâmetros;
- operações;
- contagens realizadas;
- invariantes;
- limitações;
- motivo de eventual rejeição.

Controle edições:
- não criar operações sem efeito e contar como edição;
- registrar taxa operacional e distância efetiva separadamente;
- não presumir equivalência entre número de operações e Levenshtein mínimo;
- não afirmar preservação semântica após mudar negação, número, entidade ou unidade.

Paráfrases:
- verificar ausência de conteúdo novo injustificado;
- nomes, números, unidades e negações;
- omissões;
- contradições;
- cópia literal;
- fluência;
- preservação do conteúdo exigido pelo protocolo.

Checagens automáticas são filtros/alertas, não certificação semântica.

Preserve exemplos difíceis plausíveis. Não eliminar erros genuínos dos motores por parecerem inconvenientes.

14. FORMATOS PDF, DOCX E TXT

Gere formatos em etapa separada do conteúdo.

Cada variante referencia o mesmo ID de conteúdo/família/split.

Use:
- fontes Unicode apropriadas no PDF;
- DOCX válido e simples;
- TXT com codificação declarada;
- metadados estáveis quando fizer parte da reprodutibilidade.

Separe:
- conteúdo canônico;
- arquivo renderizado;
- texto reextraído;
- comparação de ida e volta.

Não modificar o conteúdo esperado usando a saída do parser.

Se o round-trip divergir:
- preservar os dois textos e arquivos;
- identificar o estágio;
- distinguir falha do gerador e do parser;
- não corrigir silenciosamente o gabarito.

Datas, IDs de PDF e timestamps de ZIP podem impedir igualdade binária. Controle-os quando necessário ou estabeleça identidade de conteúdo separada da identidade do contêiner, explicitamente.

Não contar PDF/DOCX/TXT do mesmo conteúdo como três observações independentes.

Não criar cabeçalhos, nomes de arquivo ou metadados que revelem a classe ao modelo. Metadados de rastreabilidade ficam fora do texto de inferência.

15. IDF EXPERIMENTAL SOMENTE DO TREINO

Preserve o corpus e IDF provisórios históricos.

Construa um novo artefato experimental:
- somente com fontes permitidas do split de treino;
- sem validação/teste;
- com o pipeline lexical do core;
- com fórmula, N, df e política de termos novos explícitos.

Registre no ato da construção:
- dataset/split de origem;
- fontes/revisões/hashes;
- configuração;
- código;
- stopwords efetivas;
- spaCy/modelo;
- versões;
- tabela produzida;
- hash da tabela;
- descritor e identidade.

Diferencie identidade de conteúdo/entradas, ambiente e bytes serializados.

Não atestar retroativamente a construção histórica do IDF provisório.

Não ativar o IDF experimental na aplicação de demonstração nem regravar comparações existentes silenciosamente. Exponha configuração separada para experimentos futuros.

Teste que alterações apenas nas fontes de validação/teste não modificam o IDF de treino.

16. VALIDAÇÃO AUTOMÁTICA E VAZAMENTO

Implemente comando independente de validação que falhe diante de requisitos violados.

Verifique:
- schemas;
- IDs e referências;
- splits;
- grupos;
- proveniência;
- denominadores;
- r calculado independentemente;
- classes e transformações;
- distribuição por split/tema/severidade/formato;
- hashes;
- cache;
- determinismo;
- round-trip;
- duplicatas e quase duplicatas;
- ausência de gabarito no input de inferência.

Negativos de teste devem provar detecção de:
- mesma fonte em treino/teste;
- patchwork com fonte externa ao split;
- variantes de formato separadas;
- r incorreto;
- IDs órfãos;
- cache de outro prompt/modelo;
- tentativa de sobrescrever artefato;
- dados de teste no IDF.

Conteúdo compartilhado:
- distinguir boilerplate/frase comum de vazamento de fonte;
- parâmetros e critérios documentados;
- não prometer ausência de toda sobreposição semântica;
- não deduplicar apenas pelo texto normalizado ignorando famílias.

Se detectar vazamento após geração:
- não mover um exemplo isolado entre splits;
- corrigir agrupamento e regenerar os derivados afetados;
- preservar a versão anterior e a causa.

Não rodar os motores de comparação sobre o teste final para validar qualidade do dataset. Controles de integridade, inspeção humana do gabarito e geração não são avaliação preditiva.

17. REVISÃO HUMANA

Prepare pacote local simples para revisão, com JSONL/CSV e visualização ou instruções acessíveis.

Se gerar XLSX, use a ferramenta/workflow apropriado e verifique o arquivo.

Cada item deve mostrar:
- ID;
- split;
- texto-fonte;
- texto transformado;
- método;
- operações;
- critério de revisão;
- campos de resposta vazios.

Não mostrar escores/predições do sistema como sugestão de gabarito.

Amostra:
- seleção reproduzível;
- política definida antes da revisão;
- estratificação por classe/método/severidade;
- atenção a C5, C6, negativos difíceis e alterações de sentido;
- separar amostra aleatória de inspeções dirigidas por alertas.

Campos:
- aceita;
- rejeita;
- ambígua;
- motivo;
- observação;
- responsável;
- data.

Não preencher as respostas pelo autor. Revisão do agente pode ser registrada separadamente, sem substituir revisão humana.

Explique ao autor como observar:
- conteúdo preservado;
- fatos novos;
- negações;
- números/unidades;
- entidades;
- omissões;
- incoerência;
- sobreposição indevida em negativos.

Um revisor:
- registrar revisão individual;
- não calcular κ de Cohen nem concordância fictícia.

Dois revisores reais:
- somente se houver avaliações independentes suficientes;
- explicitar amostra/unidade e método antes de calcular concordância;
- não presumir existência de segundo revisor.

Rejeições:
- preservar exemplos;
- política prévia de exclusão/regeneração;
- limite de tentativas;
- registrar alteração de versão;
- não regenerar para agradar o modelo.

A revisão de uma amostra não valida cada item individual. Declare o alcance.

Se a revisão humana ainda não ocorreu, entregar “dataset candidato — revisão humana pendente”. Não declarar dataset final aprovado.

18. REPRODUTIBILIDADE E VERSIONAMENTO

Organize as etapas de CLI, adaptando nomes à arquitetura existente:
- coletar;
- normalizar;
- agrupar;
- dividir;
- gerar;
- gerar-formatos;
- validar;
- preparar-revisao;
- importar-revisao;
- construir-idf-treino;
- congelar;
- exportar/importar versão.

Não exigir esses nomes literais nem duplicar comando existente.

Um comando coordenador pode executar as etapas, respeitando dependências e impedimentos.

Reprodução:
- entradas e raw congelados;
- configuração/seed fixos;
- cache LLM preservado;
- serialização canônica;
- ordenação estável;
- precisão definida;
- execução sem rede após preparo.

Mesma seed, isoladamente, não garante o mesmo dataset.

Identidade:
- manifesto de conteúdo imutável;
- hashes dos arquivos relevantes;
- configurações e saídas do cache;
- versão do gerador/pipeline;
- exclusão explícita de campos voláteis da identidade de conteúdo, quando justificada;
- datas e histórico preservados em metadados de execução.

Evite hash circular e log ainda aberto dentro do manifesto que ele sela.

Compare reprodução em diretórios novos e processos com PYTHONHASHSEED distintos. Não sobrescrever artefatos para esconder divergência.

19. CONGELAMENTO, DATASHEET E EXPORTAÇÃO

Separe:
- especificação aprovada;
- candidato gerado;
- candidato validado automaticamente;
- revisão humana realizada;
- versão congelada apta ao uso pretendido.

Congele somente com requisitos satisfeitos:
- fontes/licenças;
- split/grupos;
- gabarito/proveniência;
- validações;
- revisão prevista;
- cache íntegro;
- configuração;
- identidade;
- limitações documentadas.

Se o alvo contínuo do siamês estiver pendente, não inventá-lo:
- pode existir versão congelada para derivação/classificação, se esse alcance estiver autorizado e completo;
- ela não fica automaticamente apta ao treino/avaliação semântica de H2.

Datasheet deve descrever:
- motivação;
- composição e contagens reais;
- fontes/licenças;
- geração;
- splits/grupos;
- rótulos e limitações;
- revisão;
- exclusões/rejeições;
- uso previsto e inadequado;
- proveniência;
- modelo gerador;
- exposição prévia;
- riscos de viés;
- reprodutibilidade;
- manutenção/versionamento.

Exporte JSONL e manifestos para uso local. Eventual depósito futuro é apenas preparado, sem upload/publicação.

Persistência:
- core é dono das coleções de dataset;
- importação por versão;
- idempotência;
- conflito explícito se mesmo ID tiver conteúdo diferente;
- sem apagar versões anteriores;
- sem misturar dados com comparações dos usuários.

20. PROTEÇÃO DO TESTE FINAL

Treino, validação e teste devem ter acesso e finalidade separados.

Nesta sessão:
- permitido gerar, validar estrutura/proveniência e revisar gabarito;
- proibido comparar desempenho dos sistemas no teste;
- proibido selecionar exemplos por predições do teste;
- proibido calibrar com teste.

Implemente um guard explícito nos futuros caminhos de avaliação, quando pertinente. Não tratar nome de pasta como barreira suficiente.

Registre exposição humana necessária ao controle dos dados e não a confunda com execução preditiva.

O plano de abertura do teste, seeds/repetições/métricas e configurações será congelado antes da avaliação S5.

Não prometer que um simples bloqueio técnico elimina todo risco de vazamento.

21. TESTES E CI

Testes devem usar fixtures pequenas e identificadas como desenvolvimento.

Inclua:
- pureza/determinismo das transformações;
- repetição entre processos;
- split por grupos;
- multiorigem;
- negativos no mesmo split;
- r por fonte;
- edição solicitada versus realizada;
- resegmentação;
- schemas/proveniência;
- cache e falhas de API;
- round-trip;
- detecção de vazamento;
- IDF treino;
- importação idempotente;
- congelamento bloqueado sem requisitos;
- exportação/reprodução por hash.

Esperados independentes:
- conjuntos pequenos com proveniência conhecida;
- r como fração exata;
- permutações explícitas;
- arquivos com conteúdo declarado;
- adulterações deliberadas do manifesto;
- mocks apenas da fronteira de rede/LLM, identificados.

Teste com mock não comprova coleta nem geração real por LLM. Registre ao menos a integração real autorizada necessária; se impedida, mantenha pendência.

Não incorporar ao CI geração paga, chaves pessoais, dataset final ou teste final de pesquisa.

Preserve gatilhos:
- push somente main;
- pull_request destinado main, types apenas opened.

Não acrescentar novos eventos ou publicar para dispará-los.

CI pode validar pipeline com corpus/fixtures públicos pequenos, cache de resposta de teste claramente artificial e dados sem segredos.

Não apresentar resposta fictícia de teste como geração real da API.

22. DOCUMENTAÇÃO E PROMPTS SEGUINTES

Atualize:
- TCC/00;
- TCC/01;
- TCC/02;
- TCC/03 quando houver novos cálculos;
- TCC/06;
- TCC/09;
- TCC/10 se afetado;
- TCC/11;
- TCC/12 quanto à preparação futura;
- TCC/14;
- README público pertinente;
- docs/03 e prompt completo S4.

Corrija referências antigas a κ com um revisor, r como alvo semântico automático e “originalidade comprovada”, preservando histórico e explicando a correção.

Não reescrever H1–H3 em função dos dados produzidos.

Atualize S5A–S5D com:
- dataset/versão efetivamente disponíveis;
- alvo e unidade realmente definidos;
- pendências metodológicas;
- separação entre treino/classificação e índice;
- splits e IDF corretos;
- revisão humana;
- agrupamento nas métricas/intervalos;
- protocolo congelado antes do teste.

Se a S4 não resolver alvo do siamês ou protocolo de H2, mantenha isso como condição antes do treino correspondente. Não assumir aprovação.

23. CRITÉRIOS DE ENCERRAMENTO

Diferencie dois estados:

A. Pipeline S4 implementado/verificado:
- coleta e manifestos;
- grupos/split;
- transformações;
- proveniência/r;
- cache;
- formatos;
- validação;
- revisão preparada;
- versionamento;
- IDF de treino;
- testes e documentação.

B. Dataset experimental pronto:
- decisões necessárias respondidas;
- geração real concluída;
- integridade e vazamento verificados;
- revisão humana prevista concluída;
- exclusões tratadas;
- identidade congelada;
- reprodução validada;
- finalidade/gabarito delimitados.

Não declarar B com apenas A concluído.

Ausência de chave, orçamento, fontes, decisão ou revisão humana não autoriza dados fictícios. Complete o trabalho independente e entregue o impedimento concreto.

Não exigir treinamento ou eficácia científica para fechar a construção dos dados.

24. ENTREGA FINAL

Retorne:

1. Estado: pipeline implementado, candidato ou versão congelada.
2. Decisões existentes, novas decisões e propostas pendentes.
3. Fontes/grupos/splits e quantidades reais.
4. Cobertura C0–C7/métodos/severidades/formatos.
5. Definição do gabarito e r.
6. Cache/modelo/prompts/chamadas reais e custos conhecidos.
7. Validações, testes, comandos, versões e códigos de retorno.
8. Falhas, rejeições e regenerações preservadas.
9. IDF experimental e identidade de construção.
10. Manifesto, hashes, datasheet e exportações locais.
11. Pacote e roteiro de revisão humana acessível.
12. Pendências que impedem congelamento ou uso em S5.
13. Arquivos alterados.
14. Prompts seguintes atualizados.
15. Matriz requisito → implementação → evidência → status.

Separe:
- executado e verificado;
- decisões do projeto;
- limitações;
- pendências humanas/técnicas/metodológicas.

Não apresente contagem de testes como acurácia.
Não invente aceites ou alegue validade semântica por construção.
Não publique arquivos ou execute operações Git proibidas.

Finalize com um veredito delimitado:
“S4 concluída e dataset congelado para [finalidade verificada]”
ou
“Pipeline S4 concluído; dataset ainda pendente de [itens]”
ou
“S4 não concluída”, com os impedimentos específicos.

Pare sem iniciar a Sessão 5.


## Complemento integral posterior — prevalece sobre o pedido histórico

COMPLEMENTO DE CONTEXTO E DECISÕES — SESSÃO 4

Continue a S4 em andamento. Não reinicie o trabalho nem substitua as respostas anteriores. Preserve alterações e evidências existentes.

1. RESTRIÇÃO FINANCEIRA E GERAÇÃO POR LLM

Não autorizo contratação de outra IA, API paga, compra de créditos ou qualquer cobrança adicional.

Já utilizo o Codex pelo ChatGPT. Para os candidatos de transformação textual, use a própria sessão disponível, em lotes controlados e respeitando seus limites, sem presumir acesso programático gratuito a APIs.

Gemini/google-genai deixa de ser requisito obrigatório do projeto. Registre essa mudança metodológica em TCC/ e atualize os prompts afetados, preservando o histórico.

Não implemente mecanismos para contornar limites ou reutilizar credenciais de assinatura como chave de API.

A geração pela própria sessão deve ser registrada honestamente:
- provedor/interface utilizados;
- identificação do modelo somente quando observável;
- prompt e texto-fonte de cada lote;
- respostas efetivamente produzidas;
- IDs dos candidatos;
- hashes;
- data real;
- validações e rejeições;
- relação entre entrada e saída.

Se versão interna, temperatura, seed ou contagem de tokens não estiverem disponíveis, registre “não disponível”. Não invente metadados ou chamadas de API.

As respostas geradas nesta sessão são dados sintéticos reais do procedimento adotado, não mocks de Gemini/API. Preserve-as como artefatos imutáveis. A reprodução reconstruirá o dataset a partir dessas saídas salvas, sem prometer que uma nova geração produzirá o mesmo texto.

O Codex gera candidatos; não certifica suas próprias paráfrases nem substitui a revisão humana. Uma autoavaliação pode ser registrada como triagem do agente, separada da avaliação humana.

Se alguma transformação não puder ser realizada pelos recursos disponíveis, registre a pendência e continue o trabalho independente. Não contrate nada e não preencha saídas fictícias.

2. RESPOSTA À PRIMEIRA PERGUNTA NOVA — REVISÃO PILOTO

Adoto a opção:
“Sim, 8 itens piloto; amostra final pendente.”

Prepare oito itens de revisão piloto, com diversidade de transformações e dificuldades pertinentes, sem alegar representatividade estatística.

Apresente instruções simples, fonte e candidato lado a lado, com campos vazios para:
- aceitar;
- rejeitar;
- marcar como ambíguo;
- justificar.

Não preencha minhas avaliações.

O piloto serve para avaliar clareza do roteiro e esforço de revisão. Não equivale à aprovação dos demais exemplos nem valida toda a amostra experimental.

Só registre tempo humano se ele for efetivamente medido ou informado por mim. Não estime horas como se fossem observadas.

As quantidades apresentadas — 60 fontes × 16 variantes = 960 pares e aproximadamente 384 itens de revisão — são projeções do plano, não dados já gerados ou aprovados.

Confira a contagem pelo desenho efetivo. Diferencie:
- fontes e grupos independentes;
- documentos derivados;
- pares documentais;
- sentenças;
- variantes de formato;
- itens de revisão.

Não trate pares da mesma fonte ou formatos do mesmo conteúdo como observações independentes.

Não considere esta resposta aprovação automática do tamanho final do dataset ou da amostra de revisão. Preserve decisões já tomadas e apresente somente o que ainda exigir definição.

Mantenha o piloto fora do teste final e identifique os exemplos já expostos durante desenvolvimento.

3. RESPOSTA À SEGUNDA PERGUNTA NOVA — C6

Adoto a opção:
“Sim, somente piloto; classe final pendente.”

No piloto, C6 poderá ser operacionalizada como:
“reescrita guiada por frase”.

Procedimento:
- selecionar uma frase-fonte;
- identificar palavras-chave e trechos utilizados;
- gerar um candidato que reutilize esses elementos;
- preservar IDs e proveniência;
- registrar as operações e a saída real.

Derivação conhecida não demonstra preservação semântica.

Não atribuir automaticamente:
- classe paráfrase;
- alvo semântico máximo;
- ausência de contradição;
- qualidade validada;
- conclusão de plágio.

Identifique o item como candidato C6 do piloto, com qualidade semântica e classificação avaliativa pendentes.

Essa definição piloto não modifica silenciosamente a taxonomia experimental final. Registre sua relação com a definição histórica e o que ainda precisa ser decidido.

Não use os escores dos motores ou a classificação V2 para aprovar o gabarito.

4. CONTINUE O TRABALHO INDEPENDENTE

Enquanto as avaliações humanas estiverem pendentes, prossiga com:
- implementação do pipeline;
- fontes e proveniência;
- agrupamento e split antes da geração;
- transformações determinísticas;
- suporte à importação das saídas preservadas do Codex;
- validação de schemas, hashes e vazamento;
- formatos e round-trip;
- testes com fixtures de desenvolvimento;
- preparação do pacote de revisão.

Não iniciar geração completa dependente de decisões ainda abertas.

Não iniciar treinamento, calibração, avaliação dos motores no teste ou Sessão 5.

Não congelar o dataset experimental como aprovado enquanto houver requisito obrigatório de revisão ou gabarito pendente. Uma versão de piloto pode ser selada para rastreabilidade, claramente identificada como desenvolvimento.

O alvo contínuo do siamês continua separado: não transformar r documental, taxa de edição ou a palavra “paráfrase” em verdade semântica sem definição e validação específicas.

5. DOCUMENTAÇÃO E COMUNICAÇÃO

Atualize TCC/00/01/02/06/11/14 e os prompts efetivamente afetados.

Diferencie sempre:
- decisão autorizada;
- proposta;
- implementação;
- teste executado;
- dado gerado;
- revisão humana pendente;
- resultado científico ainda não medido.

Não repita perguntas já respondidas. Agrupe dúvidas novas realmente indispensáveis, explicando a consequência e recomendando uma opção compreensível.

Ao entregar os oito itens, explique exatamente onde devo abrir, o que comparar e como registrar minhas respostas. Não exija que eu certifique código ou fórmulas.

Permanecem proibidos commit, push, tag, merge, rebase, publicação, abertura de PR e contratação de serviços.

Continue a S4 no alcance autorizado, preservando o estado atual e sem iniciar a S5.