#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('cnf',type=Path);ap.add_argument('solver_output',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 vals={};status=None
 for line in a.solver_output.read_text(errors='replace').splitlines():
  if line.startswith('s '):status=line.strip()
  if line.startswith('v '):
   for s in line[2:].split():
    x=int(s)
    if x: vals[abs(x)]=x>0
 V=C=0;checked=bad=0;first_bad=None
 with a.cnf.open() as f:
  clause=[]
  for line in f:
   if not line or line[0]=='c':continue
   if line[0]=='p':_,_,V,C=line.split()[:4];V=int(V);C=int(C);continue
   for s in line.split():
    x=int(s)
    if x:clause.append(x)
    else:
     checked+=1
     ok=any(vals.get(abs(l))==(l>0) for l in clause)
     if not ok:
      bad+=1
      if first_bad is None:first_bad={'index':checked,'clause':clause[:]}
     clause=[]
 result={'status':status,'variables_expected':V,'variables_assigned':len(vals),'clauses_expected':C,'clauses_checked':checked,'bad_clauses':bad,'first_bad':first_bad,'valid_sat_model':status=='s SATISFIABLE' and len(vals)==V and checked==C and bad==0}
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 raise SystemExit(0 if result['valid_sat_model'] else 1)
if __name__=='__main__':main()
