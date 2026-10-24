import subprocess
import sys
import os

# Somente o web possui coleções necessárias nesta etapa.
if not all(os.environ.get(name) for name in ('HTS_SEED_EMAIL', 'HTS_SEED_PASSWORD')):
    sys.exit('Defina HTS_SEED_EMAIL e HTS_SEED_PASSWORD de uma conta local existente; valores não serão exibidos.')
sys.exit(subprocess.run(['docker', 'compose', 'exec', '-T', '-e', 'HTS_SEED_EMAIL', '-e', 'HTS_SEED_PASSWORD', 'web', 'npm', 'run', 'seed']).returncode)
