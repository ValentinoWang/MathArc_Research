#!/usr/bin/env python3
"""Generate a self-contained ES(7)=33 canonical signotope SAT instance.

This CI instance contains the exact signotope/tight-path encoding and all
51,156 bichromatic length-6 fork guards. The 19,182 earlier local-window guards
are omitted because they are logical consequences, not part of the semantics.
Thus SAT/UNSAT is unchanged; the generated file has a frozen reference hash.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
from pathlib import Path
N=33; OMAX=math.comb(N,3); SIGNS=(1,-1); LENGTHS=range(3,8)

def omap(): return {t:i+1 for i,t in enumerate(itertools.combinations(range(N),3))}
def alloc():
 r={};p={};v=OMAX+1
 for s in SIGNS:
  for l in LENGTHS:
   for a,i,j in itertools.combinations(range(N),3):
    if i-a>=l-2:r[s,l,a,i,j]=v;v+=1
 for s in SIGNS:
  for l in LENGTHS:
   for a,g in itertools.combinations(range(N),2):
    if g-a>=l-1:p[s,l,a,g]=v;v+=1
 return r,p,v-1
def slit(v,s):return v if s==1 else -v
def signotope_clauses(o):
 for a,b,c,d in itertools.combinations(range(N),4):
  A=o[a,b,c];B=o[a,b,d];C=o[a,c,d];D=o[b,c,d]
  yield [-A,-C,B];yield [A,C,-B];yield [-A,-D,C];yield [A,D,-C]
def path_clauses(o,r,p):
 for a,i,j in itertools.combinations(range(N),3):
  for s in SIGNS:yield [-slit(o[a,i,j],s),r[s,3,a,i,j]]
 for s in SIGNS:
  for l in range(3,7):
   for a,h,i,j in itertools.combinations(range(N),4):
    if (s,l,a,h,i) in r:yield [-r[s,l,a,h,i],-slit(o[h,i,j],s),r[s,l+1,a,i,j]]
 for s in SIGNS:
  for l in LENGTHS:
   for a,i,g in itertools.combinations(range(N),3):
    if (s,l,a,i,g) in r:yield [-r[s,l,a,i,g],p[s,l,a,g]]
 for a,g in itertools.combinations(range(N),2):
  if g-a<6:continue
  yield [-p[1,7,a,g]];yield [-p[-1,7,a,g]]
  yield [-p[1,3,a,g],-p[-1,6,a,g]]
  yield [-p[1,4,a,g],-p[-1,5,a,g]]
  yield [-p[1,5,a,g],-p[-1,4,a,g]]
  yield [-p[1,6,a,g],-p[-1,3,a,g]]
def fork_clauses(r):
 for u,v in itertools.combinations(range(N),2):
  if v>=N-1:continue
  plus=[r[1,6,s,u,v] for s in range(u-3) if (1,6,s,u,v) in r]
  minus=[r[-1,6,s,u,v] for s in range(u-3) if (-1,6,s,u,v) in r]
  for x in plus:
   for y in minus:yield [-x,-y]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);a=ap.parse_args()
 o=omap();r,p,last=alloc();fork=list(fork_clauses(r));assert len(fork)==51156
 base=4*math.comb(N,4)+math.comb(N-1,2)+329930;total=base+len(fork)
 a.out.parent.mkdir(parents=True,exist_ok=True);w=0
 with a.out.open('w',encoding='ascii',newline='\n',buffering=1<<20) as f:
  f.write('c ES(7)=33 round-six orientation-only tight-path encoding\n')
  f.write(f'p cnf {last} {total}\n')
  for C in signotope_clauses(o):f.write(' '.join(map(str,C))+' 0\n');w+=1
  for x,y in itertools.combinations(range(1,N),2):f.write(f'{o[0,x,y]} 0\n');w+=1
  for C in path_clauses(o,r,p):f.write(' '.join(map(str,C))+' 0\n');w+=1
  for C in fork:f.write(' '.join(map(str,C))+' 0\n');w+=1
 assert w==total,(w,total)
 expected='f67b2421174e063c6090b4114e0e01c7a3f246e0c7645638150a2162562efed6'
 result={'schema_version':1,'n':N,'k':7,'variables':last,'clauses':total,'fork_guards':len(fork),'sha256':sha(a.out),'expected_sha256':expected,'exact_reproduction':False,'semantic_scope':'exact canonical rank-3 signotope relaxation; UNSAT proves planar ES(7)<=33; SAT may be nonstretchable'}
 result['exact_reproduction']=result['sha256']==expected
 a.manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2,sort_keys=True))
 if not result['exact_reproduction']:raise SystemExit(3)
if __name__=='__main__':main()
