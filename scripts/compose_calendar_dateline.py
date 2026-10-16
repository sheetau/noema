"""Compose a calendar address and a displayed document dateline."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.grammar import number_word
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT, closure

PARENT = 'examples/v016/kant-conditional-imputation.noema'
PARENT_BASIS = 'data/conditional-imputation-basis-v1.json'
FULL = 'examples/v016/kant-calendar-dateline.noema'
LIBRARY = 'examples/v016/calendar-address.noema'
BASIS = 'data/calendar-dateline-basis-v1.json'
ANNOTATIONS = 'data/calendar-dateline-identifiers-v1.json'
PRIMITIVES = {
    'hzir': ('[a a b d] c', ['暦規約', '年期間', '年番号', '文脈'], '指定した紀元・年の区切りを含む暦規約の下で、この年期間にこの年番号が付く。別の暦や文脈の同じ番号とは同一視しない。'),
    'hzis': ('[a a d] j[a]', ['暦規約', '年期間', '文脈'], 'この暦規約における、この年の月期間を暦順に並べた有限列。重複を含まず全ての月を一度ずつ含むという解釈契約。未指定の暦や年には空列等を推測して補わず解釈を保留する。'),
    'hzit': ('[a a d] j[a]', ['暦規約', '月期間', '文脈'], 'この暦規約における、この月の日期間を暦順に並べた有限列。重複を含まず全ての日を一度ずつ含むという解釈契約。暦の改訂等で欠番がある場合、日付ラベルと列内順位は別途記述を要する。'),
    'hziu': ('[a a a d] c', ['日付行の提示', '文書', '表示場所', '文脈'], '同じ提示が指定文書の日付行の場所欄としてこの場所を表示する。実際の執筆場所・刊行場所や提示者は含意しない。'),
    'hziv': ('[a a a d] c', ['日付行の提示', '文書', '表示日期間', '文脈'], '同じ提示が指定文書の日付行の日付としてこの日期間を表示する。刊行日や実際の執筆完了日であることは含意しない。'),
    'hziw': ('[a a a d] c', ['場所', '地域', '日期間', '文脈'], '指定日の地理的な記述において、この場所がこの地域の内に位置する。現在の所属や政治的主権まで含意しない。'),
    'hzix': ('[] a', [], 'この日付行が用いる民用暦の規約。紀元と年月日の区切りを含む局所参照。グレゴリオ暦・UTC・閏年規則を未確認のまま同一視しない。'),
    'hziy': ('[] a', [], 'カント本文末尾u0019の日付行として表された提示。物理的な筆記行為を指定しない。'),
    'hziz': ('[] d', [], 'この文書末尾の日付行の表示文脈。日付が指す日そのものとは別の型である。'),
    'hzja': ('[] a', [], 'この日付行で場所を指すために用いられる名称個体。綴りは識別表記の別添えに置く。'),
    'hzjb': ('[] a', [], 'この日付行が場所として指すケーニヒスベルクの局所参照。名称個体とは異なる。現代地名や座標は補わない。'),
    'hzjc': ('[] a', [], 'この日付行で地域を指すために用いられる名称個体。綴りは識別表記の別添えに置く。'),
    'hzjd': ('[] a', [], 'この日付行が当時の地域として指すプロイセンの局所参照。名称個体とは異なる。現代国家と同一視しない。'),
    'hzjf': ('[] a', [], 'この日付行が指定する年期間の局所参照。年番号との対応は本文で要求する。'),
    'hzjg': ('[] a', [], 'この日付行が指定する月期間の局所参照。指定年の月列内の位置は本文で要求する。'),
    'hzjh': ('[] a', [], 'この日付行が指定する日期間の局所参照。指定月の日列内の位置は本文で要求する。'),
}
MEANINGS = {
    'rqrm': '指定した暦・文脈で年番号に対応する年を取り、その年の月列の指定位置の月、その月の日列の指定位置の日を結ぶ。月・日の位置は既存列演算に合わせて0始まりであり、8は第9月、29は第30日。非整数・負・範囲外位置は成立しない。年番号と列の割当は引数で与え、月名の対訳表を使わない。',
    'hzje': '同じ文書の日付行の成立と、名称から場所・地域への適用を結ぶ。原文が使う暦で年番号1784、第9月、第30日を指定し、その同じ日についての場所の地域内所在、同じ文書への場所表示・日付表示を要求する。提示者、刊行日、実際の執筆イベントは補わない。',
}
LIMITS = [
    '民用暦の局所参照と年・月・日列の意味契約を使う。暦の歴史的同定、閏日や改暦欠番、絶対時刻への換算、全ての暦への日付ラベルの一般化は未実装。',
    'Septemberをこの暦の第9月、30を当月の第30日として読む。この対応を原文全体の意味確認済みと自動認定しない。',
    '固有名の綴りと対象への適用は分離する。名称による局所参照は都市や地域の全性質の定義ではない。地理的所在の真実性を外部史料で検証したとはしない。',
    '原刊494頁の日付行を視認した。電子版の[er]は編集上の展開で、画像の略記Septemb.とは区別する。字面・改行・活字の再現は目的としない。',
    '既存の本文と意味規約を保存する。本文全体の未解決事項を引き継ぎ、翻訳機は保留したままである。',
]


def num(value):
    return 'n p ' + number_word(value) + ' ' + number_word(1)


def conjunction(parts):
    result = parts[-1]
    for part in reversed(parts[:-1]):
        result = 'w[' + part + '][' + result + ']'
    return result


def additions():
    declarations = ''.join('r ' + name + signature + '.' for name, (signature, _, _) in PRIMITIVES.items())
    declarations += ('d rqrm[calendar a year a month a day a yearnumber b monthindex b dayindex b context d '
        'years h[a a b d] c months h[a a d] j[a] days h[a a d] j[a]] c['
        'w[c[v years][v calendar v year v yearnumber v context]]'
        '[w[a[c[v months][v calendar v year v context]][v monthindex][v month]]'
        '[a[c[v days][v calendar v month v context]][v dayindex][v day]]]].')
    dated = conjunction([
        'k rqrm[k hzix[] k hzjf[] k hzjg[] k hzjh[] ' + num(1784) + ' ' + num(8) + ' ' + num(29) + ' k hziz[] p hzir p hzis p hzit]',
        'k hziw[k hzjb[] k hzjd[] k hzjh[] k hziz[]]',
        'k hziu[k hziy[] k hzik[] k hzjb[] k hziz[]]',
        'k hziv[k hziy[] k hzik[] k hzjh[] k hziz[]]',
    ])
    declarations += 'd hzje[] c[' + conjunction([
        'k dg[k hziy[] k hziz[]]',
        'u[e[k hzja[]][k hzjb[]]]', 'u[e[k hzjc[]][k hzjd[]]]',
        'k hzih[k hziy[] k hzja[] k hzjb[] k hziz[]]',
        'k hzih[k hziy[] k hzjc[] k hzjd[] k hziz[]]',
        dated,
    ]) + '].'
    return declarations


def build():
    catalog = load_catalog(ROOT, PARENT_BASIS)
    doc = deepcopy(catalog.document)
    previous = doc['statements']; doc['statements'] = []
    size = len(doc['declarations'])
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(catalog.entries)
    doc = parse(format_graph(doc, 'compact') + additions() + 's[k hzje[]].')
    doc['statements'] = previous + doc['statements']
    lib = deepcopy(doc); lib['statements'] = []; lib['declarations'] = closure(doc, ['rqrm'])
    primitives = {}
    for d in doc['declarations'][size:]:
        if d['kind'] == 'primitive':
            _, arguments, meaning = PRIMITIVES[d['name']]
            primitives[d['name']] = dict(parameters=d['parameters'], result=d['result'], arguments=arguments, meaning_ja=meaning)
    basis = dict(status='partial_calendar_address_and_displayed_dateline', document=FULL, library=LIBRARY,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives=primitives, definitions=MEANINGS,
        new_signatures={d['name']: {k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT/'data/conditional-imputation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    for symbol, spelling in [('hzja','Königsberg'), ('hzjc','Preußen')]:
        annotations['entries'].append(dict(symbol=symbol, role='designation', forms=[dict(text=spelling, language='de', role='edition_transcription')]))
    return {FULL:body, LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n', ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name, body in build().items():
        path = ROOT/name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
    print('Calendar address and displayed dateline composed')


if __name__ == '__main__': main()
