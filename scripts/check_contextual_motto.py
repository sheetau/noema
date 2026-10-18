"""Check the adopted motto and the current opening's integrated dependencies."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_contextual_motto import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,parent,build,closure,replace_symbols

REPORT='reports/contextual-motto-v1.json'
READING='data/contextual-motto-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','method','faculty','act','otheract','author','first','second','third','latin','german','conclusion')


def unknown(*args):raise ValueError('Unknown contextual motto input')
def is_ref(code,name):return code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


def evaluate(doc,values,domain=DOMAIN,scenes=('now','other')):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=20000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def directive_checks():
    doc=fixture(['hzsi','hzs6','bm','ao'],'r zscene[] d.'+
        'q[t[o[k hzsi[k ao[]]]][k zscene[]]].q[t[o[k hzs6[k ao[]]]][k zscene[]]].q[t[k bm[k ao[]]][k zscene[]]].')
    rows=[]
    def model(bits=(True,True,True,True),use=False,variant='baseline'):
        courage,attempt,actor,occurs=bits;v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(ao=lambda:'person',zscene=lambda:'now',
            hzio=lambda p,g,s:courage and (p,s)==('other' if variant=='other_person' else 'person','other' if variant=='other_scene' else 'now') and is_ref(g,'bk' if variant=='old_goal' else 'bm'),
            f5=lambda p,a,g,s:attempt and (p,a,s)==('person','otheract' if variant=='other_attempt' else 'act','now') and is_ref(g,'bb' if variant=='independent_goal' else 'bm'),
            df=lambda p,a,s:actor and (p,a,s)==('person','act','now'),dg=lambda a,s:occurs and (a,s)==('act','now'),
            ab=lambda f,p,s:(f,p,s)==('faculty','other' if variant=='other_owner' else 'person','now'),
            ac=lambda p,f,a,s:use and (p,f,a,s)==('person','faculty','act','now'))
        return v
    for bits in product((False,True),repeat=4):
        for use in (False,True):
            actual=evaluate(doc,model(bits,use));assert actual==[all(bits),False,use],(bits,use,actual);rows.append(actual)
    contrasts={}
    for variant in ('other_person','other_scene','old_goal','other_attempt','independent_goal','other_owner'):
        actual=evaluate(doc,model(use=True,variant=variant))
        expected=[variant=='other_owner',False,variant!='other_owner'];assert actual==expected,(variant,actual);contrasts[variant]=actual
    quoted=deepcopy(doc);quoted['statements']=doc['statements'][:2];v=model();v['ab']=v['ac']=unknown
    assert evaluate(quoted,v)==[True,False]
    for name in ('hzio','f5','df','dg'):
        v=model();v[name]=unknown
        try:evaluate(quoted,v)
        except ValueError as e:assert 'Unknown contextual motto' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=len(rows),contrasts=contrasts,unknown_inputs_refused=4,
        target_success_not_required=True,old_competence_goal_not_used=True,uncached_and_unlowered=True)


def presentation_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));nodes=('first','second','third','latin','german','conclusion');rows={}
    variants=('baseline','old_latin','old_motto','swapped_quotes','reverse_explanation','other_author','other_context','missing_condition','reverse_order','missing_conclusion')
    for variant in variants:
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update({n:(lambda value=value:value) for n,value in zip(('wa','wb','wc','wd','we','wf','wg'),('author',*nodes))});v['wh']=lambda:'now'
        def context(a,c):return (a,c)==('other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'now')
        def define(n,a,code,c):return context(a,c) and is_ref(code,{'first':'bi','second':'bf'}.get(n))
        def quoted(n,a,code,c):
            expected={'latin':'hzs6' if variant=='old_latin' else 'hzsi','german':'bn'}
            if variant=='swapped_quotes':expected={'latin':'bn','german':'hzsi'}
            return context(a,c) and json.loads(code.syntax)==dict(kind='call',symbol=expected.get(n),arguments=[dict(kind='call',symbol='ao',arguments=[])])
        def claim(n,a,code,c):
            if variant=='missing_condition' and n=='third' or variant=='missing_conclusion' and n=='conclusion':return False
            return context(a,c) and json.loads(code.syntax)==dict(kind='call',symbol={'third':'rqrk','conclusion':'hzsa' if variant=='old_motto' else 'hzsk'}.get(n),arguments=[])
        v.update(ua=define,ub=quoted,uc=claim,
            ue=lambda a,b,c:c=='now' and a in nodes and b in nodes and (nodes.index(a)>nodes.index(b) if variant=='reverse_order' else nodes.index(a)<nodes.index(b)),
            uf=lambda a,x,y,c:context(a,c) and (x,y)==(('german','latin') if variant=='reverse_explanation' else ('latin','german')),
            ud=lambda a,p,n,c:context(a,c) and n=='conclusion' and [x for x in DOMAIN if p(x)]==list(nodes[:-1]))
        actual=evaluate(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    motto=fixture(['hzsk'],'r zscene[] d.q[t[k hzsk[]][k zscene[]]].')
    for variant in ('baseline','old_latin','german_only','other_property','reversed'):
        v={d['name']:unknown for d in motto['declarations'] if d['kind']=='primitive'};v['zscene']=lambda:'now'
        def relation(parts,property_code,scene):
            expected={'baseline':['hzsi','bn'],'old_latin':['hzs6','bn'],'german_only':['bn'],'other_property':['hzsi','bn'],'reversed':['bn','hzsi']}[variant]
            return scene=='now' and is_ref(property_code,'bf' if variant=='other_property' else 'bi') and [json.loads(x.syntax)['symbol'] for x in parts.items]==expected
        v['ga']=relation;assert evaluate(motto,v)==[variant=='baseline'],variant
    return dict(cases=rows,motto_contrasts=5,quoted_world_inputs_remain_unknown=True)


def integrated_conditions():
    doc=fixture(['bd','rqrj','rqrk'],'r zp[] a.r zs[] d.q[k bd[k zp[] k zs[]]].q[k rqrj[k zp[] k zs[]]].q[t[k rqrk[]][k zs[]]].')
    rows=[]
    def model(ability,deficits,cause,imputed,intellect=False,intellect_cause=False):
        v={d['name']:(lambda *args:False) for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(zp=lambda:'person',zs=lambda:'anchor',aa=lambda p:p=='person',
            ab=lambda f,p,s:(f,p,s)==('faculty','person','result'),ac=lambda p,f,a,s:ability and (p,f,a,s)==('person','faculty','act','result'),
            ae=lambda p,m,s:(p,m,s)==('person','method','trial'),af=lambda p,m,s,t:(p,m,s,t)==('person','method','trial','result'),
            ap=lambda p,m,s,t:(p,m,s,t)==('person','method','trial','result'),
            hzsc=lambda p,a,s:(p,a,s)==('person','anchor','trial'),hzsd=lambda p,a,s:(p,a,s)==('person','anchor','trial'),
            hzse=lambda p,s:(p,s)==('person','trial'),hzsg=lambda p,m,a,s:(p,m,a,s)==('person','method','anchor','trial'),
            hzsh=lambda p,m,a,s:(p,a,s)==('person','anchor','trial'),
            hzin=lambda p,g,s:not deficits,hzio=lambda p,g,s:not deficits,hzip=lambda p,g,s:not intellect,
            hzie=lambda p,g,q,r,s:p==q=='person' and is_ref(r,'bf') and (cause and is_ref(g,'rqrh') or intellect_cause and is_ref(g,'rqri')),
            hziq=lambda p,g,s:imputed and p=='person' and is_ref(g,'bf'))
        return v
    for bits in product((False,True),repeat=4):
        ability,deficits,cause,imputed=bits;condition=not ability and deficits and cause;blame=not ability and imputed
        actual=evaluate(doc,model(*bits),domain=('person','method','faculty','act'),scenes=('anchor','trial','result'))
        assert actual==[condition,blame,not condition or blame],(bits,actual);rows.append(actual)
    for intellect,intellect_cause in product((False,True),repeat=2):
        actual=evaluate(doc,model(False,True,True,False,intellect,intellect_cause),domain=('person','method','faculty','act'),scenes=('anchor','trial','result'))
        condition=not(intellect and intellect_cause);assert actual==[condition,False,not condition],actual
    return dict(combinations=len(rows),understanding_cause_contrasts=4,current_capacity_and_cause_and_imputation_executed=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-4]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert new.document['statements'][1]==replace_symbols(old.document['statements'][1],{'hzsb':'hzsl'})
    assert all(a==b for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if i!=1)
    latin={d['name'] for d in closure(new.document,['hzsi'])};assert not latin&{'bk','yb','ya','fa','fb','fc','fd','fe','xd'}
    core=parse((ROOT/CORE).read_text(encoding='utf-8'));assert not {d['name'] for d in core['declarations']}&{'bk','yb','hzs6'}
    idx=json.loads((ROOT/'data/semantic-review-index-v25.json').read_text(encoding='utf-8'))
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));indices=[x['index'] for x in r['selection']['statements']]
        assert selection_binding(old,indices)==r['selection']==selection_binding(new,indices)
    for p in (FULL,CORE):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(new_definitions=4,new_primitives=0,changed_statement_indices=[1],unchanged_statements=34,
        eight_review_bindings_preserved=True,old_competence_test_absent_from_active_opening=True,roundtrips=True,
        core_characters=len((ROOT/CORE).read_text(encoding='utf-8')),previous_core_characters=len((ROOT/'examples/v016/exercise-capacity-core.noema').read_text(encoding='utf-8')))


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0008')
    return dict(status='adopted_author_gloss_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])]),
        references=['https://korpora.org/Kant/aa08/035.html','https://alatius.com/ls/index.php?met=up&ord=sapio','https://dcc.dickinson.edu/grammar/latin/complementary-infinitive'],
        facsimile=dict(path='artifacts/publication-header-v1/page-481.jpg',visually_inspected=True,observation='第一段落の全体と、ラテン語・ドイツ語・標語の連続を視認した。'),
        decision='この文脈でのsapereは、直後の著者自身の説明に沿ってbmの自分の理解力の使用と読む。audeは同じ本人がその目標へ勇気を持って取り組む要求としてhzs5で表す。',
        reason='語義資料の分別・理解の意味はこの読みを許すが、特定範囲の全事柄に理由ある判断を成功させる方法の存在までは要求していない。旧bkのその条件を外す。文法資料は同一主体の接続を支え、カントのドイツ語説明がこの箇所での目標を指定する。',
        rejected_additions=['理由を用いた支持付き判断の全対象への能力試験','能力の習得を呼びかけの目標とすること','理解力使用の実際の成功','ラテン語の全用法を同じ意味にすること'],
        interpretation_limit='著者の説明に即した文脈的な翻訳判断であり、独立したラテン語の全語義や音韻・原綴りの再現を認定しない。二つの引用の位置と命令の違いは保存する。',
        binding=selection_binding(catalog(),[1]),runtime_lexical_lookup=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,'artifacts/publication-header-v1/page-481.jpg','data/latin-motto-review-v1.json','data/courageous-undertaking-reading-v1.json')})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('directives',directive_checks),('presentation',presentation_checks),('integrated_conditions',integrated_conditions),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading
    prior=json.loads((ROOT/'reports/exercise-capacity-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,
        'reports/exercise-capacity-v1.json','scripts/compose_contextual_motto.py','scripts/check_contextual_motto.py','tests/test_contextual_motto.py','docs/contextual-motto-v1.md','docs/opening-paragraph-review-v1.md'}
    u=reading['source'];alignment=dict(unit=u['unit'],unit_sha256=u['unit_sha256'],range=[382,394],source=u['text'][382:394],definitions=list(MEANINGS),
        status='partial_adopted_author_gloss_reading',full_semantic_equivalence=False)
    return dict(status='contextual_motto_checked_separately_from_whole_unit_judgment',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--reading-only',action='store_true');cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()))
    if args.reading_only:print('Contextual Latin reading recorded',flush=True);return
    report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Contextual motto and current opening dependencies checked',flush=True)


if __name__=='__main__':main()
