# TCC: base teórica e arquitetura do sistema de comparação de textos

*Tema 4: desenvolvimento de sistema de comparação de conteúdo de textos, com índice de correlação entre dois arquivos, engenharia do sistema e front end.* Objetivo do tema: buscar as inter-relações entre dois arquivos, obtendo o índice de correlação.

Nomenclatura usada: **A1 a A9**, na ordem da seção 1.

## 0. Escopo final (decisão de 21/10/2026)

*Esta é a lista única do que o sistema faz. Onde outra seção divergir, vale esta. Objetivo do tema: buscar as inter-relações entre dois arquivos e obter o índice de correlação.*

### 0.1 Entra

-   **Entrada:** dois arquivos por comparação (PDF com camada de texto, DOCX ou TXT) ou texto colado, em PT-BR; limite de tamanho configurável.

-   **Parsing:** pdfplumber e python-docx (o A4 usa PyMuPDF; a troca é pela licença, ver 0.4); junção de palavras quebradas no fim da linha e troca do hífen suave (0xad) \[A3; A5, Figs. 4 e 5\]; segmentação em sentenças.

-   **Pré-processamento em dois perfis:** lexical (minúsculas, ruído, stopwords, lematização, tokens com mais de 2 letras) e semântico (texto quase bruto) \[A1, A2, A5, A8\].

-   **E1 léxico:** TF-IDF + cosseno \[A1, A5, A6\] e os 7 algoritmos do A4 (Levenshtein, Damerau-Levenshtein, Jaro, Jaro-Winkler, Smith-Waterman, cosseno no modelo vetorial e n-gramas/Dice).

-   **E2 assinatura:** adaptação por termos salientes e assinatura para triagem rápida de possíveis duplicados, sem prova de identidade \[A3\].

-   **E3 semântico:** Sentence-BERT multilíngue, cosseno por sentença \[A2, A5, A6\].

-   **E4 alinhamento:** matriz sentença × sentença e alinhamento um a um pelo algoritmo húngaro, equivalente ao alinhamento mínimo de A9; é a base do mapa de calor.

-   **Siamês:** BERT em português + rede siamesa de A7, treinado no dataset sintético, com os hiperparâmetros de 4.4.

-   **Fusão e classificação:** primeiro as regras de A5 e A6 (baseline explicável); depois fusão aprendida por regressão logística sobre os escores dos motores \[A9\]. Classe por sentença: cópia exata, cópia editada, paráfrase ou original; classe do documento: a predominante, com trecho inserido quando só parte do documento é reaproveitada.

-   **Índice de correlação:** de 0 a 100 entre os dois arquivos (definição em 0.3).

-   **Aplicação:** autenticação local simples (e-mail e senha), envio, processamento, tela de resultado (6.1), seletor de algoritmo e modo \"rodar todos\" com tempo e memória \[A4\], histórico \[A6\] e exportação em PDF pela impressão do navegador.

-   **Pesquisa:** gerador e validador do dataset sintético (5.3 e 5.4), execução de experimentos por configuração, métricas da seção 6 e registro em TCC/.

-   **Engenharia:** Docker Compose com MongoDB, core e web; seeds; testes da seção 6 e 6.2, incluindo carga e segurança; README de execução local.

### 0.2 Fica de fora

-   Busca online (E5): trabalho futuro, só se houver tempo e sem violar termos de uso nem diretrizes.

-   Comparação contra uma base de documentos, FAISS e métricas de recuperação de A2 (Recall@K, MRR, MAP, nDCG): extensão futura.

-   OCR de PDF escaneado; nível de parágrafo; tradução e comparação entre idiomas; deploy.

### 0.3 Definições operacionais (para não deixar lacuna na implementação)

-   **IDF com só dois arquivos:** com N = 2, todo termo presente nos dois recebe IDF = log(2/2) = 0, como \"bisa\" no exemplo de A1, e dois documentos idênticos dariam vetores nulos. Por isso o IDF do sistema vem de um corpus de referência em PT-BR, congelado e versionado (as fontes do dataset, 5.4), com suavização para termos novos: idf = ln((1+N)/(1+df)) + 1. A fórmula exata de A1 é usada nos testes de referência, para provar a implementação.

-   **Unidade de comparação:** a sentença. Os escores de documento saem da agregação das sentenças.

-   **Índice de correlação:** para cada sentença de um arquivo, o maior escore fundido com as sentenças do outro; média ponderada pelo tamanho da sentença nos dois sentidos (A→B e B→A), média dos dois sentidos, × 100. É um índice de similaridade do sistema, distinto dos coeficientes estatísticos de Pearson e Spearman. Sua associação com o grau de reuso r do dataset (fração de sentenças derivadas do suspeito) é hipótese ainda não confirmada: simetrização e pesos por palavras impedem afirmar equivalência com essa fração direcional. r é gabarito de avaliação, nunca entrada da inferência.

-   **Limiares iniciais:** os dos artigos (0,85 e 0,75 de A6; 0,30 de A5), marcados como provisórios até a calibração na validação do dataset (5.3).

-   **Algoritmos de caractere:** rodam sobre os pares de sentenças alinhados pelo E4. No texto inteiro, só no modo \"rodar todos\", com limite de tamanho, porque Smith-Waterman é O(m·n) e levou 38,36 s no exemplo de A4.

-   **Assinatura (E2):** soma de hashes estáveis (ex.: blake2b dos termos normalizados), não hash() do Python, que muda a cada execução e quebraria a reprodutibilidade.

-   **Classes do dataset × saída do sistema:** cada sentença do suspeito recebe do gerador um rótulo de saída: cópia exata (C1, e as sentenças copiadas de C3, C4 e C7), cópia editada (C2), paráfrase (C5 e C6) ou original (C0 e as sentenças novas de C3). O tipo do documento é a própria classe C0 a C7. A avaliação mede os dois níveis: 4 classes por sentença e 8 tipos por documento.

-   **Antes do dataset existir:** siamês e fusão aprendida ficam desligados; o índice usa a fusão por regras. Nada calculado com os seeds de desenvolvimento é resultado (seção 12).

### 0.4 Plano de entrega em 5 dias (decisão de 22/10/2026)

*O prazo histórico é de 5 dias; não representa cinco dias restantes a partir da retomada. Este plano prevalece sobre a seção 12; a ordem das sessões está em docs/03-prompts-por-etapa.md. O escopo da 0.1 se mantém, com os cortes abaixo.*

-   **Dias:** 1, núcleo de cálculo (E1, E2, parsing, métricas) com testes de referência; 2, E3, E4, fusão por regras, índice, API e integração; 3, frontend integrado (com autenticação local e histórico) e testes de sistema; 4, dataset sintético completo (fluxo 5.4, com paráfrase por LLM em cache e revisão humana da amostra); 5, experimentos (siamês na GPU, fusão aprendida, calibração, ablação) e fechamento.

-   **Fica de fora (trabalho futuro):** busca online; base de documentos e FAISS; κ de Cohen (só há um revisor); OCR; nível de parágrafo.

-   **Se atrasar, cortar nesta ordem:** repetições do siamês com várias sementes; fusão aprendida (fica a fusão por regras); autenticação e histórico; versão em PDF/DOCX da amostra do dataset. Nunca cortar testes de referência, divisão por documento-fonte nem registros em TCC/.

-   **Limitações a declarar:** dataset só sintético; revisão humana feita por um único revisor; limiares calibrados num único conjunto de validação.

-   **Licença e PDF:** código sob Apache-2.0, com LICENSE oficial preservada e autoria confirmada em NOTICE. O parser escolhido é pdfplumber; referências históricas ao PyMuPDF usado pelo A4 permanecem. Licenças de dependências, dados e modelos são registradas separadamente; a escolha não constitui parecer jurídico automático de compatibilidade.

### 0.5 Integração documental do roteiro revisado — 2026-10-24

O tema permanece a comparação explicável do conteúdo de dois arquivos PT-BR. Similaridade, relações textuais e rótulos sintéticos não constituem detecção conclusiva de plágio. O contrato científico em TCC/02-metodologia.md é proposta a ratificar; hipóteses H1–H3 da seção 6 permanecem com sua redação e status anteriores, sem validação experimental ou aprovação do orientador presumida. Melhor correspondência simétrica, alinhamento um a um e r direcional são grandezas distintas.

Estado reconstruído: núcleo S1 implementado e evidências anteriores preservadas; E3/E4, fusão, índice documental, API e interface ainda não implementados. As sessões já executadas não recomeçam. O roteiro antigo foi copiado em docs/historico/; as Regras comuns de docs/03 e o roteiro recebido em docs/04 disciplinam futuras execuções, sempre limitadas ao pedido da vez.

Ambiente: preservar Python 3.11.9/lock como baseline. Python 3.11.17 é candidato separado, não promovido; sua release oficial de 01/10/2026 é de segurança, somente fontes, e a série 3.11 tem suporte de segurança previsto até outubro de 2027. Validar candidato no Windows e Docker, runtime/imports/CLI/suíte/referências, antes de alinhar seletor/imagem. Node 24 LTS é candidato para S2/S3, patch ainda a verificar; Node 20+ não é requisito suficiente de suporte. Nenhuma instalação ou migração foi feita nesta revisão documental.

Medição futura: delta RSS não é pico nem consumo exclusivo do algoritmo; zero medido não prova uso zero. tracemalloc cobre blocos rastreados pelos alocadores Python, não toda memória nativa/GPU. Definir processo, aquecimento, amostragem, unidade, ambiente e limites antes dos experimentos; não comparar medidas distintas como se fossem iguais. Teste de fumaça verifica caminho/dimensões/valores finitos/backprop/salvamento quando implementados, sem obrigação de queda da perda e sem provar aprendizagem.

Fontes oficiais consultadas nesta edição: https://www.python.org/downloads/release/python-31117/ ; https://devguide.python.org/versions/ ; https://nodejs.org/en/about/previous-releases ; https://docs.python.org/3.11/library/tracemalloc.html ; https://psutil.io/api/ . Versões observadas e limites da consulta ficam no relatório documental privado.

## 1. Mapa dos 9 artigos e seu papel no projeto

-   **A1** Halim e Lasut (2024), TF-IDF + cosseno em aplicação web. Papel: **espinha dorsal de engenharia de software** (Waterfall, ERD, DFD, teste caixa-preta) e baseline lexical.

-   **A2** Lubis et al. (2026), Sentence-BERT + FAISS em repositório acadêmico. Papel: **busca semântica e indexação vetorial**, métricas de recuperação, arquitetura em camadas.

-   **A3** Cooper, Coden e Brown (IBM, CIKM 2002), termos salientes e assinatura de documento. Papel: **detecção rápida de duplicados e de documentos revisados ou com trechos inseridos**, comparação com shingles.

-   **A4** Poljak, Crčić e Horvat (2025), comparação de 5 algoritmos (7 funções) e aplicação web. Papel: **catálogo de algoritmos léxicos**, arquitetura frontend/backend/algoritmos e benchmark de tempo e memória.

-   **A5** Setu et al. (2025), estratégia em 3 fases: cosseno TF-IDF + BERT + busca online. Papel: **algoritmo de decisão** (cópia direta, paraphrase, cópia online) e **dataset real (MIT, Kaggle)** (descartado como fonte de dados; o projeto usa só dataset sintético, 5.3).

-   **A6** Gawade et al. (2025), TF-IDF + SBERT com classificação por sentença. Papel: **regras de classificação e pontuação por sentença**, relatório e UI.

-   **A7** Sarkar et al. (2024), BERT + rede siamesa treinada. Papel: **modelo treinável de similaridade** (regressão), curadoria de dataset e métricas de regressão.

