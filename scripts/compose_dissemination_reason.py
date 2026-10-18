"""Bind the author's dissemination argument to its preceding conclusion."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT, closure

PARENT='examples/v016/kant-focused-dissemination.noema'
PARENT_BASIS='data/focused-dissemination-basis-v1.json'
FULL='examples/v016/kant-dissemination-reason.noema'
CORE='examples/v016/dissemination-reason-core.noema'
BASIS='data/dissemination-reason-basis-v1.json'
READING='data/dissemination-reason-reading-v1.json'
REFERENCES={
 'hzp3':('d','カント1784の公衆の自己啓蒙を論じる段落u0011の提示文脈。現実の将来時点や、自由を仮定した候補世界の時点ではない。先行段落の提示文脈whとは暗黙に同一化しない。'),
 'hzp4':('a','u0011の先頭文、原文位置[0,128)で公衆の自己啓蒙の可能性と自由の条件付きのほぼ不可避性を述べる結論側の文章箇所。文章箇所への参照であって、その全文内容の代替や真理値ではない。'),
 'hzp5':('a','u0011の原文位置[129,448)でDennから伝播の将来記述までを述べる根拠側の文章箇所。自己思考者、後見役、自立、価値評価と伝播の内容自体を一つの不透明な意味述語へ置き換えたものではない。'),
}
MEANING='同じ著者waが、この段落の提示文脈hzp3で、伝播を述べる箇所hzp5を、公衆の自己啓蒙の可能性と自由の条件を述べる箇所hzp4の根拠として提示する。本文順序では結論箇所が根拠箇所より前であり、二箇所は異なる。主張内容の真理、論理的含意、原因としての十分性や、自由が現実に成立することを要求しない。'
LIMITS=[
 'Dennを著者の理由提示として読む。udは根拠と結論の談話関係であり、因果的な出来事の発生や証明の妥当性ではない。ueは本文順序であり時間順序ではない。',
 '結論側の参照範囲は自由の条件付き判断を含む先頭文全体とする。根拠が先頭文の各下位節を独立に証明するとは要求しない。',
 '局所参照は原文箇所を同定する。全文内容の記述は既存の構成候補へ別途結ぶ必要があり、この談話関係から自動生成・確定しない。',
 '原刊483頁と照合した採用する読みを別資料へ保存する。自由の仮定の下での将来予測、比較背景、比喩、具体的な引数の接続と全文の意味確認は未完。',
 '既存32文と全宣言・意味規約・七単位の確認を保持し、理由提示について一文追加する。追加の明示的な原文対応範囲はDennの四文字だけである。',
]


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not (set(REFERENCES)|{'hzp6'})&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text=''.join('r '+name+'[] '+sort+'.' for name,(sort,_) in REFERENCES.items())
    text+='d hzp6[] c[w[u[e[k hzp4[]][k hzp5[]]]][w[k ud[k wa[] i[node a][e[v node][k hzp5[]]] k hzp4[] k hzp3[]]][k ue[k hzp4[] k hzp5[] k hzp3[]]]]].s[k hzp6[]].'
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hzp6']);core['statements']=doc['statements'][-1:]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']][1])
                for d in doc['declarations'][size:] if d['kind']=='primitive'}
    basis=dict(status='source_anchored_author_reason_presentation',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions={'hzp6':MEANING},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        reading_manifest=READING,limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Source-anchored reason presentation added to the manuscript',flush=True)


if __name__=='__main__':main()
