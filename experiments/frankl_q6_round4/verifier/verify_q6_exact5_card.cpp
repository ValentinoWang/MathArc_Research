#include <bits/stdc++.h>
using namespace std; using u64=uint64_t;
struct TT{uint8_t m;int t,d;};
vector<int> cores; u64 coreMask=0; uint8_t JN[256][256];
inline u64 addcore(u64 G,int x){u64 H=G,b=G;while(b){int z=__builtin_ctzll(b);b&=b-1;H|=1ULL<<(z|x);}return H;}
inline int Hcharge(u64 G){int v=6;for(int z=0;z<64;z++)if((G>>z)&1ULL){int s=__builtin_popcount((unsigned)z);if(s>=4)v+=3*(2*s-6);}if((G>>63)&1ULL)v-=6;return v;}
bool uc(int m){for(int a=0;a<8;a++)if(m>>a&1)for(int b=0;b<8;b++)if(m>>b&1)if(!(m>>(a|b)&1))return false;return true;}
vector<array<int,6>> perms6(){array<int,6>a{0,1,2,3,4,5};vector<array<int,6>>p;do{p.push_back(a);}while(next_permutation(a.begin(),a.end()));return p;}
int pset(int x,const array<int,6>&p){int y=0;for(int i=0;i<6;i++)if(x>>i&1)y|=1<<p[i];return y;}
vector<int> canon(vector<int>M,const vector<array<int,6>>&P){sort(M.begin(),M.end());vector<int>best;bool first=true;for(auto&p:P){vector<int>v;for(int x:M)v.push_back(pset(x,p));sort(v.begin(),v.end());if(first||v<best){best=v;first=false;}}return best;}
array<uint8_t,64> forced_map(const vector<int>&supp,const vector<uint8_t>&masks,bool &feasible){array<uint8_t,64>f{};for(size_t i=0;i<supp.size();i++)f[supp[i]]|=masks[i];bool ch=true;while(ch){ch=false;vector<int>a;for(int i=0;i<64;i++)if(f[i])a.push_back(i);for(int u:a)for(int v:a){int w=u|v;uint8_t nm=f[w]|JN[f[u]][f[v]];if(nm!=f[w]){f[w]=nm;ch=true;}}}
 feasible=true;for(size_t i=0;i<supp.size();i++)if(f[supp[i]] & ~masks[i]){feasible=false;break;}return f;}
