import hashlib
import math
import re


def stable_id(*parts: str) -> str:
    payload = ''.join(f'{len(part)}:{part}' for part in parts)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def ranked(values, seed, context):
    return sorted(values, key=lambda value: (stable_id(str(seed), context, str(value)), str(value)))


def source_groups(sources, threshold=.8, shingle_size=5):
    if not 0 < threshold <= 1 or shingle_size < 1:
        raise ValueError('parâmetros de agrupamento inválidos')
    parent = {s['id']: s['id'] for s in sources}

    def find(value):
        while parent[value] != value:
            value = parent[value]
        return value

    def shingles(text):
        words = re.findall(r'\w+', text.casefold())
        return {tuple(words[i:i + shingle_size]) for i in range(len(words) - shingle_size + 1)}

    ordered = sorted(sources, key=lambda s: s['id'])
    representations = {s['id']: shingles(s['text']) for s in ordered}
    alerts = []
    for i, left in enumerate(ordered):
        for right in ordered[i + 1:]:
            a, b = representations[left['id']], representations[right['id']]
            overlap = len(a & b) / len(a | b) if a | b else 0
            same_page = left['provider'] == right['provider'] and left['pageid'] == right['pageid']
            identical = left['text'] == right['text']
            if same_page or identical or overlap >= threshold:
                x, y = sorted((find(left['id']), find(right['id'])))
                parent[y] = x
                alerts.append({'left': left['id'], 'right': right['id'], 'jaccard': overlap,
                               'reason': 'page' if same_page else 'exact' if identical else 'near'})
    groups = {s['id']: find(s['id']) for s in ordered}
    return groups, alerts


def split_groups(groups, seed, proportions=(70, 15, 15)):
    if len(proportions) != 3 or any(p <= 0 for p in proportions) or sum(proportions) != 100:
        raise ValueError('proporções inválidas')
    unique = ranked(set(groups.values()), seed, 'split-groups-v1')
    exact = [len(unique) * p / 100 for p in proportions]
    counts = [math.floor(x) for x in exact]
    for i in sorted(range(3), key=lambda i: (-(exact[i] - counts[i]), i))[:len(unique) - sum(counts)]:
        counts[i] += 1
    allocated, offset = {}, 0
    for name, count in zip(('train', 'validation', 'test'), counts):
        allocated.update({g: name for g in unique[offset:offset + count]})
        offset += count
    return {source: allocated[group] for source, group in sorted(groups.items())}


def edit_characters(text, rate, seed):
    if not 0 < rate <= 1:
        raise ValueError('taxa deve pertencer a (0,1]')
    eligible = [i for i, char in enumerate(text) if char.isalpha() and char.islower()]
    count = min(len(eligible), math.floor(len(eligible) * rate + .5))
    positions = ranked(eligible, seed, 'character-substitutions')[:count]
    output, operations = list(text), []
    for i in sorted(positions):
        before = output[i]
        after = 'x' if before != 'x' else 'z'
        output[i] = after
        operations.append({'position': i, 'before': before, 'after': after, 'operation': 'substitute'})
    return ''.join(output), {'requested_rate': rate, 'eligible': len(eligible), 'operations': operations,
                             'realized_count': count, 'realized_rate': count / len(eligible) if eligible else 0}


def reorder_indices(count, seed):
    if count < 2:
        raise ValueError('reordenação exige pelo menos duas sentenças')
    result = ranked(range(count), seed, 'sentence-permutation')
    if result == list(range(count)):
        result = result[1:] + result[:1]
    return result


def reuse_fraction(sentences, focal_source):
    if not sentences:
        raise ValueError('denominador vazio')
    numerator = sum(any(a['source_id'] == focal_source for a in s['ancestors']) for s in sentences)
    return {'numerator': numerator, 'denominator': len(sentences)}
