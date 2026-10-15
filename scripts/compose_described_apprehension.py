"""Keep an aversive anticipation, its described target and actuality distinct."""
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,op,both,quant,v

LIBRARY='examples/v016/described-apprehension.noema'
EXAMPLE='examples/v016/described-apprehension-example.noema'
BASIS='data/described-apprehension-basis-v1.json'
REVIEW='data/shadow-reading-review-v1.json'
DESCRIPTION='i[h[a] e]'
RELATIONS=[('experienced','h[a a d] c'),('directed','h[a '+DESCRIPTION+' d] c'),('aversive','h[a d] c'),
    ('anticipated','h[a d d] c'),('adverse','h[a d] c')]
FIELDS=[('person','a'),('topic',DESCRIPTION),('anchor','d')]+RELATIONS
SCOPED=[('person','a'),('topics','j['+DESCRIPTION+']'),('anchor','d')]+RELATIONS


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def args(fields):return [v(n) for n,t in fields]


def definitions():
    possibility=quant('g','prospect','d',both(app(v('anticipated'),v('episode'),v('anchor'),v('prospect')),
        app(v('adverse'),v('person'),v('prospect'))))
    state=both(app(v('experienced'),v('person'),v('episode'),v('anchor')),
        app(v('directed'),v('episode'),v('topic'),v('anchor')),app(v('aversive'),v('episode'),v('anchor')),possibility)
    text=definition('rvm',params(FIELDS),quant('g','episode','a',state))
    check=op('u',k('rvm',v('person'),v('topic'),v('anchor'),*args(RELATIONS)))
    text+=definition('rvn',params(SCOPED),'q[v topics][e[v person][v person]][i[clear c topic '+DESCRIPTION+'][w[v clear]['+check+']]]')
    text+=definition('rvo','topic '+DESCRIPTION+' anchor d',quant('g','entity','a',op('t',app('s[v topic]',v('entity')),v('anchor'))))
    return text


def build():
    library=parse('p:'+definitions());text=format_graph(library,'compact')
    text+='r jxperson[] a.r jxanchor[] d.r jxcreature[a d] c.r jxwings[a d] c.'
    text+=definition('jxtopic','entity a','b point[w[k jxcreature[v entity v point]][k jxwings[v entity v point]]]','e')
    text+=definition('jxalias','entity a','k jxtopic[v entity]','e')
    for name,sort in RELATIONS:
        # These relation sorts have no function-valued result.
        text+='r jx'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    ref=dict(person='k jxperson[]',anchor='k jxanchor[]',topic='r[p jxtopic]',topics='l['+DESCRIPTION+'][r[p jxtopic] r[p jxalias]]')
    ref.update({n:'p jx'+n for n,t in RELATIONS})
    fear=k('rvm',*[ref[n] for n,t in FIELDS])
    alias=k('rvm',*[('r[p jxalias]' if n=='topic' else ref[n]) for n,t in FIELDS])
    clear=k('rvn',*[ref[n] for n,t in SCOPED])
    empty=k('rvn',*[('l['+DESCRIPTION+'][]' if n=='topics' else ref[n]) for n,t in SCOPED])
    questions=[fear,alias,clear,k('rvo',ref['topic'],ref['anchor']),k('rvo','r[p jxalias]',ref['anchor']),
        'e[r['+fear+']][r['+fear+']]',empty,'k jxadverse[k jxperson[] k jxanchor[]]']
    text+=''.join('q['+q+'].' for q in questions)
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}


def basis():
    return dict(status='operational_aversive_anticipation_not_complete_fear_theory',definitions={
        'rvm':'本人が基準文脈で経験する一つの心理状態が、指定した対象記述に向けられ、不快であり、その状態で予期する候補の少なくとも一つが本人への不利益となる。全てを同じ心理状態・本人・文脈へ結ぶ。',
        'rvn':'明示した対象記述列の各項について、同じ本人・文脈のrvmが成立しない。列外の対象への恐れは否定しない。空列では真となり、世界のあらゆる対象への無恐怖を意味しない。',
        'rvo':'指定した対象記述を明示的に評価し、基準文脈でその性質を満たす個体があることを調べる。rvmとrvnから独立した検査であり、恐れている対象の実在を暗黙に要求しない。'},
        parameters={
            'experienced':'本人・心理状態・文脈を結ぶ経験関係。状態名だけから本人の経験を推定しない。',
            'directed':'同じ心理状態がどの性質記述に向けられているか。記述の内容の真理や、その性質を満たす現実の個体の存在は含意しない。',
            'aversive':'その心理状態が、その文脈で不快な情動を伴うこと。単なる不利益の評価、否定判断、行為の未実行とは区別する。',
            'anticipated':'その心理状態・基準文脈で予期する候補状況。実際に後で生じる出来事や、本人が確実と判断した状況とは限らない。',
            'adverse':'候補状況が本人にとって不利益であること。同じ本人について予期候補と照合し、別の不可能な候補の不利益を流用しない。',
            'topic':'個体の性質を返す関数の閉じた記述。語の綴りを不透明な内容として格納するものではない。例では二つの性質の連言を記述する。'},
        limitations=[
            'rvmは不利益の予期と不快な心理状態を結んだ一つの操作的な構成であり、恐れ一般の必要十分条件や心理学的な理論ではない。心配・不安などとの区別、身体反応、程度、無自覚な恐れは未完。',
            '心理的な経験・不快さ・志向・予期・不利益は意味規約を持つ入力関係である。これらの基礎付けまで完成したとはしない。',
            '対象記述への志向と予期は同じ心理状態へ結ぶが、その対象が不利益の原因であることまでは定義しない。因果的な対象・行為との接続は別途必要。',
            '同じ真理を持つ別記述への態度を自動で移さない。別名の認識や同一視は追加の関係を要する。',
            'rvnは指定した全入力が解釈済みの場合の意味上の否定である。未知の関係を偽と補う処理は行わない。対象一覧の現実の網羅性は呼出側の責任である。',
            'Schattenの字義的な光学的説明と比喩的な対象、原文の恐れの読みは未接続。この構成をカント本文の完成訳へ自動代入せず、原文対応範囲は追加しない。'])


def review():
    return dict(status='primary_text_checked_interpretation_open',checked_date='2026-10-15',
        primary_url='https://www.korpora.org/Kant/aa08/041.html',location='AA VIII, page 41, lines 23–27',
        short_excerpt='sich nicht vor Schatten fürchtet',
        observations_ja=[
            '原文では本人への啓蒙の修飾、影を恐れない条件、軍隊の条件が、発言可能な者への制限に連なる。',
            'この箇所だけから影の指示対象や比喩の対応先を一意に定められるとはしない。光学的な影や根拠のない政治的不安への読みを未検証のまま確定しない。'],
        retrieval_limits_ja='AdelungのSchatten項のMDZおよびZenoの直接取得は失敗した。検索結果の断片を、原文の比喩の確定根拠として使用しない。',
        implementation_decision_ja='対象を指す記述への情動的な志向と、その性質を満たす対象の存在を分ける。恐れの全意味と影の語義は未完で、原文対応は増やさない。')


def main():
    data={BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(review(),ensure_ascii=False,indent=2)+'\n'}
    for name,body in (build()|data).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
