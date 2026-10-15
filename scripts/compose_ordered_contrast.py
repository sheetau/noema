"""Connect ordered contrast acts without asserting that their contents conflict."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_faculty_opportunities import ROOT, SOURCE as PARENT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, v
from scripts.compose_qualified_utterance import closure

LIBRARY = 'examples/v016/ordered-contrast.noema'
SOURCE = 'examples/v016/kant-ordered-contrast.noema'
CORE = 'examples/v016/ordered-contrast-core.noema'
BASIS = 'data/ordered-contrast-basis-v1.json'
CODE = 'i d[e]'
RECORD = 'h[a a '+CODE+' a d] c'
CONTRAST = 'h[a a '+CODE+' '+CODE+' a d] c'
FIELDS = [
    ('node', 'a'), ('author', 'a'), ('first', 'a'), ('second', 'a'),
    ('left', CODE), ('right', CODE), ('scope', 'a'), ('context', 'd'),
    ('records', RECORD), ('contrasts', CONTRAST), ('before', 'h[a a d] c')]


def definitions():
    return definition('rw3', ' '.join(n+' '+t for n,t in FIELDS), both(
        op('u', op('e', v('first'), v('second'))),
        app(v('records'), v('first'), v('author'), v('left'), v('scope'), v('context')),
        app(v('records'), v('second'), v('author'), v('right'), v('scope'), v('context')),
        app(v('before'), v('first'), v('second'), v('context')),
        op('u', app(v('before'), v('second'), v('first'), v('context'))),
        app(v('contrasts'), v('node'), v('author'), v('left'), v('right'), v('scope'), v('context'))))


def additions():
    text = 'r iafleftnode[] a.r iafrightnode[] a.r iafpresents[a a '+CODE+' '+CODE+' a d] c.'
    # The left side includes the appearance AND the actual barriers.  The right
    # side is the opportunities in the lower regime, at the SAME comparison view.
    text += definition('iafleft', '', 'k iadcontrast[]', 'e')
    text += definition('iafright', '', 'b anchor[k iaeroom[v anchor]]', 'e')
    text += definition('iafparallel', '', k('rw3', k('iacnode'), k('wa'),
        k('iafleftnode'), k('iafrightnode'), 'r d[k iafleft[]]', 'r d[k iafright[]]',
        k('iacscope'), k('wh'), 'p iaereport', 'p iafpresents', 'p ue'))
    # Keep the prior semantic candidate as well as the new discourse structure.
    # Neither the quotation nor its attribution executes the quoted content.
    text += definition('iafannotation', '', both(k('iaeattribution'), k('iafparallel')))
    return text


def build():
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib = parse('p:'+definitions())
    doc = deepcopy(parent); doc['statements'] = []
    doc = parse(format_graph(doc, 'compact')+definitions()+additions()+'s[k iafannotation[]].')
    doc['statements'] = parent['statements'][:-1]+doc['statements']
    core = deepcopy(doc); core['statements'] = core['statements'][-1:]
    core['declarations'] = closure(doc, _references(core['statements']))
    return {path:format_graph(d, 'compact')+'\n' for path,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='partial_ordered_discourse_contrast', parent=PARENT, document=SOURCE,
        definitions={
            'rw3':'異なる二箇所に同じ著者・範囲・文脈で第一・第二の内容記述を帰属し、本文順序が第一から第二へ向き、逆順がなく、同じ記述を同じ順で対比として提示する。内容を評価しない。',
            'iafleft':'前段のiadcontrastをそのまま用い、市民的自由の高い側が有利に見えることと実際の障壁を保持する。',
            'iafright':'同じ比較視点のiaeroomを内容にし、前段と同じ低い側の発展機会を保持する。',
            'iafparallel':'本文の二箇所と二つの内容記述をrw3へ渡す。既存のiaereportとueを用い、著者・範囲・文脈を揃える。',
            'iafannotation':'前段の結合内容iaecontrastへの帰属を保持し、iafparallelによる順序付きの対比帰属も要求する。'},
        inputs={
            'records':'指定箇所・著者・内容の記述・範囲・文脈への帰属関係。真理判定ではない。',
            'contrasts':'著者が二つの内容の記述をこの順で対比して提示するという談話行為の帰属。既存のzbcと同じ役割を、階数3の記述に用いる。対比を認定する行為関係そのものは解釈の入力である。',
            'before':'本文上の順序。出来事の先後や因果方向ではない。二箇所間の正順と逆順の不在を検査するが、文書全体の順序の整合性を代替しない。',
            'iafleftnode/iafrightnode':'原文u0017で、高い側の見かけの利益・障壁を述べる箇所と、低い側の発展機会を述べる箇所への局所参照。語彙の意味を原語で代用する記号ではない。'},
        limitations=[
            '対比する内容は論理的な否定同士でなくてもよい。同じ真偽の内容や同じ記述にもrw3の一般定義は矛盾条件を加えない。談話行為の適切さはcontrastsの入力に依存する。',
            '今回接続したのはhingegenによる二制度側の提示の対比である。dochの期待違反を表す候補集合は追加していない。有利さと一部の障壁は両立し得るため、前段の見かけの候補から障壁の不存在を導かない。',
            '対比関係の原文からの認定や談話一般の基礎への還元は未完。新しい文法演算子や自然言語からの自動認定規則は追加しない。',
            '階数3の記述を扱う。引用した内容が真か、意味が完全か、原文の唯一の読みかは帰属の成立とは別に検査する。',
            '前段の自由・能力・発展・因果モデルの候補解釈と未解決事項を引き継ぐ。自然と成長の比喩、段落全体と両作品の全文の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists(): assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
        print(name,len(body))


if __name__=='__main__': main()