int combined_high(u64 G,const array<uint8_t,64>&small){array<uint8_t,64>f{};vector<int>zs;u64 b=G;while(b){int z=__builtin_ctzll(b);b&=b-1;zs.push_back(z);}for(int u=0;u<64;u++)if(small[u])for(int z:zs)f[u|z]|=small[u];int total=0;for(int w=0;w<64;w++){int s=__builtin_popcount((unsigned)w);if(s<4)continue;int k=__builtin_popcount((unsigned)f[w]);if((G>>w)&1ULL)k=max(3,k+(f[w]&1?0:1));total+=(2*s-6)*k;}int topk=__builtin_popcount((unsigned)f[63]);if((G>>63)&1ULL)topk=max(3,topk+(f[63]&1?0:1));if(topk==0) total+=6;return total;}
inline u64 shifted(u64 G,int y){u64 out=0,b=G;while(b){int z=__builtin_ctzll(b);b&=b-1;out|=1ULL<<(z|y);}return out;}
int fullpaircharge(u64 G,int y){u64 gy=shifted(G,y);int total=0;for(int w=0;w<64;w++){int s=__builtin_popcount((unsigned)w);if(s<4)continue;int k=0;if(G>>w&1ULL)k=3;if(gy>>w&1ULL)k=max(k,7);total+=(2*s-6)*k;}if(!((G|gy)>>63&1ULL))total+=6;return total;}
int fullsinglecharge(u64 G,int y){u64 gy=shifted(G,y);int total=0;for(int w=0;w<64;w++){int s=__builtin_popcount((unsigned)w);if(s<4)continue;bool a=G>>w&1ULL,b=gy>>w&1ULL;int k=a&&b?5:(a?3:(b?4:0));total+=(2*s-6)*k;}if(!((G|gy)>>63&1ULL))total+=6;return total;}
pair<int,int> restricted_cap(int cap,int y,bool pairmode){vector<int>E;u64 em=0;for(int x:cores)if((x&y)!=y){E.push_back(x);em|=1ULL<<x;}unordered_set<u64>seen;seen.reserve(10000);vector<u64>q{1};seen.insert(1);int mx=0;for(size_t h=0;h<q.size();h++){u64 G=q[h];mx=max(mx,__builtin_popcountll(G&em));for(int x:E)if(!(G>>x&1ULL)){u64 N=addcore(G,x);int c=pairmode?fullpaircharge(N,y):fullsinglecharge(N,y);if(c<=cap&&seen.insert(N).second)q.push_back(N);}}return {(int)q.size(),mx};}
int cardinal_high(u64 G,const vector<int>&supp,const vector<int>&tv){int mx[64]={0};u64 b=G;vector<int>zs;while(b){int z=__builtin_ctzll(b);b&=b-1;zs.push_back(z);}for(size_t i=0;i<supp.size();i++)for(int z:zs)mx[supp[i]|z]=max(mx[supp[i]|z],tv[i]);int total=0;for(int w=0;w<64;w++){int s=__builtin_popcount((unsigned)w);if(s<4)continue;int k=mx[w];if(G>>w&1ULL)k=max(3,k+(k?1:0));total+=(2*s-6)*k;}int kt=mx[63];if(G>>63&1ULL)kt=max(3,kt+(kt?1:0));if(kt==0)total+=6;return total;}
int main(){
 for(int a=0;a<256;a++)for(int b=0;b<256;b++){int o=0;for(int r=0;r<8;r++)if(a>>r&1)for(int q=0;q<8;q++)if(b>>q&1)o|=1<<(r|q);JN[a][b]=o;}
 vector<TT>S,P; map<pair<int,int>,vector<TT>> SG,PG;
 for(int m=0;m<256;m++)if((m>>7&1)&&uc(m)){int t=__builtin_popcount((unsigned)m),sum=0;for(int r=0;r<8;r++)if(m>>r&1)sum+=__builtin_popcount((unsigned)r);int d=3*t-2*sum;bool sOK=true,pOK=true;for(int r=0;r<8;r++)if(m>>r&1){if(__builtin_popcount((unsigned)r)<2)sOK=false;if(__builtin_popcount((unsigned)r)<1)pOK=false;}if(sOK&&t<4){TT z{(uint8_t)m,t,d};S.push_back(z);SG[{t,d}].push_back(z);}if(pOK&&t<7){TT z{(uint8_t)m,t,d};P.push_back(z);PG[{t,d}].push_back(z);}}
 vector<pair<int,int>> SK,PK;for(auto &x:SG)SK.push_back(x.first);for(auto &x:PG)PK.push_back(x.first);
 for(int x=1;x<64;x++)if(__builtin_popcount((unsigned)x)>=3){cores.push_back(x);coreMask|=1ULL<<x;}
 auto fp=restricted_cap(83,0b11,true); auto fs=restricted_cap(89,0b1,false);
 if(fp.second>=14||fs.second>=17){cerr<<"full cap failure\n";return 2;}
 unordered_set<u64> seen;seen.reserve(500000);vector<u64>q{1};seen.insert(1);for(size_t h=0;h<q.size();h++){u64 G=q[h];for(int x:cores)if(!(G>>x&1ULL)){u64 N=addcore(G,x);if(Hcharge(N)<=66&&seen.insert(N).second)q.push_back(N);}}
 vector<int> pc(q.size()),hc(q.size());for(size_t i=0;i<q.size();i++){pc[i]=__builtin_popcountll(q[i]&coreMask);hc[i]=Hcharge(q[i]);}
 map<pair<int,int>,vector<int>> cache;
 auto cand=[&](int pr,int need)->vector<int>&{auto key=make_pair(pr,need);auto it=cache.find(key);if(it!=cache.end())return it->second;vector<int>v;for(int i=0;i<(int)q.size();i++)if(pc[i]>=pr&&hc[i]<need)v.push_back(i);return cache.emplace(key,move(v)).first->second;};
 auto PP=perms6();set<vector<int>> orbitset;vector<int>singles;for(int i=0;i<6;i++)singles.push_back(1<<i);vector<int>pairs;for(int x=0;x<64;x++)if(__builtin_popcount((unsigned)x)==2)pairs.push_back(x);
 for(int a=0;a<=2;a++){vector<vector<int>>As;vector<int>ia(a);function<void(int,int)>ra=[&](int st,int dep){if(dep==a){vector<int>v;for(int i:ia)v.push_back(singles[i]);As.push_back(v);return;}for(int i=st;i<=6-(a-dep);i++){ia[dep]=i;ra(i+1,dep+1);}};ra(0,0);for(auto A:As){set<int>req;for(size_t i=0;i<A.size();i++)for(size_t j=i+1;j<A.size();j++)req.insert(A[i]|A[j]);int e=5-a;vector<int>ie(e);function<void(int,int)>re=[&](int st,int dep){if(dep==e){vector<int>E;for(int i:ie)E.push_back(pairs[i]);for(int r:req)if(find(E.begin(),E.end(),r)==E.end())return;vector<int>M=A;M.insert(M.end(),E.begin(),E.end());orbitset.insert(canon(M,PP));return;}for(int i=st;i<=(int)pairs.size()-(e-dep);i++){ie[dep]=i;re(i+1,dep+1);}};re(0,0);}}
 vector<vector<int>>orbits(orbitset.begin(),orbitset.end());
 long long summaryAssignments=0,coarseClosed=0,cardinalityChecks=0;int minMargin=INT_MAX;string witness="";int orbitIndex=0;
 for(auto M:orbits){orbitIndex++;vector<int>choice(5);int ns=0;for(int x:M)if(__builtin_popcount((unsigned)x)==1)ns++;
  function<void(int)> rec=[&](int pos){if(pos==5){summaryAssignments++;int dsum=0,need=12;vector<int>tv(5);for(int i=0;i<5;i++){bool isS=__builtin_popcount((unsigned)M[i])==1;auto td=isS?SK[choice[i]]:PK[choice[i]];tv[i]=td.first;dsum+=td.second;need+=(isS?4:2)*td.first;}int pr=3-dsum;auto &cv=cand(pr,need);if(cv.empty()){coarseClosed++;return;}int mn=INT_MAX;for(int qi:cv)mn=min(mn,cardinal_high(q[qi],M,tv));cardinalityChecks++;minMargin=min(minMargin,mn-need);if(mn<need&&witness.empty()){witness="orbit="+to_string(orbitIndex)+" ns="+to_string(ns)+" pr="+to_string(pr)+" need="+to_string(need)+" mn="+to_string(mn);}return;}bool isS=__builtin_popcount((unsigned)M[pos])==1;int n=isS?SK.size():PK.size();for(int k=0;k<n;k++){choice[pos]=k;rec(pos+1);if(!witness.empty())return;}};
  rec(0);if(!witness.empty())break;
 }
 cout<<"{\n\"support_orbits\":"<<orbits.size()<<",\n\"low_charge_states\":"<<q.size()<<",\n\"summary_assignments\":"<<summaryAssignments<<",\n\"coarse_closed\":"<<coarseClosed<<",\n\"cardinality_checks\":"<<cardinalityChecks<<",\n\"minimum_cardinality_margin\":"<<(minMargin==INT_MAX?999:minMargin)<<",\n\"counterexample_class\":\""<<witness<<"\",\n\"all_checks_passed\":"<<(witness.empty()?"true":"false")<<"\n}\n";
 return witness.empty()?0:1;
}
