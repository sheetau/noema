"""Check fixed personal claims independently of favorable consequences."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.script import transcribe
from scripts.compose_claim_conformance import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,FIELDS,STABLE,COMBINED,build,basis,reading_review
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts.check_apparent_liberty import UNITS

REPORT=ROOT/'reports/claim-conformance-v1.json'
CLAIMS=('first','second')
SCENES=('now','low','high','anchor')
DOMAIN=('source','actor','office','person','other')+CLAIMS


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=4)
def fixture(path=LIBRARY):
    doc=deepcopy(document(path));doc['statements']=[]
    from scripts.compose_restricted_utterance import primitive
    text=format_graph(doc,'compact');refs={}
    for name,sort in COMBINED:
        if name=='description':continue
        provider=not sort.startswith('h[')
        text+=primitive('jv'+name,'h[] '+sort if provider else sort)
        refs[name]='k jv'+name+'[]' if provider else 'p jv'+name
    text+='r jvcontent[a a a d] c.r jvfirst[] a.r jvsecond[] a.r jvbenefit[] c.r jvanchor[] d.'
    for name,claim in (('jvone','jvfirst'),('jvtwo','jvsecond')):
        text+='d '+name+'[bindings j[a]] e[b context[w[e[d[v bindings]][n p c b]][g actor a[g person a[w[a[v bindings][n p a b][v actor]][w[a[v bindings][n p b b][v person]][k jvcontent[k '+claim+'[] v actor v person v context]]]]]]]].'
    text+='d jvalias[bindings j[a]] e[k jvone[v bindings]].'
    from scripts.compose_claim_conformance import DESCRIPTION
    # Select among literal Noema quotes created in this evaluation. Aliases can
    # have the same content without being the same target of a requirement.
    text+='r jvselect[a '+DESCRIPTION+' '+DESCRIPTION+' '+DESCRIPTION+'] '+DESCRIPTION+'.'
    text+='d jvdescription[claim a] '+DESCRIPTION+'[k jvselect[v claim r[p jvone] r[p jvtwo] r[p jvalias]]].'
    refs['description']='p jvdescription'
    queries=['k '+name+'['+' '.join(refs[n] for n,t in fields)+']' for name,fields in (
        ('ryb',FIELDS),('ryc',FIELDS[:-1]),('ryd',FIELDS),('rye',STABLE),('ryf',COMBINED))]
    queries+=['k jvbenefit[]']
    if path!=LIBRARY:
        identity=' '.join(refs[n] for n in ('source','actor','office','person'))
        queries+=['k iaustanding['+identity+' k jvanchor[] p jvcases]',
            'k iautreatment['+identity+' k jvanchor[] k jvcontext[] p jvcases]']
    return parse(text+''.join('q['+q+'].' for q in queries))


def values(norms=(3,3,3),fulfilled=3,*,variant='baseline',benefit=True,path=LIBRARY,indices=None,memoize=True,calls=None):
    catalogue=() if variant=='empty_claims' else CLAIMS+('first',) if variant=='duplicate_claims' else CLAIMS[:1] if variant=='omitted_claim' else CLAIMS
    def norm(source,actor,office,description,bindings,polarity,context):
        if calls is not None:calls.append(('norm',source,actor,office,description,bindings.items,polarity,context))
        if variant=='unknown_norm':raise ValueError('Unknown personal requirement')
        expected=('actor','other') if variant=='other_person' else ('person','actor') if variant=='reversed_binding' else ('actor','person')
        if (source,actor,office)!=('source','actor','office') or bindings.items!=expected or not polarity or context not in SCENES[:3]:return False
        mask=norms[SCENES.index(context)]
        return (code_is(description,'jvone') and bool(mask&1)) or (code_is(description,'jvtwo') and bool(mask&2))
    def content(claim,actor,person,context):
        if calls is not None:calls.append(('content',claim,actor,person,context))
        if variant=='unknown_content':raise ValueError('Unknown treatment content')
        expected='other' if variant=='other_recipient' else 'person'
        return actor=='actor' and person==expected and claim in CLAIMS and bool(fulfilled&(1<<CLAIMS.index(claim)))
    def select(claim,first,second,alias):return alias if variant=='alias' and claim=='first' else first if claim=='first' else second
    def claims(person,anchor):
        if calls is not None:calls.append(('claims',person,anchor))
        return SequenceValue(catalogue if (person,anchor)==('person','anchor') else (), '"individual"')
    def scope(person,anchor,claim):
        if variant=='unknown_scope':raise ValueError('Unknown personal claim scope')
        return (person,anchor)==('person','anchor') and claim in CLAIMS and variant!='empty_claims'
    p=dict(arithmetic(),**{'jv'+n:(lambda n=n:n) for n in ('source','actor','office','person')},
        jvcontext=lambda:'now',jvanchor=lambda:'anchor',jvclaims=lambda:SequenceValue(catalogue,'"individual"'),
        jvscope=lambda claim:scope('person','anchor',claim),jvcases=lambda point:variant!='empty_cases' and point in ('low','high'),
        jvrequired=norm,jvcontent=content,jvfirst=lambda:'first',jvsecond=lambda:'second',jvselect=select,
        jvbenefit=lambda:benefit,aa=lambda person:person=='person' and variant!='nonhuman',
        h7k=norm,iauclaims=claims,iauscope=scope)
    doc=deepcopy(fixture(path))
    # The source adapter uses the same literal Noema descriptions as the generic
    # relation; substitute a function alias, not an unchecked foreign CodeValue.
    if path!=LIBRARY:
        row=next(d for d in doc['declarations'] if d['name']=='iaudescription')
        row.update(kind='definition',parameters=[dict(name='claim',sort='individual')],
            body=dict(kind='call',symbol='jvdescription',arguments=[dict(kind='variable',name='claim')]))
        doc['declarations'].remove(row);doc['declarations'].append(row)
        # Callers must follow their dependencies after replacing the primitive.
        delayed=[d for d in doc['declarations'] if d['name'] in ('iaustanding','iautreatment')]
        doc['declarations']=[d for d in doc['declarations'] if d['name'] not in ('iaustanding','iautreatment')]+delayed
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


def alignment():
    r=reading_review()
    return dict(unit=r['source_unit'],text_sha256=r['source_sha256'],status='explicit_interpretive_annotation',
        definitions=['ryb','ryc','ryd','rye','ryf','iaustanding','iautreatment'],adds_new_text_coverage=False,
        semantic_completion=False,dignity_content_unfilled=True,policy_integration_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==reading_review()
    for norms in product(range(4),repeat=3):
        stable=norms[1:]==(3,3)
        assert values(norms)==[norms[0]==3,True,norms[0]==3,stable,stable and norms[0]==3,True]
    assert values(memoize=False)==values()
    for path in (CORE,SOURCE):assert values(path=path,indices=(6,7))==[True,True]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements']==old['statements']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,UNITS,'scripts/compose_claim_conformance.py','scripts/check_claim_conformance.py',
        'tests/test_claim_conformance.py','scripts/check_caused_choice.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='fixed_personal_requirements_fulfillment_and_stability_checked',documents=documents,
        norm_profiles=64,roundtrips=True,source_alignment=alignment(),limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Personal claims and fulfillment checked; dignity and concrete policy remain incomplete')


if __name__=='__main__':main()
