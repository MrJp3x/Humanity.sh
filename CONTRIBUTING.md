# Contributing

Humanity.sh's primary engine is Python. Small, explainable additions are welcome.

1. Describe the proposed behavior and the assumptions behind it.
2. Keep world logic in `humanity/engine`, independent of Qt, HTML, and external providers.
3. Use seeded randomness. Keep dataclasses and module state serializable.
4. Preserve the separation of facts, subjective interpretation, and outward expression.
5. Add meaningful behavior or invariant tests for engine changes. Never encode a desired societal conclusion as a test.
6. Update `docs/model.md` when assumptions change and document snapshot compatibility.
7. Keep UI changes in the frontend; desktop state changes must go through the command bridge.

Before submitting, run:

```sh
python -m unittest discover -s tests_python -v
npm run check
npm test
npm run build
```

Qt tests require the desktop extra. Cross-language migration tests require Node 22+; they are skipped when Node is unavailable. Browser compatibility code is retained as a reference, not as a second desktop backend. If model semantics intentionally change, update the documented model version and compatibility expectations rather than blindly copying code between languages.

Code contributions use the project's MIT license. Preserve third-party font and dependency attribution.