-   **A8** Afzal et al. (MayoNLP, SemEval-2016), rede semântica léxica + DSSM. Papel: **STS clássico**, pré-processamento detalhado, subconjunto *plagiarism* do SemEval como benchmark (o benchmark não é usado: só dataset sintético, 5.3).

-   **A9** Henderson et al. (MITRE, SemEval-2017), ensemble de 5 sistemas. Papel: **alinhamento de palavras, dependências, tradução automática e ensemble**.

Como se complementam: A1, A4 e A3 cobrem a camada **lexical e estrutural**; A2, A6 e A7 a camada **semântica densa**; A8 e A9 a camada **STS com alinhamento e ensemble**; A5 e A6 mostram como **fundir** tudo numa decisão; A2 mostra como **escalar** com índice vetorial.

## 2. Fichas por artigo

### A1: Document Plagiarism Detection Application Using Web-Based TF-IDF and Cosine Similarity (Bit-Tech 7(2), 2024)

-   **Problema:** ferramenta web barata para detectar plágio entre documentos, com cálculo manual mostrado passo a passo (a contribuição declarada).

-   **Método:** Waterfall em 5 etapas (requisitos, projeto, desenvolvimento, teste, manutenção); ERD; DFD (hierarquia, contexto, nível 0, nível 1); teste caixa-preta por partições de equivalência. Pré-processamento: minúsculas, remoção de ruído, stopwords (Sastrawi), tokenização e seleção de atributos. Peso w_ij = tf_ij × idf, com idf = log(N/df) (base 10 nos exemplos), e cosseno entre vetores. Stack: MySQL via XAMPP, upload só de PDF. A tela de resultado mostra % e as palavras plagiadas coloridas.

-   **Dados:** periódicos em indonésio; o exemplo manual compara 1 documento do usuário (u) com 3 da base (d1, d2, d3), logo N = 4 (Tabela 6).

-   **Resultado:** manual 4% contra aplicação 4,34%. Os 74 itens de teste caixa-preta, em 15 telas e formulários (Tabela 3), passaram. Recalculado: cos(u, d2) = 0,09062 / (1,50515 × 1,64881) = 0,0365 = 3,65%, que o artigo arredonda para 4%; a tela mostra 4,34% como maior similaridade e 1,45% como escore geral (Fig. 10).

-   **Pontos de atenção:** validação fraca (3 documentos, diferença 4% vs 4,34% usada como prova de consistência); termo presente em todos os documentos recebe IDF 0 (ex.: *bisa* no exemplo); só indonésio; os autores admitem lentidão com muitos dados e sugerem Word2Vec/BERT e multiformato; o artigo chama os dados do usuário de \"dados de treino\", mas TF-IDF + cosseno não tem treino; a legenda da Eq. 1 define n em vez de df; o exemplo de tokenização lista 5 tokens e diz 7; as datas de revisão e aceite estão como \"20xx\".

-   **Aproveitar:** estrutura do capítulo de engenharia (Waterfall, ERD, DFD), tabelas IDF/TF-IDF como **testes de regressão com valores de referência**, UI com destaque colorido. A taxonomia da revisão (verbatim, patchwork, paráfrase e plágio de palavras-chave/frases) é a base das classes do dataset sintético (5.3).

### A2: Semantic Search in an Academic Repository Using Sentence-BERT and FAISS (Sinkron 10(2), 2026)

-   **Problema:** busca por palavra-chave falha quando a consulta usa termos diferentes do documento.

-   **Método:** MySQL guarda 100 documentos administrativos em indonésio; limpeza de HTML; Sentence-BERT com **pooling por média** (u = (1/n) Σ h_i); índice FAISS IndexFlatL2 (busca exata, distância euclidiana); backend FastAPI (indexação, busca, avaliação); frontend CodeIgniter 4 (4 páginas: documentos, modelo, dados de avaliação, busca). Arquitetura em 3 camadas: aplicação, modelo e API.

-   **Avaliação:** 3 conjuntos de 10 consultas, top-K = 10, relevância binária rotulada manualmente.

    -   Recall@K: 0,55 / 0,667 / 0,60 (média 0,61)

    -   nDCG@K: 0,409 / 0,44 / 0,376

    -   MRR: 0,575 / 0,381 / 0,418

    -   MAP: 0,45 / 0,381 / 0,341 (média 0,39)

    -   No-hit: 0,10 / 0 / 0

    -   Latência p50 ≈ 0,3 ms, p99 \< 0,5 ms; embeddings das consultas: 118 a 132 ms por conjunto

