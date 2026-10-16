"""Check unilateral control against an independent finite truth-table oracle."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.constructed_discourse import sequence_sort
from noema.script import transcribe
from scripts.compose_unilateral_decision import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,MEANINGS,FIELDS,CONTROL,build
from scripts.compose_qualified_utterance import closure
from scripts.check_relational_departure import evaluate,model as departure_model,structure as parent_structure
from scripts.check_rod_setup import guarded

REPORT=ROOT/'reports/unilateral-decision-v1.json'
PEOPLE=('holder','target','replacement')
REFS=' '.join('p jdu'+n for n,t in FIELDS)
CODES=' '.join('r[p jdu'+n+']' for n,t in FIELDS)


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def arithmetic():return dict(ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda value:Fraction(int(value)))


@lru_cache(None)
def generic_fixture(path=LIBRARY):
    doc=parse(text(path));doc['statements']=[]
    return parse(format_graph(doc,'compact')+'''r jduvoter[] a.r jdupeople[] j[a].r jdurule[j[c]] c.
q[k rqv[k jduvoter[] k jdupeople[] p jdurule]].q[k rqw[k jduvoter[] k jdupeople[] p jdurule]].''')


def decision(table,count):
    def fn(inputs):
        assert len(inputs.items)==count
        return bool(table&(1<<sum(int(bit)<<i for i,bit in enumerate(inputs.items))))
    return fn


def generic_model(doc,count,table,voter=0,listed=None):
    values=guarded(doc);people=PEOPLE[:count] if listed is None else listed
    values.update(arithmetic());values.update(jduvoter=lambda:PEOPLE[voter],
        jdupeople=lambda:SequenceValue(people,json.dumps('individual')),jdurule=decision(table,len(people)))
    return values


def oracle(count,table,voter):
    outcomes=[bool(table&(1<<bits)) for bits in range(1<<count)]
    influence=any(outcomes[bits]!=outcomes[bits^(1<<voter)] for bits in range(1<<count))
    groups=[{outcomes[bits] for bits in range(1<<count) if bool(bits&(1<<voter))==value} for value in (False,True)]
    unilateral=all(len(group)==1 for group in groups) and groups[0]!=groups[1]
    return [influence,unilateral]


@lru_cache(None)
def source_fixture(path=LIBRARY):
    doc=parse(text(path));doc['statements']=[]
    extra=''.join('r jdu'+n+t[1:]+'.' for n,t in FIELDS)
    extra+='''r jdutarget[] a.r jduholder[] a.r jdupoint[] d.r jdukind[a] c.r jduanchor[] d.
r jduprospects[a d d] c.r jdusecond[a] e.'''
    relation='k rqx[k jduholder[] k jdutarget[] k jdupoint[] '+' '.join('p jdu'+n for n,t in CONTROL)+']'
    content='t[c[k hzhr['+REFS+']][k jdutarget[]]][k jdupoint[]]'
    assembled='k hzht[r b[k jdutarget[]] r b[p jdukind] r b[r[p jdusecond]] r b[k jduanchor[]] r b[p jduprospects] '+CODES+']'
    literal='r b[c[p hzhk][k jdutarget[] p jdukind r[c[p hzhr]['+REFS+']] r[p jdusecond] k jduanchor[] p jduprospects]]'
    return parse(format_graph(doc,'compact')+extra+'q['+relation+'].q['+content+'].q[e['+assembled+']['+literal+']].q[s['+assembled+']].')


def source_model(doc,variant='baseline'):
    old=departure_model(doc,variant if variant in ('different_transition','unassessed_after','cause_absent') else 'baseline')
    values=guarded(doc);values.update(arithmetic())
    for name in ('holders','history','before','assessed','transitions','affected'):
        values['jdu'+name]=old['jdr'+name]
    values.update(jdutarget=lambda:'other' if variant=='wrong_target' else 'target',
        jduholder=lambda:'holder',jdupoint=lambda:'after',jduanchor=lambda:'before',
        jdukind=old['jdrkind'],jduprospects=old['jdrprospects'],jdusecond=old['jdrsecond'],dg=old['dg'])
    def participants(target,scene):
        people=PEOPLE[:2]
        if variant=='missing_target':people=('holder',)
        if variant=='duplicate_input':people=('holder','target','target')
        if variant=='invalid_after' and scene=='after':people=('holder',)
        if variant=='duplicate_after' and scene=='after':people=('holder','target','target')
        if variant=='extra_after' and scene=='after':people=PEOPLE
        if variant=='reverse_order':people=tuple(reversed(people))
        return SequenceValue(people,json.dumps('individual'))
    def contributors(person,target,scene):
        if variant=='unknown_contributors':raise ValueError('unknown contributors')
        members=PEOPLE if variant=='omitted_contributor_after' and scene=='after' else PEOPLE[:2]
        return target=='target' and scene in ('before','after') and person in members
    def rules(target,scene):
        def decide(inputs):
            if variant=='unknown_rule':raise ValueError('unknown rule')
            if target!='target':return False
            holder_index=1 if variant=='reverse_order' else 0
            target_index=0 if variant=='reverse_order' else 1
            # Two distinct postconditions: retained power vs the target gaining control.
            if scene=='before' and variant=='already_free':return inputs.items[target_index]
            if scene=='before' or variant=='continues':return inputs.items[holder_index]
            if variant=='joint_after':return all(inputs.items)
            return inputs.items[target_index]
        return FunctionValue((sequence_sort('truth'),),'truth',decide)
    values.update(jduparticipants=participants,jdurules=rules,jducontributors=contributors)
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='hzhr'),
        arguments=[dict(kind='function_ref',symbol='jdu'+n) for n,t in FIELDS])
    def produces(activity,target,description,scene):
        return variant!='other_description' and (activity,target,scene)==('cause','target','after') and json.loads(description.syntax)==expected
    values['g3']=produces
    return values


@lru_cache(None)
def checks():
    doc=generic_fixture();count=0
    for size,voters in ((2,range(2)),(3,range(1))):
        for table in range(1<<(1<<size)):
            for voter in voters:
                actual=evaluate(doc,generic_model(doc,size,table,voter));wanted=oracle(size,table,voter)
                assert actual==wanted,(size,table,voter,actual,wanted);count+=1
    examples={}
    tables={'holder':170,'inverted_holder':85,'target':204,'majority':232,'unanimity':128,'any':254,'parity':150,'constant':255}
    for path in (LIBRARY,FULL):
        doc=generic_fixture(path);examples[path]={}
        for name,table in tables.items():
            result=evaluate(doc,generic_model(doc,3,table));assert result==oracle(3,table,0)
            examples[path][name]=result
    invalid={}
    doc=generic_fixture()
    for name,listed in dict(empty=(),absent=('target',),duplicate=('holder','holder')).items():
        actual=evaluate(doc,generic_model(doc,len(listed),15,listed=listed));assert actual==[False,False]
        invalid[name]=actual
    # An explicit permutation preserves person identity and remaps the positional rule.
    assert evaluate(doc,generic_model(doc,3,240,listed=tuple(reversed(PEOPLE))))==[True,True]
    for table in (170,232):
        assert evaluate(doc,generic_model(doc,3,table),short=False,memoize=False)==oracle(3,table,0)
    sources={}
    expected={name:[False,False,True,False] for name in ('already_free','missing_target','duplicate_input','wrong_target','different_transition','unassessed_after',
        'invalid_after','duplicate_after','extra_after','omitted_contributor_after')}
    expected.update(baseline=[False,True,True,True],reverse_order=[False,True,True,True],joint_after=[False,True,True,True],continues=[True,False,True,False],
        cause_absent=[False,True,True,False],other_description=[False,True,True,False])
    for path in (LIBRARY,FULL):
        doc=source_fixture(path);sources[path]={}
        for variant,wanted in expected.items():
            actual=evaluate(doc,source_model(doc,variant));assert actual==wanted,(path,variant,actual,wanted)
            sources[path][variant]=actual
        def forbidden(*args):raise AssertionError('Constructing a quotation executed its content')
        values={n:forbidden for n in source_model(doc)}
        assert evaluate(doc,values,indices=(2,))==[True]
    refused=[]
    for variant in ('unknown_rule','unknown_contributors'):
        try:evaluate(doc,source_model(doc,variant),indices=(0,))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(variant)
        else:raise AssertionError(variant)
    return dict(exhaustive_rule_cases=count,rules=examples,invalid_lists=invalid,permutation_checked=True,
        source_contrasts=sources,unknown_inputs_refused=refused,quotation_does_not_execute_content=True,
        unlowered_uncached_rule_cases=2,actual_control_transition_and_causality_executed=True)


def structure():
    inherited=parent_structure();old=parse(text(PARENT));doc=parse(text(FULL));basis=json.loads(text(BASIS))
    assert doc['declarations'][:len(old['declarations'])]==old['declarations'] and doc['statements']==old['statements']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)==set(basis['definitions'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(doc,['rqv','hzht'])
    return dict(inherited_basis_checked=inherited['inherited_basis_checked'],previous_statements_preserved=len(old['statements']),
        previous_declarations_preserved=True,new_definitions=len(added),new_primitives=0,new_assertions=0)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    alignment=deepcopy(json.loads(text('reports/relational-departure-v1.json'))['alignment'])
    for row in alignment['segments']:
        row['definitions']=list(MEANINGS);row['status']='partial_unilateral_binary_decision_relation'
        row['remaining'].append('physical or institutional mechanism and complete meaning of personal despotism')
    paths=set(files)|{PARENT,PARENT_BASIS,'reports/relational-departure-v1.json',
        'docs/unilateral-decision-v1.md','tests/test_unilateral_decision.py','artifacts/written-units-v1/kant-1784.json'}
    paths.update('scripts/'+n+'.py' for n in ('compose_unilateral_decision','check_unilateral_decision','compose_relational_departure',
        'check_relational_departure','check_quoted_outcomes','compose_origin_clock','compose_limits','compose_situated_criticism',
        'compose_qualified_utterance','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','meaning_basis','script','constructed',
        'constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='partial_unilateral_control_not_complete_political_concept',document=FULL,
        finite=checks(),structure=structure(),alignment=alignment,roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Unilateral control, departure, and causal description checked',flush=True)


if __name__=='__main__':main()
