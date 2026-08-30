#include <bits/stdc++.h>
using namespace std; using u64=uint64_t;
struct TT{uint8_t m;int t,d;};
vector<int> cores; u64 coreMask=0;
uint8_t JN[256][256];
inline u64 addcore(u64 G,int x){u64 H=G,b=G;while(b){int z=__builtin_ctzll(b);b&=b-1;H|=1ULL<<(z|x);}return H;}
inline int Hcharge(u64 G){int v=6;for(int z=0;z<64;z++)if((G>>z)&1ULL){int s=__builtin_popcount((unsigned)z);if(s>=4)v+=3*(2*s-6);}if((G>>63)&1ULL)v-=6;return v;}
bool uc(int m){for(int a=0;a<8;a++)if(m>>a&1)for(int b=0;b<8;b++)if(m>>b&1)if(!(m>>(a|b)&1))return false;return true;}
int hlow(int p){if(p<=5)return 12;if(p==6)return 24;if(p==7)return 30;if(p<=9)return 36;if(p<=12)return 42;if(p<=16)return 48;return 60;}
vector<array<int,6>> perms6(){array<int,6>a{0,1,2,3,4,5};vector<array<int,6>>p;do{p.push_back(a);}while(next_permutation(a.begin(),a.end()));return p;}
int pset(int x,const array<int,6>&p){int y=0;for(int i=0;i<6;i++)if(x>>i&1)y|=1<<p[i];return y;}
vector<int> canon(vector<int>M,const vector<array<int,6>>&P){sort(M.begin(),M.end());vector<int>best;bool first=true;for(auto&p:P){vector<int>v;for(int x:M)v.push_back(pset(x,p));sort(v.begin(),v.end());if(first||v<best){best=v;first=false;}}return best;}

array<uint8_t,64> forced_map(const vector<int>&supp,const vector<uint8_t>&masks,bool &feasible){array<uint8_t,64>f{};for(size_t i=0;i<supp.size();i++)f[supp[i]]|=masks[i];bool ch=true;while(ch){ch=false;vector<int>a;for(int i=0;i<64;i++)if(f[i])a.push_back(i);for(int u:a)for(int v:a){int w=u|v;uint8_t nm=f[w]|JN[f[u]][f[v]];if(nm!=f[w]){f[w]=nm;ch=true;}}}
 feasible=true;for(size_t i=0;i<supp.size();i++)if(f[supp[i]] & ~masks[i]){feasible=false;break;}return f;}
int combined_high(u64 G,const array<uint8_t,64>&small){array<uint8_t,64>f{};vector<int>zs;u64 b=G;while(b){int z=__builtin_ctzll(b);b&=b-1;zs.push_back(z);}for(int u=0;u<64;u++)if(small[u])for(int z:zs)f[u|z]|=small[u];int total=0;for(int w=0;w<64;w++){int s=__builtin_popcount((unsigned)w);if(s<4)continue;int k=__builtin_popcount((unsigned)f[w]);if((G>>w)&1ULL)k=max(3,k+(f[w]&1?0:1));total+=(2*s-6)*k;}int topk=__builtin_popcount((unsigned)f[63]);if((G>>63)&1ULL)topk=max(3,topk+(f[63]&1?0:1));if(topk==0) total+=6;return total;}

