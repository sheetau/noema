"""Check nonfactive council functions, complete districts and adjacent levels."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_church_councils import ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parents, build, closure
from scripts.check_motive_causes import unknown, symbol
from scripts.check_pastoral_roles import evaluate
from scripts.fetch_delegated_associations_evidence import EVIDENCE, plain, validate as validate_evidence

REPORT = 'reports/church-councils-v1.json'
READING = 'data/church-councils-reading-v1.json'
DOC = 'docs/church-councils-v1.md'
PRIORS = ('reports/delegated-associations-v1.json', 'reports/fifth-paragraph-v1.json')
SCENES = ('reference', 'other')


def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, query, domain, boundaries=(), extra=''):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    constants = ''.join('r z'+n+'[] a.' for n in domain) + 'r zref[] d.r zotherpoint[] d.'
    return parse(format_graph(doc,'compact') + constants + extra + query)


def base(doc, domain):
    v = {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in domain}); v.update(zref=lambda:'reference', zotherpoint=lambda:'other')
    return v


def run(doc, values, domain): return evaluate(doc, values, domain, SCENES, True)


def actual_content(value): return Content(SCENES, (value,False))


@lru_cache(None)
def deliberation_checks():
    domain = ('person','body','activity','issue','church','creed','subject','other')
    args = ' '.join('k z'+n+'[]' for n in domain[:-1])
    doc = fixture(('r46d',), 'q[t[k r46d['+args+']][k zref[]]].', domain, ('r35r',))
    expected = {
        'h246c':('body','person','reference'), 'dg':('activity','reference'), 'f3':('person','activity','reference'),
        'h254i':('activity','body','reference'), 'h254h':('activity','issue','reference'),
        'h254j':('body','issue','reference'), 'h254k':('issue','church','reference'),
        'r35r':('church','creed','subject','reference'),
    }
    def values(change=None):
        v = base(doc,domain)
        for name,row in expected.items():
            wanted = tuple('other' if change==(name,i) else x for i,x in enumerate(row))
            v[name] = lambda *args,wanted=wanted: args==wanted
        return v
    assert run(doc,values(),domain)==[True]
    rows = []
    for name,row in expected.items():
        for i in range(len(row)):
            result=run(doc,values((name,i)),domain);assert result==[False],(name,i,result);rows.append([name,i])
    for name in expected:
        v=values();v[name]=unknown
        try:run(doc,v,domain)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    # Separate the existential wiring from the native same-event conjunction.
    # Five witness positions are distinct; no Cartesian execution of r35r.
    adapter=fixture(('r46e',),'q[t[k r46e[k zperson[] k zbody[]]][k zref[]]].',domain[:-1],('r46d',))
    results=[]
    for permitted in (True,False):
        v=base(adapter,domain[:-1]);v['r46d']=lambda *a:actual_content(permitted and a==domain[:-1])
        result=run(adapter,v,domain[:-1]);assert result==[permitted];results.append(result[0])
    return dict(native_same_event_and_issue=True,argument_mutations_rejected=rows,unknown_not_false=True,
        existing_church_boundary='r35r; unchanged definition and prior report pinned',
        separate_existential_adapter=results,adapter_boundary='r46d; seven distinct positions tested above')


@lru_cache(None)
def function_checks():
    domain=('body','other')
    doc=fixture(('r46f',),'q[k r46f[k zbody[] k zref[]]].',domain,('r456','r46c'))
    rows={}
    for variant in ('clerics','delegates','both','neither','wrong_body','wrong_reference','wrong_practice','wrong_rank','no_assignment'):
        v=base(doc,domain)
        v['r456']=lambda body,ref:variant in ('clerics','both') and (body,ref)==('body','reference')
        v['r46c']=lambda body,ref:variant not in ('clerics','neither') and (body,ref)==('body','reference')
        v['h246h']=lambda body,code,ref:variant!='no_assignment' and (body,symbol(code),code.rank,ref)==(
            'other' if variant=='wrong_body' else 'body','hzxi' if variant=='wrong_practice' else 'r46e',
            1 if variant=='wrong_rank' else 0,'other' if variant=='wrong_reference' else 'reference')
        result=run(doc,v,domain);assert result==[variant in ('clerics','delegates','both')],(variant,result);rows[variant]=result[0]
        assert v['dg'] is unknown and v['h254h'] is unknown
    return dict(contrasts=rows,assigned_practice_does_not_execute_meeting=True,
        membership_boundaries=['r456','r46c'],unchanged_memberships_pinned=True)


@lru_cache(None)
def order_checks():
    domain=('lower','middle','upper','extra','polity')
    doc=fixture(('r46h',),'q[k r46h[k zmiddle[] k zlower[] k zupper[] k zpolity[] k zref[]]].',domain)
    cases={}
    for variant in ('baseline','missing_transitive','cycle','self_edge','missing_lower','missing_middle','missing_upper',
                    'inserted_lower','inserted_upper','outside_edge','other_polity','other_reference','reversed'):
        scope={'lower','middle','upper'}
        edges={('middle','lower'),('upper','middle'),('upper','lower')}
        if variant=='missing_transitive':edges.remove(('upper','lower'))
        if variant=='cycle':edges.add(('lower','upper'))
        if variant=='self_edge':edges.add(('middle','middle'))
        if variant.startswith('missing_') and variant!='missing_transitive':scope.remove(variant[8:])
        if variant=='inserted_lower':
            scope.add('extra');edges|={('middle','extra'),('extra','lower'),('upper','extra')}
        if variant=='inserted_upper':
            scope.add('extra');edges|={('upper','extra'),('extra','middle'),('extra','lower')}
        if variant=='outside_edge':edges|={('middle','extra'),('extra','lower')}
        if variant=='reversed':edges={(b,a) for a,b in edges}
        v=base(doc,domain)
        v['h254l']=lambda body,polity,ref:body in scope and (polity,ref)==('polity','reference')
        v['h254m']=lambda high,low,polity,ref:(high,low) in edges and (polity,ref)==(
            'extra' if variant=='other_polity' else 'polity','other' if variant=='other_reference' else 'reference')
        result=run(doc,v,domain);assert result==[variant in ('baseline','outside_edge')],(variant,result);cases[variant]=result[0]
    return dict(native_strict_transitive_adjacent_levels=cases,no_other_polity_or_hidden_intermediate=True,
        complete_scope_is_interpretation_contract=True)


COUNCIL_DOMAIN=('body','district','province','polity','upper','churcha','churchb','locala','localb','other')


def council_model(doc,variant='baseline'):
    v=base(doc,COUNCIL_DOMAIN)
    churches={'churcha','churchb'}
    if variant=='singleton':churches.remove('churchb')
    if variant=='empty':churches.clear()
    if variant=='extra_church':churches.add('other')
    v['h254g']=lambda body,church,ref:(body,ref)==('body','reference') and church in churches
    v['h254o']=lambda church,district,ref:church in ({'churcha'} if variant=='split_district' else {'churcha','churchb'}) and (district,ref)==('district','reference')
    v['r46f']=lambda body,ref:variant!='not_council' and (body,ref)==('body','reference')
    v['r46c']=lambda body,ref:variant!='not_delegated' and (body,ref)==('body','reference')
    def exact(name,row):return lambda *args:variant!=name and args==row
    v['h254p']=exact('no_part',('district','province','reference'))
    v['h254r']=exact('not_province',('province','polity','reference'))
    v['h254q']=lambda body,province,polity,ref:(body,province,polity,ref)==(
        'other' if variant=='other_upper' else 'upper','other' if variant=='other_province' else 'province',
        'other' if variant=='other_polity' else 'polity','other' if variant=='other_reference' else 'reference')
    v['h246h']=lambda body,code,ref:variant!='no_upper_practice' and (body,symbol(code),code.rank,ref)==('upper','r46e',0,'reference')
    def local(body,church,ref):
        pairs={('locala','churcha'),('localb','churchb')}
        if variant=='missing_local':pairs.remove(('localb','churchb'))
        if variant=='swapped_locals':pairs={('locala','churchb'),('localb','churcha')}
        return ref=='reference' and (body,church) in pairs
    v['h254n']=local
    v['r46h']=lambda body,local,upper,polity,ref:local in ({'locala'} if variant=='missing_order' else {'locala','localb'}) and (body,upper,polity,ref)==(
        'body','other' if variant=='split_upper' else 'upper','other' if variant=='split_polity' else 'polity',
        'other' if variant=='split_reference' else 'reference')
    return v


@lru_cache(None)
def district_checks():
    doc=fixture(('r46i',),'q[k r46i[k zbody[] k zdistrict[] k zref[]]].',COUNCIL_DOMAIN)
    rows={}
    for variant in ('baseline','singleton','empty','extra_church','split_district'):
        result=run(doc,council_model(doc,variant),COUNCIL_DOMAIN);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    return dict(native_all_constituent_churches_in_same_district=rows)


@lru_cache(None)
def regional_checks():
    args=' '.join('k z'+n+'[]' for n in COUNCIL_DOMAIN[:5])+' k zref[]'
    doc=fixture(('r46j',),'q[k r46j['+args+']].',COUNCIL_DOMAIN,('r46f','r46c','r46h'))
    rows={}
    for variant in ('baseline','swapped_locals','not_council','not_delegated','singleton','empty','extra_church','split_district',
        'no_part','not_province','other_upper','other_province','other_polity','other_reference','no_upper_practice',
        'missing_local','missing_order','split_upper','split_polity','split_reference'):
        result=run(doc,council_model(doc,variant),COUNCIL_DOMAIN)
        # The association of local councils to churches is input, not the
        # spelling of fixture IDs. A consistent permutation remains valid.
        assert result==[variant in ('baseline','swapped_locals')],(variant,result);rows[variant]=result[0]
    v=council_model(doc);v['h254n']=lambda local,church,ref:(local,church,ref) in {
        ('locala','churcha','reference'),('other','churchb','reference')}
    assert run(doc,v,COUNCIL_DOMAIN)==[False]
    domain=COUNCIL_DOMAIN[:5]
    adapter=fixture(('r46k',),'q[k r46k[k zbody[] k zref[]]].',domain,('r46j',))
    for permit in (True,False):
        v=base(adapter,domain);v['r46j']=lambda *args:permit and args==(*domain,'reference')
        assert run(adapter,v,domain)==[permit]
    for name in ('h254g','h254o','h254p','h254r','h254q','h254n','r46h'):
        v=council_model(doc);v[name]=unknown
        try:run(doc,v,COUNCIL_DOMAIN)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(same_district_province_polity_upper_and_all_locals=rows,local_witness_not_mixed=True,
        boundaries=['r46f and r46h separately tested','r46c unchanged with pinned native tests'],
        separate_existential_adapter='r46j; all four supplied positions distinct',unknown_not_false=True)


def reading_record():
    evidence=read(EVIDENCE);validate_evidence(evidence)
    raw=(ROOT/evidence['sources'][0]['path']).read_text(encoding='utf-8');text=plain(raw)
    articles={}
    for first,last in [('XXX.','XXXII.'),('XXXVI.','XXXVIII.'),('XLI.','XLIII.'),('XLVII.','XLIX.')]:
        start=text.index(first);articles[first]=text[start:text.index(last,start)]
    return dict(status='explicit_institutional_reading_dependency_not_complete_sentence',
        source=evidence['source'],primary_page=evidence['primary_page'],evidence=EVIDENCE,
        evidence_sha256=digest((ROOT/EVIDENCE).read_bytes()),historical_articles=articles,
        interpretation=[
            'Kirchenversammlungは、この文脈の聖職者または教会の職務代表が、共同の宗教上の事柄を審議・議決する機能を持つ会議体として読む。分類は共同実践の指定であり、実際の会合・決議を要求しない。',
            'Klassisは近隣の諸教会を代表し、各教会内部の地方会議と州段階の広域会議の間に位置する教会統治の会議体として構成する。各教会との対応と同じ州会議を保持する。',
            '史料の人数や多数決等の細則をこの語の必須条件にしない。完全な機関範囲の直接段階差は採用する歴史制度上の解釈であり、全時代の名称一般を定義しない。',
        ],remaining=['自己呼称とオランダの用法','ehrwürdigの呼称上の働き','etwaの例示','否定疑問と権限','同じ不変信条への相互宣誓','上位後見と人民への媒介','持続と次の回答'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            prior=next(c.entries[n] for c in sources if n in c.entries)
            assert e['declaration']==prior['declaration'] and e['meaning_ja']==prior['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        body=format_graph(new.document,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    assert read(READING)==reading_record()
    assert not new.document['statements'] and len(sources[0].document['statements'])==96
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        historical_articles_and_explicit_reading_pinned=True,no_new_source_sentence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('deliberation',deliberation_checks),('function',function_checks),('order',order_checks),
                   ('district',district_checks),('regional',regional_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,READING,EVIDENCE,evidence['source']['inventory'],
        evidence['primary_page']['path'],*[p['path'] for p in evidence['sources']],
        'scripts/compose_church_councils.py','scripts/check_church_councils.py','tests/test_church_councils.py',
        'scripts/fetch_delegated_associations_evidence.py','scripts/check_motive_causes.py','scripts/check_pastoral_roles.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_spiritual_guardians.py'}
    return dict(status='religious_deliberative_practice_and_regional_council_level',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
