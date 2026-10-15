"""Connect criticism of previously adopted prescriptions to public permission."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_disclosure_actions import LIBRARY as DISCLOSURES, BUNDLE, FIELDS, CODE
from scripts.compose_candid_assessments import CRITERION
from scripts.compose_public_permission_risk import FIELD_SYMBOLS, PCODE
from scripts.compose_comparative_speech import CATALOGUE
from scripts.compose_topic_scopes import SCOPE
from scripts.compose_described_norms import TRUE

PARENT = 'examples/v016/kant-comparative-speech.noema'
SOURCE = 'examples/v016/kant-prior-criticism.noema'
CORE = 'examples/v016/prior-criticism-core.noema'
BASIS = 'data/prior-criticism-basis-v1.json'
LAW = [('adopter', 'a'), ('lawrole', 'a'), ('condition', CRITERION), ('goal', CRITERION),
       ('positive', 'c'), ('history', 'h[d] c'), ('before', 'h[d d] c')]
LAW_CODES = [(n, t if n in ('condition', 'goal') else 'i[' + t + ']') for n, t in LAW]
LAW_SELECTORS = [(n, 'h[a a d] ' + t) for n, t in LAW_CODES]
LAW_SYMBOLS = {n: 'hzqlaw' + chr(ord('a') + i) for i, (n, _) in enumerate(LAW)}
LAW_MEANINGS = dict(
    adopter='その規定を採用した出所。現在の統治者と同一とは限らない。',
    lawrole='規定の条件と目標が適用される名宛人の役割。批判者の発言上の役割とは区別する。',
    condition='規定が適用される条件を、人から状況ごとの真偽へ返す関数の閉じた記述。批判者がこの条件を満たすとは要求しない。',
    goal='条件に当てはまる人に求める目標を、同じ関数型の閉じた記述で保持する。目標の実現や正当性は要求しない。',
    positive='真なら目標の成立、偽ならその不成立を求めるという規定内容の肯否。規定の採用・廃止の有無とは別。',
    history='基準時点と過去の採用時点を同じ時間的経過へ制限する状況の範囲。実際の履歴の同定は解釈入力として明示する。',
    before='その履歴上の厳密な時間的先行関係。逆向き・同時・循環を採用済みの証拠にしない。')
REFERENCE = [field for field in SCOPE if field[0] != 'domains'] + LAW_SELECTORS
POLICY = CATALOGUE + LAW_SELECTORS


def definitions():
    adopted = k('rba', v('law'), v('adopter'), v('lawrole'), v('condition'), v('goal'), v('positive'), v('earlier'))
    previous = quant('g', 'earlier', 'd', both(app(v('history'), v('earlier')),
        app(v('before'), v('earlier'), v('anchor')), adopted))
    text = definition('rsp', 'law a anchor d ' + params(LAW),
        both(k('ta', v('history'), v('before')), app(v('history'), v('anchor')), previous))
    selected = both(app(v('people'), v('person'), v('anchor')),
                    app(v('activities'), v('person'), v('activity'), v('anchor')))
    chosen = lambda n: app(v(n), v('person'), v('activity'), v('anchor'))
    arguments = ['s[' + chosen('subject') + ']', v('anchor')]
    arguments += [chosen(n) if n in ('condition', 'goal') else 's[' + chosen(n) + ']' for n, _ in LAW]
    text += definition('rsq', params(REFERENCE), quant('f', 'person', 'a', quant('f', 'activity', 'a',
        op('y', selected, k('rsp', *arguments)))))
    text += definition('rsr', params(POLICY), 'b point[' + both(k('rsq', *(v(n) for n, _ in REFERENCE)),
        op('t', k('rrx', *(v(n) for n, _ in CATALOGUE)), v('point'))) + ']', 'e')
    coded = [(n, 'i[' + t + ']') for n, t in POLICY]
    text += definition('rss', params(coded), 'o a[r b[p rsr]][' + ' '.join(v(n) for n, _ in POLICY) + ']', PCODE)
    return text


def build():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    names = {d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in parse((ROOT / DISCLOSURES).read_text(encoding='utf-8'))['declarations'] if d['name'] not in names]
    text = definitions()
    text += 'r hzqactivities[a a d] c.r hzqrecords[a a d] j[i[a]].'
    text += 'r hzqcriteria[a a d i[a]] ' + CRITERION + '.r hzqpolarities[a a d i[a]] i[c].'
    text += 'r hzqscope[a a d] i[h[a d] c].r hzqlinked[a ' + CRITERION + ' c d] c.r hzqcandidates[a d d] c.'
    text += 'r hzqnode[] a.r hzqrange[] a.'
    for name, type_ in LAW_CODES:
        text += 'r ' + LAW_SYMBOLS[name] + '[a a d] ' + type_ + '.'
    selected = lambda symbol: k(symbol, v('person'), v('activity'), v('anchor'))
    refs = dict(records=selected('hzqrecords'), scope=selected('hzqscope'), critical='r[' + TRUE + ']',
        criteria='i[record i[a]][' + k('hzqcriteria', v('person'), v('activity'), v('anchor'), v('record')) + ']',
        polarities='i[record i[a]][' + k('hzqpolarities', v('person'), v('activity'), v('anchor'), v('record')) + ']',
        judgments='r[p fa]', matters='r[p fb]', linked='r[p hzqlinked]', candidates='r[p hzqcandidates]')
    refs.update({n: selected(FIELD_SYMBOLS[n]) for n, _ in FIELDS if n in FIELD_SYMBOLS})
    combined = k('rsk', selected('hzptarget'), k('rso', *(refs[n] for n, _ in BUNDLE)))
    text += definition('hzqtarget', 'person a activity a anchor d', combined, CODE)
    policy = dict(ruler='r[k hzmruler[]]', anchor='r[k wh[]]', people='r[p hzmpeople]', activities='r[p hzqactivities]',
        subject='r[p ' + FIELD_SYMBOLS['subject'] + ']', domains='r[p hzodomains]', role='r[p ' + FIELD_SYMBOLS['role'] + ']',
        targets='r[p hzqtarget]', required='r[p h7a]', allowed='r[p h7b]')
    policy.update({n: 'r[p ' + LAW_SYMBOLS[n] + ']' for n, _ in LAW})
    text += definition('hzqcritical', '', k('rss', *(policy[n] for n, _ in POLICY)), PCODE)
    text += definition('hzqpolicy', '', k('rrz', k('hzppolicy'), k('hzqcritical')), PCODE)
    text += definition('hzqsafety', '', 'b context[' + k('rrm', k('hzqpolicy'), v('context'), 'p hzmprospects', 'p hzmadverse') + ']', 'e')
    text += definition('hzqinsight', '', 'b context[' + k('rrq', k('hzmruler'), 'r c[k hzqsafety[]]', v('context'), 'p hznalternatives', 'p hznawareness') + ']', 'e')
    text += definition('hzqattribution', '', k('hznreport', k('hzqnode'), k('wa'), 'r d[k hzqinsight[]]', k('hzqrange'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzqattribution[]].')
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
    return dict(status='partial_criticism_of_previously_adopted_prescriptions', parent=PARENT, document=SOURCE,
        definitions=dict(rsp='同じ法・採択主体・法の名宛人の役割・条件記述・目標記述・肯否について、基準時点より前にrbaの採用がある。基準時点と過去時点を同じ非空の厳密全順序の履歴に置く。',
            rsq='選んだ全ての批判の話題を、同じ本人・行為・基準文脈から得た採用項目へ結び、rspを要求する。成立しない話題を選択範囲から除かない。',
            rsr='rsqの過去の採用と、rrxの立法範囲・各行為への許可を併記する。過去条件は方針の基準時点に固定する。',
            rss='rsrの閉じた方針記述を作る。', hzqtarget='同じ人・活動・基準文脈から比較発言hzptargetと全記録の批判的提示rsoを構成し、rskで同じ行為として結ぶ。比較発言側にある本人の能力使用も維持する。',
            hzqcritical='選択した批判の行為記述を、その話題の過去の採用と同じ統治者の立法範囲に結ぶ許可方針。',
            hzqpolicy='従来の一般使用・比較発言の方針を保持し、今回の批判の方針と同じ評価状況で結合する。',
            hzqsafety='結合した同じ方針の想定結果に指定の不利益がないか調べる。',
            hzqinsight='同じ統治者の認識・肯定と、同じ結合方針の安全性をrrqで結ぶ。',
            hzqattribution='新しい部分内容を同じ著者へ帰属し、先行16文を保持する。'),
        bindings=dict(hzqactivities='批判の提示として選ぶ活動。一般使用や比較発言の範囲を置き換えない。',
            hzqrecords='同じ人・活動・基準文脈に対する判断記録の閉じた記述の有限列。',
            hzqcriteria='同じ人・活動・基準文脈・記録記述に対する、望ましい要件の充足を評価する基準の記述。基準の正当性や網羅性を補わない。',
            hzqpolarities='同じ項目に対する肯否の記述。', hzqscope='同じ提示における評価対象の記録範囲の記述。',
            hzqlinked='同じ判断・基準記述・肯否・文脈を結ぶ。', hzqcandidates='同じ判断・判断文脈で本人が排除していない候補状況。',
            hzqnode='批判と過去の採用を補った本文位置。', hzqrange='認識・立法範囲・安全性・比較発言・批判の部分範囲。') | {
                LAW_SYMBOLS[n]: dict(field=n, type=t, meaning=LAW_MEANINGS[n], selection='同じ本人・提示行為・基準文脈で選ぶ採用項目の閉じた記述。') for n, t in LAW_CODES},
        unresolved=[
            'der schon gegebenenの参照先を、既に採用されていた法的な規定として部分的に記述する。rbaの条件付き規定を用いる操作的な読解であり、法律全般、公布の手続、法文と法の関係の語義全体ではない。',
            '採用主体と現在の統治者、法の名宛人の役割と批判する人の役割を区別する。現在も同じ規定が採用されていることや、同じ統治者による採用を要求しない。',
            'すでにという語の期待との比較や前提投射までは表現していない。厳密な先行と同じ履歴の所属を検査するが、現実の履歴の同定は解釈入力である。',
            '批判対象と比較提案の話題は同じ規定へ結ぶが、過去の規定の条件・目標と比較元の法文の版との対応までは説明していない。',
            '批判は同じ本人の評価の提示に少なくとも一つの要件不充足を含む作例である。率直さ・誠実さ・誤導の意図の不在の必要十分条件ではなく、freimüthigenは対応範囲へ追加しない。',
            '単独の比較発言の許可を保持し、批判を伴う比較発言への許可を追加する。後者は両内容を同じ人・行為・状況で提示する複合行為であり、別々の許可からの推論ではない。sogarの焦点・強調は未記述。',
            '選択範囲の網羅性、規定の基礎意味、統治者の前段への照応、洞察・安全性の意味全体、末尾の実例と全文確認は未完。旧方針より強い追加条件を伴う解釈注記であり、完全な同義文と認定しない。'])


def main():
    for name, text in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored prior criticism differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
