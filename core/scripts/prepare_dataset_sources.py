import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from hts_core.adapters.dataset_collect import _get
from hts_core.adapters.dataset_store import read_json, write_json, write_new
from hts_core.application.dataset_pipeline import normalize_sources, pipeline_descriptor
from hts_core.domain.dataset import source_groups, split_groups


def resolve(proposal, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'proposal.json', proposal)
    plan, failures = [], []
    for theme, titles in proposal['themes'].items():
        raw = _get({'action': 'query', 'prop': 'revisions', 'titles': '|'.join(titles), 'redirects': 1, 'rvprop': 'ids|timestamp'})
        write_new(destination/f'{theme}-response.json', raw)
        data = json.loads(raw)
        for page in data['query']['pages']:
            if page.get('missing') or not page.get('revisions'):
                failures.append({'theme': theme, 'page': page.get('title'), 'reason': 'missing'})
                continue
            plan.append({'pageid': page['pageid'], 'revid': page['revisions'][0]['revid'], 'title': page['title'],
                         'theme': theme, 'resolved_utc': datetime.now(timezone.utc).isoformat()})
    if len({e['pageid'] for e in plan}) != len(plan):
        failures.append({'reason': 'redirects resolved to same page; do not count as independent sources'})
    write_json(destination/'fixed-plan.json', sorted(plan, key=lambda e: e['pageid']))
    write_json(destination/'failures.json', failures)
    if failures:
        raise ValueError('plano incompleto; não substituir título silenciosamente')
    return {'resolved': len(plan), 'themes': {t: sum(e['theme'] == t for e in plan) for t in proposal['themes']}}


def prepare(corpus, plan_path, destination, config):
    from hts_core.adapters.dataset_store import digest, inside, seal, write_jsonl
    corpus, destination = Path(corpus), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    plan = read_json(plan_path)
    manifest = read_json(corpus/'manifest.json')
    config['themes'] = {p['title']: p['theme'] for p in plan}
    config['purpose'] = 'source_preparation'
    sources, ledger = normalize_sources(manifest['documents'], lambda e: inside(corpus, e['file']).read_bytes(), destination, config)
    groups, alerts = source_groups(sources, config['near_duplicate_threshold'], config['shingle_size'])
    splits = split_groups(groups, config['seed'], tuple(config['split_percent']))
    exposure = {e['pageid'] for e in read_json(Path(__file__).resolve().parents[1]/'data/refcorpus/manifest.json')['documents']}
    for s in sources:
        s.update(group=groups[s['id']], split=splits[s['id']], exposure='no_overlap_found_in_recorded_development_inventory' if s['pageid'] not in exposure else 'development_refcorpus')
    write_jsonl(destination/'sources.jsonl', sources)
    write_json(destination/'config.json', config)
    write_json(destination/'pipeline.json', pipeline_descriptor())
    write_json(destination/'selection.json', ledger)
    write_json(destination/'group-alerts.json', alerts)
    write_json(destination/'upstream-manifest.json', manifest)
    summary = {'purpose': 'sources_only_no_derived_pairs', 'sources': len(sources), 'groups': len(set(groups.values())),
               'splits': {split: {'sources': sum(s['split'] == split for s in sources),
                                  'groups': len({s['group'] for s in sources if s['split'] == split}),
                                  'themes': {theme: sum(s['theme'] == theme and s['split'] == split for s in sources) for theme in sorted(config['themes'].values())}}
                          for split in ('train', 'validation', 'test')},
               'near_duplicate_alerts': alerts, 'prior_refcorpus_overlap': [s['id'] for s in sources if s['pageid'] in exposure],
               'limits': 'candidate sources; licenses and semantic/common-content review pending; no claim of statistical sufficiency or model pretraining isolation'}
    write_json(destination/'summary.json', summary)
    seal(destination, {'purpose': 'source_preparation', 'state': 'not_experimental_dataset'})
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    resolving = sub.add_parser('resolve')
    resolving.add_argument('--proposal', required=True)
    resolving.add_argument('--out', required=True)
    preparing = sub.add_parser('prepare')
    preparing.add_argument('--corpus', required=True)
    preparing.add_argument('--plan', required=True)
    preparing.add_argument('--config', required=True)
    preparing.add_argument('--out', required=True)
    args = parser.parse_args()
    result = resolve(read_json(args.proposal), args.out) if args.action == 'resolve' else prepare(args.corpus, args.plan, args.out, read_json(args.config))
    print(json.dumps(result, ensure_ascii=False))
