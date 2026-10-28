"""General closed energy accounting and rational reference contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.tenth_energy_visible_profile import ROOT,TenthEnergyVisibleVocabulary,write_once
from scripts.energy_reference_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/energy-reference-visible-profile-v1.noema'
BASIS='data/energy-reference-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-energy-reference-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'closedenergyexchange': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'round'], 'describedrationalreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'nao', 'fruit']}
CONTEXT=['過程・粒子・場・系・開始と終了・単位・状況を保持する。', '参照取得、閉じた役割の成立、保存の数式と収支の物理的条件を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile83。既存の閉じた収支条件の一般関数と型付き有理数参照を追加する。', 'closedenergyexchangeは引数で指定する過程に他の移転や内部変化がない条件であり、数値的保存式や放射零を自動的に含意しない。', '有理数参照は既知の候補だけを返す。単位尺度の正性や役割の成立は本文で別に述べる。', '構文・型・有限診断は全文の意味判断、実数全域の証明、実SVGからの復号とは別である。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_energy_reference_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=83,parent_profile=82,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='エネルギー帰属の語群に、一般的な閉じた収支条件と有理数候補への記述参照を続ける。個別の値や結論は語義へ埋め込まない。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class EnergyReferenceVisibleVocabulary(TenthEnergyVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'EnergyReference-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'EnergyReference-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'EnergyReference-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-energy-reference-visible-profile-1',edition=83)
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
    parent=TenthEnergyVisibleVocabulary()
    vocabulary=EnergyReferenceVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1046 and len(vocabulary._words)==1048,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/energy_reference_visible_profile.py',
        'scripts/energy_reference_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    paths.add('tests/test_energy_reference_visible_profile.py')
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
    require(len(source)==1 and len(EXTRA)==1 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-energy-reference-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=83,parent_edition=82,
        words=1048,parent_words=1046,new_public_contracts=1,new_reference_primitives=1,new_core_words=0,
        source_contracts=source,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


class RationalReferences:
    """Known exact rational candidates, without evaluating their quoted roles."""
    def __init__(self,roles):
        from fractions import Fraction
        require(all(type(value) in (int,Fraction) for value in roles.values()),
                'Expected an exact rational candidate')
        self.roles={key:Fraction(value) for key,value in roles.items()}

    def described(self,document,node,role,context):
        from noema.constructed_semantics import DescriptionValue
        from noema.constructed_discourse import function_sort
        expected=function_sort(['number','situation'],'truth')
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==expected and role.rank==0,
                'Expected a checked closed rational role description')
        key=(document,node,role.syntax,context)
        require(key in self.roles,'Unknown rational reference')
        return self.roles[key]

    def handlers(self):return dict(describedrationalreference=self.described)
