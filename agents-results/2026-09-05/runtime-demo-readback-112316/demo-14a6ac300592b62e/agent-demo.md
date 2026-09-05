# MathArc Agent Demo

- Status: `VERIFIED_CERTIFICATE`
- Question: Prove that the sum of the first n positive odd integers equals n squared.
- Question SHA-256: `14a6ac300592b62e31b4679449638223fd6860f1efe2706659d623626a105859`
- Runtime run: `demo-14a6ac300592b62e`

## Observable Loop

1. Decomposition: `READY` (`6fed5eb31da318ea4d7fdef39395c5533f5711240e7bba36a4682dfafa5e3d70`)
2. Deterministic model proposal: `d0eaff0976a59faea36e088a15d998b326d4d953f82c7c3748d99e461685a69b`; authority `False`
3. Exact tool: `exact:induction_certificate` -> `PASS`; output `a8968662f72a8115fa8f35b12cffe42c380800f6b1b46ad5294122b54a2f7b79`
4. Independent replay: `PASS`; replay `3587a63db25be30f8639b70101c7b0ca555a92fef1459d131c3cc7641b0bc5c4`
5. Evidence: `ev-25f4ae4c6b7071ef9ff4f8f0f2cf2531e1d1e26db20bee8c7e68f8e0b1a0a2fc`; digest `fe59158e9ac337767f207fd93cd5272f30596caf52358a91b451e073a25e57b7`

Result: The odd-sum induction certificate passed independent replay. (claim `C-STEP`)
The certificate is verified, but this demo does not promote a theorem claim.

## Provenance

```json
{
  "workspace_id": "matharc-demo-workspace",
  "trace_id": "trace-14a6ac300592b62e",
  "runtime_run_id": "demo-14a6ac300592b62e",
  "generation_id": "generation-1",
  "network": false,
  "credentials": false,
  "deterministic": true
}
```

