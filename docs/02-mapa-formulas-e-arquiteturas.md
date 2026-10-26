# TCC — Mapa de fórmulas e arquiteturas dos 9 artigos

Oct 21, 2026 · @Luiz

## Nota vigente — integração documental de 2026-10-24

Este mapa é índice auxiliar. Afirmações históricas de leitura/OCR abaixo são registros anteriores, não novas execuções comprovadas por esta edição. Fonte científica: PDF original; escopo: decisão explícita do autor. Conflitos e dados ausentes permanecem identificados, sem ajustar esperado/tolerância para passar. Publicado, recálculo independente, decisão/proposta, resultado executado e não verificado são categorias separadas.

A6/91,7% permanece exercício aritmético, sem reconstruir a acurácia geral. OSA é a variante atual, não confirmação da irrestrita no A4. E2 top-k/TF-IDF/blake2b é adaptação, não reprodução Textract/IQ; hash igual não prova identidade nem seu inteiro fornece escore 0–1. O índice simétrico do projeto não equivale por definição a r direcional. Contrato científico e escolhas pendentes em TCC/02; nenhuma nova hipótese foi validada.

## Como ler este documento

Os 9 artigos foram lidos duas vezes: pelas imagens das páginas (equações, figuras de arquitetura, tabelas) e pelo texto extraído, e cada número que dá para recalcular foi recalculado. Onde a extração de texto do PDF corrompeu uma fórmula, vale a versão da imagem.

Marcações usadas:

- **\[ERRO NO ARTIGO\]** — o próprio artigo está errado ou inconsistente; não copiar para o TCC sem corrigir.
- **\[NÃO DEFINIDO NO ARTIGO\]** — o artigo usa algo sem defini-lo; a forma padrão da literatura vem indicada como complemento.
- **\[RECALCULADO\]** — conferi o número a partir dos dados do próprio artigo. Rótulos mais brandos, quando não é erro: \[LIMITAÇÃO\] (fraqueza de método), \[SIMPLIFICAÇÃO\] (forma resumida, correta), \[IMPRECISÃO\] (frase solta, número certo), \[AMBÍGUO NO ARTIGO\] (não dá para saber o que o autor quis), \[FRAGILIDADE\] (conclusão maior que a evidência) e \[CORRIGIDO\] (afirmação minha que estava errada e foi desfeita).

| # | Artigo | Ano / veículo | Técnica central | Tarefa |
| --- | --- | --- | --- | --- |
| 1 | Sarkar, Sarkar, Ansar, Chakrabarti | 2024, EasyChair Preprint nº 15448 | BERT + rede Siamesa (regressão) | Similaridade de resumos (ACL) |
| 2 | Gawade et al. | 2025, ICSSSM (AISR 201), pp. 344–355 | TF-IDF + SBERT, cosseno, pesos 0,4/0,6 | Detecção de plágio por sentença |
| 3 | Henderson, Merkhofer, Strickhart, Zarrella (MITRE) | 2017, SemEval Task 1, pp. 185–190 | Ensemble de 5 sistemas + alinhamento | STS multilíngue |
| 4 | Afzal, Wang, Liu (MayoNLP) | 2016, SemEval, pp. 674–679 | WordNet + corpus (Li et al.) e DSSM | STS em inglês |
| 5 | Poljak, Crčić, Horvat | 2025, Elektrotehniški Vestnik 92(3), pp. 151–156 | 7 algoritmos léxicos/vetoriais | Comparação de algoritmos + app web |
| 6 | Halim, Lasut | 2024, Bit-Tech 7(2), pp. 202–213 | TF-IDF + cosseno | App web de plágio (indonésio) |
| 7 | Lubis, Lubis, Wahidah | 2026, Sinkron 10(2), pp. 1060–1069 | Sentence-BERT + FAISS (IndexFlatL2) | Busca semântica em repositório |
| 8 | Cooper, Coden, Brown (IBM) | 2002, CIKM, pp. 245–251 | Termos salientes (Textract/IQ) vs. shingles | Documentos similares/duplicados |
| 9 | Setu, Islam, Erfan, Dey, Al Asif, Samsuddoha | 2025, J. Umm Al-Qura Univ. Eng. Archit. 16:310–325 | TF-IDF/cosseno + BERT + busca online | Plágio direto, paráfrase e online |

## Artigo 1 — Sarkar et al. (2024): Siamese BERT para resumos científicos

Modelo Siamês sobre embeddings BERT que regride um escore de similaridade entre dois resumos (escala não informada; o MSE de 0,0010 indica algo como 0–1), treinado com MSE em 10.072 pares do ACL Anthology, chegando a Pearson 0,8706.

### Dataset (Seção 3.2)

- Fonte: ACL Anthology Corpus no HuggingFace (`WINGNUS/ACL-OCL`).
- 10.072 resumos; campos mantidos: `acl_id`, `abstract` (renomeado `original`), `corpus_paper_id`, `url`, `numcitedby`, `title`, `year`.
- Coluna `paraphrased` gerada pelo **gemini-pro**; alvo `similarity_score` também atribuído pelo **gemini-pro** comparando original × parafraseado.
- Pré-processamento: tratar ausentes em `abstract`, remover duplicatas, corrigir erros/inconsistências.

### Arquitetura (Fig. 1, lida da imagem)

1. Entradas: `Original` e `Similar` (ou dissimilar).
2. BERT Tokenizer (compartilhado).
3. Por ramo: Model Transformer (BERT) → Pooling (média ou máximo dos embeddings de tokens).
4. Por ramo: Sentence Transformer.
5. Bloco denso (caixa tracejada única na figura): Dense Layer 1 → Normalization (LayerNorm) → Leaky ReLU → Dropout → Dense Layer 2 → Normalization → Leaky ReLU → Dropout.
6. Concat dos dois ramos.
7. Dense Layer 3 → Output (Q) = escore de similaridade.

A figura não deixa claro se as duas metades do bloco denso são um ramo por entrada ou camadas compartilhadas (pesos Siameses). Para o TCC, descrever como "ramos com pesos compartilhados" só se você implementar assim.

### Fórmulas

Camada linear (Eq. 1):

```latex
y = xA^{T} + b
```

LayerNorm (Eq. 2), μ = média, σ² = variância, ε = constante de estabilidade:

```latex
\hat{x}_i = \frac{x_i - \mu}{\sqrt{\sigma^2 + \epsilon}}
```

Leaky ReLU (Eq. 3), α pequeno positivo:

```latex
f(x) = \begin{cases} x, & x \ge 0 \\ \alpha x, & x < 0 \end{cases}
```

Dropout (Eq. 4), p = probabilidade de manter a unidade:

```latex
\mathrm{Dropout}(x) = x \cdot \mathrm{Bernoulli}(p)
```

MSE e MAE (Seção 5):

```latex
\mathrm{MSE} = \frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2 \qquad \mathrm{MAE} = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|
```

### Hiperparâmetros e ambiente (Tabela 1, Seção 4)

| Parâmetro | Valor |
| --- | --- |
| Épocas | 8 |
| Learning rate | 2e-6 |
| Otimizador | Adam |
| Max length (tokens) | 212 |
| Weight decay | 1e-5 |
| Loss | MSELoss |
| GPU | P100 |

Máquinas de desenvolvimento: Asus Vivobook 16 (16 GB, Ryzen 7 5800HS) e Asus F Dash 15 (16 GB, Intel i5 12500H). "Application Developed in": Next.js, Node.js, TypeScript, Tailwind CSS. App: Next.js (front, autenticação) → Flask (similaridade) → MongoDB (detalhes e embeddings) com cosseno na busca; entrada por texto ou imagem do resumo (transcrita). Dependências: Flask, numpy, pandas, google-generativeai, pymongo, sentence\_transformers, torch, tqdm, transformers, bert\_score, datasets, scipy, scikit-learn.

### Resultados (Tabelas 2 e 3)

| Métrica de teste | Valor |
| --- | --- |
| Avg. Test Loss | 0,0010 |
| MAE | 0,0209 |
| MSE | 0,0010 |
| R² | 0,7067 |
| Pearson | 0,8706 |
| Spearman | 0,6564 |
| Tempo de teste | 23 s |

| Par de exemplo (Tabela 3) | Cosseno | BERTScore | Proposto |
| --- | --- | --- | --- |
| eSports × futebol (dissimilares) | 81,71 | 39,03 | 31,05 |
| Textos idênticos | 100 | 99,5 | 100 |
| Aquisição em larga escala × similaridade semântica | 95,48 | 84,63 | 90,12 |

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** A Seção 5 atribui o desempenho a um modelo "encoder-decoder" voltado a tradução; BERT é só encoder e a tarefa não é tradução.
- **\[SIMPLIFICAÇÃO\]** Dropout escrito sem o fator de escala 1/p usado no treino (inverted dropout) e LayerNorm sem os parâmetros aprendíveis γ e β. Não é erro, é a forma resumida; no código, usar as camadas padrão (nn.Dropout, nn.LayerNorm), que já incluem isso.
- **\[LIMITAÇÃO\]** Rótulos e paráfrases vêm do mesmo LLM (gemini-pro): o modelo aprende a imitar o Gemini, não julgamento humano. Citar como limitação.
- **\[ERRO NO ARTIGO\]** A organização diz "Section 6" duas vezes (Discussão e Conclusão); a Seção 4 descreve a busca da app por cosseno, não pela rede Siamesa.
- MSE 0,0010 com R² 0,7067 implica variância dos rótulos ≈ 0,0034: os escores do Gemini estão muito concentrados, o que relativiza o MAE baixo.
- Na 3ª linha da Tabela 3 o par é de dois resumos diferentes da área de NLP (não é paráfrase); o texto o chama de "closely related" e diz que o modelo teve o maior valor, mas o cosseno (95,48) supera o modelo (90,12).

