"""Construct closed action descriptions for a finite assessment disclosure."""
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_speech_principals import PUBLIC
from scripts.compose_described_norms import TRUE
from scripts.compose_candid_assessments import (
    LIBRARY as PARENT, EXAMPLE as PARENT_EXAMPLE, CRITERION, RELATIONS, PRESENTATION,
)

LIBRARY = 'examples/v016/disclosure-actions.noema'
EXAMPLE = 'examples/v016/disclosure-actions-example.noema'
BASIS = 'data/disclosure-actions-basis-v1.json'
ACTION = 'h[a a] e'
CODE = 'i[' + ACTION + ']'
FIXED = [(n, t) for n, t in PRESENTATION if n not in ('person', 'activity', 'context')] + RELATIONS
FIELDS = [(n, 'i[' + t + ']') for n, t in FIXED]
ITEM = [('record', 'i[a]'), ('criterion', CRITERION), ('polarity', 'i[c]')] + FIELDS
BUNDLE = [('records', 'j[i[a]]'), ('criteria', 'h[i[a]] ' + CRITERION),
          ('polarities', 'h[i[a]] i[c]'), ('scope', 'i[h[a d] c]'), ('critical', 'i[c]')] + FIELDS


def definitions():
    selected = app(v('candidates'), v('record'), v('context'), v('point'))
    own = both(
        app(v('judgments'), v('person'), v('record'), v('context')),
        app(v('matters'), v('record'), v('subject'), v('context')),
        app(v('linked'), v('record'), v('criterioncode'), v('polarity'), v('context')),
        quant('g', 'point', 'd', selected),
        quant('f', 'point', 'd', op('y', selected, op('z',
            op('t', app(v('criterion'), v('subject')), v('point')), v('polarity')))),
    )
    template = [('criterion', 'h[a] e'), ('criterioncode', CRITERION),
                ('polarity', 'c'), ('record', 'a'), ('message', 'i[h[a] f]')] + FIXED
    public = k('hzb4', *(v(n) for n, _ in PUBLIC))
    text = definition('rsh', params(template),
        'i[person a activity a][b context[' + both(own, public) + ']]', ACTION)
    args = [v('criterion'), 'o r[v criterion]', v('polarity'), v('record'),
            'o r[' + k('rsb', v('criterion'), v('polarity')) + ']'] + [v(n) for n, _ in FIELDS]
    text += definition('rsi', params(ITEM), 'o a[r[p rsh]][' + ' '.join(args) + ']', CODE)
    conjunction = both(*(op('t', app(v(n), v('person'), v('activity')), v('context')) for n in ('left', 'right')))
    text += definition('rsj', 'left ' + ACTION + ' right ' + ACTION,
        'i[person a activity a][b context[' + conjunction + ']]', ACTION)
    text += definition('rsk', 'left ' + CODE + ' right ' + CODE,
        'o a[r[p rsj]][v left v right]', CODE)
    append = 'r[i[prefix j[a] item a][m[v prefix][l[a][v item]]]]'
    sequence = 'q[v records][r[l[a][]]][i[state i[j[a]] record i[a]][o a[' + append + '][v state v record]]]'
    text += definition('rsl', 'records j[i[a]]', sequence, 'i[j[a]]')
    guard = both(k('rse', v('records'), v('scope'), v('context')), op('y', v('critical'), v('negative')))
    text += definition('rsm', 'records j[a] scope h[a d] c critical c negative c',
        'i[person a activity a][b context[' + guard + ']]', ACTION)
    negative = 'q[v records][r[' + op('u', TRUE) + ']][i[state i[c] record i[a]][o a['
    negative += 'r[i[previous c sign c][' + op('x', v('previous'), op('u', v('sign'))) + ']]'
    negative += '][v state ' + app(v('polarities'), v('record')) + ']]]'
    text += definition('rsn', 'records j[i[a]] polarities h[i[a]] i[c]', negative, 'i[c]')
    initial = 'o a[r[p rsm]][' + k('rsl', v('records')) + ' v scope v critical ' + k('rsn', v('records'), v('polarities')) + ']'
    item = k('rsi', v('record'), app(v('criteria'), v('record')), app(v('polarities'), v('record')),
             *(v(n) for n, _ in FIELDS))
    combined = 'q[v records][' + initial + '][i[state ' + CODE + ' record i[a]][' + k('rsk', v('state'), item) + ']]'
    text += definition('rso', params(BUNDLE), combined, CODE)
    return text


def library():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    return parse(format_graph(doc, 'compact') + definitions())


