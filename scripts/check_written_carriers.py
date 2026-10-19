"""Check work/record/carrier bindings, multiplicity and source composition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_written_carriers import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,parent,build,closure
from scripts.check_role_qualifications import evaluate,source_values as role_values
from scripts.check_substituted_judgment import SOURCE_PEOPLE,SOURCE_SCENES
from scripts.check_motive_causes import unknown,symbol
from scripts.check_designation_order import substantive

INDEX='data/semantic-review-index-v46.json'
REPORT='reports/written-carriers-v1.json'
AUDIT='data/written-carriers-reading-v1.json'
DOC='docs/written-carriers-v1.md'
PEOPLE=(*SOURCE_PEOPLE,'roleA','roleB','recordA','recordB','paperA','paperB')

def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jw[] a.r jm[] a.r js[] d.
r jr[a a d] c.r jc[a a d] c.r ja[a d] c.
q[k rqxk[k jw[] k jm[] k js[] p jr p jc p ja]].''')
    people=('workA','workB','mediumA','mediumB','recordA','recordB');scenes=('now','other');rows=[]
    for bits in product((False,True),repeat=6):
        encoded={r for r,b in zip(('recordA','recordB'),bits[:2]) if b}
        carried={r for r,b in zip(('recordA','recordB'),bits[2:4]) if b}
        readable={r for r,b in zip(('recordA','recordB'),bits[4:]) if b}
        v=dict(jw=lambda:'workA',jm=lambda:'mediumA',js=lambda:'now',
            jr=lambda r,w,s:r in encoded and (w,s)==('workA','now'),
            jc=lambda r,m,s:r in carried and (m,s)==('mediumA','now'),
            ja=lambda r,s:r in readable and s=='now')
        actual=evaluate(doc,v,people,scenes)[0]
        assert actual==bool(encoded&carried&readable)
        rows.append(dict(bits=list(bits),value=actual))
    contrasts={}
    for variant in ('baseline','other_work','other_medium','split_record','other_readable_record',
        'other_encoding_time','other_carrier_time','other_reading_time'):
        v=dict(jw=lambda:'workA',jm=lambda:'mediumA',js=lambda:'now',
            jr=lambda r,w,s:(r,w,s)==('recordA','workB' if variant=='other_work' else 'workA',
                'other' if variant=='other_encoding_time' else 'now'),
            jc=lambda r,m,s:(r,m,s)==('recordB' if variant=='split_record' else 'recordA',
                'mediumB' if variant=='other_medium' else 'mediumA','other' if variant=='other_carrier_time' else 'now'),
            ja=lambda r,s:(r,s)==('recordB' if variant=='other_readable_record' else 'recordA',
                'other' if variant=='other_reading_time' else 'now'))
        contrasts[variant]=evaluate(doc,v,people,scenes)[0]
        assert contrasts[variant]==(variant=='baseline')
    return dict(record_combinations=rows,binding_contrasts=contrasts)

def multiplicity_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jwa[] a.r jwb[] a.r jma[] a.r jmb[] a.r js[] d.
r jr[a a d] c.r jc[a a d] c.r ja[a d] c.
q[k rqxk[k jwa[] k jma[] k js[] p jr p jc p ja]].
q[k rqxk[k jwa[] k jmb[] k js[] p jr p jc p ja]].
q[k rqxk[k jwb[] k jma[] k js[] p jr p jc p ja]].
q[e[k jwa[]][k jma[]]].q[e[k jwa[]][k jwb[]]].''')
    people=('workA','workB','mediumA','mediumB','recordA','recordB','recordC');rows={}
    for variant in ('two_copies','two_works_same_carrier','one_copy_unreadable'):
        representations={('recordA','workA'),('recordB','workA'),('recordC','workB')}
        carriers={('recordA','mediumA'),('recordB','mediumB')}
        if variant=='two_works_same_carrier':carriers.add(('recordC','mediumA'))
        readable={'recordA','recordB','recordC'}-({'recordA'} if variant=='one_copy_unreadable' else set())
        v=dict(jwa=lambda:'workA',jwb=lambda:'workB',jma=lambda:'mediumA',jmb=lambda:'mediumB',js=lambda:'now',
            jr=lambda r,w,s:(r,w) in representations and s=='now',
            jc=lambda r,m,s:(r,m) in carriers and s=='now',ja=lambda r,s:r in readable and s=='now')
        rows[variant]=evaluate(doc,v,people,('now',))
        assert rows[variant]==[variant!='one_copy_unreadable',True,variant=='two_works_same_carrier',False,False]
    return dict(cases=rows,work_not_identified_with_copy=True,shared_carrier_does_not_identify_works=True)

@lru_cache(None)
def source_doc(previous=False):
    c=parent() if previous else load_catalog(ROOT,BASIS);d=deepcopy(c.document)
    d.update(declarations=closure(d,['sd','sl','ss','sv','re','s2','sy','wh']),statements=[])
    return parse(format_graph(d,'compact')+'''r jperson[] a.r jbook[] a.r jscene[] d.
q[k sd[k jbook[] k jscene[]]].q[k sl[k jbook[] k jscene[]]].
q[t[k ss[k jperson[]]][k jscene[]]].q[t[k sv[k jperson[]]][k jscene[]]].
q[k re[k jperson[] p sv i[scene d][k s2[k jperson[] k wh[] v scene]]]].
q[t[k sy[k jperson[]]][k wh[]]].''')

def source_values(variant):
    v=role_values(variant);v.update(jperson=lambda:'person',jbook=lambda:'book',jscene=lambda:'case')
    encoded={('recordA','book','case')};carried={('recordA','paperA','case')};readable={('recordA','case')}
    if variant=='no_record':encoded=set()
    if variant=='wrong_work':encoded={('recordA','other','case')}
    if variant in ('no_carrier','destroyed_copy'):carried=set()
    if variant=='unreadable':readable=set()
    if variant=='split_record':carried={('recordB','paperA','case')}
    if variant=='wrong_readable_record':readable={('recordB','case')}
    if variant=='other_encoding_time':encoded={('recordA','book','text')}
    if variant=='other_carrier_time':carried={('recordA','paperA','text')}
    if variant=='other_reading_time':readable={('recordA','text')}
    if variant in ('second_copy','two_copies'):
        encoded.add(('recordB','book','case'));carried.add(('recordB','paperB','case'));readable.add(('recordB','case'))
        if variant=='second_copy':readable.remove(('recordA','case'))
    if variant=='no_reader_access':
        access=v['sa'];v['sa']=lambda p,w,s:access(p,w,s) and w!='book'
    if variant=='not_a_written_work':v['sc']=lambda *args:False
    v.update(hzwr=lambda r,w,s:(r,w,s) in encoded,hzws=lambda r,m,s:(r,m,s) in carried,
        hzwt=lambda r,s:(r,s) in readable)
    # Interpret the former high-level predicate from independent relation sets.
    # This comparison does not treat an arbitrary old sd=True as a counterexample.
    v['sd']=lambda w,s:any((r,w,s) in encoded and (r,m,s) in carried and (r,s) in readable
        for r in PEOPLE for m in PEOPLE)
    return v

def source_checks():
    absent=('no_record','wrong_work','no_carrier','destroyed_copy','unreadable','split_record',
        'wrong_readable_record','other_encoding_time','other_carrier_time','other_reading_time')
    variants=('baseline',*absent,'second_copy','two_copies','no_reader_access','not_a_written_work','wrong_beneficiary','failed_goal')
    rows={}
    for variant in variants:
        v=source_values(variant);new=evaluate(source_doc(),v,PEOPLE,SOURCE_SCENES)
        old=evaluate(source_doc(True),v,PEOPLE,SOURCE_SCENES)
        external=variant not in absent;book=external and variant!='not_a_written_work'
        supplied=book and variant not in ('no_reader_access','wrong_beneficiary')
        expected=[external,book,supplied,supplied,supplied,not supplied or variant!='failed_goal']
        assert new==old==expected,(variant,new,old,expected)
        rows[variant]=new
    for n in PRIMITIVES:
        v=source_values('baseline');v[n]=unknown
        try:evaluate(source_doc(),v,PEOPLE,SOURCE_SCENES)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(contrasts=rows,former_predicate_interpreted_from_reference_relation_sets=True,
        definitions_replaced_by_primitives=False,task_content_not_executed=True,unknown_inputs_refused=3)

def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_node','other_description','other_context','reverse_order','reverse_examples','closed_list'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(s3=lambda:'examples',mw=lambda:'cause',wa=lambda:'author',wh=lambda:'text',
            s4=lambda n,a,t,s:(n,a,symbol(t),s)==('other' if variant=='other_node' else 'examples',
                'other' if variant=='other_author' else 'author','sv' if variant=='other_description' else 'sy',
                'other' if variant=='other_context' else 'text'),
            s5=lambda n,a,ds,s:variant!='closed_list' and (n,a,s)==('examples','author','text') and
                [symbol(x) for x in ds.items]==(['su','st','ss'] if variant=='reverse_examples' else ['ss','st','su']),
            ue=lambda a,b,s:(a,b,s)==(('examples','cause','text') if variant=='reverse_order' else ('cause','examples','text')))
        rows[variant]=evaluate(doc,v,('examples','cause','author','other'),('text',))
        assert rows[variant]==[variant=='baseline']
    return dict(contrasts=rows,all_work_record_and_carrier_facts_unknown=True)

def structure():
    old,new=parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)==set(PRIMITIVES)|{'rqxk'}
    assert [n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]==['sd']
    assert old.entries['sd']['kind']=='primitive' and new.entries['sd']['kind']=='definition'
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n not in MEANINGS)
    affected=[i for i,s in enumerate(new.document['statements']) if 'sd' in {d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[4]
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a==r['selection'] and a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2,3],[5]):
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            s=format_graph(d,style);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=42,changed_declarations=['sd'],changed_meanings=['sd','sl'],affected_statements=affected,
        added_definitions=2,added_primitives=3,removed_primitives=['sd'],net_added_primitives=2,preserved_review_meanings=11,
        first_cause_sentence_meanings_unchanged=True,payment_meanings_unchanged=True,roundtrips=True)

def audit():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='ein Buch, das für mich Verstand hat';start=unit['text'].index(phrase)
    paths=(PARENT,PARENT_BASIS,INDEX,inv,'artifacts/first-cause-reading-v1/page-482.jpg','docs/substituted-judgment-v1.md')
    return dict(status='partial_written_work_carrier_explanation',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        reading='書物を、記された作品が外部媒体上の記録から参照でき、その内容を本人が利用するものとして部分的に説明する。',
        decisions=['sdを三つの関係から定義し、作品・記録・媒体・状況を共有する。',
            '複数の写しや、一媒体上の複数作品を許し、作品と媒体の同一性や媒体の一意性は加えない。',
            '個人の利用可能性はsaで別に述べ、読解・理解・賛同を媒体の存在から補わない。'],
        remaining=['書物を他の記された作品から区別する全条件','作品・版・記号表現の基礎説明',
            '宗教上の助言者・良心、第二段落全体','二作品全文'],
        whole_unit_semantically_verified=False,full_noun_equivalence=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('multiplicity',multiplicity_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[n]=f();print(n+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_written_carriers.py','scripts/check_written_carriers.py','scripts/register_written_carriers.py',
        'tests/test_written_carriers.py','scripts/check_role_qualifications.py','scripts/check_substituted_judgment.py','scripts/check_motive_causes.py',
        'scripts/check_designation_order.py','scripts/compose_falling_depiction.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_written_carrier_composition',document=FULL,**results,
        alignment=dict(**reading['source'],definitions=['rqxk','sd','sl','ss'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))

if __name__=='__main__':main()
