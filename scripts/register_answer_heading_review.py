"""Record the explicit u0005 judgment and carry seven unchanged reviews forward.

The judgment below is a recorded reading, not the result of a test classifier.
Registration validates provenance and selections; it does not prove equivalence.
"""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,load_reviews,validate_hashes
from scripts.compose_answer_heading import ROOT,FULL,BASIS,ANNOTATIONS

PREVIOUS='data/semantic-review-index-v22.json'
INDEX='data/semantic-review-index-v23.json'
REVIEW='data/answer-heading-review-v1.json'
EVIDENCE='data/answer-heading-evidence-v1.json'
FORMAL='reports/answer-heading-v1.json'
READING='docs/answer-heading-review-v1.md'


def encoded(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'


def build():
    old_index=json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'));load_reviews(ROOT,PREVIOUS)
    old_active=old_index['works']['kant-1784'];old_cat=load_catalog(ROOT,old_active['meaning_basis'])
    cat=load_catalog(ROOT,BASIS)
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    formal=json.loads((ROOT/FORMAL).read_text(encoding='utf-8'));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['structure']['seven_review_bindings_preserved'] and formal['structure']['new_source_statements']==1
    shared=set(cat.source_sha256)|set(formal['source_sha256'])|set(evidence['source_sha256'])|{
        FULL,BASIS,ANNOTATIONS,FORMAL,EVIDENCE,READING,'scripts/register_answer_heading_review.py','tests/test_answer_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(shared)}
    outputs={};migrated=[]
    for path in old_active['reviews']:
        old=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in old['selection']['statements']]
        assert selection_binding(old_cat,indices)==old['selection']==selection_binding(cat,indices)
        new=deepcopy(old);new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            revalidated_from=path,revalidation='Selected statements, transitive definitions and meaning conventions are unchanged; the original semantic judgment is carried forward.')
        new['evidence']['formal_checks'].append(FORMAL);new['evidence']['semantic_reading'].append(READING)
        new['source_sha256'].update(pins);new['source_sha256'][path]=digest((ROOT/path).read_bytes())
        name='data/answer-heading-inherited-'+old['unit'].split(':')[-1]+'-review-v1.json'
        outputs[name]=encoded(new);migrated.append((old['unit'],name))
    unit=evidence['source'];assert unit['unit']=='kant-1784:u0005' and unit['text']=='Beantwortung der Frage:'
    reasons=[
        ('fixed_source','固定電子転記u0005の全23文字とハッシュを指定し、原刊481頁の導入と次行の問いを視認した。'),
        ('semantic_relations','現在の論説内にある導入が、同じ論説を後続の問いへの回答として指す。成立・記載・回答としての言及・本文順序を同じ文脈で結び、問いと導入を区別する。'),
        ('references','hzikは現在の論説、hziaは後続の既存の問い箇所、hzs2は今回の導入、whは既存の表題と冒頭の提示文脈である。冒頭の回答箇所と脚注の言及を代用しない。'),
        ('presentation_role','名詞句を論説全体の回答としての位置付けと読む。現実の読者へ返答を要求する出来事、冒頭第一文だけの完全な回答、正しさの認定へ替えない。'),
        ('additions_and_omissions','定冠詞とコロンによる後続の問いへの照応、現在の論説を回答とする位置付けを保持する。正答・説明の十分性・執筆日時・実際の印刷・読者の理解を加えない。'),
        ('meaning_conventions','dg・hzjk・hzjj・ueと既存の文書・問い・文脈の意味規約を再読した。新しい意味関係はなく、原文全体を未説明の基本記号へ隠していない。'),
        ('evidence_and_limits','原刊の読解、意味規約の再読、32組合せ・三文の12対照・未知入力・往復検査を区別した。試験の成功だけで自然言語との意味一致を判定していない。'),
        ('whole_unit_rereading','u0005全体を、同じ論説を後続の問いへの回答として位置付ける導入と再読し、その読みの位置付け・照応・提示の役割に未処理項目はないと判断した。'),
    ]
    review=dict(schema_version='noema-semantic-review-1',work='kant-1784',unit=unit['unit'],document=FULL,meaning_basis=BASIS,
        identifier_annotations=ANNOTATIONS,source=dict(inventory='artifacts/written-units-v1/kant-1784.json',
            unit_sha256=unit['unit_sha256'],text=unit['text'],range=unit['range'],math=[]),selection=selection_binding(cat,[34]),
        decision='equivalent_under_stated_reading',reviewer='assistant_review',
        interpretation=['表題の名詞句を、現在の論説を後続する問いへの回答として位置付ける導入と読む。問いの箇所は文脈上の同じ参照を用いる。'],
        limits=['実装したアシスタントの意味判断であり、独立査読や意味一致の自動証明ではない。',
            'この単位の問いへの照応を確認する。u0006の問い内容・啓蒙の語義、u0008の回答内容、表題全体と本文全体の完成は認定しない。',
            '確認する分量は21非空白文字。短い単位の件数を論説全体の完成割合とみなさない。'],
        unresolved=[],requirements=[dict(id=key,decision='satisfied',reason=reason) for key,reason in reasons],
        evidence=dict(source_reading=[EVIDENCE],formal_checks=[FORMAL],semantic_reading=[READING,'docs/answer-heading-v1.md']),source_sha256=pins)
    outputs[REVIEW]=encoded(review)
    index=deepcopy(old_index);active=index['works']['kant-1784']
    active.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        reviews=[path for unit,path in sorted(migrated+[(unit['unit'],REVIEW)])])
    index['source_sha256'].update({p:digest((ROOT/p).read_bytes()) for p in (PREVIOUS,FULL,BASIS,ANNOTATIONS)})
    index['source_sha256'].update({p:digest(text.encode('utf-8')) for p,text in outputs.items()})
    outputs[INDEX]=encoded(index)
    return outputs


def audit_registration():
    old=load_reviews(ROOT,PREVIOUS);new=load_reviews(ROOT,INDEX)
    before={r['unit']:r for r in old['works']['kant-1784']};after={r['unit']:r for r in new['works']['kant-1784']}
    assert set(after)-set(before)=={'kant-1784:u0005'} and set(before)<=set(after)
    assert len(after)==8 and after['kant-1784:u0005']['source_nonblank_characters']==21
    assert sum(r['source_nonblank_characters'] for r in after.values())==166
    assert not {'kant-1784:u0006','kant-1784:u0008'}&set(after)
    assert new['works']['einstein-1905']==old['works']['einstein-1905']==[]
    for unit,row in before.items():
        prior=json.loads((ROOT/row['review']).read_text(encoding='utf-8'));current=json.loads((ROOT/after[unit]['review']).read_text(encoding='utf-8'))
        for key in ('selection','source','decision','reviewer','interpretation','requirements','unresolved'):
            assert current[key]==prior[key],(unit,key)
        assert current['revalidated_from']==row['review']
    assert new['semantic_equivalence_automatically_proved'] is False
    return dict(previous_reviews_preserved=7,new_unit='kant-1784:u0005',total_units=8,reviewed_nonblank_characters=166,
        title_question_and_body_still_unreviewed=True,automatic_equivalence_proof=False)


def main():
    for p,text in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==text,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    print(json.dumps(audit_registration(),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