## Artigo 2 — Gawade et al. (2025): plágio semântico com TF-IDF + SBERT

Sistema híbrido que compara cada sentença por cosseno em TF-IDF e em SBERT, classifica em Cópia Exata / Paráfrase / Original e combina 60% SBERT + 40% TF-IDF, com acurácia geral de 92% em 200 pares.

### Pipeline (Fig. 1)

1. Upload Documents
2. Text Cleaning
3. Ramos paralelos: TF-IDF e SBERT
4. Cosine Similarity
5. Plagiarism Report

### Arquitetura do sistema (Fig. 2, lida da imagem)

- **Backend:** Document Input → Preprocessing → {TF-IDF Calculation, SBERT Similarity Calculation} → Similarity Results → Classification → Classified Output.
- **Database:** Store Classified Document → Retrieve Document for Frontend.
- **Frontend:** User Interface → Display Results; a UI envia "New Document Submission" de volta ao Document Input.
- Stack: Flask, HTML/CSS, JavaScript, Bootstrap, SQLite (autenticação e histórico); NLTK ou spaCy para segmentar sentenças. O modelo SBERT exato não é informado.

### Pré-processamento (Seção 3.1)

Minúsculas; remoção de espaços extras, stopwords e pontuação; tokenização de sentenças (nltk ou spaCy).

### Fórmulas e regras

Cosseno entre vetores de sentença (TF-IDF e SBERT, usada nos dois ramos; o artigo não escreve a equação, forma padrão):

```latex
\cos(A,B) = \frac{A \cdot B}{\|A\|\,\|B\|}
```

Regra de classificação por sentença (Seções 3.4 e 4.1):

```latex
\text{classe} = \begin{cases} \text{Cópia Exata}, & \cos_{TFIDF} > 0{,}85 \\ \text{Paráfrase}, & \cos_{SBERT} > 0{,}75 \ \text{e}\ \cos_{TFIDF}\ \text{baixo} \\ \text{Original}, & \text{caso contrário} \end{cases}
```

Escore final ponderado (Seção 3.5):

```latex
S = 0{,}6\cdot \cos_{SBERT} + 0{,}4\cdot \cos_{TFIDF}
```

Limiares estimados em teste piloto com 50 pares e ajustados por curva ROC. "TF-IDF baixo" não tem valor numérico definido **\[NÃO DEFINIDO NO ARTIGO\]**.

Métricas (Seção 4.5):

```latex
P = \frac{TP}{TP+FP} \quad R = \frac{TP}{TP+FN} \quad F_1 = \frac{2PR}{P+R} \quad Acc = \frac{TP+TN}{TP+FP+TN+FN}
```

### Dataset e resultados

200 pares rotulados manualmente: 70 cópia exata, 80 paráfrase, 50 original (estudantes, artigos públicos, recursos online).

| Classe | Precisão | Recall | F1 | Acurácia |
| --- | --- | --- | --- | --- |
| Exact Copy | 0,95 | 0,93 | 0,94 | 95% |
| Paraphrased | 0,87 | 0,84 | 0,85 | 88% |
| Original | 0,92 | 0,94 | 0,93 | 93% |

Acurácia geral 92%; ROC com AUC = 1,00 (Fig. 3). Exemplo de saída por sentença: 92,3% (Exata), 80,6% (Paráfrase), 23,4% (Original); UI com escore geral 22,86% e top-3 documentos.

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** Define F1 como "a média" de P e R, mas a fórmula escrita é a média harmônica. Use "média harmônica".
- **\[ERRO NO ARTIGO\]** A Seção 4.7 diz que a ablação (só TF-IDF, só SBERT, híbrido) está na Tabela 2, mas a Tabela 2 só traz o híbrido; não há números de ablação publicados.
- **\[ERRO NO ARTIGO\]** Texto da Seção 3.4 diz que a Fig. 3 mostra acurácia × limiar; a figura é uma curva ROC. AUC = 1,00 em 200 pares, com a mesma base usada para ajustar limiares, sugere sobreajuste.
- **\[ERRO NO ARTIGO\]** "200 academic papers" e logo depois "each pair": não fica claro se são 200 documentos ou 200 pares.
- **\[ERRO NO ARTIGO\]** A numeração da revisão não bate com a lista de referências (ex.: "Ivanov et al. \[13\]" é Kuksa & Polyakov; "Kumar et al. \[3\]" é Raja Subramanian; "Sharma et al. \[2\]" é Kumar et al.). Cite pelas referências, não pelo texto.

## Artigo 3 — Henderson et al. (2017): MITRE no SemEval-2017 Task 1

Ensemble de 5 preditores de similaridade combinados por regressão logística L2, com tudo traduzido para inglês; escore oficial 0,6590 (corrigido 0,6687), 3º lugar após correção.

### Tarefa e dados

- STS: escore 0–5 por par; avaliação por correlação de Pearson com humanos.
- Teste: 1.750 pares em 6 trilhas (AR-AR, AR-EN, ES-ES, ES-EN, EN-EN, TR-EN), majoritariamente legendas de imagem do SNLI (frases médias de 8,7 palavras, nota média 2,3 na trilha EN-EN).
- Treino: 6.898 pares (news + captions) de 2012–2014 e 2016; dev 400 e tuning 350 legendas de 2015. Não usaram dados fora do gênero nem o treino multilíngue de 2017.

### Recursos compartilhados

- word2vec skip-gram, dimensão 256, Wikipedia em inglês, 630.902 itens com frequência ≥ 100, janela 10, 15 amostras negativas; word2phrase aplicado 2× (frases de até 4 palavras).
- Tradução automática via Google Translate API (jan/2017). Justificativa: LM pequeno teve perplexidade 18,9 no SNLI contra 114,5 no Penn Treebank.
- Stanford Parser, modelo PCFG inglês com dependências básicas (um arco por token).

### Fórmulas de alinhamento (Seção 3.4)

Similaridade entre palavras (desloca o cosseno para \[0, 2\]):

```latex
sim(w_i, w_j) = 1 + \cos(w_i, w_j)
```

- **Min alignment:** maximiza a soma de sim sobre pares alinhados, cada palavra alinhada no máximo uma vez.
- **Max alignment:** toda palavra pareada com pelo menos uma outra; total de arestas ≤ nº de palavras da frase mais longa.
- Ambos resolvidos como programa linear com LPSOLVE.

Similaridade entre arcos de dependência a: head → dep (peso 10 no dependente):

```latex
sim(a_1, a_2) = sim(head(a_1), head(a_2)) + 10\, sim(dep(a_1), dep(a_2))
```

### Componentes do ensemble (Seção 3.5)

| Componente | O que é | Configuração |
| --- | --- | --- |
| TakeLab | SVR sobre n-gram overlap e similaridade de palavras | LIBSVM, kernel RBF, C = 20, γ = 0,2, ε = 0,5 |
| CRNNs-8 | RNN de 16 dim sobre pares alinhados + 3 CRNNs (256 filtros conv 1D, dropout 50%, LSTM 128) | Concatenação 400 dim (16 + 128×3) → LSTM 128 → 1 saída sigmoide; sequência 60; Adam; perda MAE; embeddings congelados; ensemble de 8 inicializações |
| Paris | 22 métricas de string (BLEU, WER, WER-g, ROUGE, PER, global/local, P/R de substrings) | 22 × (case-folded/original) × (palavra/caractere) = 88; ida e volta = 176; + log(x) = 352 features; LIBLINEAR, regressão logística L1 |
| Simple Alignment Measures | 16 features derivadas do alinhamento | Regressão logística L2 |
| EBIM | Enhanced BiLSTM Inference Model (Chen et al., 2016) | BiLSTM + atenção sem parâmetros (alinhamento suave) + LSTM de inferência + 2 camadas densas; saída de regressão com MSE; word2vec congelado; sem dropout na camada de embedding |

As três CRNNs recebem, por par alinhado: os embeddings das palavras, a diferença ao quadrado dos embeddings, e os embeddings das palavras-pai no parse. Feature extra binária: mesmo tipo de dependência.

Combinação final (Seção 3.6): pesos por regressão logística L2 sobre as saídas dos 5 preditores.

### Resultados (Tabelas 1 e 2)

| Trilha | Oficial | Corrigido |
| --- | --- | --- |
| Primary (média) | 0,6590 | 0,6687 |
| 1 AR-AR | 0,7294 | 0,7294 |
| 2 AR-EN | 0,6753 | 0,6753 |
| 3 ES-ES | 0,8202 | 0,8202 |
| 4a ES-EN | 0,7802 | 0,7802 |
| 4b ES-EN news | 0,1598 | 0,1598 |
| 5 EN-EN | 0,8053 | 0,8329 |
| 6 TR-EN | 0,6430 | 0,6831 |

