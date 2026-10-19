"""Check actual capacity, bodily experiences, prospects and their quoted depiction."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_walking_acquisition import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v80.json'
REPORT='reports/walking-acquisition-v1.json'
AUDIT='data/walking-acquisition-reading-v1.json'
DOC='docs/walking-acquisition-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PEOPLE=('person','other','process','one','two','method','act')
SCENES=('actual','start','first','fallone','second','falltwo','end','precase','postcase','success','failure','otherend')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots.split()),statements=[])
    return parse(format_graph(d,'compact')+suffix)


def model(d,variant='baseline',body=True,mind=True):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    when=lambda event:'first' if event=='one' else 'second'
    result=lambda event:'fallone' if event=='one' else 'falltwo'
    def goal(g):return symbol(g)=='bb' if variant=='wrong_task_profile' else symbol(g)=='zal'
    def cases(p,a,s):return p=='person' and (a,s) in (('start','precase'),('end','postcase'))
    def preserved(p,a,s):return cases(p,a,s) and not(variant=='changed_basis' and a=='start')
    def opportunity(p,s):return p=='person' and s in ('precase','postcase') and not(variant=='no_external_opportunity' and s=='postcase')
    def scope(p,m,a,s):return cases(p,a,s) and m=='method' and variant!='training_only'
    def checked(p,m,a,s):return cases(p,a,s) and not(variant=='unclassified' and a=='end')
    def available(p,m,s):return (p,m)==('person','method') and s in ('precase','postcase')
    def outcomes(p,m,s,t):return available(p,m,s) and t in ('success','failure')
    def selected(p,m,s,t):
        if variant=='unassessed_before' and s=='precase' or variant=='unassessed_after' and s=='postcase':return False
        success=s=='postcase' or variant in ('already_capable','training_only')
        return available(p,m,s) and t==('success' if success else 'failure')
    def trial(p,e,g,s):
        return p==('other' if variant=='other_experiencer' else 'person') and e in ('one','two') and s==when(e) and (
            symbol(g)=='zal' and body and variant!='wrong_experience_task' or symbol(g)=='bb' and mind)
    def changes(e,a,b):return variant!='no_acquisition' and (e,a,b)==('process','start','end') or e in ('one','two') and (a,b)==(when(e),result(e))
    def affected(p,e,a,b):return p==('other' if variant=='other_changed_person' and e=='process' else 'person') and changes(e,a,b)
    v.update(zp=lambda:'person',zprocess=lambda:'process',zstart=lambda:'start',zend=lambda:'end',znow=lambda:'actual',
        aa=lambda p:p=='person',ae=available,af=outcomes,ap=selected,
        ab=lambda f,p,s:(f,p)==('act','person'),ac=lambda p,f,a,s:(p,f,a,s)==('person','act','act','success'),ad=lambda *args:False,
        hzsc=cases,hzsd=preserved,hzse=opportunity,hzsf=lambda *args:False,hzsg=scope,hzsh=checked,
        hzyf=lambda p,g,a,s:goal(g) and cases(p,a,s),
        hzyg=lambda p,g,a,s:goal(g) and preserved(p,a,s),
        hzyh=lambda p,g,s:goal(g) and opportunity(p,s),hzyi=lambda *args:False,
        hzyj=lambda p,g,m,a,s:goal(g) and scope(p,m,a,s),
        hzyk=lambda p,g,m,a,s:goal(g) and checked(p,m,a,s),
        zai=lambda p,a,s:(p,a,s)==('person','act','success'),
        zaj=lambda p,a,s:variant=='supported_only' and (p,a,s)==('person','act','success'),
        f5=trial,f6=lambda e,s:variant!='missing_fall_result' and e in ('one','two') and s==result(e),f7=when,
        fh=lambda process:SequenceValue(() if process!='process' or variant=='empty_experiences' else
            ('one','one') if variant=='duplicate_experience' else ('two','one') if variant=='reversed_experiences' else ('one','two'),'"individual"'),
        fi=lambda process:'start',fm=lambda count,context:context=='actual' and 1<=count<=(1 if variant=='too_many' else 3),
        fk=lambda e,p,process,a,b:variant!='no_contribution' and e in ('one','two') and
            (p,process,a,b)==('person','other' if variant=='foreign_contribution' else 'process','start','end'),
        fl=lambda p,a,s:variant!='empty_prospects' and (p,a)==('person','actual') and
            (s==('actual' if variant=='current_candidate' else 'end') or variant=='bad_extra_prospect' and s=='otherend'),
        tx=lambda a,b:(a,b)==('actual','end') or variant=='bad_extra_prospect' and (a,b)==('actual','otherend'),
        dd=lambda a,b:SCENES.index(a)<SCENES.index(b),dg=lambda e,s:e in ('one','two') and s==when(e),ag=changes,la=affected,
        hzui=lambda p,s:p=='person' and s in ('first','second'),
        hzuj=lambda p,s:p=='person' and s in ('fallone','falltwo'),
        hzuk=lambda p,e,a,b:(p==('other' if variant=='foreign_fall' else 'person')) and e in ('one','two') and (a,b)==(when(e),result(e)),
        hzul=lambda p,e,a,b:variant=='controlled_descent' and e in ('one','two') and (p,a,b)==('person',when(e),result(e)))
    return v


CAPACITY='r zp[] a.r zstart[] d.r zend[] d.q[t[k r2at[k zp[]]][k zstart[]]].q[t[k r2au[k zp[]]][k zstart[]]].q[t[k r2at[k zp[]]][k zend[]]].q[t[k r2au[k zp[]]][k zend[]]].'
ACQUISITION='r zp[] a.r zprocess[] a.r zend[] d.r znow[] d.q[k r2aw[k zp[] k zprocess[] k zend[] k znow[]]].'
PROSPECT='r zp[] a.r znow[] d.q[t[k fr[k zp[]]][k znow[]]].q[t[k r2ay[k zp[]]][k znow[]]].'


@lru_cache(None)
def capacity_checks():
    d=fixture('r2at r2au',CAPACITY);rows={}
    expected={'baseline':[True,False,True,True], 'already_capable':[True,True,True,True],
        'unassessed_before':[False,False,True,True], 'unassessed_after':[True,False,False,False],
        'unclassified':[True,False,False,False], 'changed_basis':[False,False,True,True],
        'no_external_opportunity':[True,False,False,False], 'wrong_task_profile':[False]*4,
        'training_only':[True,False,True,False], 'supported_only':[True,False,True,False]}
    for name,wanted in expected.items():
        actual=evaluate(d,model(d,name),PEOPLE,SCENES,True)
        assert actual==wanted,(name,actual,wanted);rows[name]=actual
    for name in ('hzyf','hzyg','hzyh','hzyi','hzyj','hzyk','ap'):
        v=model(d);v[name]=unknown
        try:evaluate(d,v,PEOPLE,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_refused=7,actual_walking_not_required=True,
        no_body_profile_borrowed_from_intellectual_task=True,pure_memoization=True)


@lru_cache(None)
def acquisition_checks():
    d=fixture('r2aw',ACQUISITION);rows={}
    for name in ('baseline','already_capable','unassessed_before','unassessed_after','empty_experiences',
        'duplicate_experience','reversed_experiences','too_many','no_contribution','foreign_contribution',
        'other_experiencer','other_changed_person','no_acquisition','missing_fall_result',
        'foreign_fall','controlled_descent','wrong_experience_task'):
        actual=evaluate(d,model(d,name),PEOPLE,SCENES,True)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
        print('acquisition '+name+' checked',flush=True)
    for name in ('fk','f5','hzul'):
        v=model(d);v[name]=unknown
        try:evaluate(d,v,PEOPLE,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_refused=3,native_body_capacity_and_falls_executed=True,
        same_person_experiences_process_and_endpoints=True,pure_memoization=True)


@lru_cache(None)
def prospect_checks():
    d=fixture('fr r2ay',PROSPECT);rows=[]
    for mind,body in product((False,True),repeat=2):
        actual=evaluate(d,model(d,body=body,mind=mind),PEOPLE,SCENES,True)
        assert actual==[mind,body],(mind,body,actual)
        rows.append(dict(intellectual_experiences=mind,bodily_experiences=body,values=actual))
    contrasts={}
    for name in ('empty_prospects','current_candidate','bad_extra_prospect'):
        actual=evaluate(d,model(d,name),PEOPLE,SCENES,True)
        assert actual==[False,False],(name,actual);contrasts[name]=actual
    for name in ('fl','tx'):
        v=model(d);v[name]=unknown
        try:evaluate(d,v,PEOPLE,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_contents=rows,contrasts=contrasts,unknown_inputs_refused=2,
        native_intellectual_and_bodily_prospects_executed=True,actual_acquisition_not_required=True,pure_memoization=True)


@lru_cache(None)
def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for name in ('baseline','other_author','other_node','other_context','reversed','only_fall','other_target'):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(fv=lambda:'node',wa=lambda:'author',wh=lambda:'context',
            qa=lambda n,a,t,b,s:(n,a,symbol(t),symbol(b),s)==(
                'other' if name=='other_node' else 'node','other' if name=='other_author' else 'author',
                'r2ay' if name=='reversed' else 'eu' if name=='other_target' else 'fr',
                'fr' if name=='reversed' else 'hzum' if name=='only_fall' else 'r2ay',
                'elsewhere' if name=='other_context' else 'context'))
        actual=evaluate(d,v,('node','author','other'),('context','elsewhere'))
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    v['qa']=unknown
    try:evaluate(d,v,('node','author','other'),('context','elsewhere'))
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown depiction became true')
    return dict(contrasts=rows,all_world_contents_unknown=True,unknown_inputs_refused=1,ordinary_evaluation=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    text='denn sie würden durch einigemahl Fallen wohl endlich gehen lernen';start=unit['text'].index(text)
    paths=(INDEX,INVENTORY,PARENT,PARENT_BASIS,FULL,BASIS,'reports/guarded-walking-reading-v1.json',
        'data/guarded-walking-reading-v1.json','data/falling-depiction-reading-v1.json',
        'reports/experience-acquisition-v1.json','reports/exercise-capacity-v1.json','reports/falling-depiction-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='partial_bodily_learning_prospect_connected',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(text)],text=text),
        decision='身体的な転倒経験から補助なしの足移動能力を得る見込みを合成し、同じ理由節の知的側の見込みの描写として追加する。',
        selection=selection_binding(catalog(),[50]),interpretation_limits=LIMITS,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        remaining=['würden・wohl・endlichの作用範囲と見込みの妥当性','危険の程度・萎縮・通常の回避を含む末尾一文','第二段落全体','二作品全文'],
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-13]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==51
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(PRIMITIVES)|set(MEANINGS)
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in review['selection']['statements']]
        assert review['selection']==selection_binding(old,ids)==selection_binding(new,ids)
    # The preceding six-sentence judgment remains bound to the same entries.
    previous=json.loads((ROOT/'reports/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT,previous['source_sha256'])
    for row in previous['preceding']['reviews'].values():
        binding=row['current_selection'];ids=[s['index'] for s in binding['statements']]
        assert binding==selection_binding(new,ids)
    sixth=json.loads((ROOT/'data/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))
    assert sixth['selection']==selection_binding(new,[s['index'] for s in sixth['selection']['statements']])
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    return dict(new_definitions=7,new_primitives=6,preserved_statements=50,total_statements=51,
        preserved_review_selections=11,preserved_reviewed_sentence_characters=1021,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('capacity',capacity_checks),('acquisition',acquisition_checks),('prospects',prospect_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_walking_acquisition.py','scripts/check_walking_acquisition.py','scripts/register_walking_acquisition.py',
        'tests/test_walking_acquisition.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_bodily_learning_prospect_with_native_capacity_and_fall_evidence',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
