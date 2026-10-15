"""Reconcile the stale input and independent historical libraries explicitly.

The current 175 statements survive. Imported older candidates are definitions,
not additional author assertions. Independent namespaces are never identified.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from noema.closed_document import prune_document, fingerprint
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.linking import link_documents, project_document
from noema.meaning_basis import audit_basis
from scripts.compose_manuscript_pruning import alignment_inventory, ROOTS as INVENTORY

ROOT=Path(__file__).resolve().parents[1]
CURRENT='examples/v014/einstein-density-time.noema'
CURRENT_BASIS='data/einstein-density-time-basis-v1.json'
PREVIOUS='data/manuscript-pruning-v1.json'
SOURCE='examples/v014/einstein-reconciled-v1.noema'
BASIS='data/einstein-reconciled-basis-v1.json'
MANIFEST='data/einstein-reconciliation-v1.json'
DONORS={
    'paths':('examples/v014/einstein-path-observations.noema','data/path-observations-basis-v1.json'),
    'epistemic':('examples/v013/einstein-epistemic.noema','data/einstein-epistemic-basis-v1.json'),
    'worldlines':('examples/v014/einstein-worldlines.noema','data/worldlines-basis-v1.json'),
}
ORIGINS={
    'coordinates':('data/coordinates-basis-v1.json','paths'),
    'epistemic':('data/einstein-epistemic-basis-v1.json','epistemic'),
    'finite-paths':('data/finite-paths-basis-v1.json','paths'),
    'integrals':('data/integrals-basis-v1.json','worldlines'),
    'limits':('data/limits-basis-v1.json','worldlines'),
    'moving-clocks':('data/moving-clocks-basis-v1.json','paths'),
    'moving-shapes':('data/moving-shapes-basis-v1.json','paths'),
    'path-observations':('data/path-observations-basis-v1.json','paths'),
    'phi-normalization':('data/phi-normalization-basis-v1.json','paths'),
    'real-products':('data/real-products-basis-v1.json','paths'),
    'worldlines':('data/worldlines-basis-v1.json','worldlines'),
}


@lru_cache(None)
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def closed_pair(doc,basis,roots):
    converted=convert(doc,'0.14')
    selected=extract_document(converted,roots=sorted(roots),statement_indices=[])
    audit_basis(doc,basis)
    assert convert(converted,doc['schema_version'])==doc
    names=set(selected.retained_symbols)
    return selected.document,dict(
        primitives={r['symbol']:r for r in basis['primitives'] if r['symbol'] in names},
        definitions={n:s for n,s in basis['definitions'].items() if n in names})


def verify_same_candidates(origin,origin_basis,donor,donor_basis,roots):
    left,meanings=closed_pair(origin,origin_basis,roots)
    right,other=closed_pair(donor,donor_basis,roots)
    # Order outside these closures and the document edition are not identifiers.
    a={d['name']:d for d in left['declarations']}
    b={d['name']:d for d in right['declarations']}
    if a!=b or meanings!=other:
        raise ValueError('Candidate dependencies or meaning conventions differ')
    return dict(roots=sorted(roots),dependency_count=len(a),
        declarations_sha256={n:fingerprint(d) for n,d in sorted(a.items())},
        meaning_conventions_sha256=fingerprint(meanings),edition_roundtrip=True)


def pinned(path,report):
    assert path in report['source_sha256'],path
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==report['source_sha256'][path],path


@lru_cache(None)
def assembly():
    inventory=alignment_inventory()
    rows=[r for r in inventory['evidence_records'] if r['unit'].startswith('einstein-1905:')]
    previous=load(PREVIOUS)['works']['einstein-1905']
    old_missing=set(previous['source_aligned_symbols_absent_from_input'])
    current=document(CURRENT);current_basis=load(CURRENT_BASIS);audit_basis(current,current_basis)
    names={d['name'] for d in current['declarations']}
    native=old_missing&names;independent=old_missing-names
    all_roots={n for row in rows for n in row['definitions']}&names
    selected=prune_document(current,roots=sorted(all_roots))
    inputs={'current':selected.document}
    pairs={'current':(current,current_basis,selected)}
    root_sets={label:set() for label in DONORS}
    checks=[];used={CURRENT,CURRENT_BASIS,PREVIOUS,INVENTORY,previous['source']}
    # The earlier reading text's 174 statements are an exact prefix of the
    # later 175-statement draft. Preserve the subsequent density correction.
    earlier=document(previous['source'])
    assert current['statements'][:len(earlier['statements'])]==earlier['statements']
    assert len(current['statements'])==len(earlier['statements'])+1
    for stem,(basis_path,label) in ORIGINS.items():
        report_path='reports/'+stem+'-v1.json';report=load(report_path)
        roots={n for r in rows if r['report']==report_path for n in r['definitions']}&independent
        assert roots,stem
        basis=load(basis_path);origin=basis['document'];donor,donor_basis=DONORS[label]
        pinned(origin,report);pinned(basis_path,report)
        evidence=verify_same_candidates(document(origin),basis,document(donor),load(donor_basis),roots)
        evidence.update(report=report_path,source=origin,basis=basis_path,donor=label)
        checks.append(evidence);root_sets[label].update(roots)
        used.update((report_path,origin,basis_path,donor,donor_basis))
    assert set.union(*root_sets.values())==independent
    # Resolve the 83 newer names by pinned source documents AND their meaning
    # conventions, not by spelling in the latest draft alone.
    for report_path in sorted({r['report'] for r in rows if native.intersection(r['definitions'])}):
        report=load(report_path)
        roots={n for r in rows if r['report']==report_path for n in r['definitions']}&native
        chosen=None
        for basis_path in sorted(p for p in report['source_sha256'] if p.endswith('.json') and 'basis' in p):
            basis=load(basis_path);origin=basis.get('document')
            if not isinstance(origin,str) or origin not in report['source_sha256'] or not origin.endswith('.noema'):
                continue
            if not roots <= {d['name'] for d in document(origin)['declarations']}:
                continue
            try:evidence=verify_same_candidates(document(origin),basis,current,current_basis,roots)
            except ValueError:continue
            pinned(origin,report);pinned(basis_path,report)
            chosen=(origin,basis_path,evidence);break
        if chosen is None:raise ValueError('No verified native origin: '+report_path)
        origin,basis_path,evidence=chosen
        evidence.update(report=report_path,source=origin,basis=basis_path,donor='current')
        checks.append(evidence);used.update((report_path,origin,basis_path))
    for label,(path,basis_path) in DONORS.items():
        doc=document(path);basis=load(basis_path)
        converted=convert(doc,'0.14')
        extraction=extract_document(converted,roots=sorted(root_sets[label]),statement_indices=[])
        inputs[label]=extraction.document;pairs[label]=(converted,basis,extraction)
    linked=link_documents(inputs)  # No implicit sharing of primitive or quoted identities.
    for label,doc in inputs.items():assert project_document(linked,label)==doc,label
    assert linked.document['statements']==current['statements']
    resolutions={n:dict(source='current',symbol=linked.symbols['current'][n],status='present_in_later_draft') for n in sorted(native)}
    for label,roots in root_sets.items():
        for name in sorted(roots):
            assert name not in resolutions
            resolutions[name]=dict(source=label,symbol=linked.symbols[label][name],status='independent_library_candidate')
    assert set(resolutions)==old_missing
    return linked,inputs,pairs,checks,resolutions,used


def build():
    linked,inputs,pairs,checks,resolutions,used=assembly()
    basis=dict(version='einstein-reconciled-basis-v1',document=SOURCE,
        status='partial_draft_with_independent_historical_candidates',primitives=[],definitions={},unresolved=[],
        convention_scope='Explanations retain source-local names. Resolve them through the corresponding source_symbols map.',
        source_symbols=linked.symbols,source_bases={})
    for label,(doc,original,extraction) in pairs.items():
        projected=extract_basis(doc,original,extraction,version='reconciliation-'+label,document_path=SOURCE)
        mapping=linked.symbols[label]
        basis['source_bases'][label]=dict(document=original['document'],version=original['version'])
        for row in projected['primitives']:
            moved=deepcopy(row);moved.update(symbol=mapping[row['symbol']],source_namespace=label,source_symbol=row['symbol'])
            moved['meaning_ja']='['+label+' の記号名] '+row['meaning_ja'];basis['primitives'].append(moved)
        for name,meaning in projected['definitions'].items():basis['definitions'][mapping[name]]='['+label+' の記号名] '+meaning
        basis['unresolved'].extend('['+label+'] '+text for text in projected['unresolved'])
    basis['unresolved'] += [
        '旧143記号の所在と定義の接続を照合したが、原文の意味確認や未記述部分の追加ではない。',
        '独立ライブラリの候補を現行本文の175文が使用しているとは限らない。輸入した定義を新しい著者主張として実行・帰属しない。',
        '異なる出典の同じ綴りや同じ式は自動統合しない。対応する原始関係の解釈が現実に一致するかは別の確認を要する。']
    audit_basis(linked.document,basis)
    text=format_graph(linked.document,'compact')+'\n'
    manifest=dict(status=basis['status'],document=SOURCE,
        document_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
        prior_missing_symbols=len(resolutions),present_in_later_draft=sum(r['source']=='current' for r in resolutions.values()),
        imported_independent_candidates=sum(r['source']!='current' for r in resolutions.values()),
        unresolved_old_symbol_locations=[],resolutions=resolutions,provenance_checks=checks,
        source_symbols=linked.symbols,source_statements=linked.statements,
        current_statements_preserved=len(linked.document['statements']),imported_author_assertions=0,
        sources={label:dict(declarations=len(doc['declarations']),statements=len(doc['statements']),ast_sha256=fingerprint(doc)) for label,doc in inputs.items()},
        semantic_completion=False,adds_new_text_coverage=False,
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(used)})
    return {SOURCE:text,BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',MANIFEST:json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,text in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==text,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
        print(name,len(text),flush=True)


if __name__=='__main__':main()
