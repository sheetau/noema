"""General speed-parameter conventions and hypothetical propagation carriers."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.frontmatter_reference_visible_profile import ROOT,FrontmatterReferenceVisibleVocabulary,write_once
from scripts.early_reference_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/early-reference-visible-profile-v1.noema'
BASIS='data/early-reference-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-early-reference-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'signalvelocityratioparameter': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'inside', 'home', 'home'], 'directionpreservingscalelimit': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'inside', 'home', 'above'], 'completeparameterdirections': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'inside', 'home', 'give'], 'hypothesizedpropagationmedium': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'inside', 'home', 'inside']}
CONTEXT=['同じ対象・速度尺度・比較系列・適用範囲と解釈文脈を保持する。', 'propagation_kindは個体・参照系・状況を引数とする伝播分類の閉じた記述であり、引用を実行しない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile89。一般的な四関係を別々の入力として扱う。', '物理量の帰属・極限規約・範囲の完全性は解釈の入力であり、有限の例から保証しない。', '次数、成立する法則、確認試行の成功、媒体の実在や理論上の必要性は各関係から導かない。', '原文の対象参照を説明する役割定義と、原文の主張・仮定・引用は別に合成して検証する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_early_reference_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=89,parent_profile=88,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='速度比・方向を保った縮小・適用範囲と、仮説的な伝播媒体の役割を区別する一般語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class EarlyReferenceVisibleVocabulary(FrontmatterReferenceVisibleVocabulary):
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
        data.update(schema='noema-visible-early-reference-visible-profile-1',edition=89)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def build_report():
    import hashlib,sys
    parent=FrontmatterReferenceVisibleVocabulary();vocabulary=EarlyReferenceVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1130 and len(vocabulary._words)==1134,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/early_reference_visible_profile.py',
           'scripts/early_reference_visible_profile_contracts.py','tests/test_early_reference_visible_profile.py',
           'scripts/early_individual_reference_roles.py','tests/test_early_individual_reference_roles.py',
           'data/writing-freeze-v1.json','data/relativity-conjecture-basis-v1.json',
           'data/relativity-conjecture-reading-v1.json','data/ether-dispensability-basis-v1.json'}
    for cls in type(vocabulary).__mro__:
        if not cls.__module__.startswith('scripts.'):continue
        module=sys.modules[cls.__module__]
        paths.add(__import__('pathlib').Path(module.__file__).resolve().relative_to(ROOT).as_posix())
        for name in ('LIBRARY','BASIS','MANIFEST'):
            p=getattr(module,name,None)
            if isinstance(p,str) and (ROOT/p).is_file():paths.add(p)
    require(not CONTRACTS and not SOURCE_RELATIONS and not MATH_ALIASES and len(EXTRA)==4,'Unexpected source-specific contracts')
    return dict(schema='noema-early-reference-visible-profile-check-1',
        status='general_reference_constraints_and_frozen_parent_preserved',edition=89,parent_edition=88,
        words=1134,parent_words=1130,new_reference_primitives=0,new_general_contracts=4,new_core_words=0,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})

