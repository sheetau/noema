"""Check roles, assignment, mission identity and the source qualification."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.script import transcribe
from scripts.compose_assigned_formation import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,build,basis
from scripts.compose_qualified_utterance import closure
from scripts.check_protective_qualification import alignment as parent_alignment

REPORT=ROOT/'reports/assigned-formation-v1.json'
DOMAIN=('actor','m1','m2','outsider','r1','r2','leader','institution','group','community','other')
SCENES=('anchor','later')
CONTRASTS=('wrong_assignment_institution','wrong_assignment_group','wrong_assignment_community','wrong_assignment_anchor',
    'missing_office','mixed_institution','foreign_role','other_holder','alias_assigned','alias_responsibilities',
    'second_mission','new_unassigned_member','empty_members')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def interpretation(flags=(True,)*6,actual=False,variant='baseline'):
    constituted,assigned,first,second,commander,directs=flags
    def members(group,person,point):
        if variant=='unknown_members':raise ValueError('Unknown members')
        people=() if variant=='empty_members' else ('m1','m2','outsider') if variant=='new_unassigned_member' else ('m1','m2')
        return (group,point)==('group','anchor') and person in people
    def mission(i,g,c,code,t):
        if variant=='unknown_assignment':raise ValueError('Unknown assignment')
        expected=('other' if variant=='wrong_assignment_institution' else 'institution',
            'other' if variant=='wrong_assignment_group' else 'group',
            'other' if variant=='wrong_assignment_community' else 'community',
            'later' if variant=='wrong_assignment_anchor' else 'anchor')
        return assigned and (i,g,c,t)==expected and json.loads(code.syntax)==dict(kind='function_ref',symbol='jpalias' if variant=='alias_assigned' else 'jpmission')
    def offices(role,i,g,t):
        if variant=='missing_office' and role=='r1':return False
        return role in ('r1','r2','leader') and (i,g,t)==('institution','other' if variant=='foreign_role' and role=='r2' else 'group','anchor')
    def holders(p,r,i,g,t):
        return (p,r) in ({('outsider' if variant=='other_holder' else 'm1','r1')} if first else set()) | \
            ({('m2','r2')} if second else set()) | ({('actor','leader')} if commander else set()) and \
            (i,g,t)==('other' if variant=='mixed_institution' and p=='m2' else 'institution',
                'other' if variant=='leader_other_group' and p=='actor' else 'group','anchor')
    def responsibilities(r,i,g,c,code,t):
        if variant=='unknown_responsibilities':raise ValueError('Unknown responsibilities')
        name='jpalias' if variant=='alias_responsibilities' or variant=='second_mission' and r=='r2' else 'jpmission'
        return r in ('r1','r2','leader') and (i,g,c,t)==('institution','group','community','anchor') and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)
    def achieved(g,c,t):
        if variant=='unknown_mission':raise ValueError('Unknown mission outcome')
        return actual and (g,c,t)==('group','community','anchor')
    return dict(jpactor=lambda:'actor',jpinstitution=lambda:'institution',jpgroup=lambda:'group',jpbeneficiary=lambda:'community',
        jpanchor=lambda:'anchor',jpachieved=achieved,jpmembers=members,
        jpconstituted=lambda i,g,t:constituted and (i,g,t)==('institution','group','anchor'),jpassigned=mission,
        jpoffices=offices,jpholders=holders,jpresponsibilities=responsibilities,
        jpdirects=lambda r,i,g,t:directs and (r,i,g,t)==('leader','institution','group','anchor'))


def values(flags=(True,)*6,actual=False,variant='baseline',indices=(0,1,2,3),memoize=True):
    doc=deepcopy(document(EXAMPLE));alias=deepcopy(doc['statements'][2])
    alias['body']['content']['symbol']='jpalias';doc['statements'].append(alias)
    doc['statements']=[doc['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=interpretation(flags,actual,variant),
        memoize_definitions=memoize,memoize_expressions=memoize,max_steps=2_000_000)]


@lru_cache(maxsize=1)
def source_setup():
    doc=deepcopy(document(EXAMPLE));doc['statements']=[];names={d['name'] for d in doc['declarations']}
    for decl in closure(document(SOURCE),['hzyqualified']):
        if decl['name'] not in names:doc['declarations'].append(decl);names.add(decl['name'])
    text=format_graph(doc,'compact')+'r jpremaining[a a a d] c.'
    args='r[p jpmission] k jpactor[] k jpgroup[] k jpbeneficiary[] k jpanchor[]'
    expr='k hzyqualified[r[p jpmission] p jpremaining k jpactor[] k jpgroup[] k jpbeneficiary[] k jpanchor[]]'
    return parse(text+'q[k hzyformation['+args+']].q['+expr+'].q[t[k jpmission[k jpgroup[] k jpbeneficiary[]]][k jpanchor[]]].q[e[r['+expr+']][r['+expr+']]].')


def source_values(flags=(True,)*6,actual=False,remaining=True,variant='baseline',indices=(0,1,2,3)):
    doc=deepcopy(source_setup());doc['statements']=[doc['statements'][i] for i in indices]
    model=interpretation(flags,actual,variant)
    for name in ('constituted','assigned','offices','holders','responsibilities','directs'):model['hzy'+name]=model['jp'+name]
    def selected(actor,group,anchor):
        assert (actor,group,anchor)==('actor','group','anchor')
        return 'other' if variant=='other_institution_selection' else 'institution'
    def members(actor,group,anchor):
        assert (actor,group,anchor)==('actor','group','anchor')
        def relation(g,p,t):
            return model['jpmembers']('other' if variant=='other_members_selection' else g,p,t)
        return FunctionValue(('individual','individual','situation'),'truth',relation)
    def residue(actor,group,community,point):
        if variant=='unknown_remaining':raise ValueError('Unknown remaining condition')
        expected=('outsider' if variant=='other_remaining_actor' else 'actor',
            'other' if variant=='other_remaining_group' else 'group',
            'other' if variant=='other_remaining_community' else 'community',
            'later' if variant=='other_remaining_anchor' else 'anchor')
        return remaining and (actor,group,community,point)==expected
    model.update(hzyinstitution=selected,hzxmembersof=members,jpremaining=residue)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        memoize_definitions=True,memoize_expressions=True,max_steps=2_000_000)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Mission, formation or protection was evaluated during attribution')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzyonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hzyannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def binding_structure():
    lookup={d['name']:d for d in document(SOURCE)['declarations']}
    d=lookup['hzyonly'];mission,remaining,anchor=(p['name'] for p in d['parameters']);body=d['body']
    assert body['kind']=='call' and body['symbol']=='hzxonly'
    fn=body['arguments'][0];bound=[p['name'] for p in fn['parameters']]
    assert fn['body']==dict(kind='call',symbol='hzyqualified',arguments=[dict(kind='variable',name=n) for n in [mission,remaining,*bound]])
    assert body['arguments'][1]==dict(kind='variable',name=anchor)
    return True


def alignment():
    result=parent_alignment();result.update(definitions=['hzyformation','hzyqualified','hzyonly','hzyattribution'],
        military_mission_open=True,residual_qualification_open=True)
    return result


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
    for bits in product((False,True),repeat=7):
        flags,actual=bits[:6],bits[6];result=values(flags,actual)
        assert result==[all(flags[:4]),all(flags),actual,True],(bits,result)
        matrix.append(dict(bits=bits,result=result))
    contrasts={v:values(variant=v) for v in CONTRASTS}
    assert all(r==[False,False,False,True] for r in contrasts.values()),contrasts
    assert values(variant='leader_other_group')==[True,False,False,True]
    assert values(actual=True,variant='alias_assigned',indices=(0,2,4))==[False,True,True]
    assert values(variant='unknown_mission',indices=(0,1,3))==[True]*3
    for variant in ('unknown_members','unknown_assignment','unknown_responsibilities'):
        assert values(variant=variant,indices=(3,))==[True]
        try:values(variant=variant,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown institutional relation treated as absent')
    assert values(memoize=False)==[True,True,False,True]
    source=[]
    for formed,leader,remaining,actual in product((False,True),repeat=4):
        result=source_values((formed,True,True,True,leader,True),actual,remaining)
        assert result==[formed and leader,formed and leader and remaining,actual,True]
        source.append(dict(bits=[formed,leader,remaining,actual],result=result))
    for variant in ('other_institution_selection','other_members_selection'):
        assert source_values(variant=variant)==[False,False,False,True]
    for variant in ('other_remaining_actor','other_remaining_group','other_remaining_community','other_remaining_anchor'):
        assert source_values(variant=variant)==[True,False,False,True]
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,'scripts/compose_assigned_formation.py','scripts/check_assigned_formation.py',
        'tests/test_assigned_formation.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='assigned_formation_with_open_military_mission',documents=documents,matrix=matrix,contrasts=contrasts,
        source_matrix=source,binding_structure=binding_structure(),roundtrips=True,integrated_protection_evaluated=False,
        source_alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Assigned roles, command position, mission identity and source qualification verified')


if __name__=='__main__':main()