-   **Pontos de atenção:** corpus pequeno (100 documentos), então latência baixa não prova escala; os próprios autores dizem que o ranking é fraco (nDCG moderado) e sugerem híbrido ou re-ranking; distância L2 sobre vetores não normalizados; o resumo diz que todas as consultas tiveram resultado, mas o No-Hit de 0,033 indica 1 de 30 sem relevante (a conclusão diz \"a maioria\"); o tempo de embedding é o total de 10 consultas (≈ 12,5 ms por consulta); na Tabela 2 a consulta sobre junho de 2025 tem como relevante um documento de junho de 2024.

-   **Aproveitar:** **todo o conjunto de métricas de recuperação**, o desenho de API (index, search, evaluate), o esquema de tabelas de avaliação (eval_sets, eval_relevants) e a ideia de página administrativa para reindexar.

### A3: Detecting Similar Documents Using Salient Terms (IBM, CIKM 2002)

-   **Problema:** resultados de busca trazem quase-duplicatas; como detectar sem comparar texto inteiro.

-   **Método:** sistema Talent, com o extrator Textract (termos multi-palavra e nomes próprios, formas canônicas, abreviações). Cada termo tem um **IQ** (*Information Quotient*): seletividade do termo na coleção. Termos e IQ são carregados em DB2 e a similaridade é uma **consulta SQL** que conta termos de um documento ausentes no outro. Compara com **shingles** de Broder (janela de 10 palavras, hash, amostragem por módulo e menores valores).

-   **Regras e limiares:** documentos com tamanho dentro de \~10% e menos de 10% dos termos diferentes = muito similares; com texto inserido, relaxa-se para 50%; abaixo de 20% de termos diferentes = relacionados. **Assinatura do documento** = soma dos hashes dos termos salientes.

-   **Experimentos:** consulta 1 (36 documentos, 6 clusters, versões de um manual do WebSphere e rascunho vs. versão final de um paper) e consulta 2 (47 documentos, 13 muito similares; 6 com assinatura idêntica apesar de 4 tamanhos diferentes). Na inserção de uma notícia de 2.533 bytes em 12 documentos, o método de termos teve precisão e recall de 100%, contra recall abaixo de 50% dos shingles.

-   **Pontos de atenção:** é de 2002 e usa ferramenta proprietária; a assinatura por soma de hashes **ignora ordem** (os autores citam o risco de um \"not\" inverter a conclusão); a fórmula do IQ não aparece no texto; o módulo da amostragem de shingles é 25 (conferido nas imagens das seções 4 e 9.1; não existe 250); o PDF não traz DOI; na Tabela 5, pares com Δ de termos diferente de zero (Fund1 e Fund3; Fund0 e Fund5; ct7mhna1 e ct7mhna2) têm a mesma assinatura de shingles, e Fund2 e Fund4 têm Δ = 0 mas assinaturas de termos diferentes, porque o Δ é direcional; a Tabela 4 conta 257 e 218 termos, enquanto o texto fala em cerca de 1.300 termos por documento (provavelmente antes do filtro IQ \> 0).

-   **Aproveitar:** o conceito de **termos-chave como representação comprimida**, a comparação com shingles e a assinatura para **triagem rápida de duplicados**. Textract pode ser substituído por extração de palavras-chave/sintagmas nominais em Python.

### A4: Comparative Analysis of Text Similarity Algorithms (Elektrotehniški vestnik 92(3), 2025)

-   **Problema:** escolher o algoritmo certo conforme o tipo de texto.

-   **Algoritmos (5 famílias, 7 funções):** Levenshtein, Damerau-Levenshtein, Jaro, Jaro-Winkler, Smith-Waterman (alinhamento local), cosseno no modelo vetorial e similaridade de n-gramas (coeficiente de Dice sobre n-gramas).

-   **Aplicação web:** 3 módulos (frontend, backend, algoritmos). Frontend em HTML, CSS, JavaScript, jQuery e Bootstrap; backend Flask; PyMuPDF extrai texto de 2 PDFs; psutil mede **tempo e memória** de cada algoritmo. O usuário escolhe um algoritmo no dropdown ou roda todos, e vê uma tabela com similaridade (%), tempo (s) e memória (bytes).

-   **Teste:** 5 cenários; textos simples 93%, formatação diferente 89%, erros gramaticais 76%, textos diferentes 12%, textos longos 40%.

-   **Pontos de atenção:** é artigo de revisão, com teste qualitativo (sem corpus anotado nem métrica de acurácia); métodos de caractere custam O(m·n) e não capturam semântica; a seção de trabalhos relacionados cita abordagens híbridas, aspect-based e CBR, que ficam como leitura extra; Jaro e Jaro-Winkler deram o mesmo 80,09% porque os dois textos não têm prefixo comum (l = 0); a Eq. 2 escreve \"Longest word length\" onde o correto é o comprimento da maior string; há duas figuras numeradas \"Figure 1\" e o texto cita uma \"Fig. 3\" que não existe.

-   **Aproveitar:** o **catálogo de algoritmos**, o seletor de algoritmo, o **benchmark de desempenho no próprio front end** e o upload de dois PDFs.

### A5: A comprehensive strategy for identifying plagiarism in academic submissions (J. Umm Al-Qura Univ. 2025)

-   **Problema:** detectar cópia direta, paraphrase e cópia online com ferramenta gratuita.

-   **Algoritmo 1 (integridade acadêmica):** calcula S = max(cosseno TF-IDF, similaridade BERT). Se S \> 30%: se o cosseno for maior, **cópia direta**; se BERT for maior, **paraphrase**. Se S ≤ 30%, vai para a busca online.

-   **Algoritmo 2 (similaridade com a internet):** gera consultas, usa o pacote googlesearch, extrai páginas com BeautifulSoup, calcula TF-IDF + cosseno linha a linha; linha com similaridade ≥ 65% é marcada como copiada e as fontes são listadas.

-   **Fase 1 (dados):** entregas em PDF, PPTX, DOCX e TXT convertidas para texto; pares únicos C(n,2), com n = 100 gerando **4.950** pares em CSV; validação no **MIT Plagiarism Detection Dataset (Kaggle), 367.375 amostras**. Pré-processamento em 9 passos (Fig. 2 e seção 3.1.3): carregar o dataset, tokenizar, limpar (pontuação, não alfabéticos, minúsculas), remover stopwords, lematizar, POS tagging, filtrar tokens com \|t\| \> 2, reagrupar a frase e vetorizar por TF-IDF; separação 80/20 (990 pares de teste = 20% de 4.950).

-   **Fase 2:** cosseno TF-IDF e BERT: Sentence Transformer all-MiniLM-L6-v2 e bert-base-uncased com 2 classes, softmax como probabilidade de paraphrase, AdamW com taxa de aprendizado 1e-5; limiar ótimo 0,3.

-   **Resultados:** base privada: precisão 62%, recall 93%, acurácia 64%, F1 74%. MIT: precisão 68%, recall 80%, acurácia 71%, F1 74%. Online (limiar de 65% no Algoritmo 2; o resumo diz 0,2): precisão 65%, recall 56%, acurácia 60%, F1 60%. Tempo de treino: cópia direta 6,11 s, semântica 68,21 s; teste: 1,55 s e 14,25 s. Recalculado das matrizes (Figs. 9 e 10): privado TN 117, FP 318, FN 37, TP 518; MIT TN 11.443, FP 6.863, FN 3.715, TP 14.716 (36.737 = 10% de 367.375); online TN 300, FP 160, FN 240, TP 300. Todos conferem com os percentuais.

-   **Pontos de atenção:** na discussão (p. 323) o MIT aparece com precisão 62% e recall 79%, mas o resumo e a matriz (14.716 TP, 6.863 FP, 3.715 FN) dão 68,2% e 79,8%; a Eq. 2 do TF-IDF está impressa com \"+\" no próprio artigo (conferido na imagem; o texto manda multiplicar, use ×); o Algoritmo 1 usa Threshold_Textual sem defini-lo; há dois modelos BERT (all-MiniLM-L6-v2 e bert-base-uncased) sem dizer qual entra no máximo; não fica claro em que dados o BERT foi ajustado; a busca online por googlesearch é frágil e a base privada é inacessível; nas Figs. 4 e 5, o texto pré-processado ainda tem tokens de 1 e 2 letras (\"k\", \"x\", \"an\"), contra o filtro \|t\| \> 2 descrito, e mantém a palavra quebrada \"follo wing\" (quebra de linha do PDF, o mesmo problema de hifenização de A3); na Fig. 6, todas as comparações do arquivo 18CSE031 ficam entre 65,71% e 71,62%, o que sugere escore inflado por conteúdo comum.

-   **Aproveitar:** **o desenho em 3 fases e a árvore de decisão**, o dataset MIT e as métricas.

### A6: Semantic-Aware Plagiarism Detection Using Machine Learning (ICSSSM 2025)

-   **Problema:** ferramentas lexicais perdem texto parafraseado.

-   **Método:** pré-processamento (minúsculas, espaços, stopwords, pontuação, tokenização de sentenças com nltk ou spaCy); **TF-IDF + cosseno** por sentença; **SBERT** (Hugging Face) por sentença, com cosseno. **Classificação por sentença:** *Exact Copy* se cosseno TF-IDF \> 0,85; *Paraphrased* se SBERT \> 0,75 com TF-IDF baixo; senão *Original*. **Pontuação final:** 60% SBERT + 40% TF-IDF. Limiares estimados em piloto com 50 pares e refinados por **curva ROC**.

-   **Dados:** 200 trabalhos (70 cópia exata, 80 paraphrase, 50 originais), rotulados manualmente.

-   **Resultados:** Exact P 0,95, R 0,93, F1 0,94; Paraphrased P 0,87, R 0,84, F1 0,85; Original P 0,92, R 0,94, F1 0,93; acurácia geral 92%.

-   **Stack:** Flask, HTML, CSS, JavaScript, Bootstrap, SQLite (login e histórico). Trabalhos futuros: relatório em PDF, dashboard, painel admin, multilíngue, sugestões de paráfrase.

-   **Pontos de atenção:** dataset pequeno e próprio; o texto cita um estudo de ablação mas **não mostra os números**; o modelo SBERT usado não é especificado; os limiares dependem desse modelo; o artigo chama F1 de \"média\" (a fórmula é a média harmônica); a Fig. 3 é uma ROC com AUC = 1,00 em dados usados para ajustar os limiares, e o texto a descreve como acurácia × limiar; \"F1 acima de 0,85 em todas as classes\", mas Paraphrased = 0,85; as citações da revisão têm numeração trocada (ex.: \"Ivanov et al. \[13\]\" é Kuksa & Polyakov). Recálculo ilustrativo: ponderar os valores 95/88/93 pelos suportes 70/80/50 resulta em 91,7%; isso não reconstrói nem confirma a acurácia geral de 92% publicada. Faltam denominadores por classe e matriz que justifiquem essa equivalência (A6, PDF 8–9 / pp. 351–352).

-   **Aproveitar:** **a classificação por sentença em 3 classes**, o relatório (originalidade geral + lista por tipo) e a revisão de literatura (LSA, SVM, Random Forest, RNN, OCR, LSH, detecção de texto gerado por IA).

### A7: Evaluating Semantic Similarity in Research Papers via Siamese BERT (EasyChair Preprint 15448, 2024)

-   **Problema:** achar artigos parecidos com um dado, indo além de palavra-chave e cosseno simples.

-   **Curadoria do dataset:** ACL Anthology (Hugging Face WINGNUS/ACL-OCL); remove ausentes e duplicatas; mantém campos (acl_id, abstract, title, year etc.); abstract vira original; cria paraphrased e similarity_score com **gemini-pro**. Resultado: **10.072 resumos**.

-   **Arquitetura (7 blocos):** tokenizador → modelo transformer (BERT) → pooling (média ou máximo) → Sentence Transformer → Linear + LayerNorm + LeakyReLU + Dropout → concatenação dos dois ramos → Dense Layer 3 → score de similaridade (saída Q da Fig. 1).

-   **Hiperparâmetros:** 8 épocas, taxa 2e-6, Adam, tamanho máximo 212, weight decay 1e-5, **MSELoss**; treino em GPU P100.

-   **Resultados:** perda 0,0010; MAE 0,0209; MSE 0,0010; R² 0,7067; Pearson 0,8706; Spearman 0,6564; teste 23 s.

-   **Experimental Setup:** login, entrada de texto ou imagem de resumo transcrita, dois servidores: o primeiro, ligado ao front Next.js, faz a autenticação e repassa a consulta a um servidor Flask, que consulta o MongoDB (detalhes e embeddings) e calcula o cosseno; aplicação desenvolvida em Next.js, Node.js, TypeScript e Tailwind CSS; treino em GPU P100; desenvolvimento em Asus Vivobook 16 (16 GB, Ryzen 7 5800HS) e Asus F Dash 15 (16 GB, Intel i5 12500H); dependências (13): Flask, numpy, pandas, google-generativeai, pymongo, sentence_transformers, torch, tqdm, transformers, bert_score, datasets, scipy, scikit-learn.

-   **Pontos de atenção:** as **etiquetas de similaridade foram geradas por LLM**, o que introduz ruído e viés circular; Pearson alto com Spearman bem menor sugere ordenação fraca; a Tabela 3 mostra só 3 exemplos; domínio restrito a resumos de NLP; não informa divisão treino/teste, tamanho de lote, α da LeakyReLU, p do dropout, dimensões das camadas densas nem a variante do BERT; só gera pares parafraseados (similares), embora a arquitetura cite \"Similar/Dissimilar\"; a Seção 5 chama o BERT de \"encoder-decoder\" (é só encoder); as referências \[10\] e \[19\] são a mesma.

-   **Aproveitar:** receita de **curadoria de dataset**, arquitetura siamesa, métricas de regressão, esqueleto de sistema.

### A8: MayoNLP at SemEval-2016 Task 1 (rede semântica léxica + deep learning)

-   **Tarefa:** pares de frases com nota 0 a 5; avaliação por correlação de Pearson.

-   **Dados:** STS 2016 com 5 conjuntos: *answer-answer* (254 pares), *headlines* (249), ***plagiarism* (230)**, *postediting* (244), *question-question* (209).

-   **Pré-processamento (fluxo da Fig. 1):** expandir contrações, remover URLs, e-mails e parênteses, normalizar abreviações via WordNet e lista manual, trocar negações por antônimos, corrigir ortografia (pyenchant), remover stopwords (exceto em *answer-answer* e *question-question*, onde há pares só de stopwords) e lematizar com NLTK.

-   **Run 1 (rede semântica):** vetor de palavras conjunto (JWV); similaridade semântica e sintática combinadas com Ω = 0,85; similaridade entre palavras pelo WordNet com α = 0,2 e β = 0,45, limiar 0,2; conteúdo de informação pelo corpus Brown.

-   **Run 2 (DSSM):** *word hashing* em trigramas de letras (3.073 dimensões), 1 camada oculta de 1.000 nós, ativação tanh, cosseno mapeado para 0 a 5 (via Sent2Vec).

-   **Run 3:** média simples das duas (0,5 + 0,5).

-   **Resultados (Pearson, STS 2016):**

    -   *plagiarism:* 0,769 / 0,801 / **0,805** (melhor da competição: 0,841)

    -   média ponderada: 0,726 / 0,736 / **0,756** (melhor: 0,778)

    -   STS 2015, média ponderada: 0,760 / 0,754 / 0,772

-   **Pontos de atenção:** inglês e frases curtas; pesos heurísticos; a fórmula do WordNet está impressa com e\^(α·l), sem o sinal de menos (conferido na imagem; correto e\^(−α·l), seção 3.6); o artigo diz que os vetores do DSSM são não negativos, mas usa tanh; não diz como o Run 1 é levado à escala 0--5 antes da média com o Run 2; código citado no artigo: github.com/naveedafzal/MayoClinic_SemEval_2016_Task-1.

-   **Aproveitar:** pré-processamento defensável (e o aviso de **não remover stopwords em textos curtos**), o **benchmark público *plagiarism*** e o princípio de combinar abordagem léxica e neural (o benchmark plagiarism não é usado: só dataset sintético, 5.3).

### A9: MITRE at SemEval-2017 Task 1: Simple Semantic Similarity

-   **Tarefa:** STS em inglês, árabe, espanhol e turco, 1.750 pares em 6 trilhas (monolinguais e cruzadas); legendas de imagem do corpus SNLI.

-   **Visão geral (§3):** ensemble de 5 sistemas que compartilham embeddings, traduções, alinhamentos e árvores de dependência.

    -   **Embeddings:** word2vec skip-gram de 256 dimensões, treinado na Wikipédia inglesa (vocabulário de 630.902 itens, janela 10, 15 amostras negativas, word2phrase aplicado 2 vezes).

    -   **Tradução automática:** tudo é traduzido para inglês pelo Google Translate (jan/2017), justificado por um modelo de linguagem com perplexidade 18,9 em SNLI contra 114,5 no Penn Treebank (vocabulário simples).

    -   **Dependências:** Stanford Parser (PCFG, dependências básicas, uma aresta por token).

    -   **Alinhamento:** alinhamento mínimo e máximo que maximizam a soma de 1 + cos entre vetores de palavras, resolvido com lp_solve; para arestas de dependência, sim(a1,a2) = sim(head) + 10·sim(dep).

-   **Componentes do ensemble:** TakeLab (SVR com kernel RBF: C=20, γ=0,2, ε=0,5); RNN/CRNN (RNN de 16 dimensões + 3 CRNNs com 256 filtros 1D e LSTM de 128, passos de 400 dimensões, sequência de 60, Adam, 8 instâncias); Paris (22 métricas de string × 2 caixas × 2 níveis × 2 direções = 176, + log = **352 atributos**, regressão logística L1; inclui BLEU, WER, ROUGE e métricas globais e locais de alinhamento); alinhamento simples (16 atributos, regressão logística L2); EBIM (BiLSTM + atenção sem parâmetros + LSTM de inferência, perda MSE). Pesos do ensemble por regressão logística L2.

-   **Dados:** 6.898 pares de treino (2012-2014 e 2016), 400 de desenvolvimento e 350 de ajuste fino.

-   **Resultados:** 0,659 oficial (0,669 corrigido); por trilha, de 0,16 (ES-EN news) a 0,83 (EN-EN corrigido). A ablação mostra que o alinhamento deveria ter sido removido (teste 0,6687 → 0,6722).

-   **Pontos de atenção:** ganho modesto (de 0,650, o TakeLab isolado, para 0,672, o ensemble sem o Align) com custo grande; legendas de imagem têm pouca complexidade linguística; o desempenho multilíngue depende da qualidade da tradução; um erro de arquivo reduziu a nota oficial.

-   **Aproveitar:** o conceito de **ensemble ponderado**, o uso de **tradução para comparação multilíngue**, o alinhamento palavra a palavra para **explicar** a similaridade (mapa de calor) e a lição de que combinar modelos exige ablação. O Apêndice A traz as matrizes de alinhamento mínimo (sim = 1 + cos, de 0 a 2, com o par alinhado destacado) para pares com nota 5,0, 2,6 e 0,0: é o modelo direto do mapa de calor da tela de resultados (6.1). O resumo diz \"linear regression\", mas o método (3.6) usa regressão logística L2.

## 3. Compêndio de fórmulas e cálculos

Convenção: **\[Ax\]** = o artigo traz a fórmula ou o cálculo; **(reconstruída)** = a extração do PDF veio corrompida e escrevi a forma padrão da literatura, que você deve conferir no PDF (na revisão de 21/10/2026 todas foram conferidas nas imagens; ver seção 13); **(padrão)** = definição clássica que os artigos usam ou citam sem escrever.

### 3.1 Representação lexical

-   **Frequência de termo e IDF \[A1\]:** tf(t,d) = nº de ocorrências de t em d; idf(t) = log10(N / df(t)), com N = nº de documentos e df = nº de documentos que contêm t. Exemplo de A1 (Tabela 6): N = 4 (u, d1, d2, d3); df = 1 dá log10(4) = 0,60206 e df = 2 dá log10(2) = 0,30103. No exemplo didático (Tabelas 4 e 5, N = 2), df = N dá 0 (termo bisa).

-   **Peso TF-IDF \[A1, A5\]:** w(t,d) = tf(t,d) × idf(t). A5 usa logaritmo natural, ln(N/df) (a Eq. 2 de A5 está impressa com \"+\"; o correto é ×); escolha uma base e mantenha em todo o sistema. Variante suavizada usada em bibliotecas (padrão): idf = ln((1+N)/(1+df)) + 1. Atenção: o TfidfVectorizer do scikit-learn usa idf = ln(N/df) + 1 mesmo com smooth_idf=False e normaliza os vetores por L2; para reproduzir os valores de A1, implementar a fórmula do artigo.

-   **Cosseno \[A1, A4, A5; A6 usa sem escrever a fórmula\]:** cos(A,B) = (A·B) / (‖A‖·‖B‖) = Σ A_i B_i / (√ΣA_i² · √ΣB_i²). Com pesos TF-IDF (não negativos) o resultado fica em \[0, 1\]; A5 converte para percentual.

-   **Nº de pares \[A5\]:** C(n,2) = n! / (2!(n−2)!) = n(n−1)/2. Com n = 100 são 4.950 pares; com n = 1.000 são 499.500. Isso é o argumento para recuperar candidatos antes de comparar (seção 4).

### 3.2 Algoritmos de string \[A4\]

-   **Levenshtein:** lev(i,j) = max(i,j) se min(i,j) = 0; senão min{ lev(i−1,j)+1, lev(i,j−1)+1, lev(i−1,j−1)+1\[a_i ≠ b_j\] }. Similaridade 1 − lev(a,b)/max(\|a\|,\|b\|) (A4, Eq. 2, escreve \"Longest word length\"). Custo O(m·n).

-   **Damerau-Levenshtein:** acrescenta a transposição de caracteres adjacentes como quarta operação. A implementação atual é OSA, variante restrita; A4 não confirma essa restrição nem fornece recorrência para ela. Não equivale automaticamente à distância irrestrita (A4, PDF 2 / p. 152).

-   **Jaro \[A4, Eq. 3; a janela e a definição de t são padrão, o artigo não as dá\]:** sim_j = 0 se m = 0; senão (1/3)·( m/\|s1\| + m/\|s2\| + (m−t)/m ), com m = caracteres casados dentro da janela ⌊max(\|s1\|,\|s2\|)/2⌋ − 1 e t = metade das transposições.

-   **Jaro-Winkler \[A4, Eq. 4; l e p não são definidos no artigo\]:** sim_w = sim_j + l·p·(1 − sim_j), com l = tamanho do prefixo comum (máx. 4) e p = 0,1 (valores clássicos).

-   **Smith-Waterman (alinhamento local) \[A4, Eq. 5; o artigo dá só a recorrência, sem inicialização, pontuações nem normalização\]:** H(i,0) = H(0,j) = 0 e H(i,j) = max{ 0, H(i−1,j−1) + s(a_i,b_j), H(i−1,j) − gap, H(i,j−1) − gap }; a pontuação é o máximo de H. Custo O(m·n).

-   **Similaridade de n-gramas \[A4\]:** Sim = 2·\|X ∩ Y\| / (\|X\| + \|Y\|), onde X e Y são os conjuntos de n-gramas (de caracteres ou palavras) dos dois textos.

### 3.3 Impressão digital e termos salientes \[A3\]

-   **Shingles (Broder, \[A3\]):** janela deslizante de 10 palavras, hash de cada janela, descarte dos duplicados e amostragem por múltiplo de 25 (s mod 25 = 0) (ou os 400 menores valores). Semelhança por interseção de conjuntos; forma clássica (padrão): \|S(A) ∩ S(B)\| / \|S(A) ∪ S(B)\|. Contenção (padrão): \|S(A) ∩ S(B)\| / \|S(A)\|, útil para trecho inserido em documento maior.

-   **Diferença de termos \[A3\]:** d(A,B) = \|T_B \\ T_A\| / \|T_menor\|, onde T são os termos salientes (IQ \> 0, excluindo palavras desconhecidas). A prosa e o SQL da p. 247 divergem na direção; a p. 250 usa os termos do documento menor por tamanho documental, cuja unidade/etapa não é explicitada. A expressão mostra a interpretação da prosa, não uma definição inequívoca; conferir TCC/03 e 14. Regras: duplicado se d \< 10% com tamanhos próximos; com texto embutido, d \< 50%; \"relacionados\" se d \< 20%.

-   **Assinatura \[A3\]:** sig(D) = Σ hash(t) para t nos termos salientes de D. A igualdade de assinatura serve apenas como triagem e não prova identidade textual, pois ignora ordem e admite colisões. E2 atual adapta o A3: top-30 TF-IDF e blake2b de 64 bits com soma modular sobre conjunto; não reproduz Textract/IQ e não transforma o inteiro do hash em escore de similaridade.

### 3.4 Embeddings, índice e recuperação \[A2, A6, A7\]

-   **BERT por token \[A2\]:** h_i = BERT(w_i). **Pooling:** u = f(h_1..h_n), com média u = (1/n) Σ h_i (A7 também cita máximo).

-   **Distância L2 no FAISS \[A2\]:** d(x_q, x_i) = ‖x_q − x_i‖₂. Para vetores normalizados, d² = 2 − 2·cos, então o ranking é o mesmo do cosseno; normalizar os vetores e usar produto interno é equivalente e mais interpretável (recomendação minha, padrão).

-   **Camadas da rede siamesa \[A7\]:** y = x·Aᵀ + b (linear); x̂ = (x − μ) / √(σ² + ε) (LayerNorm); f(x) = x se x ≥ 0, αx se x \< 0 (LeakyReLU); Dropout(x) = x · Bernoulli(p).

-   **Probabilidade de paráfrase \[A5\]:** p = softmax(logits)\[classe paráfrase\] do bert-base-uncased com 2 classes.

### 3.5 Regras de decisão e fusão

-   **A5, fase 2:** S = max(cos_TFIDF, p_BERT). Se S \> 0,30: cos_TFIDF \> p_BERT ⇒ cópia direta; p_BERT \> cos_TFIDF ⇒ paráfrase (empate não definido no artigo; Threshold_Textual do Algoritmo 1 também não). Se S ≤ 0,30: vai para a busca online.

-   **A5, fase 3:** para cada linha, cos_TFIDF(linha, página) ≥ 0,65 ⇒ copiada. O percentual online é P = total_copy / total_lines × 100 (Algoritmo 2, linha 22); o documento é marcado como copiado de fonte online se P ≥ 65 (linha 23, mesmo limiar das linhas).

-   **A6, por sentença:** *Exact Copy* se cos_TFIDF \> 0,85; *Paraphrased* se cos_SBERT \> 0,75 e cos_TFIDF baixo; *Original* caso contrário. **Pontuação:** score = 0,60·cos_SBERT + 0,40·cos_TFIDF.

-   **A8, run 3 e A9, ensemble:** S = α·S1 + β·S2 com α = β = 0,5 (A8, pesos heurísticos); em A9 os pesos vêm de regressão logística L2 sobre as saídas dos 5 sistemas. A8 não diz como o Run 1 é levado à escala 0--5 do Run 2 antes da média.

### 3.6 STS clássico \[A8, A9\]

-   **Conteúdo de informação (Resnik, \[A8\]):** I(w) = 1 − log(n+1) / log(N+1), com N = nº de palavras no corpus Brown e n = frequência de w.

-   **Similaridade de palavras no WordNet \[A8; o artigo imprime e\^(α·l), sem o menos; a forma correta, de Li et al., é\]:** s(w_i,w_j) = e\^(−α·l) · (e\^(β·h) − e\^(−β·h)) / (e\^(β·h) + e\^(−β·h)), com l = menor caminho, h = profundidade, α = 0,2, β = 0,45; valores abaixo de 0,2 viram 0.

-   **Vetor semântico:** entrada = 1 se a palavra está na frase, senão a maior s com as palavras da frase, ponderada por I(w); S_sem = cosseno dos dois vetores.

-   **Vetor sintático (ordem das palavras) \[A8\]:** S_syn = 1 − ‖o1 − o2‖ / ‖o1 + o2‖. **Final:** S = Ω·S_sem + (1−Ω)·S_syn com Ω = 0,85.

-   **DSSM \[A8\]:** l_1 = W_1·x; l_i = f(W_i·l\_(i−1) + b_i); y = f(W_N·l\_(N−1) + b_N), com f = tanh; entrada por trigramas de letras (#girl# → #gi, gir, irl, rl#), 3.073 dimensões. Cosseno mapeado linearmente para \[0, 5\].

-   **Alinhamento \[A9\]:** sim(w_i,w_j) = 1 + cos(w_i,w_j); alinhamento mínimo e máximo por programação linear (lp_solve); arestas de dependência sim(a1,a2) = sim(head1,head2) + 10·sim(dep1,dep2).

-   **Atributos do componente Paris \[A9\]:** 22 métricas × 2 (caixa) × 2 (palavras ou caracteres) × 2 (direção) = 176; + log de cada = 352.

### 3.7 Métricas de avaliação

-   **Regressão \[A7, A8, A9\]:** MSE = (1/n) Σ (y_i − ŷ_i)²; MAE = (1/n) Σ \|y_i − ŷ_i\|; R² = 1 − SS_res/SS_tot (padrão); Pearson r e Spearman ρ entre predição e nota humana.

-   **Classificação \[A6\]:** Precisão = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2·P·R/(P+R); Acurácia = (TP+TN)/(TP+FP+TN+FN).

-   **Recuperação \[A2\], definições padrão:** Recall@K = \|relevantes ∩ top-K\| / \|relevantes\|; MRR = (1/\|Q\|) Σ 1/rank_i; AP = (1/\|R\|) Σ_k P@k · rel_k e MAP = média de AP; DCG@K = Σ rel_i / log2(i+1) e nDCG@K = DCG/IDCG; *No-Hit Rate* = fração de consultas sem nenhum relevante; latência p50, p95 e p99.

-   **Eficiência \[A4\]:** tempo de execução (s) e memória (bytes) por algoritmo; **\[A5\]** tempo de treino e teste por componente.

### 3.8 Checklist de cobertura dos termos que você listou

-   **BERT, text embedding, Sentence-BERT (S-BERT):** A2 (seção Text Embedding Model), A5 (fase 2), A6 (3.3), A7 (3.3).

-   **Cálculo e fórmulas:** seção 3 deste documento.

-   **Modelo de arquitetura, Model Creation, Experimental Setup, Dataset Curation, MSE:** A7 (3.2, 3.4, 4, 5).

-   **System Description, Preprocessing, Data, Run, Evaluation, Performance on STS:** A8 (seções 2 e 3, 3.1).

-   **Dependency Parses, 3 System Overview, Machine Translation, Ensemble Components:** A9 (3, 3.2, 3.3, 3.5).

-   **Algorithm for detecting Academic Integrity, Third phase, Determine the Internet\'s Text Similarity:** A5 (Algoritmos 1 e 2, 3.3).

-   **Dataset real tratado (MIT, Kaggle), Data preprocessing, 3.1.4 Training and testing, Second phase:** A5 (3.1.2, 3.1.3, 3.1.4, 3.2).

-   **Text Similarity Algorithms, Web Application, Application architecture diagram, User interface, Application Testing:** A4 (3, 4, 4.1, 4.2, 4.3); A1 tem o teste caixa-preta.

-   **Duplicate or similar documents, Talent text mining system, Textract, Detecting identical documents, Query 2, Finding similar documents:** A3 (seções 3, 2, 2.1, 6, 7, 8).

-   **Vector Indexing and Search (FAISS), System Architecture:** A2 (Vector Indexing, System Architecture); A4 e A6 também descrevem arquitetura.

-   **Literature Review:** A1 (II), A4 (2), A5 (2), A6 (2), A7 (2).

-   **Similarity Detection using TF-IDF, SBERT, Plagiarism Classification Logic, Scoring at the Sentence Level:** A6 (3.2 a 3.5).

## 4. Arquitetura proposta (engenharia do sistema)

*Esta seção é recomendação minha, construída sobre o que os artigos mostram. Onde algo vem de um artigo, indico \[Ax\].*

### 4.1 Pipeline em 5 estágios

1.  **Ingestão:** upload de PDF, DOCX, TXT (e texto colado). pdfplumber para PDF (o A4 usa PyMuPDF; a troca é pela licença Apache-2.0 do código, ver 0.4); conversão de tudo para texto puro \[A5\]; OCR fora do escopo: PDF sem camada de texto é recusado com mensagem clara (A6 cita OCR na revisão). Detecção de idioma com aviso quando o texto não for PT-BR. Juntar palavras quebradas no fim da linha (A5, Figs. 4 e 5). Cuidado com hifenização e *soft hyphens* de PDF, que derrubam métodos por janela de palavras \[A3\].

2.  **Pré-processamento com dois perfis:**

    -   **Perfil lexical:** minúsculas, remoção de ruído e stopwords, tokenização, lematização, POS, descartar tokens com menos de 3 letras \[A1, A5, A8\].

    -   **Perfil semântico:** texto quase bruto (só limpeza de marcação), porque modelos de embedding usam o contexto; A2 só remove HTML e caracteres especiais e normaliza, e A8 mantém stopwords quando as frases são curtas.

3.  **Motores de similaridade (rodam em paralelo):**

    -   **E1 lexical e estrutural:** TF-IDF + cosseno \[A1, A5, A6\]; n-gramas/Dice, shingles e contenção \[A3, A4\]; Levenshtein, Jaro-Winkler e Smith-Waterman para trechos e erros de digitação \[A4\].

    -   **E2 termos salientes:** extração de palavras-chave e sintagmas (substitui o Textract) e assinatura do documento para triagem rápida de duplicados \[A3\]. Entra (seção 0): termos salientes = top-k termos por TF-IDF com IDF do corpus de referência, e assinatura = soma de hashes estáveis (não usar hash() do Python, que muda a cada execução).

    -   **E3 semântico denso:** Sentence-BERT multilíngue + cosseno por sentença \[A5, A6\]. O ajuste fino siamês \[A7\] entra (seção 0). FAISS fica fora (comparação entre dois arquivos).

    -   **E4 alinhamento (entra; seção 0):** alinhar palavras ou sentenças por similaridade de embeddings e gerar um mapa de calor explicável \[A9\]. Em vez de programação linear (lp_solve), dá para usar o algoritmo húngaro (scipy.optimize.linear_sum_assignment).

    -   **E5 online (fora do escopo; trabalho futuro, seção 9):** gerar consultas, buscar, extrair a página e comparar linha a linha \[A5\]. O pacote googlesearch é frágil e pode violar termos de uso; prefira uma API oficial de busca e verifique custo e disponibilidade atuais.

4.  **Fusão e classificação:** começar pelas **regras** de A5 e A6 (baseline de regras explicitadas, a validar); depois um **modelo de fusão aprendido** (regressão logística ou gradient boosting sobre as pontuações dos motores), seguindo a ideia de ensemble de A9. Saída: índice de correlação de 0 a 100, em 2 níveis (documento e sentença; parágrafo fica fora) e rótulo do tipo (cópia exata, trecho inserido, paráfrase, original).

5.  **Relatório e front end:** nota geral; sentenças coloridas por tipo \[A1, A6\]; seletor de algoritmo e modo \"rodar todos\" com tabela de tempo e memória \[A4\]; histórico e painel \[A6\]; exportar PDF pela impressão do navegador (entra; A6 cita como trabalho futuro).

### 4.2 Escolhas de plataforma e justificativa

-   **Linguagem:** Python no motor de ML. Os artigos recentes com implementação usam Python (A1 com Sastrawi, A2 com FastAPI, A4 e A6 com Flask, A5 com scikit-learn e transformers, A7 com PyTorch); A3 (2002) usa Java e DB2.

-   **\[Superado pela decisão 4.4\] Backend:** **FastAPI** (A2) em vez de Flask (A4, A6, A7): tipagem, documentação OpenAPI automática e assíncrono, úteis para uma API com endpoints de indexar, comparar e avaliar.

-   **\[Superado pela decisão 4.4\] Banco relacional:** **PostgreSQL** para usuários, documentos, comparações, resultados e execuções de avaliação. É um meio-termo entre MySQL (A1, A2), SQLite (A6, bom para desenvolvimento) e MongoDB (A7). O ERD de A1 e as tabelas de avaliação de A2 servem de ponto de partida.

-   **Vetores:** **FAISS** em arquivo (como A2) ou pgvector no próprio PostgreSQL (uma peça a menos para operar). Para até algumas dezenas de milhares de documentos, índice exato (IndexFlatIP com vetores normalizados) basta; só avance para índices aproximados (IVF, HNSW) se a medição mostrar necessidade, como o próprio A2 argumenta. Atualizado: FAISS fora do escopo atual (seção 0); fica para a extensão. Decisão em 4.4: FAISS (faiss-cpu) com IndexFlatIP sobre vetores normalizados; pgvector deixa de se aplicar.

-   **Front end:** React ou Next.js (A7 usa Next.js + Tailwind) ou, se o prazo apertar, páginas simples com Bootstrap (A1, A4, A6). Se você já domina uma stack, mantenha-a; o motor Python fica atrás da API. Decidido em 4.4: Next.js + TypeScript + Tailwind CSS.

-   **\[Superado pela decisão 4.5\] Execução assíncrona:** comparações longas (embeddings, busca online) em fila de tarefas (Celery ou RQ); o front consulta o estado.

-   **Metodologia de projeto:** Waterfall com ERD e DFD (A1) é aceita em TCC e rende capítulos prontos; adapte com entregas incrementais por motor.

### 4.3 Decisões técnicas que os artigos não resolvem

-   **Português:** nenhum artigo trata PT-BR. Use modelo de embedding multilíngue (ou treinado para português), stopwords e lematizador de português, e confirme que os limiares de A5 e A6 se mantêm. **Re-calibre os limiares** (0,30, 0,65, 0,75, 0,85) nos seus dados; eles não são universais. O 0,65 só se aplica à busca online, fora do escopo.

-   **Documentos longos:** modelos de embedding têm limite de tokens (modelos tipo MiniLM costumam truncar em 256; confirme na ficha do modelo). A7 usa 212. Divida em parágrafos ou janelas, gere um vetor por trecho e agregue (média e máximo). No escopo atual, a unidade é a sentença (seção 0.3).

-   **Escala:** comparar tudo com tudo é O(n²) (seção 3.1). Use recuperação de candidatos por FAISS e, em seguida, a comparação detalhada só nos top-k, como A2 e, de outro modo, A3 (ordena por tamanho e compara só vizinhos). Com o escopo de dois arquivos (seção 0), o custo que importa é o da matriz sentença × sentença, O(m·n) em sentenças, e o dos algoritmos de caractere.

-   **Privacidade (LGPD):** A5 restringe o acesso aos envios dos alunos; se usar documentos reais de terceiros, anonimize e registre o consentimento.

### 4.4 Decisão de stack e arquitetura (orientação de 21/10/2026)

*A stack toma o ambiente de A7 como referência; reprodução integral não demonstrada. O desenho do projeto é uma adaptação (Seção 4: \"Application Developed in\", \"Dependencies\", \"Database\" e Tabela 1), organizado como monólito modular. Onde houver conflito, esta seção prevalece sobre 4.2.*

-   **Aplicação (monólito modular):** Next.js, Node.js, TypeScript e Tailwind CSS, como em A7. Um único app web com módulos por domínio: autenticação, documentos (upload e parsing), comparação, relatório, avaliação e dataset. Cada módulo tem pasta, tipos e testes próprios e conversa com os outros por interfaces internas. Avaliação e geração do dataset rodam no core, por linha de comando (4.5); no web ficam auth, documents, comparison e reports.

-   **Núcleo de ML (core):** Python + Flask, como o servidor de similaridade de A7. Fica no mesmo repositório e no mesmo Docker Compose, acessível só pela aplicação (rede interna), nunca pelo navegador.

-   **Ponto a validar com o orientador:** Next.js + Flask são dois processos (A7 também descreve \"two servers\"). Se \"monólito modular\" tiver de ser um único processo, a alternativa é levar a camada web para Python, o que contraria a stack pedida. Decisão do autor (21/10/2026): seguir com Next.js + Flask e confirmar com o orientador em paralelo; registrar em TCC/01-decisoes.md.

-   **Banco:** MongoDB (A7). Coleções iniciais: users, documents, comparisons, sentence_matches, algorithm_runs, datasets, dataset_pairs, eval_runs e model_runs. O ERD de A1 (Login, User, Upload, Admin, PDF) e as tabelas eval_sets e eval_relevants de A2 são o ponto de partida. Como a comparação é entre dois arquivos, as tabelas de avaliação de busca de A2 não se aplicam; os experimentos usam dataset_pairs e eval_runs.

-   **Vetores:** FAISS (faiss-cpu) no core, com IndexFlatIP sobre vetores normalizados (equivale ao cosseno, seção 3.4), seguindo o argumento de A2 para busca exata em acervo pequeno. Alternativa: MongoDB Search e Vector Search na Community Edition, em GA desde 30/06/2026, que exige o processo mongot; só adotar se reduzir a complexidade. Atualização: com o escopo de dois arquivos (seção 0), o FAISS fica fora; esta descrição vale para a extensão futura.

-   **Hiperparâmetros de referência do siamês (A7, Tabela 1):** 8 épocas, taxa de aprendizado 2e-6, Adam, tamanho máximo 212 tokens, weight decay 1e-5 e MSELoss. A7 não informa tamanho de lote, divisão treino/validação/teste, α da LeakyReLU, p do dropout, dimensões das camadas densas nem a variante do BERT: esses valores serão definidos, justificados e registrados em TCC/ (pendente).

-   **Dependências de A7 (13):** Flask, numpy, pandas, google-generativeai, pymongo, sentence_transformers, torch, tqdm, transformers, bert_score, datasets, scipy e scikit-learn.

-   **Atenção ao google-generativeai:** o pacote é legado e o suporte terminou em 30/11/2025 (página do PyPI); o substituto é google-genai. Só é necessário se algum LLM for usado, por exemplo para gerar paráfrases do dataset. Pela seção 5.3, o LLM nunca define o rótulo.

-   **Acréscimos necessários:** separar por etapa, sem instalar toda a pilha futura. S1 existente: pdfplumber, python-docx, spaCy/modelo PT, NumPy, PyYAML e mwparserfromhell; dev: pytest, Hypothesis, RapidFuzz como oráculo e ReportLab. S2 futura: Flask/Pydantic/SciPy/Sentence-Transformers/torch/transformers e acesso Mongo quando necessário. S2/S3 web: Next.js/TypeScript/Tailwind, driver MongoDB, zod e testes próprios. S4: google-genai somente para geração em cache; S5: aprendizado adicional conforme protocolo aprovado. Grupos/perfis opcionais e ferramentas novas exigem necessidade/versão registradas; FAISS permanece fora do escopo. Verificar versões e licenças efetivas, sem parecer jurídico.

-   **Modelos para PT-BR (4.3):** um modelo Sentence-Transformers multilíngue para o E3 e um BERT em português (ex.: BERTimbau, neuralmind/bert-base-portuguese-cased) como base do siamês. Confirmar o limite de tokens e a licença na ficha de cada modelo antes de usar.

### 4.5 Camadas e responsabilidades

*Arquitetura limpa na medida certa: fórmulas e regras sem I/O no centro; banco, FAISS, parsers e HTTP nas bordas. Regra única: o domínio não importa nada das bordas.*

-   **core/domain:** fórmulas, métricas e transformações do dataset, puras e sem I/O; é aqui que entram os testes com valor de referência (ex.: Tabelas 4 a 8 de A1).

-   **core/application:** casos de uso (comparar, gerar_dataset, calibrar, rodar_experimento).

-   **core/adapters:** Flask (HTTP), MongoDB, FAISS, parsers (pdfplumber, no lugar do PyMuPDF do A4 por causa da licença; python-docx) e carregamento de modelos.

-   **core/cli:** gerar-dataset, validar-dataset, rodar-experimento e carregar-seeds; core/configs com um YAML por experimento, versionado.

-   **web (Next.js):** src/modules/\<auth \| documents \| comparison \| reports\>, cada um com domain, application e infra (repositório Mongo e cliente do core).

-   **Um dono por coleção:** o web grava usuários, documentos, comparações e relatórios; o core grava datasets, pares, experimentos e execuções. Duas aplicações escrevendo na mesma coleção é a fonte de bug mais comum nesse desenho.

-   **Core sem estado na comparação:** recebe texto e devolve escores; quem persiste é o web. Simplifica testes e a medição de carga.

-   **Contrato explícito:** rotas /v1, modelos pydantic no core e zod no web, com teste de contrato que quebra quando um lado muda.

-   **Sem cerimônia:** sem contêiner de injeção de dependência e sem interface para tudo; interface só onde há segunda implementação real (ex.: core falso nos testes do web).

-   **Sem fila no início:** comparação síncrona com limite de tamanho; coleção jobs com consulta de estado só se a latência medida exigir. Substitui a sugestão de Celery/RQ da 4.2.

-   **FAISS fora do escopo atual:** o sistema compara dois arquivos (decisão da seção 9), então FAISS e índice vetorial ficam como extensão futura.

## 5. Dados: real ou sintético?

### 5.1 O que existe de real nos artigos

-   **MIT Plagiarism Detection Dataset (Kaggle, 367.375 amostras) \[A5\]:** único dataset de plágio citado com métricas comparáveis (precisão 68%, recall 80%, F1 74%). **Não consegui abrir a página do Kaggle**, então confira idioma (provavelmente inglês), formato dos pares, rótulos e licença antes de contar com ele.

-   **SemEval STS 2015, 2016, 2017 \[A8, A9\]:** pares com nota humana de 0 a 5, públicos; o subconjunto *plagiarism* de 2016 tem 230 pares; STS 2017 tem 1.750 pares em 6 trilhas, incluindo cruzadas. Ideal para validar a camada semântica por correlação de Pearson.

-   **ACL-OCL (Hugging Face) \[A7\]:** 10.072 resumos de NLP; porém as paráfrases e as notas foram geradas por LLM (rótulos ruidosos).

-   **Privados e inacessíveis:** A2 (100 documentos administrativos), A5 (100 trabalhos de alunos), A6 (200 trabalhos). Servem só como referência de tamanho e desenho.

-   **Fora da pasta (encontrei em busca, vale ler):** os corpora **PAN-PC** (PAN-PC-10 tem 64.558 casos artificiais e 4.000 simulados, e o artigo defende que construir corpora sob medida pode ser automatizado) e um trabalho de 2024 (arXiv 2404.01582) que gera 32.927 pares de plágio com GPT-3.5 e usa FAISS + BERT. Ambos reforçam a abordagem sintética. Conferido em 21/10/2026: Potthast et al., COLING 2010 (64.558 artificiais + 4.000 simulados = 68.558 casos) e Xian et al., arXiv 2404.01582 (32.927 pares, GPT-3.5, FAISS + BERT).

### 5.2 Recomendação: estratégia em 3 camadas

Nenhum dataset real cobre sua lista de funcionalidades (cópia exata, trecho inserido, paráfrase, colagem de várias fontes, texto traduzido, formatos diferentes, português). Por isso recomendo **combinar**, e não escolher um só:

1.  **Benchmark sintético controlado (núcleo do experimento).** Parta de textos reais em português (artigos do SciELO, Wikipedia em PT, trabalhos abertos) e gere pares com **rótulo conhecido por construção**:

    -   cópia exata e cópia com pequenas edições e erros de digitação (A4);

    -   trecho de uma fonte inserido em documento maior, em proporções que cruzam os limiares de A3 (10%, 20%, 50%; lá são limiares de diferença de termos, não proporções inseridas);

    -   *patchwork*: sentenças de várias fontes misturadas (taxonomia de A1);

    -   paráfrase por LLM com **revisão humana em amostra**, e retrotradução PT→EN→PT (ideia de tradução de A9);

    -   reordenação de parágrafos e de sentenças (A3);

    -   mesmo conteúdo em PDF, DOCX e HTML (A3);

    -   negativos fáceis (temas distintos) e **negativos difíceis** (mesmo tema, conteúdo diferente). A Tabela 3 de A7 mostra que o cosseno chegou a 81,7% em um par de textos não relacionados, então negativos difíceis são necessários.

    -   **Evite o circularidade de A7:** não deixe o mesmo LLM gerar a paráfrase e a nota. Use transformações programáticas para o rótulo e valide uma amostra com pessoas.

2.  **\[Descartado em 21/10/2026: só dataset sintético, ver 5.3\] Benchmark real público (validade externa).** STS 2016 e 2017 (correlação de Pearson e Spearman) e o MIT Plagiarism (precisão, recall, F1), comparando com os números dos artigos. Isso protege o TCC da crítica de \"só funciona nos dados que eu mesmo gerei\".

3.  **\[Descartado em 21/10/2026: só dataset sintético, ver 5.3\] Corpus de demonstração real e pequeno.** Documentos com consentimento (ou abertos) para o teste de usabilidade e a demo.

**Regra de ouro (minha recomendação):** divida treino, validação e teste **por documento-fonte**, e não por par. A5 separa 80/20 por amostras; se o mesmo documento aparece em pares de treino e de teste, há vazamento e as métricas ficam otimistas.

### 5.3 Decisão: dataset sintético (orientação de 21/10/2026)

*Decisão final: o projeto usa só o dataset sintético, em treino, validação e teste. Nenhum conjunto real (STS, MIT, ASSIN, PAN) entra nos experimentos; as seções 5.1 e 5.2 ficam como registro da análise que levou a essa escolha.*

-   **Por que sintético:** nenhum conjunto real dos artigos cobre PT-BR e todos os tipos de reuso do escopo (5.2); o sintético dá rótulo conhecido por construção e é reproduzível.

-   **Textos-fonte:** textos em PT-BR de licença aberta (ex.: SciELO com CC-BY, Wikipédia em português). Registrar no manifesto a origem, a licença e a data de coleta de cada fonte.

-   **Classes, cada uma ligada a um artigo:**

    -   C0 original: negativo fácil (temas distintos) e negativo difícil (mesmo tema, conteúdo diferente) \[A7, Tabela 3\];

    -   C1 cópia exata (verbatim) \[A1, A5, A6\];

    -   C2 cópia com edições leves e erros de digitação, com taxa de edição controlada \[A4\];

    -   C3 trecho inserido em documento maior, em proporções escolhidas para cruzar os limiares de A3 (10%, 20% e 50%, que no artigo são limiares de diferença de termos; o experimento de A3 inseriu um trecho fixo de 2.533 bytes) \[A3\];

    -   C4 patchwork: sentenças de 2 a 4 fontes misturadas \[A1\];

    -   C5 paráfrase, por LLM e por retrotradução PT→EN→PT, com revisão humana de amostra \[A5, A6, A7, A9\];

    -   C6 plágio de palavras-chave e frases \[A1\];

    -   C7 reordenação de sentenças e parágrafos \[A3\];

    -   variação de formato: o mesmo conteúdo em PDF, DOCX e TXT \[A3, A4, A5\].

-   **Rótulos por construção:** (a) a classe do par; (b) o grau de reuso r ∈ \[0, 1\] = fração das sentenças do documento suspeito derivadas da fonte, conhecida pelo gerador. r é o alvo da regressão (siamês; Pearson e Spearman) e a classe é o alvo da classificação (P, R, F1, matriz de confusão). Isso evita a circularidade de A7, em que o mesmo LLM gera a paráfrase e a nota.

-   **Reprodutibilidade:** gerador determinístico com semente fixa; cada par com manifesto JSON (fonte, transformação, parâmetros, semente, versão do gerador); hash da versão do dataset registrado em TCC/06-dataset-sintetico.md.

-   **Divisão:** 70/15/15 por documento-fonte (nenhuma fonte aparece em dois conjuntos), estratificada por classe. Limiares (0,30; 0,75; 0,85; o 0,65 só vale para a busca online, fora do escopo) e pesos de fusão são calibrados só na validação (ROC/PR) e reportados uma única vez no teste.

-   **Validação do próprio dataset:** contagem por classe e por formato; distribuição de r; revisão humana de uma amostra estratificada (tamanho a definir com o orientador); concordância entre revisores (κ de Cohen) se houver dois; checagem automática de vazamento entre conjuntos.

-   **Tamanho:** a definir com o orientador, com a justificativa registrada. Escalas nos artigos: 200 pares (A6), 4.950 pares de 100 documentos (A5) e 10.072 resumos (A7).

-   **Limitação declarada:** com dados só sintéticos, a generalização para plágio real não é medida; isso entra como limitação no TCC. Os negativos difíceis, a revisão humana da paráfrase (C5) e a separação por documento-fonte reduzem esse risco.

### 5.4 Fluxo do dataset sintético

*Pipeline de etapas puras e versionadas, executado por linha de comando (não pela API) e com o mesmo pré-processamento e a mesma segmentação da comparação, para que o modelo seja avaliado com o pré-processamento que de fato usa.*

1.  **Coleta das fontes:** textos em PT-BR de licença aberta vão para raw/, cada um com manifesto (URL, licença, data, hash). Camada imutável.

2.  **Normalização:** limpeza e segmentação em sentenças com as mesmas funções do core.

3.  **Divisão antes de gerar pares:** 70/15/15 por documento-fonte, com semente fixa, antes de qualquer transformação. É o ponto que impede o vazamento: a mesma fonte nunca aparece em treino e teste.

4.  **Geração por transformação:** cada classe (C0 a C7) é uma função pura (fonte, parâmetros, semente) → (suspeito, rótulos). Grava-se a origem de cada sentença do suspeito; assim r = sentenças derivadas da fonte ÷ total de sentenças do suspeito sai por contagem exata, e o gabarito por sentença serve à classificação por sentença (A6) e ao mapa de calor (A9). No patchwork (C4), cada par suspeito × fonte tem o seu r.

5.  **Formato à parte:** gerar PDF, DOCX e TXT é uma etapa separada; extrair o texto de volta vira teste de ida e volta do parser.

6.  **Validação automática:** esquema, contagem por classe, distribuição de r, ausência de vazamento e de quase-duplicatas entre conjuntos, e determinismo (mesma semente, mesmo hash).

7.  **Revisão humana por amostra:** concentrada em C5; aceito ou rejeitado registrado; rejeitados descartados e regenerados; κ de Cohen se houver dois revisores.

8.  **Congelamento:** versão = hash do manifesto; datasheet (fontes, licenças, classes, parâmetros, limitações, no modelo \"Datasheets for Datasets\"); exportação em JSONL para o Zenodo; um comando carrega a versão no MongoDB.

9.  **Consumo:** experimentos leem só versões congeladas; calibração na validação; teste rodado uma única vez.

-   **Paráfrase por LLM:** a saída do LLM não é determinística. Guardar as saídas como artefato, com modelo, versão e prompt, e regenerar a partir desse cache, sem chamar o LLM de novo.

-   **Negativos difíceis:** montados com fontes da mesma categoria temática (ex.: mesma categoria da Wikipédia). Sem eles, o cosseno parece bom demais; A7 mostra 81,7% de cosseno entre textos sem relação.

## 6. Plano de avaliação

-   **Pontuação contínua (regressão):** Pearson, Spearman, MAE, MSE e R² \[A7, A8, A9\]. Reporte Pearson **e** Spearman: em A7 a diferença (0,87 vs 0,66) revela ordenação fraca.

-   **Classificação de relações textuais:** precisão, recall, F1 por classe, F1 macro, acurácia e **matriz de confusão** \[A5, A6\]; limiares escolhidos em validação com curva ROC ou PR \[A6\].

-   **Recuperação de fontes:** Recall@K, MRR, MAP, nDCG@K, No-Hit e latência p50, p95, p99 \[A2\]. Fora do escopo atual (comparação entre dois arquivos, seção 9); fica para extensão.

-   **Eficiência:** tempo e memória por motor \[A4\], tempo de embedding \[A2\], curva de escalabilidade pelo tamanho dos arquivos (nº de sentenças).

-   **Ablação:** TF-IDF só, SBERT só, híbrido, híbrido + algoritmos de string e + siamês (a busca online está fora do escopo). Faça tanto a ablação \"isolado\" quanto \"removido do conjunto\", como A9, que revelou um componente prejudicial.

-   **Robustez estatística:** repita com várias sementes e reporte média ± desvio. A9 viu modelos únicos oscilarem entre 0,605 e 0,636; intervalos de confiança por *bootstrap*.

-   **Testes de software:** caixa-preta por partições de equivalência (A1); **testes de regressão com valores de referência** (as tabelas IDF e TF-IDF de A1 e os casos de A4).

-   **Índice de correlação (objetivo do tema):** escore fundido de 0 a 100 entre os dois arquivos. Sua validade é medida pela correlação de Pearson e Spearman entre o índice e o grau de reuso r do dataset sintético (5.3), além da classificação por tipo.

-   **Hipóteses (a confirmar com o orientador):** H1, a fusão lexical + semântica tem F1 macro maior que cada motor isolado (ablação, como A6 e A9); H2, o siamês ajustado tem Spearman maior que o SBERT sem ajuste no teste sintético; H3, o sistema mantém a latência p95 dentro de uma meta sob uma carga definida (metas pendentes).

-   **Testes de unidade das fórmulas:** valores de referência de A1 (N = 4: 0,60206 e 0,30103; cos(u, d2) = 0,0365; exemplo didático = 0); propriedades por função e domínio: distância de edição tem identidade zero; similaridades de caracteres normalizadas têm identidade um; cosseno geral não nulo pertence a [−1,1], e TF-IDF não negativo a [0,1]. Norma zero segue política explícita (atualmente zero), sem identidade artificial; 1+cos pode chegar a 2. Delta A3 pode ser direcional e superar 1; hash não é escore. Simetria só quando o contrato a exigir.

-   **Integração, ponta a ponta e caixa-preta:** APIs do core e da aplicação; Playwright no fluxo upload → comparação → relatório; partições de equivalência por tela, como a Tabela 3 de A1.

-   **Carga e eficiência:** k6 ou Locust medindo vazão, taxa de erro e latência p50/p95/p99 \[A2\]; tempo e memória por algoritmo \[A4\]; tempo de embedding \[A2\]; curva de escala pelo tamanho dos arquivos (nº de sentenças), já que a comparação é sempre entre dois arquivos.

-   **Segurança:** limite de tamanho e checagem do tipo real dos arquivos; sanitização do texto extraído; autenticação e acesso restrito aos próprios documentos (A5 restringe o acesso aos envios); limite de requisições; core sem exposição pública; auditoria de dependências (npm audit, pip-audit); segredos só em variáveis de ambiente.

-   **Reprodutibilidade de ML:** sementes e versões fixadas; cada execução registrada em TCC/12-experimentos.md com configuração, métricas e artefatos.

### 6.1 Telas de resultado e de retorno

-   Índice de correlação geral de 0 a 100 e rótulo do tipo predominante.

-   Lado a lado: os dois arquivos do par, com sentenças coloridas por classe \[A1, Fig. 11; A6, Fig. 4\].

-   Lista de sentenças com classe, escore e fonte \[A6, Tabela 1\].

-   Mapa de calor do alinhamento (palavra a palavra ou sentença a sentença), com o par alinhado destacado \[A9, Apêndice A\].

-   Tabela por algoritmo com similaridade (%), tempo (s) e memória (bytes), e modo \"rodar todos\" \[A4, Fig. 2\].

-   Estados da tela: enviando, processando (com progresso), concluído e erro com mensagem clara.

-   Exportar o relatório em PDF pela impressão do navegador, com CSS de impressão (entra; seção 0) \[A6 cita como trabalho futuro\].

-   Histórico das comparações do usuário, com acesso ao relatório de cada uma \[A6\].

### 6.2 Testes por camada

-   **Domínio:** valores de referência (mapa, seção \"Valores de referência para testes\") e propriedades com hypothesis por função/domínio, conforme 6: distinguir distâncias, similaridades normalizadas, vetores nulos, cosseno geral, Delta direcional e assinatura. Não impor simetria, [0,1] ou identidade um universalmente.

-   **Aplicação:** casos de uso com repositórios falsos em memória.

-   **Bordas:** integração com o MongoDB do Docker Compose, em perfil de teste.

-   **Web ↔ core:** teste de contrato.

-   **Fluxo completo:** Playwright de ponta a ponta.

-   **Carga:** k6 no endpoint de comparação.

-   **Dataset:** determinismo, vazamento e esquema.

-   **Seeds de desenvolvimento:** começar pelo exemplo numérico de A1 (u, d1, d2, d3), que tem gabarito publicado e prova desde o primeiro dia que o pipeline reproduz um cálculo da literatura. Usar como entrada os tokens já pré-processados das Tabelas 6 e 7 (o texto original é indonésio e passou pelo Sastrawi), não o texto bruto.

## 7. Roteiro sugerido

1.  **Fundamentação e reprodução:** reproduzir os cálculos de A1 e A4 à mão e em código; as dúvidas marcadas como (reconstruída) foram conferidas em 21/10/2026 (seção 13).

2.  **Baseline lexical (E1, E2):** TF-IDF, cosseno, n-gramas, shingles, algoritmos de string; testes de regressão.

3.  **Camada semântica (E3):** embeddings, FAISS, métricas de recuperação, calibração de limiares em português.

4.  **Dataset:** gerador sintético (5.3), validação do dataset e divisão por documento-fonte, seguindo o fluxo da 5.4.

5.  **Fusão e classificação:** regras de A5 e A6, depois modelo aprendido; ablações; modelo siamês de A7 treinado no dataset sintético com os hiperparâmetros de 4.4.

6.  **API e front end:** Next.js (TypeScript, Tailwind) + Flask + MongoDB em monólito modular (4.4); interface de comparação com destaque e relatório (6.1); testes da seção 6.

7.  **Fora do escopo: busca online (E5). O alinhamento (E4) e o siamês (A7) passaram a fazer parte do escopo (seção 0).**

8.  **Avaliação final e escrita:** capítulos de revisão (A1 a A9), engenharia (ERD, DFD, arquitetura), metodologia experimental e resultados.

## 8. Inconsistências e riscos que encontrei nos artigos

-   **A1:** validação com 3 documentos; \"4% vs 4,34%\" não prova generalização; documentos em indonésio; \"7 tokens\" para 5 listados; n × df na legenda da Eq. 1; equação do cosseno numerada 2 e depois 3; datas \"20xx\".

-   **A2:** corpus de 100 documentos e 30 consultas; ranking fraco (nDCG 0,38 a 0,44); L2 sobre vetores não normalizados; resumo diz que todas as consultas tiveram resultado, mas No-Hit = 0,033 (1 de 30) e a conclusão diz \"a maioria\"; na Tabela 2 a consulta sobre junho de 2025 tem como relevante um documento de junho de 2024.

-   **A3:** método de 2002 com ferramenta proprietária; assinatura por soma de hashes ignora a ordem; módulo de amostragem conferido nas imagens: 25 nas seções 4 e 9.1 (não existe 250); sem DOI impresso.

-   **A4:** teste qualitativo sem corpus anotado; algoritmos de caractere não capturam semântica; duas figuras numeradas \"Figure 1\" e citação a uma \"Fig. 3\" inexistente; Eq. 2 com \"Longest word length\"; Tabela 1 não diz qual algoritmo gerou cada número; Jaro-Winkler e Smith-Waterman sem parâmetros.

-   **A5:** na discussão (p. 323) o MIT aparece com precisão 62% e recall 79%, mas o resumo e a matriz dão 68,2% e 79,8%; o \"+\" da Eq. 2 está impresso no artigo; limiar online 0,2 no resumo × 65% no Algoritmo 2; Threshold_Textual não definido; dois modelos BERT sem dizer qual entra no máximo; não fica claro como o BERT foi ajustado; busca online frágil.

-   **A6:** dataset pequeno e próprio; limiares tirados de um piloto de 50 pares; números da ablação não aparecem; modelo SBERT não especificado; F1 descrito como \"média\"; Fig. 3 é ROC com AUC = 1,00, mas o texto fala em acurácia × limiar; numeração de citações trocada na revisão.

-   **A7:** rótulos gerados por LLM; Pearson alto com Spearman baixo; domínio estreito (resumos de NLP); divisão treino/teste, lote, α, p e variante do BERT não informados; só pares similares gerados; \"encoder-decoder\" na Seção 5; referências \[10\] e \[19\] duplicadas.

-   **A8:** pesos heurísticos; e\^(α·l) impresso sem o sinal de menos; DSSM dito não negativo, mas com tanh; escala do Run 1 antes da média não informada; avaliado em inglês e frases curtas.

-   **A9:** ganho pequeno (0,650 a 0,672) para a complexidade; dependência de tradução; legendas de imagem são simples; o 0,650 da conclusão é o TakeLab isolado e o 0,672 é o ensemble sem o Align; resumo diz \"linear regression\", método usa regressão logística L2.

-   **Em comum:** nenhum artigo trata português; poucos tratam documentos longos ou escala.

## 9. Pendências para fechar com você

-   **Comentários do orientador**: recebidos em 21/10/2026 e incorporados nas seções 4.4, 4.5, 5.3, 5.4, 6, 6.1, 6.2, 10, 11 e 12.

-   **Idioma dos textos** que o sistema vai comparar (PT-BR?) e tipos de arquivo aceitos. Decidido em 21/10/2026: PT-BR; PDF, DOCX e TXT.

-   **Tamanho esperado do acervo** (dezenas, milhares ou mais de documentos) e se há comparação só entre dois arquivos ou também contra uma base. Decidido em 21/10/2026: comparação entre dois arquivos, sem base de documentos (FAISS e métricas de recuperação ficam como extensão futura).

-   **Busca online** entra no escopo ou fica como trabalho futuro?. Decidido em 21/10/2026: trabalho futuro, só se houver tempo e sem violar termos de uso nem diretrizes.

-   **Restrições da universidade** para stack, banco e prazo; **hardware** disponível (GPU ou só CPU: A5 rodou em notebook i5 com 8 GB, A7 treinou em GPU P100). Stack e banco definidos em 4.4; prazo e hardware seguem pendentes.

-   **Dataset MIT:** posso tentar de novo ler a página do Kaggle por outra rota, ou você baixa e me mostra o esquema das colunas. Descartado em 21/10/2026: o projeto usa só o dataset sintético (5.3). Para registro, a URL citada em A5 é kaggle.com/datasets/ruvelpereira/mit-plagairism-detection-dataset.

## 10. Organização documental: docs/ e TCC/

*docs/ e TCC/ ficam fora do Git (.gitignore) e nunca vão para o repositório remoto.*

-   **docs/:** os 9 PDFs (A1 a A9), este guia e o mapa de fórmulas e arquiteturas. Guias, mapas, roteiros e cópias identificadas são preservados como histórico privado; nenhuma limpeza está autorizada nesta revisão.

-   **Referências com DOI impresso nos PDFs:** A1 10.32877/bt.v7i2.1697; A2 10.33395/sinkron.v10i2.15940; A5 10.1007/s43995-025-00108-1; A6 10.2991/978-94-6463-950-6_23. Sem DOI impresso: A3 (CIKM 2002, pp. 245--251), A4 (Elektrotehniški vestnik 92(3), pp. 151--156), A7 (EasyChair Preprint 15448, 20/11/2024), A8 (SemEval-2016, pp. 674--679) e A9 (SemEval-2017, pp. 185--190).

-   **TCC/:** registro privado e progressivo do desenvolvimento, base para a escrita do TCC. Permanece privado, preservado e disponível para a redação; não apagar nesta execução.

-   **.gitignore:** linhas docs/, TCC/, CLAUDE.md e AGENTS.md (os dois últimos guardam as regras da seção 11 para a IA). Se algum arquivo dessas pastas já estiver rastreado, git rm -r \--cached docs TCC tira do índice sem apagar os arquivos locais. Essa operação é feita pelo autor, não pela IA (seção 11).

-   **Arquivos de TCC/:** 00-indice.md, 01-decisoes.md, 02-metodologia.md, 03-formulas-e-calculos.md, 04-parsing.md, 05-core.md, 06-dataset-sintetico.md, 07-backend.md, 08-frontend.md, 09-banco-e-seeds.md, 10-docker.md, 11-testes.md, 12-experimentos.md, 13-resultados.md e 14-pendencias.md.

-   **Modelo de cada registro:** data; etapa; objetivo; o que foi feito; decisões e motivo (com o artigo de base, A1 a A9); configuração e comandos; saída obtida (números reais, copiados da execução); arquivos criados ou alterados; testes executados e resultado; pendências.

-   **Rastreabilidade:** 03-formulas-e-calculos.md liga cada fórmula ao artigo, ao arquivo do código e ao teste com o valor de referência; 12-experimentos.md tem uma entrada por execução (semente, versão do dataset, configuração, métricas, artefatos). O que não foi executado fica marcado como PENDENTE.

## 11. Regras obrigatórias para a IA que desenvolver o projeto

*Valem para qualquer assistente de IA que use este guia, durante todo o desenvolvimento.*

1.  **Sem Git remoto nem histórico:** não executar commit, push, tag, merge, rebase, cherry-pick, revert, reset/clean, PR, release ou publicação, inclusive por APIs/scripts; não apagar volumes nem descartar alterações; não alterar a configuração do Git nem as linhas docs/, TCC/, CLAUDE.md e AGENTS.md do .gitignore. A IA escreve, corrige, implementa e testa; versionar é tarefa do autor.

2.  **TCC/ sempre preenchido:** ao terminar cada etapa, e antes de passar à próxima, atualizar o arquivo da etapa e o 00-indice.md com o modelo da seção 10.

3.  **Nada inventado:** distinguir valor publicado (PDF/página), recálculo independente (fórmula/entradas), decisão/proposta (origem/aprovação/status), resultado executado (comando/saída/artefato) e não verificado. Não inventar resultados ou aprovações; parâmetros propostos não são resultados obtidos. Seeds/fumaça não são resultados de pesquisa; não preencher revisão humana.

4.  **Comentários mínimos:** só quando indispensáveis para algo não óbvio, em uma linha curta e em tom natural. Sem comentários que repetem o código, sem cabeçalhos decorativos e sem docstrings longas.

5.  **Fórmulas do mapa:** usar o mapa como índice auxiliar e conferir a fonte original; conflitos não se resolvem escolhendo o que faz o teste passar. Onde o artigo tem erro marcado (ex.: \"+\" no TF-IDF de A5, e\^(α·l) em A8), usar a forma corrigida e registrar em TCC/03-formulas-e-calculos.md.

6.  **Teste para cada fórmula:** toda fórmula implementada ganha teste com valor de referência (ex.: A1, Tabelas 4 a 8).

7.  **Reprodutibilidade:** sementes fixas, versões de dependências fixadas e configurações em arquivo.

8.  **Pesquisa antes de produto:** as decisões seguem os objetivos científicos, a metodologia (5.3 e 6) e as orientações do orientador. Em dúvida de escopo, registrar em TCC/14-pendencias.md e perguntar ao autor.

9.  **Segurança:** nenhum segredo no código; variáveis de ambiente; validação de toda entrada.

10. **Ordem e originalidade:** seguir a ordem da seção 12 (backend, testes, frontend integrado, dataset) e não copiar código de terceiros.

## 12. Ordem de desenvolvimento e execução local (orientação de 21/10/2026)

*Projeto de pesquisa, sem deploy: qualquer pessoa com acesso ao código deve conseguir rodá-lo na própria máquina. Esta ordem prevalece sobre o roteiro da seção 7.*

1.  **Backend completo:** core Python + Flask com as fórmulas do mapa nos motores E1 a E4 (E5 e FAISS ficam para o futuro, seção 9), parsing, pré-processamento, fusão, classificação e siamês (A7); integração com MongoDB e com a API da aplicação (Next.js/Node). Cada fórmula já sai com teste de valor de referência.

2.  **Testes:** unidade, integração, ponta a ponta da API, caixa-preta, eficiência, carga e segurança (seção 6).

3.  **Frontend com integração:** telas da 6.1 já ligadas ao backend, com configurações e estados de erro.

4.  **Dataset sintético (5.3), por último:** depois dele vêm os experimentos (treino do siamês, calibração de limiares e métricas de H1 a H3), registrados em TCC/12-experimentos.md e TCC/13-resultados.md.

-   **Dependência a respeitar:** treino, calibração e métricas dependem do dataset. Até a etapa 4, o backend usa seeds pequenos e fixos, com rótulo conhecido, só para desenvolvimento e testes; nada calculado com eles entra como resultado do TCC.

-   **Banco:** MongoDB no Docker Desktop via Docker Compose; seeds versionados no repositório e carregados por um único comando.

-   **Execução local intuitiva:** README com pré-requisitos e versões (Docker Desktop, Node.js, Python); .env.example; um comando para subir tudo (docker compose up), um para carregar os seeds e um para rodar os testes; nenhuma etapa manual escondida.

-   **Originalidade:** nenhum código copiado de terceiros; os artigos entram só como base teórica e são citados; bibliotecas instaladas pelo gerenciador de pacotes, com as licenças registradas em TCC/01-decisoes.md.

-   **Publicação:** preparação local futura de LICENSE, CITATION.cff e README de reprodução; qualquer depósito ou publicação é ação exclusiva do autor e não está autorizado para a IA.

## 13. Registro de revisões

-   **21/10/2026:** conferência de texto e imagem dos 9 PDFs (88 páginas) e incorporação das orientações do orientador. O conteúdo anterior foi mantido; as correções estão nas próprias seções:

    -   A1: N = 4 no exemplo (não 3); 74 itens de teste em 15 telas; cos(u, d2) recalculado = 3,65%.

    -   A3: módulo dos shingles = 25 nos dois trechos; a ressalva sobre 250 foi encerrada.

    -   A4: Jaro e Jaro-Winkler estão impressos no artigo (Eqs. 3 e 4); deixaram de ser \"reconstruídas\".

    -   A5: limiar online de 65% no método (0,2 só no resumo); pré-processamento com os 9 passos completos; o \"+\" do TF-IDF está impresso no artigo; percentual online formalizado pelo Algoritmo 2; matrizes de confusão recalculadas.

    -   A7: setup completo (13 dependências, máquinas, dois servidores) e parâmetros que o artigo não informa.

    -   A8: e\^(α·l) está impresso no artigo (erro do artigo); notação S_sem, S_syn, o1, o2 e Ω, como no artigo.

    -   A9: Apêndice A (matrizes de alinhamento) e a origem do 0,650 e do 0,672.

    -   Seção 0 (escopo final) criada; 4.1, 4.3, 6, 6.1 e 7 alinhadas a ela; definidos o IDF por corpus de referência (com N = 2 o TF-IDF degenera), a unidade sentença, a fórmula do índice de correlação, os limiares provisórios, o limite dos algoritmos de caractere e o hash estável da assinatura.

    -   Decisões do autor (21/10/2026, 18h30): dois arquivos, sem base; PT-BR com PDF, DOCX e TXT; busca online como trabalho futuro; Next.js + Flask confirmado em paralelo com o orientador. Validação das capturas do A3, A4 e A5: novos pontos nas Tabelas 4 e 5 de A3 e nas Figs. 4 a 6 de A5.

    -   Revisão final: arredondamento de ‖u‖ e ‖d2‖ em A1; Dense Layer 3 em A7; afirmação de que todos os artigos usam Python (A3 usa Java); proporções do C3 em relação aos limiares de A3; TF-IDF do scikit-learn × A1; escopo de E5 e FAISS na seção 12; CLAUDE.md e AGENTS.md no .gitignore; números do PAN-PC-10 e do arXiv 2404.01582 conferidos.

    -   Decisão de usar só o dataset sintético; conjuntos reais descartados (5.2 itens 2 e 3 marcados).

    -   Seções novas: 4.4, 4.5, 5.3, 5.4, 6.1, 6.2, 10, 11, 12 e 13; 4.2 marcada como superada onde conflita com 4.4; a ordem da seção 12 prevalece sobre o roteiro da seção 7.

-   **22/10/2026:** prazo de 5 dias; seção 0.4; PDF com pdfplumber por causa da licença Apache-2.0.

-   **2026-10-24:** reconstrução documental e integração do roteiro; correções pontuais de A6, OSA, E2, propriedades e evidências; contrato científico proposto em TCC/02, sem experimento, alteração de H1–H3 ou aprovação humana presumida.
