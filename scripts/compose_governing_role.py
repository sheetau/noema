"""Tie the policy actor to a governing office over the same community."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_dispositional_resistance import ROOT,SOURCE as PARENT
from scripts.compose_collective_office import ORDER,params,av
from scripts.compose_political_consequence import SCHEMA,GOV,HIGH,REST
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/governing-role.noema'
SOURCE='examples/v016/kant-governing-role.noema'
CORE='examples/v016/governing-role-core.noema'
BASIS='data/governing-role-basis-v1.json'
READING='data/governing-role-reading-v1.json'
REVIEW='data/kant-manuscript-obligations-v9.json'
FIELDS=[('actor','a'),('community','a')]+ORDER+[
    ('occupants','h[a a a d] c'),('jurisdiction','h[a a d] c')]


def parent_schema():
    return json.loads((ROOT/'data/kant-manuscript-obligations-v8.json').read_text(encoding='utf-8'))['templates'][0]['symbol']


def definitions():
    return definition('ryv',params(FIELDS),both(k('rwo',*av(ORDER)),
        app(v('occupants'),v('actor'),v('office'),v('organization'),v('anchor')),
        app(v('jurisdiction'),v('organization'),v('community'),v('anchor'))))


def additions():
    text='r ibdorganization[a d] a.r ibdoccupants[a a a d] c.r ibdjurisdiction[a a d] c.'
    refs=dict(actor=v('actor'),community=v('community'),office=v('office'),
        organization=k('ibdorganization',v('community'),v('anchor')),anchor=v('point'),
        roles='p iabroles',above='p iababove',occupants='p ibdoccupants',jurisdiction='p ibdjurisdiction')
    text+=definition('ibdqualified','actor a office a community a anchor d point d',k('ryv',*[refs[n] for n,t in FIELDS]))
    qualify=lambda point:k('ibdqualified',v('actor'),v('office'),v('community'),v('anchor'),v(point))
    rest='i[reading '+HIGH+' community a contributors j[a] anchor d start d end d late d]['+both(
        qualify('start'),qualify('late'),
        app(v('remaining'),*[v(n) for n in ('reading','community','contributors','anchor','start','end','late')]))+']'
    context=quant('f','community','a',op('y',k('iaqcommunities',v('community'),k('wh')),
        k('ibdqualified',v('actor'),v('office'),v('community'),k('wh'),k('wh'))))
    text+=definition('ibdschema',params(SCHEMA),both(context,k(parent_schema(),v('reading'),*av(GOV),rest)))
    text+=definition('ibdattribution','',k('iatreport',k('iagnode'),k('wa'),'r c[p ibdschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k ibdattribution[]].')
    doc['statements']=deepcopy(parent['statements'][:-1])+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryv'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='governing_office_and_same_community_connected',parent=PARENT,document=SOURCE,
        definitions={
            'ryv':'指定主体が、同じ組織・文脈の対象役職範囲の最高役職を担い、その組織が同じ共同体を管轄する。最高役職の判定は既存rwoを再利用する。',
            'ibdqualified':'共同体と基準文脈で一つの組織を固定し、指定時点で同じ主体・役職の資格と同じ共同体への管轄を調べる。主体と規範の出所は同一化しない。',
            'ibdschema':'選択された各共同体について基準時の資格を先に確認する。既存の条件文に同じ8引数を渡し、後件では同じ主体・役職・組織について始点と政治的終点の資格を要求する。',
            'ibdattribution':'具体化した8引数のひな形を同じ著者・箇所・範囲・発話文脈へ帰属する。引数を充足した文章になったとはしない。'},
        primitive_conventions={
            'ibdorganization':'同じ共同体・基準文脈で評価対象として固定した統治組織。候補時点ごとに別組織へ替えない。',
            'ibdoccupants':'指定主体が同じ組織の指定役職を同じ時点で担うこと。主体は一人でも組織でもよく、単にその組織に所属するだけでは足りない。',
            'ibdjurisdiction':'指定組織の統治上の管轄が同じ共同体に及ぶこと。財産の所有、単なる場所の一致、組織への所属とは別の制度的関係。',
            'iabroles/iababove':'既存の意思決定権限に関わる役職範囲と推移的な上下関係を使用する。今回は統治を指導する役職体系を選ぶ。儀礼上の席次や全国家機関の無条件の一列化とはしない。'},
        limitations=[
            '政府の資格の一候補であり、組織・役職・管轄の制度的な成立、国家や市民的共同体の残る構成は未説明。会社の役職体系だけで国家の政府と認定できる定義にはしない。',
            '同じ一つの最高役職を選ぶ構成である。権限分立・分掌・連邦制をこの役職範囲へどう対応させるかは別の説明が必要。',
            '一人の統治者と組織としての政府を許し、複数の保持者・多数決・選挙・民主的正当性・全住民の参加を要件にしない。組織の判断を構成員の判断から構成する説明は残る。',
            '基準時・始点・政治的終点を確認する。途中の全時点での在任や同一構成員の維持は要求しない。実際の政策履行や管轄の道徳的正当性もここから導かない。',
            'Dudenの現代語義とAdelungの隣接語Obrigkeitを比較した。1784年のRegierungの唯一の意味や現代の行政制度を確定する根拠にはしない。',
            '旧定義と先行21主張、8引数の部分ひな形を保持する。尊厳・残余条件と全文の意味一致は未完で、新しい原文範囲や意味確認済み区間を加算しない。'])


def reading():
    return dict(checked_on='2026-10-16',sources=[
        dict(url='https://www.korpora.org/Kant/aa08/041.html',lines='35–37',observation='民衆の態度と行為の自由への作用に続き、政府の原則と政府自身の利益判断が述べられる。ここで共同体と政府の関係を切り離さない候補を検討する。'),
        dict(url='https://www.duden.de/rechtschreibung/Regierung',section='Bedeutungen 2',observation='国家・地域を指導する機関と、それを統治する人々を挙げる現代語義を比較資料にした。'),
        dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_3_0_199',section='Obrigkeit 2',observation='共同体で命令・禁止・紛争判断の権力を持つ人々を説明し、最高・下位の当局と地域の当局を区別する。Regierungそのものの見出しではない。')],
        interpretation='統治を指導する同じ役職と、その役職を担う主体、同じ共同体への管轄を分けた候補。',
        limitations=['原刊画像の新規照合は行っていない。','DRWのRegierung見出し本文は取得に失敗し、確認済みの根拠に加えていない。','役職範囲の選択と語義全体の適合は未確定。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v8.json').read_text(encoding='utf-8'))
    packet.update(version='kant-manuscript-obligations-v9',supersedes='data/kant-manuscript-obligations-v8.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        if row['id']=='government':
            row['candidate_roots']+=['ryv','ibdqualified','ibdschema']
            row['remaining']='政策変更と自己利益判断の同じ主体・役職を、同じ共同体を管轄する組織の最高役職へ接続した。国家・組織・管轄の制度的基礎、役職範囲、原則への作用を置換に限る強さ、焦点と語義全体は未確認。'
    packet['templates'][0]['symbol']='ibdschema';packet['evidence_files']+=[BASIS,READING]
    return packet


def main():
    files=build();files|={BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',READING:json.dumps(reading(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(review(files),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
