"""Check recognized risk, undertaking and permission without conflating actuality."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from unittest.mock import patch

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_risk_undertaking import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,build,basis
from scripts.compose_qualified_utterance import closure
from scripts import check_restricted_utterance as speech
from scripts import check_integrated_qualification as integrated

REPORT=ROOT/'reports/risk-undertaking-v1.json'
UNITS='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','trial','secondtrial','standard','role')
SCENES=('anchor','view','harm','safe')
CONTRASTS=('other_prospect_person','other_prospect_activity','alias_prospect','other_prospect_view','other_outcome',
           'alias_recognition','extra_safe_view','other_begin_person','alias_pursuit')
NORM_CONTRASTS=('norm_standard','norm_actor','norm_role','norm_activity','norm_description','norm_context')


@lru_cache(maxsize=5)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def model(flags=(True,)*7+(False,),*,prefix='jra',person='person',activity='trial',view='view',outcome='harm',
          goal='jragoal',normgoal=None,actual_possible=False,achieved=False,variant='baseline'):
    possible,adverse,recognized,views,begins,pursues,allowed,forbidden=flags
    normgoal=normgoal or goal
    def code(value,name):return value.rank==2 and json.loads(value.syntax)==dict(kind='function_ref',symbol=name)
    def prospect(p,a,d,c,e):
        if variant=='unknown_prospects':raise ValueError('Unknown prospects')
        return (p,a,c,e)==('other' if variant=='other_prospect_person' else person,
            'secondtrial' if variant=='other_prospect_activity' else activity,
            'anchor' if variant=='other_prospect_view' else c,
            'safe' if variant=='other_outcome' else outcome) and code(d,'jraalias' if variant=='alias_prospect' else goal) and (
                possible and c==view or actual_possible and c=='anchor')
    def recognition(p,a,d,c):
        return recognized and (p,a,c)==(person,activity,'anchor') and code(d,'jraalias' if variant=='alias_recognition' else goal)
    def considered(p,a,d,c,s):
        return views and (p,a,c)==(person,activity,'anchor') and code(d,goal) and (s==view or variant=='extra_safe_view' and s=='safe')
    def start(p,a,c):return begins and (p,a,c)==('other' if variant=='other_begin_person' else person,activity,'anchor')
    def aim(p,a,d,c):return pursues and (p,a,c)==(person,activity,'anchor') and code(d,'jraalias' if variant=='alias_pursuit' else goal)
    def normative(standard,p,role,a,d,sign,c,wanted):
        if variant=='unknown_norm':raise ValueError('Unknown normative input')
        return wanted and sign and (standard,p,role,a,c)==(
            'other' if variant=='norm_standard' else 'standard','other' if variant=='norm_actor' else person,
            'other' if variant=='norm_role' else 'role','secondtrial' if variant=='norm_activity' else activity,
            view if variant=='norm_context' else 'anchor') and code(d,'jraalias' if variant=='norm_description' else normgoal)
    result={prefix+n:fn for n,fn in dict(prospects=prospect,adverse=lambda p,s:adverse and (p,s)==(person,outcome),
        recognizes=recognition,views=considered,begins=start,pursues=aim,
        allowed=lambda s,p,r,a,d,sign,c:normative(s,p,r,a,d,sign,c,allowed),
        required=lambda s,p,r,a,d,sign,c:normative(s,p,r,a,d,not sign,c,forbidden)).items()}
    if prefix=='jra':
        def achievement(p,a,c):
            if variant=='unknown_goal':raise ValueError('Unknown goal achievement')
            return achieved and (p,a,c)==(person,activity,'anchor')
        result.update(jraperson=lambda:person,jraactivity=lambda:activity,jraanchor=lambda:'anchor',
            jrastandard=lambda:'standard',jrarole=lambda:'role',jraachieved=achievement,
            jracandidates=lambda p,a,c:variant!='empty_candidates' and (p,a,c)==(person,activity,'anchor'))
    return result


def values(flags=(True,)*7+(False,),*,indices=None,memoize=True,**options):
    doc=deepcopy(document(EXAMPLE))
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=model(flags,**options),memoize_definitions=memoize,memoize_expressions=memoize)]


def expected(flags,actual_possible=False,achieved=False):
    possible,harm,recognized,views,begins,pursues,allowed,forbidden=flags
    perceived=possible and harm and recognized and views
    return [actual_possible and harm,perceived,perceived and begins and pursues,allowed and not forbidden,
            not (allowed and not forbidden),achieved,True]


def source_fixture(*,allowed=False,forbidden=False,success=True,begins=True,variant='baseline',combined=False,qualified=True):
    if combined:doc,kwargs=integrated.fixture(remaining=qualified)
    else:
        captured={}
        def receive(doc,**kwargs):captured.update(document=deepcopy(doc),kwargs=kwargs);return []
        old_variant=variant if variant in ('extra_hearer','missing_hearer','unknown_speaker') else 'baseline'
        with patch.object(speech,'evaluate_document',side_effect=receive):
            speech.values(speaker=variant!='wrong_speaker',context=variant!='wrong_context',
                success=success,variant=old_variant,indices=(0,))
        doc,kwargs=captured['document'],captured['kwargs']
    doc=deepcopy(doc);doc['statements']=[];names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iaacontrast' if combined else 'iaadenial']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    text=format_graph(doc,'compact')+'r jrasactivity[] a.r jraspopulation[a d] c.r jrasstandardfor[a d] a.r jrasrolefor[a d] a.r jrascandidates[a a d] c.'
    args='p jraspopulation p jrasstandardfor p jrasrolefor p jrascandidates k juanchor[]'
    expression='k iaacontrast[p jiremaining '+args+']' if combined else 'k iaadenial['+args+']'
    actor='k juperson[] k jrasactivity[]'
    questions=[expression,'t[k iaautterance['+actor+']][k jufirst[]]',
        't[k iaaundertake['+actor+']][k juanchor[]]','e[r c['+expression+']][r c['+expression+']]']
    doc=parse(text+''.join('q['+q+'].' for q in questions))
    primitives=kwargs['primitives']
    primitives.update(model((True,True,True,True,begins,True,allowed,forbidden),prefix='iaa',person='speaker',
        view='left',outcome='right',goal='iaautterance',normgoal='iaaundertake',variant=variant))
    primitives.update(iaastart=lambda p,a:'right' if variant=='wrong_anchor' else 'anchor',jrasactivity=lambda:'trial',
        jraspopulation=lambda p,c:variant!='empty_population' and (p,c)==('speaker','anchor'),
        jrasstandardfor=lambda p,c:'standard',jrasrolefor=lambda p,c:'role',
        jrascandidates=lambda p,a,c:variant!='empty_candidates' and (p,a,c)==('speaker','trial','anchor'))
    if variant=='unknown_goal':
        def unknown(*args):raise ValueError('Unknown source utterance')
        primitives['hztoccurs']=unknown
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    assert not required-set(primitives),required-set(primitives)
    kwargs.update(primitives={n:primitives[n] for n in required},individuals=tuple(dict.fromkeys([*kwargs['individuals'],'trial','secondtrial','standard','role'])))
    return doc,kwargs


def source_values(*,indices=(0,1,2,3),combined=False,**options):
    doc,kwargs=source_fixture(combined=combined,**options);doc['statements']=[doc['statements'][i] for i in indices]
    if combined:doc,kwargs['primitives']=lower(doc,kwargs['primitives'])
    return [r['value'] for r in evaluate_document(doc,**kwargs)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Undertaking, permission or qualification evaluated during attribution')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='iaacontrast')
    primitives.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',iaaannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=primitives)]


def alignment():
    corpus=json.loads((ROOT/UNITS).read_text(encoding='utf-8'));unit=next(u for u in corpus['units'] if u['id']=='kant-1784:u0017')
    phrase='nicht wagen darf';start=unit['text'].index(phrase)
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=start,end=start+len(phrase),text=phrase)],definitions=['iaaundertake','iaadenial','iaacontrast','iaaattribution'],
        semantic_completion=False,political_classification_open=True,normative_standard_open=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for flags in product((False,True),repeat=8):
        result=values(flags);assert result==expected(flags),(flags,result)
        matrix.append(dict(flags=list(flags),result=result))
    actuality=[]
    for possible,achieved in product((False,True),repeat=2):
        flags=(True,)*7+(False,);result=values(flags,actual_possible=possible,achieved=achieved)
        assert result==expected(flags,possible,achieved)
        actuality.append(dict(possible=possible,achieved=achieved,result=result))
    contrasts={v:values(variant=v) for v in CONTRASTS+NORM_CONTRASTS}
    assert all(not r[2] for v,r in contrasts.items() if v in CONTRASTS)
    assert all(r[3:5]==[False,True] for v,r in contrasts.items() if v in NORM_CONTRASTS)
    source=[]
    for allowed,forbidden,success,begins in product((False,True),repeat=4):
        result=source_values(allowed=allowed,forbidden=forbidden,success=success,begins=begins)
        assert result==[not (allowed and not forbidden),success,begins,True],result
        source.append(dict(bits=[allowed,forbidden,success,begins],result=result))
    references={v:source_values(variant=v,indices=(0,3)) for v in ('wrong_speaker','wrong_context','wrong_anchor','extra_hearer','missing_hearer')}
    assert all(r==[False,True] for r in references.values())
    combined=[]
    for allowed,qualified in product((False,True),repeat=2):
        result=source_values(allowed=allowed,qualified=qualified,combined=True,indices=(0,3))
        assert result==[qualified and not allowed,True]
        combined.append(dict(allowed=allowed,qualified=qualified,result=result))
    assert source_values(variant='unknown_goal',indices=(0,3))==[True,True]
    for variant,index in [('unknown_norm',0),('unknown_goal',1),('unknown_prospects',2),('unknown_speaker',0)]:
        assert source_values(variant=variant,indices=(3,))==[True]
        try:source_values(variant=variant,indices=(index,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown input was filled')
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements']
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,UNITS,'scripts/compose_risk_undertaking.py','scripts/check_risk_undertaking.py',
           'scripts/check_restricted_utterance.py','scripts/check_anchored_ability.py','scripts/check_integrated_qualification.py',
           'reports/integrated-qualification-v1.json','tests/test_risk_undertaking.py','noema/diagnostic_short_circuit.py',
           'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py']
    return dict(status='candidate_undertaking_denial_with_open_political_scope',documents=documents,matrix=matrix,actuality=actuality,
        contrasts=contrasts,source_matrix=source,reference_contrasts=references,combined_qualification=combined,
        combined_description_domains_finite=True,roundtrips=True,source_alignment=alignment(),unresolved=basis()['unresolved'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Risk-aware undertaking, separate permission and shared utterance target verified')


if __name__=='__main__':main()
