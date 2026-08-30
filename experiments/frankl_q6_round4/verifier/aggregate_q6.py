#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result_dir=a.root/'results'
    names={
      'k_le_3':'q6-at-most-three-small.json',
      'k_4':'q6-exact4.json',
      'k_5':'q6-exact5.json',
      'k_6':'q6-exact6.json',
      'k_7_nonfull':'q6-exact7-nonfull.json',
      'k_7_full':'q6-exact7-full.json',
      'positive_core_hmin':'q6-positive-core-hmin.json',
      'k_ge_8':'q6-many-small.json',
    }
    loaded={key:json.loads((result_dir/name).read_text(encoding='utf-8')) for key,name in names.items()}
    for key,data in loaded.items():
        passed = data.get('all_checks_passed', data.get('all_expected'))
        assert passed is True, (key,data)
    assert loaded['k_le_3']['residual_obligation'].endswith('at least four small outside parts.')
    assert loaded['k_4']['minimum_exact_margin'] >= 0
    assert loaded['k_5']['minimum_cardinality_margin'] >= 0
    assert loaded['k_6']['minimum_margin'] >= 0
    assert loaded['k_7_nonfull']['minimum_margin'] >= 0
    assert loaded['positive_core_hmin']['Hmin'][42] == 180
    assert loaded['k_ge_8']['conclusion']['k_8_to_18'] == 'all relaxed margins nonnegative'
    files=[]
    for path in sorted(a.root.rglob('*')):
        if path.is_file() and path != a.output:
            files.append({'path':str(path.relative_to(a.root)),'bytes':path.stat().st_size,'sha256':sha256(path)})
    out={
      'schema_version':1,
      'status_date':'2026-08-23',
      'claim':(
        'Let F be a finite union-closed family with empty set adjoined, let S be a '
        'minimum nonempty member of size three, and let Omega=(union F)\\S have size six. '
        'If all three elements of S occur in strictly fewer than half the members of F, '
        'then B_6>=0 and therefore some element of Omega occurs in at least half the members.'
      ),
      'claim_status':'machine-checked candidate q=6 special-case theorem; not externally peer reviewed',
      'coverage':{
        'small_parts_0_or_1':'previous cross-fiber proof',
        'small_parts_2_or_3':'exact trace and charge verifier',
        'small_parts_4':'24 support orbits plus trace propagation',
        'small_parts_5':'51 support orbits plus cardinal propagation',
        'small_parts_6':'92 support orbits plus relaxed cardinal propagation',
        'small_parts_7':'24 seven-pair orbits plus full-trace exclusions',
        'small_parts_8_to_18':'complete H_min table plus exact deficit-cost dynamic program',
        'small_parts_19_to_21':'infeasible: more than 42 positive cores required',
      },
      'conclusion':{
        'q6_bridge':'CLOSED_INTERNAL_EXACT',
        'minimum_three_set_q_le_6':'CLOSED_INTERNAL_EXACT',
        'minimum_three_set_q_ge_7':'OPEN',
        'full_frankl_conjecture':'INCONCLUSIVE',
      },
      'checks':{key:{'file':names[key],'all_checks_passed':True} for key in names},
      'artifacts':files,
      'all_checks_passed':True,
    }
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n';a.output.write_text(text,encoding='utf-8');print(text,end='');return 0
if __name__=='__main__':raise SystemExit(main())
