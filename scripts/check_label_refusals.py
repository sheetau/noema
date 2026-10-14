"""Verify refusal presentation, name use, descriptive truth and message force separately."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_label_refusals import ROOT,PARENT,BUILDERS,SETTINGS,SOURCE_SETTINGS,MEANINGS

REPORT=ROOT/'reports/label-refusals-v1.json'
DOMAIN=('leader','caller','other','label','alternate','speech','naming','otheract')
SCENES=('now','later')
EXTRA="""r jwperson[] a.r jwactivity[] a.r jwlabel[] a.r jwcontext[] d.r jwnamer[] a.r jwnaming[] a.
r jwusers[a] c.r jwoccurs[a d] c.r jwpresents[a a d] c.r jwassigns[a a a d] c.
r jwconveys[a a a i[h[a] f] d] c.r jwquality[a a d] c."""


def setup(text,source=False,label='k jwlabel[]',users='p jwusers'):
    base=candidate(text,EXTRA)
    refs={'label':label,'users':users,'assigns':'p jwassigns','occurs':'p dg' if source else 'p jwoccurs',
        'presents':'p f3' if source else 'p jwpresents'}
    fields=SOURCE_SETTINGS if source else SETTINGS
    message=k('hzfw' if source else 'rnj',*(refs[n] for n,_ in fields))
    content=k('hzfv' if source else 'rni',*(refs[n] for n,_ in fields))
    reportargs=['k jwperson[]','k jwactivity[]',users,'r['+message+']','k jwcontext[]']
    report=k('hzft',*reportargs) if source else k('rnc',*reportargs,refs['occurs'],refs['presents'],'p jwconveys')
    naming=k('rnh','k jwnamer[]','k jwnaming[]',label,'k jwperson[]','k jwcontext[]',refs['occurs'],refs['presents'],refs['assigns'])
    actualcontent='c['+content+'][k jwperson[]]'
    queries=[report,'t['+actualcontent+'][k jwcontext[]]',naming,k('jwquality',label,'k jwperson[]','k jwcontext[]'),
        'e[c['+message+'][k jwperson[]]][j s['+actualcontent+']]']
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,source=source,message=message,content=content,label=label,users=users,
        message_syntax=syntax(description(base,message)))


def model_for(data,bits=(True,True,True,True,True),variant='baseline'):
    occurs,presents,conveys,used,quality=bits
    model=guarded(data['document'])
    occurrence=lambda act,point: point=='now' and ((act=='speech' and occurs) or (act=='naming' and used))
    presenter=lambda person,act,point: point=='now' and ((presents and (person,act)==(
        'other' if variant=='wrong_speaker' else 'leader','otheract' if variant=='wrong_speech' else 'speech')) or (
        person,act)==('other' if variant=='wrong_namer' else 'caller','naming'))
    assignment=lambda act,label,subject,point: (act,label,subject,point)==(
        'otheract' if variant=='wrong_naming_act' else 'naming','alternate' if variant=='other_label' else 'label',
        'other' if variant=='other_target' else 'leader','later' if variant=='later_naming' else 'now')
    delivery=lambda act,recipient,subject,desc,point: conveys and variant!='wrong_message' and (
        act,recipient,subject,point)==('speech','caller','other' if variant=='wrong_report_subject' else 'leader',
        'later' if variant=='later_report' else 'now') and desc.syntax==data['message_syntax']
    model.update(jwperson=lambda:'leader',jwactivity=lambda:'speech',jwlabel=lambda:'label',jwcontext=lambda:'now',
        jwnamer=lambda:'caller',jwnaming=lambda:'naming',jwusers=lambda person: person=='caller' and variant!='empty_users',
        jwoccurs=occurrence,jwpresents=presenter,jwassigns=assignment,jwconveys=delivery,
        jwquality=lambda label,subject,point: quality and label in ('label','alternate') and subject=='leader')
    if data['source']:model.update(dg=occurrence,f3=presenter,f2=delivery)
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=2_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=5):
        occurs,presents,conveys,used,quality=bits
        expected=[occurs and presents and conveys,not used,used,quality,False]
        actual=values(data,model_for(data,bits))
        if actual!=expected:raise ValueError('Refusal conflated with content: '+repr((bits,actual)))
        grid.append(dict(bits=list(bits),result=actual))
    rows=[];print('32 refusal/use/descriptive-truth profiles passed',flush=True)
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','wrong_speaker','wrong_speech','wrong_report_subject','wrong_message','later_report','empty_users',
            'other_label','other_target','wrong_namer','wrong_naming_act','later_naming'):
            expected=[True,False,True,True,False]
            if variant in ('wrong_speaker','wrong_speech','wrong_report_subject','wrong_message','later_report','empty_users'):expected[0]=False
            if variant in ('other_label','other_target','wrong_namer','wrong_naming_act','later_naming'):expected[1:3]=[True,False]
            actual=values(data,model_for(data,variant=variant))
            if actual!=expected:raise ValueError('Refusal source contrast failed: '+repr((variant,actual)))
            cases[variant]=actual
        rows.append(cases);print('Source label-refusal contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Label refusal artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2'))) != doc:raise ValueError('Label-refusal roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:
        raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    start=unit['text'].index('den hoch');end=unit['text'].index(': ist selbst')
    paths={*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_label_refusals.py','scripts/check_label_refusals.py','scripts/check_described_appraisals.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_communicated_refusal_of_a_designation',documents=documents,sizes=sizes,interpretation=checks(texts),
        parent_preserved=True,roundtrips=True,new_definitions=5,new_primitives=0,new_author_statements=0,
        alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,end],text=unit['text'][start:end],definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Label refusal record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Refusal, compliance, descriptive truth and directive force remain distinct')


if __name__=='__main__':main()
