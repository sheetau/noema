"""Verify policy inclusion, nonvacuity, identity and actual criterion binding."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.manuscript_obligations import audit
from noema.script import transcribe
from scripts.compose_policy_constraints import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,build,basis,review
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts.check_public_reason_claim import permission_model,DOMAIN as PUBLIC_DOMAIN

REPORT=ROOT/'reports/policy-constraints-v1.json'
AUDIT=ROOT/'reports/kant-manuscript-obligations-v4.json'
SCENES=('on','off','current')
DOMAIN=PUBLIC_DOMAIN+('community','goal')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jzpolicyvalue[d] c.r jzconstraintvalue[d] c.r jzcases[d] c.
d jzpolicy[bindings j[a]] e[b point[k jzpolicyvalue[v point]]].
d jzconstraint[bindings j[a]] e[b point[k jzconstraintvalue[v point]]].
q[k ryp[r[p jzpolicy] p jzconstraint p jzcases]].
q[k ryq[r[p jzpolicy] p jzconstraint p jzcases]].
''')


def values(policy=1,constraint=3,*,empty=False,memoize=True):
    p=dict(jzpolicyvalue=lambda point:bool(policy&(1<<SCENES.index(point))),
        jzconstraintvalue=lambda point:bool(constraint&(1<<SCENES.index(point))),jzcases=lambda point:not empty)
    return evaluate(fixture(),p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=2)
def source_fixture(policy_name='jzpolicy'):
    doc=deepcopy(document(CORE));doc['statements']=[]
    text=format_graph(doc,'compact')+'''
r jzsource[] a.r jzactor[] a.r jzoffice[] a.r jzcommunity[] a.r jzanchor[] d.r jznow[] d.
r jzpolicyvalue[d] c.
d jzpolicy[bindings j[a]] e[b point[k jzpolicyvalue[v point]]].
d jzalias[bindings j[a]] e[k jzpolicy[v bindings]].
'''
    bound='k jzsource[] k jzactor[] k jzoffice[] r[p '+policy_name+'] k jzcommunity[] k jzanchor[]'
    text+='q[k iaymeaning['+bound+']].q[t[k '+policy_name+'[l[a][]]][k jznow[]]].'
    text+='q[t[c[k iaycontent['+bound+']][l[a][]]][k jznow[]]].'
    text+='q[k ryq[r[p '+policy_name+'] k iaycontent['+bound+'] i[point d][e[n p a b][n p a b]]]].'
    return parse(text)


def source_model(policy=1,permission=5,*,variant='baseline',calls=None):
    p=dict(arithmetic(),**permission_model(calls=calls))
    allowed=p['h7b']
    def signature(actor,code,community,anchor):
        if calls is not None:calls.append(('targets',actor,code,community,anchor))
        return (actor,community,anchor)==('government','community','current') and code_is(code,'jzpolicy')
    person='other' if variant=='other_beneficiary' else 'person'
    def required(source,actor,office,target,bindings,polarity,point):
        if calls is not None:calls.append(('criterion',source,actor,office,target,bindings.items,polarity,point))
        return variant!='missing_requirement' and (source,actor,office)==('norm','government','office') and code_is(target,'iavclaim') and bindings.items==('government','person') and polarity
    def normcases(source,actor,office,code,community,anchor,point):
        return variant!='empty_cases' and (source,office)==('norm','office') and signature(actor,code,community,anchor) and point in ('on','off')
    def permission_relation(*args):
        point=args[-1]
        if variant=='unknown_permission' and point=='on':raise ValueError('Unknown permission')
        return bool(permission&(1<<SCENES.index(point))) and allowed(*args)
    p.update(jzsource=lambda:'other' if variant=='other_source' else 'norm',jzactor=lambda:'government',
        jzoffice=lambda:'other' if variant=='other_office' else 'office',jzcommunity=lambda:'community',
        jzanchor=lambda:'current',jznow=lambda:'current',jzpolicyvalue=lambda point:bool(policy&(1<<SCENES.index(point))),
        iaxpeople=lambda actor,code,community,anchor:SequenceValue(() if variant=='empty_people' else (person,),'"individual"'),
        iaxscope=lambda actor,code,community,anchor,target:signature(actor,code,community,anchor) and target==person,
        iaynormcases=normcases,h7k=required,h7b=permission_relation)
    return p


def source_values(policy=1,permission=5,*,variant='baseline',policy_name='jzpolicy',calls=None):
    doc=source_fixture(policy_name);p=source_model(policy,permission,variant=variant,calls=calls)
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES)


def realization_values(policy=1,permission=5,*,variant='baseline'):
    doc=deepcopy(source_fixture());meaning=doc['statements'][:1];doc['statements']=[]
    text=format_graph(doc,'compact')+'''
r jzgoalscope[a] c.r jzgoalholds[a a d] c.r jzgoalclassified[a a d] c.
r jzoutcomes[a i[h[j[a]] e] c d d] c.
q[k rx6[k jzactor[] k jzactor[] r[p jzpolicy] k jznow[] l[a][k jzgoal[]] p jzgoalscope p jzgoalholds p jzgoalclassified p jzoutcomes]].
'''
    # Insert the goal constant before its use, keeping the original document typed.
    text=text.replace('r jzgoalscope','r jzgoal[] a.r jzgoalscope',1)
    doc=parse(text);doc['statements']=meaning+doc['statements'];p=source_model(policy,permission,variant=variant)
    p.update(jzgoal=lambda:'goal',jzgoalscope=lambda goal:goal=='goal',
        jzgoalholds=lambda actor,goal,point:(actor,goal,point)==('government','goal','on'),
        jzgoalclassified=lambda actor,goal,point:(actor,goal)==('government','goal'),
        jzoutcomes=lambda actor,code,sign,context,point:actor=='government' and code_is(code,'jzpolicy') and context=='current' and point==('on' if sign else 'off'))
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES)


def wrapper_values(*,variant='baseline',remaining=True):
    doc=deepcopy(source_fixture());doc['statements']=[]
    parent=next(d for d in doc['declarations'] if d['name']=='iaxschema')
    parent.update(kind='primitive',parameters=[p['sort'] for p in parent['parameters']]);parent.pop('body')
    text=format_graph(doc,'compact')+'''r jzprobes[d] c.r jzremaining[i b[h[a] e] a j[a] d d d d] c.
q[k iayschema[r b[p iahinner] k jzsource[] k jzactor[] k jzoffice[] r[p jzalias] r[p jzpolicy] p jzprobes p jzremaining]].'''
    doc=parse(text);p=source_model(variant=variant);seen=[]
    def parent_call(reading,source,actor,office,first,second,probes,rest):
        seen.append((source,actor,office,first,second))
        return rest(reading,'community',SequenceValue(('other',),'"individual"'),'current','off','on','current')
    p.update(iaxschema=parent_call,jzprobes=lambda point:True,
        jzremaining=lambda reading,community,contributors,anchor,start,end,late:remaining and code_is(reading,'iahinner',1) and
            (community,contributors.items,anchor,start,end,late)==('community',('other',),'current','off','on','current'))
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    result=evaluate(doc,p,DOMAIN,SCENES)
    assert seen and code_is(seen[0][3],'jzalias') and code_is(seen[0][4],'jzpolicy')
    return result


def attribution(variant='baseline'):
    doc=document(CORE);p={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'other' if variant=='author' else 'author',iagscope=lambda:'scope',wh=lambda:'now',
        iatreport=lambda node,author,code,scope,point:(node,author,scope,point)==('node','author','scope','now') and code_is(code,'iaxschema' if variant=='old' else 'iayschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('now',),primitives=p)]


def review_report():
    packet=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    units=json.loads((ROOT/packet['source_units']).read_text(encoding='utf-8'))['units'];unit=next(u for u in units if u['id']==packet['unit'])
    assert hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()==packet['document_sha256']
    return audit(document(SOURCE),unit,packet)


def build_report():
    files=build();documents={}
    for path,text in files.items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review(files)
    for policy,constraint in product(range(8),repeat=2):assert values(policy,constraint)==[not bool(policy&~constraint),bool(policy)]
    assert source_values()==[True,False,True,True]
    assert realization_values()==[True,True] and realization_values(policy=0)==[True,False]
    assert wrapper_values()==attribution()==[True]
    inspected=review_report();row=next(r for r in inspected['obligations'] if r['id']=='dignified_treatment')
    assert not row['unconnected_candidate_roots']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,'scripts/compose_policy_constraints.py','scripts/check_policy_constraints.py',
        'tests/test_policy_constraints.py','docs/policy-constraints-v1.md','noema/manuscript_obligations.py',
        'scripts/check_public_reason_claim.py','scripts/check_caused_choice.py','noema/constructed.py',
        'noema/constructed_discourse.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py',
        'noema/diagnostic_short_circuit.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='policy_includes_public_permission_for_same_beneficiaries',documents=documents,
        source_alignment=dict(unit=inspected['unit'],text_sha256=inspected['source_sha256'],status='explicit_interpretive_annotation',
            definitions=['ryp','ryq','iaycontent','iaymeaning','iayschema','iavclaim','iavtreatment'],adds_new_text_coverage=False,semantic_completion=False),
        verification_scope='Concrete criterion and existing rx6 evaluated; parent schema interface checked with a recording stand-in, not a full causal-model rerun.',
        roundtrips=True,limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report();inspected=review_report();inspected.update(document=SOURCE,input_sha256=report['source_sha256'])
    for path,value in ((REPORT,report),(AUDIT,inspected)):
        if args.verify_only:assert json.loads(path.read_text(encoding='utf-8'))==value
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Concrete treatment criterion now included by the same policy; dignity remains incomplete')


if __name__=='__main__':main()
