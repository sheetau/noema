# Contributing to Noema

**English** · [日本語](CONTRIBUTING.ja.md) · [Noema](README.md)

Start with the [language guide](docs/guide/language.md) and the [evidence boundaries](docs/guide/evidence.md). A useful change identifies the meaning, syntax, writing behavior, or documentation problem it addresses, and preserves the distinctions the current release already makes.

## Local development

Use Python 3.11 or later from the repository root. Install the test dependency when needed:

```sh
python -m pip install -e ".[test]"
python -X utf8 -m scripts.project_work check --tests tests/test_quotation_construction.py
```

This is a focused example, not a required full-suite run for every edit. Parser and formatter examples work without the private project ledger. Some publication, historical audit, and source-review commands additionally require separately retained artifacts; a fresh checkout is not the maintainer's entire production environment.

The optional `ml`, `proof`, `font`, and `srl` dependency groups serve particular tools. Do not install them just to read or parse a document. Translation-engine work is deferred.

## Choose checks for the change

| Change | Appropriate checks |
| --- | --- |
| Public documentation | Local links, language switches, factual references, and executable examples |
| Parser or structural conversion | A small distinguishing example, rejection cases, and normalized syntax/binding preservation |
| Meaning or a source reading | Explicit semantic requirements, relevant definitions, contrast cases, and review of the whole affected statement |
| Circle layout or form | Actual geometry decoding and recovered syntax, plus inspection of affected shapes |
| Cache or validator | Small cached/uncached comparisons with content and validator-version hashes |

Use `project_work check` to combine applicable local tests and report work in one process. Do not routinely rerun the entire historical corpus for an isolated edit. Passing tests, structural identity, and semantic equivalence are distinct claims. Preserve old judgments, source files, and validators; do not refresh hashes to disguise stale evidence.

Before a potentially long corpus job, add durable progress, bounded checkpoint steps, and interruption/resume behavior using `scripts.long_run.LongRun`. Report a heartbeat at least every 60 seconds. Validate input and implementation hashes on resume; retry an interrupted step. A saved test result is not a semantic judgment.

## Documentation and files

English is the default for current public documentation. Maintain the paired Japanese page and reciprocal language links when changing a guide. Public guides live in `docs/guide/`; Japanese counterparts are in `docs/ja/`. Root entry points use `README.md` / `README.ja.md` and `CONTRIBUTING.md` / `CONTRIBUTING.ja.md`.

Keep public instructions usable from a checkout. Label optional local artifacts as such instead of linking to ignored output as if it were distributed. Keep progress reports and private handoff details out of the introductory README. Historical specifications and semantic contracts remain in their original language and at their original paths where evidence depends on them.

Read and write text explicitly as UTF-8. Preserve existing encoding and newlines; use UTF-8 without BOM for new text. Preserve unrelated changes and running processes. The immutable 1.0 snapshot is separate from the evolving root documentation.

## Maintainer workflow

These steps apply when working in the retained project environment. They are not setup steps for a new reader. Inspect Git and active processes, then read the authoritative handoff:

```sh
python -X utf8 -m scripts.project_notes brief
```

Read only the relevant note keys. `.noema-project/ledger.sqlite` is authoritative handoff data; `.noema-cache/` is disposable acceleration. The ledger is not distributed by Git, and a missing ledger must not be replaced with an invented empty history. `data/work-state.json` explicitly selects active evidence; filenames do not determine the active version.

Detailed operational procedures already exist in Japanese: [workflow](docs/WORKFLOW.md), [project records and recovery](docs/project-records.md), [verification boundaries](docs/verification-boundaries.md), and [long jobs](docs/long-jobs.md). The [historical README](README.history.md) remains an archive, not the starting guide. Update the relevant ledger notes with expected revisions and take a backup at meaningful boundaries. Commit coherent verified changes; push when requested.
