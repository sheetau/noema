"""Verify a label's explicit description, adoption, self-reference and truth separately."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts import check_policy_discretion as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_described_routines import matcher
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_policy_discretion import CLAIM,SOURCE_CLAIM,DUTY
from scripts.compose_described_labels import ROOT,PARENT,BUILDERS,USE,USE_FIELDS,ALL,FIXED,SOURCE_FIXED,MEANINGS

REPORT=ROOT/'reports/described-labels-v1.json'
DOMAIN=(*prior.DOMAIN,'label')
SCENES=prior.SCENES
EXTRA="""r jylabel[] a.r jysubject[] a.r jyoccurs[a d] c.r jypresents[a a d] c.r jyassigns[a a a d] c.
r jystored[a i[h[a] e] d] c.r jyuse[a a a d] c.r jyapplied[a i[e] a d] c."""


def setup(text,source=False,argument='k jtperson[]',instance_argument=None):
    old=prior.setup(text,source);base=old['document'];base['statements']=[]
    base=parse(format_graph(base,'compact')+EXTRA)
    spec=specialize_definition(base,'hzf3' if source else 'rnl','jyknown',{2:description(base,old['old']['policy'])})
    base=spec.document
    pattern=k('jyknown',old['refs']['assessor'],old['refs']['office']) if source else k('rnp',k('jyknown',*(old['refs'][n] for n,_ in DUTY if n!='policy')))
    instance='c['+pattern+']['+(argument if instance_argument is None else instance_argument)+']'
    refs={**old['refs'],'speaker':old['refs']['person'],'subject':'k jysubject[]','label':'k jylabel[]',
        'pattern':'r['+pattern+']','argument':'r['+argument+']','instance':'r['+instance+']',
        'occurs':'p dg' if source else 'p jyoccurs','presents':'p f3' if source else 'p jypresents','assigns':'p jyassigns',
        'stored':'p hw2' if source else 'p jystored','use':'p hx2' if source else 'p jyuse','applied':'p hy2' if source else 'p jyapplied'}
    assumed=k('hzf4' if source else 'rnt',refs['standing'],*(refs[n] for n,_ in (SOURCE_FIXED if source else FIXED)))
    claimrefs={**old['refs'],'assumes':assumed}
    critique=k('hzf2' if source else 'rno',*(claimrefs[n] for n,_ in (SOURCE_CLAIM if source else CLAIM)))
    queries=[k(n,*(refs[f] for f,_ in fields)) for n,fields in (('rnh',USE),('rnq',USE_FIELDS),('rnr',ALL),('rns',ALL))]
    queries += ['c['+assumed+']['+' '.join(refs[n] for n in ('speaker','activity','standing','context'))+']',
        't[c['+pattern+']['+refs['speaker']+']]['+refs['context']+']','t['+critique+']['+refs['context']+']']
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,old=old,source=source,refs=refs,pattern=pattern,instance=instance,assumed=assumed,critique=critique,
        pattern_syntax=syntax(description(base,pattern)),instance_syntax=syntax(description(base,instance)),
        disquotations_removed=spec.disquotations_removed,matcher=matcher(doc))


def model_for(data,bits=(True,True,True,True,False,True),variant='baseline'):
    named,stored,used,adopted,choice,grant=bits
    model=prior.model_for(data['old'],(grant,True,choice,not choice,False,False))
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    occurs=lambda act,point:named and (act,point)==('act','now')
    presents=lambda person,act,point:(person,act,point)==('coholder' if variant=='other_namer' else 'leader','otheract' if variant=='other_naming_act' else 'act','now')
    assigns=lambda act,label,subject,point:(act,label,subject,point)==('act','external' if variant=='other_label' else 'label',
        'coholder' if variant=='other_target' else 'leader','now')
    holds=lambda label,pattern,point:stored and (label,point)==('external' if variant=='other_stored_label' else 'label',
        'elsewhere' if variant=='other_stored_context' else 'now') and pattern.syntax==data['pattern_syntax'] and variant!='other_stored_pattern'
    use=lambda person,label,act,point:used and (person,label,act,point)==('coholder' if variant=='other_user' else 'leader','label',
        'otheract' if variant=='other_use_act' else 'act','now')
    applied=lambda person,instance,act,point:adopted and (person,act,point)==('leader','otheract' if variant=='other_adoption_act' else 'act','now') and instance.syntax==data['instance_syntax'] and variant!='other_instance'
    model.update(jylabel=lambda:'label',jysubject=lambda:'leader',jyoccurs=occurs,jypresents=presents,jyassigns=assigns,
        jystored=holds,jyuse=use,jyapplied=applied,rbo=data['matcher'])
    if data['source']:model.update(dg=occurs,f3=presents,hw2=holds,hx2=use,hy2=applied)
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=16_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        named,stored,used,adopted,choice,grant=bits;matched=named and stored;selfuse=matched and used and adopted
        expected=[named,matched,selfuse,selfuse,selfuse,choice and grant,selfuse and not choice]
        actual=values(data,model_for(data,bits))
        if actual!=expected:raise ValueError('Described label conflated: '+repr((bits,actual)))
        grid.append(dict(bits=list(bits),result=actual))
    print('64 described-label/use/adoption/truth profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','other_namer','other_naming_act','other_label','other_target','other_stored_label','other_stored_context','other_stored_pattern','other_user','other_use_act','other_adoption_act','other_instance'):
            expected=[True,True,True,True,True,False,True]
            if variant!='baseline':
                cutoff=0 if variant in ('other_namer','other_naming_act','other_label','other_target') else (1 if variant.startswith('other_stored') else 2)
                expected[cutoff:5]=[False]*(5-cutoff);expected[6]=False
            actual=values(data,model_for(data,variant=variant))
            if actual!=expected:raise ValueError('Described-label source contrast failed: '+repr((variant,actual)))
            cases[variant]=actual
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source described-label contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Described-label artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Described-label roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    phrase='Namen der Toleranz';start=unit['text'].index(phrase)
    paths={*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_described_labels.py','scripts/check_described_labels.py','scripts/check_policy_discretion.py','scripts/check_scoped_nonprescription.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_described_routines.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','noema/description_templates.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_explicit_description_of_a_label',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=7,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Described-label record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Explicit label meaning, use, self-adoption and actual truth remain distinct')


if __name__=='__main__':main()
