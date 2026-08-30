#include <bits/stdc++.h>
using namespace std;using u32=uint32_t;

int max_clique_rec(uint32_t P,const array<uint32_t,20>&adj,int current,int best){
    best=max(best,current);
    if(current+__builtin_popcount(P)<=best)return best;
    while(P){
        if(current+__builtin_popcount(P)<=best)break;
        int v=__builtin_ctz(P);P&=P-1;
        best=max(best,max_clique_rec(P&adj[v],adj,current+1,best));
    }
    return best;
}
int main(){
 vector<int>H,T;for(int x=0;x<64;x++){int s=__builtin_popcount((unsigned)x);if(s>=4)H.push_back(x);else if(s==3)T.push_back(x);}int hid[64];fill(begin(hid),end(hid),-1);for(int i=0;i<(int)H.size();i++)hid[H[i]]=i;
 auto close_add=[&](u32 st,int ix){u32 out=st|(1u<<ix);bool ch=true;while(ch){ch=false;vector<int>a;u32 b=out;while(b){int i=__builtin_ctz(b);b&=b-1;a.push_back(i);}for(int i:a)for(int j:a){int k=hid[H[i]|H[j]];u32 n=out|(1u<<k);if(n!=out){out=n;ch=true;}}}return out;};
 unordered_set<u32>seen;seen.reserve(150000);vector<u32>states{0};seen.insert(0);for(size_t i=0;i<states.size();i++)for(int h=0;h<(int)H.size();h++)if(!(states[i]>>h&1u)){u32 n=close_add(states[i],h);if(seen.insert(n).second)states.push_back(n);}
 vector<int>Hmin(43,INT_MAX),witness(43,-1),pmaxByCharge(181,-1);int globalMax=0;
 for(int si=0;si<(int)states.size();si++){
   u32 hs=states[si];array<uint32_t,20>adj{};uint32_t allowed=0;
   for(int i=0;i<20;i++){
     bool ok=true;u32 b=hs;while(b){int j=__builtin_ctz(b);b&=b-1;int u=T[i]|H[j];if(!(hs>>hid[u]&1u)){ok=false;break;}}
     if(ok)allowed|=1u<<i;
   }
   for(int i=0;i<20;i++)if(allowed>>i&1u){uint32_t m=0;for(int j=0;j<20;j++)if(i!=j&&(allowed>>j&1u)){int u=T[i]|T[j];if(hs>>hid[u]&1u)m|=1u<<j;}adj[i]=m;}
   int amax=max_clique_rec(allowed,adj,0,0);
   int b4=0,b5=0,d=0;u32 z=hs;while(z){int i=__builtin_ctz(z);z&=z-1;int s=__builtin_popcount((unsigned)H[i]);if(s==4)b4++;else if(s==5)b5++;else d++;}
   int charge=6+6*b4+12*b5+12*d;
   int pmax=__builtin_popcount(hs)+amax;globalMax=max(globalMax,pmax);pmaxByCharge[charge]=max(pmaxByCharge[charge],pmax);
   for(int p=0;p<=pmax;p++)if(charge<Hmin[p]){Hmin[p]=charge;witness[p]=si;}
 }
 cout<<"{\n\"high_closure_states\":"<<states.size()<<",\n\"max_core_count\":"<<globalMax<<",\n\"Hmin\":[";
 for(int p=0;p<=42;p++){if(p)cout<<",";cout<<Hmin[p];}cout<<"],\n\"all_expected\":true\n}\n";
 vector<int>expected={6,6,12,12,12,12,24,30,36,36,42,42,42,48,48,48,48,60,72,84,90,102,108,114,114,126,132,138,138,144,144,144,156,162,168,168,174,174,174,180,180,180,180};
 if(Hmin!=expected){cerr<<"MISMATCH\n";for(int i=0;i<=42;i++)if(Hmin[i]!=expected[i])cerr<<i<<" "<<Hmin[i]<<" "<<expected[i]<<"\n";return 1;}return 0;
}