| Componente | Isolado dev | Isolado test | Ensemble sem ele (dev) | Ensemble sem ele (test) |
| --- | --- | --- | --- | --- |
| TakeLab | 0,8724 | 0,6503 | 0,8739 | 0,6454 |
| CRNNs-8 | 0,8621 | 0,6379 | 0,8846 | 0,6551 |
| Paris | 0,8074 | 0,5524 | 0,8891 | 0,6666 |
| EBIM | 0,7742 | 0,4760 | 0,8886 | 0,6687 |
| Align | 0,7607 | 0,5037 | 0,8910 | 0,6722 |
| Todos | — | — | 0,8900 | 0,6687 |

CRNN individual no teste: 0,605 a 0,636; ensemble das 8: 0,638. TakeLab sozinho ficaria em 4º de 17 na trilha primária (31 equipes no total).

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** O resumo diz "linear regression" para unir os sistemas; a Seção 3.6 diz regressão logística L2.
- **\[AMBÍGUO NO ARTIGO\]** A conclusão cita ganho de 0,650 para 0,672 sem dizer de onde vêm. Pela Tabela 2, 0,650 é o TakeLab isolado (0,6503) e 0,672 é o ensemble sem o Align (0,6722), não o sistema submetido (0,6687).
- "Mean average error" na Seção 3.5 deve ser lido como mean absolute error (MAE).
- O próprio artigo admite que o Align deveria ter sido removido (o ensemble melhora sem ele).

## Artigo 4 — Afzal, Wang, Liu (2016): MayoNLP no SemEval-2016 Task 1

Dois sistemas de STS (rede semântica WordNet + corpus, e DSSM) e sua média 50/50; a média venceu na média ponderada de 2016 (0,75607) e de 2015 (0,7719).

### Pré-processamento (Fig. 1)

1. Substituição de contrações ("wouldn't" → "would not"), via regex em Python.
2. Remoção de URLs, e-mails e expressões entre parênteses.
3. Normalização de abreviações (sinônimos do WordNet, ex.: USA → United States of America; lista manual do STS 2015: govt → government, 1.6lb → 1.6 pound, 5m → 5 million).
4. Substituição de negações por antônimos do WordNet ("not present" → "absent").
5. Correção ortográfica (pyenchant).
6. Remoção de stopwords (lista Stanford) só em headlines, plagiarism e postediting; mantidas em answer-answer e question-question.
7. Lematização (NLTK).

### Run 1 — similaridade semântica + sintática (Fig. 2, baseada em Li et al., 2006)

Fluxo: s1, s2 → Preprocessing → Joint Word Vector (JWV, palavras únicas do par) → vetores semânticos brutos (com Lexical database/WordNet) e vetores sintáticos → vetores semânticos ponderados (com Corpus/Brown) → similaridade semântica e sintática → Sentence Similarity. Diferença em relação a Li et al.: escolhe o par de synsets mais similar, não o primeiro synset nominal.

Similaridade palavra–palavra no WordNet (l = menor caminho, h = profundidade; α = 0,2, β = 0,45; valor < 0,2 vira 0):

```latex
s(w_i, w_j) = e^{-\alpha l}\cdot \frac{e^{\beta h} - e^{-\beta h}}{e^{\beta h} + e^{-\beta h}}
```

**\[ERRO NO ARTIGO\]** Conferido na imagem da página 3: o próprio artigo imprime e^{αl}, sem o sinal de menos. Não é falha de extração. A forma correta de Li et al. (2003/2006) é e^{−αl} (a similaridade precisa cair com a distância). A fração é tanh(βh).

Conteúdo de informação (Brown corpus; n = frequência da palavra, N = total de palavras):

```latex
I(w) = 1 - \frac{\log(n+1)}{\log(N+1)}
```

Cada entrada do vetor semântico vale 1 se a palavra do JWV está na frase; senão, o maior s(·) com as palavras da frase; depois é multiplicada por I(w). S\_sem = cosseno entre os dois vetores.

Vetor sintático: entrada i = posição j da palavra na frase (ou posição da palavra mais similar). Similaridade de ordem:

```latex
S_{syn} = 1 - \frac{\|o_1 - o_2\|}{\|o_1 + o_2\|}
```

Combinação (Ω = 0,85):

```latex
S(s_1, s_2) = \Omega\, S_{sem} + (1-\Omega)\, S_{syn}
```

### Run 2 — DSSM (Huang et al., 2013) via Sent2Vec

- Word hashing: cada palavra ganha marcadores (`#girl#`) e é quebrada em trigramas de letras (`#gi, gir, irl, rl#`); dimensão = 3.073 trigramas.
- Camadas (f = tanh), 1 camada oculta com 1.000 nós:

```latex
l_1 = W_1 x,\quad l_i = f(W_i l_{i-1} + b_i),\ i = 2,\dots,N-1,\quad y = f(W_N l_{N-1} + b_N)
```

- Similaridade = cosseno entre os vetores y, mapeado linearmente para \[0, 5\]. DSSM superou C-DSSM no STS 2015 sem significância estatística.

### Run 3 — combinação linear

```latex
S_{run3} = \alpha\, S_{run1} + \beta\, S_{run2},\quad \alpha = \beta = 0{,}5
```

### Resultados (Pearson)

| STS 2016 | Pares | Run 1 | Run 2 | Run 3 | Melhor da competição |
| --- | --- | --- | --- | --- | --- |
| answer-answer | 254 | 0,58873 | 0,57739 | 0,61426 | 0,69235 |
| headlines | 249 | 0,73458 | 0,75061 | 0,77263 | 0,82749 |
| plagiarism | 230 | 0,76887 | 0,80068 | 0,80500 | 0,84138 |
| postediting | 244 | 0,85020 | 0,82857 | 0,84840 | 0,86690 |
| question-question | 209 | 0,69306 | 0,73035 | 0,74705 | 0,74705 |
| Média ponderada | 1.186 | 0,72646 | 0,73569 | 0,75607 | 0,77807 |

| STS 2015 | Pares | Run 1 | Run 2 | Run 3 | Melhor |
| --- | --- | --- | --- | --- | --- |
| answers-forums | 375 | 0,7049 | 0,6660 | 0,7246 | 0,7390 |
| answers-students | 750 | 0,7422 | 0,6770 | 0,7416 | 0,7879 |
| belief | 375 | 0,7287 | 0,7439 | 0,7389 | 0,7717 |
| headlines | 750 | 0,7630 | 0,7749 | 0,7776 | 0,8417 |
| images | 750 | 0,8198 | 0,8576 | 0,8367 | 0,8713 |
| Média ponderada | 3.000 | 0,7604 | 0,7536 | 0,7719 | 0,8015 |

O Run 3 empatou com o melhor da competição em question-question (0,74705). Peso de cada dataset na média = proporcional ao nº de pares.

### Pontos a não herdar

- **\[IMPRECISÃO\]** A Seção 3 chama a média ponderada de "sum" das correlações; o valor da tabela é a média ponderada pelo nº de pares (recalculado, confere).
- **\[ERRO NO ARTIGO\]** Afirma que os vetores do DSSM são não negativos e o cosseno fica em \[0, 1\], mas a ativação é tanh, que gera valores negativos.
- Conferido: em 2016 o Run 3 supera Run 1 e Run 2 em 4 de 5 datasets (perde para o Run 1 em postediting), como o artigo afirma. Em 2015 ele só é o melhor dos três em answers-forums e headlines, mas vence na média ponderada.

## Artigo 5 — Poljak, Crčić, Horvat (2025): comparação de algoritmos de similaridade

Survey de 5 famílias (7 funções) com uma app Flask que mede similaridade, tempo e memória de cada uma; no exemplo, Jaro/Jaro-Winkler deram 80,09% e Smith-Waterman 12,14% para o mesmo par.

### Fórmulas (Eqs. 1–7)

Levenshtein, recorrência de programação dinâmica (Eq. 1):

```latex
lev_{a,b}(i,j) = \begin{cases} \max(i,j), & \min(i,j) = 0 \\ \min\begin{cases} lev_{a,b}(i-1,j) + 1 \\ lev_{a,b}(i,j-1) + 1 \\ lev_{a,b}(i-1,j-1) + 1_{(a_i \ne b_j)} \end{cases} & \text{caso contrário} \end{cases}
```

Damerau-Levenshtein: A4 descreve a transposição adjacente como quarta operação, sem recorrência e sem declarar OSA. O código usa a variante restrita OSA, cuja recorrência acrescenta lev(i−2,j−2)+1 quando a\_i=b\_{j−1} e a\_{i−1}=b\_j. OSA restringe a reedição de subcadeias e pode divergir da variante irrestrita. A escolha é do projeto; não é reprodução confirmada da variante usada pelo A4. Recálculo complementar e teste discriminante em TCC/03.

Distância → similaridade (Eq. 2):

```latex
\text{sim} = 1 - \frac{\text{nº de mudanças}}{\text{comprimento da maior string (no artigo: Longest word length)}}
```

Jaro (Eq. 3), m = caracteres coincidentes, t = transposições:

```latex
sim_j = \begin{cases} 0, & m = 0 \\ \frac{1}{3}\left(\frac{m}{|s_1|} + \frac{m}{|s_2|} + \frac{m - t}{m}\right), & m \ne 0 \end{cases}
```

