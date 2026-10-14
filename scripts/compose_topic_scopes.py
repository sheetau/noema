"""Bind a permission policy's speech subjects to its authority's topic scope."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_public_permission_risk import POLICY, INPUTS, FIELD_SYMBOLS, PCODE

PARENT = 'examples/v016/kant-policy-recognition.noema'
SOURCE = 'examples/v016/kant-topic-scopes.noema'
CORE = 'examples/v016/topic-scopes-core.noema'
BASIS = 'data/topic-scopes-basis-v1.json'
DOMAIN = ('domains', 'h[a a d] c')
SCOPED_POLICY = POLICY + [DOMAIN]
SCOPE = [field for field in POLICY if field[0] in ('ruler', 'anchor', 'people', 'activities', 'subject')] + [DOMAIN]


def definitions():
    selected = both(app(v('people'), v('person'), v('anchor')),
        app(v('activities'), v('person'), v('activity'), v('anchor')))
    subject = 's[' + app(v('subject'), v('person'), v('activity'), v('anchor')) + ']'
    belongs = app(v('domains'), v('ruler'), subject, v('anchor'))
    text = definition('rrr', params(SCOPE), quant('f', 'person', 'a', quant('f', 'activity', 'a', op('y', selected, belongs))))
    # Validate every selected subject. Filtering selected acts by membership
    # would hide incorrectly bound subjects and unpermitted selected acts.
    text += definition('rrs', params(SCOPED_POLICY), 'b point[' + both(
        k('rrr', *(v(n) for n,_ in SCOPE)),
        op('t', k('rrj', *(v(n) for n,_ in POLICY)), v('point'))) + ']', 'e')
    codes = [(n, 'i[' + t + ']') for n,t in SCOPED_POLICY]
    text += definition('rrt', params(codes), 'o a[r b[p rrs]][' + ' '.join(v(n) for n,_ in SCOPED_POLICY) + ']', PCODE)
    return text


def build():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions() + 'r hzodomains[a a d] c.r hzonode[] a.r hzoscope[] a.'
    refs = dict(ruler='r[k hzmruler[]]', anchor='r[k wh[]]', people='r[p hzmpeople]',
        activities='r[p hzmactivities]', required='r[p h7a]', allowed='r[p h7b]', domains='r[p hzodomains]')
    refs.update({n:'r[p ' + FIELD_SYMBOLS[n] + ']' for n,_ in INPUTS})
    text += definition('hzopolicy', '', k('rrt', *(refs[n] for n,_ in SCOPED_POLICY)), PCODE)
    text += definition('hzosafety', '', 'b context[' + k('rrm', k('hzopolicy'), v('context'), 'p hzmprospects', 'p hzmadverse') + ']', 'e')
    text += definition('hzoinsight', '', 'b context[' + k('rrq', k('hzmruler'), 'r c[k hzosafety[]]',
        v('context'), 'p hznalternatives', 'p hznawareness') + ']', 'e')
    text += definition('hzoattribution', '', k('hznreport', k('hzonode'), k('wa'),
        'r d[k hzoinsight[]]', k('hzoscope'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzoattribution[]].')
    doc['statements'] = statements[:-1] + doc['statements']
    lookup = {d['name']:d for d in doc['declarations']}
    pending, retained = _references(doc['statements'][-1:]), set()
    while pending:
        name = pending.pop()
        if name in retained: continue
        retained.add(name); pending.update(_references(lookup[name]) - retained)
    core = deepcopy(doc)
    core['declarations'] = [d for d in doc['declarations'] if d['name'] in retained]
    core['statements'] = doc['statements'][-1:]
    return {SOURCE:format_graph(doc,'compact')+'\n', CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='partial_authority_bound_subject_scope', document=SOURCE, parent=PARENT,
        definitions=dict(
            rrr='基準文脈で選んだ各人・各活動の話題記述を評価し、その同じ対象が同じ出所の対象範囲に基準文脈で属することを要求する。',
            rrs='rrrによる話題範囲の条件と、既存rrjによる全選択行為への許可を同時に要求する。対象外の活動を除いて真にする条件ではない。',
            rrt='対象範囲の関係も含めたrrsの閉じた方針記述を構成する。',
            hzopolicy='先行する人物・活動・役割・提示項目・規範関係を保持し、同じ統治者の立法に関する話題範囲をrrtへ渡す。',
            hzosafety='この範囲付き方針について、同じ記述に属する想定結果と不利益をrrmで評価する。',
            hzoinsight='同じ統治者が範囲付き方針の安全性を認識して肯定し、その内容も成立するというrrqの部分条件。',
            hzoattribution='対象範囲と認識を含む改訂内容を、同じ著者の新しい部分範囲へ帰属する。'),
        bindings=dict(
            hzodomains='統治者・話題対象・基準文脈について、その対象を当人の立法に関する範囲として採る関係。法や立法の語義をこの関係名だけで説明済みとはしない。',
            hzonode='対象範囲を補った部分内容の本文位置。', hzoscope='認識・対象範囲・安全性に対応する原文範囲。'),
        unresolved=[
            'in Ansehung seiner Gesetzgebungを同じ統治者の立法に関する話題範囲への部分的な接続として読む。selbstの焦点と、前の宗教領域からの拡張・比較は未記述。',
            'hzodomainsは原文の参照範囲を保持する解釈入力。法的な制度・規範集合・法文・立法行為の関係や所有的照応の全てを構成的に説明したものではない。実際の成立や採択の過程は補わない。',
            'rrrは選択済みの全活動の整合条件。対象外の発言を禁止せず、この方針の範囲指定に不一致があることを表す。rrsが偽でも危険や禁止を直ちに意味しない。',
            '母集団や活動が空なら範囲条件と一般許可は空虚に真になり得る。対象の存在や範囲の網羅性を追加していない。未知の対象範囲は偽や空集合で補わない。',
            '話題の範囲と話題選択は基準文脈に固定する。将来候補で範囲を縮めて、許可されない発言や他の出所の話題を除くことはしない。',
            '許可・方針結果・認識に渡す記述は変更後のものにそろえる。旧方針への許可や旧内容への認識を構文一致なしで引き継がない。',
            'よりよい法文案、公然たる率直な批判、先行する統治者の照応と強調、後続の実例は未記述。危険・理性・理解力・洞察の基礎課題も継承し、全文の意味確認済みには数えない。'])


def main():
    files = build() | {BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}
    for name,text in files.items():
        path = ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8') != text: raise ValueError('Stored topic scope differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(text)
        print(name,len(text),'characters')


if __name__ == '__main__': main()
