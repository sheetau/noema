"""Read-only checks of the visual freeze and concrete decoding limitations."""
from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path

from noema.constructed import parse
from scripts.contextual_opening_script import compile_expression

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def visible_signature(compiled):
    # Only what can affect the visible, unwrapped drawing; no dictionary, AST,
    # symbol payload, occurrence path or other invisible annotation is included.
    visible = {k: compiled[k] for k in ('shapes', 'paths', 'width')}
    return hashlib.sha256(json.dumps(visible,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_report():
    manifest = json.loads((ROOT/'data/writing-freeze-v1.json').read_text(encoding='utf-8'))
    mismatches = []
    for group in ('source_sha256','output_sha256'):
        for path, expected in manifest[group].items():
            if not (ROOT/path).is_file() or digest(path) != expected:
                mismatches.append(path)
    if mismatches:
        raise ValueError('Frozen visual assets changed or missing: '+', '.join(mismatches))
    path = 'examples/v016/branch-circle-samples.noema'
    doc = parse((ROOT/path).read_text(encoding='utf-8'))
    registry = {d['name']: i for i,d in enumerate(doc['declarations'])}
    witnesses = []
    for index, replacements, readings in [
        (0, {0:'home'}, ['rain(town)', 'rain(home)']),
        (1, {0:'aki', 1:'nao'}, ['above(birdone,treeone)', 'above(aki,nao)']),
    ]:
        left = doc['statements'][index]
        right = deepcopy(left)
        for position, symbol in replacements.items():
            right['body']['arguments'][position]['symbol'] = symbol
        a = compile_expression(left,reference_order=registry)
        b = compile_expression(right,reference_order=registry)
        witnesses.append(dict(readings=readings, same_registry=True, source_different=left!=right,
                              visible_equal=visible_signature(a)==visible_signature(b),
                              left=left,right=right,visible_sha256=[visible_signature(a),visible_signature(b)]))
    original = doc['statements'][2]
    a = compile_expression(original,reference_order=registry)
    b = compile_expression(original,reference_order={name:len(registry)-1-i for name,i in registry.items()})
    reorder = dict(source=original, same_source=True,
                   registry_order_changes_visible=visible_signature(a)!=visible_signature(b),
                   visible_sha256=[visible_signature(a),visible_signature(b)])
    # Keep the prior meaning checks separate from visual identity. These totals
    # include retained, unused declarations and document-specific constants.
    state = json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    manuscripts = {}
    index = json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))
    for work, active in index['works'].items():
        p = active['document']
        parsed = parse((ROOT/p).read_text(encoding='utf-8'))
        manuscripts[work] = dict(path=p,sha256=digest(p),statements=len(parsed['statements']),
                                declarations=dict(Counter(d['kind'] for d in parsed['declarations'])))
    return dict(schema='noema-writing-readiness-1', visual_freeze_verified=True,
                standalone_decoding_complete=False, collision_witnesses=witnesses,
                registry_order_witness=reorder, manuscripts=manuscripts,
                meaning_checkpoint=state['progress_report'],
                source_sha256={p:digest(p) for p in [path,'data/writing-freeze-v1.json',
                    'scripts/check_writing_freeze.py','scripts/contextual_opening_script.py',
                    'scripts/balanced_circle_script.py']},
                limits=['A successful freeze check is not a successful optical decoder.',
                        'A shared learned vocabulary is allowed; a per-document dictionary/AST sidecar is not.',
                        'No new natural-language coverage or semantic equivalence is certified here.'])


if __name__ == '__main__':
    print(json.dumps(build_report(),ensure_ascii=False,indent=2))
