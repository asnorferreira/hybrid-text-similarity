# Plano de conclusão e plano de testes

## Atualização do CI — run 40510356894, 2026-10-27

A revisão publicada `c20d3bf` passou nos 1.022 testes Core, mas o MongoDB
8.0.34 encerrou na inicialização; as etapas dependentes ficaram sem execução.
A reprodução local confirmou a incompatibilidade dessa imagem com kernel
Linux >=6.19. O CI foi corrigido localmente para o MongoDB 7.0.45 fixado por
digest, já verificado na S5D, em volume isolado. Web15/tipos, integração,
segurança12, paginação, dez E2E e auditorias passaram em Docker. Logs dos
serviços, kernel e runtime Mongo passam a ser preservados pelo workflow.
O CI remoto da correção continua pendente de publicação pelo autor; o item
remoto do checklist permanece aberto. Nenhum retreino/inferência P10 repetida.

[Relatório e evidências da correção](../TCC/evidencias/codex-ci-40510356894-01/relatorio.md).
O estado P12 abaixo descreve a entrega anterior à correção do CI.

## Estado final local — P0–P12, 2026-10-27

Reprodução final vigente: P12 tentativa02. O empacotador conserva também
arquivos históricos de cache exigidos pelos selos; a cópia nova conferiu
os selos antes/depois e repetiu todas as suítes. A tentativa anterior
e a falha de integridade da primeira entrega foram preservadas.



Plano 16 executado no alcance documentado. P9: duas devoluções de 96 IDs,
independência humana declarada, identidade não autenticada, nomes dispensáveis;
95 H1/82 H2 elegíveis, ambiguidades mantidas. Referência congelada antes da
inferência única P10. H1/H2 não sustentadas; Platt piorou Brier/log-loss.
H3 não sustentada em todos os cenários obrigatórios, com 12 cenários completos e falhas preservadas.
P12: cópia limpa da árvore local com manifesto, Core 1022, Web 15/tipos,
19 E2E ativos e três indisponibilidades aprovados; seeds/12 controles/retomada,
recarga de seis H1/Platt/H2 em validation e recálculo P10 aprovados.
Sem retreino, calibração, inferência P10 repetida ou publicação pelo agente.
CI remoto de 3d26db5 passou; CI da revisão final depende da publicação manual.

[Relatório final](../TCC/evidencias/codex-p12-02/relatorio.md) ·
[Matriz por ID](../TCC/evidencias/codex-p12-02/matriz-testes.md) ·
[Partes P0–P12](../TCC/evidencias/codex-p12-02/matriz-execucao.md).


## Registros anteriores preservados


## Registro histórico — fechamento P11

Integração opt-in verificada; Core 1.022, Web 15/tipos, 12 controles de segurança,
RG-02/PL-09 em 32 casos e E2E-01–08 aprovados. H3 não sustentada em todos os cenários obrigatórios; todos os 12
cenários foram medidos sem mudar protocolo/modelos. Tentativa01 inválida por
cadência preservada; tentativa02 parcial preservada após correção de integração;
tentativa03 auditada por timestamps. P12 ainda pendente.
CI publicado anterior passou; código posterior ainda local, publicação pelo autor.

[Relatório P11](../TCC/evidencias/codex-p11-01/relatorio.md) ·
[H3](../TCC/evidencias/codex-p11-01/h3-tentativa-03/h3-tabelas.md).


## Registro histórico — estado nessa etapa — P10 concluída, 2026-10-27

Avaliação científica única concluída e claim preservado: 96 predições,
95 H1 e 82 H2 elegíveis; referência humana parcial, independente por declaração.
H1 não sustentada: fusões macro-F1 0,4104104104, lexical 0,4173913043 e
semântico 0,4090909091. H2 não sustentada: Spearman siamês 0,1823451914,
SBERT 0,8166448555. P1 piorou Brier/log-loss; ECE menor não implica ganho global.
Sem novo treino, escolha posterior ou repetição de inferência. Recálculo aprovado.
P11/P12 pendentes; CI publicado de 3d26db5 passou, código posterior ainda local.
Registros anteriores abaixo preservam estados históricos e seus limites.

[P10: relatório](../TCC/evidencias/codex-p10-01/relatorio.md).

## Registro histórico — estado nessa etapa — P9 concluída em 2026-10-27, após as devoluções

Dois arquivos finais recebidos, preservados e auditados: 96 IDs cada, participação
humana independente declarada; identidade não autenticada pelo JSON. κ H1=1,0
em 95 pares; Spearman H2=0,9884743917439475 em 82 pares. Ambiguidades preservadas,
sem substituição de itens. Referência congelada antes das predições:
`8b4af816b99468b3f8eac081d1009004916d8513cdf2a29dabb5ef6f3bd50047`.
Runner final e guards implementados; 1.010 testes Core aprovados em Docker/CPU,
Pyright 136 arquivos sem erros/avisos e Ruff aprovado. Os 838 arquivos científicos
pré-seleção foram conferidos, com única mudança de roteamento CLI documentada.

P10 ainda não executada neste registro; P11/P12 pendentes. O CI publicado pelo
autor em 3d26db5 passou no run 40455735826; código posterior ainda é local.
Os blocos anteriores abaixo passam a ser histórico dos seus próprios estados.

[Relatório P9](../TCC/evidencias/codex-p09-02/relatorio.md) ·
[Referência](../TCC/evidencias/codex-p09-02/referencia-final-01.json) ·
[Testes](../TCC/evidencias/codex-p09-02/testes.json).

## Preparação humana cega e correção local do CI — 2026-10-27

**Pacotes A1/A2 preparados e verificados:** 96 pares do teste, cinco por cada
uma das 16 células método/severidade mais 16 combinações sem ancestralidade
direta; 96 pares textuais ordenados únicos. Mesmos itens em ordens diferentes,
formulário offline com respostas inicialmente vazias, rubrica, rascunho/retomada,
exportação e declaração pseudônima. Nomes civis dispensáveis; o autor deverá
enviar separadamente a duas pessoas reais distintas e registrar as datas.
Vínculo/exposição anterior e participação individual precisam ser declarados.
As declarações não autenticam identidade nem provam independência por si sós.

**Verificação local final em Docker/CPU:** 987 testes do Core aprovados;
5 fluxos do formulário com fixtures artificiais no Chromium aprovados;
ambos os pacotes reais percorridos nos 96 itens sem preencher julgamentos;
CRC/hashes/campos cegos/cobertura conferidos. Pyright: 134 arquivos, zero
erros/avisos; Ruff aprovado. Testes anteriores falhos e a interrupção do autor
foram preservados. Os números não somam reexecuções nem testes de ambientes
diferentes. A Web/integração histórica não foi reexecutada nesta mudança.

**CI 40451552564 corrigido localmente:** orçamento numérico explícito apenas
para campos semânticos float32 e derivados; equivalência limitada LF/CRLF no
manifesto. Snapshot e recursos científicos preservados; 47 proteções da política
mais 34 RG-01 aprovados. O run remoto original continua falho, aguardando
publicação e nova execução pelo autor; não houve commit/push pelo agente.

**Estado científico:** PH2/D5 autoriza esta preparação humana do caminho B/96,
sem nomes ou respostas inventados. Modelos/IDF/dataset/código inventariados antes
da seleção. Textos expostos para anotação, **zero respostas humanas recebidas,
zero predições do teste, referência científica ainda não congelada**. P9 permanece
parcial: faltam respostas reais, concordância real, elegibilidade/congelamento e
runner final. P10–P12, RG-02, PL-09 e E2E-01–09 continuam pendentes no alcance
científico/integrado previsto. Não houve novo treino nem ajuste de esperado.

Os registros abaixo descrevem snapshots históricos. Este registro
atualiza somente o alcance desta entrega.