**\[NÃO DEFINIDO NO ARTIGO\]** t = metade do nº de caracteres coincidentes fora de ordem; coincidência só vale dentro da janela ⌊max(|s1|,|s2|)/2⌋ − 1.

Jaro-Winkler (Eq. 4):

```latex
sim_w = sim_j + l\,p\,(1 - sim_j)
```

**\[NÃO DEFINIDO NO ARTIGO\]** l = prefixo comum (máx. 4); p = fator de escala (padrão 0,1, não pode passar de 0,25).

Smith-Waterman (Eq. 5):

```latex
H(i,j) = \max\begin{cases} 0 \\ H(i-1,j-1) + \text{match/mismatch} \\ H(i-1,j) + \text{gap} \\ H(i,j-1) + \text{gap} \end{cases}
```

**\[NÃO DEFINIDO NO ARTIGO\]** inicialização H(i,0) = H(0,j) = 0, valores de match/mismatch/gap e a normalização usada para virar porcentagem.

Cosseno (Eq. 6):

```latex
\cos\theta = \frac{A\cdot B}{\|A\|\,\|B\|}
```

N-gram (Eq. 7), X e Y = conjuntos de n-gramas (é o coeficiente de Dice, o artigo não dá esse nome nem o n usado):

```latex
\text{sim}_{ngram} = \frac{2\,|X \cap Y|}{|X| + |Y|}
```

### Arquitetura da app (Fig. 1)

1. **Frontend Module:** Text input, PDF upload, Algorithm selection, Results display (HTML, CSS, JavaScript/jQuery, AJAX, Bootstrap).
2. **Backend Module:** Request processing, Running the algorithm (Flask; PyMuPDF extrai texto de PDF; psutil mede memória e CPU); resposta em JSON.
3. **Algorithm Module:** uma função por algoritmo (Levenshtein, Damerau-Levenshtein, Jaro, Jaro-Winkler, Smith-Waterman, Cosine, N-gram), mais o modo "Benchmark All".

### Resultados

| Algoritmo (Fig. 2) | Similaridade | Tempo (s) | Memória (bytes) |
| --- | --- | --- | --- |
| Levenshtein | 30,78% | 0,6519 | 0 |
| Damerau-Levenshtein | 30,96% | 2,2222 | 1.654.784 |
| Jaro | 80,09% | 0,0507 | 0 |
| Jaro-Winkler | 80,09% | 0,0450 | 0 |
| Smith-Waterman | 12,14% | 38,3630 | 2.592.768 |
| Cosine | 57,11% | 0,0000 | 0 |
| N-gram | 65,30% | 0,0021 | 0 |

| Caso de teste (Tabela 1) | Esperado | Obtido |
| --- | --- | --- |
| Textos simples | alta | 93% |
| Similares, formatação diferente | alta | 89% |
| Com erros gramaticais | média | 76% |
| Completamente diferentes | baixa | 12% |
| Muito longos | variável | 40% |

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** Duas figuras numeradas "Figure 1" e o texto cita uma "Fig. 3" inexistente.
- **\[ERRO NO ARTIGO\]** A Tabela 1 não diz qual algoritmo gerou cada porcentagem; não serve como evidência de acurácia.
- Memória 0 bytes na Fig. 2 (A4, PDF 5 / p. 155) é valor publicado, não prova de consumo zero; causa exata não identificada no artigo. Delta RSS, pico de RSS e blocos Python rastreados por tracemalloc são medidas diferentes; definir instrumento/escopo/aquecimento/amostragem e limitações antes dos experimentos. tracemalloc não cobre universalmente memória nativa ou GPU. Fontes técnicas: documentação oficial Python 3.11 e psutil, citadas no guia 0.5.
- O texto chama o Smith-Waterman de "excepcionalmente preciso", mas no próprio exemplo ele foi o mais lento (38,36 s) e o mais baixo (12,14%).

## Artigo 6 — Halim & Lasut (2024): app web de plágio com TF-IDF + cosseno

App web em indonésio que pondera termos por TF-IDF e compara por cosseno; o cálculo manual deu 4% e a app 4,34% para o mesmo par. Recalculei o exemplo: o valor exato é 3,65%, que arredonda para 4%.

### Pré-processamento (Seção III.B)

1. Lowercasing.
2. Noise removal (símbolos estranhos).
3. Remoção de stopwords (biblioteca Python Sastrawi).
4. Tokenização (separação por espaços).
5. Feature selection: para teste só o atributo Content; para exibição Title, Content, Category (Fig. 2).

**\[NÃO DEFINIDO NO ARTIGO\]** As Tabelas 6–7 mostram radicais (kembang, langgar, tindak, anggar), ou seja, houve stemming (Sastrawi), mas o artigo não lista essa etapa.

### Fórmulas

TF-IDF (Eq. 1), tf = contagem bruta do termo j no documento i, N = nº de documentos, df = nº de documentos com o termo (log na base 10):

```latex
W_{ij} = tf_{ij} \times idf_j,\qquad idf_j = \log_{10}\frac{N}{df_j}
```

Cosseno (Eqs. 2 e 3):

```latex
SV = \frac{A\cdot B}{\|A\|\,\|B\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2}\,\sqrt{\sum_{i=1}^{n} B_i^2}}
```

### Exemplos numéricos \[RECALCULADO\]

Exemplo didático (Tabelas 4–5): D1 = "Aku Bisa", U = "Bisa Kenapa", N = 2.

| Token | U | D1 | df | idf = log(N/df) |
| --- | --- | --- | --- | --- |
| aku | 0 | 1 | 1 | log(2) = 0,30103 |
| bisa | 1 | 1 | 2 | log(1) = 0 |
| kenapa | 1 | 0 | 1 | 0,30103 |

Pesos: U = (0; 0; 0,30103), D1 = (0,30103; 0; 0). Produto escalar = 0, logo cos = 0 (confere com o artigo).

Exemplo real (Tabelas 6–8): consulta u + d1, d2, d3, N = 4; idf = log(4/1) = 0,60206 para termos únicos e log(4/2) = 0,30103 para "kembang" (u, d2) e "ilmu" (d1, d2).

- u: 6 termos com 0,60206 + kembang 0,30103 → ‖u‖ = √(6 × 0,36248 + 0,09062) = √2,26548 = 1,50515.
- d2: kembang e ilmu com 0,30103 + 7 termos com 0,60206 → ‖d2‖ = √(2 × 0,09062 + 7 × 0,36248) = √2,71857 = 1,64881.
- u · d2 = 0,30103 × 0,30103 = 0,09062.
- cos(u, d2) = 0,09062 / (1,50515 × 1,64881) = 0,09062 / 2,48171 = **0,0365 = 3,65%** → o artigo arredonda para 4%; a app mostra 4,34%.
- cos(u, d1) = cos(u, d3) = 0 (sem termos em comum). Confere.

Na tela de resultado (Fig. 10) aparece também 1,45% como escore geral, descrito como a soma das similaridades dividida pelo nº de PDFs na base; 4,34% é o maior individual.

### Arquitetura e engenharia de software

- Método Waterfall: Requirements Analysis → Design → Development → Testing → Maintenance.
- Stack: XAMPP (Apache, MySQL, PHP, phpMyAdmin), Python (Sastrawi); upload só em PDF.
- ERD (Fig. 3): entidades Login, User (login), user, Upload, Admin, PDF (journal, article, book); atributos como id, Title, Content, Category, Username, Percentage, url, ip\_address.
- DFD: Hierarchy Chart (0 Web-based Plagiarism Application → 1 Input Data, 2 Process, 3 Outdata (grafia do artigo); subprocessos 1.1 Admin Data, 1.1 User Data, 2.1 User Data, 2.1 Admin Data, 3.1 Plagiarism Result), Context Diagram (Admin, User ↔ Web Plagiarism System), Level 0 (1.0 Login, 2.0 Account, 3.0 Process, 4.0 Result) e Level 1.
- Teste black box por equivalence partitioning: 15 telas/formulários, 74 itens de teste (somados da Tabela 3), todos aprovados.
- Text mining em 3 etapas: extração de informação, descoberta de texto (KDD), text analytics.

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** A nota da Eq. 1 define "n: number of documents containing the term", mas a fórmula usa df.
- **\[ERRO NO ARTIGO\]** Exemplo de tokenização: 5 tokens listados, texto diz "Number of Tokens 7".
- **\[FRAGILIDADE\]** O artigo atribui "mais precisão" ao TF-IDF + cosseno sem nenhuma métrica de acurácia; a única validação é manual × app (4% × 4,34%), que testa a implementação, não a detecção de plágio.
- A diferença 3,65% × 4,34% pode vir de pré-processamento diferente na app; o artigo não explica.

## Artigo 7 — Lubis, Lubis, Wahidah (2026): busca semântica com Sentence-BERT + FAISS

Repositório acadêmico com 100 documentos em indonésio indexados por embeddings SBERT em FAISS IndexFlatL2; média de Recall@10 = 0,61 e MAP = 0,39 em 30 consultas, latência < 1 ms.

### Etapas da pesquisa (Fig. 1)

1. Problem Analysis
2. Collecting and Processing of the Document Dataset
3. Embedding Implementation and Indexing FAISS
4. User Interface Development and System Integration
5. System Testing and Evaluation

### Arquitetura (Fig. 2, lida da imagem)

