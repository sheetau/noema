"""Review the complete guardian sentence under an explicit, fixed reading."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_guardian_reading import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure,focus_declaration
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_guardian_purpose import goal_key
from scripts.check_described_appraisals import source_model as appraisal_model
from scripts.fetch_guardian_reading_evidence import PATH as EVIDENCE,validate
from scripts.fetch_payment_reading_evidence import validate as validate_assurance

INDEX='data/semantic-review-index-v66.json'
REPORT='reports/guardian-reading-v1.json'
AUDIT='data/guardian-reading-v1.json'
DOC='docs/guardian-reading-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jn[] a.r ja[] a.r js[] d.r jtruth[d] c.r jproperty[a d] c.
d jclaim[] e[b scene[k jtruth[v scene]]].d jfocus[] e[b scene[k jtruth[v scene]]].
d jother[] e[b scene[k jtruth[v scene]]].
d jbase[person a] e[b scene[k jproperty[v person v scene]]].
d jadded[person a] e[b scene[k jproperty[v person v scene]]].
r jclaims[a a i[e] d] c.r jassures[a a i[e] i[e] d] c.
r jadds[a a i[e] i[h[a] e] i[h[a] e] d] c.
q[k rqyy[k jn[] k ja[] r[k jclaim[]] r[k jfocus[]] k js[] p jclaims p jassures]].
q[k rqyz[k jn[] k ja[] r[k jclaim[]] r[p jbase] r[p jadded] k js[] p jclaims p jadds]].
''')


def generic_values(claimed=True,assured=True,added=True,variant='baseline'):
    assurance=['node','author','jclaim','jfocus','context']
    addition=['node','author','jclaim','jbase','jadded','context']
    changes={'other_node':(0,'other'),'other_author':(1,'other'),'other_claim':(2,'jother'),
        'other_focus':(3,'jother'),'other_context':(4,'elsewhere')}
    if variant in changes:
        i,value=changes[variant];assurance[i]=value
    changes={'add_other_node':(0,'other'),'add_other_author':(1,'other'),'add_other_claim':(2,'jother'),
        'add_other_background':(3,'jadded'),'add_other_addition':(4,'jbase'),'add_other_context':(5,'elsewhere')}
    if variant in changes:
        i,value=changes[variant];addition[i]=value
    if variant=='reversed_addition':addition[3:5]=['jadded','jbase']
    return dict(jn=lambda:'node',ja=lambda:'author',js=lambda:'context',jtruth=unknown,jproperty=unknown,
        jclaims=lambda n,a,p,s:claimed and (n,a,s)==('node','author','context') and symbol(p) in (
            ('jclaim','jother') if variant=='two_claims' else ('jclaim',)),
        jassures=lambda n,a,p,q,s:assured and (n,a,symbol(p),symbol(q),s)==tuple(assurance),
        jadds=lambda n,a,p,q,r,s:added and (n,a,symbol(p),symbol(q),symbol(r),s)==tuple(addition))


DOMAIN=('node','author','person','other')
CONTEXTS=('context','elsewhere')


def generic_checks():
    rows=[]
    for claimed,assured,added in product((False,True),repeat=3):
        for truth in (False,True,None):
            v=generic_values(claimed,assured,added)
            v['jtruth']=unknown if truth is None else lambda s:truth
            v['jproperty']=unknown if truth is None else lambda p,s:truth
            actual=evaluate(generic(),v,DOMAIN,CONTEXTS)
            assert actual==[claimed and assured,claimed and added]
            rows.append(dict(claimed=claimed,assured=assured,added=added,world_truth=truth,values=actual))
    return dict(combinations=rows,world_content_not_executed=True,ordinary_evaluation=True)


def scope_checks():
    rows={}
    for name in ('other_node','other_author','other_claim','other_focus','other_context',
            'add_other_node','add_other_author','add_other_claim','add_other_background','add_other_addition',
            'add_other_context','reversed_addition'):
        actual=evaluate(generic(),generic_values(variant=name),DOMAIN,CONTEXTS)
        expected=[name.startswith('add_') or name=='reversed_addition',not (name.startswith('add_') or name=='reversed_addition')]
        assert actual==expected,(name,actual);rows[name]=actual
    # Two claims at the same node must not lend their framing to each other.
    v=generic_values(variant='two_claims')
    v['jassures']=lambda n,a,p,q,s:(n,a,symbol(p),symbol(q),s)==('node','author','jother','jfocus','context')
    v['jadds']=lambda n,a,p,q,r,s:(n,a,symbol(p),symbol(q),symbol(r),s)==('node','author','jother','jbase','jadded','context')
    assert evaluate(generic(),v,DOMAIN,CONTEXTS)==[False,False]
    same=deepcopy(generic());same['statements']=same['statements'][1:]
    same['statements'][0]['body']['arguments'][4]=deepcopy(same['statements'][0]['body']['arguments'][3])
    v=generic_values();v['jadds']=lambda *args:True
    assert evaluate(same,v,DOMAIN,CONTEXTS)==[False]
    for name in ('jclaims','jassures','jadds'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,DOMAIN,CONTEXTS)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(contrasts=rows,same_node_multiple_claims_not_conflated=True,
        same_description_not_an_addition=True,unknown_inputs_refused=3,ordinary_evaluation=True)


def source_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    names=('baseline','no_claim','no_order','no_female_depiction','no_benevolent_frame','no_critical_distance',
        'no_assurance','other_assured_claim','other_assured_focus','other_assured_group','other_assured_context',
        'no_addition','other_additive_claim','reversed_addition','actual_risk_as_addition','other_additive_context')
    for name in names:
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(dq=lambda:'node',wa=lambda:'author',wh=lambda:'text',t4=lambda:'payment',
            uc=lambda n,a,p,s:name!='no_claim' and (n,a,symbol(p),s)==('node','author','dp','text'),
            ue=lambda a,b,s:name!='no_order' and (a,b,s)==('payment','node','text'),
            du=lambda n,a,p,q,s:name!='no_female_depiction' and (n,a,symbol(p),symbol(q),s)==('node','author','dr','ds','text'),
            hzxs=lambda n,a,p,q,r,s:name!='no_benevolent_frame' and (n,a,symbol(p),symbol(q),symbol(r),s)==('node','author','dp','rqyl','rqyp','text'),
            hzxt=lambda n,a,p,q,r,s:name!='no_critical_distance' and (n,a,symbol(p),symbol(q),symbol(r),s)==('node','author','dp','rqyl','rqyp','text'),
            hzxu=lambda n,a,p,q,s:name!='no_assurance' and (n,a,symbol(p),goal_key(q),s)==(
                'node','author','un' if name=='other_assured_claim' else 'dp',
                ('do' if name=='other_assured_focus' else 'rqyx','mv' if name=='other_assured_group' else 'db'),
                'actual' if name=='other_assured_context' else 'text'),
            hzxv=lambda n,a,p,q,r,s:name!='no_addition' and (n,a,symbol(p),symbol(q),symbol(r),s)==(
                'node','author','un' if name=='other_additive_claim' else 'dp','ux' if name=='reversed_addition' else 'uy',
                'uy' if name=='reversed_addition' else 'uw' if name=='actual_risk_as_addition' else 'ux',
                'actual' if name=='other_additive_context' else 'text'))
        actual=evaluate(doc,v,('node','author','payment'),('text','actual'))
        expected=[name not in ('no_claim','no_order'),name!='no_female_depiction',
            name not in ('no_claim','no_benevolent_frame','no_critical_distance'),
            name in ('baseline','no_order','no_female_depiction','no_benevolent_frame','no_critical_distance')]
        assert actual==expected,(name,actual,expected);rows[name]=actual
    return dict(contrasts=rows,all_world_facts_unknown=True,current_four_statements_executed=True,
        assurance_focus_is_same_group_causal_content=True,ordinary_evaluation=True)


def fact_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,['uy','ux','uw','uz']),statements=[])
    text=format_graph(d,'compact')+'r za[] a.r zb[] d.'
    for name in ('uy','ux','uw','uz'):text+='q[t[k '+name+'[k za[]]][k zb[]]].'
    doc=parse(text);rows=[]
    for burden,judged,actual in product((False,True),repeat=3):
        v=appraisal_model(doc,burden=burden,believed_risk=judged,actual_risk=actual)
        values=evaluate(doc,v,('person','low','high'),('actual','belief','loss'))
        assert values==[burden,judged,actual,burden and judged],(burden,judged,actual,values)
        rows.append(dict(burden=burden,judged_risk=judged,actual_risk=actual,values=values))
    return dict(combinations=rows,current_appraisal_definitions_executed=True,
        burden_and_judgment_not_actual_danger=True,ordinary_evaluation=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    parts=[
        ('dependent_content','Daß ',['dp','do','rqyd'],'危険判断を述べる内容を、後半の目的的な働きかけの対象として読む。'),
        ('majority','der bei weitem größte Theil der Menschen ',['mv','hr','aa','u5','rqyc','u4'],'同じ人間の母集団の厳密な過半数で、文脈の強い程度基準も満たす範囲。数値の固定割合は補わない。'),
        ('included_class','(darunter das ganze schöne Geschlecht) ',['da','ro','dn','dr','ds','rq','du'],'文脈で女性とされる範囲の全員が含まれる。美しさは呼称としての描写であり、実際に美しい女性だけを選ばない。'),
        ('transition','den Schritt zur Mündigkeit, ',['up','uu','uw'],'各人が同じ自立的理解力使用の能力へ向かう活動。既に達成したことや身体的な一歩を追加しない。'),
        ('background','außer dem daß er beschwerlich ist, ',['uy','uu','uv','uz','rqyz','hzxv'],'その活動が骨の折れる水準にあるという著者の挿入説明を、追加の前に置く背景として扱う。後見人が負担自体を生じさせるとはしない。'),
        ('addition','auch ',['rqyz','hzxv','rqy2'],'同じ人々について負担の説明へ危険判断を付け加える提示。無順序の連言、時間順序、因果だけでは代用しない。'),
        ('judgment','für sehr gefährlich halte: ',['ux','uw','u2','u3','rm','ut'],'同じ活動を非常に危険だとみなす判断。候補は非空で、記述と評価対象を保持し、実際の危険性を断言しない。'),
        ('purpose_and_cause','dafür sorgen ',['do','rqyg','rqye','rqyd','hzie','rqyx'],'記述対象の後見人たちが同じ活動で同じ危険判断分布を目指し、その活動が実際にその分布へ寄与するという結果を伴う読み。'),
        ('assurance','schon ',['hzxu','rqyy','rqyx','rqy2'],'同じ後見人群の目的的な寄与の部分を確かなものとして提示する。既了・未来・唯一の原因・必然的な成功にはしない。'),
        ('guardians','jene Vormünder, ',['db','dk'],'文脈で指示された後見人群。現実の全後見人を一律に選ぶこと、固定の人数、指揮階層は補わない。'),
        ('highest_supervision','die die Oberaufsicht ',['di','rqyj','rqyi','hzxn'],'同じ対象への監督範囲で最高位にあること。同順位の最高位も許し、全員が全対象を担当するとはしない。'),
        ('targets','über sie ',['dj','dk','rp'],'同じ母集団で負担と危険判断を持つ人々を指すという読み。各後見人と各対象の少なくとも一つの結び付きを保つ。'),
        ('critical_evaluation','gütigst ',['rqyl','rqyp','rqyq','rqyr','hzxs','hzxt'],'同じ引受け行為を強い好意として描写しながら、その評価から批判的に距離を置く。実際の親切さやその反対を自動的に断言しない。'),
        ('prior_assumption','auf sich genommen haben.',['di','rqyl','de','dv','hzxo','dd'],'現在の立場と、同じ最高位を先行状況で実際に引き受けた行為を結ぶ。別の立場の引受け、単なる名乗り、継続保持、正当性、自発的発意まで補わない。'),
    ]
    text=''.join(p[1] for p in parts);start=unit['text'].index(text);pos=start;clauses=[]
    for name,phrase,definitions,interpretation in parts:
        clauses.append(dict(id=name,range=[pos,pos+len(phrase)],text=phrase,definitions=definitions,
            interpretation_ja=interpretation,status='reviewed_under_stated_reading'));pos+=len(phrase)
    paths=(INVENTORY,INDEX,PARENT,PARENT_BASIS,FULL,BASIS,EVIDENCE,'data/payment-reading-evidence-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg','data/guardian-purpose-reading-v1.json',
        'data/guardian-causation-evidence-v1.json','data/supervisory-rank-reading-v1.json',
        'data/benevolent-framing-reading-v1.json','data/directed-purpose-reading-v1.json',
        'reports/benevolent-framing-v1.json','reports/directed-purpose-v1.json')
    return dict(status='guardian_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,pos],text=text,
            nonblank_characters=sum(not c.isspace() for c in text)),clauses=clauses,
        selection=selection_binding(catalog(),[7,8,44,45]),
        context=dict(population='同じmvと文脈の程度基準を固定する。女性の範囲は実際の美しさで絞らない。',
            guardians='本文の活動に参加する指示された人々をdbとし、各人に同じ目標を帰属する分配的な読みを採る。',
            purpose_choice='単純な全員目的と方向付けを伴う分担は区別できる。本文は具体的な指揮関係を指定しないため、比較候補rqywは採用せず現行doを保つ。これは唯一の集合的読解であるという証明ではない。',
            result='sorgenだけから成功を導かず、前後の依存維持の描写と合わせ、判断が成立し働きかけが実際に寄与する読みを採る。',
            burden='負担は著者の挿入説明、危険性は人々の判断として区別する。後見人の目的・因果結果は危険判断分布へ限定する。',
            assurance='schonを確言と読む。焦点はdoの目的的寄与の部分式に固定し、監督順位や負担を焦点内容へ混ぜない。',
            addition='負担uyを背景とし、危険判断uxを追加する。実際の危険性uwへの追加としては扱わない。',
            attribution='著者による主張・描写・評価態度の帰属であり、その歴史的な真理や正当性の認定ではない。'),
        findings=['原刊482頁の一文全体を十四範囲に分け、既存の内容と新しい確言・追加の提示へ照合した。',
            'schonの歴史的な確言用法とauchの追加用法を固定した出典で確認し、採用読解を明示した。',
            '焦点内容rqyxはdoの部分式の正確な写しであり、既存の真理条件を変更しない。',
            '公開した基本関係の解釈と明示した範囲の下で、この一文は対応すると判断する。'],
        interpretation_limits=LIMITS+['アシスタントによる読解判断であり、独立査読や自動的な意味一致証明ではない。',
            '他者の善・心理・社会的な地位・因果・程度・提示態度の基礎説明の拡充は残る。',
            '綴り・語順の復元や皮肉の全効果を保証せず、他の文脈や後続版へ判断を無条件に継承しない。'],
        remaining=['第二段落後半の家畜・歩行器・転倒・学習・萎縮の記述と段落全体',
            '二作品全文','基本関係の構成的説明の拡充'],whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False,new_whole_unit_reviews=0,
        new_verified_sentence_characters=sum(not c.isspace() for c in text),semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog();assert len(new.document['statements'])==46 and new.document['statements'][:45]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    assert new.entries['rqyx']['declaration']==focus_declaration()
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[r['index'] for r in review['selection']['statements']]
        assert selection_binding(old,ids)==review['selection']==selection_binding(new,ids)
    for ids in ([2,3],[4,42],[6],[5,43],[7,8,44]):assert selection_binding(old,ids)==selection_binding(new,ids)
    # The prior same-act, rank, benefit and critical-distance tests remain bound to
    # identical declarations and meanings; do not repeat their large model sweeps.
    reused={}
    for path in ('reports/benevolent-framing-v1.json','reports/directed-purpose-v1.json'):
        report=json.loads((ROOT/path).read_text(encoding='utf-8'));validate_hashes(ROOT,report['source_sha256'])
        reused[path]=digest((ROOT/path).read_bytes())
    r=reading();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==r
    validate_hashes(ROOT,r['source_sha256'])
    assert r['source']['range']==[648,924] and len(r['clauses'])==14
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    for clause in r['clauses']:
        a,b=clause['range'];assert clause['text']==r['source']['text'][a-648:b-648]
        assert all(n in new.entries for n in clause['definitions'])
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    validate_assurance(json.loads((ROOT/'data/payment-reading-evidence-v1.json').read_text(encoding='utf-8')))
    return dict(preserved_statements=45,new_statements=[45],new_primitives=2,new_definitions=4,
        exact_focus_subexpression=True,preserved_review_selections=11,prior_source_meanings_unchanged=True,
        reused_pinned_evidence=reused,clause_partition=14,current_selection_bound=True,
        reviewed_sentence_characters=r['source']['nonblank_characters'],roundtrips=True,
        semantic_equivalence_automatically_proved=False)


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('scope',scope_checks),('source',source_checks),('facts',fact_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading()
    previous=json.loads((ROOT/'reports/directed-purpose-v1.json').read_text(encoding='utf-8'))
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|set(previous['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_guardian_reading.py','scripts/check_guardian_reading.py','scripts/register_guardian_reading.py',
        'scripts/fetch_guardian_reading_evidence.py','scripts/fetch_payment_reading_evidence.py',
        'scripts/check_described_appraisals.py','tests/test_guardian_reading.py'}
    return dict(status='whole_guardian_sentence_reviewed_under_explicit_reading',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        review_decision=r['decision'],reviewer='assistant_review',whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=r['source']['nonblank_characters'],new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
