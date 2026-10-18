"""Register the explanatory title reading while preserving nine earlier judgments."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_explanatory_question import ROOT,FULL,BASIS,ANNOTATIONS

PREVIOUS='data/semantic-review-index-v34.json'
INDEX='data/semantic-review-index-v35.json'
REVIEW='data/title-question-review-v1.json'
EVIDENCE='data/explanatory-question-reading-v1.json'
FORMAL='reports/explanatory-question-v1.json'
READING='docs/title-question-review-v1.md'
STATUS='data/title-question-status-v1.json'
INTERPRETATION=[
 'Was istを、同じ文脈で啓蒙の内容・構成を明らかにする性質記述を求める問いとして読む。実例や別名だけを求める問いとはしない。',
 '対象は第一段落で確認したbiと同じ啓蒙の内容であり、本人に帰責された未成熟から自立的な行使能力への移行を参照する。',
 '質問は外延条件と説明としての条件を区別する。定義を展開した説明は使えるが、構文や外延が一致するだけで十分な説明と認定しない。',
 '著者が表題に問いを提示する関係であり、現実の聞き手への命令、著者の無知、正答の存在・唯一性・十分性は追加しない。',
 '隣接する回答の位置付けと本文冒頭の説明は別の文に保持する。問いの単位自体はカントの答えの真実性を主張しない。',
]
REASONS=[
 ('fixed_source','固定電子転記u0006の全19文字とハッシュを指定し、原刊481頁の独立した表題行と疑問符を再度目視した。直前の導入、直後の参照指示、冒頭の説明と区別した。'),
 ('semantic_relations','問いを、性質記述を答えとする型付き質問として構成する。外延一致と、同じ概念の構成・成立条件を明らかにする説明関係を分け、別名だけでは足りない役割を保持する。'),
 ('references','著者wa、問い箇所hzia、表題・冒頭の文脈whと同じbiを用いる。biの定義本体と意味規約は確認済み第一段落のものから変えていない。'),
 ('presentation_role','文0のhzvaは表題での質問提示のみを記述する。答えの提示との接続は末尾の別文hzvbに分け、問いから答えの真理や実際の聞き手への要求を導かない。'),
 ('additions_and_omissions','何かを問う役割、対象の概念、疑問の提示を保持する。特定の実例、別名だけの回答、数値的基準、唯一の答え、著者の無知や読者の理解成功を加えない。原刊の字間や書体を意味の条件としない。'),
 ('meaning_conventions','hzv6を参照・候補・文脈に結ぶ説明関係として定義した。外延や構文同一性へ還元せず、構成・成立条件の説明という規約を持つ。具体候補を自動評価する汎用アルゴリズムの完成を、問いを記述する条件とはしない。'),
 ('evidence_and_limits','原刊目視と第一段落の採用読解、512組合せ・八つの個体状況対照・四つの記述文脈対照、32提示組合せ・13本文条件、未知入力と引用階層、表記往復を別の根拠とする。有限検査から自然言語との意味一致を自動証明しない。'),
 ('whole_unit_rereading','原刊の一行を、対象、概念の説明を求める役割、疑問の提示として再読した。明示した読みの下でこの単位内の未処理の意味項目はないと判断する。後続の回答の真実性や他のwhat・wasの用法へ判断を広げない。'),
]


def encoded(obj):return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'


def build():
    old_index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));load_reviews(ROOT,PREVIOUS)
    active=old_index['works']['kant-1784'];old_cat=load_catalog(ROOT,active['meaning_basis']);cat=load_catalog(ROOT,BASIS)
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    formal=json.loads((ROOT/FORMAL).read_text(encoding='utf-8'));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['structure']['nine_review_bindings_preserved'] and formal['structure']['changed_statement_indices']==[0]
    assert formal['structure']['appended_statement_indices']==[40] and formal['structure']['other_statements_preserved']==39
    opening_path=next(p for p in active['reviews'] if 'u0008' in p)
    opening=json.loads((ROOT/opening_path).read_text(encoding='utf-8'));validate_hashes(ROOT,opening['source_sha256'])
    paths=set(cat.source_sha256)|set(formal['source_sha256'])|set(evidence['source_sha256'])|set(opening['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,FORMAL,EVIDENCE,READING,opening_path,'scripts/register_title_question_review.py',
        'docs/explanatory-question-v1.md','docs/opening-paragraph-review-v1.md'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in active['reviews']:
        old=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in old['selection']['statements']]
        assert selection_binding(old_cat,indices)==old['selection']==selection_binding(cat,indices)
        new=deepcopy(old);new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            revalidated_from=path,revalidation='Selected statements, transitive definitions and meaning conventions are unchanged; the separate title question has its own review.')
        new['evidence']['formal_checks'].append(FORMAL);new['evidence']['semantic_reading'].append(READING)
        new['source_sha256'].update(pins);new['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/explanatory-question-inherited-'+old['unit'].split(':')[-1]+'-review-v1.json';outputs[name]=encoded(new);migrated.append((old['unit'],name))
    src=evidence['source'];assert src['unit']=='kant-1784:u0006' and src['range']==[0,19]
    review=dict(schema_version='noema-semantic-review-1',work='kant-1784',unit=src['unit'],document=FULL,meaning_basis=BASIS,
        identifier_annotations=ANNOTATIONS,source=dict(inventory='artifacts/written-units-v1/kant-1784.json',unit_sha256=src['unit_sha256'],
            text=src['text'],range=src['range'],math=[]),selection=selection_binding(cat,[0]),
        decision='equivalent_under_stated_reading',reviewer='assistant_review',interpretation=INTERPRETATION,
        limits=['実装したアシスタントの採用読解による判断であり、独立査読や意味一致の自動証明ではない。',
            '文脈上の概念説明を求める表題として確認する。what・wasの全用法や、啓蒙の歴史的・哲学的な全解釈は含まない。',
            '説明関係の意味規約を記述できることと、あらゆる候補の真偽の自動判定を分ける。著者の答えの正しさや全読者の理解は認定しない。',
            '今回の追加は17非空白文字だけであり、後続本文、アインシュタイン全文、言語全体の完成へ判断を広げない。'],
        unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in REASONS],
        evidence=dict(source_reading=[EVIDENCE],formal_checks=[FORMAL],
            semantic_reading=[READING,'docs/explanatory-question-v1.md','docs/opening-paragraph-review-v1.md',opening_path]),source_sha256=pins)
    outputs[REVIEW]=encoded(review)
    outputs[STATUS]=encoded(dict(status='title_definition_question_reviewed_under_stated_reading',document=FULL,review=REVIEW,
        resolved=['外延一致だけでは説明を求める役割が不足する問題','表題の問いと第一段落で確認した概念との接続','u0006全体の意味確認'],
        remaining=['第二段落以降の意味確認','歩行・学習見込み等の残る本文表現','アインシュタイン全文と文語体系全体'],
        source_sha256={REVIEW:digest(outputs[REVIEW].encode('utf-8')),EVIDENCE:digest((ROOT/EVIDENCE).read_bytes())}))
    index=deepcopy(old_index);index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        reviews=[p for _,p in sorted(migrated+[(src['unit'],REVIEW)])])
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(body.encode('utf-8')) for p,body in outputs.items()});outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old=load_reviews(ROOT,PREVIOUS);new=load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(after)-set(before)=={'kant-1784:u0006'} and set(before)<=set(after) and len(after)==10
    assert after['kant-1784:u0006']['source_nonblank_characters']==17
    assert sum(r['source_nonblank_characters'] for r in after.values())==604
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        a=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));b=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k]==b[k] for k in ('selection','source','decision','reviewer','interpretation','requirements','unresolved'))
        assert b['revalidated_from']==row['review']
    status=json.loads((ROOT/STATUS).read_text(encoding='utf-8'));validate_hashes(ROOT,status['source_sha256'])
    assert status['review']==after['kant-1784:u0006']['review'] and not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=9,new_unit='kant-1784:u0006',total_units=10,reviewed_nonblank_characters=604,
        automatic_equivalence_proof=False)


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
