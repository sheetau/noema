"""Optional naming and purpose relations with explicit contextual designation references."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,description_sort,function_sort
from scripts.discourse_setting_profile import ROOT,DiscourseSettingVocabulary,DiscourseReferences,I,S,T,N,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/designation-purpose-profile-v1.noema'
BASIS='data/designation-purpose-profile-basis-v1.json'
MANIFEST='noema/resources/visible-designation-purpose-profile-v1.json'
C=description_sort('content');ALTERNATIVES=description_sort(function_sort([I,S],T))
PARAMETERS=dict(designationreference=[I,I,N,S],adoptsdesignation=[I,I,I,I,I,S],
    actionpurpose=[I,C,C,I,S],designationdistinguishes=[I,I,ALTERNATIVES,I,S],
    anticipatedreferent=[I,I,I,S],designationclarifies=[I,I,I,S])
RESULTS={n:I if n=='designationreference' else T for n in PARAMETERS}
ROLES=dict(designationreference=['document','node','designation_item','context'],
    adoptsdesignation=['node','author','designation','target','document','context'],
    actionpurpose=['agent','action','goal','scope','context'],
    designationdistinguishes=['designation','target','alternatives','document','context'],
    anticipatedreferent=['referent','document','after','context'],
    designationclarifies=['designation','target','document','context'])
MEANINGS={
 'designationreference':'同じ文書・提示文脈の指定箇所で呼称として採用する名称個体への参照。複数の名称はその箇所で採用する順を1から数える。参照値の供給から、命名行為の成立、目的の達成、対象の性質、同じ表記を持つ名称の同一性を導かない。名称の表記は別に記述する。',
 'adoptsdesignation':'authorがnodeでdesignationを、同じdocumentの議論における同じtargetの呼称として採用する命名行為。対象個体を指す名前の規約であり、閉じた命題内容の略称とは区別する。現在の命名の宣言として行われ、対象の新たな物理的性質や名称の字面の性質を付与しない。文中の引用された呼称の同一性を保持し、以後同じ対象を言い分けるために使える。原文にない改名歴、社会全体の承認や他者による実際の使用は要求しない。',
 'actionpurpose':'agentがscopeの活動で同じactionを行う目的として、goalに記述される事柄を目指すという目的関係。行為と目標の対象・向きを保ち、結果が先に生じたという時間順序や、目的が既に達成された事実とは区別する。同じ行為が複数の目的を持つことを許し、目標だけから行為の成功や正当性を推論しない。',
 'designationdistinguishes':'同じdocumentの言語上の指示において、designationを用いることでtargetをalternativesの型が指定する別の対象群と取り違えずに言い分けられるという状態。共通の対象分類と本文上の参照を保つ。物理的な相違を新たに作ることや、違う名前を与えれば絶対運動を検出できることとは異なる。alternativesが今後導入予定の対象群の場合も、区別の目標を記述でき、現在それらが導入済み又は現実に存在することは要求しない。',
 'anticipatedreferent':'referentが同じdocumentでafterより後に導入されるものとして見越された対象群に属する。これは本文の展開における将来の指示範囲であり、物理的な未来時刻での生成や、現在導入済みの対象の一覧ではない。該当する全予定範囲を扱い、都合のよい比較相手だけを後から選ばない。予定された仮定的対象も含み、現実での存在を断言しない。',
 'designationclarifies':'designationをtargetに固定して用いることで、同じdocumentでどの対象を考え、その関係や規約をどう捉えるかという観念が明確に定まるという状態。指示の曖昧さや対象の混同を減らし、後の記述を一つの同じ対象の下で把握するという意味の明確化である。座標値の測定精度、実験の実施、全読者の心理状態や完全理解を要求しない。'}
CONTEXT=['同じ名称・対象・行為・目的・本文文脈を保つ。目的の記述をその場で実行せず、行為と目標を交換しない。',
         '後続対象の全予定範囲を型の記述として保持し、現在の対象の存在を加えない。']
LIMITS=['名称の取得、命名、目的、目的の達成、物理的な性質は独立である。',
        '名称のUnicode表記は識別表記であり、自然言語の一文を文字列にして意味の記述を代用するものではない。',
        '未知の名称参照は有限実行では拒否する。完全なモデルの全域解釈とは区別する。']
SPELLINGS={n:['book','give','book',part] for n,part in zip(PARAMETERS,
    ['aki','give','above','inside','home','assessmentvalid'],strict=True)}
SOURCE_RELATIONS=dict(eisd4='adoptsdesignation',eisd5='actionpurpose',eisd6='designationdistinguishes',
    eisd7='anticipatedreferent',eisea='designationclarifies')


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=p,result=RESULTS[n]) for n,p in PARAMETERS.items()],statements=[])


def basis():
    return dict(status='optional_designation_purpose_profile',document=LIBRARY,definitions={},
        primitives={n:dict(parameters=p,result=RESULTS[n],arguments=ROLES[n],meaning_ja=MEANINGS[n]) for n,p in PARAMETERS.items()},
        public_contracts={n:dict(arguments=[dict(role=r,sort=s) for r,s in zip(ROLES[n],p,strict=True)],
            result=RESULTS[n],interpretation_inputs=CONTEXT) for n,p in PARAMETERS.items()},limitations=LIMITS,
        source_relations=SOURCE_RELATIONS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=20,parent_profile=19,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='book/give/bookを命名と目的の語群とする。意味と引数は公開規約から学び、特定の名称や一文全体を基本語にしない。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class DesignationPurposeVocabulary(DiscourseSettingVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Designation profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Designation declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Designation meanings changed')
        for d in library()['declarations']:
            n=d['name'];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=ROLES[n],meaning=MEANINGS[n],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-designation-purpose-profile-1',edition=20)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class DesignationReferences:
    def __init__(self,references):
        self.references={(d,node,TextPresentation.coordinate(n),s):value for (d,node,n,s),value in references.items()}

    def reference(self,document,node,item,context):
        return DiscourseReferences.known(self.references,(document,node,TextPresentation.coordinate(item),context))

    def handlers(self):return dict(designationreference=self.reference)
