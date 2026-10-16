"""Connect the self-referenced current answer to the existing title question."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT
from scripts.compose_calendar_dateline import conjunction

PARENT = 'examples/v016/kant-courteous-reference.noema'
PARENT_BASIS = 'data/courteous-reference-basis-v1.json'
FULL = 'examples/v016/kant-current-answer.noema'
BASIS = 'data/current-answer-basis-v1.json'
ANNOTATIONS = 'data/current-answer-identifiers-v1.json'
MEANING = '脚注の現在の回答への言及hzlsが同じ論説hzik内にあり、その論説を表題箇所hziaが表す同じ問いへの回答として指す。先の回答hzjnおよび紹介記事内の紹介hzjqと区別する。回答の正しさ・十分性や実際の刊行は要求しない。'


def build():
    catalog = load_catalog(ROOT, PARENT_BASIS)
    assert not {'hzls', 'hzlt'} & set(catalog.entries)
    doc = deepcopy(catalog.document)
    statements = doc['statements']; doc['statements'] = []
    additions = 'r hzls[] a.d hzlt[] c[' + conjunction([
        'u[e[k hzls[]][k hzjq[]]]', 'u[e[k hzik[]][k hzjn[]]]',
        'k dg[k hzls[] k hzjl[]]',
        'k hzjk[k hzls[] k hzik[] k hzjl[]]',
        'k hzjj[k hzls[] k hzik[] k hzia[] k hzjl[]]',
    ]) + '].s[k hzlt[]].'
    doc = parse(format_graph(doc, 'compact') + additions)
    doc['statements'] = statements + doc['statements']
    added = doc['declarations'][-2:]
    reference = added[0]
    basis = dict(status='partial_current_answer_to_shared_question', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzls': dict(parameters=reference['parameters'], result=reference['result'],
            arguments=[], meaning_ja='脚注でdie gegenwärtigeと現在の回答を指す言及の箇所。先の回答を紹介する案内内の行為とは別である。実際の印刷作業や話し手の内心を表す個体ではない。')},
        definitions={'hzlt': MEANING},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
        limitations=[
            '現在の回答を現在の論説hzikとする既存の読みを、同じ表題の問いへの回答としての言及へ結ぶ。',
            '意味関係は既存のdg・hzjk・hzjjを再利用する。新しい基本関係はなく、局所参照と合成定義を一つずつ追加する。',
            '回答として言及されることは、実際に十分または正しい答えを与えることを含意しない。',
            '脚注の補足先、刊行物名の説明要素、敬称の社会的含意、偶発性と思想比較などの全体確認は残る。',
            '既存24文・全宣言・意味規約を保存する。脚注全体や二作品全文の意味一致を認定しない。',
        ])
    text = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/courteous-reference-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
    return {FULL: text, BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n',
            ANNOTATIONS: json.dumps(annotations, ensure_ascii=False, indent=2) + '\n'}


def main():
    for name, text in build().items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == text, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    print('Current answer connected to the same title question')


if __name__ == '__main__':
    main()
