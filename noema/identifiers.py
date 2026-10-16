"""Orthographic annotations for designation objects, never identity inference."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from .meaning_catalog import load_catalog,BasisError,_object


def require(condition,message):
    if not condition:raise BasisError(message)


def scalar_text(value,label):
    require(isinstance(value,str) and bool(value.strip()),'Empty or invalid '+label)
    try:value.encode('utf-8')
    except UnicodeEncodeError:raise BasisError('Non-scalar Unicode in '+label) from None
    return value


class IdentifierAnnotations:
    def __init__(self,catalog,annotations,path,digest):
        self.catalog=catalog;self.annotations=deepcopy(annotations);self.path=path;self.digest=digest

    def show(self):
        return dict(status='orthographic_designation_annotations_only',document=self.catalog.document_path,
            basis=self.catalog.basis_path,annotations=self.path,entries=deepcopy(self.annotations['entries']),
            referent_identity_inferred=False,conceptual_meaning_certified=False,source_coverage_certified=False,
            source_sha256={**self.catalog.source_sha256,self.path:self.digest})

    def find(self,text,language=None):
        scalar_text(text,'search text')
        if language is not None:scalar_text(language,'language label')
        matches=[]
        for entry in self.annotations['entries']:
            forms=[f for f in entry['forms'] if f['text']==text and (language is None or f['language']==language)]
            if forms:matches.append(dict(symbol=entry['symbol'],forms=deepcopy(forms)))
        result=self.show();result.pop('entries');result.update(query=text,language=language,matches=matches,
            matching='Exact Unicode scalar sequence; no normalization, case folding, transliteration or referent selection.')
        return result


def load_annotations(root,basis_path,annotations_path):
    root=Path(root).resolve();path=(root/annotations_path).resolve()
    require(path.is_relative_to(root),'Annotations path is outside project root')
    raw=path.read_bytes();data=json.loads(raw.decode('utf-8'),object_pairs_hook=_object)
    require(isinstance(data,dict) and set(data)=={'schema_version','document','document_sha256','entries'},'Invalid identifier annotation fields')
    require(data['schema_version']=='noema-identifiers-1','Unsupported identifier annotation edition')
    catalog=load_catalog(root,basis_path)
    require(data['document']==catalog.document_path,'Identifier document differs from meaning basis')
    require(data['document_sha256']==catalog.source_sha256[catalog.document_path],'Identifier document digest differs')
    require(isinstance(data['entries'],list) and data['entries'],'No designation entries')
    seen=set()
    for entry in data['entries']:
        require(isinstance(entry,dict) and set(entry)=={'symbol','role','forms'},'Invalid designation entry fields')
        symbol=scalar_text(entry['symbol'],'designation symbol')
        require(symbol not in seen,'Duplicate designation symbol: '+symbol);seen.add(symbol)
        require(entry['role']=='designation','Only designation objects may receive identifier forms')
        require(symbol in catalog.entries,'Unknown designation symbol: '+symbol)
        declaration=catalog.entries[symbol]['declaration']
        require(declaration['parameters']==[] and declaration['result']=='individual','Designation must be a closed individual: '+symbol)
        require(isinstance(entry['forms'],list) and entry['forms'],'No forms for designation: '+symbol)
        forms=set()
        for form in entry['forms']:
            require(isinstance(form,dict) and set(form)=={'text','language','role'},'Invalid identifier form fields')
            key=tuple(scalar_text(form[k],k) for k in ('text','language','role'))
            require(key not in forms,'Duplicate identifier form: '+symbol);forms.add(key)
    return IdentifierAnnotations(catalog,data,path.relative_to(root).as_posix(),hashlib.sha256(raw).hexdigest())


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation',choices=('show','find'));cli.add_argument('--root',type=Path,default=Path.cwd())
    cli.add_argument('--basis',required=True);cli.add_argument('--annotations',required=True)
    cli.add_argument('--text');cli.add_argument('--language');cli.add_argument('--output',type=Path)
    args=cli.parse_args(argv)
    try:
        require(args.operation=='find' or args.text is None and args.language is None,'Search arguments require find')
        annotations=load_annotations(args.root,args.basis,args.annotations)
        result=annotations.show() if args.operation=='show' else annotations.find(args.text,args.language)
        body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        else:print(body,end='')
    except (ValueError,OSError) as error:
        print('Identifier annotations: '+str(error),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
