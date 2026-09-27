import argparse
import json
from pathlib import Path
import sys
from .grammar import parse, format_graph
from .render import render, alphabet_svg
from .semantics import SemanticError


def read_input(args):
    if args.input:
        return Path(args.input).read_text(encoding="utf-8-sig")
    if args.text is not None:
        return args.text
    return sys.stdin.read()


def emit(value, output=None):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)


def main(argv=None):
    # Explicit UTF-8 for Windows pipes as well as terminals.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="noema", description="Noema formal language and frozen-encoder experiment")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("parse", "format", "render", "analyze"):
        p = commands.add_parser(name)
        source = p.add_mutually_exclusive_group()
        source.add_argument("--text")
        source.add_argument("--input", "-i")
        p.add_argument("--output", "-o")
        if name == "format":
            p.add_argument("--edition", choices=("0.1", "0.2", "0.3", "0.4", "0.5", "0.6"), help="Explicit lossless conversion to another edition")
            p.add_argument("--notation", choices=("full", "compact"), default="full")
        if name == "render":
            p.add_argument("--columns", type=int, default=34)
            p.add_argument("--alphabet", choices=("v1", "v2"), default="v2")
            p.add_argument("--notation", choices=("full", "compact"), help="Default: preserve input notation")
        if name == "analyze":
            p.add_argument("--language", required=True)
            p.add_argument("--checkpoint")
            p.add_argument("--device", default="cpu")
            p.add_argument("--offline", action="store_true")
    p = commands.add_parser("alphabet")
    p.add_argument("--output", "-o")
    p.add_argument("--alphabet", choices=("v1", "v2"), default="v2")
    p = commands.add_parser("edit", help="Open the local writing desk server")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--checkpoint", help="Frozen analyzer checkpoint for the local translation page")
    p = commands.add_parser("script", help="Encode/decode the original alphabet's private-use characters")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--input", "-i")
    p.add_argument("--output", "-o")
    p.add_argument("--decode", action="store_true")
    p.add_argument("--alphabet", choices=("v1", "v2"), default="v2")
    p.add_argument("--notation", choices=("full", "compact"), help="Default: preserve input notation")
    p = commands.add_parser("dataset")
    p.add_argument("--edition", choices=("0.1", "0.2"), default="0.1")
    p.add_argument("--output", "-o", default="data/evaluation.jsonl")
    p.add_argument("--check", action="store_true")
    p = commands.add_parser("features")
    p.add_argument("--dataset", default="data/evaluation.jsonl")
    p.add_argument("--model", choices=("xlmr", "minilm"), default="xlmr")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--offline", action="store_true")
    p = commands.add_parser("train")
    p.add_argument("--dataset", default="data/evaluation.jsonl")
    p.add_argument("--features", required=True)
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--architecture", choices=("linear", "mlp"), default="linear")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--fraction", type=float, default=1.)
    p.add_argument("--threshold", type=float, default=.9)
    p.add_argument("--seed", type=int, default=17)
    args = parser.parse_args(argv)
    try:
        if args.command == "parse":
            emit(parse(read_input(args)), args.output)
        elif args.command == "format":
            graph = json.loads(read_input(args))
            if not isinstance(graph, dict):
                raise SemanticError("Meaning structure must be a JSON object")
            if args.edition and graph.get("schema_version") != args.edition:
                from .language import convert
                graph = convert(graph, args.edition)
            emit(format_graph(graph, args.notation), args.output)
        elif args.command == "render":
            emit(render(read_input(args), args.columns, args.alphabet, args.notation), args.output)
        elif args.command == "alphabet":
            emit(alphabet_svg(args.alphabet), args.output)
        elif args.command == "edit":
            from .editor import serve
            serve(args.port, args.checkpoint)
        elif args.command == "script":
            from .script import encode, decode
            emit(decode(read_input(args), args.notation) if args.decode else encode(read_input(args), args.alphabet, args.notation), args.output)
        elif args.command == "analyze":
            from .analyzer import Analyzer
            emit(Analyzer(args.checkpoint, args.device, args.offline).analyze(read_input(args), args.language), args.output)
        elif args.command == "dataset":
            from .dataset import load_dataset, validate_dataset, write_dataset
            if not args.check and args.edition == "0.2":
                from .corpus_v2 import write
                emit(write(args.output))
            else:
                rows = load_dataset(args.output) if args.check else write_dataset(args.output)
                if rows and rows[0].get("corpus_version") == "0.2":
                    from .corpus_v2 import validate
                    emit(validate(rows))
                else:
                    emit(validate_dataset(rows))
        elif args.command == "features":
            from .training import cache_features
            if args.batch_size < 1:
                raise ValueError("batch-size must be positive")
            emit(cache_features(args.dataset, args.output, args.model, args.device, args.batch_size, args.offline))
        elif args.command == "train":
            from .training import train
            report = train(args.dataset, args.features, args.output, args.architecture, args.epochs, args.fraction, args.threshold, args.seed)
            emit({"output": args.output, "test": report["test"]})
    except (ValueError, OSError, ImportError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0
