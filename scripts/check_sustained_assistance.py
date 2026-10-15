"""Check temporal scope, purpose bindings and sustained assistance separately."""
import argparse
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_sustained_assistance import ROOT,PARENT,TEMPORAL,SOURCE,LIBRARY,CORE,READING,PERIOD,TEMP,OCCASIONS,build,reused_temporal
from scripts.compose_limits import call as k
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks,guarded

REPORT=ROOT/'reports/sustained-assistance-v1.json'
SCENES=('early','middle','late','now','future')
PEOPLE=('helper','recipient','work','act0','act2','other')
ALIASES=dict(helper='zrqperson',recipient='rd',work='zrqwork',context='ri',occurs='zrqoccurs',performs='zrqperforms')
ALIASES.update({n:'zrr'+n for n,_ in PERIOD if n not in ALIASES and n!='goal'})


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,people=PEOPLE):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=12_000_000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def fixture(path=CORE,generic=False):
    names={n:'js'+n for n,_ in PERIOD if n!='goal'} if generic else ALIASES
    goal='jgoal' if generic else 'sewv'
    refs={n:k(symbol) for n,symbol in names.items()};refs['goal']='r['+k(goal)+']'
    if generic:
        extra=''.join('r js'+n+'[] '+t+'.' for n,t in PERIOD if n!='goal')
        extra+='d jgoal[] h[j[a]] e[i[bindings j[a]][b point[e[n p a b][n p b b]]]].'
    else:extra='d jalias[] h[j[a]] e[k sewv[]].'
    queries=[k(root,*[refs[n] for n,_ in PERIOD]) for root in ('sews','sewt','sewu')]
    queries += [k('sewq',*[refs[n] for n,_ in TEMP]),k('sewr',*[refs[n] for n,_ in OCCASIONS])]
    if not generic:queries+=['t[k seww[]][k ri[]]','t[k sewx[]][k ri[]]']
    return candidate(text(path),extra+''.join('q['+q+'].' for q in queries))


def model_for(doc,variant='baseline',generic=False,work='work'):
    names={n:'js'+n for n,_ in PERIOD if n!='goal'} if generic else ALIASES
    goal='jgoal' if generic else 'sewv';model=guarded(doc)
    for n,value in dict(helper='helper',recipient='recipient',work=work,context='now').items():model[names[n]]=lambda value=value:value
    times={point:i for i,point in enumerate(SCENES)}
    def history(point):return point!='future' or variant=='future_period'
    def scope(point):
        if variant=='unknown_scope':raise ValueError('Work scope missing')
        if variant=='empty_scope':return False
        if variant=='future_period':return point=='future'
        if variant=='present_period':return point=='now'
        return point in ('early','late') if variant=='scope_hole' else point in ('early','middle','late')
    def before(left,right):return times[left]<times[right] or variant=='bad_order' and left==right=='early'
    def occasions(point):
        if variant=='empty_occasions':return False
        if variant in ('future_period','present_period'):return point==('future' if variant=='future_period' else 'now')
        return point in ('early','late') or point=='middle' and variant=='extra_occasion' or point=='now' and variant=='outside_occasion'
    def working(person,project,point):
        return (person,project)==('recipient',work) and not (variant=='wrong_work' or variant=='work_gap' and point=='middle')
    def goalfor(person,project,description,point):
        return (person,project)==('recipient',work) and json.loads(description.syntax)['symbol']==goal and variant!='no_beneficiary_goal'
    episodes={('act0','early'),('act2','late')}
    def occurs(act,point):return (act,point) in episodes and variant!='no_action'
    def performs(person,act,point):
        expected='other' if variant=='other_helper' and point=='late' else 'helper'
        return person==expected and (act,point) in episodes
    def aims(person,act,description,bindings,point):
        if variant=='unknown_intention':raise ValueError('Intention missing')
        correct=('recipient',work)
        if variant=='reversed_bindings':correct=(work,'recipient')
        if variant=='other_recipient':correct=('other',work)
        if variant=='other_project':correct=('recipient','other')
        expected='jalias' if variant=='different_goal' else goal
        return person=='helper' and (act,point) in episodes and bindings.items==correct and json.loads(description.syntax)['symbol']==expected and variant not in ('no_intention','different_act') and not (variant=='missed_second' and point=='late')
    callbacks(doc,model,{names[n]:fn for n,fn in dict(history=history,scope=scope,before=before,occasions=occasions,
        working=working,goalfor=goalfor,occurs=occurs,performs=performs,aims=aims).items()})
    # zrradvances intentionally remains guarded: a purpose's truth must not run.
    return model


