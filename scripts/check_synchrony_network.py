"""Finite relational checks, pulse adapter bindings and nonfactive source attribution."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.compose_synchrony_network import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/synchrony-network-v1.json'
CLOCKS=('clocka','clockb','clockc')
DOMAIN=(*CLOCKS,'placea','placeb','frame','unit','reference','author','assumption','symmetry','fork','scope','other',
        'trialone','trialtwo','departone','reflectone','arriveone','rayone','departtwo','reflecttwo','arrivetwo','raytwo')


def values(doc,model,people=DOMAIN):
    return [row['value'] for row in evaluate_document(doc,individuals=people,situations=('text',),
        primitives=model,max_steps=5_000_000,memoize_definitions=True)]


def disjoint_cliques(nodes,edges):
    """Characterize the joint laws independently as disjoint complete components."""
    unseen={node for edge in edges for node in edge}
    while unseen:
        component={unseen.pop()}
        while True:
            expanded=component | {b for a,b in edges if a in component} | {a for a,b in edges if b in component}
            if expanded==component: break
            component=expanded
        if {(a,b) for a in component for b in component} != {edge for edge in edges if edge[0] in component}:
            return False
        unseen-=component
    return True


def relation_checks():
    doc=parse(generic_composed()[0]+'''
r za[a] c.r zb[a a] c.r zc[] a.
q[k saa[p za p zb]].q[k sab[p za p zb]].q[k sac[p za p zb k zc[]]].
''')
    rows=[]
    pairs=tuple(product(CLOCKS,repeat=2))
    for bits in product((False,True),repeat=9):
        edges={pair for pair,bit in zip(pairs,bits) if bit}
        model={'za':lambda clock:clock in CLOCKS,'zb':lambda a,b:(a,b) in edges,'zc':lambda:'clocka'}
        actual=values(doc,model,CLOCKS)
        symmetric=edges=={(b,a) for a,b in edges}
        fork=all((b,c) in edges for a,b in edges for x,c in edges if a==x)
        common=all((clock,'clocka') in edges for clock in CLOCKS)
        if actual!=[symmetric,fork,common] or (actual[0] and actual[1])!=disjoint_cliques(CLOCKS,edges):
            raise ValueError('Relational laws differ from independent clique characterization')
        if all(actual) and edges!=set(pairs): raise ValueError('A shared reference did not yield pairwise agreement')
        rows.append({'relation':''.join('1' if bit else '0' for bit in bits),'symmetric':actual[0],
                     'common_source_law':actual[1],'same_reference':actual[2]})
    empty=values(doc,{'za':lambda clock:False,'zb':lambda a,b:False,'zc':lambda:'clocka'},CLOCKS)
    if empty!=[True,True,False]: raise ValueError('Empty laws were confused with a common reference')
    return {'cases':rows,'joint_law_models':sum(r['symmetric'] and r['common_source_law'] for r in rows),
        'same_reference_models':sum(r['same_reference'] for r in rows),
        'all_three_models':sum(r['symmetric'] and r['common_source_law'] and r['same_reference'] for r in rows),
        'empty_selection':empty,'arbitrary_size_physical_realizability_proved':False}


def trial_checks():
    doc=parse(generic_composed()[0]+'r za[a] c.r zb[a] c.q[k sad[p za p zb]].')
    rows=[]
    for selected in product((False,True),repeat=2):
        for accepted in product((False,True),repeat=2):
            model={'za':lambda trial:selected[('one','two').index(trial)],
                   'zb':lambda trial:accepted[('one','two').index(trial)]}
            actual=values(doc,model,('one','two'))[0]
            expected=any(selected) and all(not relevant or valid for relevant,valid in zip(selected,accepted))
            if actual!=expected: raise ValueError('Single successful or empty trial set accepted')
            rows.append({'selected':list(selected),'criteria':list(accepted),'accepted':actual})
    return rows


def source_model(doc):
    def forbidden(*args): raise ValueError('Unexpected physical or numeric evaluation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    model.update(ra=lambda:'frame',rb=lambda:'unit',rc=lambda:'clocka',rd=lambda:'author',re=lambda:'assumption',
        rf=lambda:'symmetry',rg=lambda:'fork',rh=lambda:'scope',ri=lambda:'text',
        qa=lambda clock,frame,context:clock in CLOCKS and (frame,context)==('frame','text'),
        ca=lambda clock:clock in CLOCKS,cc=lambda clock,frame:clock in CLOCKS and frame=='frame',
        cb=lambda obj,place,frame:obj in CLOCKS and place=='placea' and frame=='frame',ci=lambda unit:unit=='unit')
    return model


def scope_checks():
    doc=candidate(source_composed()[0],'q[k qv[k ra[] k rb[] k ri[]]].')
    rows={}
    for variant in ('baseline','empty','nonclock_selected','moving_clock','no_location','other_frame','other_context','not_time_unit'):
        model=source_model(doc)
        if variant=='empty': model['qa']=lambda *args:False
        if variant=='nonclock_selected': model['qa']=lambda clock,frame,context:clock=='other'
        if variant=='moving_clock': model['cc']=lambda clock,frame:clock in CLOCKS[1:] and frame=='frame'
        if variant=='no_location': model['cb']=lambda obj,place,frame:obj in CLOCKS[1:] and place=='placea' and frame=='frame'
        if variant=='other_frame': model['ra']=lambda:'other'
        if variant=='other_context': model['qa']=lambda clock,frame,context:clock in CLOCKS and context=='other'
        if variant=='not_time_unit': model['ci']=lambda unit:False
        actual=values(doc,model)[0]
        if actual!=(variant=='baseline'): raise ValueError('Clock scope silently dropped an invalid selected clock: '+variant)
        rows[variant]=actual
    return rows


def adapter_checks():
    doc=candidate(source_composed()[0],'''
r za[] a.r zb[] a.r zt[] h[a a a a a a a a a a h[b] c h[b] c h[b] c] c.
q[k qn[k za[] k zb[] k ra[] k rb[] k ri[] k zt[]]].
''')
    signature=next(d['result'] for d in doc['declarations'] if d['name']=='zt')
    rows={}
    variants=('baseline','second_trial_fails','empty_trials','incomplete_trials','foreign_frame_trials',
        'foreign_unit_trials','wrong_first_clock','wrong_second_clock','wrong_departure_place','wrong_reflection_place',
        'wrong_departure','wrong_reflection','wrong_return','wrong_ray','mixed_readings')
    for variant in variants:
        model=source_model(doc)
        trials=('trialone','trialtwo')
        records={trial:('placea','placeb',*tuple(prefix+suffix for prefix in ('depart','reflect','arrive','ray')))
                 for trial,suffix in zip(trials,('one','two'))}
        model.update(za=lambda:'other' if variant=='wrong_first_clock' else 'clocka',
            zb=lambda:'other' if variant=='wrong_second_clock' else 'clockb',
            ql=lambda a,b,frame,unit,context:variant!='incomplete_trials',
            qb=lambda a,b,frame,unit,context,trial:variant!='empty_trials' and trial in trials and
                (frame,unit,context)==('other' if variant=='foreign_frame_trials' else 'frame',
                                     'other' if variant=='foreign_unit_trials' else 'unit','text'))
        variant_for=('wrong_departure_place','wrong_reflection_place','wrong_departure','wrong_reflection','wrong_return','wrong_ray')
        for index,name in enumerate(('qc','qd','qe','qf','qg','qh')):
            model[name]=lambda trial,index=index:'other' if variant==variant_for[index] else records.get(trial,('other',)*6)[index]
        for index,name in enumerate(('qi','qj','qk')):
            def read(trial,index=index):
                value=index+(2 if trial=='trialtwo' else 0)
                if variant=='mixed_readings' and trial=='trialtwo' and index==1:value=0
                return FunctionValue(('number',),'truth',lambda q:q<value)
            model[name]=read
        seen=[]
        def criterion(first,second,placea,placeb,depart,reflect,arrive,ray,frame,unit,start,middle,end):
            suffix='two' if depart=='departtwo' else 'one'
            expected=('clocka','clockb','placea','placeb','depart'+suffix,'reflect'+suffix,'arrive'+suffix,'ray'+suffix,'frame','unit')
            actual=(first,second,placea,placeb,depart,reflect,arrive,ray,frame,unit)
            readings=tuple(tuple(cut(Fraction(n,2)) for n in range(-1,10)) for cut in (start,middle,end))
            offset=2 if suffix=='two' else 0
            expected_readings=tuple(tuple(Fraction(n,2)<offset+i for n in range(-1,10)) for i in range(3))
            seen.append(list(actual))
            return actual==expected and readings==expected_readings and not (variant=='second_trial_fails' and suffix=='two')
        model['zt']=lambda:FunctionValue(tuple(signature['parameters']),signature['result'],criterion)
        actual=values(doc,model)[0]
        if actual!=(variant=='baseline'): raise ValueError('Protocol argument or complete trial scope differs: '+variant)
        rows[variant]={'accepted':actual,'criterion_calls':len(seen)}
    return {'cases':rows,'criterion_is_injected_binding_oracle':True,
        'full_real_cut_protocol_evaluated':False,
        'limit':'Probes distinguish only the explicit rational embeddings in this fixture. They do not decide arbitrary real-cut equality.'}


def attribution_checks():
    doc=parse(source_composed()[0])
    rows={}
    for variant in ('baseline','no_assumption','wrong_scope','wrong_author','wrong_assumed_content','swapped_laws'):
        model=source_model(doc)
        def name(description): return json.loads(description.syntax)['symbol']
        model['ug']=lambda node,author,content,scope,context: variant!='no_assumption' and (
            node,author,name(content),scope,context)==('assumption','other' if variant=='wrong_author' else 'author',
                'qs' if variant=='wrong_assumed_content' else 'qr','other' if variant=='wrong_scope' else 'scope','text')
        model['uh']=lambda node,author,content,scope,context:(node,author,name(content),scope,context) in (
            ('symmetry','author','qq' if variant=='swapped_laws' else 'qp','scope','text'),
            ('fork','author','qp' if variant=='swapped_laws' else 'qq','scope','text'))
        actual=values(doc,model)[0]
        if actual!=(variant=='baseline'): raise ValueError('Assumption scope or law reference differs: '+variant)
        rows[variant]={'attributed':actual,'physical_contents_evaluated':False}
    return rows


def alignment():
    units=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))['units']
    hashes={15:'c7dcd8fcbdbb158bf9f602402fdce4c9b401e37b1dec571db5a3050cf9b3d482',
        16:'d21e0175205f5ca74208e90a5654dc7701d5dee5f97ab1972d34c9f0f317f0a1',
        17:'994305085317b0739bcc1b504d384273b5a91e0dd73b46d65198987a32bad6b7',
        18:'b2fea62ee64ba6bc7aae1ee4d8efb0e739ed115a90500377e2a601b982d64b9f'}
    rows=[]
    for number,names in ((15,['qr']),(16,['saa','qp']),(17,['sab','qq']),(18,['sac','qs'])):
        unit=next(u for u in units if u['id']==f'einstein-1905:u{number:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=hashes[number]:raise ValueError('Pinned synchrony source differs')
        start=unit['text'].index('welche mit einer bestimmten') if number==18 else 0
        excerpt=unit['text'][start:]
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'start':start,'end':len(unit['text']),
            'source':excerpt,'definitions':names,'status':'partial_explicit_reading','full_semantic_equivalence':False,
            'remaining':['physical grounding and complete trial scope','arbitrary-size realizability',
                         'all temporal determinations and event readings','facsimile review']})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored synchrony differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Synchrony roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    files=[*documents,'data/synchrony-network-basis-v1.json','data/einstein-synchrony-network-basis-v1.json',
        'examples/v011/einstein-clock-protocol.noema','data/clock-protocol-basis-v1.json',
        'scripts/compose_synchrony_network.py','scripts/check_synchrony_network.py',
        'noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_scoped_synchrony_laws_and_same_reference','documents':documents,
        'relations':relation_checks(),'trials':trial_checks(),'clock_scope':scope_checks(),'adapter':adapter_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'full_physical_synchrony_consistency_verified':False,
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--verify-only',action='store_true')
    args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Synchrony network report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2)
            stream.write('\n')
    print('512 relation models, 16 trial scopes, 8 clock scopes, 15 argument bindings, 6 attributions checked')


if __name__=='__main__':main()
