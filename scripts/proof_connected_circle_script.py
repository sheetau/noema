"""Reproducible specimens and a compact report for connected circle script 02."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scripts.connected_circle_script import VERSION, STROKE, compile_document, svg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/alphabet-circle-v2'
SOURCE = 'examples/v014/connected-circle-samples.noema'
PROFILE = 'data/connected-circle-reading-v2.json'
INK = '#182629'
ACCENT = '#377b78'
MUTED = '#617779'
SS = 3
JP = 'C:/Windows/Fonts/YuGothM.ttc'
LATIN = 'C:/Windows/Fonts/segoeui.ttf'


class Sheet:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.image = Image.new('RGB', (width * SS, height * SS), '#fffefd')
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, text, size=22, fill=INK, jp=True):
        self.draw.text((round(x * SS), round(y * SS)), text,
                       font=ImageFont.truetype(JP if jp else LATIN, size * SS), fill=fill)

    def line(self, points, fill='#dce5e3', width=1):
        self.draw.line([(round(x * SS), round(y * SS)) for x, y in points],
                       fill=fill, width=max(1, round(width * SS)))

    def contour(self, sentence, x, y, scale=1, fill=INK):
        for s in sentence['shapes']:
            if s['kind'] == 'line':
                self.line([(x + s['x1'] * scale, y + s['y1'] * scale),
                           (x + s['x2'] * scale, y + s['y2'] * scale)], fill, STROKE * scale)
            else:
                cx, cy, r = (x + s['x'] * scale) * SS, (y + s['y'] * scale) * SS, s['r'] * scale * SS
                self.draw.ellipse((round(cx-r), round(cy-r), round(cx+r), round(cy+r)),
                                  outline=fill, fill=fill if s['kind'] == 'dot' else None,
                                  width=max(1, round(STROKE * scale * SS)))

    def save(self, name):
        self.image.resize((self.width, self.height), Image.Resampling.LANCZOS).save(OUT / name)


@lru_cache(maxsize=1)
def result():
    return compile_document((ROOT / SOURCE).read_text(encoding='utf-8'),
                            json.loads((ROOT / PROFILE).read_text(encoding='utf-8')))


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    data = result()
    sentences = data['sentences']
    captions = data['profile']['captions']
    sheet = Sheet(1800, 2040)
    sheet.text(76, 38, 'NOEMA  /  CONNECTED CONTOURS  /  02', 19, ACCENT, False)
    sheet.text(72, 83, '語の形は、関係の中で生まれる。', 40)
    sheet.text(76, 148, '定義を合成し、共有部分を融合する。一本の文として接続してから、形を決める。', 23, MUTED)
    sheet.line([(76, 204), (1724, 204)])
    notes = [
        '二つの関係が、同じ主語・対象を共有する。',
        '同じ「信頼」でも、役割の反転で内部の向きと接続が変わる。',
        '否定の範囲は両端で示す。内部の各関係を別々に否定しない。',
        '「信頼」と「助ける」を合成。対象を繰り返さず、既存の接合部も変形する。',
        '中央の下降する経路が条件から帰結への接続。',
        '中央の分岐・合流が選言。条件文と異なる接続になる。',
    ]
    for i, (sentence, caption, note) in enumerate(zip(sentences[:6], captions, notes)):
        y = 235 + i * 270
        sheet.text(76, y, f'{i+1:02}', 19, ACCENT, False)
        sheet.text(130, y-3, caption, 26)
        # A common scale makes fusion and length directly comparable.
        sheet.contour(sentence, 85, y+76, 1)
        sheet.text(130, y+204, note, 20, MUTED)
        sheet.line([(76, y+246), (1724, y+246)])
    sheet.text(76, 1900, 'この試作の「信頼」＝肯定的な見込み ∧ 自分の選択を相手に依存させること。', 21, MUTED)
    sheet.text(76, 1939, '円は3サイズ。中心と横線は3段。線は縦・横・45度。文内のインクはすべて接続。', 20, MUTED)
    sheet.text(76, 1976, '文字や数字の置換表は使わない。語義は明示した規約を用い、綴りから推測しない。', 20, MUTED)
    sheet.save('sentences.png')

    sheet = Sheet(1800, 1520)
    sheet.text(76, 38, 'NOEMA  /  FUSION & SCOPE', 19, ACCENT, False)
    sheet.text(72, 83, 'どこが一文字かを、固定しない。', 40)
    sheet.text(76, 150, '一つの円・接合部を、複数の意味関係が共有する。隣の要素に合わせて出入口も変わる。', 22, MUTED)
    sheet.line([(76, 207), (1724, 207)])
    sheet.text(76, 237, 'A  /  二つの関係を一つの連結体へ', 26)
    base = sentences[0]
    sheet.contour(base, 100, 324, 1.4)
    bundle = base['bundles'][0]
    joint = base['nodes'][bundle['shared_joints'][0]]
    cx, cy = 100 + joint['x']*1.4, 324 + joint['y']*1.4
    sheet.line([(cx, cy+36), (cx, 490), (920, 490)], ACCENT, 1)
    sheet.text(948, 321, '左端：アキ（点の標識）', 23)
    sheet.text(948, 367, '右端：ナオ（小円の標識）', 23)
    sheet.text(948, 437, 'この接合部は、前の関係の出口と', 22, ACCENT)
    sheet.text(948, 474, '次の関係の入口を兼ねる。', 22, ACCENT)
    sheet.text(76, 535, '独立した「信頼」の字形は保存しない。定義・参加者・前後の接続から、その場で生成する。', 22, MUTED)
    sheet.line([(76, 596), (1724, 596)])
    sheet.text(76, 628, 'B  /  同じ要素でも、否定する範囲を変えると形が変わる', 26)
    sheet.text(96, 689, '¬（肯定的な見込み ∧ 依存）', 24)
    sheet.contour(sentences[2], 85, 753, 1)
    sheet.text(96, 906, '肯定的な見込み ∧ ¬ 依存', 24)
    sheet.contour(sentences[6], 85, 970, 1)
    sheet.text(96, 1124, '大円を通る斜線の対が否定の範囲。小円の内向きの腕が、入れ子になった範囲の両端。', 21, MUTED)
    sheet.line([(76, 1190), (1724, 1190)])
    sheet.text(76, 1227, '生成規則で増える形', 26)
    sheet.text(76, 1280, '意味の部品を増やす → 共有する対象をまとめる → 文の構造で配置を変える → 隣同士の経路を解く。', 22, MUTED)
    sheet.text(76, 1324, '複合と入れ子に、字形一覧としての上限は設けない。実装は機械の資源と現行構文の深さに制約される。', 21, MUTED)
    sheet.text(76, 1398, '試作範囲：二項関係・個体定数・通常の定義・連言・選言・条件・否定。', 21, MUTED)
    sheet.text(76, 1437, '引用・量化・数値などは未対応として拒否する。画像単独の一意な読解やOCRは、まだ検証していない。', 21, MUTED)
    sheet.save('fusion-and-scope.png')

    # A clean, connected writing sample, without explanations or guides.
    sheet = Sheet(1800, 680)
    for index, y in zip((0, 3, 4), (90, 280, 470)):
        sheet.contour(sentences[index], 90, y, 1)
    sheet.save('writing.png')
    for i in range(len(sentences)):
        (OUT / f'sentence-{i+1:02}.svg').write_text(svg(data, i), encoding='utf-8', newline='\n')
    (OUT / 'structure.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def build_report():
    data = result()
    inputs = [SOURCE, PROFILE, 'scripts/connected_circle_script.py',
              'scripts/proof_connected_circle_script.py', 'tests/test_connected_circle_script.py',
              'docs/connected-circle-script-v2.md']
    outputs = [OUT / n for n in ('sentences.png', 'fusion-and-scope.png', 'writing.png', 'structure.json')]
    outputs += [OUT / f'sentence-{i+1:02}.svg' for i in range(len(data['sentences']))]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(schema='noema-connected-circle-proof-2', renderer=VERSION,
                source_sha256={p: digest(ROOT / p) for p in inputs},
                output_sha256={p.relative_to(ROOT).as_posix(): digest(p) for p in outputs},
                sentences=[dict(nodes=len(s['nodes']), width=s['width'],
                                bundle_relations=[b['relations'] for b in s['bundles']],
                                participant_occurrences=sum(b['participant_occurrences'] for b in s['bundles']))
                           for s in data['sentences']],
                limits=['Explicit sample reading; not automatic semantic interpretation',
                        'Assertions with profiled binary relations/constants and four logical operators only',
                        'Source and semantic plan retained; no pixel-to-language decoding claim'])


if __name__ == '__main__':
    prepare()
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