[Pacote A1](../TCC/evidencias/codex-p09-01/campanha-01/A1.zip) ·
[Pacote A2](../TCC/evidencias/codex-p09-01/campanha-01/A2.zip) ·
[Roteiro do autor](../TCC/evidencias/codex-p09-01/roteiro-autor.md) ·
[Relatório](../TCC/evidencias/codex-p09-01/relatorio.md) ·
[CI local](../TCC/evidencias/codex-ci-40451552564-01/relatorio.md).


<!-- VERIFICACAO-INTEGRAL-20261027 -->
## Verificação integral disponível — 2026-10-27

Nova execução local em Docker/CPU: **899 testes do Core, 12 da Web e 10 do
navegador aprovados**, sem falhas, erros ou skips. A matriz reconcilia os 70 IDs
NF/NFo/RF, RL-01–06 e PL-01–08. Os 34 testes RG-01 passaram sem regravar o
snapshot. Integração, persistência/retomada, 12 controles de segurança e
paginação passaram. Pyright analisou 128 arquivos sem erros ou avisos; o
typecheck passou. Npm sem alertas; pip-audit sem alertas conhecidos nas
distribuições cobertas, com **torch CPU e modelo spaCy fora da cobertura** da
ferramenta. A carga de engenharia mediu 18 requisições sem erros, com 1/2
usuários; **não é H3**. Tentativas falhas de infraestrutura e registro foram
preservadas e explicadas.

**Plano completo ainda pendente:** D5 precisa de dois humanos reais; recomendam-se
96 pares, sem seleção ou anotação nesta verificação. A autorização geral do
autor já foi recebida. Faltam referência e runner da P9, avaliação P10,
integração/H3 da P11 e reprodução P12. RG-02, PL-09 e E2E-01–09 não foram
declarados aprovados. Nenhum treino novo ou predição científica do teste.
Serviços isolados parados, volumes preservados, sem stage, commit, push ou
publicação.

[Relatório](../TCC/evidencias/codex-verificacao-integral-01/relatorio.md) ·
[Matriz por ID](../TCC/evidencias/codex-verificacao-integral-01/matriz-testes.md) ·
[Partes/decisões/hipóteses](../TCC/evidencias/codex-verificacao-integral-01/matriz-execucao.md) ·
[Preparação PH2](../TCC/evidencias/codex-verificacao-integral-01/preparacao-ph2.md).
<!-- /VERIFICACAO-INTEGRAL-20261027 -->

Atualização: 2026-10-27. **A entrega integral ainda não está concluída.** P0–P8
foram executadas no alcance local, com H1/Platt e agora H2 científicos exploratórios.
O próximo passo é PH2, antes de P9–P12. Não houve abertura preditiva do teste,
anotação humana, integração dos modelos treinados no app ou medição científica H3.
CI remoto continua dependente da publicação manual do autor.

Esta revisão documental corrige o estado antigo e conserva o desenho aprovado:
D1–D4 pelo autor; H1 na r3 e reinício técnico r3.1; H2 na r4, em 2 GB sem swap.
Não atribui aprovação separada ao orientador. O planejamento original foi preservado
na [auditoria](../TCC/evidencias/codex-entrega-01/antes/docs/16-plano-conclusao-e-testes.md).
As alternativas históricas da seção 3 não substituem as decisões vigentes.

[Auditoria de entrega](../TCC/evidencias/codex-entrega-01/relatorio.md) ·
[Treino H2 e validação P8](../TCC/evidencias/codex-p08-02/relatorio.md) ·
[Handoff e hashes do selecionado](../TCC/evidencias/codex-p08-02/handoff.json).

## 1. Estado atual

P0–P12 concluídas no alcance local, com evidências E/T/V/G individuais e
matriz final por ID. PH1/PH2 e D1–D6 registrados sob autorização do autor.
Nenhuma aprovação específica do orientador é atribuída.

| Etapa | Estado | Evidência |
| --- | --- | --- |
| P0 | concluída no alcance registrado | [codex-p00-02](../TCC/evidencias/codex-p00-02/handoff.json) |
| P1 | concluída no alcance registrado | [codex-p01-02](../TCC/evidencias/codex-p01-02/handoff.json) |
| P2 | concluída no alcance registrado | [codex-p02-03](../TCC/evidencias/codex-p02-03/handoff.json) |
| P3 | concluída no alcance registrado | [codex-p03-01](../TCC/evidencias/codex-p03-01/handoff.json) |
| P4 | concluída no alcance registrado | [codex-p04-01](../TCC/evidencias/codex-p04-01/handoff.json) |
| P5 | concluída no alcance registrado | [codex-p05-02](../TCC/evidencias/codex-p05-02/handoff.json) |
| P6 | concluída no alcance registrado | [codex-p06-01](../TCC/evidencias/codex-p06-01/handoff.json) |
| P7 | concluída no alcance registrado | [codex-p07-04](../TCC/evidencias/codex-p07-04/handoff.json) |
| P8 | concluída no alcance registrado | [codex-p08-02](../TCC/evidencias/codex-p08-02/handoff.json) |
| P9 | concluída no alcance registrado | [codex-p09-02](../TCC/evidencias/codex-p09-02/handoff.json) |
| P10 | concluída no alcance registrado | [codex-p10-01](../TCC/evidencias/codex-p10-01/handoff.json) |
| P11 | concluída no alcance registrado | [codex-p11-01](../TCC/evidencias/codex-p11-01/handoff.json) |
| P12 / S5D | concluída na cópia limpa | [P12](../TCC/evidencias/codex-p12-02/relatorio.md) |

## 2. Auditoria final L1–L9

| Lacuna | Fechamento / limite |
| --- | --- |
| L1/L2 | Treinos autorizados concluídos; recursos medidos; sem novo fit |
| L3 | H1 avaliada uma vez; hipótese não sustentada |
| L4 | Dois humanos declarados/96 IDs; referência parcial, identidade não autenticada |
| L5 | S5C única selada; recálculo das predições salvas aprovado |
| L6 | Loaders/API/UI opt-in, RG-02/PL-09/E2E aprovados |
| L7 | H3 completa, metas preservadas e falhas reportadas; veredito no relatório |
| L8 | CI de3d26db5 passou; revisão local final aguarda publicação manual e novo CI |
| L9 | S5D em destino novo, suítes/recargas/E2E-09; licenças/citação/texto final |

## 3. Alternativas históricas anteriores à PH1

**Histórico, não instrução vigente de treino.** D1 adotou B; D2 adotou encoder congelado com cabeça MLP, lr 2e-6. As opções e estimativas abaixo eram propostas antes da medição e não foram todas adotadas.

"Válido" aqui significa: cada afirmação do texto final tem execução registrada, e o alcance declarado bate com o tipo de referência usada. Nenhum caminho permite afirmar validação semântica independente sem anotação humana.

| | Caminho A — mínimo válido | Caminho B — recomendado | Caminho C — protocolo original |
| --- | --- | --- | --- |
| Máquina | Atual (7,35 GiB) | Atual ou do colega | 16 GiB, WSL com teto de 6 GiB |
| H1 | Logísticas + fusão aprendida + baselines Q5-V2 e majoritária | Igual ao A | Igual ao A |
| H2 | Encoder congelado, só a cabeça (≈ 0,5 GiB) **ou** cosseno com embeddings congeladas | Cosseno (`CosineSimilarityLoss`) com embeddings congeladas | Fine-tune completo, lr escolhido na validação |
| Platt | Calibração da fusão para derivação (seção 4) | Igual ao A | Igual ao A |
| Referência | Automatizada dependente | Automatizada + **80–100 pares do teste anotados por 2 humanos** | Anotação humana ampla |
| H3 | Protocolo pequeno na máquina atual | Protocolo completo (seção 7.3) | Igual ao B |
| Revisão do protocolo | Revisão 3 (H2 e H1) | Revisão 3 | Revisão 3 (só H1 e lr) |
| O que permite afirmar | H1 e H2 **exploratórias** contra referência dependente | H1 e H2 contra referência humana parcial, com concordância medida | Interpretação original de H2, se κ aceitável |
| Risco principal | Banca questionar a independência | Tempo de anotação | Máquina e prazo |

