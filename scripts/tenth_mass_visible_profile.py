"""Optional force, measurement and comparison contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.tenth_motion_visible_profile import ROOT,TenthMotionVisibleVocabulary,write_once
from scripts.tenth_mass_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/tenth-mass-visible-profile-v1.noema'
BASIS='data/tenth-mass-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-tenth-mass-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'forceaccelerationconvention': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'home'], 'comparisonprocedurerequirement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'above'], 'comparisonactor': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'give'], 'comparisonlefttheory': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'inside'], 'comparisonrighttheory': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'aki'], 'comparisonfield': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'nao'], 'comparisoncases': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'book'], 'comparisonmismatchconclusion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'home', 'round'], 'comparisoninterpretations': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'home'], 'comparisonmeaningcorrespondence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'above'], 'comparisonunitnormalization': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'give'], 'comparisonphysicalcorrespondence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'inside'], 'comparisonleftvalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'aki'], 'comparisonrightvalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao'], 'assignedchargevalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book'], 'addedchargeamount': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'round'], 'chargeadditionoperation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'home'], 'reversibleelasticresponse': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'above'], 'calibratedelasticinstrument': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'give'], 'directedloadcomparison': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'inside'], 'conditionalcutpairinquiry': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'aki'], 'conventionalinquiryframing': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'nao'], 'adoptunqualifieddesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'book'], 'directionalcoefficientdesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round'], 'operationalquantityredefinition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'home'], 'distinctoperationalquantitydefinition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'above'], 'conventioncomparisonalternative': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'give'], 'theorylawmembership': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'inside'], 'theorycomparisonactivity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'aki'], 'relevantcomparisonaspect': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'nao'], 'attentiveexamination': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'book'], 'markedlyabovestandard': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'inside', 'round'], 'ponderablepointidealization': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'home'], 'mechanicalforceattribution': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'above'], 'priorsenselimiteddesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'give']}
CONTEXT=['同じ物理設定、力を評価する系、加速度を測る系、単位、規約と文脈を区別する。', '質問、測定可能性、規約の採用、注意の要求と実際の結果を分ける。', '関数値の語は各引数へ適用する一般規約であり、原文の一文や特定の結果を丸ごと表す原始語ではない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile80。既存35契約の型・引数順序・意味を公開する。', '力、加速度、質量係数は旧定義で合成する。原文の横質量を別の現代的規約へ置換しない。', 'ばね秤で測り得ることから測定済みや特定の軌道の保持を補わない。', '比較の注意要求、規約の差、理論の真理、正規化した数値の差を区別する。', '構文・型検査は原文の意味判断や一般実数域の証明とは別であり、本文の参照と実SVG統合は後続で確認する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_tenth_mass_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=80,parent_profile=79,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/treeone/insideを力・測定・比較の公開規約の語群とする。後続二要素で語を区別し、文全体は既存の構文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TenthMassVisibleVocabulary(TenthMotionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TenthMass-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TenthMass-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TenthMass-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-tenth-mass-visible-profile-1',edition=80)
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
    parent=TenthMotionVisibleVocabulary()
    vocabulary=TenthMassVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1002 and len(vocabulary._words)==1037,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/tenth_mass_visible_profile.py',
        'scripts/tenth_mass_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    paths.add('tests/test_tenth_mass_visible_profile.py')
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
    require(len(source)==35 and not EXTRA and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-tenth-mass-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=80,parent_edition=79,
        words=1037,parent_words=1002,new_public_contracts=35,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})

