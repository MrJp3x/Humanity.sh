# Contributing

Humanity.sh is an early project. Small, explainable additions are welcome.

1. Describe the behavior you want to introduce and the assumptions behind it.
2. Keep engine logic independent of DOM rendering and external providers.
3. Use seeded randomness for simulation changes; keep extension data serializable.
4. Preserve the separation of external facts, individual interpretation, and outward expression.
5. Include meaningful behavioral or invariant tests for model changes. Do not encode a desired societal conclusion as a test.
6. Update `docs/model.md` when assumptions change, and document any snapshot compatibility changes.
7. Run `npm run check`, `npm test`, and `npm run build` before submitting a pull request.

Code contributions are provided under the project's MIT license. Keep third-party asset licenses and attribution with their assets.
