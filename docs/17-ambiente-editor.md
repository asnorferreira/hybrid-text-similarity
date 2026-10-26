# Importações e ambiente do editor

O ambiente local foi instalado a partir dos locks: Python 3.11.9 em
`core/.venv`, todos os grupos do uv e dependências Node em `web/node_modules`.
O PyTorch instalado é CPU. Nenhum servidor ou contêiner permanente é necessário
para o editor. Testes e experimentos continuam executados em Docker Engine.

A [configuração do VS Code](../.vscode/settings.json) seleciona
`${workspaceFolder}/core/.venv/bin/python` e inclui o pacote local no caminho
de análise. O log real do Pylance confirmou a adoção desse interpretador.
Não foram desativados diagnósticos de importação ou de tipos. Artefatos,
evidências, modelos e dependências geradas ficam fora da indexação de código
próprio para reduzir trabalho desnecessário do analisador. A indexação global
de bibliotecas foi desativada (a análise de erros continua ativa); o processo
do Pylance tem limite de heap de 1,5 GiB, aplicado ao reiniciar o servidor.

Para restaurar o ambiente após uma cópia limpa:

```bash
uv sync --project core --frozen --all-groups --python 3.11.9
npm ci --prefix web --ignore-scripts --no-audit --no-fund
```

Abra a raiz do projeto no VS Code. Se uma janela antiga mantiver avisos em
cache, execute **Developer: Reload Window**; em **Python: Select Interpreter**,
o caminho correto é `core/.venv/bin/python`. O arquivo local
`hts-workspace.pth`, não versionado e dentro da virtualenv, também permite
resolver os pacotes do projeto no interpretador. Ele pode ser recriado após
uma reinstalação; a análise do editor usa os caminhos versionados e não depende
desse arquivo.

O [perfil Dev Container](../.devcontainer/devcontainer.json) continua opcional.
Ele usa o mesmo lock, não inicia Mongo/web/core HTTP e para ao fechar a janela
remota. Não foi iniciado nesta sessão. Não é necessário abri-lo para corrigir
as importações locais e seus limites não são os limites de treinamento.

Os cabeçalhos editoriais Python foram removidos. As diretivas de tipos geradas
pelo Next em `next-env.d.ts`, as licenças e as evidências históricas foram
preservadas. A remoção do cabeçalho de `refcorpus.py` possui migração explícita
que verifica os bytes anteriores e atuais; o snapshot numérico RG-01 permanece
intacto. A [evidência](../TCC/evidencias/codex-editor-01/relatorio.md) registra
instalação, verificações e eventuais falhas de execução.