Recomendação: **Caminho B**. Ele usa o hardware atual (com o H2 revisado), e a anotação humana é a ação que mais aumenta o valor científico por hora gasta.

### Opções por lacuna

| Lacuna | Opção 1 | Opção 2 | Opção 3 |
| --- | --- | --- | --- |
| L1 memória | Medir o pico real de RSS do H1 e revisar a reserva com evidência | Máquina do colega (16 GiB) | Linux nativo, sem a camada WSL |
| L2 siamês | Cosseno + embeddings congeladas (reduz o estado do Adam em cerca de 80%; a matriz de 250 mil × 384 ≈ 96 M parâmetros fica fixa) | Encoder congelado + cabeça MLP | LoRA (dependência `peft`) |
| L3 H1 | Logística `[L, C_op]` | `[L, C_op, OSA]` se OSA for aprovada como feature | Manter só as 3 atuais e declarar o limite |
| L4 referência | 2 anotadores humanos em 80–100 pares do teste, às cegas | 1 anotador humano + IA, com concordância IA × humano | Manter a referência automatizada e declarar "exploratório" |
| L5 S5C | Runner novo em `application/` + CLI `experimento avaliar` | Notebook versionado (menos rastreável) | — |
| L6 app | Modelos atrás de flag de configuração versionada | Só documentar, sem integrar | — |
| L7 H3 | Protocolo da seção 7.3 | Declarar H3 como não testada | — |
| L8 CI | Ler log/artefato, reproduzir em Docker, corrigir | — | — |

Cada escolha de L2 a L4 é uma decisão D1–D6 (seção 8).

### Sugestões históricas não adotadas como alteração da H2

O protocolo efetivo manteve lr 2e-6; não aplicar as sugestões abaixo ao modelo selecionado.

- lr na faixa usual de fine-tune de sentence-transformers (de 1e-5 a 2e-5), escolhido na validação;
- Spearman do SBERT na validação registrado como linha de base para a seleção de época;
- seed, janelas completas, orçamento de tempo e teste fechado mantidos.

---

## 4. Regressão logística e Platt scaling

### Parecer

**Sim, Platt scaling é válido e cabe no projeto, com três ressalvas.**

1. **Ele já estava previsto.** As decisões 5 e 6 de `01-decisoes.md` dizem "limiar calibrado na validação" e "limiares calibrados na validação", e isso nunca foi feito. As regras Q5-V2 seguem sem calibração. Platt scaling é uma forma fundamentada de cumprir essa pendência.
2. **Na H1 há uma forma logística sobre escores.** A classificação multinomial de quatro relações não equivale ao Platt binário original. Um segundo ajuste sobre suas saídas exigiria objetivo e validação próprios. O ganho está em outro lugar (abaixo).
3. **Ele não muda a H2.** Uma transformação estritamente crescente preserva os ranks e o Spearman; inclinação negativa inverte a ordem e saturação numérica pode criar empates. Platt P1 estima derivação, não o alvo semântico H2, e não foi usado para alterar seus escores. Ele também só muda o macro-F1 se o limiar de decisão mudar.

### Onde Platt agrega valor

| Uso | Escore de entrada | Alvo | Dados | Valor |
| --- | --- | --- | --- | --- |
| **P1. Probabilidade de derivação no app** (recomendado) | Fusão `F` por par de sentenças alinhado | Binário: sentença do suspeito derivada da fonte (proveniência da S4) | Pares de sentenças do split de validação da S4 | Substitui limiares arbitrários por uma probabilidade calibrada, com centenas de pares e não 17 |
| P2. Limiar de "sem correspondência" | `max(L, C_op)` | Binário: com ou sem correspondência | Mesmo do P1 | Calibra o corte 0,30 da regra Q5-V2 |
| P3. Calibração da saída do siamês | Sigmoide do siamês | Alvo 0–1 da H2 | 13 itens de validação | Fraco: amostra mínima e sem efeito no Spearman; só diagnóstico |

Cuidados obrigatórios do P1/P2:

- O alvo é **derivação textual** (tarefa A do contrato da S4), não similaridade semântica. A tela do app deve chamá-lo de "probabilidade de derivação", nunca de "índice" ou "similaridade" (`02-metodologia.md`: "não converter probabilidade de classe em índice").
- `r`, classe C0–C7, origem e tipo de transformação **nunca** entram como feature. A proveniência só serve como alvo.
- Ajustar no split de **validação** (ou em validação cruzada só dentro de treino + validação), nunca no treino usado para o modelo nem no teste.
- O índice contínuo do app (fusão fixa) continua igual. A probabilidade aparece como informação separada.

### Método

Platt com os alvos regularizados do artigo original (evita probabilidades 0/1 com poucos dados):

```latex
P(y=1 \mid s) = \frac{1}{1 + \exp(A s + B)}, \qquad
t_{+} = \frac{N_{+} + 1}{N_{+} + 2}, \quad t_{-} = \frac{1}{N_{-} + 2}
```

A e B são obtidos minimizando a log-loss sobre os alvos t₊ e t₋. Comparar com:

- o escore bruto tratado como probabilidade (linha de base sem calibração);
- a regressão isotônica, só se a validação tiver mais de cerca de 1.000 pares (com poucos dados ela sobreajusta).

### Plano de testes — regressão logística (H1) e Platt

| ID | Teste | Entrada | Critério de aprovação |
| --- | --- | --- | --- |
| RL-01 | Export portátil igual ao sklearn | Classificador ajustado em fixture | Predições do JSON iguais a `model.predict` (já existe: `portable classifier differs`) |
| RL-02 | Determinismo | Mesma seed, mesmos dados, 2 ajustes | Coeficientes iguais até 1e-12 |
| RL-03 | Recusa de feature proibida | Feature `r`, `origin` ou `class` | Erro de contrato antes do ajuste |
| RL-04 | Classe ausente no treino | Fixture sem `parafrase` | Falha explícita (readiness: mínimo de 2 por classe) |
| RL-05 | Fusão aprendida com 2 features | `[L, C_op]` | Coeficientes finitos; export recarregável; predição igual |
| RL-06 | Sanidade de separação | Fixture sintética linearmente separável | Acurácia de validação = 1,0 |
| PL-01 | Monotonicidade | Escores crescentes | Probabilidades não decrescentes se A < 0 |
| PL-02 | Intervalo | Qualquer escore finito | 0 < P < 1, finito |
| PL-03 | Alvos regularizados | N₊ = 3, N₋ = 5 | t₊ = 0,8; t₋ = 1/7 |
| PL-04 | Recuperação de parâmetros | Dados gerados com A = −8, B = 4, n = 5.000 | Â e B̂ a menos de 10% dos valores reais |
| PL-05 | Preservação de ordem | Escores da validação | Spearman(escore, P) = 1 |
| PL-06 | Split correto | Tentativa de ajuste com split `test` | Recusa pelo guard de teste |
| PL-07 | Métricas de calibração | Validação | Brier, log-loss, ECE e contagens/diagrama calculados corretamente; melhoria ou degradação reportada. Ressubstituição identificada; métricas independentes null com motivo quando não há grupos suficientes |
| PL-08 | Persistência | Parâmetros A, B + hash da entrada | Recarga gera probabilidades idênticas |
| PL-09 | Não vira índice | Resposta da API com P1 ativo | `index.value` inalterado em relação à fusão fixa; P em campo próprio |

