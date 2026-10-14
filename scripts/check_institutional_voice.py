"""Check institutional attribution, nested reporting and unexecuted duties."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_appointment_terms import APPOINTS,TERMS
from scripts.compose_institutional_voice import ROOT,PARENT,BUILDERS,VOICE,SERVES,TEACHES

REPORT=ROOT/'reports/institutional-voice-v1.json'
TRUE='e[n p a b][n p a b]'
EXTRA=('r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[a] c.r zf[] a.r zg[] d.'
    'r zh[] '+VOICE+'.r zi[] '+SERVES+'.r zj[a d] c.'
    'd zk[subject a] f[j s[b context[k zj[v subject v context]]]].'
    'd zl[subject a] f[j s[b context[k zj[v subject v context]]]].'
    'd zn[subject a] f[j q[b context[k zj[v subject v context]]]].'
    'r zm[] '+TEACHES+'.r zo[a a i[h[a] f] d] c.'
    'r zr[] '+APPOINTS+'.r zs[] '+TERMS+'.')
DOMAIN=('speaker','speech','organization','office','topic','listener','reader','other','appointment')
SCENES=('past','now','elsewhere')


def call(name):return quoted('call',name)['body']


def application(symbol,args):return {'kind':'call','symbol':symbol,'arguments':args}


def ask(body):return {'kind':'ask','body':body}


def speech_setup(text):
    doc=candidate(text,EXTRA)
    inner=quoted('function_ref','zk')
    settings=[quoted('call','zc'),quoted('call','zd'),quoted('function_ref','ze'),quoted('call','zf'),
        description(doc,'r[p zk]'),quoted('call','zh'),quoted('call','zi')]
    target=apply_description(doc,quoted('function_ref','hzbr'),settings)
    core=[call('za'),call('zb'),call('zc'),call('zd'),quoted('function_ref','ze')['body'],call('zf'),inner,call('zg')]
    doc['statements']=[ask(application('hzbp',core+[call('zh')])),ask(application('hzbq',core+[call('zh'),call('zi')]))]
    # Use a parsed template to avoid depending on the spelling of AST effects.
    template=candidate(text,EXTRA+'d zp[person a activity a] e[b context[e[v person][v person]]].q[t[c[s[r[p zp]]][k za[] k zb[]]][k zg[]]].')
    def replace(node):
        if isinstance(node,dict):
            if node==quoted('function_ref','zp'):return target
            return {n:replace(x) for n,x in node.items()}
        if isinstance(node,list):return [replace(x) for x in node]
        return node
    doc['statements'].append(replace(template['statements'][0]))
    truth=parse('n:q['+TRUE+'].')['statements'][0]['body']
    norm=[call('zc'),call('za'),call('zd'),call('zb'),target,truth,call('zg')]
    doc['statements'].append(ask(application('h7a',norm)))
    return parse(format_graph(doc,'compact')),target,inner,core


def model_for(setup,bits=(True,)*7,variant='baseline',required=True,accepted=None):
    doc,target,inner,_=setup
    occurred,presented,conveyed,voiced,positioned,entrusted,serves=bits
    accepted=accepted or inner
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='elsewhere' if label=='context' else 'other'
        return list(actual)==expected
    def conveys(activity,recipient,subject,message,context):
        return conveyed and recipient in ('listener','reader') and not(variant=='missing_reader' and recipient=='reader') and match(
            (activity,subject,context),('speech','topic','now'),'delivery',('activity','subject','context')) and message.syntax==syntax(
                quoted('function_ref','zn') if variant=='delivery_force' else quoted('function_ref','zl') if variant=='delivery_alias' else accepted)
    def voice(person,activity,principal,role,subject,message,context):
        return voiced and match((person,activity,principal,role,subject,context),
            ('speaker','speech','organization','office','topic','now'),'voice',('person','activity','principal','role','subject','context')) and message.syntax==syntax(
                quoted('function_ref','zn') if variant=='voice_force' else quoted('function_ref','zl') if variant=='voice_alias' else accepted)
    def norm(principal,person,role,activity,description,positive,context):
        return required and positive and match((principal,person,role,activity,context),
            ('organization','speaker','office','speech','now'),'norm',('principal','person','role','activity','context')) and description.syntax==syntax(target) and variant!='norm_description'
    model=guarded(doc)
    model.update(za=lambda:'speaker',zb=lambda:'speech',zc=lambda:'organization',zd=lambda:'office',
        ze=lambda recipient:variant!='empty_audience' and recipient in ('listener','reader'),zf=lambda:'topic',zg=lambda:'now',
        dg=lambda activity,context:occurred and (activity,context)==('speech','now'),
        f3=lambda person,activity,context:presented and match((person,activity,context),('speaker','speech','now'),'presentation',('person','activity','context')),
        f2=conveys,cb=lambda person,activity,role,context:positioned and match((person,activity,role,context),
            ('speaker','speech','office','now'),'position',('person','activity','role','context')),
        cf=lambda person,role,context:entrusted and match((person,role,context),('speaker','office','now'),'delegation',('person','role','context')),
        h7a=norm)
    callbacks(doc,model,{'zh':voice,'zi':lambda person,principal,role,context:serves and match(
        (person,principal,role,context),('speaker','organization','office','now'),'service',('person','principal','role','context'))})
    return model


def evaluate(doc,model):
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{name:value for name,value in model.items() if name in used},DOMAIN,SCENES)


def speech_checks(texts):
    setups=[speech_setup(text) for text in texts]
    cases=[]
    for bits in product((False,True),repeat=7):
        voiced=all(bits[:4]);delegated=voiced and all(bits[4:])
        expected=[voiced,delegated,delegated,True]
        rows=[evaluate(s[0],model_for(s,bits)) for s in setups]
        if rows!=[expected]*2:raise ValueError('Voice and delegated presentation collapsed: '+repr((bits,rows)))
        cases.append(dict(states=list(bits),results=expected))
    groups={
        'presentation':('person','activity','context'),'delivery':('activity','subject','context'),
        'voice':('person','activity','principal','role','subject','context'),
        'position':('person','activity','role','context'),'delegation':('person','role','context'),
        'service':('person','principal','role','context'),'norm':('principal','person','role','activity','context','description')}
    contrasts={}
    for variant in [group+'_'+field for group,fields in groups.items() for field in fields]+[
        'delivery_force','delivery_alias','voice_force','voice_alias','empty_audience','missing_reader']:
        expected=([True,True,True,False] if variant.startswith('norm_') else
            [True,False,False,True] if variant.split('_')[0] in ('position','delegation','service') else [False,False,False,True])
        rows=[evaluate(s[0],model_for(s,variant=variant)) for s in setups]
        if rows!=[expected]*2:raise ValueError('Voice binding differs: '+repr((variant,rows)))
        contrasts[variant]=expected
    for s in setups:
        if evaluate(s[0],model_for(s,required=False))!=[True,True,True,False]:raise ValueError('Actual speech created obligation')
        # Institutional teaching, the inner truth and personal endorsement all
        # remain guarded; the presentation and its normative target still work.
        for name in ('zh','zi','f2','f3','dg','cb','cf','h7a'):
            model=model_for(s);model[name]=guarded(s[0])[name]
            try:evaluate(s[0],model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown voice/role relation supplied: '+name)
    return dict(cases=cases,binding_contrasts=contrasts,standalone_agrees=True,
        actual_and_constructed_target_agree=True,actual_speech_does_not_create_obligation=True,
        truth_institutional_teaching_and_endorsement_not_executed=True,unknown_relations_refused=True)


def report_checks(texts):
    setups=[]
    for text in texts:
        s=speech_setup(text);doc,target,inner,core=s
        report=apply_description(doc,quoted('function_ref','rgd'),
            [quoted('call','zc'),description(doc,'r[p zk]'),quoted('call','zm')])
        reported_core=list(core);reported_core[6]=report
        doc['statements']=[ask(application('hzbp',reported_core+[call('zh')]))]
        # Construct content inspections from typed AST nodes via parsed forms.
        probes=candidate(text,EXTRA+'q[t[o[c[k rgd[k zc[] r[p zk] k zm[]]][k zf[]]]][k zg[]]].'
            'q[t[o[c[s[r[p zk]]][k zf[]]]][k zg[]]].q[k zo[k za[] k zf[] r[p zk] k zg[]]].'
            'q[e[c[k rgd[k zc[] r[p zk] k zm[]]][k zf[]]][j s[b context[c[k zm[]][k zc[] k zf[] r[p zk] v context]]]]].')
        def substitute(node,old,new):
            if node==old:return new
            if isinstance(node,dict):return {n:substitute(x,old,new) for n,x in node.items()}
            if isinstance(node,list):return [substitute(x,old,new) for x in node]
            return node
        unquote=probes['statements'][1]['body']['content']['message']['function']
        report_function=substitute(unquote,inner,report)
        direct=application('rgd',[call('zc'),inner,call('zm')])
        probes['statements']=substitute(probes['statements'],direct,report_function)
        doc['statements']+=probes['statements'];doc=parse(format_graph(doc,'compact'))
        setups.append(((doc,target,inner,core),report))
    cases=[]
    def model(s,report,taught,truth,endorsed,variant='baseline'):
        m=model_for(s,accepted=report)
        def teaches(principal,subject,message,context):
            expected=['other' if variant=='principal' else 'organization','other' if variant=='subject' else 'topic',
                'elsewhere' if variant=='context' else 'now']
            return taught and [principal,subject,context]==expected and message.syntax==syntax(
                quoted('function_ref','zn') if variant=='force' else quoted('function_ref','zl') if variant=='alias' else s[2])
        callbacks(s[0],m,{'zm':teaches})
        m['zj']=lambda subject,context:truth and (subject,context)==('topic','now')
        m['zo']=lambda person,subject,message,context:endorsed and (person,subject,context)==('speaker','topic','now') and message.syntax==syntax(s[2])
        return m
    for bits in product((False,True),repeat=3):
        expected=[True,*bits,True]
        rows=[evaluate(s[0],model(s,report,*bits)) for s,report in setups]
        if rows!=[expected]*2:raise ValueError('Nested report became factive')
        cases.append(dict(states=list(bits),results=expected))
    contrasts={}
    for variant in ('principal','subject','context','force','alias'):
        rows=[evaluate(s[0],model(s,report,True,True,True,variant)) for s,report in setups]
        if rows!=[[True,False,True,True,True]]*2:raise ValueError('Reported organization/message changed')
        contrasts[variant]=rows[0]
    for s,report in setups:
        doc=s[0];m=model_for(s,accepted=report)
        if evaluate({**doc,'statements':doc['statements'][:1]},m)!=[True]:raise ValueError('Report presentation executed nested content')
        try:evaluate({**doc,'statements':doc['statements'][:2]},m)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown institutional teaching supplied')
        m=model(s,report,True,False,False);m['zj']=guarded(doc)['zj'];m['zo']=guarded(doc)['zo']
        if evaluate({**doc,'statements':doc['statements'][:2]},m)!=[True,True]:raise ValueError('Organization report required inner truth')
        m=model(s,report,True,True,True);m['dg']=lambda *args:False
        if evaluate(doc,m)!=[False,True,True,True,True]:raise ValueError('Institutional teaching created a speech event')
    return dict(cases=cases,binding_contrasts=contrasts,report_is_assertion=True,
        nested_content_not_executed_by_presentation=True,unknown_institutional_content_refused=True,
        exact_presented_report_is_evaluated=True,institutional_teaching_does_not_create_speech=True,
        institutional_teaching_does_not_require_truth_or_endorsement=True)


def appointment_checks(texts):
    setups=[speech_setup(text) for text in texts]
    truth=parse('n:q['+TRUE+'].')['statements'][0]['body']
    for s in setups:
        doc,target,_,_=s
        args=[call('zc'),call('za'),call('zd'),call('zb'),target,truth,call('zg'),call('zr'),call('zs')]
        doc['statements']=[ask(application(name,args)) for name in ('hzbm','hzbn')]
    cases=[]
    for occurred,delegated,appointed,terms,required in product((False,True),repeat=5):
        expected=[occurred and delegated and appointed and terms,occurred and delegated and appointed and terms and required]
        rows=[]
        for s in setups:
            doc,target,_,_=s;m=model_for(s,(False,)*7,required=required)
            m.update(ia=lambda person,context,point:(person,context)==('speaker','now') and point in ('past','now'),
                ic=lambda first,second,context:(first,second,context)==('past','now','now'),
                dg=lambda activity,context:occurred and (activity,context)==('appointment','past'),
                cf=lambda person,role,context:delegated and (person,role,context)==('speaker','office','past'))
            callbacks(doc,m,{'zr':lambda event,issuer,person,role,context:appointed and
                (event,issuer,person,role,context)==('appointment','organization','speaker','office','past'),
                'zs':lambda event,activity,description,positive,context:terms and positive and
                (event,activity,context)==('appointment','speech','past') and description.syntax==syntax(target)})
            rows.append(evaluate(doc,m))
        if rows!=[expected]*2:raise ValueError('Institutional voice appointment executed the target')
        cases.append(dict(states=[occurred,delegated,appointed,terms,required],results=expected))
    return dict(cases=cases,same_closed_voice_target_used=True,present_voice_not_required=True,standalone_agrees=True)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpts=[('im Namen eines andern vorzutragen',['hzbp','hzbq','hzbr']),
        ('unsere Kirche lehrt dieses oder jenes',['rgd'])]
    segments=[]
    for excerpt,definitions in excerpts:
        if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous institutional voice range')
        start=unit['text'].index(excerpt)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=definitions,status='partial',review_ja='組織の名での提示を委任された役割と結ぶ。外側の組織教示の報告、組織の実際の教示、内側の真理、本人の賛同は別に保持する。制度の意味、集団の指示、不特定性と予想、全文意味一致は未完。'))
    return dict(segments=segments,semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored institutional voice differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Voice roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_institutional_voice.py','scripts/check_institutional_voice.py','scripts/compose_appointment_terms.py',
        'scripts/check_assessed_payments.py','scripts/check_closed_policies.py','scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/finite_semantics.py','noema/description_templates.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_institutional_voice_and_nested_reports',documents=documents,sizes=sizes,
        speech=speech_checks(texts[1:]),reports=report_checks(texts[1:]),appointment=appointment_checks(texts[1:]),alignment=alignment(),
        new_definitions=7,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Institutional voice report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Institutional voice, nested reports and unexecuted appointment targets checked')


if __name__=='__main__':main()
