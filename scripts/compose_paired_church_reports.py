"""Bind ranked teaching and grounds reports to the same speaker and church."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import MESSAGE

PARENTS=('data/clerical-explanation-basis-v1.json','data/institutional-teaching-grounds-basis-v1.json')
LIBRARY='examples/v016/paired-church-reports.noema'
BASIS='data/paired-church-reports-basis-v1.json'
RANKED='i b[h[a] f]'
PRIMITIVES={
    'h247x':('[a a a a '+RANKED+' '+RANKED+' d] c',
        ['utterance','speaker','recipient','subject','first_message','second_message','point'],
        '同じ発話で同じ話者が同じ受け手に同じ主題について、第一の発話内容を述べ、続けて第二の発話内容をそれに関連する説明として付ける。二つの提示は別に結ぶ。単なる順序なしの連言、対照的留保、第一の撤回、第二が第一を論理的に証明することへ置き換えない。記述を脱引用せず、両内容の真理や受け手の理解を要求しない。'),
    'h247y':('[a a a d] c',['utterance','speaker','organization','point'],
        'この発話で話者が、同じ組織を自分を含む文脈上の複数者に共通する所属先として一人称複数で指示する。著者のわれわれ、話者を含まない他者集団、別組織への指示とは分ける。受け手全員をその複数者に含めること、全成員の信念一致、所有権、実際の所属の真理はこの指示の提示から導かない。'),
}
MEANINGS={
    'r4t':'同じ組織の閉じた呼称と同じ段階0の内側の発話記述から、r4rの教示報告を段階1の閉じた記述として構成する。内側の記述そのものを引用の値として渡し、教義の内容を実行しない。',
    'r4u':'同じ組織・教示判断・理由範囲の閉じた呼称と同じ内側の発話記述から、r4sの使用論拠報告を段階1の閉じた記述として構成する。組織と内側の発話をr4tと共有でき、別の内容の根拠へすり替えない。',
    'r4v':'同じ話者による同じ実際の発話が、非空の指定受け手範囲の全員へ、同じ主題についてr4tとr4uを提示する。話者側の一人称複数による同じ組織の指示と、教示報告から論拠報告への説明的な順序を保持する。報告内容・教義・実際の所属を事実化しない。',
    'r4w':'同じ本人・職務・教会・主題の現職と業務担当r37z、同じ発話の職務分類cbに、r4vの二報告を結ぶ。組織の呼称が元の教会を指すことを明示してから同じ記述を両報告へ渡す。発言の予想や存在一般の主張とは別の実行内容である。',
}
LIMITS=[
    'u0012[3794,3898)の予想される発言の実行内容に向けた依存群。Er wird sagenの見込み、dieses oder jenesの不特定性、dasの論拠範囲への指示、著者帰属は未統合。本文と意味確認文字数は据え置く。',
    '段階1の閉じた報告記述を既存h234gで提示する。段階0しか受けないf2へ押し込まず、r4t/r4uで同じ内側の発話記述を値として引用する。引用の別名を内容の真理値だけで同一視しない。',
    '二報告は同じ発話行為・話者・主題・全指定宛先へ結ぶ。原文が具体的な受け手人数を指定しないため非空だけを要求し、全会衆への一度の実際の講義を補わない。',
    'unsereは引用内の話者を含む文脈上の複数者に共通する所属先としての指示と読む。実際の成員の完全な一覧、全受け手の所属、著者本人の宗教や教義への確信は補わない。所属提示の一般関係h247yを明示するが、あらゆる所有表現の理論を完成したとはしない。',
    'セミコロンで続く根拠報告は、先の教示報告に関連してその用いる根拠を説明する継続として保持する。対照的留保h234hを流用せず、論理的十分性や妥当性を加えない。',
    'r4wの実行内容は後続構成で予想の内側に置く。現実の講義済み、将来の必然的実行や自己の確信をこの依存群から主張しない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r4t[church i[a] message '+MESSAGE+'] '+RANKED+'[o a[r b[p r4r]][v church o r[v message]]].\n'
    text+='d r4u[church i[a] judgment i[a] message '+MESSAGE+' reasons i[h[a] c]] '+RANKED+'[o a[r b[p r4s]][v church v judgment o r[v message] v reasons]].\n'
    fields='speaker a utterance a subject a church i[a] judgment i[a] message '+MESSAGE+' reasons i[h[a] c] audience h[a] c point d'
    first='k r4t[v church v message]';second='k r4u[v church v judgment v message v reasons]'
    text+='d r4v['+fields+'] c['+both('k aa[v speaker]','k dg[v utterance v point]','k f3[v speaker v utterance v point]',
        'k h247y[v utterance v speaker s[v church] v point]',
        'g recipient a[c[v audience][v recipient]]',
        'f recipient a[y[c[v audience][v recipient]]['+both('k aa[v recipient]',
            'k h234g[v utterance v recipient v subject '+first+' v point]',
            'k h234g[v utterance v recipient v subject '+second+' v point]',
            'k h247x[v utterance v speaker v recipient v subject '+first+' '+second+' v point]')+']]')+'].\n'
    text+='d r4w[person a role a church a subject a utterance a churchname i[a] judgment i[a] message '+MESSAGE+' reasons i[h[a] c] audience h[a] c] e[b point['+both(
        'e[v church][s[v churchname]]','k r37z[v person v role v church v subject v point]',
        'k cb[v person v utterance v role v point]',
        'k r4v[v person v utterance v subject v churchname v judgment v message v reasons v audience v point]')+']].\n'
    return text


def build():
    old,dependency=parents();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r37z','h234g','dg','f3','cb']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(dependency.document,['r4r','r4s']):
        n=d['name'];e=dependency.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(dependency.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_speaker_church_and_ranked_ordered_reports',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
