"""Use one closed description for both adoption and evaluation of a standard."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app
from scripts.compose_situated_criticism import params, args
from scripts.compose_prescribed_teaching import SETTINGS, RELATIONS, CRITERIA, ADOPTED, generic_composed as teaching_document

PARENT = 'examples/v014/kant-prescribed-teaching.noema'
DESCRIPTION = 'i['+CRITERIA+']'
DESCRIBED_ADOPTION = 'h[a a '+DESCRIPTION+' d] c'
BOUND_SETTINGS = [(('standarddescription', DESCRIPTION) if name == 'criteria' else
    (name, DESCRIBED_ADOPTION) if name == 'adopted' else (name, sort)) for name, sort in SETTINGS]


def definitions():
    # The interpreted list comes from this same description. The caller cannot
    # supply an unrelated runtime list alongside a matching adoption record.
    adapter = 'i[organization a rule a unused '+CRITERIA+' scene d]['+app(v('adopted'),
        v('organization'), v('rule'), v('standarddescription'), v('scene'))+']'
    body = k('rfv', *args(SETTINGS, criteria='s[v standarddescription]', adopted=adapter), *args(RELATIONS))
    return definition('rfw', params(BOUND_SETTINGS+RELATIONS), body, 'h[a a] e')


MEANING = '採用関係へ渡す基準列の閉じた記述を、そのまま脱引用してrfvの実行基準列にも使う。同じ数の別基準や、結果が同じ別記述への採用を移さない。動的な脱引用を含むため、そのままは引用できない。'
LIMITS = [
    '基準の同一性を関数値の未知の等しさから推測せず、型付きの閉じた式記述で指定する。採用された記述と、その評価から得る列が同じ入力に由来する。',
    '記述の同一性は構文と変数名の正規化に従う。列の順序・重複・別名は保持する。同じ真偽を返す任意の基準の同義性は認定しない。',
    '規範の対象として引用するには、基準記述を既知の閉じた引用へ固定し、既存の特殊化で静的な脱引用を除去する。出力は通常のNoema定義であり、基本関係を実行・推定する処理ではない。',
]


def generic_composed():
    text, basis = teaching_document(); basis = deepcopy(basis)
    doc = parse(text+definitions())
    basis.update(version='adopted-standards-basis-v1', document='examples/v014/adopted-standards.noema')
    basis['definitions']['rfw'] = MEANING; basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-prescribed-teaching-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()+definition('hzbi', params(BOUND_SETTINGS),
        k('rfw', *args(BOUND_SETTINGS), 'p cb', 'p cf', 'p dg', 'p f3', 'p f2'), 'h[a a] e')
    doc = parse(format_graph(doc,'compact')+text); doc['statements'] = statements
    basis.update(version='kant-adopted-standards-basis-v1', document='examples/v014/kant-adopted-standards.noema')
    basis['definitions'].update({'rfw':MEANING,
        'hzbi':'カントの教示構成で、採用関係と実行する基準列を同じ閉じた記述へ接続する。既知の基準記述で特殊化した定義をhzbf・hzbg・hzbhの規範対象に引用して使う。'})
    basis['unresolved'] += LIMITS + [
        '先行のhzbeと自由な関数列による構成は保持する。本版では基準の採用と実行に同じ記述を用いる選択肢を追加する。基準の正当性、完全性、教理や制度の一般的な意味説明は別課題である。',
        '具体的な教義の基準を勝手に補わない。検査用の二基準と別名は接続を区別するためのモデルであり、カントや教会がその基準を採用したとの主張ではない。',
        '静的な特殊化の値の一致は、純粋で全域的な解釈とNoemaの値の同一性を尊重する関係について扱う。副作用・処理順・Pythonオブジェクトの同一性を観察する外部実装の動作一致は保証しない。',
        'u0012の既存範囲の採用基準の結合を深めるが、新たな原文範囲・著者主張を追加しない。受任条件の因果、良心、辞職、全文の意味一致は未完。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc,'compact')+'\n', basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hzbi','hzbf','hzbg','hzbh'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='adopted-standards-core-basis-v1',document_path='examples/v014/adopted-standards-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'adopted-standards'),(source_composed,'kant-adopted-standards'),(core_composed,'adopted-standards-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored adopted standard differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
