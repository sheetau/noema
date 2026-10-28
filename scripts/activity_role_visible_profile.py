"""General activity roles and contextual standards, extending optional profile 80."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from scripts.tenth_mass_visible_profile import ROOT,TenthMassVisibleVocabulary,write_once
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/activity-role-visible-profile-v1.noema'
BASIS='data/activity-role-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-activity-role-visible-profile-v1.json'
ACTIVITY=function_sort(['individual','individual','situation'],'truth')
PROCEDURE=function_sort(['individual','individual'],'content')
CONTRACTS={
    'methodologicalactivityrole':dict(
        parameters=['individual',description_sort(ACTIVITY),'situation'],result='truth',
        arguments=['role','participation','context'],
        meaning_ja='roleが、participationの閉じた関係記述で主体・活動・適用状況を指定する活動上の立場であるという文脈上の対応。記述は誰がどの活動を担う立場かを定め、実行中の活動だけでなく企図された活動にも適用できる。立場の同定から現実の参加者や活動の存在、実行済み、制度上の職位や権限を導かない。役割を担う個人と役割そのものを区別し、引用した関係を実行しない。'),
    'ordinaryprocedurestandard':dict(
        parameters=['individual',description_sort(PROCEDURE),'situation'],result='truth',
        arguments=['standard','procedure','context'],
        meaning_ja='standardが、procedureの閉じた記述で主体・活動ごとに指定する性質又は手続きを、同じ文脈で通常どの程度行うかを比較するための基準であるという対応。対象手続きと文脈を保ち、比較する結果を見て基準を変えない。基準の存在から手続きの実行、成功、完全性、数値による尺度や通常以上という結論を導かない。基準より上か下か、差が大きいかは別に述べ、引用した手続きを実行しない。'),
}
SPELLINGS={
    'methodologicalactivityrole':'above round treeone home nao book birdone fruit treeone inside aki inside'.split(),
    'ordinaryprocedurestandard':'above round treeone home nao book birdone fruit treeone inside aki aki'.split(),
}
CONTEXT=['役割を担う主体・活動、引用された手続き、適用文脈の同一性を保つ。',
         '参照対象の同定、役割の現実成立、実際の実行、程度比較、規範的要求を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile81。特定の原文や人物を原始語にしない。',
        '方法上の活動役割と通常程度の基準を記述する一般関係であり、原文の比較対象・手続き・程度や要求の内容は本文で合成する。',
        '語彙の構文・型・綴り検査は意味判断、引用した内容の実行、実SVGからの復号とは別である。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_activity_role_visible_profile',document=LIBRARY,definitions={},primitives=CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in CONTRACTS.items()},limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=81,parent_profile=80,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='力・測定・比較の語群の後続位置に、一般的な活動上の立場と通常程度基準の二関係を置く。原文の個別参照は本文の閉じた記述で同定する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ActivityRoleVisibleVocabulary(TenthMassVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Activity role manifest changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Activity role declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Activity role meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d
            data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-activity-role-visible-profile-1',edition=81)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def build_report():
    parent=TenthMassVisibleVocabulary();vocabulary=ActivityRoleVisibleVocabulary()
    require(len(parent._words)==1037 and len(vocabulary._words)==1039,'Vocabulary boundary changed')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
        for n,w in parent._words.items()),'Parent spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/activity_role_visible_profile.py','data/writing-freeze-v1.json'}
    for cls in type(vocabulary).__mro__:
        if not cls.__module__.startswith('scripts.'):continue
        module=sys.modules[cls.__module__]
        paths.add(Path(module.__file__).resolve().relative_to(ROOT).as_posix())
        for name in ('LIBRARY','BASIS','MANIFEST'):
            p=getattr(module,name,None)
            if isinstance(p,str) and (ROOT/p).is_file():paths.add(p)
    return dict(schema='noema-activity-role-visible-profile-check-1',status='typed_general_contracts_and_frozen_parent_preserved',
        edition=81,parent_edition=80,words=1039,parent_words=1037,new_public_contracts=2,new_core_words=0,
        new_source_references=0,document_integration_credit=0,limitations=LIMITS,
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