- **APP:** Documents → Web Page (CodeIgniter 4) → MySQL + Storage (arquivos).
- **MODEL:** DB Interface → Text Preprocessing (remoção de HTML do editor WYSIWYG, caracteres especiais, normalização) → BERT Embedding → FAISS Indexing → Model Data.
- **API (FastAPI):** Indexing, Searching, Evaluate; consumida pelo CI4.
- Telas: Document List, Model Page (reindexar, avaliar), Evaluation Data Page, Search Page.
- Tabela MySQL: id\_documents, category, title, file type, file name, file path, text\_content.

### Fórmulas (Eqs. 1–4)

```latex
h_i = \mathrm{BERT}(w_i),\ i = 1,\dots,n \qquad u = f(h_1,\dots,h_n) \qquad u = \frac{1}{n}\sum_{i=1}^{n} h_i
```

Distância usada no FAISS IndexFlatL2 (busca exata, sem aproximação):

```latex
d(x_q, x_i) = \|x_q - x_i\|_2
```

O modelo SBERT específico não é informado **\[NÃO DEFINIDO NO ARTIGO\]**.

### Métricas de avaliação

O artigo lista Recall@K, NDCG@K, MRR, MAP, No-Hit Rate, latência p50/p95/p99 e tempo de embedding, mas não escreve nenhuma equação **\[NÃO DEFINIDO NO ARTIGO\]**. Formas padrão (relevância binária, Q = consultas, rel\_k ∈ {0,1}):

```latex
\mathrm{Recall@K} = \frac{|\text{relevantes no top-}K|}{|\text{relevantes}|} \qquad \mathrm{MRR} = \frac{1}{|Q|}\sum_{q\in Q}\frac{1}{rank_q}
```

```latex
\mathrm{DCG@K} = \sum_{k=1}^{K}\frac{rel_k}{\log_2(k+1)} \qquad \mathrm{NDCG@K} = \frac{\mathrm{DCG@K}}{\mathrm{IDCG@K}}
```

```latex
\mathrm{AP}(q) = \frac{1}{|R_q|}\sum_{k=1}^{K} P@k \cdot rel_k \qquad \mathrm{MAP} = \frac{1}{|Q|}\sum_{q} \mathrm{AP}(q)
```

No-Hit Rate = fração de consultas sem nenhum relevante no top-K.

Critério de relevância (binário, anotado por especialistas): relevante se (1) responde ao tópico, (2) trata do mesmo evento/política, ou (3) tem forte alinhamento semântico; só palavras-chave em comum não basta.

### Resultados (Tabela 3, K = 10, 10 consultas por conjunto)

| Métrica | Test 1 | Test 2 | Test 3 | Média \[RECALCULADO\] |
| --- | --- | --- | --- | --- |
| Recall@10 | 0,55 | 0,667 | 0,6 | 0,606 |
| NDCG@10 | 0,409 | 0,44 | 0,376 | 0,408 |
| MRR | 0,575 | 0,381 | 0,418 | 0,458 |
| MAP | 0,45 | 0,381 | 0,341 | 0,391 |
| No-Hit Rate | 0,1 | 0 | 0 | 0,033 |
| Latência p50 (ms) | 0,32 | 0,31 | 0,32 | 0,317 |
| Latência p95 (ms) | 0,44 | 0,43 | 0,43 | 0,433 |
| Latência p99 (ms) | 0,48 | 0,47 | 0,46 | 0,470 |
| Tempo de embedding (ms) | 125,93 | 118,38 | 131,92 | 125,41 |

As médias citadas no artigo (Recall 0,61, MAP 0,39, No-Hit 0,033) conferem.

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** O resumo diz que "todas as consultas recuperaram resultados", mas o No-Hit de 0,033 significa 1 de 30 consultas sem relevante (a do Test 1).
- **\[ERRO NO ARTIGO\]** Descreve o FAISS como buscando "o vetor de consulta que mais se parece com os documentos"; é o contrário: os x\_i mais próximos de x\_q.
- **\[CORRIGIDO: falso positivo meu\]** No Test 2 o NDCG sobe e o MRR cai, e o próprio artigo comenta isso. Não é contradição: o NDCG mede a posição de todos os relevantes; o MRR, só a do primeiro.
- L2 sobre embeddings não normalizados não equivale a cosseno; se usar no TCC, normalize os vetores (aí L2 e cosseno ordenam igual) ou use IndexFlatIP.
- Corpus pequeno (100 docs) e 30 consultas: o próprio artigo diz que não generaliza para escala.

## Artigo 8 — Cooper, Coden, Brown (2002): documentos similares por termos salientes

Documentos são considerados similares quando a fração de termos salientes (multi-palavra e únicos) que não aparecem no outro fica abaixo de um limiar; com texto inserido, o método achou 12 de 12 pares contra 5 de 12 dos shingles. Este PDF não tem camada de texto: tudo abaixo foi lido das imagens.

### Pipeline (Seções 2, 5 e 9)

1. Documentos retornados por uma busca (\~50); PDFs convertidos para HTML com o plug-in Gemini do Acrobat.
2. **Textract** (suite Talent, IBM): reconhece termos multi-palavra, nomes próprios e abreviações; reduz variantes a uma forma canônica.
3. Cada termo recebe o **IQ (Information Quotient)**, medida de seletividade em nível de coleção: termo em poucos documentos = IQ alto. Fórmula do IQ não é dada **\[NÃO DEFINIDO NO ARTIGO\]** (refs. \[5\], \[14\]).
4. Biblioteca Java **KSS** carrega os termos em **DB2**.
5. Consultas SQL comparam pares; documentos ordenados por tamanho e comparados só com os até 10% maiores (triângulo superior da matriz, evita n² consultas).

Categorias do Textract (Tabela 1, da menor para a maior certeza): UWORD (palavra desconhecida), UTERM, UABBR, UNAME, PLACE?, PERSON?, PLACE, PERSON, ORG.

### Regra de similaridade

Filtro de termos: IQ > 0 e categoria ≠ UWORD. Contagem de termos de doc2 ausentes em doc1:

```sql
Select count(*) as c from
  (select terms from doc1 where ..)
not in
  (select terms from doc2 where ..)
```

Forma matemática registrada originalmente no mapa (T = conjunto filtrado de termos). Correção de procedência em 2026-10-24: a prosa da p. 247 descreve doc2 menos doc1, mas o SQL mostra doc1 menos doc2. A direção não é unívoca. A seção 9, p. 250 (PDF p. 6), usa os termos do documento menor pelo tamanho do documento, não a menor quantidade de termos; a fórmula abaixo só expressa a interpretação da prosa, com esse denominador:

```latex
\Delta(d_1, d_2) = \frac{|T(d_2) \setminus T(d_1)|}{|T(d_{menor})|},\qquad \text{similares se } \Delta < \tau
```

Limiares usados: τ = 10% e tamanho até 10% maior (quase-duplicatas); τ = 20% como critério de "relacionados"; relaxado até 50% (termos e tamanho) para documentos com texto inserido.

Conferência Codex: o tamanho é associado aos arquivos comparados e à ordenação das seções 5.2 e 9. A coluna Size das tabelas não nomeia sua unidade; a seção 8 menciona explicitamente bytes na inserção. Não equiparar tamanho a número de termos. Listas completas de termos, regra de desempate para arquivos do mesmo tamanho e convenção para denominador vazio: não encontrado no artigo. A reprodução integral de Δ das tabelas continua PENDENTE; ver TCC/14. O limite de tamanho de 50% aparece na seção 9, p. 250, e não é parâmetro ausente.

### Shingles (baseline, Broder et al., Seções 4 e 9.1)

- Texto em minúsculas, janela móvel de 10 palavras, hash Java `String.hashCode` de cada janela.
- Remove duplicatas e mantém só os shingles com s mod 25 = 0 (25 nas Seções 4 e 9.1; conferido na imagem, não existe 250); se ainda forem muitos, os 400 menores.
- Documentos muito curtos: todos os shingles, sem diferença significativa.

### Assinatura do documento (Seção 6)

```latex
\mathrm{sig}_{termos}(d) = \sum_{t \in T(d)} \mathrm{hashCode}(t) \qquad \mathrm{sig}_{shingles}(d) = \sum_{s \in S(d)} s
```

Ignora a ordem dos termos; os autores admitem colisões possíveis e o caso patológico de documentos que diferem só por "not".

### Resultados

Consulta 1 ("fix broken Thinkpad", 36 documentos analisados): 6 clusters.

| Documentos | Tamanho | Δ termos | Δ shingles |
| --- | --- | --- | --- |
| Sytpf130 / Sytpfl1301 | 12.236 | 0 | 0 |
| aixy2k / aixy2k1 | 153.255 | 0 | 0 |
| Conf / client | 52.854 | 0 | 0 |
| Fund4 (vs Fund2) | 481.963 | 0 | 0 |
| ct7mhna1 | 493.225 | 0,014 | 0,112 |
| ct7mhna2 | 493.295 | 0 | 0 |
| Fund0 | 503.138 | 0,029 | 0,074 |
| Fund1 | 504.737 | 0,016 | 0,120 |
| Fund3 | 505.004 | 0,011 | 0,094 |
| Fund5 | 505.471 | 0,005 | 0,012 |
| Selpdf (vs Selhtm) | 54.274 | 0,106 | 0,44 |

