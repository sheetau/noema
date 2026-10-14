"""Check minimum source scopes without inferring exhaustive release."""
import argparse
import hashlib
from itertools import product
import json
from noema.finite_semantics import Content
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts import check_first_achievers as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_first_achievers import CONFIG
from scripts.compose_limited_release import ROOT,PARENT,BUILDERS,SETTINGS,MEANINGS

REPORT=ROOT/'reports/limited-release-v1.json'
SCENES=prior.SCENES
SOURCES=('governor','private')
DOMAIN=(*prior.DOMAIN,'private')
EXTRA='r jpminimum[a] c.r jpbroader[a] c.r jpcondition[a a] e.r jpsubject[] a.r jpcontext[] d.r jpother[] a.'


def setup(text,source=False):
    old=prior.setup(text,True) if source else None
    base=old['document'] if source else parse(text);base['statements']=[];base=parse(format_graph(base,'compact')+EXTRA)
    condition='p jpcondition';removed=0
    if source:
        fields=dict(members='p jomembers',roles='p joroles',topic='k jotopic[]',anchor='k joview[]',activities='p joactivities',
            descriptions='i[person a activity a][r[p joexecution]]',assessed='p joevaluated')
        condition=k('hzgg',*(fields[n] for n,_ in SETTINGS))
        limited=k('hzgh','k jogovernor[]','p jpbroader',*(fields[n] for n,_ in SETTINGS))
    else:limited=k('roi','p jpminimum','p jpbroader',condition)
    broad=k('roi','p jpbroader','p jpbroader',condition)
    at=lambda expr:'t['+expr+'][k jpcontext[]]';ap=lambda property:at('c['+property+'][k jpsubject[]]')
    queries=[k('roh','p jpminimum','p jpbroader'),ap(limited),ap(broad)]
    first=None
    if source:
        spec=specialize_definition(base,'hzge','jpfacts',{2:description(base,limited)});base=spec.document;removed=spec.disquotations_removed
        facts=k('jpfacts','p johistory','p jobefore')
        refs={**old['refs'],'goal':'r['+limited+']','achieves':facts}
        first=k('rod',*(refs[n] for n,_ in CONFIG))
        actual='c['+facts+'][k joperson[] k joactivity[] k jotarget[] r['+limited+'] k jopoint[]]'
        queries=[ap(limited),ap(broad),at('c['+condition+'][k jpother[] k jpsubject[]]'),actual,at('c['+first+'][k joperson[]]'),'e[r['+first+']][r['+first+']]']
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,source=source,old=old,limited=limited,broad=broad,condition=condition,first=first,
        goal_syntax=syntax(description(base,limited)),disquotations_removed=removed)


def generic_model(data,bits=(True,False,True,True,True,False)):
    minimum,broader,status=bits[:2],bits[2:4],bits[4:]
    model=guarded(data['document'])
    model.update(jpminimum=lambda s:s in SOURCES and minimum[SOURCES.index(s)],jpbroader=lambda s:s in SOURCES and broader[SOURCES.index(s)],
        jpcondition=lambda s,person:Content(SCENES,(person=='group' and s in SOURCES and status[SOURCES.index(s)],)*len(SCENES)),
        jpsubject=lambda:'group',jpcontext=lambda:'late',jpother=lambda:'private')
    return model


def source_model(data,bits=(True,True,False,False),variant='baseline'):
    positive,negative,other_positive,other_negative=bits
    model=prior.source_model(data['old'],'unassessed' if variant=='unassessed' else 'baseline')
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    def scope(source):
        if variant=='empty_broader':return False
        return source=='private' or source=='governor' and variant!='missing_government'
    def target(source,person,role,act,desc):
        return source in SOURCES and person in ('alice','bob') and (role,act)==('role','act') and desc.syntax==data['old']['execution_syntax']
    def allowed(source,person,role,act,desc,sign,point):
        if not target(source,person,role,act,desc):return False
        if variant=='private_wrong_activity' and source=='private' and person=='bob':return False
        return (positive if sign else negative) and point=='late' if source=='governor' else (other_positive if sign else other_negative)
    model.update(jpminimum=lambda s:s=='governor',jpbroader=scope,jpsubject=lambda:'group',jpcontext=lambda:'late',jpother=lambda:'private',
        h7a=lambda source,person,role,act,desc,sign,point:variant in ('government_requirement','private_requirement') and source==('governor' if variant=='government_requirement' else 'private') and target(source,person,role,act,desc) and sign,
        h7b=allowed,g3=lambda activity,subject,desc,point:variant!='no_cause' and (activity,subject,point)==('act','group','late') and desc.syntax==data['goal_syntax'])
    if variant=='wrong_group':model['jpsubject']=lambda:'alice';model['jotarget']=lambda:'alice'
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=48_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        minimum,broader,status=bits[:2],bits[2:4],bits[4:]
        valid=any(minimum) and all(not a or b for a,b in zip(minimum,broader))
        expected=[valid,valid and all(not a or b for a,b in zip(minimum,status)),any(broader) and all(not a or b for a,b in zip(broader,status))]
        result=values(data,generic_model(data,bits))
        if result!=expected:raise ValueError('Scope lattice failed: '+repr((bits,result,expected)))
        grid.append(dict(bits=list(bits),result=result))
    print('64 minimum/broader/source-condition profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);norms=[];cases={}
        for bits in product((False,True),repeat=4):
            limited=all(bits[:2]);other=all(bits[2:]);expected=[limited,limited and other,other,limited,limited,True]
            result=values(data,source_model(data,bits))
            if result!=expected:raise ValueError('Norm sources conflated: '+repr((bits,result)))
            norms.append(dict(bits=list(bits),result=result))
        for variant,expected in (
            ('missing_government',[False,True,True,False,False,True]),('empty_broader',[False,False,True,False,False,True]),
            ('private_wrong_activity',[True,False,False,True,True,True]),('government_requirement',[False,False,True,False,False,True]),
            ('private_requirement',[True,False,False,True,True,True]),('no_cause',[True,True,True,False,False,True]),('unassessed',[True,True,True,True,False,True]),('wrong_group',[False,False,False,False,False,True])):
            result=values(data,source_model(data,(True,)*4,variant))
            if result!=expected:raise ValueError('Limited release contrast failed: '+repr((variant,result,expected)))
            cases[variant]=result
        rows.append(dict(norms=norms,cases=cases,disquotations_removed=data['disquotations_removed']));print('Source limited-release contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Limited-release artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Limited-release roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    phrase='wenigstens von Seiten der Regierung';start=unit['text'].index(phrase)
    paths={*documents,PARENT,'examples/v014/first-achievers-core.noema',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_limited_release.py','scripts/check_limited_release.py','scripts/check_first_achievers.py','scripts/compose_first_achievers.py','scripts/compose_scoped_nonprescription.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py','noema/higher_order_semantics.py','noema/finite_semantics.py',
        'noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_release_relative_to_selected_sources',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=4,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Limited-release record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Minimum scope, broader release and first achievement remain distinct')


if __name__=='__main__':main()
