import hashlib
from pathlib import Path
import time
from typing import Any

import numpy as np

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import save_json_new
from hts_core.adapters.training_contract import memory_snapshot
from hts_core.application.calibration import derivation_examples, fit_calibration, predict_platt
from hts_core.domain.experiments import classification_report
from hts_core.domain.hybrid import classify_pair, fuse
from hts_core.domain.lexical import cosine
from hts_core.domain.preprocess import lexical_tokens
from hts_core.domain.strings import levenshtein


def run_p1(dataset, semantic, config, bindings, destination, started=None,
           resource_loader=None, clock=time.monotonic, resources=memory_snapshot) -> dict[str, Any]:
    from hts_core.adapters.calibration_resources import load_p1_resources
    from hts_core.adapters.nlp import analyze, STOPWORDS
    from hts_core.adapters.calibration_plot import save_reliability
    started = clock() if started is None else started
    out = Path(destination)
    out.mkdir(parents=True,exist_ok=False)
    lexical,policy,frozen = (resource_loader or load_p1_resources)(semantic)
    rows,counts = derivation_examples(dataset,'validation')
    if not rows:raise ValueError('P1 has no eligible validation sentence pairs')
    cache = {}; scored = []; decisions = []; diagnostics = []
    def guard():
        if clock()-started >= config['budget']['feature_wall_seconds']:
            raise TimeoutError('P1 feature preparation wall limit reached')
        if resources()['rss_bytes'] > config['budget']['process_rss_limit_bytes']:
            raise MemoryError('P1 inference RSS cap reached')
    for row in rows:
        guard()
        pair = row['input']
        texts = (pair.source_text,pair.suspect_text)
        for text in texts:
            if text not in cache:
                guard()
                embedding,windows = semantic.encode([text])
                vector = lexical.vector(lexical_tokens(text,analyze,STOPWORDS))
                cache[text] = (vector,embedding[0])
                diagnostics.append(dict(text_sha256=hashlib.sha256(text.encode()).hexdigest(),windows=windows))
        (a,u),(b,v) = [cache[t] for t in texts]
        l = float(np.clip(cosine(a,b),0,1)); c = float(np.clip(u@v,-1,1))
        _,fused = fuse([[l]],[[c]])
        score = float(fused[0,0])
        scored.append(dict(id=row['id'],component=row['component'],target=row['target'],score=score))
        label = classify_pair(*texts,l,max(0,c),levenshtein(*texts),
            **{k:policy[k] for k in ('edited_threshold','low_threshold','paraphrase_threshold','lexical_high')})['label']
        decisions.append('derived' if label!='sem_correspondencia_detectada' else 'not_derived')
    guard()
    fitted_bindings = dict(bindings,calibration_resource_identity=frozen['identity'],
                          calibration_observations_identity=identity(scored))
    result = fit_calibration(scored,'validation',fitted_bindings)
    result.update(counts=counts,score_resources=frozen,unique_encoded_texts=len(cache),
                  labels_independent_semantic_reference=False,elapsed_seconds=clock()-started,
                  q5v2_decision=dict(scope='binary decision comparator; not a probability or calibrated index',
                      metrics=classification_report(['derived' if r['target'] else 'not_derived' for r in scored],
                                                    decisions,['derived','not_derived'])))
    save_json_new(out/'observations.json',scored)
    save_json_new(out/'token-windows.json',diagnostics)
    save_json_new(out/'platt.json',result['model'])
    loaded = read_json(out/'platt.json')
    original = predict_platt(result['model'],[r['score'] for r in scored],fitted_bindings)
    reloaded = predict_platt(loaded,[r['score'] for r in scored],fitted_bindings)
    if original != reloaded:raise ValueError('P1 calibration reload differs')
    result['reload_verification'] = dict(loaded=True,maximum_error=0.,n=len(reloaded),
        identity=loaded['identity'],sha256=hashlib.sha256((out/'platt.json').read_bytes()).hexdigest())
    for kind in ('calibrated','raw'):
        save_reliability(out/f'reliability-fit-{kind}.svg',result['fit_diagnostics'][kind],
                         f'P1 {kind}: ressubstituicao, sem avaliacao independente')
    if result['evaluation']['metrics'] is not None:
        save_reliability(out/'reliability-out-of-fold.svg',result['evaluation']['metrics'],'P1 fora do fold por componente')
    save_json_new(out/'result.json',result)
    return result
