#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

struct Geometry {
    std::string name;
    int y1;
    int y2;
    int t1_max;
    int t2_max;
    int penalty1;
    int penalty2;
    int threshold;
    std::array<int,7> witness;
    int witness_t1;
    int witness_t2;
    int expected_margin;
};

static std::vector<int> cores;
static Geometry geom;
static std::array<unsigned long long,8> nodes{};
static std::array<unsigned long long,8> pruned{};
static std::array<int,7> chosen{};
static bool found_below = false;
static int found_margin = 0;
static std::array<int,7> found_cores{};
static int found_t1 = 0, found_t2 = 0;

inline uint64_t add_core(uint64_t G, int c) {
    uint64_t old = G;
    uint64_t result = G;
    while (old) {
        unsigned bit = __builtin_ctzll(old);
        old &= old - 1;
        result |= (uint64_t(1) << (bit | c));
    }
    return result;
}

inline uint64_t translate(uint64_t G, int y) {
    uint64_t result = 0;
    while (G) {
        unsigned bit = __builtin_ctzll(G);
        G &= G - 1;
        result |= (uint64_t(1) << (bit | y));
    }
    return result;
}

struct MarginResult { int margin; int t1; int t2; };

inline MarginResult worst_margin(uint64_t G) {
    uint64_t s1 = translate(G, geom.y1);
    uint64_t s2 = translate(G, geom.y2);
    int best = 1'000'000;
    int bt1 = 0, bt2 = 0;
    for (int t1 = 1; t1 <= geom.t1_max; ++t1) {
        for (int t2 = 1; t2 <= geom.t2_max; ++t2) {
            int total = (((G | s1 | s2) >> 63) & 1ULL) ? 0 : 6;
            for (int w = 0; w < 64; ++w) {
                int pc = __builtin_popcount((unsigned)w);
                if (pc < 4) continue;
                int mult = 0;
                if ((G >> w) & 1ULL) mult = std::max(mult, 3);
                if ((s1 >> w) & 1ULL) mult = std::max(mult, t1);
                if ((s2 >> w) & 1ULL) mult = std::max(mult, t2);
                total += mult * (2 * pc - 6);
            }
            int margin = total - 12 - geom.penalty1 * t1 - geom.penalty2 * t2;
            if (margin < best) {
                best = margin; bt1 = t1; bt2 = t2;
            }
        }
    }
    return {best, bt1, bt2};
}

void dfs(int start, int depth, uint64_t G) {
    if (found_below) return;
    nodes[depth]++;
    auto m = worst_margin(G);
    if (m.margin >= geom.threshold) {
        pruned[depth]++;
        return;
    }
    if (depth == 7) {
        found_below = true;
        found_margin = m.margin;
        found_t1 = m.t1;
        found_t2 = m.t2;
        found_cores = chosen;
        return;
    }
    int need = 7 - depth;
    int last = int(cores.size()) - need;
    for (int i = start; i <= last; ++i) {
        chosen[depth] = cores[i];
        dfs(i + 1, depth + 1, add_core(G, cores[i]));
        if (found_below) return;
    }
}

uint64_t closure_of(const std::array<int,7>& C) {
    uint64_t G = 1ULL;
    for (int c : C) G = add_core(G, c);
    return G;
}

void run_geometry(const Geometry& g) {
    geom = g;
    nodes.fill(0); pruned.fill(0);
    found_below = false;
    dfs(0, 0, 1ULL);
    auto witness_result = worst_margin(closure_of(g.witness));

    std::cout << "{\n";
    std::cout << "  \"geometry\": \"" << g.name << "\",\n";
    std::cout << "  \"negative_below_threshold_found\": " << (found_below ? "true" : "false") << ",\n";
    std::cout << "  \"threshold\": " << g.threshold << ",\n";
    std::cout << "  \"certified_lower_bound\": " << g.threshold << ",\n";
    std::cout << "  \"witness_margin\": " << witness_result.margin << ",\n";
    std::cout << "  \"witness_t\": [" << witness_result.t1 << ", " << witness_result.t2 << "],\n";
    std::cout << "  \"witness_cores\": [";
    for (int i = 0; i < 7; ++i) {
        if (i) std::cout << ", ";
        std::cout << g.witness[i];
    }
    std::cout << "],\n";
    std::cout << "  \"nodes_by_depth\": [";
    for (int i = 0; i <= 7; ++i) { if (i) std::cout << ", "; std::cout << nodes[i]; }
    std::cout << "],\n";
    std::cout << "  \"pruned_by_depth\": [";
    for (int i = 0; i <= 7; ++i) { if (i) std::cout << ", "; std::cout << pruned[i]; }
    std::cout << "]\n";
    std::cout << "}";

    if (found_below) {
        std::cerr << "unexpected counterexample below threshold for " << g.name << "\n";
        std::exit(2);
    }
    if (witness_result.margin != g.expected_margin) {
        std::cerr << "witness margin mismatch for " << g.name << ": got "
                  << witness_result.margin << " expected " << g.expected_margin << "\n";
        std::exit(3);
    }
}

int main() {
    for (int mask = 1; mask < 64; ++mask) {
        if (__builtin_popcount((unsigned)mask) >= 3) cores.push_back(mask);
    }
    std::sort(cores.begin(), cores.end(), [](int a, int b) {
        int pa = __builtin_popcount((unsigned)a), pb = __builtin_popcount((unsigned)b);
        if (pa != pb) return pa < pb;
        return a < b;
    });
    std::vector<Geometry> gs = {
        {"nested_singleton_pair", 1, 3, 4, 7, 4, 2, 0, {7,11,13,14,15,23,31}, 3,3,0},
        {"disjoint_singleton_pair", 1, 6, 4, 7, 4, 2, 0, {7,11,13,14,15,45,47}, 3,3,0},
        {"intersecting_pairs", 3, 5, 7, 7, 2, 2, 6, {7,11,13,14,15,23,31}, 3,3,6},
        {"disjoint_pairs", 3, 12, 7, 7, 2, 2, 6, {7,11,13,14,15,23,31}, 3,3,6}
    };
    std::cout << "{\n  \"schema_version\": 1,\n  \"core_count\": " << cores.size() << ",\n  \"selected_positive_cores\": 7,\n  \"results\": [\n";
    for (size_t i = 0; i < gs.size(); ++i) {
        run_geometry(gs[i]);
        std::cout << (i + 1 == gs.size() ? "\n" : ",\n");
    }
    std::cout << "  ],\n  \"status\": \"PASS\"\n}\n";
    return 0;
}
