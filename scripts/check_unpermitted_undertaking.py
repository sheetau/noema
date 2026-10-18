"""Keep missing permission, prohibition, undertaking and source scope distinct."""
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
from scripts.compose_unpermitted_undertaking import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,parent,build,closure
from scripts.check_prevented_attempt import DOMAIN,SCENES,unknown,ref
from scripts.check_confinement_depiction import target_model

REPORT='reports/unpermitted-undertaking-v1.json'
READING='data/unpermitted-undertaking-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,model,domain=DOMAIN,scenes=SCENES,memoize=True):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def undertaking_code(code,goal):
    return code.rank==0 and json.loads(code.syntax)==dict(kind='apply',function=dict(kind='function_ref',symbol='hzta'),
        arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=goal))])


PARAMS='r zperson[] a.r zsource[] a.r zrole[] a.r zscene[] d.r zsuccess[a d] c.'
GOALS='d zgoal[person a] e[b scene[k zsuccess[v person v scene]]].d zothergoal[person a] e[b scene[k zsuccess[v person v scene]]].'
GENERIC_CODE='o a[r[p hzta]][o r[r[p zgoal]]]'


def norm_document():
    return fixture(['hztc','rjq'],PARAMS+GOALS+
        'q[t[k hztc[k zsource[] k zperson[] k zrole[] r[p zgoal]]][k zscene[]]].'+
        'q[k rjq[k zsource[] k zperson[] k zrole[] '+GENERIC_CODE+' l[a][k zperson[]] e[n p a b][n p a b] k zscene[] p hztb p h7k p h7l]].'+
        'q[t[c[k hzta[r[p zgoal]]][l[a][k zperson[]]]][k zscene[]]].q[t[k zgoal[k zperson[]]][k zscene[]]].')


