"""Read the actual Kant generator and expose its geometry/meaning boundary."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import html
import json
import math
from pathlib import Path

from noema.constructed import parse
from scripts import balanced_circle_script as b
from scripts.contextual_opening_script import compile_expression
from scripts.kant_geometry_reader import read_geometry,recover_seams,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-generator-analysis'
PROVENANCE='output/kant-page-script-v3/provenance.json'
NORMAL='examples/v016/branch-circle-samples.noema'


def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def source_entries():
    freeze=json.loads((ROOT/'data/writing-freeze-v1.json').read_text(encoding='utf-8'))
    for path,expected in freeze['source_sha256'].items():
        if sha(path)!=expected:raise ValueError('Frozen generator/rules changed: '+path)
    if sha(PROVENANCE)!=freeze['output_sha256'][PROVENANCE]:raise ValueError('Frozen geometry snapshot changed')
    page=json.loads((ROOT/PROVENANCE).read_text(encoding='utf-8'))
    return [e for p in page['paragraphs'] for e in p['entries']]


@lru_cache(maxsize=40)
def observed(index):
    entry=source_entries()[index];source=entry['compiled']
    # The reader receives transport geometry, never source/groups/paths.
    drawing=from_svg(to_svg(source['shapes']))
    geometry=read_geometry(drawing);seams=recover_seams(geometry)
    expected=[[list(map(lambda x:round(x,7),p)) for p in edge['centers']] for edge in source['invisible']]
    if len(seams)!=len(expected) or any(math.dist(p,q)>1e-5 for a,b_ in zip(seams,expected) for p,q in zip(a,b_)):
        raise ValueError('Public seam rule does not recover this original boundary')
    modes=Counter()
    for group in source['groups']:
        c=next(c for c in geometry['circles'] if math.dist(c['center'],[group['x'],group['y']])<1e-5
               and c['size']==('large' if b.near(group['radius'],b.LARGE) else 'medium' if b.near(group['radius'],b.MEDIUM) else 'small'))
        modes[group['stroke_mode']+' -> '+c['center_kind']]+=1
    return dict(statement=entry['statement'],geometry=geometry,seams=seams,
                authored_to_observed=dict(sorted(modes.items())))


@lru_cache(maxsize=1)
def generator_witnesses():
    document=parse((ROOT/NORMAL).read_text(encoding='utf-8'))
    registry={d['name']:i for i,d in enumerate(document['declarations'])}
    output=[]
    for index,statement in enumerate(document['statements']):
        drawing=compile_expression(statement,reference_order=registry)
        geometry=read_geometry(from_svg(to_svg(drawing['shapes'])))
        output.append(dict(key='normal-'+str(index+1),source=statement,drawing=drawing,geometry=geometry))
    left=deepcopy(document['statements'][0]);right=deepcopy(left)
    right['body']['arguments'][0]['symbol']='home'
    a=compile_expression(left,reference_order=registry)
    c=compile_expression(right,reference_order=registry)
    collision=dict(left=left,right=right,svg_equal=to_svg(a['shapes'])==to_svg(c['shapes']))
    if not collision['svg_equal']:raise ValueError('Known lexical collision changed')
    # Check whether conjunction association survives the old display fusion.
    leaf=lambda name:dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol='town',arguments=[])])
    conjunction=lambda a,c:dict(kind='and',arguments=[a,c])
    x,y,z=leaf('fruit'),leaf('red'),leaf('round')
    forms=[dict(kind='assert',body=conjunction(conjunction(x,y),z)),
           dict(kind='assert',body=conjunction(x,conjunction(y,z)))]
    compiled=[compile_expression(f,reference_order=registry) for f in forms]
    association=dict(left=forms[0],right=forms[1],
        svg_equal=to_svg(compiled[0]['shapes'])==to_svg(compiled[1]['shapes']),
        event_count=[len(c['groups']) for c in compiled])
    return output,collision,association


@lru_cache(maxsize=1)
def regenerated_kant():
    chosen={}
    for entry in source_entries():
        source=entry['compiled'];family=source['opening']['family']
        if family in chosen:continue
        rebuilt=compile_expression(source['source'],reference_order=source['reference_order'])
        if to_svg(rebuilt['shapes'])!=to_svg(source['shapes']):
            raise ValueError('Original compiler no longer reproduces the pinned drawing')
        chosen[family]=dict(statement=entry['statement'],drawing=rebuilt)
    return chosen


@lru_cache(maxsize=1)
def allowed_pairs():
    """Finite positions allowed by the stated radii, rails and pairing rules."""
    output=[];seen=set()
    for r in b.RADII:
        for s in b.RADII:
            if r>s:continue
            for ya in b.RAILS:
                for yb in b.RAILS:
                    if (b.near(r,b.LARGE) and ya!=b.PITCH) or (b.near(s,b.LARGE) and yb!=b.PITCH):continue
                    for distance in sorted({0.,r,s,r+s}):
                        if distance<abs(yb-ya)-b.EPS:continue
                        delta=math.sqrt(max(0.,distance**2-(yb-ya)**2))
                        for dx in sorted({-delta,delta}):
                            rings=[b.circle(0.,ya,r),b.circle(dx,yb,s)]
                            if not b.legal_pair(*rings):continue
                            options=[[]]
                            large=next((c for c in rings if b.near(c['r'],b.LARGE)),None)
                            if large:
                                options=[]
                                for mode,directions in [('radius',range(8)),('outer',(1,3,5,7))]:
                                    for direction in directions:
                                        n=b.nucleus(large['x'],large['y'],b.LARGE,None,direction,mode=mode)
                                        options.append([q for q in n['shapes'] if q['kind']=='line'])
                            legal=None
                            for strokes in options:
                                try:b.geometry_check(rings+strokes,[])
                                except ValueError:continue
                                legal=rings+strokes;break
                            if legal is None:continue
                            minx=min(c['x'] for c in rings)
                            signature=tuple(sorted((round(c['x']-minx,7),c['y'],round(c['r'],7)) for c in rings))
                            if signature in seen:continue
                            seen.add(signature)
                            geometry=read_geometry(legal);relation=geometry['relations'][0]['kind']
                            # nucleus emits concentric L/M, or same-rail offsets
                            # at the main radius; tangent satellites are separate.
                            tangent_emitted=(relation=='tangent' and
                                ((b.near(r,b.SMALL) and yb==b.PITCH) or
                                 (b.near(r,b.MEDIUM) and ((ya==b.PITCH and b.near(dx,b.PITCH)) or
                                                        (yb==b.PITCH and b.near(dx,-b.PITCH))))))
                            emitted=(tangent_emitted or (relation=='concentric' and b.near(r,b.MEDIUM) and b.near(s,b.LARGE))
                                     or (relation=='center_on_rim' and ya==yb and b.near(distance,s)))
                            output.append(dict(kind=relation,radii=[r,s],rails=[ya,yb],dx=dx,
                                directly_available_in_old_constructor=emitted,shapes=legal))
    return output


@lru_cache(maxsize=1)
def rejected_forms():
    from scripts.flow_circle import margin_glyph,ligature
    forms={'small-center-row-number':margin_glyph('digit',0)['shapes'],
           'two-center-directions':ligature('ask')['shapes'],
           'three-concentric-circles':ligature('description_type')['shapes']}
    results={}
    for name,shapes in forms.items():
        try:b.geometry_check(shapes,[])
        except ValueError as error:results[name]=str(error)
        else:raise ValueError('Expected original-rule violation missing: '+name)
    return results


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);cards=[]
    normal,collision,association=generator_witnesses()
    for row in normal:
        name=row['key']+'.svg';svg=to_svg(row['drawing']['shapes'])
        (OUT/name).write_text(svg,encoding='utf-8',newline='\n')
        cards.append('<section><h2>元生成器：通常文 '+row['key'].split('-')[-1]+'</h2>'+svg+'</section>')
    for family,row in regenerated_kant().items():
        name='kant-'+family+'.svg';svg=to_svg(row['drawing']['shapes'])
        (OUT/name).write_text(svg,encoding='utf-8',newline='\n')
        cards.append('<section><h2>元生成器：カント / '+html.escape(family)+'</h2>'+svg+'</section>')
    pair_cards=[]
    for i,row in enumerate(allowed_pairs()):
        status='旧コンストラクターの形族' if row['directly_available_in_old_constructor'] else '描画規則上は許容、旧コンストラクターには形族がない'
        pair_cards.append('<div>'+to_svg(row['shapes'])+'<small>'+row['kind']+'<br>'+status+'</small></div>')
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>kant-page生成規則と復号の調査</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1450px;padding:32px;margin:auto;color:#203438;background:#f7f6f1}section{background:white;padding:22px;margin:20px 0;overflow:auto}section svg{height:100px;min-width:100%;width:auto}.pairs{display:grid;grid-template-columns:repeat(5,1fr);gap:22px}.pairs svg{height:100px;width:100%}small{font-size:11px}h1{font-size:26px}h2{font-size:18px}</style>
<h1>kant-pageの生成規則から復号を組み直す</h1>
<p>これは新しい書体の確認候補ではなく、元の生成器と描画規則を調べるページです。以下の通常文とカント各文頭族は、画像を写す代わりにcontextual_opening_script.pyを呼んで生成しました。カントは保存された元出力と図形が一致しています。</p>
<p>元の40主張に含まれる円・線は、元の幾何検査を通し、付属の構文木や不可視辺を渡さずに読みます。円の接続を読めることと、語・構文を一意に復元できることは区別します。</p>
<p>同じ規則を満たす図形でも、元生成器ではrain(town)とrain(home)が同じになります。ここは公開された語の綴りへ接続し直す必要があります。固定した文頭ヘッダーを追加する方法は採用しません。</p>'''+''.join(cards)+'''
<h2>円の組合せ：規則が許す形と旧生成器の範囲</h2>
<p>サイズと三つの高さから決まる二円の配置を列挙し、元の幾何検査を通る実例を示します。大小円の中心と円周の関係を逆にした配置、中央段と上下段をまたぐ重なり、小円を含む同心円など、旧nucleus関数が生成しない許容形もあります。これは語義を割り当て終えた一覧ではありません。方向ごとの全接続組合せや無限の離隔距離の列挙でもありません。</p><div class="pairs">'''+''.join(pair_cards)+'</div></html>\n'
    (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')


def build_report():
    observed_rows=[observed(i) for i in range(len(source_entries()))]
    modes=Counter();relations=Counter();authored=Counter()
    for row in observed_rows:
        modes.update(c['center_kind'] for c in row['geometry']['circles'])
        relations.update(r['kind'] for r in row['geometry']['relations'])
        authored.update(row['authored_to_observed'])
    _,collision,association=generator_witnesses();pairs=allowed_pairs()
    pins=['concept/alphabet-concept.md','data/writing-freeze-v1.json',PROVENANCE,NORMAL,
        'scripts/kant_geometry_reader.py','scripts/check_kant_geometry_reader.py',
        'tests/test_kant_geometry_reader.py','docs/kant-generator-decoding-design.md',
        'scripts/contextual_opening_script.py','scripts/balanced_circle_script.py','scripts/circle_contact_script.py',
        'scripts/branch_circle_script.py','scripts/visible_syntax_geometry.py','scripts/visible_lexical_script.py',
        'scripts/flow_circle.py','docs/kant-page-script-v3.md','scripts/proof_kant_page_script_v3.py']
    return dict(schema='noema-kant-observable-geometry-1',version=VERSION,status='geometry-front-end-only',
        original_statements=len(observed_rows),circles=sum(len(r['geometry']['circles']) for r in observed_rows),
        center_modes=dict(modes),circle_relations=dict(relations),authored_to_observed=dict(authored),
        line_branches=sum(sum(v['degree']>=3 for v in r['geometry']['vertices']) for r in observed_rows),
        silent_candidate_count=sum(len(r['geometry']['silent_candidates']) for r in observed_rows),
        recovered_silent_seams=sum(len(r['seams']) for r in observed_rows),
        source_code_regeneration=list(regenerated_kant()),
        lexical_collision=collision,conjunction_association=association,
        rejected_previous_draft_forms=rejected_forms(),
        allowed_pair_placements=len(pairs),
        pair_placements_not_emitted_by_old_constructor=sum(not r['directly_available_in_old_constructor'] for r in pairs),
        pair_kinds=dict(Counter(r['kind'] for r in pairs)),
        semantics='No new meaning judgments; no claim of complete syntax/word decoding',
        next_dependencies=['Public word identity with contextual allographs','Observable argument order and scope',
            'Reversible fusion without hidden occurrence paths','Quotation and binding grammar','Framing without repeated headers'],
        limits=['Canonical published grid only; calibration and page continuation not implemented here',
            'Silent seam is one proposed ordered-component production, not arbitrary missing-line inference',
            'Pair inventory enumerates touching/nested placements; not every legal multi-node composition',
            'No visual candidate submitted for approval; both preceding candidates remain rejected'],
        source_sha256={p:sha(p) for p in pins})


if __name__=='__main__':
    prepare()
    print(json.dumps(dict(output=str(OUT),pairs=len(allowed_pairs()),original_statements=len(source_entries())),ensure_ascii=False))
