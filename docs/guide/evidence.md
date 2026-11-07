# Evidence and completion scope

**English** · [日本語](../ja/evidence.md) · [Documentation](../README.md)

Noema 1.0 was fixed on 2026-11-05. Its completion scope is the expression of explicit meanings through typed composition, extensible vocabulary, preserved scope, and decodable circle writing. The project's completion judgment is that these principles and the examined distinctions provide the intended semantic range of natural language. It is not an exhaustive proof over every possible natural-language sentence.

The [release manifest](../../data/language-release-v1.json) selects the baseline. The language edition number 1.0 does not replace syntax versions 0.14, 0.15, and 0.16. These guides reorganize the public explanation; the sealed edition and its evidence remain fixed.

## Three different questions

| Question | Evidence | What it does not establish |
| --- | --- | --- |
| Does the Noema statement retain the intended source meaning? | Itemwise judgments with explicit readings, meaning contracts, references, and contrasting cases | Independent peer review or automatic equivalence proof |
| Did a structural conversion preserve the statement? | Exact normalized syntax, bindings, unchanged meanings, and reference identities | A new semantic judgment about a changed statement |
| Can the visible writing be read back? | Recovery from actual SVG geometry with the public dictionary, compared to the checked syntax | OCR for arbitrary images or handwriting; semantic correctness by appearance alone |

Parsing, type checking, and finite-model diagnostics support particular claims within these layers. They are not interchangeable. If recovered syntax, meanings, and referents are unchanged, existing source judgments can carry forward. If a meaning or relevant referent changes, matching types or updated hashes cannot substitute for a review.

## Fixed results

- Two complete works: 20 Kant units and 282 Einstein units, with 402 main assertions in total, plus auxiliary assertions and source correspondence.
- A shared catalog of 1,952 entries, separating 1,489 primitive declarations from 463 definitions and identifying 27 source-specific reference helpers.
- Cross-domain composition mapped across 36 domains, with scope, probability, interpretation, and semantic-boundary contrasts.
- Saved geometry-decoding evidence for 10,946 two-work publication records, the earlier 1,909 dictionary records, 148 general-construction records, and 195 additional records. These are artifact record counts, not distinct vocabulary counts.

See the [publication report](../../reports/two-work-final-publication-v1.json), [general-language completion](../../reports/general-language-completion-v1.json), [boundary completion](../../reports/semantic-boundaries-completion-v1.json), and [release audit](../../reports/language-release-v1.json). Some results inherit earlier actual checks after matching the pinned content and implementation; completion did not require repeating every unchanged run. Individual reports record their inheritance boundaries.

The two works' meaning judgments were made by the assistant under recorded readings. They are not independent reviews. Human readability, effects produced in actual conversation, automatic inference of unstated intentions, and automatic translation are outside this completion scope. Unknown empirical meanings still require explanation and interpretation inputs. Mathematical or scientific statements being expressible does not make them true, decidable, or executable on an infinite domain.

## Verify a retained edition

If the separate rendered edition is present, its bundled standard-library verifier checks file presence and content hashes:

```sh
python -X utf8 output/noema-1.0/scripts/verify_language_edition.py --root output/noema-1.0
```

If it was copied elsewhere, run this from that edition's root:

```sh
python -X utf8 scripts/verify_language_edition.py --root .
```

These commands are for the retained snapshot, not an arbitrary Git checkout. They do not rerun semantic judgments. The [availability guide](works.md) explains which files are distributed in Git; the [artifact lock](../../data/language-release-lock-v1.json) records the snapshot's contents.

Changes to vocabulary, syntax, or writing after 1.0 need their own versioned evidence. Preserve the original judgments and their input files rather than changing old hashes to make a new document appear previously verified. See [contributing](../../CONTRIBUTING.md) for choosing a proportionate check.
