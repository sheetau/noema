"""Compose factual task adequacy and stability under fixed normal variations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_topical_standing import TOPIC,TARGS,ENABLING,EARGS

PARENTS=('data/present-epoch-assessment-basis-v1.json','data/royal-intervention-sentence-basis-v1.json')
LIBRARY='examples/v016/judgment-performance-quality.noema'
BASIS='data/judgment-performance-quality-basis-v1.json'
QUALITY='h[a a a d d] c';GOAL='i[h[a] e]'
FIELDS='person a matter a judgment a reference d point d'
ARGS='v person v matter v judgment v reference v point'
PRIMITIVES={
 'h26j3':('[a a a d] c',['criterion','person','matter','reference'],
   'この固定基準で、この本人がこの事柄を理解し判断する知的課題に適切に取り組むための、全ての適用条件の一つ。対象の区別、根拠と結論の関係、適用可能な推論や検討の規則、認識の限界への対応など、その課題に実際に必要な条件を結果を見る前に固定する。各条件はh26j4のNoema内容として明示する。本人の任意の欲望、他者の承認、教義への服従、評価資料が入手できた項目だけの選別ではない。非空性と充足は合成側で確認する。'),
 'h26j4':('[a a a a d] e',['criterion','person','matter','judgment','reference'],
   '同じ知的課題の適用条件を、同じ本人・事柄・判断・固定基準について具体的なNoemaの命題内容として返す。対象と理由や適用規則などの条件をその内容で構成し、原語のsicher/gutや条件名だけの未説明の真偽値で代用しない。その評価点で条件が実際に成立することを表し、観察者が証拠を持つこと、本人が適合だと信じること、評価の記録が存在することとは別である。'),
 'h26j5':('[a a a d d d] c',['person','matter','judgment','reference','point','candidate'],
   '同じ本人・事柄・判断の仕方と基準時点について、その遂行の安定性を調べる通常の関連変化の全範囲。本人側の既存の知的基盤、同じ課題、評価規則を保ち、関連する情報提示や通常起こりうる錯誤要因等の変化を含める。成功する場合だけを事後に選ばず、新たな学習後の技能や別の課題へ替えない。全論理的可能世界や極端な妨害まで網羅する条件ではない。元の実行点の包含は合成側で確認する。'),
 'h26j6':('[a a a d d d] a',['person','matter','judgment','reference','point','candidate'],
   '同じ本人・事柄・元の判断・固定基準・基準時点について、指定の比較状況で同じ判断の仕方を遂行する対応判断を指す。新たに良い方法を選び直した判断、他人や別事柄の成功を流用しない。元の実行点では元の判断と同一であることを合成側で確認する。候補内での実際の判断、自己の理解力の使用、条件適合は別に評価する。'),
}
MEANINGS={
 'r5sr':'同じ本人・事柄・固定基準の知的課題の適用条件h26j3が非空である。適合した項目だけに範囲を縮めず、条件内容の充足や証拠の存在はまだ要求しない。',
 'r5ss':'同じ人による同じ事柄の判断に、r5srの固定された全適用条件のh26j4の内容が同じ実行点で実際に成立する。gutの課題への適切さとして採る構成であり、資料の有無によるhzvxの証拠適合とは区別する。',
 'r5st':'同じ判断がrcrの本人の理解力による理由ある自立的な遂行であり、同じ事柄についてr5ssの実際の課題適合を満たす。自立的な遂行と各条件を別の判断から寄せ集めない。',
 'r5su':'r5srの同じ固定条件とh26j5の関連比較範囲について、元の実行点が範囲に含まれ、そこに割り当てるh26j6が元の判断と一致する。空の比較範囲又は元の失敗を別の成功に替えた比較を受け付けない。',
 'r5sv':'r5suの同じ本人・事柄・元の判断の仕方・基準について、全ての通常の関連比較で対応判断がr5stの自立的で適切な遂行を保つ。sicherを通常の錯誤要因で崩れない用い方とする明示読解で、全可能性での無謬性、主観的な自信、未来の新しい技能は要求しない。',
 'r5sw':'同じ事柄と固定基準に、sicherのr5svとgutのr5ssをhzvpの同じ判断証人へ渡す閉じた本人別の遂行内容。二条件の重なりを許し、別判断の安全さと適切さを寄せ集めない。',
 'r5sx':'同じ事柄・基準の閉じた参照をhzvqへ渡し、r5sv/r5ssを同じ質の記述として含む本人別活動の閉じた構文を作る。構築時に参照・条件・対応判断・能力を実行しない。',
 'r5sy':'同じ主題・元の事柄範囲・個体参照・基準文脈について、r5sxと同じ質付き活動のhzvrの能力評価が整う。元の基準文脈とanchorの照合を保つ。',
 'r5sz':'r5syと同じ質付き活動・本人の既有基盤についてhzvsの通常機会での行使能力を返す。現在地での外的障害、準備後の能力、無修飾のh4lと区別する。',
 'r5s2':'同じ主題・質・元の基準と全実施者範囲について、hzvtの全支援結果での質付き能力評価を返す。将来の結果で基準を緩めず、未評価を不能へ補わない。',
 'r5s3':'r5s2と同じ範囲の一実施者の一方法・同じ一結果について、hzvuの同じ質付き能力状態へ置ける可能性を返す。全員を一度に支援できること、実施済み、成功保証は加えない。',
 'r5s4':'同じ人の同じ事柄の判断で、実際に用いた理由がその判断を支持し、h26ajの固定基準で十分な認識根拠として働くという具体的な条件例。単なる証拠記録の所持、事後の理屈、別の判断の根拠を流用しない。これ一つを全課題の適切さと同義にはしない。',
 'r5s5':'同じ人の同じ事柄の判断に、rqwrの非空の使用理由と全使用理由の支持を結ぶ具体的な条件例。結論の真理、根拠の十分性、全ての知的課題の適切さとは別である。',
}
LIMITS=[
 'u0014第二文のsicher und gut zu bedienenに向け、既存の質付き能力構成へ具体的な評価方法を接続する。sicherは同じ判断の仕方が通常の関連変化でも自立的で適切に遂行される安定性、gutは知的課題の全適用条件の実際の充足と読む。唯一の歴史的語義又は無謬性の一般理論を主張しない。',
 'Adelung Sicherの誤りからの安全と熟練した手の用法、Wohlの事柄にふさわしい遂行の用法を補助にする。Kant AA IV 331の同表現は、細かな演繹の全知を前提にしない用法の対照資料であり、この箇所の読みをそれだけで確定する証明ではない。',
 '適用条件は実際の課題内容を具体的なNoemaの式で網羅する必要がある。条件の範囲・妥当性と通常の比較範囲は固定した解釈入力であり、有限例だけで現実の全条件を自動列挙したとはしない。原文の語を一つの未説明の真偽記号へ置き換えない。',
 '現在の実行点を比較範囲へ含めるので、この読解の安定性は現在の適切さも要求する。二つの形容の独立性は仮定せず、原文の二語が完全な同義とも主張しない。反対に現在だけの適切な成功は、通常の変化で失敗すれば安定的とはしない。',
 '同じ方法・技能基盤・事柄・条件基準を保つ比較である。比較状況ごとに新しい方法や学習済みの技能を選び、失敗例を外して安全だとすることを意味規約で禁じる。全論理的可能性の成功、結論の無条件な真理、経験的な信頼率の数値閾値は追加しない。',
 '内容条件の実際の充足と、記録された証拠に基づく適合hzvxは異なる。未知の基本関係は評価拒否、明示的な能力評価不足は評価条件の不成立として保持する。資料がないから本人が適切に判断できないと結論しない。',
 'r5s4/s5は具体的な条件内容を構成できることを示す。単独で宗教的判断の全条件を尽くすとはせず、各課題に必要な区別・推論・根拠・限界の全内容を与える責任を保持する。',
 '閉じた質の構文はhzvqと同じ形に固定する。現在能力と全支援結果の評価・一結果での支援可能性に同じ基準を使い、無修飾又は別の質のプロフィールを流用しない。',
 '宗教的な対象範囲と集団到達基準、進行内容、条件付きの問答と著者帰属、全文通読は未完。本文108主張・全単位16区間を保持し、確認済み文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    selected='k h26j3[v criterion v person v matter v reference]'
    text='d r5sr[person a matter a reference d] c[g criterion a['+selected+']].\n'
    basic=both('k aa[v person]','k fa[v person v judgment v point]','k fb[v judgment v matter v point]')
    allconditions='f criterion a[y['+selected+'][t[k h26j4[v criterion v person v matter v judgment v reference]][v point]]]'
    text+='d r5ss['+FIELDS+'] c['+both(basic,'k r5sr[v person v matter v reference]',allconditions)+'].\n'
    independent='k rcr[v person v judgment v point p ab p ac p fa p fb p fc p fd p ad]'
    text+='d r5st['+FIELDS+'] c['+both(independent,'k r5ss['+ARGS+']')+'].\n'
    original=ARGS+' v point'
    text+='d r5su['+FIELDS+'] c['+both('k r5sr[v person v matter v reference]','k h26j5['+original+']','e[k h26j6['+original+']][v judgment]')+'].\n'
    pair=ARGS+' v candidate';counterpart='k h26j6['+pair+']'
    stable='f candidate d[y[k h26j5['+pair+']][k r5st[v person v matter '+counterpart+' v reference v candidate]]]'
    text+='d r5sv['+FIELDS+'] c['+both('k r5su['+ARGS+']',stable)+'].\n'
    text+='d r5sw[matter a reference d] h[a] e[k hzvp[v matter v reference p r5sv p r5ss]].\n'
    text+='d r5sx[matter i[a] reference i[d]] '+GOAL+'[k hzvq[v matter v reference r[p r5sv] r[p r5ss]]].\n'
    fields=TOPIC+' standardcontext i[d]';args=TARGS+' v standardcontext r[p r5sv] r[p r5ss]'
    for name,target,extra in (('r5sy','hzvr',''),('r5sz','hzvs',''),('r5s2','hzvt',' '+ENABLING),('r5s3','hzvu',' '+ENABLING)):
        text+='d '+name+'['+fields+extra+'] h[a] e[k '+target+'['+args+(' '+EARGS if extra else '')+']].\n'
    grounds='g reason a['+both('k fc[v judgment v reason v point]','k fd[v reason v judgment v point]','k h26aj[v reason v judgment v reference v point]')+']'
    text+='d r5s4['+FIELDS+'] c['+both(basic,grounds)+'].\n'
    text+='d r5s5['+FIELDS+'] c['+both(basic,'k rqwr[v judgment v point p fc p fd]')+'].\n'
    return text

def build():
    libs=parents();all_entries={};merged=[]
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name']
            if n in all_entries:assert d==all_entries[n]['declaration'] and lib.entries[n]['meaning_ja']==all_entries[n]['meaning_ja'],n
            else:merged.append(d);all_entries[n]=lib.entries[n]
    doc=deepcopy(libs[0].document);doc.update(declarations=merged,statements=[])
    roots=['rcr','rqwr','aa','fa','fb','fc','fd','h26aj','hzvp','hzvq','hzvr','hzvs','hzvt','hzvu']
    doc['declarations']=closure(doc,roots);imported={d['name']:all_entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(all_entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in libs))
    basis=dict(status='factual_judgment_adequacy_and_normal_variation_stability_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
