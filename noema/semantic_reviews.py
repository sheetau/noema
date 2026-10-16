"""Validate the provenance of explicit whole-unit review judgments.

This does NOT decide semantic equivalence. Reviewers supply that judgment and
their reasoning; this module prevents counting a different or incomplete unit,
stale manuscript, changed evidence, or a mere finite-test pass as that review.
"""
import hashlib
import json
from pathlib import Path,PurePosixPath

from .identifiers import load_annotations
from .meaning_catalog import _object,_references,load_catalog

REQUIREMENTS=('fixed_source','semantic_relations','references','presentation_role',
    'additions_and_omissions','meaning_conventions','evidence_and_limits','whole_unit_rereading')


def require(condition,message):
    if not condition:raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical_digest(value):
    return digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))


def path_in(root,name):
    require(isinstance(name,str) and bool(name) and '\\' not in name,'Invalid review input path')
    relative=PurePosixPath(name)
    require(not relative.is_absolute() and '..' not in relative.parts and ':' not in name,'Review input escapes root')
    path=(root/name).resolve()
    require(path.is_relative_to(root.resolve()),'Review input escapes root')
    return path


def read_json(root,name):
    return json.loads(path_in(root,name).read_text(encoding='utf-8'),object_pairs_hook=_object)


def validate_hashes(root,hashes):
    require(isinstance(hashes,dict) and bool(hashes),'Missing review input hashes')
    for name,expected in hashes.items():
        require(isinstance(expected,str) and len(expected)==64,'Invalid review input digest')
        require(digest(path_in(root,name).read_bytes())==expected,'Review input changed: '+name)


def selection_binding(catalog,indices):
    """Hash the statements and their transitive declarations AND conventions."""
    require(isinstance(indices,list) and bool(indices) and
        all(type(i) is int and 0<=i<len(catalog.document['statements']) for i in indices),
        'Invalid statement selection')
    require(indices==sorted(set(indices)),'Repeated or unordered statement selection')
    selected=[catalog.document['statements'][i] for i in indices]
    pending=set().union(*(_references(s) for s in selected));used=set()
    while pending:
        symbol=pending.pop()
        require(symbol in catalog.entries,'Unknown review dependency: '+symbol)
        if symbol in used:continue
        used.add(symbol);pending.update(_references(catalog.entries[symbol]['declaration'].get('body'))-used)
    entries=[catalog.entries[d['name']] for d in catalog.document['declarations'] if d['name'] in used]
    return dict(statements=[dict(index=i,sha256=canonical_digest(s)) for i,s in zip(indices,selected)],
        dependency_sha256=canonical_digest(entries),dependencies=[e['symbol'] for e in entries])


