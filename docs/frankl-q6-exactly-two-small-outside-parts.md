# Frankl q=6 trace bridge: exactly two small outside parts

**Status date:** 2026-08-23  
**Claim status:** exact finite/coarse-bound theorem with two implementations; not yet an external expert review or a proof of the full q=6 bridge.  
**Previous residual:** at least two small outside parts.  
**New residual:** at least three small outside parts.

## 1. Theorem

Let \(\mathcal F\) be a finite union-closed family. Adjoin the empty set if necessary. Suppose \(S\in\mathcal F\) is a minimum-cardinality nonempty member, \(|S|=3\), and

\[
\Omega=\bigcup\mathcal F\setminus S,
\qquad |\Omega|=6.
\]

For \(X\subseteq\Omega\), put

\[
T_X=\{A\cap S:A\in\mathcal F,\ A\setminus S=X\}.
\]

Call a nonempty outside part \(X\) **small** when \(|X|\in\{1,2\}\) and \(T_X\ne\varnothing\).
Assume all three elements of \(S\) occur in strictly fewer than half of the members of \(\mathcal F\), and assume **exactly two** small outside parts occur. Then

\[
B_6:=2\sum_{x\in\Omega}d_{\mathcal F}(x)-6|\mathcal F|\ge0.
\]

Consequently some element of \(\Omega\) occurs in at least half of \(\mathcal F\).

This combines with the previous at-most-one-small-part theorem to give the strict residual

\[
\boxed{\text{Any failure of the q=6 outside-balance bridge has at least three small outside parts.}}
\]

## 2. Deficit accounting

For every nonempty fiber define

\[
\Delta_X=3|T_X|-2\sum_{R\in T_X}|R|.
\]

The three-point trace classification gives \(\Delta_X\le1\); the positive-deficit fibers have \(\Delta_X=1\), contain the empty trace, and have at least three traces. If all three elements of \(S\) are below half, then

\[
D:=\sum_X\Delta_X\ge3.
\]

A positive core has outside size at least three: otherwise its empty trace would produce a nonempty member of \(\mathcal F\) smaller than \(S\).

Exact enumeration of the admissible trace fibers gives:

- singleton outside part: eight trace families,
  \[
  (t,\Delta)\in\{(1,-3),(2,-4),(3,-5),(4,-6)\};
  \]
  in particular \(t\le4\) and \(\Delta\le-3\);
- pair outside part: forty-five trace families,
  \[
  \begin{aligned}
  (t,\Delta)\in\{&(1,-3),(2,-4),(2,-2),(3,-5),(3,-3),\\
  &(4,-6),(4,-4),(4,-2),(5,-5),(5,-3),(6,-4),(7,-3)\};
  \end{aligned}
  \]
  in particular \(t\le7\) and \(\Delta\le-2\).

Thus a singleton-pair configuration has at least eight positive-deficit fibers, while a pair-pair configuration has at least seven. In either case choose seven distinct positive cores.

Two distinct singleton small parts cannot be the only two small parts: their union is a pair, and cross-fiber union closure makes its fiber nonempty. Up to a permutation of \(\Omega\), the remaining configurations are:

1. a singleton contained in a pair;
2. a singleton disjoint from a pair;
3. two intersecting pairs;
4. two disjoint pairs.

## 3. Exact coarse lower-bound functional

Let \(C\) be seven selected positive cores and let \(G=\langle C\rangle_\cup\) be their union closure, including the empty union. For every nonempty \(Z\in G\), iterated cross-fiber closure gives

\[
|T_Z|\ge3.
\]

Let the two small parts be \(Y_1,Y_2\), with \(t_i=|T_{Y_i}|\), and put

\[
G_i=\{Z\cup Y_i:Z\in G\}.
\]

Since the forced trace in every \(T_Z\), \(Z\in G\), contains the empty trace, cross-fiber closure gives \(|T_W|\ge t_i\) whenever \(W\in G_i\). Therefore set

\[
\ell_W=\max\bigl(
3\mathbf1_{W\in G},
 t_1\mathbf1_{W\in G_1},
 t_2\mathbf1_{W\in G_2}
\bigr).
\]

If \(s_i=|Y_i|\), then the following is a lower bound for the actual outside balance:

\[
\begin{aligned}
L(C;Y_1,Y_2;t_1,t_2)
={}&-12-(6-2s_1)t_1-(6-2s_2)t_2\\
&+\sum_{\substack{W\subseteq\Omega\\|W|\ge4}}
\ell_W(2|W|-6)\\
&+6\mathbf1_{\Omega\notin G\cup G_1\cup G_2}.
\end{aligned}
\]

The last term records the unavoidable full-\(S\) trace in the top fiber when the top has not already been generated. Every omitted fiber has nonnegative coefficient in \(B_6\), hence

\[
B_6\ge L(C;Y_1,Y_2;t_1,t_2).
\]

## 4. Exhaustive verification and pruning correctness

There are

\[
\binom63+\binom64+\binom65+\binom66=42
\]

possible positive outside cores. The verifier checks all seven-core collections, all four orbit types, and every coarse trace-size pair

\[
1\le t\le4\quad\text{for a singleton},
\qquad
1\le t\le7\quad\text{for a pair}.
\]

The search uses a monotone branch-and-bound. When another positive core is adjoined, \(G,G_1,G_2\) only expand. Every newly counted high-layer term is nonnegative. If the top bonus disappears, the top has been generated with multiplicity at least one and contributes at least the same six units. Hence \(L\) is nondecreasing for each fixed \((t_1,t_2)\), and so its minimum over the allowed trace sizes is also nondecreasing. A branch may therefore be pruned once its current worst margin reaches the best explicit witness.

The exact minima are:

| Orbit | Exact minimum of \(L\) |
|---|---:|
| singleton contained in pair | 0 |
| singleton disjoint from pair | 0 |
| intersecting pairs | 6 |
| disjoint pairs | 6 |

Therefore \(B_6\ge0\) in every exactly-two-small-part configuration.

## 5. Independent artifacts

- Python exact certificate SHA-256: `445c4743f45e71624a1c6e9b8b6484a77fa80b63c69f7aa771bdb3e38d6aadb4`
- Independent C++ source SHA-256: `db9ce4479cf2351c0f769486f56d974a81a15c1f7f220bc270c147a3c672650d`
- Independent C++ replay output SHA-256: `d679aa77ffdf6bc29c52f00b4ca05f3a0d85b9806d155fa3c0671c23b56b5a30`

The Python implementation additionally re-enumerates the 8 singleton and 45 pair trace families. The C++ implementation independently reconstructs the 42-core branch-and-bound and the four minima.

## 6. Remaining obligation

This theorem does **not** prove the full q=6 bridge. The new exact residual is:

> Assume the minimum-three-set q=6 setup, all three elements of \(S\) below half, and at least three distinct small outside parts. Prove \(B_6\ge0\), or produce an exact counterexample to this sufficient bridge.

The next search should classify the union-closed hypergraph formed by the small outside parts and exploit the additional positive-core count forced by their total trace deficit.
