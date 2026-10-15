"""Produce dependency-closed current drafts, preserving all source statements."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.closed_document import prune_document, certificate
from noema.extraction import extract_basis

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'kant-1784': ('examples/v016/kant-policy-revision.noema', 'examples/v016/kant-pruned-v1.noema'),
    'einstein-1905': ('examples/v014/einstein-energy-questions.noema', 'examples/v014/einstein-pruned-v1.noema'),
}
MANIFEST = 'data/manuscript-pruning-v1.json'
REVIEW = 'data/kant-manuscript-obligations-v12.json'
BASIS = 'data/einstein-pruned-basis-v1.json'
PREVIOUS_REVIEW = 'data/kant-manuscript-obligations-v11.json'
PREVIOUS_BASIS = 'data/einstein-energy-questions-basis-v1.json'
ROOTS = 'data/manuscript-pruning-roots-v1.json'


def alignment_inventory():
    """Use a pinned snapshot; later progress reports must not change this edition."""
    snapshot=json.loads((ROOT/ROOTS).read_text(encoding='utf-8'))
    reports={}
    for path,digest in snapshot['reports_sha256'].items():
        raw=(ROOT/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==digest,path
        reports[path]=json.loads(raw)
    for row in snapshot['evidence_records']:
        node=reports[row['report']]
        for component in row['pointer'].split('/')[1:]:
            node=node[int(component)] if isinstance(node,list) else node[component]
        names=node.get('definitions',[])
        if isinstance(names,dict):names=[]
        if 'definition' in node:names=[*names,node['definition']]
        assert names==row['definitions'],(row['report'],row['pointer'])
    return snapshot


def build():
    files, records = {}, {}
    inventory=alignment_inventory()
    for work, (source, output) in SOURCES.items():
        raw = (ROOT/source).read_bytes()
        doc = parse(raw.decode('utf-8'))
        names={d['name'] for d in doc['declarations']}
        recorded={n for row in inventory['evidence_records'] if row['unit'].startswith(work+':') for n in row['definitions']}
        roots=sorted(recorded & names)
        selected = prune_document(doc,roots=roots)
        text = format_graph(selected.document, 'compact') + '\n'
        files[output] = text
        before = len(format_graph(doc, 'compact') + '\n')
        records[work] = dict(source=source, document=output,
            source_sha256=hashlib.sha256(raw).hexdigest(),
            document_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
            before_characters=before, after_characters=len(text),
            reduction_percent=round(100*(before-len(text))/before, 2),
            source_aligned_roots=roots,
            source_aligned_symbols_absent_from_input=sorted(recorded-names),
            certificate=certificate(doc, selected))
        if work == 'einstein-1905':
            old_basis = json.loads((ROOT/PREVIOUS_BASIS).read_text(encoding='utf-8'))
            files[BASIS] = extract_basis(doc, old_basis, selected,
                version='einstein-pruned-basis-v1', document_path=output)
    review = deepcopy(json.loads((ROOT/PREVIOUS_REVIEW).read_text(encoding='utf-8')))
    review.update(version='kant-manuscript-obligations-v12', supersedes=PREVIOUS_REVIEW,
        document=SOURCES['kant-1784'][1], document_sha256=records['kant-1784']['document_sha256'])
    files[REVIEW] = review
    files[MANIFEST] = dict(status='dependency_closed_partial_drafts', works=records,
        semantic_completion=False, adds_new_text_coverage=False,
        limitations=[
            '全ての既存文と引用先を保存した。原文の未記述箇所を補ったものではない。',
            '使われない宣言だけを除いた。記号名・定義本体・引用の同一性・文順を変更せず、同じ本体の別定義も統合しない。',
            '原文対応表に記録され、入力文書にも存在する定義は、文から未参照でも追加ルートとして保持した。過去の候補も含む保守的な保存であり、最短の文書ではない。',
            '入力文書に存在しない対応表の記号は欠落一覧に記録した。外部草案からの統合や原文全体の収録を完了したとは扱わない。',
            '文字数は同じ短縮記法で文書全体を比較した値で、自然言語より短いことや一文の簡潔さを示さない。',
            '残存する原始関係の説明、外部解釈、未確定引数、読解の留保は元の草案と同じく残る。',
            '削除された公開定義を別文書から使う場合は、元の文書か追加ルート指定による抽出を使う。'])
    return {p: value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)+'\n'
            for p, value in files.items()}


def main():
    files = build()
    for name, text in files.items():
        path = ROOT/name
        if path.exists():
            assert path.read_text(encoding='utf-8') == text, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), flush=True)


if __name__ == '__main__':
    main()
