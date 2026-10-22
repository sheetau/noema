"""Close the civic setting of a shared highest governing office."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/legislative-freedom-sentence-basis-v1.json'
OLD='examples/v016/collective-office.noema';OLD_BASIS='data/collective-office-basis-v1.json'
LIBRARY='examples/v016/republic-polity.noema';BASIS='data/republic-polity-basis-v1.json'
PRIMITIVES={
 'h26vy':('[a a d d] c',['order','community','reference','point'],
  '同じ固定基準で指定された市民的な法秩序が、この点で同じ共同体の公的統治・裁定・執行の制度的な枠組みとして運用されている。単なる提案・過去の法典・私的団体の内部規則だけと区別する。個別違反や紛争が一つもないこと、全条件の完全な実現、全員の賛同、道徳的な正当性を要求しない。秩序の内容範囲と政治的な位置付けは既存h26hb/h26hcで別に結ぶ。'),
 'h26vz':('[a a d d] j[a]',['community','office','reference','point'],
  '同じ政治的共同体・指定役職・固定基準・評価点の保持者全員を列挙する名簿。名目だけの保持者、決定に影響しない者、任用を確認できない者を事後に落とさない。順序は同じh26v2の決定規則の入力位置に対応し、完全性・重複なし・二人以上・全員の人間性と任用を合成側で確認する。全国民の名簿や別役職の保持者列とは分ける。'),
 'h26v2':('[a a d d] h[j[c]] c',['community','office','reference','point'],
  '同じ共同体の同じ統治役職について、h26vzの各位置の保持者の肯否入力から、その役職による公的な最高意思決定として制度上採る肯否を返す決定規則。単なる参考投票や私的な賛否集計とは分け、現在の入力・採択・執行済みを含意しない。実際の役職の全保持者を入力へ対応させ、都合のよい一回の投票だけで規則を決めない。多数決・全員一致・等しい重み・普通選挙・全市民の参加は一律に要求しない。'),
}
MEANINGS={
 'r6fr':'同じ共同体は人間個人ではなく、固定基準で人の成員が非空で、対外的な合意を自らの公的行為として担う政治的主体h257dである。同じ共同体に非空の条件内容を持つ市民的法秩序r5m5があり、この点でその枠組みが運用される。私的な会社や委員会の規則だけを国家的な公的秩序へ代用しない。全規則の無違反は要求しない。',
 'r6fs':'同じ政治的共同体・役職・固定基準・点について、統治役職の全範囲h234dと上位関係h234e、同じ役職保持hzwn、名簿h26vzと公式の決定規則h26v2を既存rwpへ結ぶ。最高役職の全保持者は二人以上の人で全員に決定への影響可能性があり、全保持者の同じ共同体による有効な任用r2uiと職務委託cfを要求する。未任用者を保持者範囲から落として成功させない。',
 'r6ft':'同じ共同体・役職・法秩序・基準・点で、r6frの公的な国家的共同体の枠組みとr6fsの最高統治職の共同保持を合わせる。別共同体の秩序や最高職で条件を寄せ集めない。',
 'r6fu':'同じ共同体・固定基準について、同じ点でr6ftを満たす最高役職と法秩序がある内容。Freistaatを最高権力が複数に委ねられる共和国として読む候補範囲。特定の法案の採択、発言の可否、平穏の実現、現代の普通選挙は分類に補わない。',
}
LIMITS=[
 'u0017第一文ein Freistaatを、保存したAdelungのFreystaatからRepublikへの狭い語義に即し、国家的な市民的共同体の最高統治職を複数の人が担う共和国として読む。1811年版の電子転写は1784年本文より後であり、唯一のカント解釈や原刊画像照合を主張しない。',
 '旧rwpの共同保持と実質的な影響可能性を保持し、未充足civicを、既存の政治的な成員・対外的公的主体・非空の市民的法秩序とその運用へ具体化する。領域・国籍・外交承認など現代の主権国家の一括要件、法律の道徳的正当性、全規則が守られることを追加しない。',
 '統治制度の全役職と推移的な上位関係を使う。最高職より上の君主や比較不能な役職を隠さず、最高ではない合議委員会を共和国の最高権力としない。名簿は同じ点の実際の保持者hzwnと照合し、全員の同じ役職・共同体への任用と委託を別に確認する。',
 '決定規則は同じ最高職の公式の意思決定規則として入力する。全保持者が影響し得ることは、他者の入力を固定して本人だけを変えれば結果が変わる組合せがあるという旧rwmの強い操作的な読み。現実に自由に投票したこと、全員同意、等しい権力、多数決、普通選挙を意味しない。',
 '一つの最高職を複数で担う制度モデルを採る。複数の最高権限の分立・連邦制・複合君主制を含む歴史上の全共和国の必要十分条件とはしない。特定の立法や対外合意が現に実行されたことは分類から要求しない。',
 'この範囲は第一文の発言主体との対比へ渡すためのもの。nicht wagen darfの危険を認める試み・非許可基準、集団としての発言、同じ引用命令、上位nurの必要条件、比喩と談話・全文帰属は未統合。本文119主張・登録簿v203・19全単位判断と確認文字数を保持する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rwp',))
    means=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    return ds,{d['name']:means[d['name']] for d in ds if d['name'] in means}

def definitions():
    text='d r6fr[community a order a reference d point d] c['+both('u[k aa[v community]]','k r57y[v community v reference]',
      'k h257d[v community v reference]','k r5m5[v order v community v reference]','k h26vy[v order v community v reference v point]')+'].\n'
    holders='i[person a role a polity a context d]['+both('k h234d[v role v polity v context]','k hzwn[v person v role v context]')+']'
    collective='k rwp[v office v community v point p h234d p h234e k h26vz[v community v office v reference v point] '+holders+' p aa k h26v2[v community v office v reference v point]]'
    commissioned='f person a[y[k hzwn[v person v office v point]]['+both('k r2ui[v person v office v community v point]','k cf[v person v office v point]')+']]'
    text+='d r6fs[community a office a reference d point d] c['+both(collective,commissioned)+'].\n'
    text+='d r6ft[community a office a order a reference d] e[b point['+both('k r6fr[v community v order v reference v point]','k r6fs[v community v office v reference v point]')+']].\n'
    text+='d r6fu[community a reference d] e[b point[g office a[g order a[t[k r6ft[v community v office v order v reference]][v point]]]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r57y','r5m5','h257d','h234d','h234e','r2ui','cf','rcm','rs','rt','rz','rex')),statements=[])
    imported={d['name']:p.entries[d['name']] for d in doc['declarations']};ds,means=legacy()
    for d in ds:
        if d['name'] in imported:
            assert d==imported[d['name']]['declaration']
            if d['name'] in means:assert means[d['name']]==imported[d['name']]['meaning_ja']
        else:doc['declarations'].append(d)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='public_civic_polity_and_shared_highest_office_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
