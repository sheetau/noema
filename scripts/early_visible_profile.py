"""Optional inquiry, attribution and interaction contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.closing_function_reference_visible_profile import ROOT,ClosingFunctionReferenceVisibleVocabulary,write_once
from scripts.early_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/early-visible-profile-v1.noema'
BASIS='data/early-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-early-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'contentconsideration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'home'], 'intendeddocumentreader': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'above'], 'attributedcommonknowledge': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'give'], 'bodysurroundingregion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'inside'], 'sourceelectricfieldgeneration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'aki'], 'regionalelectricfieldenergy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'nao'], 'electricfielddrivencurrent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'book'], 'admissibleinteractioncase': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'home', 'round'], 'motionmagneticdrive': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'home'], 'driveintrinsicstoredenergy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'above'], 'localdrivencurrent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'give'], 'scopedcomponentcontrast': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'inside'], 'positivealternativeformulation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'aki'], 'documenttitlepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'nao'], 'documenttopiccontribution': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'book'], 'attributedpriorconfirmation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'above', 'round'], 'conjecturalgrounds': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'home'], 'conjecturalstatus': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'above'], 'analogouscasekind': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'give'], 'contextualexampledomain': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'inside'], 'contextualattemptdomain': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'aki'], 'observationalverificationattempt': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'nao'], 'observationalgoalachievement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'book'], 'hypothesizedmediumframe': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'give', 'round'], 'spatialpointmembership': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'home'], 'velocityvectorrecord': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'above'], 'velocityvectorcomponents': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'give'], 'intrinsicspacepointvelocity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'inside'], 'scopepreservingtheoreticalalternative': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'aki'], 'apparentclaimcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'nao'], 'privilegedrestspaceconcept': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'book'], 'privilegedspatialproperty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'inside', 'round'], 'materialmediumfreevacuumregion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'home'], 'scopequalifiedexplanation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'above'], 'physicalframebody': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'give'], 'physicalreferentialinterpretation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'inside'], 'treatmentofinquiryfact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'aki'], 'sufficientfactconsideration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'nao'], 'conceptualinquirydifficulty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'book'], 'historicallyunresolveddifficulty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'aki', 'round'], 'foundationalinquirydifficultycause': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'nao', 'home'], 'contextualdifficultydomain': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'nao', 'above'], 'simultaneityrelationinquiry': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'above', 'nao', 'give']}
CONTEXT=['同じ対象・文書・提示文脈・評価状況と、各関係が受け取る範囲を保持する。', '引用した内容の検討、帰属、推測、理論上の説明と、内容の真理や実験による確認を区別する。', '場・エネルギー・駆動・電流・速度記録と参照枠の関係を、型と引数順序を保って組み合わせる。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile87。一般43契約を既存の意味規約から移し、有理数の四演算関係は継承する。', '個別の原文・地球・仮説上の媒質・展開変数は本文の参照と定義で構成し、一般原始語へ追加しない。', '確認試行の不成功は目的の偽を含意しない。見かけの両立困難、推測、著者への帰属を事実の断定へ変えない。', '場の生成、場のエネルギー、磁気的駆動、観測される電流を区別する。速度の成分は同じ参照枠と順序を保持する。', '原文に現れる識別子を説明の追跡用に保持する。本文の定義と参照の統合、実SVG復号、有限診断は別に確認する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_early_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=87,parent_profile=86,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='探究と帰属、相互作用と空間記述の一般語彙。個別の対象や主張は本文で構成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class EarlyVisibleVocabulary(ClosingFunctionReferenceVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Early-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Early-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Early-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-early-visible-profile-1',edition=87)
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
    parent=ClosingFunctionReferenceVisibleVocabulary()
    vocabulary=EarlyVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1086 and len(vocabulary._words)==1129,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/early_visible_profile.py',
        'scripts/early_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    paths.add('tests/test_early_visible_profile.py')
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
        meaning=row['meaning_ja'].removeprefix('[paths の記号名] ').removeprefix('[current の記号名] ')
        require(d['parameters']==prior['parameters'] and d['result']==prior['result'],'Arithmetic alias type changed')
        require(meaning==before['compounds'][new]['meaning'],'Arithmetic alias meaning changed')
        aliases[old]=new
    require(len(source)==43 and not EXTRA and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-early-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=87,parent_edition=86,
        words=1129,parent_words=1086,new_public_contracts=43,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
