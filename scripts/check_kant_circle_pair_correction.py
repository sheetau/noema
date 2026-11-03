"""Reject eccentric containment and refresh affected current specimens."""
from pathlib import Path
import hashlib

from scripts.kant_geometry_rules import VERSION, geometry_check
from scripts.kant_public_fragment import forms, table
from scripts.check_kant_geometry_reader import allowed_pairs, observed, prepare as geometry_prepare
from scripts.check_kant_public_fragment import checked as public_checked, cases as public_cases, prepare as public_prepare
from scripts.check_kant_shared_argument import checked as shared_checked, cases as shared_cases, prepare as shared_prepare
from scripts.kant_public_lexicon import source_paths

ROOT = Path(__file__).resolve().parents[1]


def forbidden_shapes():
    from scripts.balanced_circle_script import SMALL, MEDIUM, LARGE, circle, nucleus
    result = {}
    for name, larger, smaller in [('medium-small',MEDIUM,SMALL),('large-small',LARGE,SMALL),('large-medium',LARGE,MEDIUM)]:
        for sign in (-1,1):
            # Add a legal large-circle stroke facing away from the companion.
            base = nucleus(0,32,larger,None,4 if sign==1 else 0)['shapes'] if larger==LARGE else [circle(0,32,larger)]
            result[name+('-left' if sign==-1 else '-right')] = base+[circle(sign*smaller,32,smaller)]
    return result


def paint_rows(rows, path, *, columns=1):
    from PIL import Image, ImageDraw, ImageFont
    width, row_height = 1600, 200
    im = Image.new('RGB',(width,row_height*len(rows)),'#fffffe')
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    cell = width/columns
    for index, variants in enumerate(rows):
        scale = min(1.,(cell-60)/max(r['compiled']['width'] for r in variants))
        for col,row in enumerate(variants):
            x,y=col*cell+24,index*row_height+80
            label=row.get('key',str(index))+(' / shared' if columns==2 and col==0 else ' / explicit' if columns==2 else '')
            draw.text((x,index*row_height+20),label,font=font,fill='#203438')
            for s in row['compiled']['shapes']:
                if s['kind']=='circle':
                    cx,cy,r=x+s['x']*scale,y+s['y']*scale,s['r']*scale
                    draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline='#203438',width=2)
                else:
                    draw.line((x+s['x1']*scale,y+s['y1']*scale,x+s['x2']*scale,y+s['y2']*scale),fill='#203438',width=2)
    im.save(path)


def prepare():
    # These are the three affected current views, not the frozen Kant page.
    geometry_prepare()
    public_prepare()
    shared_prepare()
    paint_rows([[shared_checked(i),shared_checked(i,False)] for i in (0,3,8,9,10)],
               ROOT/'output/kant-shared-argument/inspection.png',columns=2)
    paint_rows([[public_checked(i)] for i in (7,8,9,10,18,22)],
               ROOT/'output/kant-public-fragment/inspection.png')


def build_report():
    rejected={}
    for key,shapes in forbidden_shapes().items():
        try:geometry_check(shapes,[])
        except ValueError as error:rejected[key]=str(error)
        else:raise ValueError('Forbidden eccentric pair accepted: '+key)
    pairs=allowed_pairs()
    original=[observed(i) for i in range(40)]
    public=[public_checked(i,b) for i in range(len(public_cases())) for b in (True,False)]
    shared=[shared_checked(i,s) for i in range(len(shared_cases())) for s in (True,False)]
    pins=set(source_paths())|{
        'scripts/kant_geometry_rules.py','scripts/kant_geometry_reader.py','scripts/kant_public_fragment.py',
        'scripts/check_kant_circle_pair_correction.py','tests/test_kant_circle_pair_correction.py',
        'scripts/check_kant_geometry_reader.py','tests/test_kant_geometry_reader.py',
        'scripts/check_kant_public_fragment.py','tests/test_kant_public_fragment.py',
        'scripts/check_kant_shared_argument.py','tests/test_kant_shared_argument.py',
        'scripts/check_kant_public_words.py','scripts/check_visible_syntax.py',
        'scripts/kant_flow_reader.py','scripts/kant_readable_flow.py',
        'scripts/balanced_circle_script.py','scripts/branch_circle_script.py','scripts/circle_contact_script.py',
        'scripts/visible_syntax_geometry.py','docs/kant-circle-pair-rule.md',
        'docs/kant-generator-decoding-design.md','docs/kant-shared-argument.md',
        'concept/alphabet-concept.md','data/writing-freeze-v1.json',
        'output/kant-page-script-v3/provenance.json'}
    return dict(schema='kant-circle-pair-correction-1',version=VERSION,
        corrected_rule='For nonconcentric overlaps, the smaller center must lie on the larger rim',
        withdrawn_forms=['and/reverse-right','or/reverse-left','implies/reverse-right','and_shared/reverse-left'],
        rejected_eccentric_pairs=rejected,allowed_pair_placements=len(pairs),
        not_directly_emitted_by_old_constructor=sum(not p['directly_available_in_old_constructor'] for p in pairs),
        original_kant_statements_still_legal=len(original),public_shapes=len(table()),
        public_syntax_roundtrips=len(public),shared_syntax_roundtrips=len(shared),
        old_inventory_claim='41 included 10 forbidden placements; it is superseded, not evidence for current rules',
        limits=['Circle-pair correction only; the full R1 writing system remains unfinished',
                'Original frozen code and historical reports retained',
                'No changes to meanings, references, source manuscripts or semantic judgments'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(pins)})
