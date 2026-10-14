"""Check joint consistency, contained opposition and the scope of belief."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded,callbacks
from scripts import check_unsettled_teaching as previous
from scripts.compose_limits import call as k
from scripts.compose_contained_conflict import (ROOT,PARENT,BUILDERS,SCOPE,CLASHES,CANDIDATES,
    SATISFIES,COHERENT,JOINT,CONFLICT,BELIEF,SPEECH_FIELDS)

REPORT=ROOT/'reports/contained-conflict-v1.json'
EXTRA={'standard':('jyaa','a'),'scope':('jyab',SCOPE),'clashes':('jyac',CLASHES),'candidates':('jyad',CANDIDATES)}
DOMAIN=previous.DOMAIN+('standard','c3','c4','c5','c6')
SCENES=('j0','j1','p0','p1','p2','p3','actual','elsewhere')
WORLDS=('p0','p1','p2','p3')
TRUTHS={'c1':(True,True,False,False),'c2':(True,False,True,False),
    'c3':(False,True,True,True),'c4':(False,False,False,False),
    'c5':(True,True,True,True),'c6':(False,False,True,True)}


def expression(name):
    return k(EXTRA[name][0]) if name in EXTRA else previous.expression(name)


def query_document(text):
    if {symbol for symbol,_ in EXTRA.values()} & {d['name'] for d in parse(text)['declarations']}:
        raise ValueError('Contained conflict fixture symbols collide')
    previous_names=set(previous.SYMBOLS.values())|{'zzz','zzy','zzx'}
    if previous_names & {d['name'] for d in parse(text)['declarations']}:raise ValueError('Inherited fixture symbols collide')
    extra=''.join('r '+previous.SYMBOLS[name]+'[] '+sort+'.' for name,sort in previous.FIELDS)
    extra+='r zzz[a d] c.d zzy[subject a] f[j s[b context[k zzz[v subject v context]]]].'
    extra+='d zzx[subject a] f[j s[b context[k zzz[v subject v context]]]].'
    extra+=''.join('r '+symbol+'[] '+sort+'.' for symbol,sort in EXTRA.values())
    queries=[k('rgq',*(expression(n) for n,_ in SATISFIES))]
    for name in ('document','standard'):
        queries.append(k('rgr',expression(name),*(expression(n) for n,_ in COHERENT[1:])))
    for symbol,fields in (('rgs',JOINT),('rgt',JOINT),('rgu',CONFLICT),('rgv',CONFLICT),
        ('rgw',BELIEF),('rgx',BELIEF),('rgy',BELIEF),('hzbx',SPEECH_FIELDS)):
        queries.append(k(symbol,*(expression(n) for n,_ in fields)))
    adapter=k('rg2',*(expression(n) for n in ('scope','contains','contents')))
    queries.append(k('rgu',*(adapter if n=='clashes' else expression(n) for n,_ in CONFLICT)))
    doc=candidate(text,extra+''.join('q['+q+'].' for q in queries))
    if len(doc['statements'])!=12:raise ValueError('Unexpected conflict query layout')
    return doc


def model_for(doc,*,parts=('c1','c2'),standard=('c3',),scope=(True,True,True,True),
    candidates=(True,True),judged=(False,False,False,False),actual=(False,False),variant='baseline'):
    model=previous.model_for(doc)
    model[EXTRA['standard'][0]]=lambda:'standard'
    def contains(document,claim,anchor):
        expected='elsewhere' if variant=='contains_anchor' else 'actual'
        if variant=='membership_only_at_candidates':expected='j0'
        owner='other' if variant=='contains_document' else 'doctrine'
        return anchor==expected and ((document==owner and claim in parts) or (document=='standard' and claim in standard))
    def contents(claim):
        if variant=='unknown_contents':raise ValueError('Conflict content interpretation missing')
        return Content(SCENES,(False,False,*TRUTHS.get(claim,(False,)*4),False,False))
    def selected(anchor,point):
        return anchor==('elsewhere' if variant=='scope_anchor' else 'actual') and any(
            enabled and point==name for enabled,name in zip(scope,WORLDS))
    def choices(person,document,standard,anchor,point):
        expected=['person','doctrine','standard','actual']
        for i,label in enumerate(('person','document','standard','anchor')):
            if variant=='candidates_'+label:expected[i]='elsewhere' if label=='anchor' else 'other'
        return [person,document,standard,anchor]==expected and any(
            enabled and point==name for enabled,name in zip(candidates,('j0','j1')))
    def clashes(claim,standard,point):
        if standard!=('other' if variant=='clashes_standard' else 'standard'):return False
        names=('c4','c5') if variant=='clashes_claim' else ('c1','c2')
        if claim not in names:return False
        part=names.index(claim)
        if point==('elsewhere' if variant=='clashes_point' else 'actual'):return actual[part]
        return any(point==scene and judged[2*part+i] for i,scene in enumerate(('j0','j1')))
    callbacks(doc,model,{previous.SYMBOLS['contains']:contains,previous.SYMBOLS['contents']:contents,
        EXTRA['scope'][0]:selected,EXTRA['candidates'][0]:choices,EXTRA['clashes'][0]:clashes})
    return model


def evaluate(doc,model,indices=None):
    if indices is not None:doc={**doc,'statements':[doc['statements'][i] for i in indices]}
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in used},DOMAIN,SCENES)


def logic_expected(parts,standard,mask):
    worlds=[i for i,selected in enumerate(mask) if selected]
    sat=lambda claims,i:all(TRUTHS[c][i] for c in claims)
    first=any(sat(parts,i) for i in worlds);second=any(sat(standard,i) for i in worlds)
    joint=any(sat(parts,i) and sat(standard,i) for i in worlds)
    contained=any(any(TRUTHS[c][i] for i in worlds) and second and
        not any(TRUTHS[c][i] and sat(standard,i) for i in worlds) for c in parts)
    return [not parts,first,second,joint,first and second and not joint,contained]


def finite_checks(texts):
    docs=[query_document(text) for text in texts]
    def run(indices=None,**options):
        rows=[evaluate(doc,model_for(doc,**options),indices) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted conflict scope differs')
        return rows[0]
    logic_indices=[0,1,2,3,4,11]
    logical=[]
    subsets=[tuple(c for c,chosen in zip(('c1','c2','c3'),mask) if chosen) for mask in product((False,True),repeat=3)]
    for parts,standard in product(subsets,repeat=2):
        row=run(logic_indices,parts=parts,standard=standard)
        if row!=logic_expected(parts,standard,(True,)*4):raise ValueError('Joint and partwise consistency collapsed')
        logical.append(dict(parts=list(parts),standard=list(standard),results=row))
    scopes=[]
    for mask in product((False,True),repeat=4):
        row=run(logic_indices,scope=mask)
        if row!=logic_expected(('c1','c2'),('c3',),mask):raise ValueError('Empty or restricted scope overinterpreted')
        scopes.append(dict(selected=list(mask),results=row))
    edge_cases={}
    for name,parts,standard in (
        ('false_part',('c4',),('c3',)),('false_standard',('c1',),('c4',)),
        ('true_part',('c5',),('c3',)),('opposite_claims',('c1',),('c6',)),
        ('inconsistent_document',('c1','c6'),('c3',)),('empty_both',(),()),
    ):
        row=run(logic_indices,parts=parts,standard=standard)
        if row!=logic_expected(parts,standard,(True,)*4):raise ValueError('Intrinsic inconsistency became relational opposition')
        edge_cases[name]=row
    if run(logic_indices,variant='scope_anchor')!=[False]*6:raise ValueError('Scope anchor replaced')
    beliefs=[]
    for selected,judged,actual in product(product((False,True),repeat=2),product((False,True),repeat=4),product((False,True),repeat=2)):
        scenes=[i for i,chosen in enumerate(selected) if chosen]
        some=bool(scenes) and all(any(judged[2*part+i] for part in range(2)) for i in scenes)
        same=bool(scenes) and any(all(judged[2*part+i] for i in scenes) for part in range(2))
        none=bool(scenes) and all(not any(judged[2*part+i] for part in range(2)) for i in scenes)
        expected=[any(actual),not any(actual),some,same,none,not any(actual)]
        row=run(range(5,11),candidates=selected,judged=judged,actual=actual)
        if row!=expected:raise ValueError('Non-factive belief or witness scope lost')
        beliefs.append(dict(selected=list(selected),judged=list(judged),actual=list(actual),results=row))
    contrasts={}
    specs={
        **{name:[False,True,False,False,True,False] for name in ('contains_document','contains_anchor','membership_only_at_candidates')},
        **{name:[False,True,False,False,True,True] for name in ('clashes_standard','clashes_claim')},
        'clashes_point':[False,True,True,True,False,True],
        **{'candidates_'+name:[True,False,False,False,False,False] for name in ('person','document','standard','anchor')},
    }
    for variant,expected in specs.items():
        row=run(range(5,11),variant=variant,judged=(True,)*4,actual=(True,True))
        if row!=expected:raise ValueError('Conflict referent replaced: '+repr((variant,row)))
        contrasts[variant]=row
    for doc in docs:
        # Non-factive judgments with an explicit conflict relation do not inspect truth.
        if evaluate(doc,model_for(doc,variant='unknown_contents'),range(5,10))!=[False,True,False,False,True]:
            raise ValueError('Conflict relation evaluated unrelated truth')
        for name,indices in (('contains',[5]),('contents',[1]),('scope',[1]),('clashes',[5]),('candidates',[7])):
            symbol=EXTRA[name][0] if name in EXTRA else previous.SYMBOLS[name]
            model=model_for(doc);model[symbol]=guarded(doc)[symbol]
            try:evaluate(doc,model,indices)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown conflict input replaced: '+name)
        # Known absence and the belief that a conflict exists can coexist.
        if evaluate(doc,model_for(doc,judged=(True,)*4),range(5,11))!=[False,True,True,True,False,True]:
            raise ValueError('Belief incorrectly constrained actual voice')
    return dict(logical_collections=logical,scope_cases=scopes,edge_cases=edge_cases,belief_cases=beliefs,
        binding_contrasts=contrasts,standalone_agrees=True,unknown_inputs_refused=True,
        relation_based_belief_independent_of_content_truth=True,inner_message_truth_and_norms_not_executed=True,
        whole_consistency_distinct_from_partwise_nonopposition=True,belief_not_factive=True,
        general_logical_or_religious_contradiction_proved=False)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    segments=[]
    for excerpt,definitions in (
        ('nichts der innern Religion widersprechendes darin angetroffen wird',['rgu','rgv','hzbx']),
        ('glaubte er das letztere darin zu finden',['rgw','rgx','rgy']),
    ):
        if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous contained conflict range')
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=definitions,status='partial',review_ja='指定した内的宗教の基準と対立する部分の不在、および対立する部分があるという本人の判断を分けて記述する。部分の所属は基準文脈で固定する。内的宗教・対立関係の実質、発見、仮定節、良心・辞職との接続と全文意味一致は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored contained conflict differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Contained conflict roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_contained_conflict.py','scripts/check_contained_conflict.py','scripts/compose_unsettled_teaching.py',
        'scripts/check_unsettled_teaching.py','scripts/compose_institutional_voice.py','scripts/check_closed_policies.py',
        'scripts/check_conditional_release.py','scripts/check_described_appraisals.py','scripts/check_public_assessment.py',
        'scripts/check_rod_setup.py','noema/finite_semantics.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_contained_conflict_and_nonfactive_belief',documents=documents,sizes=sizes,
        finite=finite_checks(texts[1:]),alignment=alignment(),new_definitions=12,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Contained conflict report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Contained conflict, joint consistency and non-factive belief checked')


if __name__=='__main__':main()
