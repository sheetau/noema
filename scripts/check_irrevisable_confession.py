"""Check shared content, no substantive revision and all reciprocal parties."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_irrevisable_confession import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate

REPORT='reports/irrevisable-confession-v1.json'
DOC='docs/irrevisable-confession-v1.md'
READING='data/irrevisable-confession-reading-v1.json'
PRIORS=('reports/delegated-associations-v1.json','reports/fifth-paragraph-v1.json')
DOMAIN=('person','second','agreement','body','creed','subject','alternative','acta','actb','other')
SCENES=('past','reference','middle','future','candidate','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in ('ref','middle','candidate'))
EXTRA+='r zoriginal[] e.r zreword[] e.r zchanged[] e.r zchoose[a d i[e] i[e] i[e]] i[e].'
PROVIDER='d h246e[creed a point d] i[e][k zchoose[v creed v point r[k zoriginal[]] r[k zreword[]] r[k zchanged[]]]].'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query,boundaries=(),provider=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    if provider:
        prefix=parse('p:'+EXTRA+PROVIDER);new=next(d for d in prefix['declarations'] if d['name']=='h246e')
        doc['declarations']=[d for d in prefix['declarations'] if d['name']!='h246e']+[deepcopy(new if d['name']=='h246e' else d) for d in doc['declarations']]
        return parse(format_graph(doc,'compact')+query)
    return parse(format_graph(doc,'compact')+EXTRA+query)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN})
    v.update(zref=lambda:'reference',zmiddle=lambda:'middle',zcandidate=lambda:'candidate')
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


def model(doc,variant='baseline'):
    v=base(doc)
    def choose(creed,point,original,reword,changed):
        if creed=='creed':
            if point=='middle' and variant=='actual_change':return changed
            if point=='middle' and variant=='rewording':return reword
            return original
        return reword if creed=='alternative' and variant=='same_content_alternative' else changed
    v['zchoose']=choose
    v['h245z']=lambda subject,ref:variant!='not_religious' and (subject,ref)==('subject','reference')
    v['h246f']=lambda creed,subject,ref:(creed,subject,ref)==('creed','subject','reference')
    def adoption(body,creed,content,point):
        wanted='zchanged' if point=='middle' and variant=='actual_change' else 'zreword' if point=='middle' and variant=='rewording' else 'zoriginal'
        return (body,creed,symbol(content))==('body','creed',wanted) and not (point=='middle' and variant=='adoption_gap')
    v['h246g']=adoption
    v['h254w']=lambda creed,baseline,candidate,ref:(creed,symbol(baseline),baseline.rank,ref)==('creed','zoriginal',0,'reference') and candidate.rank==0 and symbol(candidate) in ('zoriginal','zreword')
    def candidates(body,creed,alternative,ref):
        allowed={'creed','alternative'}
        if variant=='missing_baseline':allowed.remove('creed')
        if variant=='empty_candidates':allowed.clear()
        if variant=='extra_allowed_change':allowed.add('other')
        return (body,creed,ref)==('body','creed','reference') and alternative in allowed
    v['h254x']=candidates
    def admitted(agreement,body,creed,alternative,ref,point):
        if (agreement,body,creed,ref)!=('agreement','body','creed','reference'):return False
        if alternative=='creed':return True
        return point=='middle' and (variant in ('allowed_change','same_content_alternative') and alternative=='alternative' or variant=='extra_allowed_change' and alternative=='other')
    v['h254y']=admitted
    points=('past','reference','middle','future')
    v['h253w']=lambda body,candidate,point:(body,candidate)==('body','candidate') and point in points and not (variant=='missing_anchor' and point=='reference')
    def before(first,last,candidate):
        result=candidate=='candidate' and first in points and last in points and points.index(first)<points.index(last)
        if variant=='missing_transitive' and (first,last)==('reference','future'):return False
        if variant=='cycle' and (first,last)==('future','reference'):return True
        return result
    v['ic']=before
    return v


@lru_cache(None)
def content_checks():
    args='k zagreement[] k zbody[] k zcreed[] k zsubject[] k zref[]'
    query=('q[k r46q[k zbody[] k zcreed[] k zref[] k zmiddle[]]].'
        'q[k r46r[k zagreement[] k zbody[] k zcreed[] k zref[] k zmiddle[]]].'
        'q[t[k r46s['+args+']][k zmiddle[]]].')
    doc=fixture(('r46q','r46r','r46s'),query,provider=True)
    expectations={'baseline':[True,True,True],'rewording':[True,True,True],'actual_change':[False,True,False],
        'adoption_gap':[False,True,False],'allowed_change':[True,False,False],'same_content_alternative':[True,True,True],
        'extra_allowed_change':[True,False,False],'missing_baseline':[True,False,False],'empty_candidates':[True,False,False],
        'not_religious':[True,True,False]}
    rows={}
    for variant,expected in expectations.items():
        v=model(doc,variant);actual=run(doc,v);assert actual==expected,(variant,actual);rows[variant]=actual
        assert all(v[n] is unknown for n in ('zoriginal','zreword','zchanged'))
    for name in ('h246g','h254w','h254x','h254y','zchoose'):
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_adoption_revision_and_combined_contrasts=rows,creed_truth_not_evaluated=True,
        content_preserving_rewording_not_syntax_equality=True,unknown_not_false=True)


@lru_cache(None)
def persistence_checks():
    doc=fixture(('r46t',),'q[t[k r46t[k zagreement[] k zbody[] k zcreed[] k zsubject[] k zref[]]][k zcandidate[]]].',provider=True)
    rows={}
    for variant in ('baseline','rewording','actual_change','adoption_gap','allowed_change','extra_allowed_change','missing_anchor','missing_transitive','cycle'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','rewording')],(variant,actual);rows[variant]=actual[0]
    return dict(native_same_complete_future_and_regime=rows,midcourse_changes_not_hidden_by_final_restoration=True,
        finite_models_are_diagnostics_not_eternity_proof=True,history_completeness_is_input_contract=True)


@lru_cache(None)
def terms_checks():
    names=('person','agreement','body','creed','subject');rows={}
    for seq in (names,names[:-1],(*names,'person'),('agreement','person','body','creed','subject'),('person','agreement','creed','body','subject')):
        literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
        doc=fixture(('r46u',),'q[t[k r46u['+literal+']][k zcandidate[]]].',('r46t',))
        v=base(doc);v['h254z']=lambda agreement:'reference';v['aa']=lambda p:p=='person'
        v['h246c']=lambda body,person,ref:(body,person,ref)==('body','person','reference')
        v['r46t']=lambda *args:Content(SCENES,tuple(args==('agreement','body','creed','subject','reference') and p=='candidate' for p in SCENES))
        actual=run(doc,v,names);assert actual==[seq==names],(seq,actual);rows[str(seq)]=actual[0]
    return dict(exact_five_position_bindings=rows,boundary='r46t; native all-future condition checked separately',
        first_person_and_fixed_membership_preserved=True)


def formation_model(doc,variant='baseline'):
    v=base(doc)
    parties={'person','second'}
    if variant=='extra_member':parties.add('other')
    if variant=='singleton':parties.remove('second')
    v['h246c']=lambda body,person,ref:body=='body' and person in (parties if ref=='reference' else {'other'})
    v['aa']=lambda person:person in ('person','second','other')
    v['h254z']=lambda agreement:'middle' if variant=='wrong_anchor' else 'reference'
    points=('past','reference','middle')
    v['h255c']=lambda agreement,ref,point:(agreement,ref)==('agreement','reference') and point in points
    v['ic']=lambda first,last,ref:ref=='reference' and first in points and last in points and points.index(first)<points.index(last)
    records={('person','acta','past'),('second','actb','reference')}
    if variant=='future_declaration':records.remove(('second','actb','reference'));records.add(('second','actb','middle'))
    v['dg']=lambda act,point:any((act,point)==(a,t) for p,a,t in records)
    v['f3']=lambda person,act,point:(person,act,point) in records
    v['h255a']=lambda agreement,code,ref:variant!='no_assignment' and (agreement,symbol(code),code.rank,ref)==('agreement','r46u',0,'reference')
    def declares(person,act,agreement,code,bindings,point):
        row=('second' if variant=='wrong_person' and person=='person' else person,act,point)
        tail=('agreement','body','creed','subject')
        if variant=='different_creed' and person=='second':tail=('agreement','body','alternative','subject')
        return variant!='no_declaration' and row in records and (agreement,symbol(code),code.rank,tuple(bindings.items))==('agreement','r46u',0,(person,*tail))
    v['h255b']=declares
    def toward(person,other,act,agreement,code,bindings,point):
        if variant=='self_only':return person==other
        if variant=='missing_reverse' and person=='second':return False
        if variant=='separate_act' and person=='person':return act=='actb'
        if variant=='separate_time' and person=='person':return point=='reference'
        if variant=='other_counterparty':return other=='other'
        if variant=='other_terms':return symbol(code)=='r46t'
        return other in ('person','second') and person!=other and declares(person,act,agreement,code,bindings,point)
    v['h255d']=toward
    return v


@lru_cache(None)
def formation_checks():
    doc=fixture(('r46v',),'q[k r46v[k zbody[] k zagreement[] k zcreed[] k zsubject[] k zref[]]].')
    rows={}
    for variant in ('baseline','extra_member','singleton','wrong_anchor','future_declaration','no_assignment','no_declaration',
                    'wrong_person','different_creed','self_only','missing_reverse','separate_act','separate_time','other_counterparty','other_terms'):
        v=formation_model(doc,variant);actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert all(v[n] is unknown for n in ('h246e','h246g','h254w','h254y','h253w'))
    for name in ('h255a','h255b','h255c','h255d','h246c'):
        v=formation_model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_all_reciprocal_parties_and_same_declarations=rows,formation_does_not_execute_terms=True,
        parties_fixed_at_reference_not_each_past_declaration=True,unknown_not_false=True)


def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    phrase='sich eidlich unter einander auf ein gewisses unveränderliches Symbol zu verpflichten'
    start=unit['text'].index(phrase)
    return dict(status='shared_irrevisable_confession_and_reciprocity_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        primary_page=dict(path='artifacts/spiritual-guardians-v1/page-488.jpg',sha256='59aea30d7cb2baa22795dbfb0fcab14a40704421f042bcfbef335a8677de943a'),
        interpretation=[
            '同じ特定の信条の実質的内容を保つ採用と、合意に定める制度上の改訂権能の不在を分ける。単なる過去の無変更、構文上の完全一致、物理的不能に縮約しない。',
            '条項は同じ共同の制度的結果を、各人が自分も拘束されるものとして引き受ける内容。全員の引数列の先頭だけを本人に変え、合意・団体・信条・主題と固定基準を共有する。',
            '相互の引受けは同じ行為・時点で他の全当事者に対する責務の表明を要求する。独立した独白や別行為での約束を合成しない。',
        ],remaining=['eidlichの宣誓修飾','団体の例示・自己呼称との統合','上位後見・人民への媒介・持続という目的','権限の問いと次の否定回答'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            old=next(c.entries[n] for c in sources if n in c.entries)
            assert e['declaration']==old['declaration'] and e['meaning_ja']==old['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        body=format_graph(new.document,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    assert read(READING)==reading_record()
    page=read(READING)['primary_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    assert not new.document['statements'] and len(sources[0].document['statements'])==96
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        source_range_and_primary_page_pinned=True,no_new_source_sentence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('content',content_checks),('persistence',persistence_checks),('terms',terms_checks),
                   ('formation',formation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=read(READING)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,READING,reading['source_inventory'],reading['primary_page']['path'],
        'scripts/compose_irrevisable_confession.py','scripts/check_irrevisable_confession.py','tests/test_irrevisable_confession.py',
        'scripts/check_motive_causes.py','scripts/check_pastoral_roles.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='same_irrevisable_confession_in_reciprocal_undertakings',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
