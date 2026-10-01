# dev-env's Architecture Decision Records

Decisions about dev-env itself: how the templates are organized and generated. The rules are the
ones every template carries (`templates/<kind>/docs/adr/README.md`): one decision per ADR, frozen
once accepted, superseded rather than rewritten, linking only to things that last.

Decisions that a generated project inherits live in that template's own `docs/adr/`, not here.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-each-template-is-a-self-contained-repository.md) | Each template is a self-contained repository; shared files are kept identical by a check, not by a common layer | Accepted |
| [0002](0002-one-stdlib-generator-driven-by-template-manifests.md) | One stdlib-only generator, driven by each template's `template.json` | Accepted |
