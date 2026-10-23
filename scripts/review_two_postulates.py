"""Record the complete second sentence under stated readings, not a whole unit."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_two_postulates import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/two-postulates-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][3];source=unit['text'][523:889]
    assert source.startswith('Wir wollen diese Vermutung') and source.endswith('[M0001] fortpflanze.')
    rows=[
        ('固定原文と頁跨ぎ','891–892頁にまたがる第二文全体を固定した転記と照合する。M0001はVであり数値に替えない。',['eiscl','tc']),
        ('先行推測と前提化の意思','diese Vermutungを第一文の同じeifjへ結ぶ。著者がこの内容を論説の仮定に採用しようとする方針として記述し、完了事実や実証へ替えない。',['eifj','eifz','eiscf']),
        ('同じ内容の今後の呼称','deren Inhaltは同じ推測の内容。後続本文全体を範囲とし、Prinzip der Relativitätという呼称をその内容へ結ぶ。',['eiscg','eisch','eisci','eif4']),
        ('第二仮定の追加','同じ論述主体・箇所・論説で光速度内容を追加採用する行為を第一の採用と結び、außerdemの追加を保持する。',['eif2','eif3','eisb2']),
        ('真空中の光と共通速度','同じ光線・放出元・放出・区間・系・単位・真空・経路長と、同期した局所時刻を結ぶ。全適格系と全伝播区間で同じVを使う明示した読みを保持する。',['eifw','eifx','eify','saf','sax','sak']),
        ('光源運動からの独立性','全運動状態・方向・時刻・非零部分区間を含む完全範囲に同じ値を要求し、静止光源だけ又は二標本の比較へ縮めない。',['eiscd','eisce','eifx']),
        ('同じ二内容の見かけ上のみの不整合','mit ihmは同じ相対性原理eifj。二内容を別々の意味や設定にせず、非空の見かけ候補全てでの不整合と、現在の判断点での同じ設定における両立性を結ぶ。',['eiscj','eisck','sqh','eif5','eif6','eif7','eigd']),
        ('一文全体の提示','意思・命名・留保を同じ点へ結び、著者と論説への帰属、命名の挿入、第二仮定への限定、第一文からの順序を保つ。',['eiga','eigb','eigc','eir3','eisa5','ue']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-principles-source-reading-v1.json','docs/vacuum-light-postulate-v1.md','reports/vacuum-light-postulate-v1.json','scripts/review_two_postulates.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[523,889],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第三文の二前提の十分性','第四文の光エーテル不要','四文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
