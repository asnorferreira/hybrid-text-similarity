import subprocess
import sys

# Somente o web possui coleções necessárias nesta etapa.
sys.exit(subprocess.run(['docker', 'compose', 'exec', '-T', 'web', 'npm', 'run', 'seed']).returncode)
