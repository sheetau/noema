"""Optional dynamics contracts and typed function references, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.ninth_section_visible_profile import ROOT,NinthSectionVisibleVocabulary,write_once
from scripts.tenth_motion_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/tenth-motion-visible-profile-v1.noema'
BASIS='data/tenth-motion-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-tenth-motion-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'dynamicallawrange': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'rain'], 'lowspeedinertialmass': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'town'], 'adoptsindependentmotionpremise': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'home'], 'particlesettingquantitydesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'above'], 'particlesettingcoordinatesdesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'give'], 'particlemotionlawrange': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'inside'], 'localmotionrepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'birdone'], 'conditionalindividualinquirytask': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'treeone'], 'successivecasepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'aki'], 'gentleaccelerationbound': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'nao'], 'describedcuttruthfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'book'], 'describedcutindividualcutfunctionfamilyreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'rain', 'fruit']}
CONTEXT=['同じ対象・基準系・出来事・履歴・単位・提示文脈を保持する。', '運動法則の内容、前提の採用、表記解釈、探究と真理を区別する。', '関数の参照は閉じた役割を識別に用い、役割や候補の実行、存在・唯一性の証明を含めない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile79。既存10契約の型・引数順序・意味と一般型付き参照2種類を公開する。', '本文の一文ごとの原始語を作らず、運動設定と方程式は既存定義を合成する。', '電子の呼称から現代の粒子種や電荷符号を補わず、瞬間速度を以前の二系間速度と同一視しない。', '参照取得で候補関数を実行せず、別々の参照結果から共通witnessを推定しない。同じ設定の結合条件は本文が要求する。', '未知入力は拒否し、既定の関数・真偽値・物理法則を補わない。', '実SVG復号、意味判断、有限診断と一般実数域の証明を区別する。本文統合は別途確認する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_tenth_motion_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=79,parent_profile=78,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/treeoneを運動の公開規約と型付き参照の語群とする。後続二要素は規約の綴りを区別し、文全体は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TenthMotionVisibleVocabulary(NinthSectionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TenthMotion-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TenthMotion-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TenthMotion-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-tenth-motion-visible-profile-1',edition=79)
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
    parent=NinthSectionVisibleVocabulary()
    vocabulary=TenthMotionVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==990 and len(vocabulary._words)==1002,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/tenth_motion_visible_profile.py',
        'scripts/tenth_motion_visible_profile_contracts.py','data/writing-freeze-v1.json',
        catalog.document_path,'data/work-state.json'}
    paths.update(catalog.source_sha256)
    paths.add('tests/test_tenth_motion_reference_profile.py')
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
    require(len(source)==10 and len(EXTRA)==2 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-tenth-motion-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=79,parent_edition=78,
        words=1002,parent_words=990,new_public_contracts=10,new_reference_primitives=2,new_core_words=0,
        source_contracts=source,document_integration_credit=0,
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
