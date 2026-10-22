"""Compose anchored united voices and a possible submission to the monarch."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/legislative-touchstone-basis-v1.json','data/public-insight-basis-v1.json','data/institutional-criticism-basis-v1.json')
LIBRARY='examples/v016/joint-petition.noema'
BASIS='data/joint-petition-basis-v1.json'
FAMILY='i b[h[j[a] d d d] e]'
FIELDS='group a community a recipient a proposal '+FAMILY+' bindings j[a] reference d candidate d anchor d'
ARGS='v group v community v recipient v proposal v bindings v reference v candidate v anchor'
PRIMITIVES={
 'h26db':('[a a d d d] c',['group','person','reference','candidate','anchor'],'同じ固定基準と候補履歴の基準点における、指定された共同提案集団の全成員関係。後の提出成功者だけへ選び直さず、集団の名だけやその場にいた人全員とは区別する。人間・市民資格・複数性・全員の共同提示は別に検査する。'),
 'h26dc':('[a a d d d] c',['activity','recipient','reference','candidate','point'],'同じ提案行為が、この宛先の公的な検討・判断に供するために提出される。単にその人について話すことや他人への私信ではない。全員が本人に身体的に対面すること・宛先の受領や採用・提案の実現は含めず、代表を通じた共同提出も許す。'),
 'h26dd':('[a a '+FAMILY+' j[a] d d d d] c',['person','activity','proposal','bindings','reference','candidate','anchor','point'],'この人が同じ共同提出行為において、この段階1の閉じた内容族を同じ対象列・基準・候補・基準点に適用する内容を、採用を求める自分の声として支持して提示する。単なる同席・伝達係・他人の意見の引用・別提案への賛同とは区別する。内容記述はここで実行せず、内容の真理・実現・相手の賛同を要求しない。'),
 'h26de':('[a a d d d] c',['group','method','reference','candidate','anchor'],'同じ集団が同じ候補履歴の基準点で利用可能な行為方法である。空想上の手段や別集団だけに利用できる方法を混ぜない。想定結果・共同提出の成立・全結果での成功は別条件にする。'),
 'h26df':('[a a d d d d] c',['group','method','reference','candidate','anchor','point'],'同じ集団・利用方法・固定基準・候補履歴・開始点に対する想定結果がこの状況点である。成功結果だけで結果範囲を定義せず、別の方法・履歴・開始点の結果を混ぜない。非空性、時間順序、提案の成立は合成側で検査する。'),
}
MEANINGS={
 'r5fw':'基準点の同じ集団に相異なる二人以上が属し、その全成員が同じ共同体の同点の人間の市民である。全市民がこの集団に属することも、必ず誰かを除くことも要求しない。結果点で成員を選び直さない。',
 'r5fx':'r5fwの同じ固定集団の全員が、一つの生起する提出行為へ参加し、同じ型付き内容族・対象列・基準・候補・基準点を自分の声として共同提示する。その行為の同じ宛先は同じ共同体の同点の君主的な統治者r2ujである。多数の別行為・別提案・別宛先を寄せ集めず、全員の身体的同席や提案内容の実現は要求しない。',
 'r5fy':'有効な同じ候補履歴の基準点で、同じ固定集団に利用可能な方法があり、その非空な想定結果の少なくとも一つの後続履歴点でr5fxの共同提出が成り立つ。既存xbの可能性を用い、現実の提出済みや全結果での成功保証へ強めない。',
}
LIMITS=[
 'u0013第七文のdurch Vereinigung ihrer Stimmen (wenn gleich nicht aller) einen Vorschlag vor den Thron bringen könnteへの依存群。同じ市民の複数の声が同じ提案を共同提出する読解を採る。各人の独立した投稿を数えるだけでは満たさないが、一人の代表を通じて全員の支持する提案を届けることを除外しない。',
 '提案集団は全市民でも一部でもよい。非全員という条件を必須にしない。全員一致がなくてもよいという括弧の譲歩の談話効果は、最終的な文章帰属で別に接続する。',
 'Thronは同じ共同体の君主の公的な判断の宛先を指す換喩として読む。既存r2ujの最高位・唯一の任用された保持者・委託された公務とh234fの君主的職を再利用する。椅子の存在、特定の君主名、世襲制、政策の正当性を追加しない。換喩表現の文章上の提示は全文帰属で残る。',
 '提案内容は対象列と固定文脈を持つ段階1の内容族で渡す。内部で段階0の記述を使う制度・保護の構成も渡せるが、共同提示・可能性の検査では脱引用しない。対象列の具体的な要素と長さは後続の保護・非妨害内容族で固定する。',
 '既存rko/rkpの複数性・全成員・同じ行為と提案・利用可能な方法の存在という骨格を型付き内容へ拡張する。旧定義やその意味は変更しない。新たな支持・提出・成員・利用可能性と結果の語彙関係には、それぞれ独立した解釈上の責任がある。',
 '公的洞察からこの提案可能性に足りる程度への接続、改革側の保護と旧制度維持側の非妨害、期間の到達条件、聖職者への取り立て、可能性・wohl・Nun・gleichsam・全文帰属は残る。全文確認の文字数を増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    member=lambda p:'k h26db[v group v '+p+' v reference v candidate v anchor]'
    plural='g first a[g second a['+both(member('first'),member('second'),'u[e[v first][v second]]')+']]'
    text='d r5fw[group a community a reference d candidate d anchor d] c['+both(plural,
        'f person a[y['+member('person')+']['+both('k aa[v person]','k h26cu[v person v community v reference v candidate v anchor]')+']]')+'].\n'
    joined='f person a[y['+member('person')+']['+both('k df[v person v activity v point]',
        'k h26dd[v person v activity v proposal v bindings v reference v candidate v anchor v point]')+']]'
    text+='d r5fx['+FIELDS+' point d] c['+both('k r5fw[v group v community v reference v candidate v anchor]',
        'k r2uj[v recipient v community v point]',
        'g activity a['+both('k dg[v activity v point]','k h26dc[v activity v recipient v reference v candidate v point]',joined)+']')+'].\n'
    available='i[owner a method a start d][k h26de[v owner v method v reference v candidate v start]]'
    outcomes='i[owner a method a start d end d]['+both('k h26df[v owner v method v reference v candidate v start v end]',
        'k h257z[v reference v candidate v end]','k ic[v start v end v candidate]')+']'
    text+='d r5fy['+FIELDS+'] c['+both(
        'k ta[i[point d][k h257z[v reference v candidate v point]] i[first d last d][k ic[v first v last v candidate]]]',
        'k h257z[v reference v candidate v anchor]',
        'k xb[v group b point[k r5fx['+ARGS+' v point]] v anchor '+available+' '+outcomes+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r2uj','xb','aa','df','dg','ta','h257z','ic'],[],['h26cu'])):
        for d in closure(source.document,roots) if roots else []:
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='anchored_joint_petition_to_monarchical_authority',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
