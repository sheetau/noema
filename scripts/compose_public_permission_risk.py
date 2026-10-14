"""Bind prospective harm to the same policy permitting public use of one's reason."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_speech_principals import PUBLIC
from scripts.compose_described_norms import RULE, TRUE

PARENT = 'examples/v016/kant-plural-actions.noema'
SOURCE = 'examples/v016/kant-public-permission-risk.noema'
CORE = 'examples/v016/public-permission-risk-core.noema'
BASIS = 'data/public-permission-risk-basis-v1.json'
ACTION = [(n, t) for n, t in PUBLIC if n not in ('person', 'activity', 'context')]
INPUTS = [(n, t if n == 'message' else 'i[' + t + ']') for n, t in ACTION]
SELECTORS = [(n, 'h[a a d] ' + t) for n, t in INPUTS]
POLICY = [('ruler', 'a'), ('anchor', 'd'), ('people', 'h[a d] c'), ('activities', 'h[a a d] c')] + SELECTORS + [('required', RULE), ('allowed', RULE)]
PCODE = 'i b[e]'
RISK = [('policy', PCODE), ('anchor', 'd'), ('prospects', 'h[' + PCODE + ' d d] c'), ('adverse', 'h[d] c')]
FIELD_SYMBOLS = {n:'hzmfield' + chr(ord('a') + i) for i,(n,_) in enumerate(INPUTS)}


def definitions():
    own = quant('g', 'faculty', 'a', both(k('ab', v('faculty'), v('person'), v('context')),
        k('ac', v('person'), v('faculty'), v('activity'), v('context'))))
    presented = k('hzb4', *(v(n) for n, _ in PUBLIC))
    text = definition('rrh', params(ACTION), 'i[person a activity a][b context[' + both(own, presented) + ']]', 'h[a a] e')
    args = [op('o r', v(n)) if n == 'message' else v(n) for n, _ in ACTION]
    # op() is for bracketed expressions; quoted lift has the same one-argument shape.
    text += definition('rri', params(INPUTS), 'o a[r[p rrh]][' + ' '.join(args) + ']', 'i[h[a a] e]')
    fields = {n:app(v(n), v('person'), v('activity'), v('anchor')) for n,_ in INPUTS}
    target = k('rri', *(fields[n] for n,_ in INPUTS))
    permission = k('rdm', v('ruler'), v('person'), 's[' + fields['role'] + ']', v('activity'), target,
        TRUE, v('point'), v('required'), v('allowed'))
    selected = both(app(v('people'), v('person'), v('anchor')), app(v('activities'), v('person'), v('activity'), v('anchor')))
    policy = quant('f', 'person', 'a', quant('f', 'activity', 'a', op('y', selected, permission)))
    text += definition('rrj', params(POLICY), 'b point[' + policy + ']', 'e')
    codes = [(n, 'i[' + t + ']') for n,t in POLICY]
    text += definition('rrk', params(codes), 'o a[r b[p rrj]][' + ' '.join(v(n) for n,_ in POLICY) + ']', PCODE)
    selected = app(v('prospects'), v('policy'), v('anchor'), v('outcome'))
    realized = op('t', 's[v policy]', v('outcome'))
    text += definition('rrl', params(RISK[:-1]), both(quant('g', 'outcome', 'd', selected),
        quant('f', 'outcome', 'd', op('y', selected, realized))))
    coherent = k('rrl', *(v(n) for n,_ in RISK[:-1]))
    text += definition('rrm', params(RISK), both(coherent,
        quant('f', 'outcome', 'd', op('y', selected, op('u', app(v('adverse'), v('outcome')))))))
    text += definition('rrn', params(RISK), both(coherent,
        quant('g', 'outcome', 'd', both(selected, app(v('adverse'), v('outcome'))))))
    return text


def build():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += 'r hzmruler[] a.r hzmpeople[a d] c.r hzmactivities[a a d] c.'
    for name, type_ in INPUTS: text += 'r ' + FIELD_SYMBOLS[name] + '[a a d] ' + type_ + '.'
    text += 'r hzmprospects[' + PCODE + ' d d] c.r hzmadverse[d] c.'
    text += 'r hzmnode[] a.r hzmscope[] a.r hzmreport[a a i c[e] a d] c.'
    refs = dict(ruler='r[k hzmruler[]]', anchor='r[k wh[]]', people='r[p hzmpeople]', activities='r[p hzmactivities]', required='r[p h7a]', allowed='r[p h7b]')
    refs.update({n:'r[p ' + FIELD_SYMBOLS[n] + ']' for n,_ in INPUTS})
    text += definition('hzmpolicy', '', k('rrk', *(refs[n] for n,_ in POLICY)), PCODE)
    text += definition('hzmsafety', '', 'b context[' + k('rrm', k('hzmpolicy'), v('context'), 'p hzmprospects', 'p hzmadverse') + ']', 'e')
    text += definition('hzmriskreport', '', k('hzmreport', k('hzmnode'), k('wa'), 'r c[k hzmsafety[]]', k('hzmscope'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzmriskreport[]].')
    doc['statements'] = statements + doc['statements']
    lookup = {d['name']:d for d in doc['declarations']}
    pending, retained = _references(doc['statements'][-1:]), set()
    # The adverse-possibility counterpart is diagnostic, not part of the claim.
    pending.add('rrn')
    while pending:
        name=pending.pop()
        if name in retained: continue
        retained.add(name); pending.update(_references(lookup[name]) - retained)
    core=deepcopy(doc); core['declarations']=[d for d in doc['declarations'] if d['name'] in retained]; core['statements']=doc['statements'][-1:]
    return {SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='partial_public_permission_without_adverse_prospects',document=SOURCE,parent=PARENT,
        definitions=dict(rrh='同じ公的提示の行為で、本人が所有する理解力を使う。別の行為での使用を流用しない。',
            rri='公的役割・受け手・対象・発話・経路・自己帰属を明示したrrhの閉じた行為記述を構成する。',
            rrj='基準文脈で選んだ各人・活動に、同じ出所と役割で同じ構成済み対象への実行許可があり、反対要求がないという方針の内容。',
            rrk='人物範囲・活動・役割・提示項目・出所・基準文脈・規範関係を同じ方針の記述へ構成する。',
            rrl='同じ方針記述と評価文脈に選んだ想定結果が非空で、その全結果で同じ方針の許可が成立する。',
            rrm='rrlを満たし、同じ選択結果の全てで指定した不利益がない。実際の実施・発言・受領や、現実の無害を断言しない。',
            rrn='rrlを満たし、同じ選択結果の少なくとも一つで不利益がある。空・不整合な結果群ではrrmの否定と同値ではない。',
            hzmpolicy='本文の出所・対象者・活動・各提示項目をrrkへ結ぶ。',
            hzmsafety='同じ方針の記述についてrrmの評価を行う内容。',
            hzmriskreport='未記述だったu0016の部分内容を、同じ著者と新しい本文範囲へ帰属する。帰属だけで引用内容を実行しない。'),
        bindings=dict(hzmruler='許可を出す統治者への局所参照。', hzmpeople='基準文脈でその統治者の臣民として対象に選ぶ人々。',
            hzmactivities='同じ本人と基準文脈で対象に選ぶ公的使用の活動。',
            hzmprospects='同じ方針を採ることに対応する、評価文脈での想定結果。単に発言した場合の結果ではない。',
            hzmadverse='対象とする不利益がその結果にある。原文が明示していない特定の被害者・損失額・確率は補わない。',
            hzmnode='u0016内のこの部分内容の位置。',hzmscope='この部分に対応する原文範囲。',hzmreport='段階2の内容記述を著者・位置・範囲・文脈に帰属する。'),
        frame_bindings={FIELD_SYMBOLS[n]:dict(field=n,type=t,meaning='同じ本人・活動・基準文脈に固定した提示項目の閉じた記述。') for n,t in INPUTS},
        unresolved=['u0016の部分注記であり、sieht einの認識・含意、立法への拡張、よりよい法文案、公然たる批判、比較・強調、後続の実例は未記述。',
            '公的役割、理解力、臣民と統治者の制度的関係、内容や各項目の範囲と網羅性は既存と今回の意味規約に依存する。新しい原始語で全文を置換しない。',
            '危険がないことを、非空の方針実現候補で不利益がないという部分的な読みで表す。確率的危険、候補の妥当性と網羅性、因果の同定は未完成。',
            '許可が対象とする行為内容と、許可を与える方針の内容を区別する。候補での許可の成立は、対象の発言が実行されたことを要求しない。',
            '各項目は本人・活動ごとに指定できる。対象者と活動の範囲は基準文脈で固定し、結果時点で選び直さない。空の対象範囲がある方針の普遍条件は空虚に真となり得る。',
            '原文の後続部分を含む全体の意味一致は未確認。全文完成件数には加えない。'])


def main():
    files=build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}
    for name,text in files.items():
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=text: raise ValueError('Stored public-permission risk artifact differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(text)
        print(name,len(text),'characters')


if __name__=='__main__': main()
