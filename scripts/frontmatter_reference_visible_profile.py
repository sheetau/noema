"""Positional frontmatter reference, separate from body paragraphs and headings."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.early_visible_profile import ROOT,EarlyVisibleVocabulary,write_once
from scripts.frontmatter_reference_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/frontmatter-reference-visible-profile-v1.noema'
BASIS='data/frontmatter-reference-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-frontmatter-reference-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'frontmatterreference':['above','round','treeone','home','nao','book','birdone','fruit','treeone','inside','nao','give','home','home']}
CONTEXT=['前付の提示文脈と1始まりの項目順を使用時に固定する。本文の文脈・段落・見出し順とは分けて照合する。']
LIMITS=['固定アルファベットと共通375語は変更しない。', '位置は語義の辞書番号ではなく、項目の内容は別に記述する。', '有限の参照実装は未知の文脈・項目、非正整数や重複した位置対応を拒否し、既定の値で補わない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_frontmatter_reference_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=88,parent_profile=87,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='前付項目の位置を本文の段落・見出しから区別する一般的な参照語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class FrontmatterReferenceVisibleVocabulary(EarlyVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Frontmatter-reference-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Frontmatter-reference-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Frontmatter-reference-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-frontmatter-reference-visible-profile-1',edition=88)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def build_report():
    import hashlib,sys
    parent=EarlyVisibleVocabulary();vocabulary=FrontmatterReferenceVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1129 and len(vocabulary._words)==1130,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/frontmatter_reference_visible_profile.py',
           'scripts/frontmatter_reference_visible_profile_contracts.py','tests/test_frontmatter_reference_visible_profile.py',
           'data/writing-freeze-v1.json'}
    for cls in type(vocabulary).__mro__:
        if not cls.__module__.startswith('scripts.'):continue
        module=sys.modules[cls.__module__]
        paths.add(__import__('pathlib').Path(module.__file__).resolve().relative_to(ROOT).as_posix())
        for name in ('LIBRARY','BASIS','MANIFEST'):
            p=getattr(module,name,None)
            if isinstance(p,str) and (ROOT/p).is_file():paths.add(p)
    require(not CONTRACTS and not SOURCE_RELATIONS and not MATH_ALIASES and len(EXTRA)==1,'Unexpected source-specific contracts')
    return dict(schema='noema-frontmatter-reference-visible-profile-check-1',
        status='general_frontmatter_reference_and_frozen_parent_preserved',edition=88,parent_edition=87,
        words=1130,parent_words=1129,new_reference_primitives=1,new_core_words=0,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


class FrontmatterReferences:
    """Resolve known positions without assertions about their text or subjects."""
    def __init__(self,rows):
        from fractions import Fraction
        self.rows={}
        for (context,item),value in rows.items():
            require(not isinstance(item,bool) and isinstance(item,(int,Fraction)) and item>0 and item==int(item),
                    'Expected positive integer frontmatter item')
            key=(context,int(item))
            require(key not in self.rows,'Duplicate frontmatter position')
            require(all(c!=context or prior!=value for (c,_),prior in self.rows.items()),'Distinct frontmatter items share a location')
            self.rows[key]=value

    def reference(self,context,item):
        from fractions import Fraction
        require(not isinstance(item,bool) and isinstance(item,(int,Fraction)) and item>0 and item==int(item),
                'Expected positive integer frontmatter item')
        key=(context,int(item))
        require(key in self.rows,'Unknown frontmatter position')
        return self.rows[key]

    def handlers(self):return {'frontmatterreference':self.reference}
