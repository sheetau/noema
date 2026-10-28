"""Optional energy attribution and discourse contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.activity_role_visible_profile import ROOT,ActivityRoleVisibleVocabulary,write_once
from scripts.tenth_energy_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/tenth-energy-visible-profile-v1.noema'
BASIS='data/tenth-energy-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-tenth-energy-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'translationalkineticenergy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'home'], 'fieldenergywithdrawal': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'above'], 'outgoingradiatedenergy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'give'], 'mechanicalworkunit': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'inside'], 'undertakesquantitydetermination': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'aki'], 'electricfieldmodelcorrespondence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'nao'], 'presentsanalogousresults': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'book']}
CONTEXT=['同じ対象・場・運動過程・基準系・出来事・単位・適用状況を保持する。', 'エネルギーの物理的帰属、数量モデル、保存の条件、計算と著者の論述を区別する。', '運動・場からの移転・放射の値は一般関係で指定し、特定の速度式や原文の結論を語義へ埋め込まない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile82。既存の一般7契約の型・引数順序・意味を保持する。', '各式のWや特定の粒子・場・過程・履歴は本文の参照で構成し、一般語彙の原始語には追加しない。', '場から取り出す仕事、粒子の運動エネルギー、放射損失を区別し、等値や無放射は別の条件として合成する。', '量を決定する取組は答えの発見済みを含意せず、先行結果との類似は同値性や証明完了を含意しない。', '語彙検査は本文の意味接続、実数全域の証明、実SVGからの復号とは別である。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_tenth_energy_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=82,parent_profile=81,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='力・測定・比較の語群に続けて、エネルギー帰属と一般論述の七関係を区別する。原文の式・対象・過程は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TenthEnergyVisibleVocabulary(ActivityRoleVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TenthEnergy-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TenthEnergy-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TenthEnergy-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-tenth-energy-visible-profile-1',edition=82)
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
    parent=ActivityRoleVisibleVocabulary()
    vocabulary=TenthEnergyVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1039 and len(vocabulary._words)==1046,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/tenth_energy_visible_profile.py',
        'scripts/tenth_energy_visible_profile_contracts.py','data/writing-freeze-v1.json',
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
    aliases={}
    for old,new in MATH_ALIASES.items():
        row=catalog.entries[old];d=row['declaration'];prior=before['primitives'][new]
        meaning=row['meaning_ja'].removeprefix('[paths の記号名] ')
        require(d['parameters']==prior['parameters'] and d['result']==prior['result'],'Arithmetic alias type changed')
        require(meaning==before['compounds'][new]['meaning'],'Arithmetic alias meaning changed')
        aliases[old]=new
    require(len(source)==7 and not EXTRA and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-tenth-energy-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=82,parent_edition=81,
        words=1046,parent_words=1039,new_public_contracts=7,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
