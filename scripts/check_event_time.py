"""Check local timestamps without equating source events and signal receptions."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import format_graph, parse
from noema.language import convert
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.script import encode, decode
from scripts.check_clock_protocol import MEANINGS
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_synchrony_network import values, source_model
from scripts.compose_event_time import ROOT, definitions, generic_composed, source_composed

REPORT = ROOT / 'reports/event-time-v1.json'
DOMAIN = ('event', 'reception', 'clocka', 'clockb', 'reference', 'remote', 'origin',
          'frame', 'unit', 'other', 'author', 'scope', 'definition')


def fingerprint(cut):
    # Only distinguish the two explicitly supplied rational embeddings 7 and 9.
    return tuple(cut(Fraction(n)) for n in (6, 7, 8, 9))


def binding_checks(source=False):
    constants = '''r za[] a.r zb[] a.r zc[] a.r zd[] h[b] c.'''
    if source:
        text = source_composed()[0]
        query = '''r ze[] h[a a a a d] c.
q[k qt[k za[] k zb[] k zc[] k zd[] k ri[] k ze[]]].'''
    else:
        text = generic_composed()[0]
        query = '''r ca[a] c.r cb[a a a] c.r cc[a a] c.r ci[a] c.
r ce[a a a a h[b] c] c.r cf[a a a a d] c.
r ra[] a.r rb[] a.r rc[] a.r ri[] d.
q[k saf[k za[] k zb[] k zc[] k rc[] k ra[] k rb[] k zd[] k ri[] p ca p cb p cc p ci p ce p cf]].'''
    doc = candidate(text, constants + query)
    base = dict(clocks={'clocka', 'clockb', 'reference'},
        locations={('event', 'remote', 'frame'), ('clocka', 'remote', 'frame'),
                   ('reception', 'origin', 'frame'), ('clockb', 'origin', 'frame')},
        stationary={(clock, 'frame') for clock in ('clocka', 'clockb', 'reference')},
        readings={('clocka', 'event', 'frame', 'unit'): 7,
                  ('clockb', 'reception', 'frame', 'unit'): 9},
        sync={('clocka', 'reference', 'frame', 'unit', 'text'),
              ('clockb', 'reference', 'frame', 'unit', 'text')},
        event='event', clock='clocka', place='remote', value=7, frame='frame', unit='unit', reference='reference')
    cases = {'local_event': (base, True)}
    received = deepcopy(base)
    received.update(event='reception', clock='clockb', place='origin', value=9)
    cases['local_reception'] = (received, True)
    confused = deepcopy(received)
    confused['event'] = 'event'
    cases['remote_reception_is_not_source_time'] = (confused, False)
    for name, key, old, new in (
        ('missing_read', 'readings', ('clocka', 'event', 'frame', 'unit'), None),
        ('wrong_event_read', 'readings', ('clocka', 'event', 'frame', 'unit'), ('clocka', 'reception', 'frame', 'unit')),
        ('wrong_clock_read', 'readings', ('clocka', 'event', 'frame', 'unit'), ('clockb', 'event', 'frame', 'unit')),
        ('wrong_read_frame', 'readings', ('clocka', 'event', 'frame', 'unit'), ('clocka', 'event', 'other', 'unit')),
        ('wrong_read_unit', 'readings', ('clocka', 'event', 'frame', 'unit'), ('clocka', 'event', 'frame', 'other')),
        ('remote_clock', 'locations', ('clocka', 'remote', 'frame'), ('clocka', 'origin', 'frame')),
        ('moving_clock', 'stationary', ('clocka', 'frame'), None),
        ('moving_reference', 'stationary', ('reference', 'frame'), None),
        ('invalid_reference', 'clocks', 'reference', None),
        ('invalid_clock', 'clocks', 'clocka', None),
        ('unsynced', 'sync', ('clocka', 'reference', 'frame', 'unit', 'text'), None),
        ('different_reference', 'sync', ('clocka', 'reference', 'frame', 'unit', 'text'), ('clocka', 'clockb', 'frame', 'unit', 'text')),
        ('different_sync_context', 'sync', ('clocka', 'reference', 'frame', 'unit', 'text'), ('clocka', 'reference', 'frame', 'unit', 'other')),
    ):
        changed = deepcopy(base)
        collection = changed[key]
        if isinstance(collection, dict):
            number = collection.pop(old)
            if new is not None: collection[new] = number
        else:
            collection.remove(old)
            if new is not None: collection.add(new)
        cases[name] = (changed, False)
    for name, key, value in (('wrong_value', 'value', 9), ('wrong_frame', 'frame', 'other'),
                             ('wrong_unit', 'unit', 'other'), ('wrong_reference', 'reference', 'clockb')):
        changed = deepcopy(base)
        changed[key] = value
        cases[name] = (changed, False)
    rows = {}
    for name, (facts, expected) in cases.items():
        def reading(clock, event, frame, unit, cut):
            number = facts['readings'].get((clock, event, frame, unit))
            return number is not None and fingerprint(cut) == tuple(n < number for n in (6, 7, 8, 9))
        def sync(*args): return args in facts['sync']
        model = source_model(doc) if source else {}
        model.update(za=lambda:facts['event'], zb=lambda:facts['clock'], zc=lambda:facts['place'],
            zd=lambda:FunctionValue(('number',), 'truth', lambda q:q < facts['value']),
            ra=lambda:facts['frame'], rb=lambda:facts['unit'], rc=lambda:facts['reference'], ri=lambda:'text',
            ca=lambda clock:clock in facts['clocks'], cb=lambda *args:args in facts['locations'],
            cc=lambda *args:args in facts['stationary'], ci=lambda unit:unit == 'unit', ce=reading)
        if source:
            model['ze'] = lambda:FunctionValue(('individual',)*4 + ('situation',), 'truth', sync)
        else:
            model['cf'] = sync
        actual = values(doc, model, DOMAIN)[0]
        if actual != expected: raise ValueError('Event reading binding differs: ' + name)
        rows[name] = actual
    return {'cases': rows, 'full_real_cut_synchrony_evaluated': False,
            'synchrony_is_supplied_relation': True,
            'probe_scope': 'Only explicit rational embeddings 7 and 9; not arbitrary cut equality.'}


def equality_checks():
    text = format_graph(convert(parse((ROOT/'examples/v011/real-cuts.noema').read_text(encoding='utf-8')), '0.14'), 'compact')
    text += definitions()
    claims = {
        'embedded_values_equal': ('s[f x b[f y b[z[k sag[k bb[v x] k bb[v y] p bc]][e[v x][v y]]]]].', 'valid'),
        'common_shift_preserves_equality': ('s[f x b[f y b[f offset b[z[k sag[k bb[k ab[v x v offset]] k bb[k ab[v y v offset]] p bc]][k sag[k bb[v x] k bb[v y] p bc]]]]]].', 'valid'),
        'one_clock_shift_must_be_zero': ('s[f x b[f offset b[z[k sag[k bb[v x] k bb[k ab[v x v offset]] p bc]][e[v offset][n p a b]]]]].', 'valid'),
        'one_way_inclusion_does_not_imply_equality': ('s[y[k bc[k bb[n p h b] k bb[n p j b]]][k sag[k bb[n p h b] k bb[n p j b] p bc]]].', 'invalid'),
    }
    rows = {}
    for name, (claim, expected) in claims.items():
        row = verify(parse(text + claim), MEANINGS, timeout_ms=15000)[0]
        if row['status'] != expected: raise ValueError('Cut equality law differs: ' + name)
        rows[name] = row
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    previous = parse((ROOT/'examples/v014/einstein-synchrony-network.noema').read_text(encoding='utf-8'))
    if doc['statements'][:-1] != previous['statements']: raise ValueError('Previous assertion changed')
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    expected = ('definition', 'author', 'qu', 'scope', 'text')
    for index in range(-1, 5):
        model = source_model(doc)
        # Every physical callback is forbidden: only the quotation is attributed.
        def forbidden(*args): raise ValueError('Timestamp contents unexpectedly executed')
        model = {name:forbidden for name in model}
        model.update(rj=lambda:'definition', rd=lambda:'author', rh=lambda:'scope', ri=lambda:'text')
        target = list(expected)
        if index >= 0: target[index] = 'other'
        model['uj'] = lambda node,author,rule,scope,context: (node,author,symbol(rule),scope,context) == tuple(target)
        actual = values(doc, model, DOMAIN)[0]
        if actual != (index == -1): raise ValueError('Definition attribution differs')
        rows['baseline' if index == -1 else 'wrong_' + ('node','author','rule','scope','context')[index]] = actual
    return rows


def alignment():
    units = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'einstein-1905:u0018')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != 'b2fea62ee64ba6bc7aae1ee4d8efb0e739ed115a90500377e2a601b982d64b9f': raise ValueError('Pinned event-time source differs')
    start = unit['text'].index('Die „Zeit“ eines Ereignisses')
    return {'segments':[{'unit':unit['id'], 'unit_sha256':digest, 'start':start, 'end':len(unit['text']),
        'source':unit['text'][start:], 'definitions':['sae','saf','qt','qu'],
        'status':'partial_explicit_reading', 'full_semantic_equivalence':False,
        'remaining':['physical grounding of clocks and local readings', 'existence and uniqueness of time assignments',
                     'first-sentence discourse', 'facsimile review']}], 'verified_full_units':0}


def build_report():
    import z3
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text: raise ValueError('Stored event-time document differs')
        doc = parse(text)
        for notation in ('compact','full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form,'v2'))) != doc: raise ValueError('Event-time roundtrip differs')
        documents[basis['document']] = audit_basis(doc,basis)
    paths = [*documents, 'data/event-time-basis-v1.json', 'data/einstein-event-time-basis-v1.json',
        'examples/v014/einstein-synchrony-network.noema', 'examples/v011/real-cuts.noema',
        'scripts/compose_event_time.py', 'scripts/check_event_time.py', 'scripts/check_synchrony_network.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'noema/rational_proofs.py']
    return {'status':'partial_local_event_time_and_common_reference', 'documents':documents,
        'bindings':binding_checks(), 'source_adapter':binding_checks(True), 'rational_equality':equality_checks(),
        'attribution':attribution_checks(), 'alignment':alignment(), 'roundtrips':True,
        'z3_version':z3.get_version_string(), 'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'full_physical_synchrony_verified':False,
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Event-time report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Local event bindings, source adapter, rational equality and definition attribution checked')


if __name__ == '__main__': main()
