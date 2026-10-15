"""Attach an explicitly scoped scalar background to the unchanged source claim."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params
from scripts.compose_scalar_backgrounds import LIBRARY, PAIR, PC, ORDER, FRAME, ACTION_CODE
from scripts.compose_public_permission_risk import FIELD_SYMBOLS
from scripts.compose_described_norms import RULE, TRUE

PARENT = 'examples/v016/kant-prior-criticism.noema'
SOURCE = 'examples/v016/kant-focused-permission.noema'
CORE = 'examples/v016/focused-permission-core.noema'
BASIS = 'data/focused-permission-basis-v1.json'
FRAME_FIELDS = [('ruler', 'a'), ('person', 'a'), ('role', 'a'), ('activity', 'a'), ('required', RULE), ('allowed', RULE)]
FRAME_CODES = [(n, 'i[' + t + ']') for n, t in FRAME_FIELDS]
SCALAR_INPUTS = [('frame', FRAME), ('focus', ACTION_CODE), ('alternatives', 'j[' + ACTION_CODE + ']'),
                 ('observer', 'i[a]'), ('anchor', 'i[d]'), ('ranking', 'i[' + ORDER + ']')]
CLAIM = 'i d[e]'
REPORT_TYPE = 'h[a a ' + CLAIM + ' a d] c'
MARKED_TYPE = 'h[a a ' + CLAIM + ' ' + CLAIM + ' a a d] c'
ATTRIBUTION = [('node', 'a'), ('author', 'a'), ('foreground', CLAIM), ('background', CLAIM),
               ('foregroundscope', 'a'), ('backgroundscope', 'a'), ('context', 'd'),
               ('reported', REPORT_TYPE), ('backgrounded', MARKED_TYPE)]


def definitions():
    permission = k('rdm', v('ruler'), v('person'), v('role'), v('activity'), v('target'), TRUE, v('point'), v('required'), v('allowed'))
    text = definition('rtm', params(FRAME_FIELDS), 'i[target ' + ACTION_CODE + '][b point[' + permission + ']]', 'h[' + ACTION_CODE + '] e')
    text += definition('rtn', params(FRAME_CODES), 'o a[r b[p rtm]][' + ' '.join(v(n) for n, _ in FRAME_CODES) + ']', FRAME)
    text += definition('rto', params(SCALAR_INPUTS), k('rtg', 'o r[' + k('rti', v('frame'), v('focus')) + ']',
        k('rtk', k('rtj', v('frame'), v('alternatives'))), v('observer'), v('anchor'), v('ranking')), PAIR)
    text += definition('rtp', 'person a activity a personcode i[a] activitycode i[a]',
        both(op('e', v('person'), 's[v personcode]'), op('e', v('activity'), 's[v activitycode]')))
    reported = app(v('reported'), v('node'), v('author'), v('foreground'), v('foregroundscope'), v('context'))
    backgrounded = app(v('backgrounded'), *(v(n) for n, _ in ATTRIBUTION[:7]))
    text += definition('rtq', params(ATTRIBUTION), both(reported, backgrounded))
    return text


def build():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    names = {d['name']: d for d in doc['declarations']}
    for declaration in parse((ROOT / LIBRARY).read_text(encoding='utf-8'))['declarations']:
        if declaration['name'] in names:
            assert declaration == names[declaration['name']]
        else:
            doc['declarations'].append(declaration)
    text = definitions()
    text += 'r hzrperson[a d] i[a].r hzractivity[a a d] i[a].r hzrranking[' + ORDER[2:ORDER.rfind(']')] + '] c.'
    text += 'r hzrrange[] a.r hzrbgreport[' + MARKED_TYPE[2:MARKED_TYPE.rfind(']')] + '] c.'
    person = k('hzrperson', v('person'), v('anchor'))
    activity = k('hzractivity', v('person'), v('activity'), v('anchor'))
    role = k(FIELD_SYMBOLS['role'], v('person'), v('activity'), v('anchor'))
    text += definition('hzrframe', 'person a activity a anchor d', k('rtn', 'r[k hzmruler[]]', person, role, activity, 'r[p h7a]', 'r[p h7b]'), FRAME)
    text += definition('hzrpackage', 'person a activity a anchor d', k('rto',
        k('hzrframe', v('person'), v('activity'), v('anchor')),
        k('hzqtarget', v('person'), v('activity'), v('anchor')),
        'l[' + ACTION_CODE + '][' + k('hzptarget', v('person'), v('activity'), v('anchor')) + ']',
        'r[k wa[]]', 'r[k wh[]]', 'r[p hzrranking]'), PAIR)
    selected = both(k('hzmpeople', v('person'), k('wh')), k('hzqactivities', v('person'), v('activity'), k('wh')))
    bound = k('rtp', v('person'), v('activity'), k('hzrperson', v('person'), k('wh')),
              k('hzractivity', v('person'), v('activity'), k('wh')))
    background = k('rsy', k('hzrpackage', v('person'), v('activity'), k('wh')), v('context'))
    text += definition('hzrbackground', '', 'b context[' + quant('f', 'person', 'a', quant('f', 'activity', 'a',
        op('y', selected, both(bound, background)))) + ']', 'e')
    refs = [k('hzqnode'), k('wa'), 'r d[k hzqinsight[]]', 'r d[k hzrbackground[]]', k('hzqrange'), k('hzrrange'), k('wh'),
            'p hznreport', 'p hzrbgreport']
    text += definition('hzrattribution', '', k('rtq', *refs))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzrattribution[]].')
    doc['statements'] = statements[:-1] + doc['statements']
    lookup = {d['name']: d for d in doc['declarations']}
    pending, retained = _references(doc['statements'][-1:]), set()
    while pending:
        name = pending.pop()
        if name in retained:
            continue
        retained.add(name)
        pending.update(_references(lookup[name]) - retained)
    core = deepcopy(doc)
    core['declarations'] = [d for d in doc['declarations'] if d['name'] in retained]
    core['statements'] = doc['statements'][-1:]
    return {SOURCE: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n'}


def basis():
    return dict(status='explicit_author_scalar_background_for_critical_permission', parent=PARENT, document=SOURCE,
        definitions=dict(rtm='同じ出所・本人・役割・行為・規範関係の枠を作り、行為記述の引数だけを変える許可内容を返す。',
            rtn='rtmの閉じた枠を構成する。', rto='同じ枠に焦点と比較対象の行為記述を適用し、尺度条件だけを背景にした組を作る。',
            rtp='本人と行為の閉じた参照記述が、同じ選択済みの本人と行為を指すことを検査する。',
            rtq='同じ著者・箇所・主張内容・文脈への既存の帰属と、その主張に別範囲の背景を結ぶ明示的な帰属を併記する。内容は実行しない。',
            hzrframe='本文の統治者・同じ本人・役割・行為・既存規範関係から許可の比較枠を作る。',
            hzrpackage='同じ枠に、批判を伴う比較提案hzqtargetと比較提案hzptargetを渡す。著者の視点・同じ基準文脈で尺度だけを背景にする。',
            hzrbackground='対象者と批判を伴う活動の選択を基準文脈に固定し、全選択対について本人・行為の参照整合と背景の尺度条件を要求する。',
            hzrattribution='元のhzqinsightの帰属を同じ箇所・著者・範囲・文脈で保持し、新しい背景を別の範囲で結ぶ。安全性や統治者の認識内容は変更しない。'),
        bindings=dict(hzrperson='選択した本人と基準文脈から、その本人の閉じた個体参照を返す。rtpで実際の指示先を照合する。',
            hzractivity='同じ本人・行為・基準文脈から、その行為の閉じた参照を返す。別の活動の参照を補わない。',
            hzrranking='視点・焦点内容記述・比較内容記述・基準文脈における、許可としてより際立つという尺度の比較関係。二内容は同じ許可枠で構成する。確率の比較とは固定しない。',
            hzrrange='sogarによる強調の部分範囲。',
            hzrbgreport='同じ箇所・著者・主張記述・背景記述・主張範囲・背景範囲・文脈について、著者がその主張をその背景とともに提示する帰属関係。背景を主張と同じ内容に潰さず、実際の真理や読者の同意は要求しない。'),
        unresolved=[
            'sogarの焦点を批判を伴う提示への許可に置き、比較提案だけへの許可と同じ枠で比べる読解候補。著者の視点を明示するが、統治者の視点や異なる作用範囲を排除した唯一の分析ではない。',
            '尺度条件だけを背景にする。許可することについての見通しが述べられているため、比較対象の許可が現在既に成立しているという追加前提は補わない。追加的な含意の一般理論は未完。',
            '背景は安全性の成否を決める条件や、統治者が認識した内容に追加しない。元のhzqpolicy・hzqsafety・hzqinsightの構造をそのまま保持する。',
            '対象者と行為の範囲が空なら普遍条件は空虚に真になる。人や発言の存在は補わない。選択した範囲と尺度の妥当性は別途説明が必要。',
            '比較提案だけの対象は批判の不在を要求する行為記述ではない。追加条件を含まない基準として使う。二記述間の意味的な含意から許可を自動で移す規則は追加しない。',
            '背景帰属は明示的な意味規約を持つ入力関係であり、自然言語全般の前提投射、背景の受容・修復、話者の信念を自動で導く機構ではない。',
            '率直さの全語義、法文の版との対応、統治者の前段への照応、後続の実例、原文区間全体の意味一致は未完。'])


def main():
    for name, text in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored focused permission differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