Métricas do relatório: Brier, log-loss, ECE (10 faixas, com a contagem de cada faixa visível) e diagrama de confiabilidade, além do F1 com o limiar 0,5 calibrado comparado ao limiar Q5-V2.

---

## 5. Plano de testes por classes de equivalência

Técnica de Jorgensen (*Software Testing: A Craftsman's Approach*):

- **Normal fraca:** cada classe válida aparece em pelo menos um caso; supõe falha única. Número de casos = maior número de classes de uma variável.
- **Normal forte:** produto cartesiano das classes válidas; detecta interação entre variáveis.
- **Robusta fraca:** normal fraca + um caso para cada classe inválida, com todas as outras variáveis válidas.
- Robusta forte (produto com inválidas) **não** entra: o sistema rejeita na primeira validação, então a combinação de inválidas acrescenta pouco.

Unidade sob teste: o fluxo de comparação, isto é, `POST /v1/extract` + `POST /v1/compare` do core (pytest + cliente Flask). Uma amostra também passa pela interface (Playwright, seção 7).

### 5.1 Variáveis e classes

| Variável | Classes válidas | Classes inválidas (saída esperada) |
| --- | --- | --- |
| **V1 Formato** | F1 TXT · F2 DOCX · F3 PDF com texto · F4 texto colado | FX1 extensão incompatível com o tipo real (415 `unsupported_format`) · FX2 formato não suportado, por exemplo ODT (415) · FX3 PDF só imagem (422 `extraction_failed`, "OCR não executado") · FX4 arquivo corrompido (422 `extraction_failed`) |
| **V2 Tamanho do upload** | T1 1 B a 5.242.880 B | TX1 vazio, 0 B (422 `no_useful_content`) · TX2 5.242.881 B (413 `invalid_input`) |
| **V3 Caracteres do texto** | C1 1 a 30.000 | CX1 só espaços (422 `no_useful_content`) · CX2 30.001 (422 `invalid_input`) |
| **V4 Sentenças** | S1 1 a 120 | SX1 121 sentenças (422 `invalid_input`) |
| **V5 Tamanho da sentença** | SL1 1 a 4.000 caracteres | SLX1 4.001 caracteres (422 `invalid_input`) |
| **V6 Encoding TXT** | E1 UTF-8 · E2 UTF-8 com BOM · E3 cp1252 | EX1 bytes inválidos em UTF-8 e cp1252 (422) · EX2 BOM UTF-8 com conteúdo inválido (422) |
| **V7 Modo** | M1 `hybrid` · M2 `lexical` | MX1 `inventado` (400 `invalid_input`) |
| **V8 Contrato** | K1 `contract_version` 1.0, campos exatos | KX1 versão 2.0 (400) · KX2 campo extra `r` (400) · KX3 campo extra `origin` (400) · KX4 `suspect` ausente (400) · KX5 `text` numérico (400) |
| **V9 Relação entre os textos** | R1 idênticos · R2 cópia editada · R3 paráfrase · R4 sem correspondência | — (domínio de saída, sem classe inválida) |
| **V10 Recursos** | RS1 modelo e IDF disponíveis | RSX1 modelo indisponível no modo `hybrid` (503 `resource_unavailable`; `lexical` continua funcionando) · RSX2 entrada acima de 12.000 tokens (503) |
| **V11 Script** | U1 latim/PT-BR · U2 árabe · U3 CJK | — (cobertos pelas fontes da S1) |
| **V12 Sessão (app web)** | A1 sessão válida com CSRF | AX1 sem sessão (redirecionamento para login) · AX2 sessão expirada · AX3 CSRF ausente (403) · AX4 usuário B abrindo resultado de A (404/403) |

Valores-limite usados nas classes válidas: mínimo, típico e máximo (por exemplo, 1, 500 e 30.000 caracteres). Assim o plano cobre também a análise de valor-limite.

Saída esperada para R1–R4 no modo `hybrid` (regras Q5-V2): R1 → `copia_exata`; R2 → `copia_editada` (D ≥ 0,80); R3 → `parafrase` (C_op > 0,75); R4 → `sem_correspondencia_detectada`. Os casos R são **testes de comportamento do sistema**, não avaliação científica de H1.

### 5.2 Normal fraca (12 casos)

A variável com mais classes válidas é V1 ou V9 (4 classes), mas V6 só vale para TXT. Por isso foram usados 12 casos, para cobrir cada classe válida ao menos uma vez com combinações plausíveis.

| ID | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V9 | V11 | Esperado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NF-01 | TXT | 1 KB | 500 | 5 | típica | UTF-8 | hybrid | R1 | U1 | 200, `copia_exata`, índice 100 |
| NF-02 | DOCX | 20 KB | 2.000 | 20 | típica | — | hybrid | R2 | U1 | 200, `copia_editada` |
| NF-03 | PDF | 100 KB | 5.000 | 40 | típica | — | hybrid | R3 | U1 | 200, `parafrase` |
| NF-04 | colado | — | 800 | 8 | típica | — | lexical | R4 | U1 | 200, `semantic_index` null |
| NF-05 | TXT | 1 KB | 500 | 5 | típica | UTF-8 BOM | hybrid | R1 | U1 | 200, texto sem BOM |
| NF-06 | TXT | 1 KB | 500 | 5 | típica | cp1252 | lexical | R2 | U1 | 200, acentos preservados |
| NF-07 | DOCX | 15 KB | 1.500 | 10 | típica | — | hybrid | R1 | U2 | 200, segmentação árabe |
| NF-08 | PDF | 80 KB | 1.500 | 10 | típica | — | hybrid | R3 | U3 | 200, segmentação CJK |
| NF-09 | colado | — | 1 | 1 | 1 | — | hybrid | R1 | U1 | 200 (mínimo) |
| NF-10 | colado | — | 30.000 | 120 | — | — | lexical | R4 | U1 | 200 (máximos simultâneos de V3/V4) |
| NF-11 | TXT | 5.242.880 B | ≤ 30.000 | ≤ 120 | — | UTF-8 | lexical | R4 | U1 | upload aceito no limite (texto do arquivo ajustado para não estourar V3) |
| NF-12 | colado | — | 4.000 | 1 | 4.000 | — | hybrid | R2 | U1 | 200 (sentença no limite) |

### 5.3 Normal forte (32 casos)

O produto cartesiano completo é inviável (4 × 3 × 2 × 4 × 3 × … ≫ 1.000). O produto fica nas variáveis com interação plausível: **V1 Formato (4) × V7 Modo (2) × V9 Relação (4) = 32 casos**, com V2–V6 e V11 fixos em valores típicos válidos (UTF-8, U1).

| | R1 idênticos | R2 editada | R3 paráfrase | R4 sem correspondência |
| --- | --- | --- | --- | --- |
| **TXT · hybrid** | NFo-01 | NFo-02 | NFo-03 | NFo-04 |
| **TXT · lexical** | NFo-05 | NFo-06 | NFo-07 | NFo-08 |
| **DOCX · hybrid** | NFo-09 | NFo-10 | NFo-11 | NFo-12 |
| **DOCX · lexical** | NFo-13 | NFo-14 | NFo-15 | NFo-16 |
| **PDF · hybrid** | NFo-17 | NFo-18 | NFo-19 | NFo-20 |
| **PDF · lexical** | NFo-21 | NFo-22 | NFo-23 | NFo-24 |
| **Colado · hybrid** | NFo-25 | NFo-26 | NFo-27 | NFo-28 |
| **Colado · lexical** | NFo-29 | NFo-30 | NFo-31 | NFo-32 |

Critérios de aprovação:

- **Invariância de formato:** o mesmo conteúdo em TXT, DOCX, PDF e colado produz as mesmas sentenças extraídas e o mesmo índice (tolerância 1e-9). Diferenças só onde a extração de PDF estiver declarada como limitação.
- **Modo:** em `lexical`, `semantic_index`, `matrices.semantic_raw` e `fused` são null; `lexical_index` é igual ao do `hybrid`.
- **Relação:** a classe Q5-V2 esperada para R1–R4 no modo `hybrid`. No modo `lexical`, classes/matches semânticos permanecem null por contrato; não exigir paráfrase.

Conteúdo: usar 4 pares fixos de desenvolvimento (um por R), escritos à mão e convertidos para os 4 formatos com o gerador de formatos da S4 (`adapters/dataset_formats.py`). **Não** usar pares do teste da pesquisa.

Extensão opcional (+24 casos): V1 × V11 (U1, U2, U3) × V7, para checar Unicode em todos os formatos.

### 5.4 Robusta fraca (12 casos normais + 26 inválidos = 38 casos)

Os 12 casos da normal fraca, mais **um caso por classe inválida**, com todas as outras variáveis em valores válidos típicos (TXT UTF-8, 500 caracteres, 5 sentenças, `hybrid`, R1, sessão válida).

| ID | Classe inválida | Entrada | Esperado |
| --- | --- | --- | --- |
| RF-01 | FX1 | `.txt` com bytes de PDF | 415 `unsupported_format` |
| RF-02 | FX2 | arquivo `.odt` | 415 `unsupported_format` |
| RF-03 | FX3 | PDF escaneado, sem camada de texto | 422 `extraction_failed`, mensagem cita OCR |
| RF-04 | FX4 | DOCX truncado (ZIP inválido) | 422 `extraction_failed` |
| RF-05 | TX1 | arquivo de 0 B | 422 `no_useful_content` |
| RF-06 | TX2 | 5.242.881 B | 413 `invalid_input` |
| RF-07 | CX1 | só espaços e quebras de linha | 422 `no_useful_content` |
| RF-08 | CX2 | 30.001 caracteres | 422 `invalid_input` |
| RF-09 | SX1 | 121 sentenças | 422 `invalid_input` |
| RF-10 | SLX1 | 1 sentença de 4.001 caracteres | 422 `invalid_input` |
| RF-11 | EX1 | TXT com byte 0x81 isolado | 422 (decodificação sem perda impossível) |
| RF-12 | EX2 | BOM UTF-8 + bytes inválidos | 422 |
| RF-13 | MX1 | `mode: "inventado"` | 400 `invalid_input` |
| RF-14 | KX1 | `contract_version: "2.0"` | 400 |
| RF-15 | KX2 | campo `r` em `source` | 400 |
| RF-16 | KX3 | campo `origin` na raiz | 400 |
| RF-17 | KX4 | sem `suspect` | 400 |
| RF-18 | KX5 | `text: 12` | 400 |
| RF-19 | RSX1 | modelo ausente, `hybrid` | 503 `resource_unavailable`, sem índice fabricado |
| RF-20 | RSX1 (controle) | modelo ausente, `lexical` | 200, lexical calculado |
| RF-21 | RSX2 | entrada acima de 12.000 tokens de conteúdo | 503, "sem classificação" |
| RF-22 | AX1 | comparação sem sessão | redirecionamento ou 401 |
| RF-23 | AX2 | sessão expirada | redirecionamento ou 401 |
| RF-24 | AX3 | POST sem token CSRF | 403 |
| RF-25 | AX4 | B abre `/results/<id de A>` | 404 ou 403, sem vazamento |
| RF-26 | `/v1/extract` com campo extra no form | `file` + `foo` | 400 |

Regra geral da robusta fraca: nenhum caso inválido pode produzir índice, classe ou resultado persistido. Os 503 devem trazer o estado explícito, nunca zero.

Rastreio para testes existentes: vários casos já estão cobertos em parte (`tests/adapters/test_http.py`, `test_txt_decoding.py`, `test_docx_safety.py`, `contracts/requests.json`, `web/e2e/system.spec.ts` "arquivo incompatível e entrada vazia", `web/e2e/unavailable.spec.ts`). O trabalho é **mapear cada ID para um teste**, criar os faltantes e registrar a matriz em `11-testes.md`.

---

## 6. Plano de testes de regressão

Objetivo: garantir que nenhuma mudança (correção de CI, integração de modelos, Platt) altere silenciosamente resultados já verificados.

### 6.1 Suítes e gatilhos

| Suíte | Conteúdo | Quando rodar | Ambiente |
| --- | --- | --- | --- |
| RG-core | pytest `core/tests` (cerca de 314 funções de teste: domínio, adaptadores, contratos, dataset, treino) | Toda mudança no core; CI | Docker |
| RG-web | `npm test` (contratos, segurança S3) + `typecheck` | Toda mudança na web; CI | Docker |
| RG-contratos | `contracts/requests.json` e `responses.json` validados no core **e** na web | Toda mudança de schema | Docker |
| RG-golden | Valores de referência numéricos (S1/S2: 55 referências S1, 15 conferências S2) | Toda mudança em `domain/` | Docker |
| RG-identidades | Hashes do dataset (`fccdffc9…`), IDF de treino (`9ddb353e…`), anotações H1/H2, protocolo e modelo-base | Antes da S5B, antes da S5C e na S5D | Docker |
| RG-modelos (novo) | Recarga dos artefatos treinados + predições fixas | Após a S5B e a cada integração | Docker, CPU |
| RG-e2e | Playwright `system.spec.ts` e `unavailable.spec.ts` | Antes de cada entrega; CI | Docker |

### 6.2 Casos de regressão novos

| ID | Teste | Critério |
| --- | --- | --- |
| RG-01 | **Snapshot Q5-V2** antes da integração: índice, matrizes e classes dos 32 casos da normal forte gravados em JSON | Após a integração, com os modelos novos **desativados**, saída idêntica (tolerância 1e-9) |
| RG-02 | Modelos ativados não mudam o índice | `index.value` igual ao snapshot; os modelos novos aparecem só em campos próprios |
| RG-03 | Recarga do export H1 | Predições em 17 itens de validação idênticas às do fim do treino |
| RG-04 | Recarga do checkpoint H2 | Saídas em 13 itens de validação iguais até 1e-6 (CPU, mesmas threads) |
| RG-05 | Parâmetros de Platt | Probabilidades idênticas após a recarga (PL-08) |
| RG-06 | IDF da aplicação × IDF de treino | O app continua com o IDF próprio; nenhuma troca sem flag explícita |
| RG-07 | Guard do teste | Qualquer comando de treino ou calibração com `split=test` é recusado |
| RG-08 | Regressões históricas de parsing | Endereços, e-mails, versões, Type1 e BOM (testes da S1) continuam passando |
| RG-09 | Falha corrigida do CI | O teste que falhou no run 40261747702 passa a ter regressão própria |

### 6.3 Regras

- Uma falha de regressão **não** é resolvida atualizando o snapshot sem uma decisão registrada explicando por que a saída nova é a correta.
- Nada de skip, xfail ou continue-on-error em teste obrigatório.
- Cada execução registra commit, ambiente, comando e resultado em `11-testes.md`. Contagens de ambientes diferentes não são somadas.

---

## 7. Plano de testes end-to-end

Já existem (S3): o fluxo real de cadastro → arquivos → resultado → mapa → histórico → impressão → logout/login → isolamento de B; a paginação do mapa; o texto colado com HTML inerte; o arquivo incompatível e a entrada vazia; e a indisponibilidade real.

### 7.1 E2E funcionais novos

| ID | Cenário | Passos | Critério |
| --- | --- | --- | --- |
| E2E-01 | Formatos cruzados | Fonte DOCX × suspeito PDF com o mesmo conteúdo | Resultado igual ao de TXT × TXT (RG-01) |
| E2E-02 | Os 4 tipos de relação na interface | Pares R1–R4 da seção 5.3, modo híbrido | Classe exibida = esperada; explicação por sentença visível |
| E2E-03 | Modelo treinado ativo | Subir com a flag do modelo H1/H2 ativada | Interface mostra nome, versão e hash do modelo; índice inalterado (RG-02) |
| E2E-04 | Modelo treinado ausente | Flag ativa, artefato removido | Estado de indisponibilidade explícito, sem fallback silencioso |
| E2E-05 | Probabilidade de derivação (se P1 aprovado) | Par R2 | Rótulo "probabilidade de derivação", separado do índice |
| E2E-06 | Limites na interface | Colar 30.001 caracteres; enviar 5,1 MB | Mensagem de erro clara; nada no histórico |
| E2E-07 | Unicode | Pares em árabe e CJK | Texto exibido sem corrupção; sentenças no mapa |
| E2E-08 | Impressão do resultado com modelos ativos | Imprimir | Versão do modelo e data aparecem no impresso |
| E2E-09 | Reprodução S5D | Cópia limpa → `docker compose up` → seeds → E2E-01 a 08 | Tudo passa sem API paga nem recurso não documentado |

### 7.2 E2E de segurança (regressão da S3)

Repetir: usuários distintos, CSRF, expiração, logout, autorização das rotas e HTML inerte. Isso cobre AX1–AX4 da seção 5 pela interface.

### 7.3 E2E de desempenho — protocolo H3 (definir antes de medir)

| Item | Proposta |
| --- | --- |
| Hardware | Máquina identificada: CPU, RAM, SO, versão do Docker, limites do container |
| Configuração | Modelos ativos congelados (sem e com siamês, se integrado) |
| Entrada | Pares de 30 e de 120 sentenças (máximo do contrato), conteúdo de desenvolvimento |
| Carga | 1, 5 e 10 usuários simultâneos; aquecimento descartado. Três minutos por cenário, adotados em D6 antes da coleta, com duração, cadência, filas e limites registrados antes da coleta |
| Metas adotadas em D6 | p95 ≤ 2 s para 30 sentenças e ≤ 10 s para 120 sentenças, com 1/5 usuários. Dez usuários exploratório, sem meta. Resultados vinculados à máquina medida |
| Ferramenta | `web/scripts/load.ts` |
| Saídas | p50/p95/p99, número de amostras, erros/429/503, vazão, pico de RSS do core e limites/uso do contêiner |
| Critério H3 a congelar em D6 | Comparar latência das operações válidas às metas; reportar falhas e rejeições com denominadores. Respostas rápidas de erro não podem fundamentar aprovação. Resultados negativos permanecem no relatório |

---

## 8. Decisões vigentes e checklist final

D1=B; D2=encoder congelado/cabeça MLP r3/r4; D3=quatro logísticas e dois
baselines; D4=P1 derivação; D5=96 pares/dois humanos; D6=H3 predefinida.
Origem: autorização do autor; nenhuma ratificação específica do orientador presumida.
P2/P3 de calibração e regressão isotônica são alternativas históricas não
adotadas por D4/r3 (`isotonic=false`), não testes omitidos. A extensão Unicode
de 24 combinações é opcional; a matriz obrigatória tem 70 IDs e E2E-07.

- [x] D1–D6 registradas; r3/r4 com hashes e decisões anteriores ao fit/coleta
- [x] CI corrigido e verde no main publicado 3d26db5, run 40455735826
- [ ] Publicar manualmente a revisão local final e conferir o seu CI remoto
- [x] 70 IDs NF/NFo/RF mapeados/executados, faltantes implementados
- [x] Snapshot RG-01 anterior à integração,32 casos/34 testes, preservado
- [x] H1: quatro classificadores+dois baselines, exports e RL01–06
- [x] H2 r4: oito épocas/56 passos, checkpoint selecionado recarregado
- [x] Platt: validation/recarga/PL01–09; resultado negativo P1 reportado
- [x] Humanos: 96 IDs cada, κ H1 e Spearman H2, ambiguidades preservadas
- [x] Referência final congelada por hash antes da inferência
- [x] S5C uma única inferência, tabelas/recálculo exatos e claim preservado
- [x] Integração opt-in e E2E01–08, segurança/persistência/impressão
- [x] H3 medida nas 12 combinações, falhas e metas mantidas
- [x] S5D/E2E09 na cópia limpa, Core/Web/seeds/modelos/licenças/citação
- [x] TCC00–14/README coerentes, alcance parcial/exploratório e limites explícitos

Evidências: [matriz por ID](../TCC/evidencias/codex-p12-02/matriz-testes.md),
[partes P0–P12](../TCC/evidencias/codex-p12-02/matriz-execucao.md).
O item remoto da revisão final é ação manual do autor, não um CI afirmado pelo agente.

---

## 9. Guia de execução para agentes de IA

Esta seção é para um agente de código (Claude Code, Codex ou similar) executar o plano. Ela é autossuficiente: o agente deve conseguir trabalhar lendo só este arquivo e os indicados em 9.1. A identidade real do agente (produto, modelo e versão) é registrada em todo relatório.

### 9.1 Contexto obrigatório antes de começar

Ler, nesta ordem:

1. Este arquivo inteiro (seções 1–8).
2. `TCC/01-decisoes.md`: decisões vigentes e Q5-V2.
3. `TCC/02-metodologia.md`: H1–H3, seções e) a h), regras sobre alvo e features.
4. `TCC/14-pendencias.md`: bloco `S5B-CURRENT`.
5. Repositório `hybrid-text-similarity`: `README.md`, `core/configs/experiment_s5b.json`, `core/configs/comparison.json`, `core/src/hts_core/application/comparison.py`, `core/src/hts_core/application/controlled_training.py`.

