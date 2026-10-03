"""Check current-position clock agreement without declaring carried clocks at rest."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_comparison import callbacks, guarded
from scripts.check_rod_measurements import ARITHMETIC, cut, fingerprint
from scripts.compose_carried_clocks import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/carried-clocks-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('motion','text','other'),
        primitives=model,max_steps=2_000_000,memoize_definitions=True,memoize_expressions=True)]


def point_checks():
    doc=parse(generic_composed()[0]+'''
r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] a.r jf[] d.r jg[] h[b] c.
r jh[a] c.r ji[a] c.r jj[a a a a d] c.r jk[a a a a h[b] c] c.
r jl[h[b] c] c.r jm[h[b] c h[b] c] c.
q[k scu[k jg[] k jg[] i[value h[b] c][k sct[k ja[] k jb[] k jc[] k jd[] k je[] v value k jf[] p jh p ji p jj p jk]] p jl p jm]].''')
    rows=[]
    for bits in product((False,True),repeat=6):
        clock,unit,located,read,localread,same=bits
        model={**ARITHMETIC,'ja':lambda:'event','jb':lambda:'carried','jc':lambda:'place','jd':lambda:'frame','je':lambda:'unit','jf':lambda:'motion','jg':lambda:cut(5),
            'jh':lambda c:clock and c=='carried','ji':lambda u:unit and u=='unit',
            'jj':lambda *args:located and args==('carried','event','place','frame','motion'),
            'jk':lambda c,e,f,u,v:read and (c,e,f,u)==('carried','event','frame','unit') and fingerprint(v)==fingerprint(cut(5)),
            'jl':lambda v:localread and fingerprint(v)==fingerprint(cut(5)),
            'jm':lambda a,b:same and fingerprint(a)==fingerprint(b)}
        actual=values(doc,model,('event','carried','place','frame','unit'))[0]
        if actual!=all(bits):raise ValueError('Current-position reading or comparison differs')
        rows.append({'conditions':list(bits),'accepted':actual})
    return rows


def source_checks():
    doc=candidate(source_composed()[0],'''r ja[] d.r jb[] h[a a a a d] c.
r jc[] h[h[b] c h[b] c] c.r jd[] h[h[b] c] c.
q[k scz[k ja[] k jb[] k jc[] k jd[]]].''')
    domain=('rod','otherrod','carrieda','carriedb','enda','endb','r1','r2','r3','r4','e1','e2','e3','e4',
        'p1','p2','p3','p4','l1','l2','l3','l4','reference','frame','unit','other')
    records={'r1':('carrieda','enda','e1','p1','l1',3),'r2':('carrieda','enda','e2','p2','l2',5),
        'r3':('carriedb','endb','e3','p3','l3',3),'r4':('carriedb','endb','e4','p4','l4',5)}
    base={'context':'motion','frame':'frame','unit':'unit','reference':'reference','secondclock':'carriedb','secondend':'endb',
        'selected':{(r,row[0],'motion') for r,row in records.items()},'complete':{'carrieda','carriedb'},
        'attachments':{('carrieda','enda','rod','motion'),('carriedb','endb','rod','motion')},
        'moving':{('rod','frame','motion'),('carrieda','frame','motion'),('carriedb','frame','motion')},
        'stationary':{'l1','l2','l3','l4','reference'},'synced':{'l1','l2','l3','l4'},
        'ownvalues':{r:row[5] for r,row in records.items()},'localvalues':{r:row[5] for r,row in records.items()},
        'reportedown':{},'reportedlocal':{},'events':{},'places':{},'localclocks':{},
        'omit_current':set(),'omit_endpoint':set(),'omit_local_location':set(),'invalid':False}
    cases={'moving_clocks_change_locations_and_local_comparators':(base,True)}
    changed=deepcopy(base)
    changed['ownvalues'].update(r3=6,r4=8);changed['localvalues'].update(r3=6,r4=8)
    cases['two_ends_need_not_have_simultaneous_records']=(changed,True)
    for name,field,item in (
        ('second_clock_missing_late_record','selected',('r4','carriedb','motion')),
        ('incomplete_record_scope','complete','carriedb'),
        ('clock_not_attached','attachments',('carriedb','endb','rod','motion')),
        ('motion_missing','moving',('carrieda','frame','motion')),
        ('local_clock_moving','stationary','l2'),('reference_not_stationary','stationary','reference'),
        ('later_local_clock_unsynchronized','synced','l4'),
    ):
        changed=deepcopy(base);changed[field].remove(item)
        if name=='second_clock_missing_late_record':
            # A smaller selection alone cannot prove that the scope is complete.
            changed['complete'].remove('carriedb')
        cases[name]=(changed,False)
    for name,field,value in (
        ('wrong_context','context','other'),('wrong_frame','frame','other'),('wrong_unit','unit','other'),
        ('wrong_reference','reference','other'),('reference_is_carried_clock','reference','carrieda'),
        ('same_clock_at_both_ends','secondclock','carrieda'),('same_endpoint_twice','secondend','enda'),
        ('invalid_reading','invalid',True),
    ):
        changed=deepcopy(base);changed[field]=value;cases[name]=(changed,False)
    for name,field,record,value in (
        ('later_carried_clock_drifts','ownvalues','r2',6),
        ('wrong_reported_carried_read','reportedown','r2',6),
        ('wrong_reported_local_read','reportedlocal','r2',6),
        ('different_event','events','r2','e1'),('different_current_place','places','r2','p1'),
        ('old_local_clock_at_new_position','localclocks','r2','l1'),('local_is_carried_clock','localclocks','r2','carrieda'),
    ):
        changed=deepcopy(base);changed[field][record]=value;cases[name]=(changed,False)
    for name,field in (('missing_current_clock_position','omit_current'),('missing_current_endpoint_position','omit_endpoint'),('missing_local_clock_position','omit_local_location')):
        changed=deepcopy(base);changed[field].add('r2');cases[name]=(changed,False)
    changed=deepcopy(base);changed['selected']={x for x in changed['selected'] if x[1]!='carriedb'}
    cases['one_clock_has_no_records']=(changed,False)
    changed=deepcopy(base);changed['attachments']={('carrieda','enda','otherrod','motion'),('carriedb','endb','otherrod','motion')}
    cases['clocks_on_a_different_rod']=(changed,False)
    rows={}
    for name,(facts,expected) in cases.items():
        model=guarded(doc)
        model.update(ja=lambda:facts['context'],ra=lambda:facts['frame'],rb=lambda:facts['unit'],rc=lambda:facts['reference'],
            xi=lambda:'rod',xn=lambda:'enda',xo=lambda:facts['secondend'],zaj=lambda:'carrieda',zak=lambda:facts['secondclock'],
            xa=lambda rod:rod=='rod',ca=lambda clock:clock in ('carrieda','carriedb','l1','l2','l3','l4','reference'),
            ci=lambda unit:unit=='unit',cc=lambda clock,frame:clock in facts['stationary'] and frame=='frame',
            xm=lambda *args:args in facts['moving'],zaa=lambda *args:args in facts['attachments'],
            xf=lambda endpoint,rod,frame,ctx:endpoint in ('enda','endb') and (rod,frame,ctx)==('rod','frame','motion'),
            zai=lambda clock,frame,ctx:clock in facts['complete'] and (frame,ctx)==('frame','motion'),zac=lambda *args:args in facts['selected'])
        def row(record):return records.get(record,records['r1'])
        model.update(zad=lambda r:facts['events'].get(r,row(r)[2]),zae=lambda r:facts['places'].get(r,row(r)[3]),
            zaf=lambda r:facts['localclocks'].get(r,row(r)[4]),
            zag=lambda r:cut(facts['reportedown'].get(r,facts['ownvalues'].get(r,3))),
            zah=lambda r:cut(facts['reportedlocal'].get(r,facts['localvalues'].get(r,3))))
        model['zab']=lambda clock,event,place,frame,ctx:(frame,ctx)==('frame','motion') and any(
            (clock,event,place)==(r[0],r[2],r[3]) for key,r in records.items() if key not in facts['omit_current'])
        model['xg']=lambda endpoint,event,place,frame,ctx:(frame,ctx)==('frame','motion') and any(
            (endpoint,event,place)==(r[1],r[2],r[3]) for key,r in records.items() if key not in facts['omit_endpoint'])
        def located(obj,place,frame):
            return frame=='frame' and any((obj,place)==(r[2],r[3]) or
                key not in facts['omit_local_location'] and (obj,place)==(r[4],r[3]) for key,r in records.items())
        def reading(clock,event,frame,unit,value):
            if (frame,unit)!=('frame','unit'):return False
            return any(event==r[2] and (clock==r[0] and fingerprint(value)==fingerprint(cut(facts['ownvalues'][key])) or
                clock==r[4] and fingerprint(value)==fingerprint(cut(facts['localvalues'][key]))) for key,r in records.items())
        model.update(cb=located,ce=reading)
        callbacks(doc,model,{
            'jb':lambda clock,reference,frame,unit,ctx:clock in facts['synced'] and (reference,frame,unit,ctx)==('reference','frame','unit','motion'),
            'jc':lambda first,second:fingerprint(first)==fingerprint(second),
            'jd':lambda value:not facts['invalid']})
        actual=values(doc,model,domain)[0]
        if actual!=expected:raise ValueError('Carried clock/local time relation differs: '+name)
        rows[name]=actual
    return {'cases':rows,'carried_clocks_in_stationary_clock_set':False,
        'finite_records_per_clock':2,'real_cut_validity_equality_and_static_synchrony_supplied':True,
        'all_continuous_time_readings_verified':False,'natural_unadjusted_clock_rate_law_asserted':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:]
    rows={}
    for name in ('baseline','missing_extension','wrong_prior_setting','wrong_qualification','wrong_frame','wrong_author','wrong_scope'):
        model=guarded(doc)
        for key,value in {'zal':'addition','zam':'term','y2':'rodsetting','rd':'author','ra':'frame','xy':'scope','ri':'text'}.items():
            model[key]=lambda value=value:value
        def common(author,scope,ctx):return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','text')
        model['ug']=lambda node,author,desc,scope,ctx:node=='addition' and common(author,scope,ctx) and json.loads(desc.syntax)['symbol']=='scy'
        model['zao']=lambda prior,added,scope,ctx:name!='missing_extension' and (prior,added,scope,ctx)==(
            'other' if name=='wrong_prior_setting' else 'rodsetting','addition','scope','text')
        model['zan']=lambda node,author,desc,frame,scope,ctx:node=='term' and common(author,scope,ctx) and json.loads(desc.syntax)['symbol']==(
            'qo' if name=='wrong_qualification' else 'scx') and frame==('other' if name=='wrong_frame' else 'frame')
        actual=values(doc,model,('addition','term','rodsetting','author','frame','scope','other'))
        expected=[name not in ('missing_extension','wrong_prior_setting','wrong_author','wrong_scope'),
            name not in ('wrong_qualification','wrong_frame','wrong_author','wrong_scope')]
        if actual!=expected:raise ValueError('Additional setup/qualified synchrony attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0035')
    digest='cc5a3d6043a41c08fa530f70227996143ca1cebdde60f8cd931da0a7b8b2981b'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Carried clocks source changed')
    rows=[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sct','scv','scw','scx','scy','scz'],'status':'partial_explicit_reading','full_semantic_equivalence':False}]
    for math_id,expected in (
        ('M0052','54d50fafeb332857187f47519e3fc74b679b89c2e3e779038dc2f566127bc4ff'),
        ('M0053','22fdbca6cc3ccac3e6770e48b1a02c0b0895a7186c326abbd29d5f489f3f2843'),
    ):
        math=next(m for m in artifact['math'] if m['id']==math_id)
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=expected:raise ValueError('Endpoint label changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':math_id,'math_sha256':expected,
            'definitions':['scv','scz'],'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored carried-clock draft differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Carried-clock roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/carried-clocks-basis-v1.json','data/einstein-carried-clocks-basis-v1.json',
        'examples/v014/einstein-geometric-replacement.noema','scripts/compose_carried_clocks.py','scripts/check_carried_clocks.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-geometric-replacement.noema').read_text(encoding='utf-8')
    return {'status':'partial_carried_clock_agreement_with_current_local_rest_time','documents':documents,
        'point_readings':point_checks(),'source_adapter':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Carried-clock report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Carried/current-place readings, local static synchronization and setup attributions checked')


if __name__=='__main__':main()
