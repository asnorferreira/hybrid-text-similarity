# Otimização de recursos

Registro da primeira intervenção. A revisão operacional vigente e a divisão dos
arquivos ainda pendentes estão em [H2 com limite de 2 GB](./19-h2-limite-2gb.md).
As reservas e a divisão de commits descritas abaixo representam aquela etapa.

Patch de engenharia sobre `ef738b420ebed48f5b02680f5beb84a0d702acd0`.
As medições usam entradas de desenvolvimento, Docker Engine, CPU, contêineres
removidos ao terminar, 2 CPUs e teto de 2 GiB sem swap adicional no contêiner.
Nenhum dataset científico foi utilizado nesta intervenção.

## Medições antes e depois

Pico de RSS do processo, em MiB (1 MiB = 1.048.576 bytes):

| Cenário | Antes | Depois | Redução |
| --- | ---: | ---: | ---: |
| Inicialização e saúde HTTP | 298,41 | 44,33 | 85,15% |
| Primeira comparação lexical | 1.191,25 | 345,82 | 70,97% |
| OSA, duas strings de 4.000 caracteres | 625,53 | 21,01 | 96,64% |
| Finitude de 32 milhões de parâmetros float32 | 567,11 | 358,18 | 36,84% |
| Extração de PDF gerado, 60 páginas | 477,19 | 56,83 | 88,09% |
| Encoder semântico, duas entradas repetidas | 1.115,91 | 1.114,20 | 0,15% |

São execuções individuais em processos novos, com dependências e limites iguais.
Não são médias, garantias para qualquer documento ou resultados de H3. RSS inclui
imports, inicialização e operação. O pico do cgroup, registrado separadamente,
inclui memória de arquivos e pode variar com o cache do kernel; não é intercambiável
com RSS. No cenário semântico ele cresceu de 981,42 para 1.253,42 MiB; essa execução
não demonstra economia de memória do encoder carregado. Os pesos permanecem inteiros.

Os arquivos JSON, vetores de referência, comandos e saídas estão na
[evidência local](../TCC/evidencias/codex-recursos-01/).
As primeiras medições intermediárias após o patch também foram preservadas;
para saúde e lexical, a tabela usa os arquivos `after-final-*.json`.

## Comportamento implementado

- A saúde não importa NumPy, spaCy, PyTorch, modelos ou parsers. O recurso lexical
  é inicializado no primeiro uso; o encoder semântico, no primeiro uso híbrido.
  Inicialização e falha do encoder são memorizadas sob lock. Uma falha semântica
  continua permitindo comparações lexicais e retorna 503 no modo híbrido.
- O serviço lexical permanece separado do híbrido. Seu `metadata.model` é nulo
  quando criado pela aplicação, inclusive depois de outro pedido híbrido.
  Um serviço explicitamente injetado mantém os recursos fornecidos pelo chamador.
- OSA mantém a recorrência de transposição adjacente usando três linhas de tamanho
  proporcional à menor string. Smith–Waterman também usa a menor string nas linhas.
  A complexidade temporal dos dois algoritmos continua quadrática.
- Cada página PDF libera seus caches após extrair texto e observar imagens,
  inclusive se a extração falhar. O texto final e os erros públicos são preservados.
- Finitude de pesos e gradientes usa blocos de até 65.536 elementos. Inclui os pesos
  congelados e aceita tensores não contíguos sem achatar uma cópia completa.
- A recarga do estado local usa `torch.load(weights_only=True, mmap=True)` após
  verificar os hashes. Os testes verificam retomada e que atualizações do otimizador
  não alteram os bytes do checkpoint de origem.
- A inferência semântica reaproveita textos repetidos dentro da mesma chamada,
  em avaliação, com até 128 chaves. O mapa é descartado ao retornar. Vetores e
  diagnósticos retornados continuam independentes para alterações do chamador.
- O encoder de janelas usa LRU de até 128 entradas e 1 MiB contabilizado para
  embeddings congelados em avaliação sem autograd/autocast. Não armazena grafos.
  Mudanças de parâmetros, buffers, dispositivo, precisão ou configuração invalidam
  o cache. Treinamento do encoder e execução estocástica ignoram e limpam o cache.
  Existe também `clear_embedding_cache()` para invalidar explicitamente. A estrutura
  Python e a assinatura dos pesos têm pequeno custo adicional ao conteúdo contabilizado.
  Os diagnósticos de cada chamada continuam preservados.

