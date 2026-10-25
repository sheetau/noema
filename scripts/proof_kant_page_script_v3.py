"""The same four-paragraph page with syntax-sensitive v10 openings."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from noema.constructed import parse
from scripts.contextual_opening_script import compile_expression, pack_lines, STROKE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/kant-page-script-v3'
DOCUMENT = 'examples/v016/kant-reviewed-complete-v1.noema'
ASSEMBLY = 'data/reviewed-works-assembly-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
UNITS = tuple(f'kant-1784:u{i:04d}' for i in range(8, 12))
ENGLISH = 'data/kant-page-english-v2.json'
WIDTH, HEIGHT, MARGIN = 1600, 2263, 90
INK, BACKGROUND, SS = '#203438', '#fffffe', 2


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def translate_shape(shape, dx):
    out = dict(shape)
    for key in ('x', 'x1', 'x2'):
        if key in out:
            out[key] += dx
    return out


def paragraph_view(entries):
    """Juxtapose intact assertions with sentence gaps, without merging their ASTs."""
    shapes, groups, offset = [], [], 0.
    for entry in entries:
        c = entry['compiled']
        entry['paragraph_offset'] = offset
        shapes.extend(translate_shape(s, offset) for s in c['shapes'])
        groups.extend(dict(left=g['left'] + offset, right=g['right'] + offset,
                           stacked=g['stacked']) for g in c['groups'])
        offset += c['width'] + 40
    return dict(shapes=shapes, groups=groups, width=offset - 40)


@lru_cache(maxsize=1)
def page_data():
    document = parse((ROOT / DOCUMENT).read_text(encoding='utf-8'))
    declarations = {d['name']: d for d in document['declarations']}
    registry = {d['name']: i for i, d in enumerate(document['declarations'])}
    assembly = read_json(ASSEMBLY)['works']['kant-1784']
    assert assembly['document'] == DOCUMENT
    inventory = {u['id']: u for u in read_json(INVENTORY)['units']}
    selections = {u['unit']: u for u in assembly['units']}
    paragraphs = []
    for unit in UNITS:
        selection, source = selections[unit], inventory[unit]
        assert source['text_sha256'] == selection['source_unit_sha256']
        entries = []
        for index in selection['statements']:
            original = document['statements'][index]
            display = deepcopy(original)
            body = display['body']
            expanded = None
            # Same display policy as proof_balanced_circle_script: expand only
            # the asserted zero-argument head. No rewrites inside quotations.
            if body['kind'] == 'call' and not body['arguments']:
                declaration = declarations[body['symbol']]
                if declaration['kind'] == 'definition' and not declaration['parameters']:
                    expanded = body['symbol']
                    display['body'] = deepcopy(declaration['body'])
            entries.append(dict(statement=index, original=deepcopy(original),
                                expanded_definition=expanded,
                                compiled=compile_expression(display, reference_order=registry)))
        paragraphs.append(dict(unit=unit, source_text=source['text'],
                               source_sha256=source['text_sha256'], review=selection['review'],
                               entries=entries, view=paragraph_view(entries)))
    # Maximize readable scale within a portrait page, with stable three-rail
    # line spacing. Sentence gaps are legal breaks; paragraph breaks are larger.
    for hundredths in range(120, 39, -1):
        scale = hundredths / 100
        rows = [pack_lines(p['view'], WIDTH - 2 * MARGIN, scale) for p in paragraphs]
        pitch = 210 * scale
        height = sum(len(r) for r in rows) * pitch + (len(paragraphs)-1) * 28 * scale
        if height <= HEIGHT - 2 * MARGIN:
            break
    else:
        raise ValueError('Page cannot fit at the minimum readable scale')
    y = MARGIN + 30 * scale
    for paragraph, lines in zip(paragraphs, rows):
        paragraph['rows'] = [dict(row, x=MARGIN, y=y + i * pitch) for i, row in enumerate(lines)]
        y += len(lines) * pitch + 28 * scale
    return dict(version='kant-page-script-v3', document=DOCUMENT,
                paragraphs=paragraphs, width=WIDTH, height=HEIGHT, scale=scale,
                source_word_count=sum(len(p['source_text'].split()) for p in paragraphs),
                limits=['Registered assertions with dictionary references, not full definition expansion.',
                        'The v9 script does not yet support independent optical decoding.'])


def prepare():
    data = page_data()
    OUT.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (WIDTH * SS, HEIGHT * SS), BACKGROUND)
    draw = ImageDraw.Draw(image)
    elements = []
    scale = data['scale']
    pen = STROKE * scale
    for paragraph in data['paragraphs']:
        for row in paragraph['rows']:
            x, y = row['x'], row['y']
            for s in row['shapes']:
                if s['kind'] == 'circle':
                    cx, cy, r = x+s['x']*scale, y+s['y']*scale, s['r']*scale
                    bound = r + pen / 2
                    draw.ellipse(tuple(round(v*SS) for v in (cx-bound, cy-bound, cx+bound, cy+bound)),
                                 outline=INK, width=max(1, round(pen*SS)))
                    elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')
                else:
                    a = (x+s['x1']*scale, y+s['y1']*scale)
                    b = (x+s['x2']*scale, y+s['y2']*scale)
                    draw.line([tuple(round(v*SS) for v in point) for point in (a, b)],
                              fill=INK, width=max(1, round(pen*SS)))
                    elements.append(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]}"/>')
    image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(OUT / 'kant-page.png')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
           f'viewBox="0 0 {WIDTH} {HEIGHT}"><rect width="100%" height="100%" fill="{BACKGROUND}"/>'
           f'<g stroke="{INK}" stroke-width="{pen}" fill="none">' + ''.join(elements) + '</g></svg>\n')
    (OUT / 'kant-page.svg').write_text(svg, encoding='utf-8', newline='\n')
    (OUT / 'provenance.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',
                                        encoding='utf-8', newline='\n')
    prepare_english()


@lru_cache(maxsize=1)
def english_layout():
    source = read_json(ENGLISH)
    assert tuple(p['unit'] for p in source['paragraphs']) == UNITS
    for size in range(46, 19, -1):
        font = ImageFont.truetype('C:/Windows/Fonts/times.ttf', size*SS)
        paragraphs = []
        for paragraph in source['paragraphs']:
            lines, current = [], ''
            for word in paragraph['text'].split():
                candidate = (current+' '+word).strip()
                if font.getlength(candidate) > (WIDTH-2*MARGIN)*SS and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
            paragraphs.append(lines)
        pitch = round(size*1.48)
        if sum(map(len, paragraphs))*pitch + (len(paragraphs)-1)*pitch <= HEIGHT-2*MARGIN:
            break
    else:
        raise ValueError('English text cannot fit')
    return dict(paragraphs=paragraphs, font_size=size, pitch=pitch)


def prepare_english():
    layout = english_layout()
    image = Image.new('RGB', (WIDTH*SS, HEIGHT*SS), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/times.ttf', layout['font_size']*SS)
    y = MARGIN
    for paragraph in layout['paragraphs']:
        for line in paragraph:
            draw.text((MARGIN*SS, y*SS), line, font=font, fill=INK, anchor='lt')
            y += layout['pitch']
        y += layout['pitch']
    image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(OUT/'kant-page-english.png')


def build_report():
    data = page_data()
    inputs = [DOCUMENT, ASSEMBLY, INVENTORY, ENGLISH, 'scripts/proof_kant_page_script_v3.py',
              'scripts/contextual_opening_script.py', 'scripts/balanced_circle_script.py', 'scripts/branch_circle_script.py',
              'scripts/circle_contact_script.py', 'tests/test_kant_page_script_v3.py',
              'docs/kant-page-script-v3.md', 'scripts/proof_kant_page_script.py',
              'examples/v016/branch-circle-samples.noema']
    inputs += [p['review'] for p in data['paragraphs']]
    digest = lambda path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    return dict(version=data['version'], source_word_count=data['source_word_count'],
                units=[dict(unit=p['unit'], statements=[e['statement'] for e in p['entries']],
                            rows=len(p['rows'])) for p in data['paragraphs']],
                page=dict(width=WIDTH, height=HEIGHT, scale=data['scale']), limits=data['limits'],
                openings=[dict(statement=e['statement'], **e['compiled']['opening'],
                               actual_ray=e['compiled']['groups'][0]['ray'])
                          for p in data['paragraphs'] for e in p['entries']],
                english=dict(source=ENGLISH, layout=english_layout()),
                source_sha256={p: digest(p) for p in inputs},
                output_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): digest(p)
                               for p in [OUT/'kant-page.png', OUT/'kant-page.svg', OUT/'provenance.json',
                                         OUT/'kant-page-english.png']})


if __name__ == '__main__':
    prepare()
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
