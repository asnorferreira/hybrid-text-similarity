from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

from hts_core.adapters.dataset_store import digest, write_json, write_new
from hts_core.adapters.refcorpus import API, USER_AGENT


def _get(params):
    query = urllib.parse.urlencode({'format': 'json', 'formatversion': 2, **params})
    request = urllib.request.Request(API + '?' + query, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def collect_fixed(plan, destination, transport=_get, pause=1):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'plan.json', plan)
    records, failures = [], []
    try:
        rights_bytes = transport({'action': 'query', 'meta': 'siteinfo', 'siprop': 'rightsinfo'})
        write_new(destination/'rightsinfo-response.json', rights_bytes)
        rights = json.loads(rights_bytes)['query']['rightsinfo']
    except Exception as exc:
        write_json(destination/'collection-failures.json', [{'stage': 'rightsinfo', 'type': type(exc).__name__}])
        raise
    for item in plan:
        try:
            payload = transport({'action': 'query', 'prop': 'revisions', 'revids': item['revid'],
                                 'rvprop': 'ids|timestamp|content', 'rvslots': 'main'})
            response_file = f"responses/{item['pageid']}-{item['revid']}.json"
            write_new(destination/response_file, payload)
            page = json.loads(payload)['query']['pages'][0]
            revision = page['revisions'][0]
            if page['pageid'] != item['pageid'] or revision['revid'] != item['revid']:
                raise ValueError('identidade fixa divergente')
            raw = revision['slots']['main']['content'].encode('utf-8')
            filename = f"raw/{page['pageid']}-{revision['revid']}.wiki"
            write_new(destination/filename, raw)
            records.append({'title': page['title'], 'pageid': page['pageid'], 'revid': revision['revid'],
                            'url': f"https://pt.wikipedia.org/w/index.php?oldid={revision['revid']}",
                            'history_url': f"https://pt.wikipedia.org/w/index.php?curid={page['pageid']}&action=history",
                            'retrieved_at': datetime.now(timezone.utc).isoformat(), 'rev_timestamp': revision['timestamp'],
                            'license': rights['text'], 'license_reference': rights['url'], 'license_status': 'historical_declared',
                            'license_check': 'API rightsinfo saved; per-source attribution/imported-content review pending',
                            'file': filename, 'sha256': digest(raw), 'response_sha256': digest(payload), 'response_file': response_file,
                            'hash_definition': 'raw revision slots.main.content UTF-8 without BOM; HTTP bytes stored separately'})
        except Exception as exc:
            failures.append({'pageid': item['pageid'], 'revid': item['revid'], 'type': type(exc).__name__})
        if pause:
            time.sleep(pause)
    write_json(destination/'manifest.json', {'source': 'pt.wikipedia.org', 'documents': records,
                                          'rightsinfo_sha256': digest(rights_bytes)})
    write_json(destination/'collection-failures.json', failures)
    if failures:
        raise ValueError('coleta incompleta; respostas/falhas preservadas')
    return {'collected': len(records), 'license_scope': 'site terms recorded; individual source review still required'}
