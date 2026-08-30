# MathArc benchmark program

The benchmark has two independent axes.

## A. Mathematical capability

- theorem solved under a frozen statement;
- pass@k / success@budget;
- proof length and kernel acceptance;
- novelty or bound improvement on research tasks;
- time, tokens, and compute.

## B. Research reliability

- scope/quantifier violations blocked;
- false bridges killed and propagated;
- certificate replay success;
- independent reconstruction rate;
- statement correspondence;
- route mechanism diversity;
- certificate debt at release;
- failure-to-regression conversion.

A system may be strong on one axis and weak on the other. MathArc's product claim is that both must be measured.

Run the deterministic B0 gate with:

```bash
python -m unittest discover -s tests -v
python -m matharc demo --out-dir artifacts/demo
python -m matharc validate --run artifacts/demo/run.json
```
