# Works and examples

**English** · [日本語](../ja/works.md) · [Documentation](../README.md)

Two complete source works are represented in Noema under explicitly recorded readings. “Complete” concerns the selected source scope, including formulas and author notes; it is not an assertion that the authors' arguments or scientific claims are true.

| Work | Source units | Main assertions | Tracked manuscript |
| --- | ---: | ---: | --- |
| Immanuel Kant, *An Answer to the Question: What Is Enlightenment?* (1784) | 20 | 119 | [Kant manuscript](../../examples/v016/kant-reviewed-complete-v1.noema) |
| Albert Einstein, *On the Electrodynamics of Moving Bodies* (1905) | 282 | 283 | [Einstein manuscript](../../examples/v014/einstein-auxiliary-reference-order-v1.noema) |

The two publications also contain 97 auxiliary assertions. Source units and assertions are different counting units: one source unit may need several Noema statements. Einstein's edition includes correspondence for 446 source mathematical occurrences, expressed in Noema rather than left solely as embedded formula images.

The [review index](../../data/semantic-review-index-v457.json) selects manuscripts, meaning bases, identifier annotations, and individual judgments. The [publication manifest](../../data/two-work-publication-v1.json) records their rendered integration. Some paths inside these records point to separately retained artifacts; the tracked record is not itself a bundle of all those files.

## What a Git checkout contains

- Native manuscripts under `examples/`, dictionary and meaning records under `data/`, and selected results under `reports/`.
- Parser/runtime code under `noema/`, publication and validation tools under `scripts/`, and regression tests under `tests/`.
- The current bilingual guides and preserved historical specifications/reviews under `docs/`.

Large generated `output/` and `artifacts/` trees are not distributed by a normal Git clone. The private `.noema-project/` handoff database is also separate. A path to one of these in a manifest describes the retained production environment; it is not a working download link. The introductory parser examples need none of these trees.

## Rendered reading editions

If a copy of the rendered artifacts is available locally, open the following HTML entries in a browser. These are local paths, not files promised by this checkout:

| Local path | Contents |
| --- | --- |
| `output/noema-1.0/index.html` | Sealed edition: works, dictionary, specifications, and evidence |
| `output/two-work-final-v2/index.html` | Two works with source alignment, mathematics, notes, and fixed circle writing |
| `output/general-language-v1/index.html` | Earlier 1,909-entry shared dictionary |
| `output/semantic-boundaries-v1/index.html` | The additional 43 definitions and contrasting examples |
| `output/noema-writing-v2/index.html` | Adopted writing inventory and examples |

These retained HTML editions and their original source/meaning descriptions have not been translated by the documentation update. The current guides are English by default; they do not rewrite the frozen edition. If the rendered bundle is absent, start with the tracked manuscripts and examples above. Do not regenerate retired previews merely to follow this guide.

## Smaller examples

| Topic | File or record | What it demonstrates |
| --- | --- | --- |
| Quantifier order | [Introductory scope example](../../examples/intro/scope.noema) | Per-object witnesses versus one common witness |
| Everyday discourse | [Conditional directive](../../examples/v010/conditional-directive.noema) | Assumed rain, a request, and a separate question |
| Reading and delivery | [Scope contrasts](../../data/general-scope-contrasts-v1.json) | Explicit interpretations and distinctions between readings |
| Probability | [Probability contrasts](../../data/general-probability-contrasts-v1.json) | Lottery cases and hypothesis updates |
| Description construction | [Personal message and purpose](../../examples/v016/personal-message-purpose.noema) | Preserving a person's particular message in a purpose description |
| Meaning boundaries | [Boundary examples](../../examples/v016/semantic-boundaries-v1.noema) | Existence, information, reports, and compositional distinctions |

The [cross-domain review](../../reports/general-language-review-v2.json) maps constructions to 36 domains. Its descriptions of possible applications are not themselves newly reviewed translations. Use the [evidence guide](evidence.md) to distinguish examples, diagnostics, and source judgments.
