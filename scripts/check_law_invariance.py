"""Countermodels distinguish shared laws, shared histories and equal coordinates."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.compose_law_invariance import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/law-invariance-v1.json'


def values(doc,model,domain):
    return [row['value'] for row in evaluate_document(doc,individuals=domain,situations=('text',),
        primitives=model,max_steps=15_000_000,memoize_definitions=True)]


def representation_checks():
    doc=parse(generic_composed()[0]+'''
r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[a a a] c.r zf[a a] c.
q[k sap[k za[] k zb[] k zc[] k zd[] p ze p zf]].
''')
    representations=('leftone','lefttwo','rightone','righttwo')
    domain=(*representations,'history','first','second','law')
    rows=[]
    for available in product((False,True),repeat=4):
        for admissible in product((False,True),repeat=4):
            selected={rep for rep,chosen in zip(representations,available) if chosen}
            left=selected & set(representations[:2]);right=selected & set(representations[2:])
            allowed={rep for rep,ok in zip(representations,admissible) if ok}
            model={'za':lambda:'history','zb':lambda:'first','zc':lambda:'second','zd':lambda:'law',
                'ze':lambda history,frame,rep:history=='history' and rep in (left if frame=='first' else right if frame=='second' else set()),
                'zf':lambda law,rep:law=='law' and rep in allowed}
            actual=values(doc,model,domain)[0]
            expected=bool(left and right) and all((a in allowed)==(b in allowed) for a in left for b in right)
            if actual!=expected:raise ValueError('Representation existence or all-pair agreement differs')
            rows.append({'available':list(available),'admissible':list(admissible),'preserved':actual})
    return rows


def coordinate_examples():
    doc=parse(generic_composed()[0]+'''
r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[a a a] c.r zf[a a] c.
q[k sap[k za[] k zb[] k zc[] k zd[] p ze p zf]].
''')
    rows=[]
    for points in product((-1,0,1),repeat=3):
        for speed,offset in product((-1,0,1),(-2,0,2)):
            transformed=tuple(x-speed*t+offset for t,x in enumerate(points))
            records={'left':points,'right':transformed}
            base={'za':lambda:'history','zb':lambda:'first','zc':lambda:'second','zd':lambda:'law',
                'ze':lambda h,f,r:h=='history' and (f,r) in {('first','left'),('second','right')}}
            def constant_difference(law,representation):
                p=records.get(representation)
                return law=='law' and p is not None and p[2]-p[1]==p[1]-p[0]
            actual=values(doc,{**base,'zf':constant_difference},('history','first','second','law','left','right'))[0]
            if not actual:raise ValueError('Affine change failed to preserve equal successive differences')
            rows.append({'positions':list(points),'relative_step':speed,'origin':offset,'transformed':list(transformed),'preserved':actual})
    # Rest of the coordinate values is not preserved by this same transformation.
    records={'left':(0,0,0),'right':(0,-1,-2)}
    model={**base,'zf':lambda law,representation:representation in records and len(set(records[representation]))==1}
    counterexample=values(doc,model,('history','first','second','law','left','right'))[0]
    if counterexample:raise ValueError('Rest was confused with law invariance')
    return {'cases':rows,'coordinate_rest_preserved':counterexample,
        'scope':'Finite algebraic examples x_new(t)=x(t)-v*t+offset at three integer times; no relativistic transformation or physical law derived.'}


def source_document(query):
    return candidate(source_composed()[0],query)


DOMAIN=('first','second','third','system','historyone','historytwo','leftone','lefttwo','rightone','righttwo','extra','lawone','lawtwo')


def source_model(doc,facts):
    def forbidden(*args):raise ValueError('Unrelated physical content unexpectedly evaluated')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    model.update(ra=lambda:'first',rc=lambda:'second',ri=lambda:'text',
        va=lambda frame:frame in facts['frames'],vb=lambda a,b,c:(a,b,c) in facts['orientation'],
        vc=lambda a,b,c:(a,b,c) in facts['velocity'],vd=lambda law,context:context=='text' and law in facts['laws'],
        ve=lambda history,context:context=='text' and history in facts['histories'],
        vf=lambda *args:args in facts['systems'],vg=lambda system:system=='system',
        vh=lambda *args:args in facts['representations'],vi=lambda *args:args in facts['allowed'],
        vj=lambda first,second,context:(first,second,context) in facts['complete'])
    return model


def base_facts():
    pairs={('first','second','text'),('second','first','text')}
    return {'frames':{'first','second'},'orientation':pairs.copy(),'velocity':pairs.copy(),
        'laws':{'lawone','lawtwo'},'histories':{'historyone','historytwo'},
        'systems':{('historyone','system','text'),('historytwo','system','text')},
        'representations':{('historyone','first','leftone','text'),('historyone','second','rightone','text'),
            ('historytwo','first','lefttwo','text'),('historytwo','second','righttwo','text')},
        'allowed':{('lawone','leftone','text'),('lawone','rightone','text'),
            ('lawtwo','lefttwo','text'),('lawtwo','righttwo','text')},'complete':pairs.copy()}


def frame_checks():
    doc=source_document('q[k sat[k ra[] k rc[] k ri[]]].')
    rows={}
    for name in ('baseline','rotating','accelerating','first_not_frame','second_not_frame','same_frame','wrong_context'):
        facts=base_facts();model=source_model(doc,facts)
        if name=='rotating':facts['orientation']=set()
        if name=='accelerating':facts['velocity']=set()
        if name=='first_not_frame':facts['frames'].remove('first')
        if name=='second_not_frame':facts['frames'].remove('second')
        if name=='same_frame':model['rc']=lambda:'first'
        if name=='wrong_context':facts['velocity']={('first','second','other')}
        actual=values(doc,model,DOMAIN)[0]
        if actual!=(name=='baseline'):raise ValueError('Eligible coordinate frames differ: '+name)
        rows[name]=actual
    return rows


def source_checks():
    doc=source_document('q[k sav[k ra[] k rc[] k ri[]]].')
    base=base_facts()
    cases={'baseline':(base,True)}
    for name,key,value in (
        ('empty_laws','laws',set()),('empty_histories','histories',set()),('incomplete_scope','complete',set()),
        ('missing_physical_systems','systems',set()),('missing_representations','representations',set())):
        changed=deepcopy(base);changed[key]=value;cases[name]=(changed,False)
    for name,key,item in (
        ('one_unbound_history','systems',('historytwo','system','text')),
        ('missing_right_representation','representations',('historytwo','second','righttwo','text')),
        ('law_not_preserved','allowed',('lawone','rightone','text')),
        ('second_law_not_preserved','allowed',('lawtwo','righttwo','text'))):
        changed=deepcopy(base);changed[key].remove(item);cases[name]=(changed,False)
    changed=deepcopy(base)
    changed['representations'].remove(('historytwo','second','righttwo','text'))
    changed['representations'].add(('historyone','second','righttwo','text'))
    cases['different_history_cannot_fill_missing_representation']=(changed,False)
    changed=deepcopy(base);changed['representations'].add(('historyone','second','extra','text'))
    cases['inconsistent_alternative_representation']=(changed,False)
    changed=deepcopy(base);changed['allowed']={('lawone',r,'text') for r in ('leftone','rightone','lefttwo','righttwo')}
    cases['one_law_allows_and_another_rejects_all_candidates']=(changed,True)
    # A candidate rejected in both frames remains part of the comparison.
    changed=deepcopy(base);changed['allowed'].add(('lawone','righttwo','text'))
    cases['unobserved_candidate_disagrees']=(changed,False)
    changed=deepcopy(base);changed['representations']={(h,f,r,'other') for h,f,r,c in changed['representations']}
    cases['foreign_context_representations']=(changed,False)
    changed=deepcopy(base);changed['histories'].add('extra')
    cases['invalid_selected_candidate_not_silently_excluded']=(changed,False)
    rows={}
    for name,(facts,expected) in cases.items():
        actual=values(doc,source_model(doc,facts),DOMAIN)[0]
        if actual!=expected:raise ValueError('Source law scope differs: '+name)
        rows[name]=actual
    return rows


def full_principle_checks():
    doc=source_document('q[t[k saw[]][k ri[]]].')
    rows={}
    for name in ('baseline','one_direction_incomplete','no_frame_pair','unpreserved_law'):
        facts=base_facts()
        # Exercise the complete quantified expression on a small, fully specified
        # model. Multi-law/multi-history comparisons are exercised separately.
        facts['laws']={'lawone'}
        facts['histories']={'historyone'}
        facts['systems']={('historyone','system','text')}
        facts['representations']={row for row in facts['representations'] if row[0]=='historyone'}
        facts['allowed']={row for row in facts['allowed'] if row[0]=='lawone'}
        if name=='one_direction_incomplete':facts['complete'].remove(('second','first','text'))
        if name=='no_frame_pair':facts['velocity']=set()
        if name=='unpreserved_law':facts['allowed'].remove(('lawone','rightone','text'))
        actual=values(doc,source_model(doc,facts),('first','second','system','historyone','leftone','rightone','lawone'))[0]
        if actual!=(name=='baseline'):raise ValueError('Full principle scope differs: '+name)
        rows[name]=actual
    return {'cases':rows,'physical_laws_are_supplied_finite_relations':True,
        'individual_domain_size':7,'selected_laws':1,'selected_histories':1,
        'arbitrary_physical_systems_verified':False}


def attribution_checks():
    doc=parse(source_composed()[0])
    previous=parse((ROOT/'examples/v014/einstein-roundtrip-speed.noema').read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=previous['statements']:raise ValueError('Earlier assertions changed')
    doc['statements']=doc['statements'][-1:]
    rows={}
    for index in range(-1,5):
        def forbidden(*args):raise ValueError('Principle truth unexpectedly evaluated during attribution')
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(vk=lambda:'node',rd=lambda:'author',rh=lambda:'scope',ri=lambda:'text')
        expected=['node','author','saw','scope','text']
        if index>=0:expected[index]='other'
        model['vl']=lambda node,author,content,scope,context:[node,author,json.loads(content.syntax)['symbol'],scope,context]==expected
        actual=values(doc,model,('node','author','scope','other'))[0]
        if actual!=(index==-1):raise ValueError('Principle definition attribution differs')
        rows['baseline' if index==-1 else 'wrong_'+('node','author','content','scope','context')[index]]=actual
    return rows


def alignment():
    units=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']=='einstein-1905:u0025')
    digest=hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest!='24af8194907783e0add320014cc8701e652888e3951df01824d9111f526f704e':raise ValueError('Relativity source changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),
        'source':unit['text'],'definitions':['sap','saq','sar','sat','sau','sav','saw'],
        'status':'partial_explicit_reading','full_semantic_equivalence':False,
        'remaining':['meaning of law identity and full candidate domains','physical grounding of states and uniform translation',
                     'definition and premise discourse across both principles','facsimile review']}], 'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored invariance differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Law roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    files=[*documents,'data/law-invariance-basis-v1.json','data/einstein-law-invariance-basis-v1.json',
        'examples/v014/einstein-roundtrip-speed.noema','scripts/compose_law_invariance.py','scripts/check_law_invariance.py',
        'noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_law_preservation_under_coordinate_representations','documents':documents,
        'representations':representation_checks(),'coordinate_examples':coordinate_examples(),
        'frames':frame_checks(),'source_scope':source_checks(),'full_principle':full_principle_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Law invariance report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Law preservation, coordinate differences, source scope and definition attribution checked')


if __name__=='__main__':main()