Registrar no início do relatório: branch, HEAD, `git status` e alterações locais não publicadas.

### 9.2 Regras invioláveis

| Regra | Motivo |
| --- | --- |
| Não abrir o split `test` (predição, anotação, seleção, calibração) sem a autorização da S5C registrada | Evita vazamento; a validade de H1/H2 depende disso |
| Não mudar o protocolo S5B revisão 2 sem uma revisão 3 aprovada (D1–D4) | Mudança silenciosa de hipótese invalida o TCC |
| Não usar `r`, classe C0–C7, origem, id de fonte ou tipo de transformação como feature | Regra da metodologia; a proveniência só serve como alvo de derivação |
| Não converter probabilidade de classe em índice | O índice do app continua sendo a fusão fixa |
| Testes e trabalho experimental só em Docker; o host apenas invoca o Docker | Reprodutibilidade |
| CPU por padrão; não ativar GPU automaticamente | Protocolo vigente |
| Não fazer commit, push, PR ou publicação; não apagar volumes, evidências ou artefatos | O autor publica manualmente |
| Não usar APIs pagas; não inventar parâmetros, resultados, aprovações ou pessoas | Integridade |
| Nada de skip, xfail ou continue-on-error em teste obrigatório | A seção 6.3 vale para o agente |
| Gatilhos do CI: push só em `main`; pull_request para `main` só `opened`. Não alterar | Decisão registrada |
| Toda falha e toda tentativa são preservadas e relatadas | Rastreabilidade |
| Parar e perguntar quando a tarefa depender de uma decisão D1–D6 ainda não registrada | Essas decisões são humanas |

