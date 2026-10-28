"""Bind unchanged visible evidence across an explicit manuscript selection change."""
from functools import lru_cache

from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.review_registry import merge_pins
from scripts import compose_auxiliary_reference_order as correction

ROOT = correction.ROOT
PRIOR = 'reports/einstein-two-force-wordings-visible-v1.json'
STATE = 'data/work-state.json'
SNAPSHOT = 'data/work-state-before-auxiliary-reference-order-v1.json'
REPORT = 'reports/auxiliary-reference-order-visible-parent-binding-v1.json'


def prepare():
    prior = correction.read(PRIOR)
    expected = prior['source_sha256'][STATE]
    target = ROOT / SNAPSHOT
    if target.exists():
        assert digest(target.read_bytes()) == expected
    else:
        raw = (ROOT / STATE).read_bytes()
        assert digest(raw) == expected, 'Save the original selection before changing it'
        with target.open('xb') as stream:
            stream.write(raw)


def checked_parent_pins():
    """Only the named selection snapshot may stand for a historical input."""
    prior = correction.read(PRIOR)
    pins = prior['source_sha256'] | prior['artifact_sha256']
    expected = pins.pop(STATE)
    assert SNAPSHOT not in pins
    assert digest((ROOT / SNAPSHOT).read_bytes()) == expected
    pins[SNAPSHOT] = expected
    validate_hashes(ROOT, pins)
    pins[PRIOR] = digest((ROOT / PRIOR).read_bytes())
    return pins


@lru_cache(None)
def build_report():
    pins = checked_parent_pins()
    prior = correction.read(PRIOR)
    old = load_catalog(ROOT, correction.PARENT_BASIS)
    new = load_catalog(ROOT, correction.BASIS)
    indices = set()
    bridges = []
    for path in sorted(prior['source_sha256']):
        if not (path.startswith('data/einstein') and 'bridge' in path and path.endswith('.json')):
            continue
        bridge = correction.read(path)
        positions = bridge.get('source_statement_indices')
        if positions is None:
            assert type(bridge.get('source_statement_index')) is int, path
            positions = [bridge['source_statement_index']]
        assert bridge.get('source_document') in (None, correction.PARENT), path
        assert all(type(i) is int and 0 <= i < len(old.document['statements']) for i in positions)
        indices.update(positions)
        bridges.append(dict(path=path, positions=positions))
    # Retained early bridges include one extra historical selection. This is a
    # conservative dependency check, not a new progress-count calculation.
    assert len(indices) == 178 and len(bridges) == 66
    assert not indices.intersection({40, 41})
    selected = sorted(indices)
    before = selection_binding(old, selected)
    after = selection_binding(new, selected)
    assert before == after, 'A retained visible source selection changed'
    assert correction.read(correction.ANNOTATIONS)['entries'] == correction.read(correction.PARENT_ANNOTATIONS)['entries']
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'], strict=True)) if a != b] == [40, 41]
    merge_pins(pins, old.source_sha256)
    merge_pins(pins, new.source_sha256)
    for path in (correction.ANNOTATIONS, correction.PARENT_ANNOTATIONS,
                 'scripts/auxiliary_reference_order_parent_evidence.py'):
        merge_pins(pins, {path: digest((ROOT / path).read_bytes())})
    return dict(status='unchanged_visible_parent_bound_to_new_source_selection',
        prior_report=PRIOR, historical_input_substitution={STATE: dict(path=SNAPSHOT, sha256=pins[SNAPSHOT])},
        original_report_and_hashes_unchanged=True, all_other_prior_inputs_and_svg_artifacts_unchanged=True,
        source_before=correction.PARENT, source_after=correction.FULL,
        prior_source_binding=before, new_source_binding=after, bridge_selections=bridges,
        checked_unique_source_selections=len(indices), changed_source_positions=[40, 41],
        retained_visible_source_assertions=177, new_visible_source_assertions=0,
        limitations=['過去の設定ファイルは元の正確なbytesを別パスに保存する。過去reportのhashを更新しない。',
                    '178は保持された初期bridgeも含む比較対象であり、円文字統合の完了件数177を変更しない。',
                    '旧検証器を新しい選択に無条件で合格させる記録ではない。旧版の再現には保存した設定又は当時のGit版を用いる。',
                    '次の円文字統合はこの明示的な継承根拠と新しい選択を別々に固定し、新規部分を検証する。'],
        source_sha256=pins)
