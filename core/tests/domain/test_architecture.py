import ast
import os
import subprocess
import sys
from importlib.util import resolve_name
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[2] / "src/hts_core/domain"
ALLOWED = {"math", "collections", "dataclasses", "re", "unicodedata", "hashlib", "numpy"}


def test_domain_imports_and_calls_stay_within_pure_dependencies():
    forbidden = {"open", "print", "input", "exec", "eval", "__import__", "read_text", "read_bytes",
                 "write_text", "write_bytes", "load", "save", "connect", "request", "urlopen"}
    for path in DOMAIN.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                name = node.module or ""
                if node.level:
                    name = resolve_name("." * node.level + name, "hts_core.domain")
                names = [name]
            for name in names:
                assert name.startswith("hts_core.domain") or name.split(".")[0] in ALLOWED, (path, name)
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                assert name not in forbidden, (path, node.lineno, name)


def test_domain_import_and_representative_execution_have_no_external_io():
    code = r'''
import sys
import numpy
import collections.abc, dataclasses, hashlib, math, re, unicodedata
def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        source = isinstance(path, str) and path.endswith(('.py', '.pyc', '.pyd'))
        reading = mode is None or ('w' not in mode and 'a' not in mode and '+' not in mode)
        if not source or not reading:
            raise RuntimeError('domain file IO: ' + str(path))
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.mkdir', 'os.remove', 'os.rename')):
        raise RuntimeError('domain external IO: ' + event)
sys.dont_write_bytecode = True
sys.addaudithook(audit)
from hts_core.domain import lexical, metrics, preprocess, signature, strings, text, vectors, hybrid
v = lexical.ReferenceIdf(2, {'casa': 1}).vector(['casa'])
assert lexical.cosine(v, v) == 1
assert metrics.mse([1, 2], [2, 2]) == 0.5
assert preprocess.semantic_text(' casa  azul ') == 'casa azul'
assert signature.signature(['casa']) == signature.signature(['casa', 'casa'])
assert strings.ngram_dice('casa', 'casa') == 1
assert text.split_sentences('Casa. Azul.') == ['Casa.', 'Azul.']
assert vectors.alignment_similarity(numpy.ones(2), numpy.ones(2)) > 1.99
assert hybrid.hungarian([[.9, .8], [.85, 0]])['objective'] == 1.65
assert hybrid.similarity_index([[1, 0]], [1], [1, 1])['value'] == 75
assert hybrid.classify_pair('abcde', 'abcdX', .1, .2, .8)['label'] == 'copia_editada'
assert hybrid.operational_cosine(-1) == 0
print('domain import and representative calls: no external IO observed')
'''
    env = {**os.environ, "PYTHONPATH": str(DOMAIN.parents[1])}
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    assert "no external IO observed" in result.stdout
