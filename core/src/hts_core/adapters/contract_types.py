import math


def object_fields(value, fields, path):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f'{path}: objeto exige campos exatos {sorted(fields)}')
    return value


def text(value, path):
    if type(value) is not str or not value.strip():
        raise ValueError(f'{path}: string não vazia exigida')
    return value


def sha256(value, path):
    text(value, path)
    if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError(f'{path}: SHA256 hexadecimal exigido')
    return value


def number(value, path, minimum=0, integer=False, positive=False):
    if type(value) not in ((int,) if integer else (int, float)) or not math.isfinite(value):
        raise ValueError(f'{path}: número finito do tipo contratado exigido, sem booleano')
    if value < minimum or (positive and value <= 0):
        raise ValueError(f'{path}: valor fora do limite')
    return value


def string_list(value, path, allowed=None, empty=False):
    if type(value) is not list or (not value and not empty):
        raise ValueError(f'{path}: lista exigida')
    for item in value:
        text(item, path)
    if len(value) != len(set(value)) or (allowed is not None and not set(value) <= set(allowed)):
        raise ValueError(f'{path}: duplicata ou valor fora do contrato')
    return value
