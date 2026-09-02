# Five-minute demo script

1. **Freeze the theorem.** Show the universal quantifier and the `GLOBAL` scope badge.
2. **Run finite reconnaissance.** The tool checks 101 values, but theorem closure stays `0/1` because the evidence is `FINITE_RANGE`.
3. **Kill a false route.** The coefficient checker finds the missing `2n` term; the bad lemma becomes `REFUTED`, and the dependent route becomes `INVALIDATED`.
4. **Verify the induction certificate.** Base and step close with exact arithmetic.
5. **Require independent reconstruction.** A separate coefficient normalizer reproduces the load-bearing identity.
6. **Release.** The root becomes `MACHINE_VERIFIED`; certificate debt is `NONE`; every tool output is hashed and replayable.
7. **Switch to Frankl.** Run `examples/frankl_scope_guard.py` to show that the same engine refuses to turn the verified `n=5` milestone into the global conjecture.

Investor takeaway: MathArc does not merely generate a plausible proof. It shows what was tried, what failed, what exact artifact supports each step, and why the public claim is no stronger than the evidence.