def example():
    doc = library()
    parent = parse((ROOT / PARENT_EXAMPLE).read_text(encoding='utf-8'))
    names = {d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in parent['declarations'] if d['name'] not in names]
    # Reuse the ordinary normative definition, without adding a language primitive.
    source = parse((ROOT / 'examples/v016/kant-comparative-speech.noema').read_text(encoding='utf-8'))
    lookup = {d['name']: d for d in source['declarations']}
    pending, needed = {'rdm'}, set()
    while pending:
        name = pending.pop()
        if name in needed or name in names:
            continue
        needed.add(name)
        pending.update(_references(lookup[name]) - needed)
    doc['declarations'] += [d for d in source['declarations'] if d['name'] in needed]
    text = 'r jdselectcriterion[i[a] ' + CRITERION + ' ' + CRITERION + '] ' + CRITERION + '.'
    text += 'r jdselectpolarity[i[a] i[c] i[c]] i[c].'
    text += 'r jdruler[] a.r jdrequired[a a a a ' + CODE + ' c d] c.r jdallowed[a a a a ' + CODE + ' c d] c.'
    text += definition('jdcodecriteria', 'record i[a]',
        k('jdselectcriterion', v('record'), 'r[p jdstandardone]', 'r[p jdstandardtwo]'), CRITERION)
    text += definition('jdcodepolarities', 'record i[a]',
        k('jdselectpolarity', v('record'), 'r[' + TRUE + ']', 'r[' + op('u', TRUE) + ']'), 'i[c]')
    refs = dict(records='l[i[a]][r[k jdfirst[]] r[k jdsecond[]]]', criteria='p jdcodecriteria',
                polarities='p jdcodepolarities', scope='r[p jdscope]', critical='r[' + TRUE + ']',
                role='r[k jdrole[]]', audience='r[p jdaudience]', subject='r[k jdsubject[]]',
                recipient='r[k jdrecipient[]]', channel='r[k jdchannel[]]', voices='r[p jdvoices]')
    refs.update({n: 'r[p jd' + n + ']' for n, _ in RELATIONS})
    text += definition('jdaction', '', k('rso', *(refs[n] for n, _ in BUNDLE)), CODE)
    permission = k('rdm', k('jdruler'), k('jdperson'), k('jdrole'), k('jdact'), k('jdaction'),
                   TRUE, k('jdcontext'), 'p jdrequired', 'p jdallowed')
    actual = op('t', app('s[k jdaction[]]', k('jdperson'), k('jdact')), k('jdcontext'))
    text += 'q[' + permission + '].q[' + actual + '].q[k jdcritical[]].'
    return parse(format_graph(doc, 'compact') + text)


def build():
    return {LIBRARY: format_graph(library(), 'compact') + '\n',
            EXAMPLE: format_graph(example(), 'compact') + '\n'}


def basis():
    return dict(status='constructed_scope_relative_disclosure_action', parent=PARENT, library=LIBRARY, example=EXAMPLE,
        definitions=dict(
            rsh='一項目の本人の評価と同じ公的提示を、人・行為・状況を引数に持つ行為として記述する。',
            rsi='同じ基準の記述から実行関数と判断の対象記述を、同じ肯否から発話を構成してrshへ渡す。',
            rsj='二つの行為条件を同じ人・行為・状況で結合する。',
            rsk='二つの閉じた行為記述からrsjの記述を構成する。',
            rsl='記録の閉じた記述の列から、同じ順序・重複の個体列の記述を構成する。',
            rsm='同じ記録列と明示範囲の一致を要求し、批判を指定した場合には少なくとも一つの否定評価を要求する。',
            rsn='同じ記録列に対する肯否の記述から、少なくとも一つが否定という条件の記述を構成する。',
            rso='範囲・否定評価の条件と全項目の公的提示を一つの閉じた行為記述へ結合する。'),
        limitations=[
            'rsf・rsgの意味を任意の状況依存の選択関数についてそのまま置き換えるものではない。各記録の基準と肯否は構成時に選んだ閉じた記述に固定する。範囲・本人の判断・実際の提示は行為の評価状況で検査する。',
            '構成時には記録の列と記述を選ぶ関数を実行するが、記述された基準の真理・本人の判断・提示は実行しない。未知の選択関数を補わない。',
            '同じ個体を指す別の記述や同じ真偽になる別構文を、同じ許可対象へ自動で統合しない。順序や重複によって行為の記述は異なり得る。',
            '空の列から空虚な開示成立を得ない。構成自体は空の列も表し、実行条件rseが不成立となる。',
            '提示の許可、実際の提示、評価の真理は独立である。複合行為の許可から各項目の許可を推論する規則は追加しない。',
            '率直さの語義全体、法の制定済みという照応、カント本文の方針への統合は未完。原文対応率は増やさない。'])


def main():
    for name, text in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored disclosure action differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
