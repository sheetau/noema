"""Record the assistant's whole-opening reading; preserve eight prior judgments.

The explicit judgment is a source reading, not inferred from passing tests.
"""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_contextual_motto import ROOT,FULL,BASIS,ANNOTATIONS

PREVIOUS='data/semantic-review-index-v25.json'
INDEX='data/semantic-review-index-v26.json'
REVIEW='data/opening-paragraph-review-v1.json'
EVIDENCE='data/contextual-motto-reading-v1.json'
FORMAL='reports/contextual-motto-v1.json'
READING='docs/opening-paragraph-review-v1.md'
STATUS='data/opening-reading-status-v4.json'

INTERPRETATION=[
    '啓蒙を、本人に帰責された未成熟から、その同じ本人の自立的な行使能力へ移る過程として説明する。',
    '未成熟の不能を、現在の本人側の判断基盤を保持し、外的な機会がある通常場面での行使能力の欠如と読む。未来の習得や単なる機会不足とは分ける。',
    '第三文は因果条件から帰責された未成熟への十分条件。決意と勇気の双方の不足が共同で原因となり、理解力の不足は原因ではないという作用範囲を採る。',
    'この箇所のラテン語は著者自身の後続説明に即して、同じ宛先が自分の理解力の使用へ勇気を持って取り組む命令と読む。全対象の判断能力を獲得する試験を加えない。',
    '後続ドイツ語は自分の理解力を使う勇気を求める。先行文の他者の指導なしという条件をこの句へ追加しない。二つの引用と説明の向きを保持する。',
    '二つの呼びかけ全体を啓蒙の標語として位置付け、先行五箇所を談話の根拠側とする帰結提示を記述する。命令の実行や論理的な証明の成立を断言しない。',
]
REASONS=[
    ('fixed_source','固定電子転記u0008の全488文字とハッシュを指定し、原刊481頁の第一段落全体とAA VIII 35頁を再読した。六箇所と順序を確認した。'),
    ('semantic_relations','同じ本人の初期の帰責された未成熟、能力への変化、他者の指導なしの使用、原因と帰責、二つの呼びかけと標語を合成している。原文の各句を別の未説明ラベルへ隠していない。'),
    ('references','本人・所有能力・使用行為・過程・前後状態を共有する。第三文のこの未成熟は同じbf、使用目標は同じbb。二つの呼びかけは同じ宛先ao、標語はその二つと同じ啓蒙biを指す。waとwbからwgの六箇所は固定の著者・本文参照である。'),
    ('presentation_role','二つの定義、条件的主張、二つの命令の引用、著者による説明と標語の帰結を分ける。引用内容や因果条件の真理、実際の命令遂行を著者の提示から推論しない。'),
    ('additions_and_omissions','原文に列挙されない全対象の理由付き判断能力の試験を除いた。特定人物、全員の実際の離脱、条件の逆向き、個々の不足の単独原因性、使用の成功保証を追加しない。所有・他者・この状態・同じ宛先と標語の指示を保持した。'),
    ('meaning_conventions','能力のプロフィール、判断基盤、方法範囲、十分さ、実際の因果的寄与と帰責、勇気・試み、著者の提示の意味規約を再読した。原文が指定しない数値や測定履歴を補わず、文脈条件として何を保持するかを明示した。'),
    ('evidence_and_limits','原刊と語義・文法資料による読解、採用した作用範囲、現在の能力・原因・帰責の16組合せと四対照、呼びかけの32組合せ、提示と標語の対照、表記往復を区別する。検査の全通過を意味同値の自動証明とはしていない。'),
    ('whole_unit_rereading','六箇所を一つの段落として再読した。この記録に明示した文脈的解釈の下で、内容・照応・提示と追加条件・脱落に未処理の項目はないと判断する。後続段落へこの判断を拡張しない。'),
]


