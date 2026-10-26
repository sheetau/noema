"""Optional discourse references and attributed settings; core edition 12 is unchanged."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,description_sort
from scripts.name_presentation_profile import ROOT,NamePresentationVocabulary,I,S,T,N,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/discourse-setting-profile-v1.noema'
BASIS='data/discourse-setting-profile-basis-v1.json'
MANIFEST='noema/resources/visible-discourse-setting-profile-v1.json'
PARAMETERS=dict(documentcontext=[I],headingreference=[S,N],discoursereferent=[I,I,N,S],
    adoptsassumption=[I,I,description_sort('content'),I,S],
    presentsmessage=[I,I,I,description_sort('message'),S],introducesreferent=[I,I,I,S],
    physicalframe=[I],newtonianframe=[I,S])
RESULTS={n:S if n=='documentcontext' else I if n in ('headingreference','discoursereferent') else T for n in PARAMETERS}
ROLES=dict(documentcontext=['document'],headingreference=['context','heading_item'],
    discoursereferent=['document','node','referent_item','context'],
    adoptsassumption=['node','author','content_description','scope','context'],
    presentsmessage=['node','author','document','message_description','context'],
    introducesreferent=['node','referent','document','context'],physicalframe=['frame'],newtonianframe=['frame','context'])
MEANINGS={
 'documentcontext':'今回読む文書の本文を提示する文脈を指定する。同じ文書でも前付の名称表示の文脈とは区別し、両者の同一性を仮定しない。物理的状態の真偽や本文内容の成立を供給しない。',
 'headingreference':'指定した本文提示文脈で、文書の先頭から数えた見出し項目の箇所を指す。見出しの階層や節番号によらず実際の出現順を1から数える。見出しが示す内容や主題は別に記述する。',
 'discoursereferent':'同じ文書・提示文脈の指定箇所に結び付けて照合する対象参照。複数の対象はその箇所での導入順を1から数えて区別する。参照値を供給することから、導入操作の成立、現実の存在、条件の成立、世界での唯一性を導かない。',
 'adoptsassumption':'著者が指定の文章箇所で内容の記述を仮定として採用し、指定した推論範囲へ置く。内容の真理、信念、証明を含意しない。',
 'presentsmessage':'著者が同じ文書・提示文脈のこの箇所で、閉じたmessageの記述が指定する発話の力と内容を読者へ提示する。指示・主張・問いを交換しない。帰属された発話の内容をその場で実行せず、読者の遵守、内容の真理、著者による実験実施を含意しない。',
 'introducesreferent':'nodeで、documentの以後の議論に使う一つの対象をreferentとして設定し、後続の指示が同じ対象を保てるよう導入する操作。対象は仮定的な設定の中で選べ、物理的な実在や測定での同定の証明とは区別する。与える条件は別の仮定内容へ保持し、条件を満たす世界唯一の対象だとはしない。名称を付ける操作とも区別する。',
 'physicalframe':'物理的な状態変化を参照する座標系。座標の構成と測定は未説明。',
 'newtonianframe':'この座標系に関する物体の位置と時間、慣性質量と機械的作用の記述で、対象とするNewtonの力学方程式が成り立つという適格性。力を受けない物体の等速直線運動、力と運動変化の関係を同じ空間・時間尺度で記述し、座標選択だけで生じる見かけの力を加えない系を指定する。後続u0008でNewtonの方程式と明記される読みを採る。どの系が実際に適格かは物理的入力であり、座標系という名前だけから認めない。電気力学・光学の法則の成立、特定の相対速度・変換式・絶対静止をこの条件へ先取りしない。'}
CONTEXT=['本文文脈、見出し・文の箇所、対象参照を明示し、同じ参照を定義と引用で保持する。',
         '仮定採用・対象導入・発話帰属・物理的適格性は独立した関係であり、参照の取得から成立を補わない。']
LIMITS=['物理関係は旧正本の基本概念の規約を保持する専門的入力である。座標の構成や測定手続を今回導出したとはしない。',
        '引用された内容や指示を実行しない。明示的にその内容を検査する診断と、原文の帰属主張を分ける。',
        '未知の文書、位置、参照、関係は有限実行では拒否する。完全なモデルの全域解釈とは区別する。']
SPELLINGS={n:['book','give','inside',part] for n,part in zip(PARAMETERS,
    ['home','above','aki','assessmentvalid','give','inside','town','round'],strict=True)}
SOURCE_RELATIONS=dict(ug='adoptsassumption',eir3='presentsmessage',eisd3='introducesreferent',va='physicalframe',eisbd='newtonianframe')


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=p,result=RESULTS[n]) for n,p in PARAMETERS.items()],statements=[])


def basis():
    return dict(status='optional_discourse_setting_profile',document=LIBRARY,definitions={},
        primitives={n:dict(parameters=p,result=RESULTS[n],arguments=ROLES[n],meaning_ja=MEANINGS[n]) for n,p in PARAMETERS.items()},
        public_contracts={n:dict(arguments=[dict(role=r,sort=s) for r,s in zip(ROLES[n],p,strict=True)],
            result=RESULTS[n],interpretation_inputs=CONTEXT) for n,p in PARAMETERS.items()},limitations=LIMITS,
        source_relations=SOURCE_RELATIONS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=19,parent_profile=18,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='book/give/insideを文書内の設定の語群とする。各語の意味と引数は公開規約から学ぶ。原文の一文全体を一つの基本語にしない。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class DiscourseSettingVocabulary(NamePresentationVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Setting profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Setting declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Setting meanings changed')
        for d in library()['declarations']:
            n=d['name'];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=ROLES[n],meaning=MEANINGS[n],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-discourse-setting-profile-1',edition=19)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class DiscourseReferences:
    """Partial reference data. Relations such as text order remain separate inputs."""
    def __init__(self,contexts,headings,sentences,referents):
        self.contexts=dict(contexts)
        self.headings={(s,TextPresentation.coordinate(n)):v for (s,n),v in headings.items()}
        self.sentences={(s,TextPresentation.coordinate(p),TextPresentation.coordinate(n)):v for (s,p,n),v in sentences.items()}
        self.referents={(d,node,TextPresentation.coordinate(n),s):v for (d,node,n,s),v in referents.items()}

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown discourse reference');return table[key]

    def handlers(self):
        pos=TextPresentation.coordinate
        return dict(documentcontext=lambda d:self.known(self.contexts,d),
            headingreference=lambda s,n:self.known(self.headings,(s,pos(n))),
            sentencereference=lambda s,p,n:self.known(self.sentences,(s,pos(p),pos(n))),
            discoursereferent=lambda d,node,n,s:self.known(self.referents,(d,node,pos(n),s)))
