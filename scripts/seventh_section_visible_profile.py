"""Optional wave and theoretical inquiry contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.seat_questions_visible_profile import ROOT,SeatQuestionsVisibleVocabulary,write_once
from scripts.seventh_section_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/seventh-section-visible-profile-v1.noema'
BASIS='data/seventh-section-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-seventh-section-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'viewattributescontent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'rain'], 'radiatingsourcesupport': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'town'], 'electromagneticradiationsource': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'home'], 'largedistanceratiostandard': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'above'], 'waveapproximationadequacy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'give'], 'forwardwaveforminterpretation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'inside'], 'elaboratesattributedsetting': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'birdone'], 'investigateswaveprocess': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'treeone'], 'presentsconditionalfieldquestion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'aki'], 'presentssharedsettingderivation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'nao'], 'objectconfigurationmodels': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'book'], 'radiationphasecorrespondence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'fruit'], 'perspicuousformassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'red'], 'presentsremainingamplitudequestion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'round'], 'comparativeformperspicuity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'bird'], 'energyfluxunitcoefficient': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'rain', 'fly'], 'adoptswaveenergyfluxmodel': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'town', 'rain'], 'theoreticalinquirytopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'nao', 'town', 'town']}
CONTEXT=['同じ波・源・観測者・領域・単位と対象の割当を保つ。', '近似、物理的役割、命名、著者への帰属、研究主題を分け、引用された内容の真理を自動的に要求しない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile76。既存18規約の意味・型・引数順序を保持する。', '文全体の原始語を加えず、波・変換・周波数・光行差・振幅・強度は既存の定義から合成する。', '源の一点性・静止・真空横波条件を先行の仮定へ追加しない。意味判断の採用読解と原典中の不整合を保持する。', '非事実的帰属や研究主題から、実在・計算成功・測定済み・研究完了を導かない。未知の入力を補わない。', '本文統合と可視復号は別途確認する。有限束縛診断を全実数・全関数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_seventh_section_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=76,parent_profile=75,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/naoを波・提示・理論研究の公開規約の語群とする。後続二要素は規約の綴りを区別し、文全体の意味は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class SeventhSectionVisibleVocabulary(SeatQuestionsVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'SeventhSection-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'SeventhSection-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'SeventhSection-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-seventh-section-visible-profile-1',edition=76)
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
    parent=SeatQuestionsVisibleVocabulary()
    vocabulary=SeventhSectionVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==935 and len(vocabulary._words)==953,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/seventh_section_visible_profile.py',
        'scripts/seventh_section_visible_profile_contracts.py','data/writing-freeze-v1.json',
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
    require(len(source)==18 and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-seventh-section-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=76,parent_edition=75,
        words=953,parent_words=935,new_public_contracts=18,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