def encoded(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'


def build():
    old_index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));load_reviews(ROOT,PREVIOUS)
    active=old_index['works']['kant-1784'];old_cat=load_catalog(ROOT,active['meaning_basis']);cat=load_catalog(ROOT,BASIS)
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    formal=json.loads((ROOT/FORMAL).read_text(encoding='utf-8'));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['structure']['eight_review_bindings_preserved'] and formal['structure']['changed_statement_indices']==[1]
    paths=set(cat.source_sha256)|set(formal['source_sha256'])|set(evidence['source_sha256'])|{FULL,BASIS,ANNOTATIONS,FORMAL,EVIDENCE,READING,
        'scripts/register_opening_paragraph_review.py','docs/contextual-motto-v1.md'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};outputs={};migrated=[]
    for path in active['reviews']:
        old=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[x['index'] for x in old['selection']['statements']]
        assert selection_binding(old_cat,indices)==old['selection']==selection_binding(cat,indices)
        new=deepcopy(old);new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            revalidated_from=path,revalidation='Selected statements, transitive definitions, meaning conventions and their bindings are unchanged.')
        new['evidence']['formal_checks'].append(FORMAL);new['evidence']['semantic_reading'].append(READING)
        new['source_sha256'].update(pins);new['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/contextual-motto-inherited-'+old['unit'].split(':')[-1]+'-review-v1.json';outputs[name]=encoded(new);migrated.append((old['unit'],name))
    source=evidence['source'];assert source['unit']=='kant-1784:u0008' and source['range']==[0,488]
    review=dict(schema_version='noema-semantic-review-1',work='kant-1784',unit=source['unit'],document=FULL,meaning_basis=BASIS,
        identifier_annotations=ANNOTATIONS,source=dict(inventory='artifacts/written-units-v1/kant-1784.json',
            unit_sha256=source['unit_sha256'],text=source['text'],range=source['range'],math=[]),selection=selection_binding(cat,[1]),
        decision='equivalent_under_stated_reading',reviewer='assistant_review',interpretation=INTERPRETATION,
        limits=['実装したアシスタントによる採用読解の判断であり、独立査読や意味一致の自動証明ではない。',
            '原文の綴り・書体・音韻や、ラテン語の全用法・歴史的含意を再現したという判断ではない。著者の説明に沿ったこの箇所の意味と提示を確認する。',
            '通常性・十分さ・因果・帰責の文脈的基準を明示した読みである。著者の主張の真実性や、人間の認知機構を証明したわけではない。',
            '追加するのはこの段落の421非空白文字だけ。後続の改訂能力に依存する草案や、表題の問い、二作品全文の完成には判断を拡張しない。'],
        unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in REASONS],
        evidence=dict(source_reading=[EVIDENCE],formal_checks=[FORMAL,'reports/exercise-capacity-v1.json'],
            semantic_reading=[READING,'docs/contextual-motto-v1.md','docs/exercise-capacity-v1.md','docs/opening-scope-v1.md','docs/opening-claims-v1.md']),source_sha256=pins)
    outputs[REVIEW]=encoded(review)
    status=dict(status='opening_paragraph_reviewed_under_stated_reading',supersedes_worklist='data/opening-reading-status-v3.json',
        document=FULL,meaning_basis=BASIS,review=REVIEW,reading_record=EVIDENCE,binding=review['selection'],
        resolved=['冒頭の能力と不足の読み','原因条件と帰責の向き','この文脈のラテン語句','二つの呼びかけと標語の範囲','第一段落の全体確認'],
        remaining_semantic_reviews=['改訂した共有能力に依存する後続草案の再確認','表題の問いと残る本文段落','アインシュタイン全文と文語体系全体'],
        source_sha256={REVIEW:digest(outputs[REVIEW].encode('utf-8')),EVIDENCE:digest((ROOT/EVIDENCE).read_bytes())})
    outputs[STATUS]=encoded(status)
    index=deepcopy(old_index);index['works']['kant-1784'].update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        reviews=[p for u,p in sorted(migrated+[(source['unit'],REVIEW)])])
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(text.encode('utf-8')) for p,text in outputs.items()});outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old=load_reviews(ROOT,PREVIOUS);new=load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(after)-set(before)=={'kant-1784:u0008'} and set(before)<=set(after) and len(after)==9
    assert after['kant-1784:u0008']['source_nonblank_characters']==421 and sum(r['source_nonblank_characters'] for r in after.values())==587
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        a=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));b=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k]==b[k] for k in ('selection','source','decision','reviewer','interpretation','requirements','unresolved'))
        assert b['revalidated_from']==row['review']
    status=json.loads((ROOT/STATUS).read_text(encoding='utf-8'));validate_hashes(ROOT,status['source_sha256'])
    assert status['review']==after['kant-1784:u0008']['review'] and not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=8,new_unit='kant-1784:u0008',total_units=9,reviewed_nonblank_characters=587,
        first_body_paragraph_reviewed=True,automatic_equivalence_proof=False)


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
