# H2 com limite de 2 GB

**Atualização científica 2026-10-27:** P8 concluída na primeira tentativa H2 r4:
28 train/13 validation, 8 épocas, 56 passos. Pico RSS amostrado 1.670.725.632 bytes;
cgroup 1.999.998.976 bytes, swap zero e zero OOM observado. Recarga independente:
13 predições exatamente iguais; encoder intacto, seis tensores da cabeça alterados.
Spearman siamês 0,3212080372 versus SBERT 0,8659812222 na validação dependente;
isso não comprova H2 no teste. O claim científico **está consumido**. Próxima etapa
PH2; não iniciar outro treino. [Evidência científica](../TCC/evidencias/codex-p08-02/relatorio.md).

Os ensaios e contagens abaixo registram a intervenção de recursos anterior ao fit,
preservando sua procedência; não são a execução científica acima.

A revisão operacional 4 mantém o desenho científico da revisão 3 e adota um teto
real de **2.000.000.000 bytes**, inferior a 2 GiB. A autorização é o pedido do autor
para otimizar H2 sem remover funções. As revisões 2 e 3 permanecem válidas e intactas.

Protocolo: [experiment_s5b.r4.json](../core/configs/experiment_s5b.r4.json).
Identidade canônica: `9ea49ccfba23361bdae8816e29bbf07817894edca79710f1816da8901e8edd7a`.
Registro local: [decisão r4](../TCC/01-decisoes.md#revisao-4-recursos-h2).

## Resultado medido

Docker Engine, CPU, duas threads, modelo real fixado, rede desativada e swap zero
no contêiner. Foram usados **somente textos e alvos de desenvolvimento**, com
28 pares de treino e 13 de validação, sem anotações científicas.

| Verificação | Resultado |
| --- | --- |
| Treino da fixture | 8 épocas, 56 atualizações Adam |
| Pico RSS de treino + checkpoints + retomada | 1.555.726.336 bytes, aproximadamente 1,56 GB |
| Pico total do cgroup | 1.999.998.976 bytes, incluindo cache de arquivos |
| Falhas de memória / processos mortos por OOM | 0 / 0 |
| Entradas longas | 12.000 tokens por texto, 96 janelas, cobertura completa |
| Retomada × execução contínua | Pesos da cabeça e estado do Adam exatamente iguais |
| Recarga do selecionado | 13 predições exatamente iguais |
| Encoder congelado | Hash integral preservado e nenhum gradiente |

O cache de arquivos ocupou o restante do orçamento: houve recuperação de páginas
pelo kernel e eventos `memory.max`. Portanto, o RSS do processo não representa a
RAM total do contêiner nem significa que ele tenha 444 MB livres. O ensaio completo
durou cerca de 215 segundos. Há evidência de viabilidade nesse ambiente e desenho;
não é uma garantia para qualquer combinação futura de versões ou concorrência.
O orçamento é exclusivo da H2; sistema operacional, editor e outros aplicativos
precisam de memória própria no host.

Uma comparação separada recarregou o mesmo checkpoint completo e repetiu as mesmas
13 predições, com resultados idênticos:

| Recarga real | Antes | Depois |
| --- | ---: | ---: |
| Pico RSS | 1.903.783.936 bytes | 1.508.397.056 bytes |
| Pico total do cgroup | 1.999.998.976 bytes | 1.850.052.608 bytes |
| Tempo da recarga | 2,374 s | 2,407 s |

A redução de RSS nessa comparação foi de aproximadamente **20,8%**. São execuções
individuais, sem promessa de aceleração. O caminho anterior também concluiu essa
recarga sob o teto de 2 GB; a comparação demonstra a margem obtida pela otimização,
não que o código anterior necessariamente exigisse 4 GiB em toda entrada.

Dados, comandos, falhas e checkpoints de desenvolvimento estão na
[evidência desta intervenção](../TCC/evidencias/codex-recursos-02/).

## Mudança no código

A [recarga de tensores](../core/src/hts_core/adapters/tensor_storage.py) valida todas
as chaves e formas antes de modificar pesos. Lê blocos lógicos de até 1 MiB,
abrindo e liberando o mapeamento de cada bloco, e compara bytes antes de copiar.
Isso evita manter uma segunda cópia inteira do encoder e evita copiar novamente
pesos iguais. Zeros com sinal e payloads de NaN são preservados. Os blocos podem
precisar de temporários do mesmo tamanho para tensores não contíguos; o consumo
auxiliar permanece proporcional ao bloco, e não ao modelo inteiro.

O checkpoint continua contendo **todos** os pesos e buffers, o otimizador, RNG,
progresso, hashes e vínculos de identidade. Objetos de parâmetros são preservados,
inclusive os ligados ao otimizador. A alteração atende tanto à retomada quanto à
recarga de inferência. Os gates de integridade, finitude e retenção continuam ativos.

O primeiro protótipo com o backend `pread` foi interrompido: na versão fixada da
biblioteca, fatiar relia o tensor inteiro, provocando I/O excessivo. O protótipo foi
substituído por mapeamentos liberados por bloco. A tentativa e seus arquivos foram
preservados. Os testes também identificaram e corrigiram uma particularidade de
stride em blocos unitários de tensores não contíguos. Falhas iniciais de lint por
imports antigos sem uso foram corrigidas; os registros não foram apagados.

## Parâmetros e desenho preservados

| Tensor treinável | Forma | Parâmetros |
| --- | --- | ---: |
| `head.0.weight` | 128 × 768 | 98.304 |
| `head.0.bias` | 128 | 128 |
| `head.1.weight` | 128 | 128 |
| `head.1.bias` | 128 | 128 |
| `head.4.weight` | 1 × 128 | 128 |
| `head.4.bias` | 1 | 1 |

Total: **98.817 treináveis**, 117.653.760 congelados. Os seis tensores receberam
gradientes finitos e não nulos e foram atualizados. A evidência registra as normas.
Arquitetura, float32, pooling, limite de 12.000 tokens, todas as janelas, Adam,
lr 2e-6, acumulação 4, micro-lote 1, seed, máximo de 8 épocas, 2.000 atualizações,
7.200 segundos, paciência 2 e seleção por MSE de validação permanecem iguais.
Nada de quantização, truncamento, redução do modelo ou retirada de verificações.

Na conclusão deste patch de recursos, nenhuma H1/H2 científica, calibração ou
avaliação do teste havia sido executada pelo patch. O claim H2 estava disponível;
posteriormente foi consumido pela P8 identificada no início deste documento. H1 histórica conserva os vínculos
da execução original. D5/D6/PH2 continuam pendentes.

## Portões de recursos

- O executor exige **2.000.000.000 bytes físicos disponíveis antes de iniciar**.
- Dentro do contêiner, H2 exige **1.800.000.000 bytes disponíveis após a preparação**,
  preservando margem sobre o RSS medido de 1.555.726.336 bytes. O teto de RSS também
  é 1.800.000.000 bytes. Os demais limites de treino permanecem iguais.
- O readiness recusa ausência de limite observável, teto diferente de 2.000.000.000
  bytes solicitados e swap permitido ou sem contabilidade observável. Aceita somente
  o arredondamento para baixo por página feito pelo kernel: nesta máquina, o limite
  efetivo foi 1.999.998.976 bytes. Esse arredondamento também tem teste de regressão.
- A disponibilidade é o mínimo entre `MemAvailable` físico, todos os ancestrais de
  cgroup expostos e uma coleta externa de host, se fornecida. Para cgroup, soma-se
  apenas cache de arquivos inativo e limpo à folga bruta. Páginas sujas ou em escrita
  são descontadas. Uso e folga brutos continuam registrados. Isso evita contabilizar
  novamente como indisponíveis os pesos que acabaram de ser lidos para verificar hash;
  não ignora falta de RAM física nem memória anônima.
- H1 conserva sua reserva. Usar a revisão 3 continua exigindo os 4 GiB originais para H2.

## Procedimento de execução e validação histórica

Validação local concluída: **899 testes core**, incluindo 34 RG-01, e 131 testes
dirigidos, sem falhas, erros ou skips nas execuções finais. Pyright 1.1.407 analisou
128 arquivos com zero erros e avisos. Ruff passou no código completo para sintaxe e
nomes e em todos os arquivos alterados com as regras F. Os buffers da fixture
receberam tipos explícitos; nenhum diagnóstico foi ocultado. A web não foi alterada.

O [executor Linux](../core/scripts/run_h2_2gb.sh) usa Docker Engine, cria um único
contêiner efêmero, dispensa serviços Mongo/web/core, fixa CPU/rede/RAM/swap e mantém
os diagnósticos do editor. Não inicia treinamento sozinho. Exemplo de readiness,
a partir da raiz do repositório, com os caminhos já existentes nesta máquina:

```bash
bash core/scripts/run_h2_2gb.sh readiness \
  --reference configs/experiment_s5a.json \
  --dataset artifacts/artifacts/s4-fechamento-01/frozen-curated-01 \
  --idf artifacts/artifacts/s4-fechamento-01/idf-final-01 \
  --annotations artifacts/artifacts/s5b-01/annotations-H2.json \
  --campaign artifacts/plan16-r3-01/campaign \
  --out artifacts/plan16-r3-01/readiness-H2-r4-manual-01
```

O diretório de saída deve ser novo. A imagem padrão é `hts-ci-core:local`, com as
dependências fixadas usadas na medição; `HTS_S5B_IMAGE` permite indicar a mesma
imagem com outro nome local. A operação científica usada foi `run`, com saída nova e sob as regras do plano.
Ela já foi concluída e seu claim consumido; o exemplo de readiness não autoriza
outro fit. Qualquer tentativa adicional exige decisão científica registrada. A reprodução de evidências antigas não
usa automaticamente a revisão nova. Não é necessário Docker Desktop.

## Commits atômicos para o autor

Divisão dos arquivos pendentes sobre `7641a207739ca59a68c7a23ff629e827520ec465`.
Os commits externos feitos durante a intervenção foram preservados. O vínculo da
[recarga de treino](../core/src/hts_core/adapters/training_runtime.py) já aparece
nessa base; o primeiro grupo abaixo inclui o módulo que completa esse vínculo.
Aplicar na ordem. O agente não executou stage, commit, push ou publicação.

1. `perf(checkpoint): recarregar pesos em blocos sem duplicar o encoder`
   - [tensor_storage.py](../core/src/hts_core/adapters/tensor_storage.py)
   - [training_artifacts.py](../core/src/hts_core/adapters/training_artifacts.py)
   - [test_tensor_storage.py](../core/tests/test_tensor_storage.py)
2. `test(training): verificar equivalência do cache congelado`
   - [test_frozen_embedding_cache.py](../core/tests/test_frozen_embedding_cache.py)
3. `feat(training): adotar revisão operacional H2 com teto de 2 GB`
   - [container_memory.py](../core/src/hts_core/adapters/container_memory.py)
   - [training_contract.py](../core/src/hts_core/adapters/training_contract.py)
   - [controlled_training.py](../core/src/hts_core/application/controlled_training.py)
   - [experiment_s5b.r4.json](../core/configs/experiment_s5b.r4.json)
   - [experiment_s5b.schema.json](../core/configs/experiment_s5b.schema.json)
   - [run_h2_2gb.sh](../core/scripts/run_h2_2gb.sh)
   - [test_container_memory.py](../core/tests/test_container_memory.py)
   - [test_protocol_r4.py](../core/tests/test_protocol_r4.py)
4. `docs: registrar treino H2 e pendências da entrega científica`
   - [README.md](../README.md)
   - [10-protocolo-s5b.md](./10-protocolo-s5b.md)
   - [16-plano-conclusao-e-testes.md](./16-plano-conclusao-e-testes.md)
   - [18-otimizacao-recursos.md](./18-otimizacao-recursos.md)
   - [19-h2-limite-2gb.md](./19-h2-limite-2gb.md)

A pasta local TCC permanece ignorada conforme a política existente. Seus registros
científicos e evidências foram preservados; não há recomendação de forçar sua inclusão.