def generic_model(doc,permitted=False,forbidden=False,courage=True,attempt=True,success=False,variant='baseline'):
    model={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def matches(source,person,role,description,bindings,polarity,scene):
        return (source,person,role,bindings.items,polarity,scene)==(
            'other' if variant=='other_source' else 'source','other' if variant=='other_person' else 'person',
            'other' if variant=='other_role' else 'role',('other',) if variant=='other_binding' else ('person',),
            variant!='negative_polarity','other' if variant=='other_scene' else 'now') and undertaking_code(description,'zothergoal' if variant=='other_goal' else 'zgoal')
    model.update(zperson=lambda:'person',zsource=lambda:'source',zrole=lambda:'role',zscene=lambda:'now',zsuccess=lambda p,s:success,
        h7l=lambda *args:permitted and matches(*args),
        h7k=lambda source,person,role,description,bindings,polarity,scene:forbidden and not polarity,
        hzio=lambda p,g,s:courage and (p,s)==('person','now') and ref(g,'zgoal'),
        f5=lambda p,a,g,s:attempt and (p,a,s)==('person','act','now') and ref(g,'zgoal'),
        df=lambda p,a,s:(p,a,s)==('person','act','now'),dg=lambda a,s:(a,s)==('act','now'))
    return model


def norm_checks():
    doc=norm_document();count=0;domain=('person','other','source','role','act');times=('now','other')
    for permitted,forbidden,courage,attempt,success in product((False,True),repeat=5):
        actual=evaluate(doc,generic_model(doc,permitted,forbidden,courage,attempt,success),domain,times,False)
        assert actual==[not permitted,forbidden,courage and attempt,success],(permitted,forbidden,courage,attempt,success,actual);count+=1
    contrasts={}
    for variant in ('baseline','other_source','other_person','other_role','other_binding','negative_polarity','other_scene','other_goal'):
        actual=evaluate(doc,generic_model(doc,permitted=True,variant=variant),domain,times,False)
        assert actual==[variant!='baseline',False,True,False],(variant,actual);contrasts[variant]=actual
    quoted=deepcopy(doc);quoted['statements']=doc['statements'][:1]
    model=generic_model(quoted)
    for name in ('h7k','hzio','f5','df','dg','zsuccess'):model[name]=unknown
    assert evaluate(quoted,model,domain,times,False)==[True]
    model['h7l']=unknown
    try:evaluate(quoted,model,domain,times,False)
    except ValueError as e:assert 'Unknown prevention' in str(e)
    else:raise AssertionError('Unknown allowance became its absence')
    return dict(combinations=count,contrasts=contrasts,permission_does_not_execute_undertaking=True,
        missing_permission_not_prohibition=True,unknown_permission_refused=True,uncached_native_definitions=True)


def binding_checks():
    suffix=PARAMS+GOALS
    for bindings in ('l[a][]','l[a][k zperson[]]','l[a][k zperson[] k zsource[]]','l[a][k zsource[]]'):
        suffix+='q[t[c[k hzta[r[p zgoal]]]['+bindings+']][k zscene[]]].'
    suffix+='q[e['+GENERIC_CODE+'][r[c[p hzta][r[p zgoal]]]]].'
    doc=fixture(['hzta'],suffix);model=generic_model(doc)
    actual=evaluate(doc,model,('person','other','source','role','act'),('now','other'),False)
    assert actual==[False,True,False,False,True],actual
    # The constructor preserves a closed goal's syntax without executing it.
    quote=deepcopy(doc);quote['statements']=doc['statements'][-1:]
    for key in model:model[key]=unknown
    assert evaluate(quote,model,('person',),('now',),False)==[True]
    return dict(empty_extra_and_other_bindings_rejected=True,closed_goal_preserved=True,quotation_world_inputs_unknown=True)


def source_checks():
    doc=fixture(['hztf','hzth','hzsp','hzss'],
        'r zp[] a.r za[] d.r zb[] d.'+
        'q[t[k hztf[k db[]]][k za[]]].q[t[k hzth[k zp[]]][k za[]]].'+
        'q[t[k hzsp[k db[]]][k za[]]].q[t[k hzss[k zp[]]][k za[]]].')
    variants=('baseline','allowed_same_person','allowed_other_recipient','allowed_only_now','allowed_other_source','allowed_other_role',
        'allowed_other_goal','allowed_other_bindings','allowed_negative_polarity','allowed_only_late',
        'blocking_now','actually_attempts','no_warning','no_blocking_cause','no_supervision')
    rows={}
    for variant in variants:
        inherited=variant if variant in ('blocking_now','actually_attempts','no_blocking_cause','no_supervision') else 'baseline'
        model=target_model(doc,inherited);model.update(hztd=lambda:'supervised',h7k=unknown,hzio=unknown,f5=unknown)
        def allowed(source,person,role,description,bindings,polarity,scene):
            if not variant.startswith('allowed_'):return False
            return (source,person,role,bindings.items,polarity,scene)==(
                'foreign' if variant=='allowed_other_source' else 'guards',
                'other' if variant=='allowed_other_recipient' else 'person',
                'foreign' if variant=='allowed_other_role' else 'supervised',
                ('other',) if variant in ('allowed_other_recipient','allowed_other_bindings') else ('person',),
                variant!='allowed_negative_polarity',
                'actual' if variant=='allowed_only_now' else 'belief' if variant=='allowed_only_late' else 'prior') and undertaking_code(description,'bm' if variant=='allowed_other_goal' else 'bb')
        model['h7l']=allowed
        if variant=='no_warning':
            occurs=model['dg'];model['dg']=lambda a,s:False if a=='warning' else occurs(a,s)
        actual=evaluate(doc,model,DOMAIN+('supervised',))
        old_full=variant not in ('blocking_now','actually_attempts','no_warning','no_blocking_cause')
        old_target=variant not in ('blocking_now','actually_attempts','no_blocking_cause','no_supervision')
        expected=[old_full and variant not in ('allowed_same_person','allowed_other_recipient'),
            old_target and variant!='allowed_same_person',old_full,old_target]
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    return dict(cases=rows,same_person_and_obstruction_time=True,other_recipient_permission_not_hidden=True,
        world_courage_and_attempt_description_unknown=True,pure_memoization_for_temporal_search=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','old_timeline','old_figure_target','reversed_figure','other_author','other_context','other_clause','reverse_order'):
        model={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(wa=lambda:'author',wh=lambda:'context',hzsq=lambda:'clause',hzst=lambda:'relative',dq=lambda:'previous')
        def same(a,s):return (a,s)==('other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context')
        def claim(n,a,c,s):return same(a,s) and n==('other' if variant=='other_clause' else 'clause') and json.loads(c.syntax)==dict(kind='call',symbol='hzsp' if variant=='old_timeline' else 'hztf',arguments=[dict(kind='call',symbol='db',arguments=[])])
        def figure(n,a,t,d,s):return same(a,s) and n=='relative' and ref(t,'zbf' if variant=='reversed_figure' else 'hzss' if variant=='old_figure_target' else 'hzth') and ref(d,'hzth' if variant=='reversed_figure' else 'zbf')
        model.update(uc=claim,qa=figure,ue=lambda a,b,s:(a,b,s)==(('clause','previous','context') if variant=='reverse_order' else ('previous','clause','context')))
        actual=evaluate(doc,model,('author','clause','relative','previous','other'),('context',))
        expected=[variant not in ('old_timeline','other_author','other_context','other_clause','reverse_order'),
            variant not in ('old_figure_target','reversed_figure','other_author','other_context')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(cases=rows,all_world_and_normative_inputs_unknown=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-9]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    changed=[i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]
    assert changed==[35,36] and len(new.document['statements'])==37
    used={d['name'] for d in closure(new.document,['hztg','hzti'])};assert {'rjp','hzs4','hzta','hztc','hzsn'}<=used
    assert not used&{'er','ek','rx','eh','q3','hzsr','hzsu'}
    idx=json.loads((ROOT/'data/semantic-review-index-v28.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert not set(indices)&set(changed)
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for path in (FULL,CORE):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(new_definitions=8,new_context_references=1,new_semantic_relations=0,changed_statement_indices=changed,
        other_statements_preserved=35,nine_review_bindings_preserved=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='wagen durften';start=unit['text'].index(phrase)
    return dict(status='explicit_permission_absence_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        references=['https://korpora.org/Kant/aa08/035.html','https://grammis.ids-mannheim.de/terminologie/155','https://grammis.ids-mannheim.de/verbs/view/401128'],
        decision='後見人の監督下で、自立した理解力使用へ勇気を伴って取り組むことへの許容がないという対象側の読みを採る。先行する阻止と同じ人・同じ時点へ結ぶ。',
        reasoning='原文のdurftenを許容に関する様相として、wagenの対象となる取り組みの外側に置く。現代語資料は許可と能力を区別する参考であり、1784年の唯一の解釈を決める証拠ではない。',
        limits=['積極的許容の欠如rjpを採り、明示的な禁止命令rjqや衝突のない許容の欠如rjrとは区別する。',
            '原文から法的制度・制裁・正当な権威を補わず、許容の欠如が阻止の唯一の原因とも断定しない。',
            '身体的な一歩、jaの強調、慎重さ・穏順さ・皮肉、身体的歩行と転倒、段落全体の確認は残る。',
            '目標の引用構成を用い、翻訳時の辞書照合・生成モデル・個別修正ルールは追加しない。'],
        whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[35,36]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('norm',norm_checks),('binding',binding_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    old=json.loads((ROOT/'reports/prevented-attempt-v1.json').read_text(encoding='utf-8'))
    assert any(x['start']<=s['range'][0]<s['range'][1]<=x['end'] for x in old['alignment']['segments'])
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS),status='partial_explicit_permission_reading',full_semantic_equivalence=False)
    prior=json.loads((ROOT/'reports/confinement-depiction-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,
        'reports/confinement-depiction-v1.json','scripts/check_confinement_depiction.py','scripts/check_prevented_attempt.py',
        'scripts/compose_unpermitted_undertaking.py','scripts/check_unpermitted_undertaking.py','tests/test_unpermitted_undertaking.py','docs/unpermitted-undertaking-v1.md'}
    return dict(status='permission_absence_bound_to_prior_obstruction',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Unpermitted undertaking and source scope checked',flush=True)


if __name__=='__main__':main()
