"""Edition four: preserve eighty words and import norm/discourse definitions."""
from copy import deepcopy
import json
from noema.constructed import parse
from scripts.visible_compound_vocabulary import CompoundVocabulary,check_compound_extension,ROOT,SCHEMA as PARENT_SCHEMA
from scripts.visible_lexical_script import require

SCHEMA='noema-visible-scope-vocabulary-1'
MANIFEST='noema/resources/visible-scope-vocabulary-v1.json'
MODULES=[dict(document='examples/v016/shared-'+n+'-v1.noema',basis='data/shared-'+n+'-basis-v1.json')
         for n in ('norms','discourse')]


class ScopeVocabulary(CompoundVocabulary):
    def __init__(self,document=None):
        parent=CompoundVocabulary()
        if document is None:
            source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
            require(source['schema']=='noema-visible-vocabulary-extension-source-1' and source['edition']==4
                    and source['parent_edition']==3 and source['modules']==MODULES,'Unknown scope vocabulary source')
            document=parent.document();added=set()
            for module in MODULES:
                library=parse((ROOT/module['document']).read_text(encoding='utf-8'))
                basis=json.loads((ROOT/module['basis']).read_text(encoding='utf-8'))
                names={d['name'] for d in library['declarations']}
                require(library['schema_version']=='0.16' and not library['statements'] and not basis['primitives']
                        and basis['document']==module['document'] and names==set(basis['definitions'])==set(basis['public_contracts']),
                        'Shared module and public inventory differ')
                require(not names&(set(document['entries'])|set(document['compounds'])),'Shared name collision')
                for d in library['declarations']:
                    n=d['name'];contract=basis['public_contracts'][n]
                    require(d['kind']=='definition','Shared definition became primitive')
                    require([p['sort'] for p in d['parameters']]==[p['sort'] for p in contract['arguments']]
                            and d['result']==contract['result'],'Shared signature differs')
                    require(n in source['spellings'],'Missing public spelling')
                    document['definitions'][n]=d
                    document['compounds'][n]=dict(parts=source['spellings'][n],parameters=[p['sort'] for p in d['parameters']],
                        result=d['result'],roles=[p['role'] for p in contract['arguments']],meaning=basis['definitions'][n],
                        context=[p['role']+': '+p['interpretation'] for p in contract['arguments']],contrast=basis['limitations'],aliases=[])
                added.update(names)
            require(added==set(source['spellings']),'Unmatched public spelling')
            document['naming_convention']+='\n'+source['naming_convention']
            document.update(schema=SCHEMA,edition=4)
        data=deepcopy(document)
        require(isinstance(data,dict) and data.get('schema')==SCHEMA and type(data.get('edition')) is int
                and data['edition']==4,'Invalid scope vocabulary')
        # Reuse the pinned structural checks; do not alter the old dictionary or reader.
        data.update(schema=PARENT_SCHEMA,edition=3)
        super().__init__(data)
        check_compound_extension(parent,self)
        self._document.update(schema=SCHEMA,edition=4)