### 9.3 Comandos de referência

Executados na raiz do repositório:

```bash
# Build e recursos (como no CI)
docker compose -f docker-compose.ci.yml build core web browser
docker compose -f docker-compose.ci.yml run --rm --no-deps prepare python -m hts_core.cli restaurar-corpus
docker compose -f docker-compose.ci.yml run --rm --no-deps prepare python scripts/prepare_model.py
docker compose -f docker-compose.ci.yml run --rm --no-deps prepare python scripts/gerar_fixtures_ci.py --out /fixtures

# Suíte do core
docker compose -f docker-compose.ci.yml run --rm --no-deps core python -m pytest -q --junitxml=/results/core.xml

# Stack e suítes web
docker compose -f docker-compose.ci.yml up -d --wait --wait-timeout 180 mongo core web
docker compose -f docker-compose.ci.yml exec -T web npm test
docker compose -f docker-compose.ci.yml exec -T web npm run typecheck
docker compose -f docker-compose.ci.yml exec -T web npm run integration
docker compose -f docker-compose.ci.yml run --rm --no-deps browser npm run test:e2e

# Treino S5B (somente train/validation)
python -m hts_core.cli.training readiness --task H1 --protocol ... --reference ... --dataset ... --idf ... --annotations ... --campaign ... --out ...
python -m hts_core.cli.training run       --task H1 (mesmos argumentos)
# Execução em Docker: core/scripts/run_s5b_docker.py com docker-compose.s5b.yml
```

