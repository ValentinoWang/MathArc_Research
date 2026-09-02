# Frankl q=6 trace bridge: exactly three small outside parts

**Status date:** 2026-08-23  
**Claim status:** exact finite/coarse-bound theorem with independent Python/NumPy and C++ implementations; not an external expert review and not the full q=6 bridge.  
**Previous residual:** at least three small outside parts.  
**New residual:** at least four small outside parts.

## 1. Theorem

Use the minimum-three-set q=6 notation

\[
T_X=\{A\cap S:A\in\mathcal F,\ A\setminus S=X\},
\qquad |S|=3,
\qquad |\Omega|=6.
\]

Assume all three elements of \(S\) occur in strictly fewer than half of the members of the finite union-closed family \(\mathcal F\). If exactly three nonempty outside parts of sizes one or two occur, then

\[
B_6=2\sum_{x\in\Omega}d_{\mathcal F}(x)-6|\mathcal F|\ge0.
\]

Hence some outside element is abundant. Together with the previously verified zero-, one-, and two-small-part cases, this implies:

\[
\boxed{\text{Any remaining q=6 outside-balance counterexample has at least four small outside parts.}}
\]

## 2. Classification of the three small parts

Let \(r\) be the number of singleton small parts and \(e\) the number of pair small parts, so \(r+e=3\). Two singleton parts force their pair by cross-fiber union closure. Enumerating the singleton/pair hypergraphs on six outside elements and quotienting by the action of \(S_6\) gives exactly eleven orbits:

```text
(1,2,3)
(1,3,5)   (1,3,6)   (1,3,12)
(1,6,10)  (1,6,24)
(3,5,6)   (3,5,9)   (3,5,10)
(3,5,24)  (3,12,48)
```

The integers are six-bit masks for outside subsets. The Python verifier independently regenerates these eleven canonical representatives from all admissible three-part configurations.

## 3. Deficit forces enough positive cores

A singleton small fiber has trace deficit at most \(-3\), while a pair small fiber has deficit at most \(-2\). Since the total three-point trace deficit satisfies \(D\ge3\), the number \(p\) of positive-deficit fibers obeys

\[
p\ge3+3r+2e.
\]

Thus the three possible compositions require respectively:

```text
r=2, e=1: p >= 11
r=1, e=2: p >= 10
r=0, e=3: p >= 9
```

Choose that many distinct positive outside cores.

## 4. Coarse exact balance functional

Let \(G\) be the union closure of the selected positive cores, including the empty union. Every nonempty \(Z\in G\) forces at least three traces in \(T_Z\). For the three small parts \(Y_1,Y_2,Y_3\), put

\[
G_i=\{Z\cup Y_i:Z\in G\},
\qquad t_i=|T_{Y_i}|.
\]

For each high outside part \(W\), define

\[
\ell_W=\max\Bigl(
3\mathbf1_{W\in G},
 t_1\mathbf1_{W\in G_1},
 t_2\mathbf1_{W\in G_2},
 t_3\mathbf1_{W\in G_3}
\Bigr).
\]

If \(s_i=|Y_i|\), then

\[
\begin{aligned}
B_6\ge L={}&-12-\sum_{i=1}^3(6-2s_i)t_i\\
&+\sum_{\substack{W\subseteq\Omega\\|W|\ge4}}
\ell_W(2|W|-6)\\
&+6\mathbf1_{\Omega\notin G\cup G_1\cup G_2\cup G_3}.
\end{aligned}
\]

The trace-size ranges are \(1\le t_i\le4\) for a singleton and \(1\le t_i\le7\) for a pair. All omitted fibers have nonnegative coefficient in \(B_6\).

As positive cores are added, the union closure and all three translates expand. Every new high-layer contribution is nonnegative; if the top bonus disappears, an actual top trace contributes at least the same six units. Therefore the worst value over all allowed trace sizes is monotone and admits exact branch-and-bound pruning.

## 5. Exact orbit minima

Both implementations exhaust the 42 possible positive cores, the required 9, 10, or 11 selected cores, all trace-size tuples, and all eleven outside orbits. The exact minima are

\[
\boxed{0,6,6,6,6,6,6,6,6,6,24}.
\]

The zero occurs for the forced configuration consisting of two singleton parts and their pair. The value 24 occurs for three mutually disjoint pairs. Every orbit has nonnegative lower bound, proving the theorem.

## 6. Independent evidence

- Python/NumPy verifier source SHA-256: `67b789330148d1075c116a2daaaeafc3ed255634021bfd3fa350ffaa6c3ebc9e`
- C++ verifier source SHA-256: `8c7419cda82f58486130583c444a630dd021a754710f361c8b060917bbf3fc6b`
- Checked-in Python certificate SHA-256: `e5525a429c0f11d40c53868b562c34319889caac6882b9ea94c174672b5014ef`
- Checked-in C++ certificate SHA-256: `6ed2d50edee009b1b0432c74b4baf21b2b36e52f11af877d4cdfefd29d5ea23d`

The Python implementation regenerates the orbit classification and uses vectorized exact integer evaluation. The C++ implementation independently reconstructs the same branch-and-bound minima.

## 7. Remaining exact obligation

The current proof does not cover four or more small outside parts. The next target is:

> In the same q=6 setup, classify admissible small-part hypergraphs of size at least four and prove the corresponding coarse balance is nonnegative, or output an exact negative configuration that survives the full trace constraints.

No statement in this document upgrades the result to the general minimum-three-set case or to Frankl's conjecture.
