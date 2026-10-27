# Prontidão para entrega acadêmica — 2026-10-27

## Parecer e alcance

A base de software e de experimentos do [plano 16](16-plano-conclusao-e-testes.md)
foi executada no alcance adotado. Há resultados e evidências para sustentar a
redação de um TCC. **Não foi demonstrada a prontidão para depósito da monografia**:
não foi localizado um manuscrito final consolidado nem o manual da instituição
entre os materiais inspecionados. A aceitação acadêmica depende da avaliação
do orientador/banca e das regras efetivas do curso, ainda não informadas.

Este parecer é uma inspeção documental do repositório, por Codex (agente de
código; versão exata do modelo não exposta nesta sessão), no HEAD
`153238e409722cdacc8208bda7279b7bf1098763`, com alterações locais posteriores.
Não constitui avaliação institucional nem aprovação atribuída ao orientador.

## O que já tem evidência

| Dimensão | Evidência disponível | Limite para o texto acadêmico |
| --- | --- | --- |
| Pergunta, método e decisões | [Metodologia](../TCC/02-metodologia.md), [decisões](../TCC/01-decisoes.md) | Consolidar a versão efetivamente adotada; estados históricos não são pendências atuais |
| Implementação e testes obrigatórios | [Matriz P12](../TCC/evidencias/codex-p12-02/matriz-testes.md), [execução P0–P12](../TCC/evidencias/codex-p12-02/matriz-execucao.md) | 103 IDs não significam 100% de cobertura de linhas/ramos; percentual não medido |
| Execução remota | [CI 40512937738](https://github.com/asnorferreira/hybrid-text-similarity/actions/runs/40512937738), [registro](../TCC/evidencias/codex-ci-40512937738-01/relatorio.md) | Aprova a revisão publicada 153238e; alterações posteriores exigem validação própria |
| Referência humana | [P9](../TCC/evidencias/codex-p09-02/relatorio.md) | Dois códigos de anotador, independência declarada; identidade não autenticada; referência parcial e dependente |
| H1/H2/P1 | [Avaliação única P10](../TCC/evidencias/codex-p10-01/relatorio.md) | Resultados negativos e limitações devem aparecer explicitamente; não selecionar modelos usando o teste já observado |
| H3 original | [Tabelas P11](../TCC/evidencias/codex-p11-01/h3-tentativa-03/h3-tabelas.md) | Metas não atingidas em todos os cenários obrigatórios; melhoria de engenharia é outro experimento |
| Reprodução | [P12](../TCC/evidencias/codex-p12-02/relatorio.md) | Pacote histórico corresponde àquela revisão, não a modificações futuras |

Resultados negativos não exigem transformar as hipóteses em positivas para
concluir um estudo. O texto deve explicar o que os dados permitem concluir:
a fusão e o siamês avaliados não superaram as bases nos critérios adotados;
Platt piorou Brier/log-loss; as metas de H3 original não foram todas satisfeitas.
Não se pode afirmar validação universal, detecção comprovada de plágio,
generalização populacional, equivalência entre ancestralidade e semântica,
ou reprodução integral dos artigos adaptados.

## O que falta conferir para o depósito

1. **Manuscrito consolidado:** introdução, problema, objetivos, fundamentação,
   método efetivo, resultados, discussão e conclusões encadeados. Os registros
   de desenvolvimento em TCC/00–14 não demonstram por si só essa entrega.
2. **Discussão dos limites:** referência humana finita, dependência entre
   derivações, critérios de elegibilidade, H2 com encoder congelado/cabeça MLP,
   diferenças de pooling, alcance das adaptações, CPU e cenários repetidos de H3.
   Separar desempenho de software, validade dos rótulos e evidência científica.
3. **Rastreabilidade acadêmica:** cada tabela/figura liga ao experimento real,
   com denominador e unidade, sem somar reexecuções; referências e citações
   conferidas contra as fontes, licenças e atribuições das adaptações.
4. **Normas reais do curso:** modalidade, template, elementos pré/pós-textuais,
   formato de referências, depósito, material suplementar e apresentação.
   Nenhuma regra institucional específica foi presumida nesta inspeção.
5. **Tratamento dos participantes e dos dados:** conferir com o orientador as
   exigências institucionais aplicáveis, registros de participação e o que pode
   ser compartilhado. Nomes civis não são necessários às métricas; os JSONs não
   autenticam as pessoas. Pacotes e evidências privadas não devem ser incluídos
   automaticamente no Git público.
6. **Revisão acadêmica e entrega:** conferir conclusões/objetivos com o orientador,
   preparar apresentação e demonstração conforme o regulamento informado.

Esses itens são verificações de prontidão, não novas exigências científicas
inventadas. Não há retreino, full fine-tuning, isotônica ou repetição de P10
obrigatórios no plano vigente. Se desejada melhoria científica H1/H2, ela
precisa de novo protocolo e avaliação independente, sem reaproveitar P10 como
teste inédito. A melhoria H3 autorizada foi implementada/testada e medida nos 12 cenários:
zero falhas e 7/8 metas obrigatórias atendidas; 120 sentenças/cinco usuários
com modelos ativos teve p95 de 12,523 s para meta de 10 s. A hipótese posterior segue não sustentada
integralmente. [Evidências](../TCC/evidencias/codex-h3-melhoria-01/relatorio.md).
Entradas repetidas após aquecimento favorecem cache; essa medição não
altera a avaliação sobre a ausência de manuscrito localizado.

## Busca realizada e informação solicitada

Foram inspecionados os registros do plano 16, README, TCC/00–14 e a listagem de
materiais .tex/.bib/.docx/.pdf e nomes relacionados a monografia/manual nas
pastas TCC e docs. Foram localizados guia técnico, artigos e PDFs de evidência,
mas não um artefato identificado como monografia final nem manual institucional.
Isso não prova que tais materiais não existam fora desse conjunto.

Foi solicitado ao autor o caminho do manuscrito e a instituição/curso ou manual
de TCC para concluir a avaliação específica de depósito. Até essa informação,
o parecer permanece: **base experimental disponível; depósito acadêmico ainda
não verificável**.