def validate_review(root,review_path,work,active,catalog,inventory):
    review=read_json(root,review_path)
    require(review.get('schema_version')=='noema-semantic-review-1','Unknown semantic review schema')
    require(review.get('decision')=='equivalent_under_stated_reading','Review is not a positive whole-unit judgment')
    require(review.get('work')==work,'Review work differs')
    for key in ('document','meaning_basis','identifier_annotations'):
        require(review.get(key)==active[key],'Review differs from active '+key)
    require(review.get('reviewer') in ('assistant_review','human_review'),'Missing reviewer category')
    for key in ('interpretation','limits'):
        require(isinstance(review.get(key),list) and review[key] and
            all(isinstance(v,str) and v.strip() for v in review[key]),'Missing '+key)
    require(review.get('unresolved')==[],'Review has unresolved unit items')
    rows=review.get('requirements')
    require(isinstance(rows,list) and len(rows)==len(REQUIREMENTS),'Missing semantic review requirements')
    require([r.get('id') for r in rows]==list(REQUIREMENTS),'Semantic review requirements differ')
    for row in rows:
        require(row.get('decision')=='satisfied' and isinstance(row.get('reason'),str) and row['reason'].strip(),
            'Requirement lacks a review judgment and reason')
    source=review.get('source',{})
    require(source.get('inventory')==active['source_inventory'],'Review source inventory differs')
    units=inventory['units'];matches=[u for u in units if u['id']==review.get('unit')]
    require(len(matches)==1,'Unknown or duplicate reviewed unit')
    unit=matches[0]
    require(unit['id'].startswith(work+':') and unit['kind']!='editorial','Not an author unit in this work')
    require(source.get('text')==unit['text'] and source.get('unit_sha256')==unit['text_sha256']==digest(unit['text'].encode('utf-8')),
        'Reviewed source text changed')
    span=source.get('range')
    require(isinstance(span,list) and all(type(x) is int for x in span) and span==[0,len(unit['text'])],
        'Review does not cover the whole unit')
    math={m['id']:m for m in inventory.get('math',[])}
    require(len(math)==len(inventory.get('math',[])),'Duplicate math source')
    expected_math=[]
    for name in unit.get('math_ids',[]):
        require(name in math,'Missing reviewed math source')
        require(digest(math[name]['mathml'].encode('utf-8'))==math[name]['sha256'],'Math source changed')
        expected_math.append(dict(id=name,sha256=math[name]['sha256']))
    require(source.get('math')==expected_math,'Review does not cover all unit math')
    selection=review.get('selection',{})
    require(isinstance(selection,dict) and isinstance(selection.get('statements'),list),'Missing reviewed statements')
    binding=selection_binding(catalog,[r.get('index') for r in selection['statements']])
    require(selection==binding,'Reviewed statements or dependency conventions changed')
    evidence=review.get('evidence')
    require(isinstance(evidence,dict) and set(evidence)=={'source_reading','formal_checks','semantic_reading'},'Missing review evidence categories')
    for paths in evidence.values():
        require(isinstance(paths,list) and paths and all(isinstance(p,str) for p in paths),'Missing review evidence')
    hashes=review.get('source_sha256');validate_hashes(root,hashes)
    required={active['source_inventory'],active['document'],active['meaning_basis']}|set(catalog.source_sha256)
    if active['identifier_annotations']:required.add(active['identifier_annotations'])
    required.update(p for paths in evidence.values() for p in paths)
    require(required<=set(hashes),'Unpinned review input')
    for name,expected in catalog.source_sha256.items():
        require(hashes[name]==expected,'Meaning catalog provenance differs')
    for paths in evidence.values():
        for name in paths:
            if name.endswith('.json'):
                record=read_json(root,name)
                for child,expected in record.get('source_sha256',{}).items():
                    require(hashes.get(child)==expected,'Review omits or changes evidence input: '+child)
    return dict(unit=unit['id'],unit_sha256=unit['text_sha256'],source_inventory=active['source_inventory'],
        review=review_path,reviewer=review['reviewer'],decision=review['decision'],
        document=active['document'],source_nonblank_characters=sum(not c.isspace() for c in unit['text']),
        source_sha256=hashes)


def load_reviews(root,index_path):
    root=Path(root).resolve();index=read_json(root,index_path)
    require(index.get('schema_version')=='noema-semantic-review-index-1','Unknown review index schema')
    hashes=index.get('source_sha256');validate_hashes(root,hashes)
    works=index.get('works');require(isinstance(works,dict) and works,'Missing active review works')
    result={};pins=dict(hashes);seen=set()
    for work,active in works.items():
        require(set(active)=={'document','meaning_basis','identifier_annotations','source_inventory','reviews'},'Invalid active document record')
        required={active['document'],active['meaning_basis'],active['source_inventory']}
        if active['identifier_annotations']:required.add(active['identifier_annotations'])
        require(isinstance(active['reviews'],list) and all(isinstance(p,str) for p in active['reviews']),'Invalid review list')
        required.update(active['reviews']);require(required<=set(hashes),'Unpinned active document or review')
        catalog=load_catalog(root,active['meaning_basis'])
        require(catalog.document_path==active['document'],'Active basis document differs')
        if active['identifier_annotations']:
            load_annotations(root,active['meaning_basis'],active['identifier_annotations'])
        inventory=read_json(root,active['source_inventory']);result[work]=[]
        for name in active['reviews']:
            row=validate_review(root,name,work,active,catalog,inventory)
            require(row['unit'] not in seen,'Duplicate reviewed unit');seen.add(row['unit'])
            for path,value in row.pop('source_sha256').items():
                require(path not in pins or pins[path]==value,'Conflicting review provenance')
                pins[path]=value
            result[work].append(row)
        for path,value in catalog.source_sha256.items():
            require(path not in pins or pins[path]==value,'Conflicting catalog provenance')
            pins[path]=value
    pins[index_path]=digest(path_in(root,index_path).read_bytes())
    return dict(status='provenance_validated_explicit_review_judgments',works=result,source_sha256=pins,
        semantic_equivalence_automatically_proved=False)
