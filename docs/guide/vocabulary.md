# Vocabulary and definitions

**English** · [日本語](../ja/vocabulary.md) · [Documentation](../README.md)

The [1.0 shared catalog](../../data/general-language-catalog-v2.json) contains 1,952 entries: 1,489 primitive declarations and 463 composed definitions. It combines the earlier 1,909-entry catalog with 43 semantic-boundary definitions. Entry counts measure the catalog's contents, not the language's expressive power.

| Portability class | Entries | How to use it |
| --- | ---: | --- |
| Shared core | 375 | Preserve meaning, types, ordered roles, and context |
| Shared extensions | 62 | Reuse the composed probability, interpretation, and semantic-boundary constructions |
| Domain contracts | 1,488 | Retain required units, scales, institutions, comparison domains, or other conditions |
| Source selectors | 27 | Identify objects in fixed examples; do not reuse their referents as general concepts |

## Read an entry

The catalog's `entries` object maps a name to its declaration, spelling, meaning, and provenance. Useful fields include:

| Field | Contents |
| --- | --- |
| `declaration` | Primitive signature or definition body, with typed parameters and result |
| `spelling`, `symbol` | Root spelling and native symbol |
| `meaning`, `roles` | Meaning and ordered argument roles |
| `context`, `contrast` | Conditions that matter and distinctions to preserve |
| `sources` | Source files supporting the entry |
| `portability`, `usage` | Reuse category and constraints |

Meaning and role descriptions in the fixed catalog are **Japanese source records**. This English guide explains how to use them; it does not silently replace them with newly translated semantic contracts. The same applies to historical review data. Machine-readable names, types, and definitions retain their original forms in both language versions of the documentation.

For example, `above` is a primitive with two individual arguments and a truth-valued result. Its contract says that the first object is above the second along a specified spatial vertical axis and comparison method. It does not imply contact, support, or superiority in rank. Position and time belong to its context. Swapping the arguments changes the meaning even though their types are identical.

Inspect this entry without loading any model or ledger:

```python
import json
from pathlib import Path

catalog = json.loads(Path("data/general-language-catalog-v2.json").read_text(encoding="utf-8"))
entry = catalog["entries"]["above"]
print(entry["declaration"])
print(entry["meaning"])
print(entry["roles"])
```

## Introduce a concept

1. Identify the objects, situations, ordered roles, and types the concept needs.
2. Find existing definitions and preserve their conditions when composing them.
3. Write the composable part as a Noema definition. Explain any remaining empirical relation or cultural convention: what it accepts, what it excludes, and its context.
4. Check a small contrasting case. Exchanging a participant, time, description, or scope should change the result when the intended meaning changes.

A new institution may need participants, roles, qualifying procedures, obligations, and time. A sensation may need an experiencer and conditions for distinguishing the experience; it need not be reduced to a physical quantity. A new name alone explains neither.

Do not introduce a primitive that simply recognizes the conclusion of one source sentence. Do not store the original sentence as a quoted string and count that as a semantic composition. Definitions should be reusable with the same meanings in another statement.

## Common compositions

**Probability.** The finite probability construction uses a duplicate-free sequence of cases, nonnegative rational weights, and a total weight of one. Event probability sums the weights of cases meeting the condition. Conditional probability requires a positive conditioning weight; zero does not supply a default answer. Unknown inputs are rejected. Infinite distributions require explicit additional measure conditions rather than pretending a finite sample is exhaustive. See the [probability basis](../../data/general-probability-basis-v1.json) and [contrasting examples](../../data/general-probability-contrasts-v1.json).

**Interpretation and social acts.** Metaphor can retain source and target features, the mapping, the literal description, the intended description, and the grounds for that reading. Irony need not mean simply negating a false literal statement. Thanks, promises, advice, and institutional declarations connect a particular act to participants, content, conventions, and conditions; the three basic message forces do not by themselves determine social success. See the [pragmatics basis](../../data/general-pragmatics-basis-v1.json).

**Existence and information.** `actualtargetwitness` combines a described property with actuality in the same situation. The `uniquevalue…` and `missingvalue…` families retain applicability and completeness conditions; listed variants handle finite candidate sequences. `reportedsupport` preserves source-attributed support, and `valueconflict…` also requires the relevant single-value condition. These are different constructions, not interchangeable labels for “unknown.” See the [boundary definitions](../../data/semantic-boundaries-basis-v1.json).

**Bound contents.** A closed content-function description can be paired with typed argument values using the `boundcontent…` construction. Only `boundcontentholds…` evaluates the function at those values and the specified situation. The construction generalizes to finite typed argument lists without capturing free variables inside quotation.

The [language guide](language.md) explains the underlying scope and type rules. The [evidence guide](evidence.md) distinguishes checking these constructions from reviewing the meaning of a new translation.
