"""Check use-free intervals, earlier causes, and the connected source candidate."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_occasional_continuation import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts import check_generic_fetters as previous

INDEX='data/semantic-review-index-v103.json'
REPORT='reports/occasional-continuation-v1.json'
AUDIT='data/occasional-continuation-reading-v1.json'
DOC='docs/occasional-continuation-v1.md'
PRIOR=('reports/shared-fetters-scope-v1.json','reports/generic-fetters-v1.json')
PREVIOUS_READING='data/shared-fetters-scope-reading-v1.json'
SCENES=(*previous.BOUNDARY_SCENES,'middle')

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def document():return parse((ROOT/FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def fixture(roots,extra,replacements=''):
    doc=deepcopy(document());doc['statements']=[]
    if replacements:
        added=parse('p:'+replacements)['declarations'];mapping={d['name']:d for d in added if d['kind']=='definition'}
        doc['declarations']=[d for d in added if d['kind']=='primitive']+[deepcopy(mapping.get(d['name'],d)) for d in doc['declarations']]
    doc['declarations']=closure(doc,roots)
    return parse(format_graph(doc,'compact')+extra)

def refuse(doc,values,names,people,scenes):
    for name in names:
        v=dict(values);v[name]=unknown
        try:evaluate(doc,v,people,scenes,True)
        except ValueError as error:assert 'Unknown' in str(error),(name,str(error))
        else:raise AssertionError(name)

@lru_cache(None)
def profile_checks():
    doc=fixture(['r2g5','r2fr'],'''r za[] d.r zu[d] c.r zr[d] c.r zb[d d] c.r zh[d d d] c.r zo[d d d d] c.r zj[d d d] c.
q[k r2g5[b p[k zu[v p]] k za[] p zb p zh p zo p zj i[branch d point d][k zr[v point]]]].
q[k r2fr[b p[k zu[v p]] b p[k zr[v p]] k za[] p zb p zh p zo]].''')
    points=('first','middle','last');scenes=(*points,'branch','other','past')
    def values(bits=(False,True,True,False,True,True,True,True)):
        om,ol,uf,um,ul,rf,rm,rl=bits
        return dict(za=lambda:'first',zu=lambda p:p in points and (uf,um,ul)[points.index(p)],
            zr=lambda p:p in points and (rf,rm,rl)[points.index(p)],zb=lambda a,b:(a,b)==('first','branch'),
            zh=lambda a,b,p:a=='first' and b in ('branch','other') and p in points,
            zo=lambda a,b,f,l:a=='first' and b in ('branch','other') and f in points and l in points and points.index(f)<points.index(l),
            zj=lambda a,b,p:a=='first' and b in ('branch','other') and p in points and (True,om,ol)[points.index(p)])
    for bits in product((False,True),repeat=8):
        om,ol,uf,um,ul,rf,rm,rl=bits
        expected=[uf and (not om or um) and (not ol or ul) and rf and rm and rl,uf and um and ul and rf and rm and rl]
        assert evaluate(doc,values(bits),('act',),scenes,True)==expected,bits
    rows={}
    for name in ('gap','continuous','result_lost_in_gap','missed_occasion','no_candidates','no_anchor','no_anchor_occasion',
                 'cycle','missing_transitivity','invalid_other_candidate','no_later_occasions'):
        v=values();want=[True,False]
        if name=='continuous':v=values((True,True,True,True,True,True,True,True));want=[True,True]
        if name=='result_lost_in_gap':v['zr']=lambda p:p in ('first','last');want=[False,False]
        if name=='missed_occasion':v['zj']=lambda a,b,p:p in points;want=[False,False]
        if name=='no_candidates':v['zb']=lambda *args:False;want=[False,False]
        if name=='no_anchor':v['zh']=lambda a,b,p:p in ('middle','last');want=[False,False]
        if name=='no_anchor_occasion':v['zj']=lambda a,b,p:p=='last';want=[False,False]
        if name=='cycle':
            before=v['zo'];v['zo']=lambda a,b,f,l:before(a,b,f,l) or (f,l)==('last','first');want=[False,False]
        if name=='missing_transitivity':
            before=v['zo'];v['zo']=lambda a,b,f,l:before(a,b,f,l) and (f,l)!=('first','last');want=[False,False]
        if name=='invalid_other_candidate':
            v['zb']=lambda a,b:a=='first' and b in ('branch','other')
            h=v['zh'];v['zh']=lambda a,b,p:b=='branch' and h(a,b,p);want=[False,False]
        if name=='no_later_occasions':v['zj']=lambda a,b,p:p=='first';v['zu']=lambda p:p=='first'
        actual=evaluate(doc,v,('act',),scenes,True);assert actual==want,(name,actual);rows[name]=actual
    refuse(doc,values(),('zu','zr','zb','zh','zo','zj'),('act',),scenes)
    return dict(combinations=256,cases=rows,unknown_inputs_refused=6,quiet_points_remain_in_result_domain=True)

@lru_cache(None)
def delayed_checks():
    doc=fixture(['r2g6'],'''r zn[] d.r zh[d] c.r zo[d d] c.r ze[a d] c.r zc[a d] c.r zr[d] c.
q[k r2g6[k zn[] p zh p zo p ze p zc b p[k zr[v p]]]].''')
    points=('past','now','future');acts=('one','two')
    def values(bits=(True,False,False,False,False,False,True,False,True)):
        return dict(zn=lambda:'now',zh=lambda p:p in points,zo=lambda f,l:f in points and l in points and points.index(f)<points.index(l),
            ze=lambda a,p:a in acts and p in points and bits[acts.index(a)*3+points.index(p)],
            zc=lambda a,p:p=='now' and a in acts and bits[6+acts.index(a)],zr=lambda p:p=='now' and bits[8])
    for bits in product((False,True),repeat=9):
        want=bits[8] and (bits[6] and (bits[0] or bits[1]) or bits[7] and (bits[3] or bits[4]))
        assert evaluate(doc,values(bits),acts,points,True)==[want],bits
    rows={}
    for name in ('earlier_effect','current_effect','future_only','split_event','lost_result','lost_cause','past_outside_history','now_outside_history','cycle'):
        v=values();want=name in ('earlier_effect','current_effect')
        if name=='current_effect':v['ze']=lambda a,p:(a,p)==('one','now')
        if name=='future_only':v['ze']=lambda a,p:(a,p)==('one','future')
        if name=='split_event':v['zc']=lambda a,p:(a,p)==('two','now')
        if name=='lost_result':v['zr']=lambda p:False
        if name=='lost_cause':v['zc']=lambda *args:False
        if name=='past_outside_history':v['zh']=lambda p:p!='past'
        if name=='now_outside_history':v['zh']=lambda p:p!='now'
        if name=='cycle':v['zo']=lambda f,l:f!=l
        actual=evaluate(doc,v,acts,points,True);assert actual==[want],(name,actual);rows[name]=actual
    refuse(doc,values(),('zh','zo','ze','zc','zr'),acts,points)
    return dict(combinations=512,cases=rows,unknown_inputs_refused=5,future_and_other_events_not_borrowed=True)

CLASSIFICATION='''r zkindrule[a d] c.r zkindform[a d] c.
d hd2[object a] e[b point[k zkindrule[v object v point]]].
d r2fg[object a] e[b point[k zkindform[v object v point]]].'''

def source_values(doc,variant='baseline'):
    values=previous.source_values(doc,boundary=True)
    def identity(scope,o,p,a):return scope=='anchor' and o in ('object','other') and p=='person' and a=='first'
    histories={'keep':('first','middle','last'),'stop':('first','released')}
    values.update(aa=lambda p:p=='person',hzzq=lambda:'judgment',hzzn=lambda n,p,s:(n,p,s)==('judgment','person','anchor'),
        hzzzh=lambda s,o,p,a,b,t:identity(s,o,p,a) and t in histories.get(b,()),
        hzzzi=lambda s,o,p,a,b,f,l:identity(s,o,p,a) and f in histories.get(b,()) and l in histories[b] and histories[b].index(f)<histories[b].index(l),
        hzzzl=lambda s,o,p,a,b,t:identity(s,o,p,a) and (b=='keep' and t in ('first','last') or b=='stop' and t in ('first','released')),
        zstate=lambda p,t:p=='person' and t in ('first','middle','last'))
    base_cause=values['g3']
    values['g3']=lambda a,p,d,s:base_cause(a,p,d,s) or (a,p,symbol(d),s)==('act','person','bf','middle')
    if variant=='middle_occasion':
        j=values['hzzzl'];values['hzzzl']=lambda s,o,p,a,b,t:j(s,o,p,a,b,t) or identity(s,o,p,a) and b=='keep' and t=='middle'
    if variant=='no_anchor_occasion':
        j=values['hzzzl'];values['hzzzl']=lambda s,o,p,a,b,t:t!='first' and j(s,o,p,a,b,t)
    if variant=='lost_gap_cause':values['g3']=base_cause
    if variant=='lost_gap_result':values['zstate']=lambda p,t:p=='person' and t in ('first','last')
    if variant=='outside_people':values['hzzn']=lambda *args:False
    if variant=='wrong_cause_act':values['g3']=lambda a,p,d,s:a=='other'
    if variant=='wrong_cause_person':values['g3']=lambda a,p,d,s:p=='other'
    if variant=='second_kind_missing':values['zkindform']=lambda *args:False
    if variant=='second_history_missing':
        h=values['hzzzh'];values['hzzzh']=lambda s,o,p,a,b,t:o=='object' and h(s,o,p,a,b,t)
    return values

@lru_cache(None)
def binding_checks():
    doc=fixture(['r2gc','r2ga','r2g7','wh'],'''r zobject[] a.r zperson[] a.r zanchor[] d.r zbranch[] d.r zpoint[] d.
q[t[k r2gc[]][k wh[]]].q[k r2ga[k wh[] k zobject[] k zperson[] k zanchor[]]].
q[k r2g7[k wh[] k zobject[] k zperson[] k zanchor[] k zbranch[] k zpoint[]]].''',
        CLASSIFICATION+'r zstate[a d] c.d bf[person a] e[b point[k zstate[v person v point]]].')
    rows={}
    for name in ('baseline','middle_occasion','no_anchor_occasion','lost_gap_cause','lost_gap_result','outside_people','wrong_cause_act','wrong_cause_person','second_kind_missing','second_history_missing'):
        v=source_values(doc,name);v.update(zbranch=lambda:'keep',zpoint=lambda:'middle')
        effect=name not in ('lost_gap_cause','lost_gap_result','wrong_cause_act','wrong_cause_person')
        profile=effect and name not in ('middle_occasion','no_anchor_occasion')
        want=[profile and name not in ('outside_people','second_kind_missing','second_history_missing'),profile,effect]
        actual=evaluate(doc,v,previous.BOUNDARY_PEOPLE,SCENES,True);assert actual==want,(name,actual,want);rows[name]=actual
    v=source_values(doc);v.update(zbranch=lambda:'keep',zpoint=lambda:'middle')
    refuse(doc,v,('hzzzl','hzzzh','hzzzi','hzzn','g3','dg','zstate'),previous.BOUNDARY_PEOPLE,SCENES)
    return dict(cases=rows,unknown_inputs_refused=7,classification_and_capacity_boundaries_isolated=True,same_object_person_history_and_activity_required=True)

@lru_cache(None)
def native_checks():
    doc=fixture(['r2g7','r2ex','wh'],'''r zobject[] a.r zperson[] a.r zanchor[] d.r zbranch[] d.r zpoint[] d.
q[t[k r2ex[k zobject[] k zperson[]]][k zpoint[]]].
q[k r2g7[k wh[] k zobject[] k zperson[] k zanchor[] k zbranch[] k zpoint[]]].''')
    rows={}
    for lost in (False,True):
        v=previous.source_values(doc,boundary=False);v.update(zbranch=lambda:'keep',zpoint=lambda:'last')
        occurrence=v['dg'];cause=v['g3']
        v['dg']=lambda a,t:t!='last' and occurrence(a,t)
        if lost:v['g3']=lambda a,p,d,t:t!='last' and cause(a,p,d,t)
        actual=evaluate(doc,v,previous.previous.PEOPLE,previous.previous.SCENES,True)
        assert actual==[False,not lost],actual;rows['lost_cause' if lost else 'earlier_effect_without_current_use']=actual
        print('native '+str(lost)+' checked',flush=True)
    return dict(cases=rows,native_use_capacity_and_delayed_cause_executed=True,whole_generic_family_not_evaluated_with_native_capacity=True)

@lru_cache(None)
def presentation_checks():
    doc=fixture(['r2ge'],'q[k r2ge[]].')
    for bits in product((False,True),repeat=5):
        v=previous.presentation_values(doc,bits)
        v['uc']=lambda n,a,d,s:bits[0] and (n,a,json.loads(d.syntax),s)==('third','author',{'kind':'call','symbol':'r2gc','arguments':[]},'now')
        v['rbt']=lambda n,a,t,d,s:bits[1] and (n,a,symbol(t),symbol(d),s)==('third','author','r2gd','h2b','now')
        assert evaluate(doc,v,previous.PRESENTATION_PEOPLE,('now',),True)==[all(bits)],bits
    baseline=dict(v)
    bad=dict(v);bad['uc']=lambda n,a,d,s:json.loads(d.syntax).get('symbol')=='r2fz'
    assert evaluate(doc,bad,previous.PRESENTATION_PEOPLE,('now',),True)==[False]
    bad=dict(v);bad['rbt']=lambda n,a,t,d,s:symbol(t)=='r2g3'
    assert evaluate(doc,bad,previous.PRESENTATION_PEOPLE,('now',),True)==[False]
    refuse(doc,baseline,('uc','rbt','rbf','ibbdenotes','ibbclarifies','ue'),previous.PRESENTATION_PEOPLE,('now',))
    return dict(combinations=32,old_assertion_and_depiction_rejected=True,unknown_inputs_refused=6,world_contents_not_executed_by_attribution=True)

def reading():
    old=read(PREVIOUS_READING)
    paths={INDEX,PARENT,PARENT_BASIS,FULL,BASIS,PREVIOUS_READING,*PRIOR,previous.FIRST,previous.SECOND,previous.INVENTORY}
    return dict(status='third_sentence_occasion_continuation_candidate',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=old['source'],selection=selection_binding(catalog(),[10,52]),
        decision='適用局面で使い続ける条件と、使用のない時点にも以前の同じ活動から残る因果的結果を結ぶ。第三文の通しの意味一致判断は未完。',
        interpretation_limits=LIMITS,preceding_reading=PREVIOUS_READING,
        references=[dict(url='https://korpora.org/Kant/aa08/036.html',title='Kant AA VIII036',accessed='2026-10-20',use='第三文と続く離脱仮定を照合。局面ごとの継続は採用する解釈であり、一意に指定された読解とはしない。')],
        revised_statement_indices=[52],preserved_reviewed_sentence_characters=247,new_verified_sentence_characters=0,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-10]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert len(new.document['statements'])==len(old.document['statements'])==54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[52]
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        row=read(path);ids=[s['index'] for s in row['selection']['statements']]
        assert row['selection']==selection_binding(old,ids)==selection_binding(new,ids)
    for p,ids in ((previous.FIRST,[51]),(previous.SECOND,[11,12])):
        row=read(p);validate_hashes(ROOT,row['source_sha256']);assert row['selection']==selection_binding(new,ids)
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    assert closure(new.document,['r2fy','r2fh','r2ev','r2ew','ho2','h3b'])==closure(old.document,['r2fy','r2fh','r2ev','r2ew','ho2','h3b'])
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert read(AUDIT)==reading()
    return dict(added_definitions=9,added_primitives=1,authored_statements=54,preserved_statements=53,revised_statement_indices=[52],
        preserved_review_selections=12,reviewed_nonblank_characters=2212,preserved_reviewed_sentence_characters=247,roundtrips=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,body in build().items():write_exact(ROOT/p,body)
    write_exact(ROOT/AUDIT,encoded(reading()))

def build_report():
    results={}
    for name,fn in [('profile',profile_checks),('delayed',delayed_checks),('binding',binding_checks),('native',native_checks),('presentation',presentation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    record=reading();paths=set(build())|set(catalog().source_sha256)|set(record['source_sha256'])|{
        AUDIT,DOC,'scripts/compose_occasional_continuation.py','scripts/check_occasional_continuation.py','scripts/register_occasional_continuation.py','tests/test_occasional_continuation.py','scripts/compose_limits.py'}
    for p in PRIOR:paths.update(read(p)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='occasion_continuation_and_delayed_effect_candidate_checked',document=FULL,**results,
        alignment=dict(**record['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_covered_characters=0,new_verified_sentence_characters=0,
        preserved_reviewed_sentence_characters=247,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
