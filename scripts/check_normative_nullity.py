"""Check all-position nullity, source identity and hypothetical confirmation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_normative_nullity import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_normative_nullity_evidence import RECORD as EVIDENCE,validate

REPORT='reports/normative-nullity-v1.json'
DOC='docs/normative-nullity-v1.md'
READING='data/normative-nullity-reading-v1.json'
PRIORS=('reports/covenant-question-v1.json','reports/ratified-norms-v1.json')
DOMAIN=('contract','other','assessor','holder','role','first','second','third','authority','authorityb','community')
SCENES=('reference','candidate','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r zchoose[a d i d[e] i d[e] i d[e]] i d[e].r zcandidates[d d] c.r zauthorities[a] c.r zconfirms[a a d] c.'
EXTRA+='r zright[a a d] c.d zact[bindings j[a]] e[b point[e[v point][v point]]].'
for n,relation in (('zneed','h7k'),('zpermit','h7l')):
    EXTRA+='d '+n+'[] e[b point[k '+relation+'[k zcontract[] k zholder[] k zrole[] r[p zact] l[a][k zholder[]] e[v point][v point] v point]]].'
EXTRA+='d zadditional[] e[b point[k zright[k zholder[] k zrole[] v point]]].'
PROVIDER='d h256k[position a reference d] i d[e][k zchoose[v position v reference r d[k zneed[]] r d[k zpermit[]] r d[k zadditional[]]]].'
ARGS='k zcontract[] k zassessor[] k ztreference[]'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query):
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,roots),statements=[])
    prefix=deepcopy(parent().document);prefix.update(declarations=closure(prefix,['h7k','h7l']),statements=[])
    provider=parse(format_graph(prefix,'compact')+EXTRA+PROVIDER)
    provided={d['name'] for d in provider['declarations']}
    doc['declarations']=provider['declarations']+[d for d in doc['declarations'] if d['name'] not in provided]
    return parse(format_graph(doc,'compact')+query)

def model(doc,grounded=(),variant='baseline',scope=('first','second','third')):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    def choose(position,reference,first,second,third):
        codes=dict(first=first,second=second,third=third)
        if variant=='swapped':codes['first'],codes['third']=codes['third'],codes['first']
        return codes.get(position,first)
    v['zchoose']=choose
    v['h256j']=lambda position,assessor,reference:position in scope and (assessor,reference)==('assessor','reference')
    def ground(assessor,source,code,reference,point):
        expected=['assessor','contract','reference']
        changes={'other_assessor':(0,'other'),'external_source':(1,'other'),'other_reference':(2,'other')}
        if variant in changes:
            i,value=changes[variant];expected[i]=value
        assert code.rank==3
        return (assessor,source,reference)==tuple(expected) and (symbol(code),point) in grounded
    v['h256l']=ground
    v.update(h255o=lambda:'reference',h255r=lambda:'community',h255p=lambda c,r:'assessor' if (c,r)==('community','reference') else 'other')
    return v

def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)

@lru_cache(None)
def consequence_checks():
    doc=fixture(('r475',),'q[t[k r475['+ARGS+']][k ztreference[]]].');rows={}
    names=('zneed','zpermit','zadditional')
    for bits in product((False,True),repeat=3):
        grounded={(n,'reference') for n,on in zip(names,bits) if on};v=model(doc,grounded)
        actual=run(doc,v);assert actual==[not any(bits)],(bits,actual);rows[str(bits)]=actual[0]
        assert all(v[n] is unknown for n in ('h7k','h7l','zright'))
    for variant in ('external_source','other_assessor','other_reference'):
        actual=run(doc,model(doc,{('zadditional','reference')},variant));assert actual==[True];rows[variant]=actual[0]
    assert run(doc,model(doc,{('zadditional','candidate')}))==[True]
    # An additional, non-duty/non-permission consequence also refutes nullity.
    assert run(doc,model(doc,{('zadditional','reference')}))==[False]
    # A finite restricted fixture illustrates why actual scope completeness is required.
    assert run(doc,model(doc,{('zadditional','reference')},scope=('first','second')))==[True]
    local=fixture(('r474',),'q[k r474[k zcontract[] k zassessor[] k zfirst[] k ztreference[] k ztreference[]]].')
    assert run(local,model(local,{('zadditional','reference')}))==[True]
    assert run(local,model(local,{('zadditional','reference')},'swapped'))==[False]
    for name in ('h256j','zchoose','h256l'):
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(all_three_independent_consequence_cases=rows,native_universal_quantification=True,
        missing_scope_member_can_change_answer_and_is_not_certified_complete=True,
        same_item_content_mapping_required=True,other_source_and_other_point_not_erased=True,
        quoted_norms_not_executed=True,unknown_rejected=True,
        model_scope='Two concrete h7k/h7l contents and a third independent normative-status content; no claim that three exhaust actual normative consequences')

@lru_cache(None)
def confirmation_checks():
    query='q[t[k r476['+ARGS+' p zcandidates p zauthorities p zconfirms]][k ztreference[]]].'
    doc=fixture(('r476',),query);count=0
    for grounded_bits in product((False,True),repeat=3):
        grounded={('zadditional',s) for s,on in zip(SCENES,grounded_bits) if on}
        for confirms in product((False,True),repeat=4):
            v=model(doc,grounded)
            v['zcandidates']=lambda ref,point:ref=='reference' and point in ('candidate','other')
            v['zauthorities']=lambda a:a in ('authority','authorityb')
            records={(a,p) for (a,p),on in zip(product(('authority','authorityb'),('candidate','other')),confirms) if on}
            v['zconfirms']=lambda authority,source,point:source=='contract' and (authority,point) in records
            expected=not grounded_bits[0] and all(not all((a,p) in records for a in ('authority','authorityb')) or not bit
                for p,bit in zip(SCENES[1:],grounded_bits[1:]))
            actual=run(doc,v);assert actual==[expected],(grounded_bits,confirms,actual,expected);count+=1
    contrasts={}
    for variant in ('baseline','no_authority','no_candidates','wrong_confirmed_source','moving_reference'):
        v=model(doc,{('zadditional','candidate')})
        v['zcandidates']=lambda ref,p:variant!='no_candidates' and ref==('candidate' if variant=='moving_reference' else 'reference') and p=='candidate'
        v['zauthorities']=lambda a:variant!='no_authority' and a=='authority'
        v['zconfirms']=lambda a,source,p:(a,source,p)==('authority','other' if variant=='wrong_confirmed_source' else 'contract','candidate')
        actual=run(doc,v);assert actual==[variant!='baseline'],(variant,actual);contrasts[variant]=actual[0]
    return dict(native_three_point_grounding_and_two_authority_cases=count,contrasts=contrasts,
        actual_absence_required_even_without_confirmation=True,confirmation_not_asserted_actual=True,
        empty_authorities_not_confirmed=True,candidates_fixed_at_reference=True)

@lru_cache(None)
def reference_checks():
    doc=fixture(('r477',),'q[t[k r477[k zcontract[]]][k ztreference[]]].');rows={}
    for variant in ('baseline','external_source','other_assessor','other_reference'):
        actual=run(doc,model(doc,{('zadditional','reference')},variant));assert actual==[variant!='baseline'];rows[variant]=actual[0]
    return dict(supplied_sixth_paragraph_assessor_and_reference=rows)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='normative_nullity_and_hypothetical_confirmation_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[444,712],text=unit['text'][444:712]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],lexical_evidence=EVIDENCE,
        adopted_reading=LIMITS,
        remaining=['同種の合意へのsolcherと全人類の今後の啓蒙を永久に妨げる共同目的','同じ合意の仮定的な形成',
            '最高権力・帝国議会・最も厳粛な和平締結による承認の種類とその参照','schlechterdingsとsollte auchの無留保・譲歩の提示','全文への著者帰属と通読判断'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    validate(read(EVIDENCE));assert read(READING)==reading_record()
    p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==98
    return dict(preserved_manuscript_statements=98,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        unchanged_imports=True,roundtrips=True,no_new_whole_sentence_judgment=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in [('consequences',consequence_checks),('confirmation',confirmation_checks),('references',reference_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,EVIDENCE,*PRIORS,read(READING)['source_inventory'],
        read(READING)['primary_page']['path'],read(EVIDENCE)['path'],'scripts/compose_normative_nullity.py',
        'scripts/check_normative_nullity.py','scripts/fetch_normative_nullity_evidence.py','tests/test_normative_nullity.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='normative_nullity_and_hypothetical_confirmation_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
