"""Export the component chart and measure rendered, unclipped glyph distinctions."""
import json
from pathlib import Path
from noema.script import SPECS, alphabet_metadata
from noema.semantics import ALPHABET
from noema.render import functional_alphabet_svg as chart


def measure(font_path, alphabet="v2"):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, __version__
    spec = SPECS[alphabet]
    reports = {}
    for size in (16, 24, 36):
        font = ImageFont.truetype(str(font_path), size)
        ascent, descent = font.getmetrics()
        for blur in (0, .6):
            rasters = []
            for i in range(32):
                canvas = Image.new("L", (size + 12, ascent + descent + 12), 0)
                ImageDraw.Draw(canvas).text((6, 6 + ascent), chr(spec["unicode_start"] + i), font=font, fill=255, anchor="ls")
                require_box = canvas.getbbox()
                assert require_box and require_box[0] > 0 and require_box[1] > 0 and require_box[2] < canvas.width and require_box[3] < canvas.height
                if blur:
                    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
                rasters.append(frozenset(j for j, value in enumerate(canvas.tobytes()) if value > 64))
            pairs = [{"a": ALPHABET[i], "b": ALPHABET[j], "iou": len(rasters[i] & rasters[j]) / len(rasters[i] | rasters[j])}
                     for i in range(32) for j in range(i + 1, 32)]
            reports[f"px{size}:blur{blur}"] = {"distinct": len(set(rasters)), "nonempty": all(rasters),
                                                   "closest_pairs": sorted(pairs, key=lambda p: -p["iou"])[:8]}
    return {"alphabet": spec["version"], "metadata": alphabet_metadata(alphabet), "pillow": __version__, "measures": reports,
            "limitation": "Distinct pixels and overlap scores are rendering checks, not evidence of human recognition, handwriting or learning speed."}


if __name__ == "__main__":
    Path("examples/alphabet-v2.svg").write_text(chart(), encoding="utf-8", newline="\n")
    report = measure("noema/resources/NoemaWritten.ttf")
    report["legacy"] = measure("noema/resources/NoemaWritten.ttf", "v1")
    Path("reports/alphabet-v2-proof.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