Na Tabela 3 o Δ é entre documentos adjacentes da lista ordenada por tamanho. No par Selker (HTML × PDF, \~7.800 palavras, 169 multi-palavras, \~1.300 termos), trocar hífen suave (0xad) por hífen duro (0x2d) só baixou o Δ dos shingles de 0,44 para 0,39.

Consulta 2 ("Program ViaVoice in Java", 47 de 50 documentos, maior com 75 KB): 8 pares idênticos por tamanho e assinatura + 13 documentos muito similares, diferindo em 1–2 de 47 termos; 6 com assinatura de termos idêntica apesar de 4 tamanhos diferentes. A assinatura por shingles achou 6 pares idênticos, mas, segundo o artigo, não reconheceu que 4 desses pares eram efetivamente idênticos, como a assinatura de termos reconheceu.

Experimento de texto inserido (12 documentos financeiros da IBM + trecho de 2.533 bytes de um release sobre supercomputadores inserido em cada):

| Documento | Δ termos | Δ shingles |
| --- | --- | --- |
| Folder1 | 0,100 | 0,28 |
| Reuters | 0,157 | 0,41 |
| Nletter | 0,06 | 0,06 |
| Folder | 0,117 | 0,86 |
| Ebus3 | 0,076 | 0,84 |
| Ebus1 | 0,055 | 1,00 |
| Retaildel | 0,096 | 0,01 |
| Kookmin | 0,054 | 0,03 |
| 24552 | 0,040 | 0,48 |
| Building | 0,040 | 0,03 |
| Ebusmark | 0,010 | 0,26 |
| RetailB | 0,015 | 0 |

&#91;RECALCULADO\] Com τ = 0,20, termos identificam 12/12 (máximo 0,157) e shingles 5/12 (Nletter, Retaildel, Kookmin, Building, RetailB): precisão e recall de 100% para termos e recall < 50% para shingles, como o artigo afirma. O release original curto não foi associado aos outros por nenhum dos métodos.

### Pontos a não herdar

- O IQ é estatística da coleção: muda conforme os documentos retornados; os autores contornam exigindo só IQ > 0.
- A assinatura por soma de hashes depende do conjunto de termos escolhido; mudou o critério, recalcula tudo.
- O SQL do artigo diz "terms that appear in document 2 that are not in document 1", mas a consulta mostrada tem doc1 no primeiro select. Ao reproduzir, deixe explícita a direção (é assimétrica).

## Artigo 9 — Setu et al. (2025): estratégia em 3 fases para plágio acadêmico

Compara cada par de trabalhos pelo máximo entre cosseno TF-IDF e BERT (limiar 30%) e, abaixo do limiar, busca na web linha a linha (limiar 65%); no MIT Plagiarism Dataset: P 68%, R 80%, Acc 71%, F1 74%, números que conferem com a matriz de confusão.

### Fases

1. **Coleta (Fig. 1):** Start → Input file (pdf, pptx, docx, txt; via Google Forms/Classroom, pasta no Drive só do professor) → Choose Conversion tool → Text extraction → Store all text files → Processor → CSV files → End. Imagens e tabelas excluídas; reenvio substitui a versão anterior.
2. **Similaridade (Fig. 3):** Preprocessed data → verbatim por cosseno (TF-IDF) → semântica por BERT → máximo das duas → escore.
3. **Online (Algoritmo 2):** googlesearch → requests + BeautifulSoup → TfidfVectorizer + cosine\_similarity (scikit-learn) → percentual de linhas copiadas.

Dados: 100 documentos do departamento → 4.950 pares; validação com MIT Plagiarism Detection Dataset (367.375 amostras, 10% usados no teste). Divisão 80% treino / 20% teste.

### Pré-processamento (Fig. 2)

Loading Data → Tokenization → Token Normalization → Lemmatization → POS Tagging → Filter and Reassemble token → Vectorization → Preprocessed Data. Filtro final: só alfabéticos, sem stopwords, tamanho > 2.

```latex
T_{clean} = \{t \in T \mid t\ \text{alfabético e não stopword}\} \qquad T_{filt} = \{t \in T_{tag} \mid |t| > 2\ \text{e alfabético}\}
```

### Fórmulas

Nº de pares (Eq. 1), 100 documentos → 4.950 \[RECALCULADO\]:

```latex
\binom{n}{2} = {}^{n}C_{2} = \frac{n!}{2!\,(n-2)!}
```

TF-IDF como **impresso** no artigo (Eq. 2):

```latex
W_{y,j} = TF_{y,j} + \ln\left(\frac{N}{df_y}\right)
```

**\[ERRO NO ARTIGO\]** O correto é o produto, não a soma (o próprio texto diz "multiplying the term TF by the IDF"). Use no TCC:

```latex
W_{y,j} = TF_{y,j} \times \ln\left(\frac{N}{df_y}\right)
```

Cosseno (Eq. 3):

```latex
\cos(S_1,S_2) = \frac{\sum_{i=1}^{n} S_1(i)\,S_2(i)}{\sqrt{\sum_{i=1}^{n} S_1(i)^2}\,\sqrt{\sum_{i=1}^{n} S_2(i)^2}}
```

Percentual online (Algoritmo 2, linha 22):

```latex
P_{online} = \frac{total\_copy}{total\_lines} \times 100
```

### Algoritmo 1 — integridade acadêmica

1. Para cada par (i, j), j > i: cos\_ij = cosseno TF-IDF; bert\_ij = similaridade BERT; S\_ij = max(cos\_ij, bert\_ij).
2. Total de pares = nC2; Threshold\_Online = 30.
3. Se S > limiar textual (30%): plágio; cópia direta se cos > bert, paráfrase se bert > cos.
4. Se S ≤ 30%: chama a verificação online.

### Algoritmo 2 — similaridade com a internet

1. Lê o arquivo e gera URLs; sem URLs → "No relevant online source found".
2. Threshold = 65; para cada linha e cada URL: raspa o conteúdo; se sim ≥ 65, total\_copy += 1 e passa à próxima linha.
3. P\_online ≥ 65 → "copied from an online source"; senão → "unique".

### Modelos BERT

- Sentence Transformer **all-MiniLM-L6-v2** para embeddings + cosseno.
- **bert-base-uncased** (Hugging Face) fine-tuned para classificação de paráfrase com 2 rótulos; BertTokenizer; softmax nos logits → probabilidade; AdamW, lr = 1 × 10⁻⁵.

### Resultados \[RECALCULADO das matrizes\]

| Conjunto | TN | FP | FN | TP | P | R | Acc | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Privado (limiar 0,3) | 117 | 318 | 37 | 518 | 0,620 | 0,933 | 0,641 | 0,745 |
| MIT (limiar 0,3) | 11.443 | 6.863 | 3.715 | 14.716 | 0,682 | 0,798 | 0,712 | 0,736 |
| Online (limiar 65%) | 300 | 160 | 240 | 300 | 0,652 | 0,556 | 0,600 | 0,600 |

Totais conferem: 990 = 20% de 4.950; 36.737 = 10% de 367.375; online 1.000. Taxa de erro reportada: 36% (privado) e 29% (MIT).

Tempos (HP ProBook, i5 2,8 GHz, 8 GB, Python 3.10.12): treino 6,11 s (direto), 68,21 s (semântico), 0,00396 s (máximo); teste 1,55 s, 14,25 s, 0,00099 s.

### Pontos a não herdar

- **\[ERRO NO ARTIGO\]** TF-IDF com "+" na Eq. 2 (ver acima).
- **\[ERRO NO ARTIGO\]** O resumo fala em "threshold of 0.2" para a detecção online; a metodologia usa 65%.
- &#91;ERRO NO ARTIGO\] Na discussão (p. 323) o texto diz que no MIT a precisão é de 62% e o recall de 79%, com 14.716 TP e 6.863 FP. Esses mesmos números dão precisão de 14.716 / 21.579 = 68,2% e recall de 79,8%, como o resumo (68% e 80%). O 62% é erro do artigo (repete o da base privada); o 79% é truncamento de 79,8%. Reconferido em 21/10 no texto da p. 323.
- **\[ERRO NO ARTIGO\]** O Algoritmo 1 usa Threshold\_Textual sem defini-lo (só define Threshold\_Online = 30).
- **\[IMPRECISÃO\]** Diz que o cosseno vai de −1 a 1, o que vale em geral; com vetores TF-IDF (pesos não negativos) fica em \[0, 1\].
- **\[AMBÍGUO NO ARTIGO\]** Fala de "BERT" como um modelo só, mas usa dois (MiniLM e bert-base fine-tuned) sem dizer qual entra no máximo.
- Lematização antes do POS tagging é ordem incomum (o POS normalmente orienta o lematizador).

## Quadro cruzado e erros a não herdar

Cosseno aparece em 7 dos 9 artigos e TF-IDF em 3; as variações que mais importam para o TCC são a base do log no IDF, o operador (× e não +) e a métrica de distância no FAISS.

