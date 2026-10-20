"""Check ordered conditional force, both kinds and the complete presentation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_generic_fetters import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, KIND_BASIS, APPOSITION, APPOSITION_BASIS, MEANINGS, PRIMITIVES, LIMITS, parent, imports, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_conditioned_persistence as previous

INDEX = 'data/semantic-review-index-v101.json'
REPORT = 'reports/generic-fetters-v1.json'
AUDIT = 'data/generic-fetters-reading-v1.json'
DOC = 'docs/generic-fetters-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
SECOND = 'data/confirmed-incapacity-reading-v1.json'
PRIOR = ('reports/conditioned-persistence-v1.json', 'reports/conjoined-kinds-v1.json', 'reports/polymorphic-forms-v1.json', 'reports/prescription-effects-v1.json')
BOUNDARY_SCENES = ('anchor', 'keep', 'stop', 'first', 'last', 'released')
BOUNDARY_PEOPLE = ('person', 'object', 'faculty', 'act', 'other', 'judgment')
PRESENTATION_PEOPLE = ('author', 'third', 'second', 'fourth', 'subject', 'apposition', 'correction', 'other')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, extra):
    doc = deepcopy(catalog().document); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


@lru_cache(None)
def ordered_checks():
    doc = fixture(['r2fr'], '''r zanchor[] d.r zcandidates[d d] c.r zhistories[d d d] c.r zbefore[d d d d] c.
r zcondition[d] c.r zresult[d] c.
q[k r2fr[b point[k zcondition[v point]] b point[k zresult[v point]] k zanchor[] p zcandidates p zhistories p zbefore]].''')
    scenes = ('past', 'anchor', 'left', 'right', 'l1', 'r1'); points = ('anchor', 'l1', 'r1')
    histories = dict(left=('past', 'anchor', 'l1'), right=('past', 'anchor', 'r1'))
    def values(bits):
        left, right, ca, cl, cr, ra, rl, rr = bits
        def before(a, b, first, last):
            h = histories.get(b, ())
            return a == 'anchor' and first in h and last in h and h.index(first) < h.index(last)
        return dict(zanchor=lambda: 'anchor', zcandidates=lambda a,b: a == 'anchor' and (b == 'left' and left or b == 'right' and right),
            zhistories=lambda a,b,p: a == 'anchor' and p in histories.get(b, ()), zbefore=before,
            zcondition=lambda p: p in points and (ca,cl,cr)[points.index(p)],
            zresult=lambda p: p in points and (ra,rl,rr)[points.index(p)])
    for bits in product((False, True), repeat=8):
        left, right, ca, cl, cr, ra, rl, rr = bits
        eligible = (left and ca and cl, right and ca and cr)
        want = any(eligible) and (not eligible[0] or ra and rl) and (not eligible[1] or ra and rr)
        assert evaluate(doc, values(bits), ('person',), scenes, True) == [want], bits
    rows = {}; base = (True, True, True, True, False, True, True, False)
    for name in ('baseline', 'no_anchor', 'empty_history', 'no_order', 'reflexive', 'cycle', 'missing_transitive_edge',
                 'past_failure_ignored', 'anchor_failure', 'late_failure', 'wrong_branch'):
        v = values(base); h, order = v['zhistories'], v['zbefore']
        if name == 'no_anchor': v['zhistories'] = lambda a,b,p: h(a,b,p) and p != 'anchor'
        if name == 'empty_history': v['zhistories'] = lambda a,b,p: b == 'left' and h(a,b,p)
        if name == 'no_order': v['zbefore'] = lambda *args: False
        if name == 'reflexive': v['zbefore'] = lambda a,b,f,l: order(a,b,f,l) or f == l
        if name == 'cycle': v['zbefore'] = lambda a,b,f,l: order(a,b,f,l) or (b,f,l) == ('left','l1','past')
        if name == 'missing_transitive_edge': v['zbefore'] = lambda a,b,f,l: order(a,b,f,l) and (b,f,l) != ('left','past','l1')
        if name == 'anchor_failure': v['zresult'] = lambda p: p == 'l1'
        if name == 'late_failure': v['zresult'] = lambda p: p == 'anchor'
        if name == 'wrong_branch': v['zhistories'] = lambda a,b,p: b == 'outside' and p in points
        actual = evaluate(doc, v, ('person',), scenes, True)
        assert actual == [name in ('baseline','past_failure_ignored')], (name, actual)
        rows[name] = actual
    for name in ('zcandidates','zhistories','zbefore','zcondition','zresult'):
        v = values(base); v[name] = unknown
        try: evaluate(doc, v, ('person',), scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=256, cases=rows, unknown_inputs_refused=5,
                original_order_and_conditional_definitions_executed=True, anchor_and_entire_ordered_tail_required=True)


@lru_cache(None)
def source_document(boundary=True):
    doc = fixture(['r2fu','r2fs','wh'], '''r zobject[] a.r zother[] a.r zperson[] a.r zanchor[] d.
q[t[k r2fu[]][k wh[]]].
q[k r2fs[k wh[] k zobject[] k zperson[] k zanchor[]]].
q[k r2fs[k wh[] k zother[] k zperson[] k zanchor[]]].''')
    replacement = parse('''p:r zkindrule[a d] c.r zkindform[a d] c.
d hd2[object a] e[b point[k zkindrule[v object v point]]].
d r2fg[object a] e[b point[k zkindform[v object v point]]].''')
    if boundary:
        replacement = parse(format_graph(replacement,'compact')+'r zstate[a d] c.d bf[person a] e[b point[k zstate[v person v point]]].')
    primitives = [d for d in replacement['declarations'] if d['kind']=='primitive']
    mapping = {d['name']:d for d in replacement['declarations'] if d['kind']=='definition'}
    doc['declarations'] = primitives + [deepcopy(mapping.get(d['name'],d)) for d in doc['declarations']]
    doc['declarations'] = closure(doc, ['r2fu','r2fs','wh','zobject','zother','zperson','zanchor'])
    return parse(format_graph(doc,'compact'))


def source_values(doc, variant='baseline', boundary=True):
    values = previous.source_values(doc, variant, boundary)
    values.update(wh=lambda:'anchor', zother=lambda:'other', zanchor=lambda:'first',
        hzzzb=lambda scope,item: scope=='anchor' and item in ('object','other'),
        hzzzc=lambda scope,item: 'object' if variant=='second_object' and item=='other' else item,
        hzzzd=lambda scope,item: 'other' if variant=='second_person' and item=='other' else 'person',
        hzzze=lambda scope,item: 'last' if variant=='second_anchor' and item=='other' else 'first',
        hzzzf=lambda scope,first,last: (first,last)==('object','other'),
        zkindrule=lambda o,s:(o,s)==('object','first'),
        zkindform=lambda o,s:(o,s)==('other','first'),
        fb=lambda j,o,s:j=='judgment' and o in ('object','other'),
        hx2=lambda p,o,a,s: p=='person' and o in ('object','other') and a=='act' and s in ('first','last'))
    def identity(scope,o,p,a): return scope=='anchor' and o in ('object','other') and p=='person' and a=='first'
    def history(scope,o,p,a,b,point):
        return identity(scope,o,p,a) and (b=='keep' and point in ('first','last') or b=='stop' and point in ('first','released'))
    values.update(hzzzg=lambda scope,o,p,a,b: identity(scope,o,p,a) and b in ('keep','stop') and not (variant=='second_branches' and o=='other'),
        hzzzh=history,
        hzzzi=lambda scope,o,p,a,b,f,l: identity(scope,o,p,a) and f=='first' and (b=='keep' and l=='last' or b=='stop' and l=='released'))
    if variant=='second_history': values['hzzzh']=lambda scope,o,p,a,b,point: o=='object' and history(scope,o,p,a,b,point)
    if variant=='second_order': values['hzzzi']=lambda scope,o,p,a,b,f,l: o=='object' and identity(scope,o,p,a) and f=='first' and l in ('last','released')
    if variant=='missing_kind': values['zkindform']=lambda *args:False
    if variant=='scope': values['hzzzg']=lambda *args:False
    if variant=='classification_context': values['zkindform']=lambda o,s:(o,s)==('other','last')
    return values


@lru_cache(None)
def binding_checks():
    doc=source_document(True);rows={}
    failures={'cause_act','cause_person','cause_lifetime','missing_last_cause','mature_last','split_use','examined','scope'}
    variants=('baseline','second_object','second_person','second_anchor','second_branches','second_history','second_order',
              'missing_kind','classification_context',*sorted(failures))
    for name in variants:
        actual=evaluate(doc,source_values(doc,name),BOUNDARY_PEOPLE,BOUNDARY_SCENES,True)
        first=name not in failures
        second=first and name not in ('second_branches','second_history','second_order','missing_kind','classification_context')
        assert actual==[name=='baseline',first,second],(name,actual)
        rows[name]=actual
    for name in ('hzzzb','hzzzc','hzzzd','hzzze','hzzzf','hzzzg','hzzzh','hzzzi','zkindrule','zkindform','g3','zstate'):
        values=source_values(doc);values[name]=unknown
        try:evaluate(doc,values,BOUNDARY_PEOPLE,BOUNDARY_SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=12,classification_and_capacity_boundaries_isolated=True,
                same_case_identity_and_both_kinds_required=True)


@lru_cache(None)
def native_checks():
    doc=source_document(False);rows={}
    for name in ('baseline','mature_last','cause_act','second_history'):
        actual=evaluate(doc,source_values(doc,name,False),previous.PEOPLE,previous.SCENES,True)
        want=[True,True,True] if name=='baseline' else [False,True,False] if name=='second_history' else [False]*3
        assert actual==want,(name,actual)
        rows[name]=actual
        print('native '+name+' checked',flush=True)
    full=fixture(['r2fu','wh'],'q[t[k r2fu[]][k wh[]]].')
    try:evaluate(full,source_values(full,boundary=False),previous.PEOPLE,previous.SCENES,True)
    except ValueError as error:assert 'Cannot finitely quantify' in str(error) and 'description' in str(error),str(error)
    else:raise AssertionError('All class descriptions replaced by finite examples')
    return dict(cases=rows,native_capacity_and_causal_profile_executed=True,classification_universe_explicitly_refused=True)


def presentation_values(doc, bits=(True,)*5, variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    refs={'wa':'author','wh':'now','h2d':'third','hzzr':'second','h3a':'fourth','hzzzj':'subject','hzzzk':'apposition','hk2':'correction'}
    if variant=='same_mentions':refs['hzzzk']='subject'
    values.update({n:(lambda value=v:value) for n,v in refs.items()})
    asserted,depicted,denoted,clarified,corrected=bits
    values.update(
        uc=lambda n,a,d,s: asserted and (n,a,json.loads(d.syntax),s)==('third','author',{'kind':'call','symbol':'r2fu','arguments':[]},'now'),
        rbt=lambda n,a,t,d,s: depicted and (n,a,symbol(t),symbol(d),s)==('third','author','r2ft','h2b','now'),
        rbf=lambda n,a,f,t,s: corrected and (n,a,symbol(f),symbol(t),s)==('correction','author','hm2','hn2','now'),
        ibbdenotes=lambda n,a,d,scope,s: denoted and n in ('subject','apposition') and (a,symbol(d),d.rank,scope,s)==('author','r2fh',1,'third','now'),
        ibbclarifies=lambda f,l,a,scope,s: clarified and (f,l,a,scope,s)==('subject','apposition','author','third','now'),
        ue=lambda f,l,s: s=='now' and (f,l) in {('subject','apposition'),('second','third'),('third','fourth')})
    if variant=='reverse_mentions':values['ue']=lambda f,l,s:s=='now' and (f,l) in {('subject','apposition'),('apposition','subject'),('second','third'),('third','fourth')}
    if variant=='lost_previous':values['ue']=lambda f,l,s:s=='now' and (f,l) in {('subject','apposition'),('third','fourth')}
    if variant=='lost_next':values['ue']=lambda f,l,s:s=='now' and (f,l) in {('subject','apposition'),('second','third')}
    if variant=='other_kind':values['ibbdenotes']=lambda n,a,d,scope,s:symbol(d)=='h22'
    if variant=='other_target':values['rbt']=lambda n,a,t,d,s:symbol(t)=='r2fj'
    return values


@lru_cache(None)
def presentation_checks():
    doc=fixture(['r2fv'],'q[k r2fv[]].');rows={}
    for bits in product((False,True),repeat=5):
        assert evaluate(doc,presentation_values(doc,bits),PRESENTATION_PEOPLE,('now',),True)==[all(bits)],bits
    for name in ('baseline','same_mentions','reverse_mentions','lost_previous','lost_next','other_kind','other_target'):
        actual=evaluate(doc,presentation_values(doc,variant=name),PRESENTATION_PEOPLE,('now',),True)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    for name in ('uc','rbt','rbf','ibbdenotes','ibbclarifies','ue'):
        values=presentation_values(doc);values[name]=unknown
        try:evaluate(doc,values,PRESENTATION_PEOPLE,('now',),True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=32,cases=rows,unknown_inputs_refused=6,world_contents_not_executed_by_attribution=True,
                same_kind_in_subject_and_apposition=True,reformulation_and_adjacent_sentences_preserved=True)


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0010')
    paths={INDEX,INVENTORY,FULL,BASIS,PARENT,PARENT_BASIS,FIRST,SECOND,KIND_BASIS,APPOSITION,APPOSITION_BASIS,*PRIOR}
    return dict(status='third_sentence_generic_conditional_candidate',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[293,473],text=unit['text'][293:473]),
        selection=selection_binding(catalog(),[10,52]),
        decision='二種類への一般化、継続使用の条件付き作用、同格と足枷の比喩を一文の候補へ接続。語義と持続の読みの最終判断は未完。',
        references=[dict(url='https://korpora.org/Kant/aa08/036.html',title='Kant AA VIII036',accessed='2026-10-20',
            use='第三文の主語と同格・言い直し・足枷・持続、および直後の離脱仮定を照合。今回の条件付き一般化が唯一の読解であるとはしない。')],
        interpretation_limits=LIMITS,revised_statement_indices=[52],preserved_reviewed_sentence_characters=247,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-20]==old.document['declarations']
    assert len(new.document['statements'])==len(old.document['statements'])==54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[52]
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    for d in imports()[0]:assert new.entries[d['name']]['declaration']==d
    assert 'h26' not in {d['name'] for d in closure(new.document,['r2fv'])}
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        r=read(path);ids=[s['index'] for s in r['selection']['statements']]
        assert r['selection']==selection_binding(old,ids)==selection_binding(new,ids)
    for p,ids in ((FIRST,[51]),(SECOND,[11,12])):
        r=read(p);validate_hashes(ROOT,r['source_sha256']);assert r['selection']==selection_binding(new,ids)
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    assert closure(new.document,['r2ew','r2ex','r2bg'])==closure(old.document,['r2ew','r2ex','r2bg'])
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert read(AUDIT)==reading()
    return dict(added_definitions=8,new_composed_definitions=6,reused_definitions=2,added_primitives=12,
        context_inputs=8,local_references=2,reused_discourse_relations=2,authored_statements=54,preserved_statements=53,
        revised_statement_indices=[52],preserved_review_selections=12,reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=247,actual_lifetime_result_removed_from_current_target=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,body in build().items():write_exact(ROOT/p,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('ordered',ordered_checks),('binding',binding_checks),('native',native_checks),('presentation',presentation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    record=reading();paths=set(build())|set(catalog().source_sha256)|set(record['source_sha256'])|{
        AUDIT,DOC,'scripts/compose_generic_fetters.py','scripts/check_generic_fetters.py','scripts/register_generic_fetters.py',
        'tests/test_generic_fetters.py','scripts/check_conditioned_persistence.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    for p in PRIOR:paths.update(read(p)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='generic_conditional_fetters_candidate_checked',document=FULL,**results,
        alignment=dict(**record['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_covered_characters=44,
        new_verified_sentence_characters=0,preserved_reviewed_sentence_characters=247,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
