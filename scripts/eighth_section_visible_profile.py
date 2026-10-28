"""Optional radiation energy and optical method contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.seventh_section_visible_profile import ROOT,SeventhSectionVisibleVocabulary,write_once
from scripts.eighth_section_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/eighth-section-visible-profile-v1.noema'
BASIS='data/eighth-section-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-eighth-section-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'approximateclaimorder': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'rain'], 'radiativeenergydensitymodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'town'], 'radiationportionregion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'home'], 'presentsanchoredscalarquestion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'above'], 'processforcecontributionmodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'give'], 'reflectedwavemodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'inside'], 'interfaceenergyflowmodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'birdone'], 'presentsanchoredsixvaluequestion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'treeone'], 'closesexplanationseries': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'aki'], 'finiteenergybalancemodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'nao'], 'sourcequantitativecontent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'book'], 'comparisontheoryrange': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'fruit'], 'bodyprocessinfluence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'red'], 'fieldanswerrecord': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'round'], 'physicalproblemclassification': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'bird'], 'problemphysicalsetting': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'rain', 'fly'], 'problemquestion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'rain'], 'methodanswerconstruction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'town'], 'methodessentialoperation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'home'], 'priorusedmethod': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'above'], 'presentsmethodconsequence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'give'], 'realvaluetransformationtopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'book', 'town', 'inside']}
CONTEXT=['同じ放射部分・波・鏡面・基準系・単位・物理設定の対応を保持する。', '印刷式、物理的な変換、近似次数、量的内容の比較、方法と著者への帰属を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile77。既存22契約の意味・型・引数順序を保持する。', '文全体の原始語を加えず、エネルギー・体積・反射・圧力・一般問題への方法は既存定義から合成する。', '同じ光の部分を光子の個数へ替えない。局所流と正味流、面積と体積、位相平均と瞬間値を区別する。', '印刷式の不一致と保存済み反例を保持する。先頭近似を無制限の等式や一次までの近似へ変えない。', '帰属・方法参照から実証済みや全問題の可解性を導かない。未知の入力を補わない。', '本文統合と可視復号は別途確認する。有限束縛診断を全実数・全関数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_eighth_section_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=77,parent_profile=76,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/bookを放射エネルギー・反射・近似・光学的方法の公開規約の語群とする。後続二要素は規約の綴りを区別し、文全体の意味は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class EighthSectionVisibleVocabulary(SeventhSectionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'EighthSection-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'EighthSection-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'EighthSection-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-eighth-section-visible-profile-1',edition=77)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def build_report():
    """Verify contract preservation; this does not award document integration."""
    import hashlib
    import sys
    from scripts.check_manuscript_context import catalogs
    catalog=catalogs()['einstein-1905']
    parent=SeventhSectionVisibleVocabulary()
    vocabulary=EighthSectionVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==953 and len(vocabulary._words)==975,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/eighth_section_visible_profile.py',
        'scripts/eighth_section_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    for cls in type(vocabulary).__mro__:
        module=sys.modules[cls.__module__]
        if not cls.__module__.startswith('scripts.'):
            continue
        paths.add(str(__import__('pathlib').Path(module.__file__).resolve().relative_to(ROOT)).replace('\\','/'))
        for name in ('LIBRARY','BASIS','MANIFEST'):
            path=getattr(module,name,None)
            if isinstance(path,str) and (ROOT/path).is_file():
                paths.add(path)
    source={}
    for old,new in SOURCE_RELATIONS.items():
        row=catalog.entries[old];d=row['declaration'];contract=CONTRACTS[new]
        expected=dict(parameters=d['parameters'],result=d['result'],arguments=row['arguments'],
            meaning_ja=row['meaning_ja'].removeprefix('[current の記号名] '))
        require(contract==expected,'Source contract changed: '+old)
        require(old not in CONTRACTS and new not in parent._words,'Local primitive or duplicate public contract')
        paths.update((row['meaning_basis'],row['declaration_document']))
        source[old]=dict(public_name=new,meaning_basis=row['meaning_basis'],
            declaration_document=row['declaration_document'])
    require(len(source)==22 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-eighth-section-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=77,parent_edition=76,
        words=975,parent_words=953,new_public_contracts=22,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
