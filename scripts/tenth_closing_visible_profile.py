"""Optional social, calendar and documentary contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.tenth_observables_visible_profile import ROOT,TenthObservablesVisibleVocabulary,write_once
from scripts.tenth_closing_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/tenth-closing-visible-profile-v1.noema'
BASIS='data/tenth-closing-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-tenth-closing-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'mutualfriendship': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'home'], 'professionalcolleagues': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'above'], 'investigationtask': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'give'], 'documentproblemfocus': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'inside'], 'closingremark': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'aki'], 'workepisodecoverage': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'nao'], 'calendaryearnumber': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'book'], 'orderedcalendarmonths': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'home', 'round'], 'orderedcalendardays': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'home'], 'datelineplace': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'above'], 'datelineperiod': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'give'], 'documentreceipt': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'inside'], 'editorialreport': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'aki'], 'documentutterancepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'nao'], 'periodcontainsmoment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'aki', 'round', 'above', 'book']}
CONTEXT=['同じ人物・研究活動・作業機会・文書・提示・暦規約・期間・評価文脈を保持する。', '関係や範囲の帰属、支援の実行、表示された場所と日時、刊行側による報告を区別する。', '引用内容を実行せず、その真理や著者の同意を提示から推論しない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile85。一般15契約の型・引数順序・意味を保持する。', '人物名・特定の研究・場所・暦期間・原文箇所は本文の参照で構成し、一般原始語へ追加しない。', '友人・同僚関係は個別の支援や共同著作を含意しない。作業範囲には支援がなかった該当機会も含める。', '日付行の表示は実際の執筆場所や執筆完了日を含意しない。編集側の受領報告は著者の主張と区別する。', '既存presentationholds/nameappliesを再利用し、語彙の保存と本文統合・実SVG復号を分けて確認する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_tenth_closing_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=85,parent_profile=84,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='社会関係と作業範囲、暦と文献上の表示・報告を区別する一般語彙。個別の対象と主張は本文で構成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TenthClosingVisibleVocabulary(TenthObservablesVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TenthClosing-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TenthClosing-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TenthClosing-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-tenth-closing-visible-profile-1',edition=85)
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
    parent=TenthObservablesVisibleVocabulary()
    vocabulary=TenthClosingVisibleVocabulary()
    before=parent.document();after=vocabulary.document()
    require(len(parent._words)==1061 and len(vocabulary._words)==1076,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(after['entries']==before['entries'],'Frozen alphabet/core entries changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/tenth_closing_visible_profile.py',
        'scripts/tenth_closing_visible_profile_contracts.py','data/writing-freeze-v1.json',
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
    require(len(source)==15 and not EXTRA and not library()['statements'],'Unexpected profile statements')
    return dict(schema='noema-tenth-closing-visible-profile-check-1',
        status='source_contracts_and_frozen_parent_preserved',edition=85,parent_edition=84,
        words=1076,parent_words=1061,new_public_contracts=15,new_reference_primitives=0,new_core_words=0,
        source_contracts=source,reused_numeric_aliases=aliases,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
