"""Reproducibly build the alphabet font and a raster proof from owned vector paths."""
import json
import math
from pathlib import Path
import re
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from noema.script import ALPHABET_SPEC, SCRIPT_START
from noema.semantics import ALPHABET


def polylines(path):
    stream = re.findall(r"[MLQ]|-?\d+(?:\.\d+)?", path)
    i, current, output = 0, [], []
    while i < len(stream):
        operation = stream[i]
        i += 1
        if operation == "M":
            if current:
                output.append(current)
            current = [(float(stream[i]), float(stream[i + 1]))]
            i += 2
        elif operation == "L":
            current.append((float(stream[i]), float(stream[i + 1])))
            i += 2
        elif operation == "Q":
            a = current[-1]
            b, c = (float(stream[i]), float(stream[i + 1])), (float(stream[i + 2]), float(stream[i + 3]))
            i += 4
            for n in range(1, 13):
                t = n / 12
                current.append(((1-t)**2*a[0] + 2*(1-t)*t*b[0] + t*t*c[0], (1-t)**2*a[1] + 2*(1-t)*t*b[1] + t*t*c[1]))
        else:
            raise ValueError("Unsupported glyph operation")
    if current:
        output.append(current)
    return output


def polygon(pen, points):
    # All overlapping contours have the same winding, so strokes form a union.
    area = sum(points[i][0]*points[(i+1)%len(points)][1] - points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    if area > 0:
        points = list(reversed(points))
    converted = [(round(x * 24), round((34 - y) * 24)) for x, y in points]
    pen.moveTo(converted[0])
    for point in converted[1:]:
        pen.lineTo(point)
    pen.closePath()


def glyph(path):
    pen = TTGlyphPen(None)
    radius = ALPHABET_SPEC["stroke_width"] / 2
    for line in polylines(path):
        for a, b in zip(line, line[1:]):
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = math.hypot(dx, dy)
            if not length:
                continue
            nx, ny = -dy/length*radius, dx/length*radius
            polygon(pen, [(a[0]+nx, a[1]+ny), (b[0]+nx, b[1]+ny), (b[0]-nx, b[1]-ny), (a[0]-nx, a[1]-ny)])
        for x, y in line:
            polygon(pen, [(x+radius*math.cos(i*math.pi/6), y+radius*math.sin(i*math.pi/6)) for i in range(12)])
    return pen.glyph()


def build(output="noema/resources/NoemaWritten.ttf"):
    builder = FontBuilder(1000, isTTF=True)
    order = [".notdef", "space"] + ["noema" + str(i) for i in range(32)]
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap({32: "space", **{SCRIPT_START+i: "noema"+str(i) for i in range(32)}})
    empty = TTGlyphPen(None).glyph()
    shapes = {".notdef": glyph("M5 5 L28 5 L28 30 L5 30 L5 5 M5 5 L28 30"), "space": empty}
    shapes.update({"noema"+str(i): glyph(path) for i, path in enumerate(ALPHABET_SPEC["paths"])})
    builder.setupGlyf(shapes)
    builder.setupHorizontalMetrics({name: (816 if name != "space" else 400, 0) for name in order})
    builder.setupHorizontalHeader(ascent=860, descent=-140)
    builder.setupOS2(sTypoAscender=860, sTypoDescender=-140, usWinAscent=860, usWinDescent=140, achVendID="NOEM")
    builder.setupNameTable({"familyName": "Noema Written", "styleName": "Regular", "uniqueFontIdentifier": "NoemaWritten-1.0-draft",
                           "fullName": "Noema Written Regular", "psName": "NoemaWritten-Regular", "version": "Version 1.000"})
    builder.setupPost()
    builder.setupMaxp()
    # Fixed OpenType timestamps ensure byte-for-byte reproducible builds.
    builder.font["head"].created = builder.font["head"].modified = 3873312000
    builder.font.recalcTimestamp = False
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    builder.save(output)
    return output


def proof(font_path):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(font_path, 66)
    caption = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    canvas = Image.new("RGB", (864, 468), "#fbfaf4")
    draw = ImageDraw.Draw(canvas)
    rasters = []
    for i, letter in enumerate(ALPHABET):
        x, y = 18+(i%8)*106, 12+(i//8)*112
        draw.text((x, y), chr(SCRIPT_START+i), font=font, fill="#162736")
        draw.text((x+24, y+74), letter, font=caption, fill="#162736")
        sample = Image.new("L", (32, 36), 0)
        ImageDraw.Draw(sample).text((0, 0), chr(SCRIPT_START+i), font=ImageFont.truetype(font_path, 36), fill=255)
        rasters.append(set(j for j, value in enumerate(sample.tobytes()) if value > 64))
    pairs = []
    for i in range(32):
        for j in range(i+1, 32):
            similarity = len(rasters[i] & rasters[j]) / len(rasters[i] | rasters[j])
            pairs.append({"a": ALPHABET[i], "b": ALPHABET[j], "pixel_iou": similarity})
    directory = Path("output/alphabet")
    directory.mkdir(parents=True, exist_ok=True)
    canvas.save(directory / "font-proof.png")
    return {"distinct_rasters": len({frozenset(r) for r in rasters}), "most_similar_pairs": sorted(pairs, key=lambda p: -p["pixel_iou"])[:10],
            "limitation": "Raster overlap measures geometric similarity; it is not a human legibility test."}


if __name__ == "__main__":
    output = build()
    report = proof(output)
    Path("reports/alphabet-proof.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(report)
