"""Connect directed, affectionate care to the same object inside the depiction."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse, format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_public_reason_claim import ROOT, SOURCE as PARENT
from scripts.compose_policy_norms import DESCRIPTION
from scripts.compose_parameterized_goals import AIMS
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY = 'examples/v016/tender-care.noema'
SOURCE = 'examples/v016/kant-tender-care.noema'
CORE = 'examples/v016/tender-care-core.noema'
BASIS = 'data/tender-care-basis-v1.json'
READING = 'data/tender-care-reading-v1.json'
REVIEW = 'data/kant-manuscript-obligations-v2.json'
CARE = [('actor','a'),('object','a'),('context','d'),('goal',DESCRIPTION),
    ('goalfor','h[a '+DESCRIPTION+' d] c'),('aims',AIMS),('occurs','h[a d] c'),('performs','h[a a d] c')]
RANKED = CARE[:3] + [('objects','j[a]'),('scope','h[a] c'),('goals','h[a] '+DESCRIPTION)] + CARE[4:] + [
    ('affection','h[a a d] c'),('classified','h[a a d] c'),('degree','h[a a d] b')]
def params(fields): return ' '.join(n+' '+t for n,t in fields)
def av(fields, **replace): return [replace.get(n,v(n)) for n,t in fields]


def definitions():
    episode = both(app(v('occurs'),v('act'),v('context')),app(v('performs'),v('act'),v('actor'),v('context')),
        app(v('aims'),v('actor'),v('act'),v('goal'),'l[a][v object]',v('context')))
    text = definition('ryj',params(CARE),both(app(v('goalfor'),v('object'),v('goal'),v('context')),quant('g','act','a',episode)))
    directed = k('ryj',*av(CARE,goal=app(v('goals'),v('object'))))
    positive = app(v('affection'),v('actor'),v('object'),v('context'))
    checked = both(app(v('classified'),v('actor'),v('object'),v('context')),
        op('u',k('hc',app(v('degree'),v('actor'),v('object'),v('context')),'n p a b')))
    text += definition('ryk',params(RANKED),both(directed,positive,checked))
    other_care = k('ryj',*av(CARE,object=v('other'),goal=app(v('goals'),v('other'))))
    other_checked = both(app(v('classified'),v('actor'),v('other'),v('context')),
        op('u',k('hc',app(v('degree'),v('actor'),v('other'),v('context')),'n p a b')))
    maximum = op('u',k('hc',app(v('degree'),v('actor'),v('object'),v('context')),
        app(v('degree'),v('actor'),v('other'),v('context'))))
    text += definition('ryl',params(RANKED),both(k('rcm',v('objects'),v('scope')),app(v('scope'),v('object')),
        k('ryk',*av(RANKED)),quant('f','other','a',op('y',app(v('scope'),v('other')),both(other_care,other_checked,maximum)))))
    return text


def additions():
    fields = [('objects','h[a d] j[a]'),('scope','h[a d a] c'),('goals','h[a d a] '+DESCRIPTION)] + [
        (n,t) for n,t in RANKED if n in ('goalfor','aims','affection','classified','degree')]
    text = ''.join(primitive('iaw'+n,t) for n,t in fields)
    bound = dict(actor=k('qb'),object=v('object'),context=v('context'),objects=k('iawobjects',k('qb'),v('context')),
        scope='i[item a][k iawscope[k qb[] v context v item]]',goals='i[item a][k iawgoals[k qb[] v context v item]]',
        occurs='p dg',performs='p df')
    bound.update({n:'p iaw'+n for n in ('goalfor','aims','affection','classified','degree')})
    text += definition('iawcare','object a','b context['+k('ryl',*[bound[n] for n,t in RANKED])+']','e')
    text += definition('iawdepiction','object a','b context['+both(
        op('t',k('iagdepiction',v('object')),v('context')),op('t',k('iawcare',v('object')),v('context')))+']','e')
    return text


def manuscript():
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(parent); doc['statements'] = []
    doc = parse(format_graph(doc,'compact')+definitions()+additions())
    # Copy only ancestors used by the actual last attribution. Historical
    # definitions remain intact; quote relocation is an explicit reading change.
    selected = closure(parent,['iatattribution'])
    affected = {'iagdepiction'}
    for row in selected:
        if _references(row) & affected: affected.add(row['name'])
    mapping = {d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'iaw'+name for name in affected if name != 'iagdepiction'})
    mapping['iagdepiction'] = 'iawdepiction'
    assert not ({mapping[n] for n in affected}-{'iawdepiction'}) & {d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] in affected and row['name'] != 'iagdepiction': doc['declarations'].append(relocate(row,mapping))
    doc['statements'] = deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')), {n:mapping[n] for n in sorted(affected)}


def build():
    doc,_ = manuscript()
    lib = deepcopy(doc); lib['statements'] = []; lib['declarations'] = closure(doc,['ryj','ryk','ryl'])
    core = deepcopy(doc); core['statements'] = core['statements'][-1:]
    core['declarations'] = closure(doc, _references(core['statements']) | {'ryj','ryk','ryl','iawcare','iawdepiction'})
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='affectionate_goal_directed_care_inside_depiction', parent=PARENT, document=SOURCE,
        definitions={
            'ryj':'同じ行為者が行った生起中の行為に、同じ対象一個体への保全・発展を表す目的記述への志向がある。目的の成功や実現可能性は要求しない。',
            'ryk':'ryjに同じ行為者から同じ対象への肯定的な感情と、その強さが評価済みで非負である条件を加える。好意のない管理や偶然の利益と区別する。',
            'ryl':'対象を含む非空の完全な比較範囲について、全対象へのryjと感情強度の評価を要求する。指定対象はrykを満たし、全比較対象以上の強度を持つ。同率を許す。',
            'iawcare':'自然qbを行為者に固定し、基準文脈で指定した対象範囲と目的を使ってrylを内容化する。',
            'iawdepiction':'従来の展開・覆いの描写と、同じ対象・同じ文脈のiawcareを結ぶ。展開行為と世話行為を同一にする条件は加えない。'},
        primitive_conventions={
            'iawgoalfor':'指定した一個体へ適用した目的記述が、その対象の存続・損傷の防止または内在的能力の発展を目的内容として表す。行為者の利益だけを表す目的とは区別する。目的の妥当性や現実の達成とは別の内容分類である。',
            'iawaims':'行為者・同じ行為・目的記述・順序付き対象列・文脈に関する目的志向。既存のparameterized-goalsのAIMS規約を用いる。',
            'iawaffection':'行為者がその対象に向ける肯定的な感情的受容。利用価値や目的達成、道徳的正しさだけから推定しない。感情機構の基礎説明は未完。',
            'iawclassified/iawdegree':'同じ行為者・対象・文脈に向けた感情強度の評価済み条件と共通の非負有理数尺度。単位や数値を原文に補わず、共通の順序保存変換で比較が不変な操作的な読みである。',
            'iawobjects/iawscope/iawgoals':'同じ行為者と文脈で先に選んだ比較対象の完全列・範囲、および各対象を一個体列で指す目的記述。結果の良い対象だけへ範囲を変更しない。'},
        limitations=[
            '世話の目的と肯定的感情を組み合わせた読解候補であり、zärtlichの全語義や心理学上の必要十分条件とはしない。感情・内容分類の基礎説明は残る。',
            'am zärtlichstenを範囲内最大として読む。同率と一対象だけの範囲を許すが、単なる強調としての絶対最上級や一意の最大への読みとは区別する。比較範囲は原文から一意に指定できていない。',
            '世話は評価文脈での目的を持つ行為の存在として構成した。長期的役割・習慣・継続の全内容、危害回避の細かな態度までは定義していない。',
            '自然の感情と目的は描写内部に置く。新しい帰属でも描写内容を実行しない。原文全体の真理、自然が文字通り感情を持つこと、目的の成功を断言しない。',
            '旧ひな形の描写参照を新しい描写へ変えた改訂読解で、同義変換ではない。旧定義・先行21主張を保存する。原文範囲と意味確認済み区間は加算しない。'])


def review(files):
    result = json.loads((ROOT/'data/kant-manuscript-obligations-v1.json').read_text(encoding='utf-8'))
    _,mapping = manuscript()
    result.update(version='kant-manuscript-obligations-v2',supersedes='data/kant-manuscript-obligations-v1.json',
        document=SOURCE,document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in result['obligations']:
        row['candidate_roots'] = [mapping.get(n,n) for n in row['candidate_roots']]
        if row['id'] == 'tender_care':
            row['candidate_roots'] = ['iawcare','iawdepiction','ryl']
            row['remaining'] = '目的付きの行為・肯定的感情・範囲内最大を同じ描写対象へ接続した。比較範囲、尺度、感情の基礎説明、最上級を強調と読む可能性と原文全体の意味一致は未確認。'
    for template in result['templates']: template['symbol'] = mapping.get(template['symbol'],template['symbol'])
    result['evidence_files'] += [BASIS,READING]
    return result


def reading():
    return dict(checked_on='2026-10-15',sources=[
        dict(url='https://www.korpora.org/Kant/aa08/041.html',lines='33-34',observation='自然を受ける代名詞が、同じ芽について最上級を伴う世話を述べる関係節に入る。'),
        dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_9_0_142',section='Zart 2(c)',observation='愛情・好意・同情に関わる用法でzärtlichがより明確で普通だとする。単なる物理的な柔らかさや成功だけには還元しない。')],
        limits=['対象語zärtlichの独立見出し本文は取得できていない。Zartの関連用法は比較材料であり、カントの語義の確定根拠ではない。',
            '原刊画像の新規照合は行っていない。数値尺度、比較対象の列挙、世話の具体的な行為は原文に指定されていない。'])


def main():
    files = build()
    files |= {BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',READING:json.dumps(reading(),ensure_ascii=False,indent=2)+'\n',
        REVIEW:json.dumps(review(files),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path = ROOT/name
        if path.exists(): assert path.read_text(encoding='utf-8') == body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
        print(name,len(body))


if __name__ == '__main__': main()
