"""Optional name-presentation references, with independent factual relations."""
from copy import deepcopy
from fractions import Fraction
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,sequence_sort
from noema.constructed_semantics import FunctionValue,SequenceValue
from scripts.text_reference_profile import ROOT,TextReferenceVocabulary,TextPresentation,write_once
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.shared_reference import definition,lam
from scripts.shared_modality import v

LIBRARY='examples/v016/name-presentation-profile-v1.noema'
BASIS='data/name-presentation-profile-basis-v1.json'
MANIFEST='noema/resources/visible-name-presentation-profile-v1.json'
ACCESSORS='examples/v016/name-presentation-accessors-v1.noema'
I='individual';S='situation';T='truth';N='number'
TEXT=sequence_sort(N);SELECTOR=function_sort([I,I,I,I],I);RECORD=function_sort([SELECTOR],I)
FIELDS=['use','designation','target','document']
PARAMETERS=dict(presentationrecord=[S,N],presentationholds=[I,S],nameapplies=[I,I,I,S],
    authordisplay=[I,I,I,S],printedform=[I,TEXT,TEXT,S])
RESULTS=dict(presentationrecord=RECORD,presentationholds=T,nameapplies=T,authordisplay=T,printedform=T)
ROLES=dict(presentationrecord=['context','frontmatter_item'],presentationholds=['use','context'],
    nameapplies=['use','designation','target','context'],authordisplay=['use','document','target','context'],
    printedform=['designation','language','form','context'])
MEANINGS={
 'presentationrecord':'同じ提示文脈の、指定した前付項目に結び付けて照合する名称使用・名称個体・対象個体・文書個体をこの順に保持する参照の組。どの選択関数にもこの4値を同じ順で渡す。参照値を供給することから、名称使用の成立、名称の適用、著者役割の成立を導かない。',
 'presentationholds':'同じ文脈で指定された提示行為が成立する。物理的な印刷者や執筆者を指定しない。',
 'nameapplies':'同じ提示行為で名称を対象へ適用する。綴りの一致から対象の同一性を推論しない。',
 'authordisplay':'指定文書のその提示行為が、同じ対象を文書の著者として表示する役割を持つ。表示の真実性、自筆性、提示者と著者の一致を含意しない。',
 'printedform':'同じ提示文脈で、名称個体に指定言語ラベルの印刷上の識別表記がある。言語ラベルと表記はUnicodeスカラー値の有限列で、正規化・大小文字変換・翻字をせず完全一致で扱う。同じ表記から人物の同一性や名称の概念内容を推論しない。'}
CONTEXT=[
 '提示文脈と対象文書を固定する。前付項目は本文段落と分けて1始まりで数える。',
 '参照の組はuse/designation/target/documentの4個体であり、その関係の真偽は別に供給する。',
 '名称個体と対象人物を同じ型の値として扱うが、同一性は型や同じ綴りから補わない。']
LIMITS=[
 '有限実行で未知の文脈・前付位置・関係・識別表記を要求したら未知として拒否する。偽や既定の人物で補わない。',
 '完全なモデルの全域関数と、既知の解釈だけを実行する参照実装を区別する。',
 '名称の文字列は識別表記であり、自然言語本文を文字列にして意味の記述を代用する機能ではない。',
 '著者として表示されていることは、実際の執筆・真正性・自筆性・物理的な提示者の同定を含意しない。']
SPELLINGS=dict(presentationrecord=['book','give','aki','book'],presentationholds=['book','give','aki','assessmentvalid'],
    nameapplies=['book','give','aki','inside'],authordisplay=['book','give','aki','aki'],printedform=['book','give','aki','red'])
HELPER_FORMS={**{'display'+field:['book','give','aki','book',part] for field,part in zip(FIELDS,['give','book','aki','home'],strict=True)},
              'makepresentation':['book','give','aki','book','round']}


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=p,result=RESULTS[n]) for n,p in PARAMETERS.items()],statements=[])


