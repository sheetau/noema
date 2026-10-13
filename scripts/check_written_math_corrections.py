"""Retain raw source math and apply explicitly reviewed, hash-bound corrections."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from noema.grammar import parse, format_graph
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_real_products import MEANINGS, call as k, op, conjunction as both, assertion
from scripts.check_moving_light_trip import literal

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'data/written-math-corrections-v1.json'
REPORT=ROOT/'reports/written-math-corrections-v1.json'
DOCUMENT=ROOT/'examples/v014/source-formula-checks.noema'
NS='{http://www.w3.org/1998/Math/MathML}'
ET.register_namespace('',NS[1:-1])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply_correction(raw, correction):
    """Return a separate serialization; never mutate the snapshot or caller data."""
    if digest(raw.encode('utf-8'))!=correction['snapshot_math_sha256']:raise ValueError('Snapshot math hash differs')
    if correction.get('operation')!='outer_fraction_denominator_identifier':raise ValueError('Unknown correction operation')
    if correction.get('occurrences')!=1 or not correction.get('from') or not correction.get('to'):raise ValueError('Ambiguous correction specification')
    tree=ET.fromstring(raw);fraction=next(tree.iter(NS+'mfrac'),None)
    if fraction is None or len(fraction)!=2:raise ValueError('Expected outer fraction with two children')
    matches=[node for node in fraction[1].iter(NS+'mi') if node.text==correction['from']]
    if len(matches)!=1:raise ValueError('Correction target is missing or ambiguous')
    matches[0].text=correction['to']
    return ET.tostring(tree,encoding='unicode')


def reviewed_math():
    """Explicitly opt into the reviewed layer while retaining both representations."""
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'))
    path=ROOT/ledger['source_units'];artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if digest(path.read_bytes())!=inventory['works'][ledger['work']]['units_sha256']:raise ValueError('Pinned source inventory differs')
    image=ROOT/ledger['facsimile']['path'];data=image.read_bytes()
    if digest(data)!=ledger['facsimile']['sha256'] or len(data)!=ledger['facsimile']['bytes']:raise ValueError('Reviewed facsimile differs')
    rows={}
    for correction in ledger['corrections']:
        mid=correction['math_id']
        if mid in rows:raise ValueError('Duplicate correction for math object')
        if correction.get('review_status')!='token_checked_against_facsimile':raise ValueError('Correction has not been reviewed')
        item=next(m for m in artifact['math'] if m['id']==mid)
        if digest(item['mathml'].encode('utf-8'))!=item['sha256']:raise ValueError('Stored math digest differs')
        unit=next(u for u in artifact['units'] if u['id']==correction['unit'])
        if mid not in unit['math_ids'] or digest(unit['text'].encode('utf-8'))!=unit['text_sha256']:raise ValueError('Math object belongs to a different source unit')
        corrected=apply_correction(item['mathml'],correction)
        rows[mid]={'correction_id':correction['id'],'unit':correction['unit'],'snapshot_mathml':item['mathml'],
            'snapshot_math_sha256':item['sha256'],'reviewed_mathml':corrected,'reviewed_math_sha256':digest(corrected.encode('utf-8')),
            'review_status':correction['review_status']}
    return rows


def noema_checks():
    """Local algebraic comparisons, not a translation of the surrounding section."""
    v=lambda name:'v '+name
    V,s,w,p,q,n,U=map(v,('light','speed','moving','cosine','sine','radical','result'))
    zero=literal(0);one=literal(1);two=literal(2)
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sq=lambda x:mul(x,x)
    sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b);nonzero=lambda x:op('u',eq(x,zero))
    numerator=sub(mul(sq(V),add(add(sq(s),sq(w)),mul(two,mul(mul(s,w),p)))),mul(mul(sq(s),sq(w)),sq(q)))
    text='n:\nr aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.\n'
    root=both(k('aa',zero,V),op('u',k('aa',n,zero)),eq(add(sq(p),sq(q)),one),eq(mul(sq(V),sq(n)),numerator))
    text+='d ba[light b speed b moving b cosine b sine b radical b] c['+root+'].\n'
    for name,angle in (('bb',p),('bc',q)):
        D=add(sq(V),mul(mul(s,w),angle))
        text+='d '+name+'[light b speed b moving b cosine b sine b radical b result b] c['+both(k('ba',V,s,w,p,q,n),nonzero(D),eq(mul(D,U),mul(sq(V),n)))+'].\n'
    d=v('denominator')
    text+='d bd[light b moving b denominator b result b] c['+both(k('aa',zero,V),k('aa',zero,d),nonzero(add(d,w)),eq(mul(add(d,w),U),mul(d,add(V,w))))+'].\n'
    args=[literal(x) for x in (5,3,1,1,0,4)]
    claims={
        'parallel_case_facsimile_value':assertion('',k('bb',*args,literal(Fraction(25,7)))),
        'parallel_case_snapshot_has_same_value':assertion('',k('bc',*args,literal(Fraction(25,7)))),
        'parallel_case_snapshot_value':assertion('',k('bc',*args,literal(4))),
        'zero_motion_masks_sin_cos_error':assertion('',both(k('bb',*(literal(x) for x in (5,0,1,1,0,1,1))),k('bc',*(literal(x) for x in (5,0,1,1,0,1,1))))),
        'reviewed_light_case_preserves_light_speed':assertion('light moving',op('y',both(k('aa',zero,V),op('u',k('aa',w,zero))),k('bd',V,w,V,V))),
        'reviewed_light_case_result_is_unique':assertion('light moving result',op('y',k('bd',V,w,V,U),eq(U,V))),
        'snapshot_lowercase_speed_preserves_light_speed':assertion('',k('bd',literal(5),literal(1),literal(3),literal(5))),
        'snapshot_lowercase_speed_value':assertion('',k('bd',literal(5),literal(1),literal(3),literal(Fraction(9,2)))),
        'zero_added_speed_masks_case_error':assertion('light denominator',op('y',both(k('aa',zero,V),k('aa',zero,d)),k('bd',V,zero,d,V))),
    }
    doc=parse(text+''.join(claims.values()));canonical=format_graph(doc,'compact')+'\n'
    results=verify_universal(doc,MEANINGS,timeout_ms=15000)
    rejected={'parallel_case_snapshot_has_same_value','snapshot_lowercase_speed_preserves_light_speed'}
    rows=dict(zip(claims,results,strict=True))
    for name,result in rows.items():
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Source-variant algebra differs: '+name)
    for notation in ('full','compact'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Source formula check roundtrip differs')
    return canonical,{'claims':rows,'interpretations':MEANINGS,'scope':'Rational polynomial comparisons at specified directions; no general angle or surrounding prose translation'}


def build_report(*, write_document=False):
    rows=reviewed_math();text,algebra=noema_checks()
    if write_document and not DOCUMENT.exists():
        with DOCUMENT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    if DOCUMENT.read_text(encoding='utf-8')!=text:raise ValueError('Stored formula checks differ')
    paths=['data/written-math-corrections-v1.json','artifacts/written-facsimiles-v1/einstein-1905-p906.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','examples/v014/source-formula-checks.noema',
        'scripts/check_written_math_corrections.py','noema/polynomial_proofs.py','noema/discourse.py']
    return {'status':'two_facsimile_checked_transcription_tokens','reviewed_math':rows,'algebra':algebra,
        'scope':{'whole_page_reviewed':False,'whole_formula_semantics_verified':False,'new_semantically_verified_units':0,
            'source_snapshot_modified':False,'new_translation_alignment_claimed':False},
        'source_sha256':{name:digest((ROOT/name).read_bytes()) for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report(write_document=not args.verify_only)
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Written math review differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Two source transcription corrections and nine Noema algebra checks verified')


if __name__=='__main__':main()