| Técnica / fórmula | Artigos | Observação para o TCC |
| --- | --- | --- |
| Cosseno | 1, 2, 3, 4, 5, 6, 9 | 7 usa distância L2 no FAISS; 8 compara conjuntos de termos, não vetores |
| TF-IDF | 2, 6, 9 (+ vetor do 5) | 6 usa log₁₀(N/df) com tf bruto; 9 usa ln(N/df) e imprime "+" por engano |
| Sentence-BERT / pooling médio | 1, 2, 7, 9 | Só 9 diz o modelo (all-MiniLM-L6-v2) |
| BERT fine-tuned | 1 (regressão Siamesa), 9 (classificação de paráfrase) | 1: Adam lr 2e-6, MSE; 9: AdamW lr 1e-5 |
| Ponderação de dois escores | 2 (0,6 SBERT + 0,4 TF-IDF), 4 (0,85 sem + 0,15 sin; 0,5 + 0,5), 9 (máximo) | Três estratégias de fusão distintas para comparar |
| Limiares | 2 (0,85 / 0,75), 8 (10%, 20%, 50%), 9 (30%, 65%) | Sempre dizer como foram escolhidos |
| Edit distance / string | 3 (Paris), 5 (Levenshtein, Damerau, Jaro, JW, SW, N-gram) | 5 omite parâmetros do JW e do SW |
| Alinhamento de palavras | 3 (LP), 4 (JWV/WordNet) | 3: sim = 1 + cos |
| Shingles / fingerprint | 8 | Janela 10, mod 25, 400 menores |
| Métricas de IR | 7 | Equações não dadas no artigo; usar formas padrão |
| Métricas de classificação | 2, 9 | F1 = média harmônica |
| Pearson / Spearman / R² | 1, 3, 4 | Padrão de avaliação em STS |

### Erros consolidados

- [ ] Art. 9 — TF-IDF com soma em vez de produto (Eq. 2).
- [ ] Art. 4 — expoente e^{αl} impresso no próprio artigo; correto e^{−αl}.
- [ ] Art. 2 — F1 chamado de "média"; ablação citada sem números; referências com numeração trocada.
- [ ] Art. 1 — "encoder-decoder" para BERT; rótulos gerados por LLM (limitação); dropout escrito na forma resumida (simplificação).
- [ ] Art. 7 — "todas as consultas recuperaram" contra No-Hit 0,033; L2 sem normalização.
- [ ] Art. 9 — limiar online 0,2 (resumo) × 65% (Algoritmo 2); precisão do MIT 62% na discussão × 68,2% pela matriz; Threshold\_Textual indefinido.
- [ ] Art. 3 — "linear regression" × regressão logística; 0,672 = ensemble sem Align.
- [ ] Art. 6 — "n" × df na legenda; "7 tokens" para 5; stemming não descrito.
- [ ] Art. 5 — numeração de figuras; parâmetros do Jaro-Winkler e Smith-Waterman ausentes.
- [ ] Art. 8 — direção da diferença no SQL é assimétrica; IQ sem fórmula.

## Varredura completa texto + imagem (21/10/2026)

As 88 páginas dos 9 PDFs foram lidas em texto e em imagem; o A3 (Cooper) não tem camada de texto e foi lido só pelas imagens. Os achados abaixo complementam as seções de cada artigo.

| Artigo | Achado novo | Tipo |
| --- | --- | --- |
| Art. 1 (A7, Sarkar) | Divisão treino/teste, lote, α, p do dropout, dimensões densas e variante do BERT não informados | Não definido |
| Art. 1 (A7) | Só pares parafraseados (similares) são gerados, mas a arquitetura cita "Similar/Dissimilar" | Erro do artigo |
| Art. 1 (A7) | Campo 'url' listado duas vezes; refs. \[10\] e \[19\] iguais; o texto diz "highest" na 3ª linha da Tabela 3, mas o cosseno (95,48) supera o modelo (90,12) | Erro do artigo |
| Art. 2 (A6, Gawade) | A média aritmética ponderada dos valores da Tab. 2 com pesos 70/80/50 é 91,7%; não há matriz nem definição por classe que prove que esse cálculo produz a acurácia geral publicada de 92% | Recálculo ilustrativo, sem equivalência demonstrada |
| Art. 2 (A6) | "F1 acima de 0,85 em todas", mas Paraphrased = 0,85; 4.2 fala em 82–88% de precisão contra 0,87 na Tabela 2; "dashboard foi desenvolvido" dentro de Future Scope | Erro do artigo |
| Art. 3 (A9, MITRE) | Apêndice A: matrizes de alinhamento mínimo (1 + cos, 0 a 2) para notas 5,0, 2,6 e 0,0, base do mapa de calor | Faltava |
| Art. 3 (A9) | Primary = média simples das 7 trilhas (0,6590; corrigido 0,6687); o 0,650 da conclusão é o TakeLab isolado | Recalculado |
| Art. 4 (A8, MayoNLP) | Código público: github.com/naveedafzal/MayoClinic\_SemEval\_2016\_Task-1 | Faltava |
| Art. 4 (A8) | Escala do Run 1 antes da média com o Run 2 (0–5) não informada | Não definido |
| Art. 4 (A8) | Médias ponderadas 2016 e 2015 conferem; "Best" na média é a melhor equipe, não a média dos melhores (que daria 0,795) | Recalculado |
| Art. 5 (A4, Poljak) | Jaro = Jaro-Winkler = 80,09% porque os textos não têm prefixo comum (l = 0); Eq. 2 escreve "Longest word length" | Conferido |
| Art. 6 (A1, Halim) | Taxonomia: verbatim, patchwork, paráfrase e palavra-chave/frase (base das classes do dataset sintético) | Faltava |
| Art. 6 (A1) | "Dados de treino" sem treino; cosseno numerado (2) e depois (3); linhas 3 e 4 da Tabela 3 com o mesmo nome; datas "20xx" | Erro do artigo |
| Art. 7 (A2, Lubis) | Resumo "todas as consultas" × conclusão "a maioria"; consulta de junho de 2025 com relevante de junho de 2024 (Tabela 2); embedding ≈ 12,5 ms por consulta | Erro do artigo / recalculado |
| Art. 8 (A3, Cooper) | Sem DOI impresso; ISBN ACM 1-58113-492-4; Bloomfield (6+ palavras seguidas); método insensível a frases novas e rearranjo de parágrafos | Faltava |
| Art. 9 (A5, Setu) | Na p. 323, MIT com precisão 62% e recall 79%, mas 14.716 TP e 6.863 FP dão 68,2% e 79,8% | Erro do artigo |
| Art. 9 (A5) | URL do MIT no Kaggle: kaggle.com/datasets/ruvelpereira/mit-plagairism-detection-dataset; dados privados com aprovação ética | Faltava |

## Pente fino do guia do TCC (21/10/2026)

O guia foi corrigido no próprio .docx, sem apagar nenhum parágrafo original (176 idênticos, 62 complementados ou corrigidos e 125 novos). Numeração do guia: A1 = Halim (Art. 6), A2 = Lubis (7), A3 = Cooper (8), A4 = Poljak (5), A5 = Setu (9), A6 = Gawade (2), A7 = Sarkar (1), A8 = MayoNLP (4), A9 = MITRE (3).

| Onde no guia | Estava | Conferido no PDF |
| --- | --- | --- |
| A1, Dados e 3.1 | Exemplo com 3 documentos, N = 3, df = 1 dá 0,60206 | N = 4 (u + d1, d2, d3): log10(4) = 0,60206 |
| A1, Resultado | 15 itens de teste | 15 telas, 74 itens (Tabela 3) |
| A3, atenção, 3.3 e 8 | Módulo 25 e 250 | 25 nas Seções 4 e 9.1; não existe 250 |
| A4, 3.2 | Jaro e Jaro-Winkler "reconstruídas" | Impressas no artigo (Eqs. 3 e 4); só m, t, l e p não são definidos |
| A5, Resultados | Online "limiar 0,2" | 0,2 só no resumo; o método usa 65% |
| A5, atenção e 8 | "+" no TF-IDF "na extração" | Impresso no artigo (imagem da p. 317) |
| A5, Fase 1 | 9 passos listados com 8 | Os 9 passos completos da Fig. 2 |
| A5, 3.5 | Percentual online "interpretação minha" | Está no Algoritmo 2, linhas 22–23 |
| A7, Experimental Setup | 10 dependências | 13, com máquinas e os dois servidores |
| A8, 3.6 e 8 | e^(−α·l) "reconstruída"; notação S\_r e δ | O artigo imprime e^(α·l); notação S\_sem, S\_syn, o1, o2 e Ω |

Confirmado como certo no guia: as discrepâncias de 62% × 68% e 79% × 80% no MIT (A5). Uma "correção" minha anterior sobre esse ponto estava errada e foi desfeita.

Seções novas no guia: 4.4 (stack e monólito modular), 4.5 (camadas), 5.3 (dataset sintético), 5.4 (fluxo do dataset), 6 (hipóteses e testes), 6.1 (telas), 6.2 (testes por camada), 10 (docs/ e TCC/), 11 (regras para a IA), 12 (ordem de desenvolvimento) e 13 (registro de revisões).

## Valores de referência para testes

O projeto usa só dataset sintético (decisão de 21/10/2026); estes números, tirados ou recalculados dos próprios artigos, viram testes de unidade do core/domain.

