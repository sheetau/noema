"""General closing-item references and name records, distinct from frontmatter."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.agency_inquiry_visible_profile import ROOT,AgencyInquiryVisibleVocabulary,write_once
from scripts.closing_presentation_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/closing-presentation-profile-v1.noema'
BASIS='data/closing-presentation-profile-basis-v1.json'
MANIFEST='noema/resources/visible-closing-presentation-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'closingreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'nao', 'home', 'home'], 'closingpresentationrecord': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'nao', 'home', 'above']}
CONTEXT=['同じ対象文章の提示と後付項目の区分規約を固定する。位置は正整数で、本文段落や前付の番号と混同しない。', '名称使用・名称・対象・文書の4役割を保持し、その関係の真偽は別の入力で与える。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile91。', '位置は語義の番号ではない。本文の意味、対象の同一性、著者役割は位置参照と別に記述する。', '有限実装は未知位置、未知の記録、不正な座標を拒否する。欠けた事実を偽や既定の人物として補わない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_closing_presentation_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=91,parent_profile=90,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='本文後の位置と名称表示の参照を、前付や本文の意味から区別する一般語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ClosingPresentationVocabulary(AgencyInquiryVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Early-reference-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Early-reference-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Early-reference-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-closing-presentation-profile-1',edition=91)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class ClosingPresentationReferences:
    """Known locations and four-field records; no author facts are inferred."""
    def __init__(self,locations,records):
        self.locations={};self.records={}
        for (context,item),value in locations.items():
            key=(context,self.coordinate(item))
            require(key not in self.locations,'Repeated closing position')
            require(all(c!=context or prior!=value for (c,_),prior in self.locations.items()),'Distinct closing items share a location')
            self.locations[key]=value
        for (context,item),record in records.items():
            key=(context,self.coordinate(item))
            require(key in self.locations,'Closing record has no known location')
            require(key not in self.records,'Repeated closing record')
            require(isinstance(record,(list,tuple)) and len(record)==4,'Expected four named presentation roles')
            self.records[key]=tuple(record)

    @staticmethod
    def coordinate(item):
        from fractions import Fraction
        require(not isinstance(item,bool) and isinstance(item,(int,Fraction)) and item>0 and item==int(item),
            'Expected positive integer closing item')
        return int(item)

    def reference(self,context,item):
        key=(context,self.coordinate(item));require(key in self.locations,'Unknown closing position')
        return self.locations[key]

    def record(self,context,item):
        from noema.constructed_semantics import FunctionValue
        from scripts.name_presentation_profile import SELECTOR,I
        key=(context,self.coordinate(item));require(key in self.records,'Unknown closing record')
        values=self.records[key]
        return FunctionValue((SELECTOR,),I,lambda selector:selector(*values))

    def handlers(self):
        return dict(closingreference=self.reference,closingpresentationrecord=self.record)


def build_report():
    import hashlib,sys
    parent=AgencyInquiryVisibleVocabulary();vocabulary=ClosingPresentationVocabulary()
    require(len(parent._words)==1153 and len(vocabulary._words)==1155,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/closing_presentation_profile.py',
        'scripts/closing_presentation_profile_contracts.py','tests/test_closing_presentation_profile.py',
        'scripts/name_presentation_profile.py','data/writing-freeze-v1.json'}
    for cls in type(vocabulary).__mro__:
        if not cls.__module__.startswith('scripts.'):continue
        module=sys.modules[cls.__module__]
        paths.add(__import__('pathlib').Path(module.__file__).resolve().relative_to(ROOT).as_posix())
        for name in ('LIBRARY','BASIS','MANIFEST'):
            p=getattr(module,name,None)
            if isinstance(p,str) and (ROOT/p).is_file():paths.add(p)
    for name in tuple(sys.modules):
        if name.startswith('scripts.') and name.endswith('_contracts'):
            paths.add(__import__('pathlib').Path(sys.modules[name].__file__).resolve().relative_to(ROOT).as_posix())
    require(not CONTRACTS and not SOURCE_RELATIONS and not MATH_ALIASES and len(EXTRA)==2,'Unexpected source contracts')
    return dict(schema='noema-closing-presentation-profile-check-1',edition=91,parent_edition=90,
        words=1155,parent_words=1153,new_reference_primitives=2,new_core_words=0,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
