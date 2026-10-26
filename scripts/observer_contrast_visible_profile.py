"""Optional observer judgments, hypothetical claims and partial text spans."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.moving_trip_visible_profile import ROOT,MovingTripVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.observer_contrast_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/observer-contrast-visible-profile-v1.noema'
BASIS='data/observer-contrast-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-observer-contrast-visible-profile-v1.json'
I='individual';S='situation';N='number'
EXTRA={
 'sentencetokenspanreference':dict(parameters=[I,I,N,I,N,S],result=I,
    arguments=['document','first_sentence','first_token','last_sentence','last_token','context'],
    meaning_ja='指定した文書・提示文脈で、最初の文のfirst_tokenから最後の文のlast_tokenまでを両端込みで対象とする連続本文範囲。各文内のトークン位置は1始まりの正整数。提示文脈の明示された転記規約で空白区切りを数え、句読点は隣接文字に付け、数式全体と本文中の数式をそれぞれ一つの原子的トークンとする。数式中の空白・改行・組版をトークン境界にしない。独立したダッシュ等は一つに数える。既知の文の順序と各トークン数に照合して逆転・範囲外を拒否する。文全体の参照と区別し、意味・真理は内容の定義で別に記述する。未知の位置を推測しない。')}

ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','aki',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_observer_contrast_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=33,parent_profile=32,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/akiを仮定範囲の主張・観測者の判断・本文部分範囲の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ObserverContrastVisibleVocabulary(MovingTripVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Observer-contrast-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Observer-contrast-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Observer-contrast-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-observer-contrast-visible-profile-1',edition=33)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class TokenSpanReferences:
    """Known sentence order and token counts validate exact inclusive spans."""
    def __init__(self,layouts,spans):
        from scripts.text_reference_profile import TextPresentation
        self.coordinate=TextPresentation.coordinate;self.layouts={}
        for key,rows in layouts.items():
            layout={}
            for index,(sentence,count) in enumerate(rows):
                require(sentence not in layout,'Duplicate sentence in token layout')
                layout[sentence]=(index,self.coordinate(count))
            self.layouts[key]=layout
        self.spans={}
        for key,node in spans.items():
            key=self.checked(*key)
            require(key not in self.spans,'Duplicate token span')
            self.spans[key]=node

    def checked(self,document,first,start,last,end,context):
        start=self.coordinate(start);end=self.coordinate(end)
        require((document,context) in self.layouts,'Unknown token presentation')
        layout=self.layouts[document,context]
        require(first in layout and last in layout,'Unknown token sentence')
        a,na=layout[first];b,nb=layout[last]
        require(start<=na and end<=nb,'Token position outside sentence')
        require(a<b or (a==b and start<=end),'Reversed token span')
        return document,first,start,last,end,context

    def span(self,document,first,start,last,end,context):
        key=self.checked(document,first,start,last,end,context)
        require(key in self.spans,'Unknown sentence token span');return self.spans[key]

    def handlers(self):return dict(sentencetokenspanreference=self.span)