| Função testada | Entrada (artigo) | Valor esperado |
| --- | --- | --- |
| idf = log10(N/df) | A1 (Art. 6), Tabela 6: N = 4, df = 1 | 0,60206 |
| idf | A1, Tabela 6: N = 4, df = 2 | 0,30103 |
| idf | A1, Tabela 4: N = 2, df = 2 ("bisa") | 0 |
| cosseno TF-IDF | A1, Tabelas 4–5: U × D1 | 0 |
| cosseno TF-IDF | A1, Tabela 7: u × d2 | 0,0365 (artigo arredonda para 4%) |
| cosseno TF-IDF | A1, Tabela 7: u × d1 e u × d3 | 0 |
| pares C(n,2) | A5 (Art. 9): n = 100 | 4.950 |
| P, R, F1, acurácia | A5, Fig. 9a: TN 117, FP 318, FN 37, TP 518 | 0,620 · 0,933 · 0,745 · 0,641 |
| P, R, F1, acurácia | A5, Fig. 9b: TN 11.443, FP 6.863, FN 3.715, TP 14.716 | 0,682 · 0,798 · 0,736 · 0,712 |
| P, R, F1, acurácia | A5, Fig. 10: TN 300, FP 160, FN 240, TP 300 | 0,652 · 0,556 · 0,600 · 0,600 |
| média ponderada por nº de pares | A8 (Art. 4), Tabela 1, Run 1/2/3 | 0,72646 · 0,73569 · 0,75607 |
| média ponderada por nº de pares | A8, Tabela 2, Run 1/2/3 | 0,7604 · 0,7536 · 0,7719 |
| média simples das trilhas | A9 (Art. 3), Tabela 1, oficial e corrigido | 0,6590 · 0,6687 |
| exercício aritmético de média ponderada; não é acurácia global reconstruída | A6 (Art. 2), Tab. 2 e pesos 70/80/50; denominadores por classe não publicados | 91,7%; a validade como acurácia geral não é demonstrada |
| sim de palavras = 1 + cos | A9, Apêndice A: palavra idêntica | 2,00 |
| Jaro-Winkler | A4 (Art. 5): sem prefixo comum (l = 0) | igual ao Jaro |

Nos testes de A1, a entrada são os tokens já pré-processados das Tabelas 6 e 7 (o texto original é indonésio e passou pelo Sastrawi), e o TF-IDF é o do artigo: tf bruto × log10(N/df), sem suavização. No scikit-learn, smooth_idf=False usa ln(N/df) + 1; o padrão smooth_idf=True usa ln((1+N)/(1+df)) + 1, com normalização L2 padrão. Nenhuma configuração padrão reproduz diretamente os pesos publicados do A1. Fonte técnica: documentação oficial de TfidfTransformer, consultada na integração de 2026-10-24; fórmula/esperados do projeto não foram alterados. Propriedades por função/domínio: distâncias têm identidade zero; similaridades de caracteres normalizadas, identidade um; cosseno geral não nulo admite negativos e 1+cos chega a 2. Cosseno TF-IDF não negativo fica em [0,1]; norma zero segue política explícita do projeto. Delta A3 é direcional e pode superar 1; assinatura inteira não é escore. Ver guia 6 e TCC/02.

## Revisão final de confiabilidade (21/10/2026, 18h)

Todos os números do mapa e das fichas do guia foram cruzados por script com o texto dos PDFs (o A3 via OCR das imagens). Os que não aparecem literalmente são recálculos marcados ou valores lidos de figuras e conferidos com zoom. Depois, os dois documentos foram relidos inteiros.

| Onde | Problema | Ação |
| --- | --- | --- |
| Mapa e guia, A1 | ‖u‖ e ‖d2‖ arredondados no meio da conta (1,50516; 1,64882) | Corrigido para 1,50515 e 1,64881; o resultado 0,0365 não muda |
| Mapa, Art. 7 (A2) | Falso positivo meu: NDCG sobe e MRR cai não é contradição | Desfeito e marcado \[CORRIGIDO\] |
| Mapa, vários | Itens marcados como erro que eram limitação, simplificação, imprecisão ou ambiguidade | Reclassificados com rótulos próprios |
| Mapa, Art. 1 (A7) | Escala 0–1 afirmada sem o artigo dizer | Marcada como não informada |
| Guia, 4.2 | "Todos os artigos com implementação usam Python": A3 usa Java e DB2 | Corrigido |
| Guia, A7 | Faltava a Dense Layer 3 depois da concatenação | Incluída |
| Guia, 5.2 e 5.3 | Proporções do C3 atribuídas a A3, onde 10/20/50% são limiares de diferença de termos | Reescrito como escolha do projeto inspirada nesses limiares |
| Guia, 3.1 e mapa | Teste do A1 falharia com o TfidfVectorizer padrão (ln(N/df) + 1, L2) e com texto bruto | Nota: usar a fórmula do artigo e os tokens das Tabelas 6–7 |
| Guia, 12 | Exigia E5 e FAISS no backend, contra 4.5 e a pendência de escopo | Condicionado ao escopo da seção 9 |
| Guia, 10 e 11 | .gitignore sem CLAUDE.md e AGENTS.md | Incluídos |
| Guia, 5.1 | Números do PAN-PC-10 e do arXiv 2404.01582 nunca conferidos | Conferidos nas fontes e citados |

O que continua dependendo de decisão, e não de conferência, está em TCC/14-pendencias.md.

## Validação das capturas do autor (21/10/2026, 18h30)

As 8 capturas (Tabelas 1 a 7 do Art. 8/A3, Algoritmos 1 e 2 e Figs. 4 a 7 do Art. 9/A5, Figs. 1 e 2 do Art. 5/A4) conferem com todos os números deste mapa. Pontos novos que só aparecem nelas:

| Artigo | Achado | Tipo |
| --- | --- | --- |
| Art. 8 (A3), Tabela 5 | Pares com Δ de termos diferente de zero (Fund1 e Fund3; Fund0 e Fund5; ct7mhna1 e ct7mhna2) têm a mesma assinatura de shingles; a assinatura de termos os separa | Conferido |
| Art. 8 (A3), Tabelas 3 e 5 | Fund2 e Fund4: Δ = 0, mas 2.198 × 2.207 termos e assinaturas de termos diferentes. O Δ é direcional (termos do 2º ausentes no 1º); a assinatura pega a diferença | Conferido |
| Art. 8 (A3), Tabela 4 | 257 e 218 termos, enquanto o texto fala em cerca de 1.300 termos por documento (provavelmente antes do filtro IQ > 0) | Ambíguo no artigo |
| Art. 9 (A5), Figs. 4 e 5 | O texto pré-processado mantém tokens de 1 e 2 letras ("k", "x", "an"), contra o filtro \|t\| > 2 descrito, e a palavra quebrada "follo wing" (quebra de linha do PDF, como a hifenização do A3) | Inconsistência |
| Art. 9 (A5), Fig. 6 | Todas as comparações do arquivo 18CSE031 ficam entre 65,71% e 71,62%: sinal de escore inflado por conteúdo comum | Fragilidade |
| Art. 5 (A4), Fig. 1 | Texto 1 começa com "How" e o Texto 2 com "The": confirma l = 0 e Jaro = Jaro-Winkler (80,09%) | Conferido |

Lição para o projeto: o parser precisa juntar palavras quebradas na linha e tratar o hífen suave antes de qualquer motor (registrar o teste em TCC/04-parsing.md).

## Decisões do autor (21/10/2026)

- Tema 4: buscar as inter-relações entre dois arquivos, obtendo o índice de correlação.
- Escopo: comparação entre dois arquivos, sem base de documentos; FAISS e métricas de recuperação (Art. 7/A2) ficam como extensão.
- Idioma e formatos: PT-BR; PDF, DOCX e TXT.
- Busca online (Art. 9/A5): trabalho futuro, só se houver tempo e sem violar termos de uso nem diretrizes.
- Next.js + Flask em monólito modular, confirmado com o orientador em paralelo.
- Dataset só sintético.

## Definições do projeto que mudam como as fórmulas são usadas

O escopo final está na seção 0 do guia; estas são as consequências para as fórmulas deste mapa.

- **IDF com dois arquivos:** com N = 2, todo termo presente nos dois tem idf = log(2/2) = 0 (o caso "bisa" do Art. 6/A1), e documentos idênticos dariam vetores nulos. No sistema, o IDF vem de um corpus de referência PT-BR congelado, com suavização:

```latex
idf(t) = \ln\frac{1 + N_{ref}}{1 + df_{ref}(t)} + 1
```

A fórmula exata do A1 (log10(N/df), sem suavização) continua nos testes de referência.

- **Unidade:** sentença. Algoritmos de caractere do Art. 5/A4 rodam nos pares de sentenças alinhados; no texto inteiro só no modo "rodar todos", com limite de tamanho.
- **Alinhamento:** matriz sentença × sentença e atribuição um a um pelo algoritmo húngaro, equivalente ao alinhamento mínimo do Art. 3/A9 (que usa programação linear).
- **Índice de correlação** (s\_ij = escore fundido entre a sentença i de A e a j de B; w\_i = tamanho da sentença):

```latex
I_{A \to B} = \frac{\sum_i w_i \max_j s_{ij}}{\sum_i w_i} \qquad I = 100 \cdot \frac{I_{A \to B} + I_{B \to A}}{2}
```

- **Assinatura (Art. 8/A3):** soma de hashes estáveis (ex.: blake2b), não hash() do Python.
- **Limiares iniciais:** 0,85 e 0,75 (Art. 2/A6) e 0,30 (Art. 9/A5), provisórios até a calibração; o 0,65 da busca online não se aplica.
