"""Audit and inspect versioned meaning conventions without evaluating Noema.

This checks declarations, explanation coverage and provenance, not the truth of
explanations, their grounding, or equivalence to a natural-language source.
"""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

from .constructed import parse as parse_constructed
from .grammar import parse as parse_legacy
from .ranked import parse as parse_ranked
from .script import transcribe


class BasisError(ValueError):
    """An incomplete or inconsistent chain of meaning conventions."""


def require(condition,message):
    if not condition:raise BasisError(message)


def _object(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Duplicate JSON key: '+key)
        result[key]=value
    return result


def _parse(text):
    decoded=transcribe(text,reverse=True)
    if re.match(r'\s*(?:p:|noema\s+p\s+p(?:\s|$))',decoded):doc=parse_constructed(decoded)
    elif re.match(r'\s*(?:o:|noema\s+o\s+o(?:\s|$))',decoded):doc=parse_ranked(decoded)
    else:doc=parse_legacy(decoded)
    require(doc['schema_version'] in ('0.13','0.14','0.15','0.16'),'Meaning catalog supports editions 0.13 through 0.16')
    return doc


def _references(value):
    if isinstance(value,dict):
        result={value['symbol']} if value.get('kind') in ('call','function_ref') else set()
        for child in value.values():result.update(_references(child))
        return result
    if isinstance(value,list):
        result=set()
        for child in value:result.update(_references(child))
        return result
    return set()


def _records(value):
    if isinstance(value,dict):
        records=[]
        for name,row in value.items():
            require(isinstance(row,dict),'Invalid primitive convention: '+name)
            require('symbol' not in row or row['symbol']==name,'Primitive convention name differs: '+name)
            records.append(dict(row,symbol=name))
    else:
        require(isinstance(value,list),'Primitive conventions must be a list or object')
        records=value
    lookup={}
    for row in records:
        require(isinstance(row,dict) and isinstance(row.get('symbol'),str),'Invalid primitive convention')
        name=row['symbol'];require(name not in lookup,'Duplicate primitive convention: '+name)
        lookup[name]=row
    return lookup


def _coverage(declarations,basis,path):
    primitives=_records(basis.get('primitives',{}))
    definitions=basis.get('definitions')
    require(isinstance(definitions,dict),path+': missing definition explanations')
    require(set(primitives)=={d['name'] for d in declarations if d['kind']=='primitive'},path+': primitive inventory differs')
    require(set(definitions)=={d['name'] for d in declarations if d['kind']=='definition'},path+': definition inventory differs')
    entries={}
    for declaration in declarations:
        name=declaration['name'];entry=dict(symbol=name,kind=declaration['kind'],meaning_basis=path)
        if declaration['kind']=='primitive':
            row=primitives[name]
            require(row.get('parameters')==declaration['parameters'] and row.get('result')==declaration['result'],path+': primitive signature differs: '+name)
            labels=row.get('arguments')
            require(isinstance(labels,list) and len(labels)==len(declaration['parameters']) and
                all(isinstance(label,str) and label.strip() for label in labels) and len(set(labels))==len(labels),
                path+': invalid argument labels: '+name)
            meaning=row.get('meaning_ja');entry['arguments']=deepcopy(labels)
        else:meaning=definitions[name]
        require(isinstance(meaning,str) and meaning.strip(),path+': missing meaning convention: '+name)
        entry.update(meaning_ja=meaning,declaration=deepcopy(declaration))
        entries[name]=entry
    return entries


def _statement_changes(old,new):
    key=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    before=Counter(map(key,old));after=Counter(map(key,new))
    return dict(added=sum((after-before).values()),removed=sum((before-after).values()),
        same_order_and_contents=old==new)


@dataclass
class Catalog:
    document:dict
    document_path:str
    basis_path:str
    entries:dict
    lineage:list
    source_sha256:dict
    projection:dict|None=None

    def _dependencies(self):
        direct={};primitive={}
        for declaration in self.document['declarations']:
            name=declaration['name'];refs=_references(declaration.get('body'))
            require(refs<=set(direct),'Unresolved or forward reference: '+name)
            direct[name]=refs
            primitive[name]={name} if declaration['kind']=='primitive' else set().union(*(primitive[r] for r in refs))
        return direct,primitive

    def audit(self):
        direct,primitive=self._dependencies()
        statements=[sorted(set().union(*(primitive[r] for r in _references(s)))) for s in self.document['statements']]
        return dict(status='signature_explanation_and_provenance_audit_only',document=self.document_path,
            basis=self.basis_path,edition=self.document['schema_version'],primitive_count=sum(e['kind']=='primitive' for e in self.entries.values()),
            definition_count=sum(e['kind']=='definition' for e in self.entries.values()),statement_count=len(statements),
            signature_and_documentation_coverage=True,lineage=deepcopy(self.lineage),projection=deepcopy(self.projection),
            definition_primitive_dependencies={d['name']:sorted(primitive[d['name']])
                for d in self.document['declarations'] if d['kind']=='definition'},
            statement_primitive_dependencies=statements,source_sha256=dict(sorted(self.source_sha256.items())),
            semantic_equivalence_to_source_proven=False,primitive_grounding_proven=False,
            dependency_scope='Static references, including quoted expressions; function, description and other formal arguments are not supplied or evaluated.')

    def explain(self,symbols):
        require(isinstance(symbols,(list,tuple)) and symbols and all(isinstance(s,str) for s in symbols),'Specify at least one symbol')
        require(len(set(symbols))==len(symbols),'Duplicate requested symbol')
        require(set(symbols)<=set(self.entries),'Unknown requested symbol: '+', '.join(sorted(set(symbols)-set(self.entries))))
        direct,primitive=self._dependencies();pending=set(symbols);retained=set()
        while pending:
            name=pending.pop()
            if name in retained:continue
            retained.add(name);pending.update(direct[name]-retained)
        rows=[]
        for declaration in self.document['declarations']:
            name=declaration['name']
            if name not in retained:continue
            row=deepcopy(self.entries[name]);row['direct_dependencies']=sorted(direct[name]);row['primitive_dependencies']=sorted(primitive[name])
            # Retain typed open arguments, rather than mistaking a parameterized
            # definition with no declared primitives for a grounded explanation.
            row['formal_parameters']=deepcopy(declaration['parameters']) if declaration['kind']=='definition' else []
            rows.append(row)
        result=self.audit();result.update(requested_symbols=list(symbols),retained_symbols=[r['symbol'] for r in rows],entries=rows)
        return result


def load_catalog(root,basis_path,*,document_path=None):
    """Read one append-only declaration lineage and optionally a closed projection.

    Every JSON key is unique. Each delta must name its exact parent document and
    document all and only its added declarations. No evaluation or source-text
    translation is performed. Paths and provenance are relative to root.
    """
    root=Path(root).resolve();hashes={};active=set();cache={}

    def locate(value):
        require(isinstance(value,(str,Path)) and str(value).strip(),'Missing project path')
        path=(root/value).resolve()
        require(path.is_relative_to(root),'Path is outside project root: '+str(value))
        return path,path.relative_to(root).as_posix()

    def read(value):
        path,name=locate(value);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        require(name not in hashes or hashes[name]==digest,'Input changed during audit: '+name)
        hashes[name]=digest
        return name,raw.decode('utf-8')

    def visit(value):
        _,name=locate(value)
        require(name not in active,'Cyclic meaning basis inheritance: '+name)
        if name in cache:return cache[name]
        active.add(name)
        _,text=read(name);basis=json.loads(text,object_pairs_hook=_object)
        require(isinstance(basis,dict),'Semantic basis must be an object: '+name)
        docname,body=read(basis.get('document'));doc=_parse(body)
        parent=basis.get('inherited_meaning_basis')
        if parent is None:
            require('parent' not in basis and 'new_signatures' not in basis,'Incomplete inheritance metadata: '+name)
            entries=_coverage(doc['declarations'],basis,name);lineage=[]
            changes=dict(added=len(doc['statements']),removed=0,same_order_and_contents=False)
        else:
            prior,priorname,entries,lineage=visit(parent)
            _,declared_parent=locate(basis.get('parent'))
            require(priorname==declared_parent,'Parent document disagrees with inherited basis: '+name)
            prior_edition=tuple(map(int,prior['schema_version'].split('.')));edition=tuple(map(int,doc['schema_version'].split('.')))
            require(edition>=prior_edition,'An inheritance edge downgrades the edition: '+name)
            size=len(prior['declarations'])
            require(doc['declarations'][:size]==prior['declarations'],'Inherited declarations changed or were removed: '+name)
            added=doc['declarations'][size:]
            signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added}
            require(basis.get('new_signatures')==signatures,'Delta signatures differ: '+name)
            additions=_coverage(added,basis,name)
            require(not set(additions)&set(entries),'Inherited meanings were redefined: '+name)
            entries=dict(entries,**additions);lineage=deepcopy(lineage)
            changes=_statement_changes(prior['statements'],doc['statements'])
        for entry in entries.values():
            if entry['meaning_basis']==name:entry['declaration_document']=docname
        caveats={key:deepcopy(basis[key]) for key in ('unresolved','limitations') if key in basis}
        lineage.append(dict(basis=name,document=docname,edition=doc['schema_version'],declarations=len(doc['declarations']),
            statement_changes=changes,caveats=caveats))
        active.remove(name);result=(doc,docname,entries,lineage);cache[name]=result
        return result

    document,name,entries,lineage=visit(basis_path);_,basisname=locate(basis_path);projection=None
    if document_path is not None:
        selectedname,body=read(document_path);selected=_parse(body)
        names={d['name'] for d in selected['declarations']}
        require(selected['schema_version']==document['schema_version'],'Projection edition differs')
        require(selected['declarations']==[d for d in document['declarations'] if d['name'] in names],
            'Projection adds, changes or reorders declarations')
        require(names<=set(entries),'Projection has undocumented declarations')
        projection=dict(source_document=name,retained_declarations=len(names),
            omitted_declarations=len(entries)-len(names),statement_comparison=_statement_changes(document['statements'],selected['statements']))
        entries={n:entries[n] for n in entries if n in names};document,name=selected,selectedname
    catalog=Catalog(deepcopy(document),name,basisname,deepcopy(entries),deepcopy(lineage),dict(hashes),projection)
    catalog.audit()
    return catalog


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation',choices=('audit','explain'))
    cli.add_argument('--root',type=Path,default=Path.cwd())
    cli.add_argument('--basis',required=True)
    cli.add_argument('--document',help='Optional unchanged declaration projection')
    cli.add_argument('--symbol',action='append',default=[])
    cli.add_argument('--output','-o',type=Path)
    args=cli.parse_args(argv)
    try:
        require(args.operation=='explain' or not args.symbol,'--symbol is only valid with explain')
        catalog=load_catalog(args.root,args.basis,document_path=args.document)
        result=catalog.explain(args.symbol) if args.operation=='explain' else catalog.audit()
        body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        else:print(body,end='')
    except (ValueError,OSError) as exc:
        print('Meaning catalog: '+str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
