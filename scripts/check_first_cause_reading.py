"""Review the first causal sentence as a whole, without claiming its paragraph."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product,permutations
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT,closure
from scripts.check_motive_causes import unknown,symbol

FULL='examples/v016/kant-scoped-attitude.noema'
BASIS='data/scoped-attitude-basis-v1.json'
INDEX='data/semantic-review-index-v43.json'
CORE='examples/v016/kant-first-cause-reading.noema'
AUDIT='data/first-cause-reading-v1.json'
REPORT='reports/first-cause-reading-v1.json'
DOC='docs/first-cause-reading-v1.md'
SCENES=('now','winA','winB','fail')
DOMAIN=('group','A','B','C','guardian','planA','planB','actA','actB')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def core():
    doc=deepcopy(catalog().document);doc['statements']=[doc['statements'][i] for i in (2,3)]
    doc['declarations']=closure(doc,_references(doc['statements']))
    return format_graph(doc,'compact')+'\n'


@lru_cache(None)
def boundary(mode):
    doc=deepcopy(catalog().document);doc['statements']=[]
    replacements=parse('''p:r jkg[a d] c.r jmq[a d] c.r jmr[a d] c.
d kg[person a] e[b scene[k jkg[v person v scene]]].
d mq[group a] e[b scene[k jmq[v group v scene]]].
d mr[group a] e[b scene[k jmr[v group v scene]]].''')['declarations']
    mapping={d['name']:d for d in replacements if d['kind']=='definition'}
    doc['declarations']=replacements[:3]+[mapping.get(d['name'],d) for d in doc['declarations']]
    names=['ms','oi'] if mode=='population' else ['og','od'] if mode=='pair' else ['ms','ok','ol']
    doc['declarations']=closure(doc,names)
    text=format_graph(doc,'compact')+'r jgroup[] a.r jguardian[] a.r jtarget[] a.r jscene[] d.'
    if mode=='population':
        text+='q[t[k ms[k jgroup[]]][k jscene[]]].q[k oi[k jgroup[] k jtarget[] k jscene[]]].'
    elif mode=='pair':
        text+='q[k og[k jguardian[] k jtarget[] k jscene[]]].q[t[k od[k jguardian[] k jtarget[]]][k jscene[]]].'
    else:
        for n in ('ms','ok'):text+='q[t[k '+n+'[k jgroup[]]][k jscene[]]].'
        text+='q[k ol[k jgroup[] k jscene[]]].'
    return parse(text)


def values(variant='baseline',members=('A','B','C'),qualifies=('A','B'),threshold=Fraction(2,3)):
    qualifies=set(qualifies)
    def outcome(actor,method,start,end):
        return actor=='guardian' and start=='now' and (method,end) in {
            ('planA','winA'),('planB','fail' if variant=='split_cost_success' else 'winB')}
    def role(act,actor,target,scene):
        if variant=='wrong_role_actor':actor_ok=actor=='C'
        else:actor_ok=actor=='guardian'
        pairs={('actA','C' if variant=='outsider_target' else 'A','winA'),('actB','B','winB')}
        if variant=='missing_B_role':pairs={('actA','A','winA')}
        if variant=='wrong_act':pairs={('actB','A','winA'),('actA','B','winB')}
        return actor_ok and (act,target,scene) in pairs
    def cause(source,factor,target,result,scene):
        pair=(symbol(factor),symbol(result))
        missing=variant.split(':',1)[1].split('/') if variant.startswith('missing_link:') else None
        return (source,target,scene)==('C' if variant=='other_cause_subject' else 'group','group',
            'fail' if variant=='other_cause_context' else 'now') and pair in set(product(('mq','mr'),('ms','ok'))) \
            and (missing is None or pair!=tuple(missing))
    v=dict(jgroup=lambda:'group',jguardian=lambda:'guardian',jtarget=lambda:'A',jscene=lambda:'now',
        mp=lambda group:SequenceValue(tuple(members),'"individual"'),
        aa=lambda p:p in ('A','B','C','guardian') and not (variant=='nonhuman_member' and p=='C'),
        ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda b:Fraction(int(b)),
        pa=lambda a,b:a/b if b else Fraction(0),
        hr=lambda pop,ctx:variant!='incomplete_population' and ctx=='now',
        hs=lambda ratio,ctx:ctx=='now' and ratio>=threshold,
        jkg=lambda person,scene:person in qualifies and scene=='now',
        jmq=lambda group,scene:variant!='missing_effort_factor' and (group,scene)==('group','now'),
        jmr=lambda group,scene:variant!='missing_fear_factor' and (group,scene)==('group','now'),
        of=lambda group,actor,scene:variant!='no_other_people' and (group,actor,scene)==('group',
            'A' if variant=='self_in_others' else 'guardian','now'),
        ae=lambda actor,method,scene:(actor,scene)==('guardian','now') and method in (
            ('planA',) if variant=='missing_B_method' else ('planA','planB')),
        af=outcome,
        ap=lambda actor,method,start,end:variant!='empty_selected' and outcome(actor,method,start,end),
        oa=lambda actor,act,scene:variant!='not_self_initiated' and actor=='guardian' and (act,scene) in {('actA','winA'),('actB','winB')},
        ob=role,
        oc=lambda actor,method,scene:Fraction(9 if variant=='high_burden' or variant=='split_cost_success' and method=='planA' else 1),
        oe=lambda burden,scene:scene==('fail' if variant=='other_ease_context' else 'now') and burden<=2,
        hzie=cause)
    return v


def run(mode,v,memo=False):
    doc=boundary(mode)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:v[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memo,memoize_expressions=memo)]


def population_checks():
    rows=[]
    for bits in product((False,True),repeat=3):
        selected=tuple(p for p,b in zip(('A','B','C'),bits,strict=True) if b)
        for threshold in (Fraction(1,3),Fraction(2,3),Fraction(3,4)):
            actual=run('population',values(qualifies=selected,threshold=threshold))
            assert actual==[Fraction(sum(bits),3)>=threshold,bits[0]],(bits,threshold,actual)
            rows.append(dict(qualifies=list(selected),threshold=str(threshold),values=actual))
    for order in permutations(('A','B','C')):assert run('population',values(members=order))==[True,True]
    bad={}
    for variant,members in [('empty',()),('duplicate',('A','A','B')),('incomplete_population',('A','B','C')),
        ('nonhuman_member',('A','B','C'))]:
        bad[variant]=run('population',values(variant,members=members))
        assert bad[variant][0] is False
    outsider=values();outsider['jtarget']=lambda:'guardian';outsider['jkg']=lambda p,s:s=='now'
    assert run('population',outsider)==[True,False]
    return dict(combinations=rows,permutations=6,invalid_populations=bad,qualifying_nonmember_not_target=True,
        ordinary_evaluation=True,kg_explicitly_abstracted=True)


def composition_checks():
    variants=('baseline','high_burden','split_cost_success','missing_B_method','missing_B_role','outsider_target',
        'wrong_role_actor','wrong_act','not_self_initiated','empty_selected','no_other_people','self_in_others','other_ease_context',
        'missing_effort_factor','missing_fear_factor','other_cause_subject','other_cause_context')+tuple(
            'missing_link:'+a+'/'+b for a,b in product(('mq','mr'),('ms','ok')))
    rows={}
    ease_failures=set(variants[1:13])
    for variant in variants:
        actual=run('combined',values(variant),memo=True)
        expected=[True,variant not in ease_failures,variant=='baseline']
        assert actual==expected,(variant,actual,expected)
        rows[variant]=actual
    pair={}
    for variant in ('baseline','high_burden','split_cost_success','missing_B_method'):
        ordinary=run('pair',values(variant));cached=run('pair',values(variant),memo=True)
        assert ordinary==cached==[variant in ('baseline','missing_B_method'),False]
        pair[variant]=ordinary
    # Population and target refer to the same qualifying property. Adding C
    # raises its proportion, but also requires a method for C; none is supplied.
    assert run('combined',values(qualifies=('A','B','C')),memo=True)==[True,False,False]
    assert run('combined',values(qualifies=('A',),threshold=Fraction(1,3)),memo=True)==[True,True,True]
    for name in ('jkg','jmq','jmr','of','oc','oe','hzie'):
        v=values();v[name]=unknown
        try:run('combined',v,memo=True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,ordinary_pair_checks=pair,cohort_change_changes_role_obligation=True,
        memoized_pure_evaluation_for_nested_composition=True,ordinary_pair_results_match=True,
        kg_mq_mr_explicitly_abstracted=True,actual_ratio_role_method_cost_and_causal_definitions_executed=True,
        complete_motive_temporal_and_ability_semantics_reexecuted=False,unknown_inputs_refused=7)


def attribution_checks():
    doc=parse(core());rows={}
    for variant in ('baseline','other_author','other_node','other_content','other_scene','reverse_order','reverse_depiction'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        def claims(node,author,content,scene):
            return (node,author,symbol(content),scene)==('other' if variant=='other_node' else 'cause',
                'other' if variant=='other_author' else 'author','ie' if variant=='other_content' else 'mx',
                'other' if variant=='other_scene' else 'text')
        def depicts(node,author,target,depiction,scene):
            return (node,author,symbol(target),symbol(depiction),scene)==('other' if variant=='other_node' else 'cause',
                'other' if variant=='other_author' else 'author','qg' if variant=='reverse_depiction' else 'kf',
                'kf' if variant=='reverse_depiction' else 'qg','other' if variant=='other_scene' else 'text')
        v.update(mw=lambda:'cause',wa=lambda:'author',wg=lambda:'opening',wh=lambda:'text',uc=claims,qa=depicts,
            ue=lambda a,b,s:(a,b,s)==(('cause','opening','text') if variant=='reverse_order' else ('opening','cause','text')))
        actual=[r['value'] for r in evaluate_document(doc,individuals=('cause','opening','author','other'),situations=('text',),primitives=v)]
        assert actual==[variant in ('baseline','reverse_depiction'),variant in ('baseline','other_content','reverse_order')]
        rows[variant]=actual
    return dict(contrasts=rows,all_claimed_facts_unknown=True,ordinary_evaluation=True)


def reading():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    text=unit['text'][:unit['text'].index('Es ist so bequem')]
    marks=[0]+[text.index(s) for s in ('sind die Ursachen','ein so großer','nachdem','(naturaliter','dennoch','gerne','und warum','sich zu')]+[len(text)]
    rows=[
        ('evaluated_motives',['mj','mk','mq','mr'],'通常の労力回避・恐れによる回避と、その傾向への帰責。単なる休息や恐怖だけではない。'),
        ('causal_claim',['ol','mx'],'二要因が二結果それぞれに実際に寄与する読み。唯一・必須・単独十分な原因とはしない。'),
        ('large_share',['ms','kh','hq','pd'],'文脈で採る有限の人々の完全な母集団における、大きいと評価される比率。過半数という固定値にはしない。'),
        ('prior_natural_release',['kf','km','rqxe','qg','qh'],'本人の自然的発達による依存からの移行は継続より前で、基準から遠い過去。自然の宣告はその非字義的な描写。'),
        ('natural_majority',['kc','ka','kb'],'自然的に成人の段階にあり、発達上の依存によって他者の指導が必要ではないこと。法定年齢や現実の知的自立とは区別する。'),
        ('concession',['kg','jb','ke'],'解放と継続の実際の共存、および著者が採る通常の期待に反すること。解放後の継続を論理的に不可能とはしない。'),
        ('willing_lifelong_persistence',['ie','ib','id','bf'],'文脈上の開始から生涯の終わりまで、未成熟な状態とそれを好ましく受け入れる態度が続く。全瞬間の快感や注意は含めない。'),
        ('others_and_ease',['ok','oj','og','nd'],'文脈上の他者と対象者の各組について、同じ実行可能な方法が成功条件と低負担の基準を満たす。数値・単位は原文へ指定しない。'),
        ('self_assumed_guardianship',['oi','od','oa','ob'],'同じ割合表現の該当者を対象に、自ら発意して判断・行為を指図する立場を引き受け、または称する。全対象への一括した方法や正当な資格を要求しない。'),
    ]
    clauses=[dict(id=n,range=[a,b],text=text[a:b],definitions=names,interpretation_ja=meaning)
        for (n,names,meaning),a,b in zip(rows,marks[:-1],marks[1:],strict=True)]
    sources=(inv,FULL,BASIS,INDEX,'artifacts/publication-header-v1/page-481.jpg',
        'artifacts/first-cause-reading-v1/page-482.jpg','artifacts/author-signature-facsimile-v1/manifest.json',
        'reports/motive-causes-v1.json','reports/evaluated-motives-v1.json','reports/relative-past-v1.json',
        'reports/scoped-attitude-v1.json','reports/easy-roles-v1.json','docs/proportions-v1.md','docs/easy-roles-v1.md')
    return dict(status='first_sentence_review_under_stated_reading_not_whole_unit',reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(text)],text=text,
            nonblank_characters=sum(not c.isspace() for c in text)),clauses=clauses,
        document=FULL,meaning_basis=BASIS,selection=selection_binding(catalog(),[2,3]),
        references=[dict(page=481,url='https://www.digitale-sammlungen.de/de/view/bsb10926843?page=521',
            image='artifacts/publication-header-v1/page-481.jpg'),
            dict(page=482,url='https://www.digitale-sammlungen.de/de/view/bsb10926843?page=522',
            image='artifacts/first-cause-reading-v1/page-482.jpg',canvas_index=521,
            image_url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00522/full/full/0/default.jpg'),
            dict(url='https://korpora.org/Kant/aa08/035.html')],
        facsimile_observations=['481頁末尾から482頁冒頭へ第一文が続く。括弧内は原刊でもnaturaliter majorennes。',
            '第一文は後見役を自ら引き受ける不定詞節で終わり、次の便宜を述べる独立文を含めない。',
            'その人々という参照、二つのwhy節、肯定的な態度と生涯の範囲を別々に確認した。'],
        interpretation_limits=['同じ二要因が各結果に寄与する読み、文脈で定まる母集団・他者の範囲・通常性・程度を採る。全ての可能な解釈の唯一性は主張しない。',
            '自己任命を述べるが法的な違法性や客観的に不当な資格を付加しない。批判的な議論の中での主張であり、著者自身やアシスタントの道徳判断を世界の真理としない。',
            'ラテン語の字体や原文の綴りを保存する翻字ではなく、括弧内の説明を自然的成人の条件として記述する。',
            '有限モデル・心理機構・歴史的事実を証明した判断ではない。意味規約を指定した手作業の読解であり、独立査読ではない。'],
        whole_unit_semantically_verified=False,new_whole_unit_reviews=0,
        remaining=['第二段落の残る文の通し確認','他の本文単位とアインシュタイン全文'],
        version_limit='固定したv43の本文・意味規約に対する第一文だけの判断。後続版への自動継承や段落全体への昇格はしない。',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sources})


def integrity_checks():
    review=reading();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==review
    validate_hashes(ROOT,review['source_sha256'])
    assert ''.join(c['text'] for c in review['clauses'])==review['source']['text']
    assert len(review['clauses'])==9 and review['source']['range']==[0,290]
    for c in review['clauses']:
        assert c['text']==review['source']['text'][slice(*c['range'])]
        assert all(n in catalog().entries for n in c['definitions'])
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document']==FULL and index['works']['kant-1784']['meaning_basis']==BASIS
    assert (ROOT/CORE).read_text(encoding='utf-8')==core()
    doc=parse(core());assert doc['statements']==[catalog().document['statements'][i] for i in (2,3)]
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(clause_partition=9,current_selection_bound=True,source_statements=2,roundtrips=True,
        new_whole_unit_reviews=0,semantic_equivalence_automatically_proved=False)


def build_report():
    results={}
    for name,fn in [('population',population_checks),('composition',composition_checks),('attribution',attribution_checks),('integrity',integrity_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    review=reading();source=review['source']
    paths=set(review['source_sha256'])|set(catalog().source_sha256)|{CORE,AUDIT,DOC,
        'scripts/check_first_cause_reading.py','scripts/register_first_cause_reading.py','tests/test_first_cause_reading.py',
        'scripts/check_motive_causes.py','scripts/compose_falling_depiction.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='first_sentence_reading_and_composition_checks_not_whole_paragraph',document=CORE,**results,
        alignment=dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],
            definitions=['mx','ol','ms','ok','kf','qg'],status='explicit_interpretive_annotation',whole_unit_semantically_verified=False),
        review_decision=review['decision'],review_scope='first sentence only in the fixed source and conventions',
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/CORE,core());write_exact(ROOT/AUDIT,encoded(reading()))


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
    print('First causal sentence reviewed with explicit scope limits',flush=True)


if __name__=='__main__':main()
