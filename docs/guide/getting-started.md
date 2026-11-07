# Getting started

**English** · [日本語](../ja/getting-started.md) · [Documentation](../README.md)

## Run from a checkout

Install Python 3.11 or later, clone the repository, and run commands from its root. Parsing and formatting use the standard library; they do not need a trained model, a network service, or the maintainer's database.

```sh
git clone https://github.com/sheetau/noema.git
cd noema
python -X utf8 -m noema.constructed parse -i examples/intro/scope.noema
python -X utf8 -m noema.constructed format -i examples/intro/scope.noema --notation full
```

An editable package installation is optional when working in the repository:

```sh
python -m pip install -e .
```

Use `python -m noema.constructed` for syntax 0.16, including description construction. The `noema` command and `python -m noema` are older entry points; they are not interchangeable with this module for every document. The syntax version is written in the document, independently of the language's release number.

## Read the example

The file [scope.noema](../../examples/intro/scope.noema) contains:

```text
p:
r aa[a a] c.
s[f x a[g y a[k aa[v x v y]]]].
s[g y a[f x a[k aa[v x v y]]]].
```

`p:` selects syntax 0.16. `r aa[a a] c.` declares a relation with two individual arguments and a truth-valued result. Its name is local to this example: the declaration supplies a type, not an empirical meaning.

`s[...]` asserts a proposition; `f` binds a universal variable and `g` an existential one. `k aa[...]` applies the relation, and `v x` uses a bound variable. The two statements say:

1. For every x, some y satisfies aa(x, y).
2. Some one y satisfies aa(x, y) for every x.

The difference is the scope of “some.” If the domain is two objects and aa means identity, the first statement is true and the second false. That is an illustrative interpretation, not a meaning assigned to `aa` throughout the dictionary. To express “every person read some book,” add the person and book conditions and a reading relation, as explained in the [language guide](language.md).

The JSON output preserves the quantifier order and references while normalizing bound names. A successful parse checks structure and types; it does not establish that an interpretation has been supplied or that either sentence is true.

## Save output and use the API

The CLI writes to a new file with `-o`. Choose a path that does not already exist; it refuses to overwrite one.

```sh
python -X utf8 -m noema.constructed parse -i examples/intro/scope.noema -o scope.json
python -X utf8 -m noema.constructed format -i examples/intro/scope.noema -o scope-formatted.noema
```

The Python API accepts textual Noema and returns the normalized document:

```python
from pathlib import Path
from noema.constructed import parse, format_graph

document = parse(Path("examples/intro/scope.noema").read_text(encoding="utf-8"))
text = format_graph(document, notation="compact")
assert parse(text) == document
```

This is a textual syntax round trip. It does not test graphical decoding.

## Text notation and circle writing

The compact letters and brackets are an editable serialization of Noema. The adopted circle writing has its own geometry and scoped abbreviations. The CLI's `--script` option and `render` operation use the legacy character font; their output is **not** the adopted connected circle edition.

See [circle writing](writing.md) for the current reader/encoder APIs and [works and examples](works.md) for the rendered editions. There is no single installed CLI command documented here for rebuilding the complete circle publications. Their production scripts operate on pinned sources and evidence; rebuilding them is unnecessary for trying the language.

Next, read the [language guide](language.md) and [vocabulary guide](vocabulary.md).
