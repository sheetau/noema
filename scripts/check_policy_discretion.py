"""Check elective permission, required realization and assumed normative latitude."""
import argparse
import hashlib
from itertools import product
import json
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts import check_scoped_nonprescription as prior
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_policy_discretion import ROOT,PARENT,BUILDERS,DUTY,SOURCE_DUTY,CLAIM,SOURCE_CLAIM,MEANINGS

REPORT=ROOT/'reports/policy-discretion-v1.json'
DOMAIN=(*prior.DOMAIN,'discretion')
SCENES=prior.SCENES
EXTRA='r jxactivity[] a.r jxstanding[] a.r jxassumes[a a a d] c.'


def setup(text,source=False):
    old=prior.setup(text,source);base=old['document'];base['statements']=[]
    base=parse(format_graph(base,'compact')+EXTRA)
    refs={**old['refs'],'policy':'r['+old['policy']+']','required':'p h7k' if source else 'p jtouterrequired',
        'allowed':'p h7l' if source else 'p jtouterallowed','activity':'k jxactivity[]','standing':'k jxstanding[]','assumes':'p jxassumes'}
    fields=SOURCE_DUTY if source else DUTY
    policies=[k(n,*(refs[f] for f,_ in fields)) for n in (('hzfx','hzfy','hzfz') if source else ('rnk','rnl','rnm'))]
    bindings='l[a]['+refs['person']+']';context=refs['context']
    at=lambda expr:'t['+expr+']['+context+']'
    applied=lambda expr:at('c['+expr+']['+bindings+']')
    claim=k('hzf2' if source else 'rno',*(refs[n] for n,_ in (SOURCE_CLAIM if source else CLAIM)))
    criterion=k('rnn',refs['standing'],*(refs[n] for n,_ in DUTY))
    queries=[applied(old['policy']),*[applied(p) for p in policies],at(claim),at('c['+criterion+']['+refs['person']+' '+refs['standing']+']')]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,old=old,source=source,refs=refs,policies=policies,claim=claim,criterion=criterion,bindings=bindings)


def model_for(data,bits=(True,True,True,True,False,True),variant='baseline'):
    grant,allow,abstain,require,prohibit,assume=bits
    model=prior.model_for(data['old'],(False,False,grant,grant,False,False))
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    def target(source,person,office,desc,bindings,point):
        return (source,person,office,point)==('external' if variant=='other_source' else 'assessor',
            'coholder' if variant=='other_person' else 'leader','suboffice' if variant=='other_office' else 'crown',
            'elsewhere' if variant=='other_context' else 'now') and desc.syntax==data['old']['policy_syntax'] and bindings.items==('leader',) and variant!='other_policy'
    required=lambda source,person,office,desc,bindings,sign,point:target(source,person,office,desc,bindings,point) and (require if sign else prohibit)
    allowed=lambda source,person,office,desc,bindings,sign,point:target(source,person,office,desc,bindings,point) and (allow if sign else abstain)
    model.update(jtouterrequired=required,jtouterallowed=allowed,jxactivity=lambda:'act',jxstanding=lambda:'discretion',
        jxassumes=lambda person,activity,standing,point:assume and (person,activity,standing,point)==(
            'coholder' if variant=='other_claimant' else 'leader','otheract' if variant=='other_activity' else 'act',
            'crown' if variant=='other_standing' else 'discretion','belief' if variant=='other_claim_context' else 'now'))
    if data['source']:model.update(h7k=required,h7l=allowed)
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=12_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        grant,allow,abstain,require,prohibit,assume=bits
        choice=allow and abstain and not require and not prohibit
        expected=[grant,choice,grant and choice,grant and require,assume and not choice,choice]
        actual=values(data,model_for(data,bits))
        if actual!=expected:raise ValueError('Discretion/obligation conflated: '+repr((bits,actual)))
        grid.append(dict(bits=list(bits),result=actual))
    print('64 discretionary-policy and assumed-standing profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','other_claimant','other_activity','other_standing','other_claim_context','other_source','other_person','other_office','other_context','other_policy'):
            expected=[True,False,False,True,True,False]
            if variant.startswith('other_'):
                if variant in ('other_claimant','other_activity','other_standing','other_claim_context'):expected[4]=False
                else:expected[3]=False
            actual=values(data,model_for(data,variant=variant))
            if actual!=expected:raise ValueError('Source discretion contrast failed: '+repr((variant,actual)))
            cases[variant]=actual
        rows.append(cases);print('Source policy-discretion contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Policy discretion artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Policy discretion roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    phrases=[unit['text'][unit['text'].index('für Pflicht'):unit['text'].index(', der also')], 'hochmüthigen Namen der Toleranz']
    segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[unit['text'].index(p),unit['text'].index(p)+len(p)],text=p,definitions=list(MEANINGS)) for p in phrases]
    paths={*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_policy_discretion.py','scripts/check_policy_discretion.py','scripts/check_scoped_nonprescription.py',
        'scripts/check_described_appraisals.py','scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_discretion_and_duty_contrast',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=9,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=segments),
        source_context=dict(url='https://korpora.org/kant/aa08/040.html',accessed='2026-10-14',edition='AA VIII, p. 40, lines 28-35',
            interpretation_not_explicit_in_source=True),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Policy discretion record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Discretion, policy realization, duty and assumed standing remain distinct')


if __name__=='__main__':main()