## Preservação científica e verificação

A revisão 3 do protocolo, os seis tensores da cabeça (98.817 parâmetros),
pesos congelados, pooling, cobertura de janelas, IDF, fórmulas, limiares e seeds
permanecem iguais. Os parâmetros treináveis continuam exatamente:

| Tensor | Forma | Parâmetros |
| --- | --- | ---: |
| `head.0.weight` | 128 × 768 | 98.304 |
| `head.0.bias` | 128 | 128 |
| `head.1.weight` | 128 | 128 |
| `head.1.bias` | 128 | 128 |
| `head.4.weight` | 1 × 128 | 128 |
| `head.4.bias` | 1 | 1 |

O snapshot RG-01 não foi regravado. Os testes comparam saída,
gradientes e atualização da cabeça com cache habilitado e desabilitado, usando
RNG idêntico. O [ensaio com o encoder real](../TCC/evidencias/codex-recursos-01/cabeca-real.json)
confirmou três atualizações idênticas da cabeça, gradientes finitos e não nulos
nos seis tensores, sem alteração nas versões dos pesos congelados.
O hash dos embeddings medidos e o hash do texto extraído do PDF
permanecem iguais aos anteriores.

Não houve novo ajuste científico, calibração, avaliação do teste ou reexecução de
H1/H2. Os portões continuam H1 ≥ 2 GiB e H2 ≥ 4 GiB disponíveis antes de carregar o
modelo. As reduções medidas não demonstram que H2 cabe na máquina. O código novo
recebe nova identidade nas execuções futuras, sem reatribuir evidências antigas.

A suíte completa aprovou 865 testes, incluindo 34 casos RG-01, sem falhas,
erros ou skips. Pyright 1.1.407 analisou 125 arquivos com zero erros e avisos.
Ruff passou no código completo para erros de sintaxe/nomes e nos arquivos
alterados com todas as regras F. Os resultados estão registrados em
[`testes.json`](../TCC/evidencias/codex-recursos-01/testes.json).
Nenhum commit, stage, push, publicação, ajuste global de swap ou encerramento de
processos do usuário é necessário para aplicar o patch.

## Divisão histórica dos commits

A divisão abaixo foi entregue na primeira intervenção. Para os arquivos ainda
pendentes na base atual, usar [a divisão atualizada](./19-h2-limite-2gb.md#commits-atômicos-para-o-autor).
Naquela entrega, o agente não havia executado os commits.

1. `perf(core): reduzir memória das métricas OSA e Smith-Waterman`
   - [core/src/hts_core/domain/strings.py](../core/src/hts_core/domain/strings.py)
2. `perf(http): carregar recursos apenas quando necessários`
   - [core/src/hts_core/adapters/http.py](../core/src/hts_core/adapters/http.py)
   - [core/src/hts_core/adapters/resources.py](../core/src/hts_core/adapters/resources.py)
   - [core/tests/adapters/test_http.py](../core/tests/adapters/test_http.py)
3. `perf(ml): limitar temporários e reutilizar embeddings congelados`
   - [core/src/hts_core/adapters/semantic.py](../core/src/hts_core/adapters/semantic.py)
   - [core/src/hts_core/adapters/trainable_siamese.py](../core/src/hts_core/adapters/trainable_siamese.py)
   - [core/src/hts_core/adapters/training_runtime.py](../core/src/hts_core/adapters/training_runtime.py)
   - [core/tests/adapters/test_semantic.py](../core/tests/adapters/test_semantic.py)
   - [core/tests/test_frozen_embedding_cache.py](../core/tests/test_frozen_embedding_cache.py)
4. `perf(pdf): liberar caches de cada página após extração`
   - [core/src/hts_core/adapters/parsers/pdf_parser.py](../core/src/hts_core/adapters/parsers/pdf_parser.py)
   - [core/tests/adapters/test_parsers.py](../core/tests/adapters/test_parsers.py)
5. `test(core): registrar regressões de memória e medições do patch`
   - [core/tests/test_resource_memory.py](../core/tests/test_resource_memory.py)
   - [docs/18-otimizacao-recursos.md](./18-otimizacao-recursos.md)

As evidências estão sob o diretório local ignorado pelo Git, conforme a política
atual do projeto. A documentação acima contém os resultados essenciais para revisão.
