"""Keep self-benefit appraisal nonfactive and tied to the same policy."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_political_consequence import ROOT, SOURCE as PARENT, HIGH, REST, GOV, SCHEMA, params, av
from scripts.compose_governing_principles import DESCRIPTION
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/self-benefit.noema'
SOURCE='examples/v016/kant-self-benefit.noema'
CORE='examples/v016/self-benefit-core.noema'
BASIS='data/self-benefit-basis-v1.json'
REVIEW='data/self-benefit-reading-v1.json'
OUTCOMES='h[a '+DESCRIPTION+' c d d] c'
BENEFIT=[('actor','a'),('beneficiary','a'),('policy',DESCRIPTION),('context','d'),('goals','j[a]'),
    ('scope','h[a] c'),('holds','h[a a d] c'),('classified','h[a a d] c'),('outcomes',OUTCOMES)]
RECIPE='i b[h[a a '+DESCRIPTION+' d d] c]'
BASE=[('assessor','a'),('actor','a'),('beneficiary','a'),('policy',DESCRIPTION),('recipe',RECIPE),('context','d')]
VIEWS='h['+' '.join(t for n,t in BASE)+' d] c'
AWARE='h['+' '.join(t for n,t in BASE)+'] c'
APPRAISAL=BASE+[('views',VIEWS),('awareness',AWARE)]
TRUE='e[n p a b][n p a b]'
FALSE='u['+TRUE+']'


def definitions():
    selected=lambda sign:app(v('outcomes'),v('actor'),v('policy'),sign,v('context'),v('outcome'))
    holds=app(v('holds'),v('beneficiary'),v('goal'),v('outcome'))
    policy=op('t',app('s[v policy]','l[a][]'),v('outcome'))
    assessed=quant('f','goal','a',op('y',app(v('scope'),v('goal')),
        app(v('classified'),v('beneficiary'),v('goal'),v('outcome'))))
    checked=[]
    for sign in (FALSE,TRUE):
        checked += [quant('g','outcome','d',selected(sign)),quant('f','outcome','d',
            op('y',selected(sign),both(op('e',policy,sign),assessed)))]
    text=definition('rx6',params(BENEFIT),both(k('rcm',v('goals'),v('scope')),*checked))
    guaranteed=lambda sign:quant('f','outcome','d',op('y',selected(sign),holds))
    preserved=quant('f','goal','a',op('y',app(v('scope'),v('goal')),op('y',guaranteed(FALSE),guaranteed(TRUE))))
    added=quant('g','goal','a',both(app(v('scope'),v('goal')),guaranteed(TRUE),op('u',guaranteed(FALSE))))
    text+=definition('rx7',params(BENEFIT),both(k('rx6',*av(BENEFIT)),preserved,added))
    view=app(v('views'),*av(BASE),v('candidate'))
    judgment=app('s[v recipe]',v('actor'),v('beneficiary'),v('policy'),v('context'),v('candidate'))
    text+=definition('rya',params(APPRAISAL),both(app(v('awareness'),*av(BASE)),
        quant('g','candidate','d',view),quant('f','candidate','d',op('y',view,judgment))))
    return text


def additions():
    text=''.join(primitive('iat'+name,sort) for name,sort in (
        ('goals','h[a d] j[a]'),('scope','h[a d a] c'),('holds','h[a a d] c'),
        ('classified','h[a a d] c'),('outcomes',OUTCOMES),('views',VIEWS),('awareness',AWARE)))
    fields='actor a beneficiary a policy '+DESCRIPTION+' anchor d context d'
    text+=definition('iatbenefit',fields,k('rx7',v('actor'),v('beneficiary'),v('policy'),v('context'),
        k('iatgoals',v('beneficiary'),v('anchor')),'i[goal a][k iatscope[v beneficiary v anchor v goal]]',
        'p iatholds','p iatclassified','p iatoutcomes'))
    text+=definition('iatappraisal','actor a policy '+DESCRIPTION+' context d',k('rya',v('actor'),v('actor'),v('actor'),
        v('policy'),'r b[p iatbenefit]',v('context'),'p iatviews','p iatawareness'))
    remainder='i[reading '+HIGH+' community a contributors j[a] anchor d start d end d late d]['+both(
        k('iatappraisal',v('actor'),v('second'),v('late')),
        app(v('remaining'),v('reading'),v('community'),v('contributors'),v('anchor'),v('start'),v('end'),v('late')))+']'
    text+=definition('iatschema',params(SCHEMA),k('iasschema',v('reading'),*av(GOV),remainder))
    sort='h['+' '.join(t for n,t in SCHEMA)+'] c'
    text+='r iatreport[a a i c['+sort+'] a d] c.'
    text+=definition('iatattribution','',k('iatreport',k('iagnode'),k('wa'),'r c[p iatschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iatattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='nonfactive_self_benefit_appraisal_of_same_new_policy',parent=PARENT,document=SOURCE,
        definitions={
            'rx6':'同じ受益対象の非空で完全な目標一覧を検査する。同じ主体が同じ政策内容を実現する側・しない側の結果候補がそれぞれ非空で、内容の実現・不実現と一致し、全目標の達成状態が評価済みである。',
            'rx7':'rx6の両側で、確実に満たされる目標を比べる。実現しない側で保証される全目標を実現する側でも保ち、さらに保証される目標が一つ以上ある。',
            'rya':'同じ判断主体・行為主体・受益対象・政策記述・評価手続の記述・判断文脈への明示的認識があり、その非空の判断候補全てで同じ手続が成立する。現実の判断文脈で手続が成立することは要求しない。',
            'iatbenefit':'受益対象と実際の判断時点で固定した目標範囲を、全判断候補に共通して使う。候補ごとに都合のよい別の目標へ替えない。',
            'iatappraisal':'規範を担う同じ主体を判断主体・行為主体・受益対象へ渡し、同じ政策についてiatbenefitの記述を判断する。',
            'iatschema':'前段と同じ新原則の内容と主体を使い、政治的終点にiatappraisalを要求する。原則を要求することと、その内容を実現する利益への判断は分ける。残余条件の全引数を保持する。',
            'iatattribution':'同じ著者・原文箇所・文脈への階数2の部分ひな形帰属を更新する。親の全宣言と先行21主張を保存する。'},
        limitations=[
            '有益さを、固定した目標の保証集合の真包含という候補で表す。期待効用・金銭・福利・道徳的価値・損益交換を同一視しない。目標の選定や比較不能の場合があり、zuträglichの唯一の必要十分条件ではない。',
            '結果候補は同じ政策内容を実現する場合・しない場合に対応させるが、実行可能な方法、現実の実行、因果機構や確率分布をこの条件だけで証明しない。',
            '目標の達成は受益対象に対して評価する。行為者が得することと別人が得することを混同せず、自己利益の原文候補では三つの主体を明示的に一致させる。',
            '規範上の採用とは別に、政策内容の実現について判断する。新原則が条件文なら適用例がない履行もあり得るため、尊厳に即した具体的な扱いを接続するときにその内容を確定する必要がある。',
            '判断は非事実的で、正しいことを要求しない。判断候補の選定、組織が判断主体であることの構成、論理的全知や矛盾した信念の一般理論は未完である。',
            '判断対象の記述と評価手続の記述を保持し、外延的に同じ別名へ認識を流用しない。未知の候補・評価・目標を偽として補わない。',
            '政府の資格、具体的な尊厳と扱い、人間と機械の対比、前段の強い因果条件の原文への適合は未完である。新しい原文範囲と意味確認済み区間は加算しない。'])


def reading_review():
    from scripts.check_apparent_liberty import UNITS
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(source_unit=unit['id'],source_sha256=unit['text_sha256'],checked_on='2026-10-15',
        sources=[dict(url='https://www.korpora.org/Kant/aa08/041.html',lines='37',observation='政府を受ける関係節で、自らにとって有益だと見なすことが述べられる。'),
            dict(url='https://www.korpora.org/Kant/aa08/042.html',lines='1-2',observation='その判断対象である扱いの不定詞句が次頁に続く。')],
        decisions=['判断主体と受益対象を同じ政府へ束縛する。判断対象は新原則の要求ではなくその内容の実現へ接続する候補とする。',
            'findetを非事実的な肯定判断として構成し、実際の利益を外側で断言しない。これは今回の解釈選択であり、本文が形式的な真理条件を明記したとはしない。',
            '有益さの保証集合によるモデルと、尊厳の未記述内容を区別する。原文には具体的な目標一覧・確率・効用尺度の指定がない。'])


def main():
    files=build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(reading_review(),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