@lru_cache(None)
def source_checks():
    cases={
        'baseline':[True,True,False,True,True],
        'missed_second':[True,False,True,True,True],
        'other_helper':[True,False,True,True,True],
        'extra_occasion':[True,False,True,True,True],
        'empty_scope':[False,False,False,False,False],
        'empty_occasions':[False,False,False,True,False],
        'outside_occasion':[False,False,False,True,False],
        'scope_hole':[False,False,False,False,True],
        'bad_order':[False,False,False,False,True],
        'work_gap':[False,False,False,False,True],
        'wrong_work':[False,False,False,False,True],
        'present_period':[False,False,False,False,True],
        'future_period':[False,False,False,False,True],
    }
    for name in ('no_action','no_intention','different_act','other_recipient','other_project','reversed_bindings','different_goal','no_beneficiary_goal'):
        cases[name]=[False,False,True,True,True]
    doc=fixture();rows={}
    for name,wanted in cases.items():
        actual=evaluate(doc,model_for(doc,name));assert actual==wanted+wanted[:2],(name,actual)
        rows[name]=actual
    full=fixture(SOURCE)
    for name in ('baseline','missed_second','work_gap'):
        assert evaluate(full,model_for(full,name))==rows[name]
    for name in ('unknown_scope','unknown_intention'):
        try:evaluate(doc,model_for(doc,name))
        except ValueError as exc:assert 'missing' in str(exc)
        else:raise AssertionError('Unknown input guessed')
    return dict(cases=rows,full_source_cases=['baseline','missed_second','work_gap'],unknown_inputs_refused=['scope','intention'],
        goal_truth_evaluated=False,physical_colocation_required=False,historical_fidelity_verified=False)


def generic_checks():
    doc=fixture(LIBRARY,True);rows={}
    for work in ('work','garden'):
        domain=tuple(work if x=='work' else x for x in PEOPLE)
        for variant in ('baseline','missed_second','extra_occasion','other_recipient'):
            expected=source_checks()['cases'][variant][:5]
            actual=evaluate(doc,model_for(doc,variant,True,work),domain);assert actual==expected,(work,variant,actual)
            rows[work+':'+variant]=actual
    return dict(cases=rows,false_goal_does_not_preclude_assistance=True)


def goal_checks():
    base=fixture();base['statements']=[]
    seq='l[a][k rd[] k zrqwork[]]'
    doc=candidate(format_graph(base,'compact'),'q[t[k sewx[]][k ri[]]].q[t[c[k sewv[]]['+seq+']][k ri[]]].'+
        'q[e[r[k sewv[]]][r[k jalias[]]]].q[e[c[k sewv[]]['+seq+']][c[k jalias[]]['+seq+']]].')
    rows={}
    for success in (False,True):
        model=model_for(doc)
        callbacks(doc,model,{'zrradvances':lambda person,work,point,success=success:success and (person,work)==('recipient','work')})
        result=evaluate(doc,model);assert result==[True,success,False,True],result;rows[str(success)]=result
    return dict(cases=rows,purpose_independent_of_achievement=True,description_identity_preserved=True)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for n,value in dict(zrrnode='claim',rd='author',zrqscope='scope',ri='now').items():model[n]=lambda value=value:value
    def claim(node,author,content,scope,context):
        target=json.loads(content.syntax)['symbol'];seen.append(target)
        return (node,author,target,scope,context)==('claim','author','sewx','scope','now')
    model['uh']=claim
    assert evaluate(doc,model,('claim','author','scope'))==[True]
    return dict(quoted_targets=seen,support_claim_evaluated=False)


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(x for x in work['units'] if x['id']=='einstein-1905:u0276')
    segments=[]
    for excerpt in ('mir beim Arbeiten an dem hier behandelten Probleme','treu zur Seite stand'):
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            status='partial_purpose_directed_assistance_across_past_occasions',definitions=['sewo','sewq','sewr','sewt','sewx']))
    return dict(segments=segments)


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));doc=parse(text(SOURCE));assert len(old['statements'])==205 and doc['statements'][:-1]==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    lookup={d['name']:d for d in doc['declarations']}
    for definition in reused_temporal():assert lookup[definition['name']]==definition
    for p in (SOURCE,LIBRARY,CORE):
        document=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(document,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(document,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==document
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==document
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,TEMPORAL,READING,reading['facsimile_path'],'data/einstein-intellectual-credit-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_sustained_assistance.py','docs/sustained-assistance-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_sustained_assistance','check_sustained_assistance','compose_parameterized_goals',
        'compose_origin_clock','compose_limits','compose_situated_criticism','check_described_appraisals','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','linking'))
    return dict(status='partial_purpose_directed_assistance_across_past_occasions',document=SOURCE,basis_audits=audits,
        source=source_checks(),generic=generic_checks(),goals=goal_checks(),attribution=attribution_check(),reused_time_definitions_identical=True,
        statements_preserved=205,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Past scope, purpose-directed acts and sustained assistance checked',flush=True)


if __name__=='__main__':main()
