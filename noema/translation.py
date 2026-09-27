"""Two-way UI adapter; keep uncertainty and translation limits explicit."""
from threading import Lock
from .grammar import parse, format_graph
from .language import convert
from .script import encode
from .semantics import require, SemanticError
from .verbalize import realize


class Translator:
    def __init__(self, checkpoint=None, analyzer=None):
        self.checkpoint, self.analyzer = checkpoint, analyzer
        self.lock = Lock()

    def translate(self, payload):
        require(isinstance(payload, dict), "Expected an object")
        text, language, direction = (payload.get(k) for k in ("text", "language", "direction"))
        require(isinstance(text, str) and text.strip(), "Enter text to translate")
        require(language in ("ja", "en"), "Choose Japanese or English")
        require(direction in ("to_noema", "from_noema"), "Unknown translation direction")
        if direction == "from_noema":
            graph = parse(text)
            try:
                output = realize(graph, language)
            except SemanticError as exc:
                return {"status": "unsupported", "text": None,
                        "message": "この構造の自然言語への変換は未対応です。", "reason": str(exc)}
            return {"status": "confirmed", "text": output, "method": "deterministic-realization",
                    "message": "Noemaの意味を定型文に変換しました。"}
        with self.lock:
            if self.analyzer is None:
                from .analyzer import Analyzer
                self.analyzer = Analyzer(self.checkpoint, offline=True)
            result = self.analyzer.analyze(text, language)
        if result["status"] != "confirmed":
            message = ("自然言語解析用のモデルが未設定です。" if result.get("diagnostics", {}).get("reason") == "checkpoint_required"
                       else "意味を確定できませんでした。入力が対応範囲外の場合もあります。")
            return {"status": result["status"], "text": None, "message": message}
        canonical = format_graph(convert(result["graph"], "0.4"))
        return {"status": "confirmed", "text": encode(canonical, "v2"), "canonical": canonical,
                "message": "Noemaに変換しました。試作のため誤解析の可能性があります。"}
