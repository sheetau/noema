# Noema

**English** · [日本語](README.ja.md)

Noema is a constructed language for expressing meaning explicitly, with a writing system made of connected circles, arcs, lines, and dots. It combines typed expressions with definitions, quantification, quotation, questions, and discourse. Its circular writing represents those structures and can be decoded back into the same normalized syntax.

The aim is a language with the semantic range of natural language: a way to describe everyday situations, mathematics, beliefs, hypothetical worlds, and unfamiliar concepts through composition. Noema 1.0 fixes the language and its adopted writing system under that scope. It does not include an automatic translator or a universal procedure for deciding whether a statement is true.

## What makes Noema distinctive?

- **Scope and roles are explicit.** “Everyone read a book” can mean a different book for each person or one book shared by everyone. Noema records that choice and the order of a relation's arguments.
- **Concepts can be composed and reused.** Definitions build on existing meanings. A new empirical relation still needs a stated interpretation; a type declaration alone does not explain it.
- **Contents and their descriptions stay distinct.** An object, a belief about it, and a quotation describing it need not collapse into the same thing. Quoting a request does not issue it.
- **The writing follows the structure.** Branches, scoped sharing, repetition marks, and distant dot pairs can abbreviate expressions without changing their bindings or argument order. Sentences do not all follow one visual template.

For example, “a person is designing a house that does not yet exist” can retain the house's description without asserting its actual existence. “Its value is unknown” can be distinguished from “no value exists.” See the [language guide](docs/guide/language.md) for these distinctions and the native notation.

## Try it

Use Python 3.11 or later. The parser needs no model download, API key, or third-party runtime dependency. Run these commands from the repository root:

```sh
python -X utf8 -m noema.constructed parse -i examples/intro/scope.noema
python -X utf8 -m noema.constructed format -i examples/intro/scope.noema --notation full
```

The first command returns a typed, normalized JSON document; the second prints its full textual notation. Neither evaluates the truth of the statements. The [getting-started guide](docs/guide/getting-started.md) explains the example, installation, and the distinction between the text CLI and the adopted circle writing.

## Read more

| Guide | Contents |
| --- | --- |
| [Language](docs/guide/language.md) | Types, syntax, scope, quotation, and semantic distinctions |
| [Circle writing](docs/guide/writing.md) | Geometry, connections, branching, sharing, and visible decoding |
| [Vocabulary](docs/guide/vocabulary.md) · [Dictionary](docs/dictionary/index.html) | English/Japanese meanings, argument roles, conventions, and how to introduce a concept |
| [Works and examples](docs/guide/works.md) | Kant, Einstein, cross-domain examples, and available files |
| [Evidence and scope](docs/guide/evidence.md) | What 1.0 establishes and what each kind of check means |
| [Contributing](CONTRIBUTING.md) | Development, focused checks, and preserving evidence |

The repository includes complete Noema manuscripts for Kant's *An Answer to the Question: What Is Enlightenment?* and Einstein's *On the Electrodynamics of Moving Bodies*, under explicitly recorded readings. A shared catalog contains 1,952 entries. The manuscripts, dictionary data, and evidence are tracked here; the large rendered reading editions are separate local artifacts. [Availability and reading instructions](docs/guide/works.md) explain the distinction.

The [documentation index](docs/README.md) is the entry to current reader documentation. Older specifications and review records remain available as historical evidence; their progress reports describe the state at the time they were written.
