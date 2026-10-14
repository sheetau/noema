"""Check qualitative endorsement separately from truth in contained claims."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_limits import call as k
from scripts.compose_unsettled_teaching import (ROOT,PARENT,BUILDERS,JUDGMENT,POSSIBILITY,COMBINED,TRUTH,SPEECH)

REPORT=ROOT/'reports/unsettled-teaching-v1.json'
FIELDS=COMBINED+[('point','d')]+[field for field in SPEECH if field[0] not in {n for n,_ in COMBINED}|{'message','context'}]
SYMBOLS={name:'jz'+number_word(i) for i,(name,_) in enumerate(FIELDS)}
DOMAIN=('person','doctrine','c1','c2','activity','organization','role','topic','listener','other')
SCENES=('j0','j1','p0','p1','actual','elsewhere')


def expression(name):
    if name=='message':return 'r[p zzy]'
    if name=='context':name='anchor'
    return k(SYMBOLS[name])


def query_document(text):
    names=set(SYMBOLS.values())|{'zzz','zzy','zzx'}
    if names & {d['name'] for d in parse(text)['declarations']}:raise ValueError('Unsettled fixture symbols collide')
    extra=''.join('r '+SYMBOLS[name]+'[] '+sort+'.' for name,sort in FIELDS)
    extra+='r zzz[a d] c.d zzy[subject a] f[j s[b context[k zzz[v subject v context]]]].'
    extra+='d zzx[subject a] f[j s[b context[k zzz[v subject v context]]]].'
    queries=[]
    for symbol,fields in (('rgi',JUDGMENT),('rgj',JUDGMENT),('rgk',JUDGMENT),('rgl',JUDGMENT),
        ('rgn',POSSIBILITY),('rgp',POSSIBILITY),('rgm',TRUTH),('rgo',COMBINED),('hzbw',SPEECH)):
        queries.append(k(symbol,*(expression(name) for name,_ in fields)))
    queries.append('c['+expression('accepts')+']['+' '.join(expression(n) for n in ('person','document','anchor'))+']')
    return extra+''.join('q['+expr+'].' for expr in queries)


def model_for(doc,*,judged=(True,True),endorsement=(True,False),alternatives=(True,True),parts=('c1','c2'),
              truth=(True,False,False,False),actual_truth=(False,False),actual_endorsement=False,variant='baseline'):
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='elsewhere' if label in ('anchor','context') else 'other'
        return list(actual)==expected
    def selection(which,mask,person,document,anchor,point):
        names=('j0','j1') if which=='judged' else ('p0','p1')
        return match((person,document,anchor),('person','doctrine','actual'),which,('person','document','anchor')) and any(
            chosen and point==name for name,chosen in zip(names,mask))
    def accepts(person,document,point):
        return match((person,document),('person','doctrine'),'accepts',('person','document')) and (
            actual_endorsement if point=='actual' else any(flag and point==name for name,flag in zip(('j0','j1'),endorsement)))
    def contains(document,claim,anchor):
        return claim in parts and match((document,anchor),('doctrine','actual'),'contains',('document','anchor'))
    def contents(claim):
        if variant=='unknown_contents':raise ValueError('Claim content interpretation missing')
        if claim=='c1':rows=(False,False,truth[0],truth[1],actual_truth[0],False)
        elif claim=='c2':rows=(False,False,truth[2],truth[3],actual_truth[1],False)
        else:rows=(False,)*len(SCENES)
        return Content(SCENES,rows)
    scalar=dict(person='person',document='doctrine',anchor='actual',point='actual',activity='activity',
        principal='organization',role='role',subject='topic')
    model=guarded(doc)
    for name,value in scalar.items():model[SYMBOLS[name]]=lambda value=value:value
    inner=syntax(quoted('function_ref','zzy'))
    def voice(person,activity,principal,role,subject,message,context):
        return variant!='no_voice' and (person,activity,principal,role,subject,context)==(
            'person','activity','organization','role','topic','actual') and message.syntax==inner
    def about(document,subject,message,context):
        return match((document,subject,context),('doctrine','topic','actual'),'about',('document','subject','context')) and message.syntax==(
            syntax(quoted('function_ref','zzx')) if variant=='about_description' else inner)
    callbacks(doc,model,{
        SYMBOLS['accepts']:accepts,
        SYMBOLS['judged']:lambda person,document,anchor,point:selection('judged',judged,person,document,anchor,point),
        SYMBOLS['alternatives']:lambda person,document,anchor,point:selection('possible',alternatives,person,document,anchor,point),
        SYMBOLS['contains']:contains,SYMBOLS['contents']:contents,
        SYMBOLS['audience']:lambda person:person=='listener',SYMBOLS['voices']:voice,
        SYMBOLS['serves']:lambda person,principal,role,context:(person,principal,role,context)==('person','organization','role','actual'),
        SYMBOLS['about']:about})
    model.update(dg=lambda activity,context:variant!='no_speech' and (activity,context)==('activity','actual'),
        f3=lambda person,activity,context:(person,activity,context)==('person','activity','actual'),
        f2=lambda activity,recipient,subject,message,context:(activity,recipient,subject,context)==('activity','listener','topic','actual') and message.syntax==inner,
        cb=lambda person,activity,role,context:(person,activity,role,context)==('person','activity','role','actual'),
        cf=lambda person,role,context:variant!='no_delegation' and (person,role,context)==('person','role','actual'))
    return model


def evaluate(doc,model):
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in used},DOMAIN,SCENES)


def finite_checks(texts):
    docs=[candidate(text,query_document(text)) for text in texts]
    def run(**options):
        rows=[evaluate(doc,model_for(doc,**options)) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted epistemic scope differs')
        return rows[0]
    judgments=[]
    for mask,accepted,actual in product(product((False,True),repeat=2),product((False,True),repeat=2),(False,True)):
        selected=[a for m,a in zip(mask,accepted) if m]
        settled=bool(selected) and all(selected)
        counter=any(not a for a in selected);rejected=bool(selected) and all(not a for a in selected)
        mixed=any(selected) and counter
        expected=[settled,counter,rejected,mixed,True,False,False,counter,counter,actual]
        row=run(judged=mask,endorsement=accepted,actual_endorsement=actual)
        if row!=expected:raise ValueError('Empty or mixed judgment candidates collapsed: '+repr((mask,accepted,row)))
        judgments.append(dict(selected=list(mask),endorsement=list(accepted),actual_endorsement=actual,results=row))
    possibilities=[]
    for mask,members,truth in product(product((False,True),repeat=2),product((False,True),repeat=2),product((False,True),repeat=4)):
        parts=tuple(name for name,chosen in zip(('c1','c2'),members) if chosen)
        possible=any(mask[world] and members[part] and truth[2*part+world] for world in range(2) for part in range(2))
        impossible=any(mask) and not possible
        expected=[False,True,False,True,possible,impossible,False,possible,possible,False]
        row=run(alternatives=mask,parts=parts,truth=truth)
        if row!=expected:raise ValueError('Possible partial truth became whole/actual truth')
        possibilities.append(dict(selected=list(mask),parts=list(parts),truth=list(truth),results=row))
    actual_cases=[]
    for actual in product((False,True),repeat=2):
        expected=[False,True,False,True,True,False,any(actual),True,True,False]
        row=run(actual_truth=actual)
        if row!=expected:raise ValueError('Actual truth constrained possibility')
        actual_cases.append(dict(truth=list(actual),results=row))
    contrasts={}
    specs={
        **{category+'_'+field:[False,False,False,False,True,False,False,False,False,False]
            for category in ('judged',) for field in ('person','document','anchor')},
        **{'accepts_'+field:[False,True,True,False,True,False,False,True,True,False] for field in ('person','document')},
        **{'possible_'+field:[False,True,False,True,False,False,False,False,False,False] for field in ('person','document','anchor')},
        **{'contains_'+field:[False,True,False,True,False,True,False,False,False,False] for field in ('document','anchor')},
        **{name:[False,True,False,True,True,False,False,True,False,False] for name in (
            'about_document','about_subject','about_context','about_description','no_voice','no_speech','no_delegation')},
    }
    for variant,expected in specs.items():
        row=run(variant=variant)
        if row!=expected:raise ValueError('Modal/teaching referent differs: '+repr((variant,row)))
        contrasts[variant]=row
    for doc in docs:
        # These queries never inspect a candidate claim or its current truth.
        basic={**doc,'statements':doc['statements'][:4]}
        m=model_for(doc,variant='unknown_contents')
        if evaluate(basic,m)!=[False,True,False,True]:raise ValueError('Endorsement evaluated contained truth')
        try:evaluate(doc,m)
        except ValueError as exc:
            if 'Claim content interpretation missing' not in str(exc):raise
        else:raise ValueError('Unknown truth replaced')
        for name in ('accepts','judged','alternatives','contains','contents','about'):
            m=model_for(doc);m[SYMBOLS[name]]=guarded(doc)[SYMBOLS[name]]
            try:evaluate(doc,m)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown modal input replaced: '+name)
    return dict(judgment_cases=judgments,possibility_cases=possibilities,actual_truth_cases=actual_cases,
        binding_contrasts=contrasts,standalone_agrees=True,unknown_relations_and_truth_refused=True,
        endorsement_does_not_evaluate_contained_truth=True,inner_message_truth_and_norms_not_executed=True,
        distinct_judgment_and_possibility_scopes=True,certainty_degree_or_probability_measured=False)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpts=[('die er selbst nicht mit voller Ueberzeugung unterschreiben würde',['rgi','rgj','rgk','rgl']),
        ('nicht ganz unmöglich ist, daß darin Wahrheit verborgen läge',['rgm','rgn','rgo','rgp','hzbw'])]
    segments=[]
    for excerpt,definitions in excerpts:
        if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous unsettled teaching range')
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=definitions,status='partial',review_ja='規定群への賛同の確定と、規定群に含まれる一部の命題の真理の可能性を、別の選択範囲で部分記述する。空範囲を判断に転用しない。程度・仮定・隠れた真理・選択根拠・weilの説明と全文意味一致は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored unsettled teaching differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Unsettled teaching roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_unsettled_teaching.py','scripts/check_unsettled_teaching.py','scripts/compose_institutional_voice.py',
        'scripts/check_closed_policies.py','scripts/check_conditional_release.py','scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py','scripts/check_rod_setup.py','noema/finite_semantics.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_unsettled_endorsement_and_possible_contained_truth',documents=documents,sizes=sizes,
        finite=finite_checks(texts[1:]),alignment=alignment(),new_definitions=9,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Unsettled teaching report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Unsettled endorsement, contained truth and separate modal scopes checked')


if __name__=='__main__':main()