Confirmar os caminhos dos argumentos no handoff mais recente (`evidencias/codex-s5b-*/handoff-*.json`) antes de executar; não deduzir.

### 9.4 Partes de execução em sequência

O trabalho é dividido em **13 partes (P0–P12)** e **2 portões humanos (PH1, PH2)**, que são pontos de parada em que só o autor e o orientador decidem. Cada parte tem sempre as mesmas quatro etapas, nesta ordem:

| Etapa | O que é | Regra |
| --- | --- | --- |
| **E — Execução** | Implementar ou rodar o que a parte pede | Só em Docker; nada fora do escopo da parte |
| **T — Teste** | Rodar os testes novos e as suítes de regressão afetadas | Toda falha preservada; nada de skip ou xfail |
| **V — Validação** | Conferir os critérios de aceite, as identidades e as regras da 9.2 | Critério não atendido → a parte não termina; volta para E com uma nova tentativa |
| **G — Gravação** | Gravar a evidência (9.5) e atualizar os arquivos do TCC indicados | Só números copiados da saída real |

Uma parte só começa quando a anterior terminou sua etapa G. Exceção: as partes marcadas "paralela".

```text
P0 → P1 (paralela) ─┐
P0 → P2 → P3 ───────┴→ [PH1: decisões D1–D4] → P4 → P5 → P6 → P7 → P8
     → [PH2: autorização S5C] → P9 → P10 → P11 → P12
```

#### P0 — Preparação e inventário

| Etapa | Conteúdo |
| --- | --- |
| E | Registrar branch, HEAD, `git status` e alterações locais. Ler o contexto da 9.1. Subir Mongo, core e web (comandos 9.3) |
| T | `GET /v1/health` do core; página inicial da web responde; ping do Mongo |
| V | Conferir os hashes: dataset `fccdffc9…`, IDF `9ddb353e…`, anotações H1 `980fcd18…`, H2 `46448d91…`, protocolo revisão 2 `1bc0736e…`, modelo-base `e8f8c211…`. Qualquer divergência → parar e relatar |
| G | `evidencias/<agente>-p00-01/`: `ambiente.json`, `hashes.json`, relatório de inventário |

#### P1 — Correção do CI (paralela a P2–P3)

| Etapa | Conteúdo |
| --- | --- |
| E | Reproduzir a suíte do core em Docker; identificar o teste que falha no run 40261747702; corrigir a causa; renomear a etapa "Validate S4" |
| T | Suíte do core completa; web `npm test` e `typecheck`; `integration`; E2E `test:e2e` e `test:unavailable`; regressão RG-09 nova |
| V | Todas verdes localmente; diff do workflow sem mudança de gatilhos; nenhum skip, xfail ou continue-on-error adicionado |
| G | Evidência p01; registro em `TCC/11-testes.md` ("local, Docker", sem chamar de CI remoto); item do checklist 8 marcado só depois de o autor publicar e o CI remoto passar |

#### P2 — Testes por classes de equivalência

| Etapa | Conteúdo |
| --- | --- |
| E | Criar as fixtures R1–R4 escritas à mão em `core/tests/fixtures/equivalence/` e convertê-las para TXT, DOCX e PDF. Implementar `core/tests/adapters/test_equivalence_classes.py` (NF-01–12, NFo-01–32, RF-01–21, RF-26) e `web/e2e/equivalence.spec.ts` (RF-22–25) |
| T | Rodar os 70 casos (12 normal fraca, 32 normal forte, 26 robusta fraca) + a suíte do core inteira |
| V | Cada ID da seção 5 tem um teste ou uma justificativa; o caso falhou → é defeito do sistema (registrar) ou erro do esperado (corrigir com justificativa). Nenhum par do dataset de pesquisa nas fixtures |
| G | Evidência p02 com a matriz "ID → arquivo::teste → resultado"; matriz anexada a `TCC/11-testes.md`; defeitos encontrados listados em `TCC/14-pendencias.md` |

#### P3 — Snapshot de regressão (RG-01)

| Etapa | Conteúdo |
| --- | --- |
| E | Gerar `core/tests/fixtures/regression/q5v2-snapshot.json` com índice, matrizes e classes dos 32 casos NFo, mais commit e hashes do modelo e do IDF; criar o teste de comparação |
| T | O teste do snapshot passa no HEAD atual; rodar duas vezes seguidas e obter saída idêntica |
| V | O snapshot registra como foi gerado; tolerância numérica 1e-9 documentada |
| G | Evidência p03 com o hash do snapshot; registro em `TCC/11-testes.md` |

#### PH1 — Portão humano: decisões

O agente **para** aqui. O autor e o orientador registram D1–D4 em `TCC/01-decisoes.md`: caminho, variante do siamês, sistemas da H1 e uso de Platt. O agente pode preparar um resumo das opções, sem decidir.

#### P4 — Revisão 3 do protocolo

| Etapa | Conteúdo |
| --- | --- |
| E | Criar `core/configs/experiment_s5b.r3.json` com as decisões de PH1; atualizar `experiment_s5b.schema.json` e `adapters/training_contract.py` |
| T | Contrato: a revisão 2 continua válida; a revisão 3 valida; controles negativos (campo inválido, split `test`, feature proibida) são recusados |
| V | Cada mudança da revisão 3 aponta para a decisão D correspondente; nenhuma mudança extra |
| G | Evidência p04 com o hash da revisão 3; o autor registra o hash em `01-decisoes.md` |

#### P5 — Implementação da H1 e do Platt

| Etapa | Conteúdo |
| --- | --- |
| E | `training_classifiers.py`: N features e export `hts-logistic-2`; sistemas `learned_fusion`, `baseline_q5v2`, `baseline_majority`. Novos `domain/calibration.py` e `application/calibration.py` (Platt com alvos regularizados, Brier, log-loss, ECE) |
| T | RL-01 a RL-06 e PL-01 a PL-08 com fixtures; suíte do core; snapshot RG-01 |
| V | Mesmos itens elegíveis para todos os sistemas; o guard recusa `split=test`; nenhuma feature proibida aceita; RG-01 inalterado |
| G | Evidência p05; testes novos registrados em `TCC/11-testes.md` |

#### P6 — Implementação da H2 revisada

| Etapa | Conteúdo |
| --- | --- |
| E | `trainable_siamese.py` e `training_runtime.py` na variante de D2: (a) cosseno com embeddings congeladas ou (b) encoder congelado com a cabeça treinável |
| T | Teste de fixture: gradientes só nos parâmetros previstos; contagem de parâmetros treináveis; um passo de treino em fixture reduz a perda; salvar e recarregar o checkpoint de fixture (RG-04 em fixture) |
| V | **Medir** o pico de RSS de um treino de fixture e propor a reserva de readiness com base nessa medida (a reserva só muda com a aprovação do autor) |
| G | Evidência p06 com o RSS medido e os parâmetros treináveis; registro em `TCC/11-testes.md`; proposta de reserva em `TCC/14-pendencias.md` |