int main(){
 for(int a=0;a<256;a++)for(int b=0;b<256;b++){int o=0;for(int r=0;r<8;r++)if(a>>r&1)for(int q=0;q<8;q++)if(b>>q&1)o|=1<<(r|q);JN[a][b]=o;}
 vector<TT>S,P;for(int m=0;m<256;m++)if((m>>7&1)&&uc(m)){int t=__builtin_popcount((unsigned)m),sum=0;for(int r=0;r<8;r++)if(m>>r&1)sum+=__builtin_popcount((unsigned)r);int d=3*t-2*sum;bool sOK=true,pOK=true;for(int r=0;r<8;r++)if(m>>r&1){if(__builtin_popcount((unsigned)r)<2)sOK=false;if(__builtin_popcount((unsigned)r)<1)pOK=false;}if(sOK&&t<4)S.push_back({(uint8_t)m,t,d});if(pOK&&t<7)P.push_back({(uint8_t)m,t,d});}
 for(int x=1;x<64;x++)if(__builtin_popcount((unsigned)x)>=3){cores.push_back(x);coreMask|=1ULL<<x;}
 unordered_set<u64> seen;seen.reserve(200000);vector<u64>q{1};seen.insert(1);for(size_t h=0;h<q.size();h++){u64 G=q[h];for(int x:cores)if(!(G>>x&1ULL)){u64 N=addcore(G,x);if(Hcharge(N)<=54&&seen.insert(N).second)q.push_back(N);}}
 map<pair<int,int>,vector<u64>> candidates;for(u64 G:q){int pc=__builtin_popcountll(G&coreMask),hc=Hcharge(G);for(int p=1;p<=20;p++)for(int need=1;need<=80;need++)if(pc>=p&&hc<need)candidates[{p,need}].push_back(G);}
 auto PP=perms6();set<vector<int>> orbitset;vector<int>singles;for(int i=0;i<6;i++)singles.push_back(1<<i);vector<int>pairs;for(int x=0;x<64;x++)if(__builtin_popcount((unsigned)x)==2)pairs.push_back(x);
 for(int a=0;a<=2;a++){
  vector<vector<int>>As; vector<int>idxA(a); function<void(int,int)>recA=[&](int st,int dep){if(dep==a){vector<int>v;for(int i:idxA)v.push_back(singles[i]);As.push_back(v);return;}for(int i=st;i<=6-(a-dep);i++){idxA[dep]=i;recA(i+1,dep+1);}};recA(0,0);
  for(auto A:As){set<int>req;for(size_t i=0;i<A.size();i++)for(size_t j=i+1;j<A.size();j++)req.insert(A[i]|A[j]);int e=4-a;vector<int>idxE(e);function<void(int,int)>recE=[&](int st,int dep){if(dep==e){vector<int>E;for(int i:idxE)E.push_back(pairs[i]);for(int r:req)if(find(E.begin(),E.end(),r)==E.end())return;vector<int>M=A;M.insert(M.end(),E.begin(),E.end());orbitset.insert(canon(M,PP));return;}for(int i=st;i<=(int)pairs.size()-(e-dep);i++){idxE[dep]=i;recE(i+1,dep+1);}};recE(0,0);}
 }
 vector<vector<int>>orbits(orbitset.begin(),orbitset.end());
 long long assignments=0,infeasible=0,coarseClosed=0,exactChecked=0;int globalMargin=INT_MAX;string witness="";
 for(auto M:orbits){vector<int>si,pi;for(int i=0;i<4;i++)(__builtin_popcount((unsigned)M[i])==1?si:pi).push_back(i);if(si.size()==2){continue;}
  if(si.empty()){
   for(auto&a:P)for(auto&b:P)for(auto&c:P)for(auto&d:P){assignments++;vector<TT>ts{a,b,c,d};int pr=3-(a.d+b.d+c.d+d.d),need=12+2*(a.t+b.t+c.t+d.t);if(hlow(pr)>=need){coarseClosed++;continue;}vector<uint8_t>ms{a.m,b.m,c.m,d.m};bool feas;auto sf=forced_map(M,ms,feas);if(!feas){infeasible++;continue;}int mn=INT_MAX;for(u64 G:candidates[{pr,need}])mn=min(mn,combined_high(G,sf));exactChecked++;globalMargin=min(globalMargin,mn-need);if(mn<need){witness="ns0";goto done;}}
  }else if(si.size()==1){int spos=si[0];vector<int>ppos=pi;for(auto&s:S)for(auto&a:P)for(auto&b:P)for(auto&c:P){assignments++;int pr=3-(s.d+a.d+b.d+c.d),need=12+4*s.t+2*(a.t+b.t+c.t);if(hlow(pr)>=need){coarseClosed++;continue;}vector<uint8_t>ms(4);ms[spos]=s.m;ms[ppos[0]]=a.m;ms[ppos[1]]=b.m;ms[ppos[2]]=c.m;bool feas;auto sf=forced_map(M,ms,feas);if(!feas){infeasible++;continue;}int mn=INT_MAX;for(u64 G:candidates[{pr,need}])mn=min(mn,combined_high(G,sf));exactChecked++;globalMargin=min(globalMargin,mn-need);if(mn<need){witness="ns1";goto done;}}
  }
 }
done:
 cout<<"{\n\"support_orbits\":"<<orbits.size()<<",\n\"low_charge_states\":"<<q.size()<<",\n\"assignments_considered\":"<<assignments<<",\n\"coarse_closed\":"<<coarseClosed<<",\n\"infeasible_assignments\":"<<infeasible<<",\n\"exact_combined_checks\":"<<exactChecked<<",\n\"minimum_exact_margin\":"<<(globalMargin==INT_MAX?999:globalMargin)<<",\n\"counterexample_class\":\""<<witness<<"\",\n\"all_checks_passed\":"<<(witness.empty()?"true":"false")<<"\n}\n";
 return witness.empty()?0:1;
}