def accessors():
    ds=[]
    for field in FIELDS:
        ds.append(definition('display'+field,[('record',RECORD)],I,
            dict(kind='apply',function=v('record'),arguments=[lam([(n,I) for n in FIELDS],v(field))])))
    ds.append(definition('makepresentation',[(n,I) for n in FIELDS],RECORD,
        lam([('selector',SELECTOR)],dict(kind='apply',function=v('selector'),arguments=[v(n) for n in FIELDS]))))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[]))


def basis():
    return dict(status='optional_name_presentation_profile',document=LIBRARY,definitions={},
        primitives={n:dict(parameters=p,result=RESULTS[n],arguments=ROLES[n],meaning_ja=MEANINGS[n]) for n,p in PARAMETERS.items()},
        public_contracts={n:dict(arguments=[dict(role=r,sort=s) for r,s in zip(ROLES[n],p,strict=True)],result=RESULTS[n],
            interpretation_inputs=CONTEXT) for n,p in PARAMETERS.items()},limitations=LIMITS,
        record_fields=FIELDS,local_accessor_library=ACCESSORS,local_accessor_spellings=HELPER_FORMS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=18,parent_profile=17,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='book/give/akiを名称の提示の語群とする。bookは参照の組、assessmentvalidは提示の成立、insideは名称の適用、akiは著者表示、redは見える識別表記を区別する綴り。意味は公開規約から学習する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())
    write_once(ACCESSORS,format_graph(accessors())+'\n')


class NamePresentationVocabulary(TextReferenceVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Name presentation profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Name presentation declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Name presentation meanings changed')
        for d in library()['declarations']:
            n=d['name'];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=ROLES[n],meaning=MEANINGS[n],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-name-presentation-profile-1',edition=18)
        data['naming_convention']+='\n'+manifest()['naming_convention']
        self._document=data;self._primitives=deepcopy(data['primitives'])
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def scalar_text(values):
    if isinstance(values,SequenceValue):values=values.items
    require(isinstance(values,(tuple,list)) and values,'Empty or invalid scalar sequence')
    codes=[]
    for value in values:
        require(type(value) in (int,Fraction),'Unicode scalar must be an exact integer')
        value=Fraction(value);require(value.denominator==1,'Unicode scalar must be an integer')
        code=int(value);require(0<=code<=0x10ffff and not 0xd800<=code<=0xdfff,'Invalid Unicode scalar')
        codes.append(code)
    result=''.join(chr(c) for c in codes);require(result.strip(),'Empty identifying text');return result


def text_expression(text):
    require(isinstance(text,str) and scalar_text([ord(c) for c in text])==text,'Invalid identifying text')
    return dict(kind='sequence',element=N,items=[dict(kind='number',numerator=ord(c),denominator=1) for c in text])


class NamePresentation:
    """References and facts are separate, and every requested fact must be known."""
    def __init__(self,anchor,records,*,presented,applied,authors,forms):
        self.anchor=anchor;self.records={}
        for (context,item),record in records.items():
            key=(context,TextPresentation.coordinate(item))
            require(isinstance(record,(list,tuple)) and len(record)==4,'Expected four named presentation roles')
            require(key not in self.records,'Repeated presentation position');self.records[key]=tuple(record)
        require(any(context==anchor for context,_ in self.records),'Unknown presentation anchor')
        self.presented=dict(presented);self.applied=dict(applied);self.authors=dict(authors);self.forms=dict(forms)
        require(all(type(x) is bool for table in (self.presented,self.applied,self.authors,self.forms) for x in table.values()),
                'Presentation facts must be explicit truth values')

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown presentation fact');return table[key]

    def record(self,context,item):
        key=(context,TextPresentation.coordinate(item));require(key in self.records,'Unknown presentation position')
        values=self.records[key]
        return FunctionValue((SELECTOR,),I,lambda selector:selector(*values))

    def form(self,name,language,text,context):
        return self.known(self.forms,(name,scalar_text(language),scalar_text(text),context))

    def handlers(self):
        return dict(textpresentation=lambda:self.anchor,presentationrecord=self.record,
            presentationholds=lambda use,ctx:self.known(self.presented,(use,ctx)),
            nameapplies=lambda use,name,target,ctx:self.known(self.applied,(use,name,target,ctx)),
            authordisplay=lambda use,doc,target,ctx:self.known(self.authors,(use,doc,target,ctx)),printedform=self.form)
