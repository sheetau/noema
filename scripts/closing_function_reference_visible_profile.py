"""General work-progress function and opaque typed references, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.tenth_closing_visible_profile import ROOT,TenthClosingVisibleVocabulary,write_once
from scripts.closing_function_reference_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES,REFERENCE_KINDS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/closing-function-reference-visible-profile-v1.noema'
BASIS='data/closing-function-reference-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-closing-function-reference-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'workadvancement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'home'], 'describedsituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'above'], 'describedtwosituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'give'], 'describedindividualsituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'inside'], 'describedtwoindividualsituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'aki'], 'describedthreeindividualsituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'nao'], 'describedindividualtwosituationtruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'book'], 'describedcriterionbindingfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'home', 'round'], 'describedbeneficiaryfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'above', 'home'], 'describedpurposefunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'nao', 'home', 'above', 'above']}
CONTEXT=['同じ文書・箇所・閉じた役割記述・評価文脈と候補関数の完全な型を保持する。', '関数の参照、役割の成立、引用内容の真理、目的の達成を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile86。一般の仕事の前進関係と、九つの関数型の記述参照を追加する。', 'workadvancementは人物・仕事・状況を引数とする一般関数で、特定の仕事・人物・達成事実を語義へ埋め込まない。評価規約は解釈の入力に残る。', '参照の取得は候補関数や役割を実行せず、目的の実現可能性・達成・引用内容の真理を要求しない。', '未知の対応を推測しない。有限診断は本文統合・人間の読解・全域の証明とは別である。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_closing_function_reference_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=86,parent_profile=85,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='仕事の前進と、状況・判断・目的に用いる関数への型付き参照。特定の人物や原文箇所は本文で構成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ClosingFunctionReferenceVisibleVocabulary(TenthClosingVisibleVocabulary):
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
        data.update(schema='noema-visible-closing-function-reference-visible-profile-1',edition=86)
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
    parent=TenthClosingVisibleVocabulary()
    vocabulary=ClosingFunctionReferenceVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1076 and len(vocabulary._words)==1086,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/closing_function_reference_visible_profile.py',
        'scripts/closing_function_reference_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    paths.add('tests/test_closing_function_reference_visible_profile.py')
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
    for old,kind in REFERENCE_KINDS.items():
        target=catalog.entries[old]['declaration']['result']
        role=function_sort([target,'situation'],'truth')
        require(EXTRA[kind]['result']==target and EXTRA[kind]['parameters']==[
            'individual','individual',dict(kind='description',result=role),'situation'],
            'Reference function type changed: '+old)
    require(len(REFERENCE_KINDS)==17,'Unexpected closed function inventory')
    require(len(source)==1 and len(EXTRA)==9 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-closing-function-reference-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=86,parent_edition=85,
        words=1086,parent_words=1076,new_public_contracts=1,new_reference_primitives=9,new_core_words=0,
        source_contracts=source,source_reference_kinds=REFERENCE_KINDS,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})

class TypedFunctionReferences:
    """Retrieve a known function by a closed role without executing either."""
    def __init__(self,kind,roles):
        from noema.constructed_semantics import FunctionValue
        require(kind in EXTRA,'Unknown typed reference kind')
        self.kind=kind;expected=EXTRA[kind]['result']
        require(all(isinstance(x,FunctionValue) and x.parameters==tuple(expected['parameters'])
            and x.result==expected['result'] and callable(x.implementation) for x in roles.values()),
            'Expected a candidate of the declared function type')
        self.roles=dict(roles)

    def described(self,document,node,role,context):
        from noema.constructed_semantics import DescriptionValue
        from noema.constructed_discourse import function_sort
        expected=function_sort([EXTRA[self.kind]['result'],'situation'],'truth')
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==expected and role.rank==0,
            'Expected a checked closed typed role description')
        key=(document,node,role.syntax,context)
        require(key in self.roles,'Unknown typed function reference')
        return self.roles[key]

    def handlers(self):return {self.kind:self.described}