#### P7 — Execução real da H1

| Etapa | Conteúdo |
| --- | --- |
| E | Readiness da H1 com a revisão 3; se liberado, `run --task H1` em Docker; ajustar os 6 sistemas e o Platt P1/P2 na validação |
| T | Recarregar os exports e repetir as predições da validação (RG-03); recarregar os parâmetros de Platt (RG-05) |
| V | Identidades de entrada iguais às de P0; macro-F1 de validação, matriz de confusão e F1 por classe de todos os sistemas presentes; nenhuma predição ausente; teste não tocado |
| G | Evidência p07 com modelos, logs, métricas e hashes; registro em `TCC/12-experimentos.md` como "S5B H1, validação, exploratório" |

#### P8 — Execução real da H2

| Etapa | Conteúdo |
| --- | --- |
| E | Readiness da H2; se liberado, `run --task H2` dentro do orçamento; seleção pela menor MSE de validação |
| T | Recarregar o checkpoint selecionado e repetir as saídas da validação (RG-04, tolerância 1e-6) |
| V | Spearman de validação do siamês e do SBERT no mesmo conjunto; histórico de épocas completo; parada (orçamento, paciência ou fim) registrada; teste não tocado |
| G | Evidência p08; registro em `TCC/12-experimentos.md`; handoff para a S5C com a lista de artefatos e hashes |

#### PH2 — Portão humano: autorização da S5C

O agente **para** aqui. O autor confere P7–P8 e registra a autorização da S5C, incluindo se haverá anotação humana (D5). Se houver, a anotação é feita por humanos fora do agente e entregue com hash.

#### P9 — Referência final e runner da S5C

| Etapa | Conteúdo |
| --- | --- |
| E | Preparar a referência final com `scripts/prepare_s5c_reference.py`; importar a anotação humana, se houver; implementar `application/final_evaluation.py` e `hts experiment evaluate` |
| T | Runner em um dataset de fixture; o guard recusa execução sem a referência congelada e o hash de autorização; os indefinidos saem como null com motivo |
| V | Referência congelada com hash **antes** de qualquer predição; κ (H1) e ICC ou Spearman entre anotadores (H2) calculados, se houver anotação humana; modelos, IDF e configurações congelados |
| G | Evidência p09 com o hash da referência e a concordância; registro em `TCC/12-experimentos.md` |

#### P10 — Avaliação final (execução única no teste)

| Etapa | Conteúdo |
| --- | --- |
| E | Rodar `hts experiment evaluate` **uma vez** no teste com os artefatos congelados |
| T | Conferir que o arquivo de predições tem uma linha por item elegível e que as métricas recalculadas a partir das predições batem com as reportadas |
| V | Nenhum parâmetro, checkpoint ou exemplo escolhido depois da execução; desagregações por transformação, severidade e formato presentes; alcance declarado (exploratório ou com referência humana parcial) |
| G | Evidência p10; tabelas geradas por script e coladas em `TCC/13-resultados.md`, cada uma com o caminho da execução de origem; veredito de H1 e H2 em `TCC/12-experimentos.md`, sem reformular hipótese |

#### P11 — Integração no app e H3

| Etapa | Conteúdo |
| --- | --- |
| E | Bloco `models` em `comparison.json` (`enabled=false` por padrão), loaders, campos novos em `schemas.py` e `contracts/*.json`, exibição em `result.tsx`. Depois, a H3 com `web/scripts/load.ts`, conforme a seção 7.3 (só com a meta X de D6 registrada) |
| T | RG-01 e RG-02; E2E-01 a E2E-08; segurança da S3; PL-09; a carga em cada nível |
| V | Com a flag desligada, resposta idêntica ao snapshot; com a flag ligada, o índice continua igual e os modelos aparecem em campos próprios; p95 comparado à meta X |
| G | Evidência p11; testes em `TCC/11-testes.md`; resultado da H3 em `TCC/12-experimentos.md` e `TCC/13-resultados.md` |

#### P12 — Reprodução S5D e fechamento

| Etapa | Conteúdo |
| --- | --- |
| E | Fazer uma cópia limpa em diretório novo; seguir só o README; restaurar pacotes, subir os serviços e carregar os seeds |
| T | E2E-09; suítes do core e da web; recarga de todos os modelos |
| V | Nenhum passo exige API paga ou recurso não documentado; README e TCC/00–14 descrevem o mesmo estado; licenças e atribuições presentes |
| G | Evidência p12; `TCC/00-indice.md` e o checklist da seção 8 atualizados; `CITATION.cff`, se aplicável |

### 9.5 Formato da gravação (etapa G de cada parte)

Cada parte termina com uma pasta `TCC/evidencias/<agente>-p<nn>-<tentativa>/` (por exemplo, `claude-p07-01/`). Uma nova tentativa cria uma pasta nova; as anteriores nunca são apagadas. Conteúdo:

| Arquivo | Conteúdo |
| --- | --- |
| `relatorio.md` | Objetivo, o que foi feito, decisões usadas (com referência), comandos, resultados reais copiados da saída, falhas e pendências |
| `comandos.txt` | Comandos exatos na ordem executada |
| `ambiente.json` | Agente e modelo, SO, CPU, RAM, Docker, commit, alterações locais |
| `testes.json` | Suítes, contagens, exit codes, por ambiente |
| `hashes.json` | SHA-256 dos artefatos produzidos e das entradas usadas |
| `handoff.json` | Estado final (`concluida`, `falhou` ou `bloqueada`), o que a próxima parte precisa, bloqueios |
| `validacao.md` | Cada critério da etapa V com atendido/não atendido e a evidência |

Depois de cada parte, atualizar os arquivos do TCC indicados na etapa G e o checklist da seção 8 deste arquivo, marcando só o que tiver evidência.

### 9.6 Modelo de instrução para iniciar um agente

```text
Você vai executar a parte <Pnn> do arquivo TCC/16-plano-conclusao-e-testes.md,
nas etapas E → T → V → G, nesta ordem.
Leia o arquivo inteiro e os documentos da seção 9.1 antes de qualquer alteração.
Siga as regras da seção 9.2 sem exceção. Se a tarefa depender de uma decisão
D1–D6 não registrada em TCC/01-decisoes.md, pare e pergunte.
Repositório: <caminho>. Branch: <branch>. Não faça commit nem push.
Confirme que a parte anterior tem handoff com estado "concluida".
Se parar em um portão (PH1, PH2) ou em uma decisão não registrada, pare e pergunte.
Grave conforme a seção 9.5 em TCC/evidencias/<agente>-p<nn>-<tentativa>/.
A parte só termina com todos os critérios da etapa V atendidos.
```

---

Fontes: `TCC_Documentacao_Geral_Sessoes_2026-10-26.docx`; `01-decisoes.md` (decisões 4–8, Q5-V2); `02-metodologia.md` (H1–H3, seções f–h); `11-testes.md`; `14-pendencias.md`; `evidencias/codex-s5b-pos-travamento-01/proposta-recursos.md`; repositório: `core/configs/{experiment_s5b,comparison}.json`, `core/src/hts_core/adapters/{http,schemas,training_classifiers,trainable_siamese,semantic}.py`, `core/src/hts_core/application/comparison.py`, `core/src/hts_core/adapters/parsers/txt_parser.py`, `contracts/*.json`, `web/e2e/*.spec.ts`, `web/package.json`. Platt (1999), "Probabilistic Outputs for Support Vector Machines"; Jorgensen, *Software Testing: A Craftsman's Approach*, cap. de teste por classes de equivalência.
