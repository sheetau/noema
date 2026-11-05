"""Small distinguishing interpretations; no cumulative historical suites."""
import json
from copy import deepcopy
from noema.constructed_semantics import evaluate_document, Content
from noema.constructed_discourse import normalize_document
from scripts.general_pragmatics import *


def ref(n): return dict(kind='function_ref', symbol=n)
def quoted(n, sort):
    return dict(kind='quote', body=call(n) if sort == DC else ref(n))
def key(x):
    if hasattr(x, 'syntax'): return json.loads(x.syntax)['symbol']
    return x
def unknown(*xs): raise ValueError('Unknown interpretation')


def fixture(name):
    decl = next(d for d in raw() if d['name'] == name)
    d = composed(); values = {}; primitives = {}; expressions = []; relations = {}
    def add(n, ps, result, impl):
        d['declarations'].append(dict(kind='primitive', name=n, parameters=ps, result=result)); primitives[n] = impl
    for p in decl['parameters']:
        n, t = p['name'], p['sort']; symbol = 'fixture' + n
        if t in (I, S) if isinstance(t, str) else False:
            value = ('later' if n == 'outcome' else 'now') if t == S else ('b' if n in ('recipient','target') else 'a')
            values[n] = value; add(symbol, [], t, lambda value=value: value); expressions.append(call(symbol))
        elif t['kind'] == 'description':
            inner = t['result']; values[n] = symbol
            add(symbol, inner['parameters'] if isinstance(inner,dict) else [], inner['result'] if isinstance(inner,dict) else inner, unknown)
            expressions.append(quoted(symbol, t))
        elif t['kind'] == 'sequence':
            add(symbol, [], I, lambda:'a'); values[n] = ('a',)
            expressions.append(dict(kind='sequence', element=I, items=[call(symbol)]))
        else:
            add(symbol, t['parameters'], t['result'], lambda *xs: True); expressions.append(ref(symbol)); relations[n] = symbol
    expected = {}
    def expect(n, *roles):
        if n in relations: expected[n] = tuple(values[r] if r in values else r for r in roles)
    expect('occurs','activity','context'); expect('presents','person','activity','context')
    expect('conveys','activity','recipient','subject','message','context')
    expect('sourcefeature','source','a','context'); expect('targetfeature','target','b','context')
    expect('associated','sign','target','context'); expect('selected','occurrence','sign','target','context')
    expect('echoes','person','activity','echoed','context'); expect('distances','person','activity','echoed','context')
    expect('interprets','person','activity','echoed','intended','context')
    expect('expresses','person','recipient','activity','subject','attitude','context')
    expect('claims','person','activity','institution','rule','status','context')
    expect('authorized','person','activity','institution','rule','status','context')
    expect('before','context','outcome'); expect('belongs','frame','voice','world')
    expect('marked','person','recipient','activity','community','role','context')
    for relation, row in expected.items():
        primitives[relations[relation]] = lambda *xs, row=row: tuple(map(key,xs)) == row
    if 'mapping' in relations: primitives[relations['mapping']] = lambda x:'b' if x == 'a' else 'a'
    if 'licensed' in relations:
        primitives[relations['licensed']] = lambda source,target,literal,intended,mapping,context: (
            source == values['source'] and target == values['target'] and key(literal) == values['literal']
            and key(intended) == values['intended'] and mapping('a') == 'b' and context == values['context'])
    for role in ('precondition','status','content'):
        if role in values: primitives[values[role]] = lambda:Content(('now','later'),(True,True))
    if name == 'expressivesincere': primitives[values['attitude']] = lambda x:Content(('now','later'),(x == values['person'],False))
    d['statements'] = [dict(kind='ask', body=call(name,*expressions))]
    return normalize_document(d), primitives, expected, values


def value(d, m):
    return evaluate_document(d, individuals=('a','b'), situations=('now','later'), primitives=m)[0]['value']


def diagnostics():
    rows=[]
    for declaration in raw():
        name=declaration['name']; d,m,expected,values=fixture(name)
        assert value(d,m) is True, name
        count=0
        for relation, arguments in expected.items():
            for slot, argument in enumerate(arguments):
                wanted=list(arguments); wanted[slot] = 'b' if argument == 'a' else 'a'
                changed={**m,'fixture'+relation:lambda *xs,wanted=tuple(wanted):tuple(map(key,xs)) == wanted}
                assert value(d,changed) is False,(name,relation,slot)
                count+=1
        rows.append(dict(name=name,native_body=True,slot_diagnostics=count))
    return rows


def build_report():
    from scripts.two_work_inventory import read, sha
    paths=['scripts/check_general_pragmatics.py','scripts/general_pragmatics.py','scripts/general_language.py',
           'data/general-language-catalog-v1.json','tests/test_general_pragmatics.py','noema/constructed_semantics.py',
           'noema/constructed_discourse.py']
    pins={**read('data/general-language-catalog-v1.json')['source_sha256'],**{p:sha(p) for p in paths}}
    return dict(scope='Two-value slot diagnostics, not an exhaustive semantic proof', definitions=diagnostics(),
                new_primitives=0, source_sha256=pins)
