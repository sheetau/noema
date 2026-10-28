"""Optional charge, conditional foundation and discourse contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.eighth_section_visible_profile import ROOT,EighthSectionVisibleVocabulary,write_once
from scripts.ninth_section_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/ninth-section-visible-profile-v1.noema'
BASIS='data/ninth-section-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-ninth-section-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'distributionmembershipfunction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'rain'], 'theoryfoundationaldependence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'town'], 'distributionsignedamount': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'home'], 'materialpartsignedamount': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'above'], 'contextualsizebound': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'give'], 'designationcarriermodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'inside'], 'inquiryproblemrange': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'birdone'], 'conditionalfoundationaladoption': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'treeone'], 'settingscalarfielddesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'aki'], 'settingvectorfielddesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'nao'], 'referstopriorcontent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'book'], 'conditionallawcontent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'fruit'], 'contentimportance': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'red'], 'conciseexposition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'round'], 'supplementaryremarkproposal': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'fruit', 'rain', 'bird']}
CONTEXT=['同じ分布・追跡物質部分・場・基準系・出来事・単位・文脈を保持する。', '物理的な帰属、条件付き法則の採用、表記解釈、論述の提示と内容の真理を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile78。既存15契約の型・引数順序・意味を公開する。', '文全体の原始語を加えず、同時刻断面、電荷密度、流速、担体、変換、基礎と原理への適合を既存定義から合成する。', '符号付き電荷の相殺を許し、零量を担体の不在と同一視しない。点の量、空間領域の量、同じ物質部分の量を区別する。', '条件と法則は同じ設定へ適用する。採用や提示から現実成立・実測・理論全体の可導出性を追加しない。', '原刊の磁気側係数の欠落と採用読解を保持する。未知入力を補わず、歴史的な担体名に現代の全性質を加えない。', '実SVG復号、意味判断、有限診断と一般実数域の証明を区別する。本文統合は別途確認する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_ninth_section_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=78,parent_profile=77,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/fruitを電荷分布・条件付き基礎・論述の公開規約の語群とする。後続二要素は規約の綴りを区別し、文全体は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class NinthSectionVisibleVocabulary(EighthSectionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'NinthSection-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'NinthSection-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'NinthSection-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-ninth-section-visible-profile-1',edition=78)
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
    parent=EighthSectionVisibleVocabulary()
    vocabulary=NinthSectionVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==975 and len(vocabulary._words)==990,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/ninth_section_visible_profile.py',
        'scripts/ninth_section_visible_profile_contracts.py','data/writing-freeze-v1.json',
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
    require(len(source)==15 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-ninth-section-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=78,parent_edition=77,
        words=990,parent_words=975,new_public_contracts=15,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
