#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using U64 = std::uint64_t;

struct Orbit {
    std::string name;
    std::array<int, 3> small_parts;
    int expected_minimum;
    std::vector<int> witness_cores;
};

static std::vector<int> positive_cores;

inline U64 add_core(U64 closure, int core) {
    U64 remaining = closure;
    U64 result = closure;
    while (remaining) {
        int outside = std::countr_zero(remaining);
        remaining &= remaining - 1;
        result |= U64(1) << (outside | core);
    }
    return result;
}

inline U64 translate(U64 closure, int small_part) {
    U64 result = 0;
    while (closure) {
        int outside = std::countr_zero(closure);
        closure &= closure - 1;
        result |= U64(1) << (outside | small_part);
    }
    return result;
}

class Verifier {
public:
    explicit Verifier(const Orbit& orbit) : orbit_(orbit) {
        int singleton_count = 0;
        for (int part : orbit_.small_parts) {
            bool singleton = std::popcount(static_cast<unsigned>(part)) == 1;
            singleton_count += singleton;
            maxima_.push_back(singleton ? 4 : 7);
            penalties_.push_back(singleton ? 4 : 2);
        }
        int pair_count = 3 - singleton_count;
        selected_ = 3 + 3 * singleton_count + 2 * pair_count;
        if (static_cast<int>(orbit_.witness_cores.size()) != selected_) {
            std::cerr << "witness-size mismatch\n";
            std::exit(10);
        }
        chosen_.resize(selected_);
        nodes_.assign(selected_ + 1, 0);
        pruned_.assign(selected_ + 1, 0);
        make_trace_sizes(0, {});
    }

    void run() {
        int witness = worst_margin(closure_of(orbit_.witness_cores));
        if (witness != orbit_.expected_minimum) {
            std::cerr << "witness margin mismatch for " << orbit_.name << "\n";
            std::exit(11);
        }
        dfs(0, 0, U64(1));
        if (counterexample_) {
            std::cerr << "counterexample below threshold for " << orbit_.name << "\n";
            std::exit(12);
        }
        std::cout << "{\n";
        std::cout << "  \"orbit\": \"" << orbit_.name << "\",\n";
        std::cout << "  \"small_parts\": [" << orbit_.small_parts[0] << ", "
                  << orbit_.small_parts[1] << ", " << orbit_.small_parts[2]
                  << "],\n";
        std::cout << "  \"selected_positive_cores\": " << selected_ << ",\n";
        std::cout << "  \"exact_minimum\": " << orbit_.expected_minimum << ",\n";
        std::cout << "  \"counterexample_below_minimum\": null,\n";
        std::cout << "  \"witness_cores\": [";
        for (std::size_t i = 0; i < orbit_.witness_cores.size(); ++i) {
            if (i) std::cout << ", ";
            std::cout << orbit_.witness_cores[i];
        }
        std::cout << "],\n  \"nodes_by_depth\": [";
        for (std::size_t i = 0; i < nodes_.size(); ++i) {
            if (i) std::cout << ", ";
            std::cout << nodes_[i];
        }
        std::cout << "],\n  \"pruned_by_depth\": [";
        for (std::size_t i = 0; i < pruned_.size(); ++i) {
            if (i) std::cout << ", ";
            std::cout << pruned_[i];
        }
        std::cout << "],\n  \"status\": \"PASS\"\n}";
    }

private:
    const Orbit& orbit_;
    int selected_ = 0;
    std::vector<int> maxima_;
    std::vector<int> penalties_;
    std::vector<std::array<int, 3>> trace_sizes_;
    std::unordered_map<U64, int> margin_cache_;
    std::vector<int> chosen_;
    std::vector<unsigned long long> nodes_;
    std::vector<unsigned long long> pruned_;
    bool counterexample_ = false;

    void make_trace_sizes(int index, std::array<int, 3> values) {
        if (index == 3) {
            trace_sizes_.push_back(values);
            return;
        }
        for (int value = 1; value <= maxima_[index]; ++value) {
            values[index] = value;
            make_trace_sizes(index + 1, values);
        }
    }

    U64 closure_of(const std::vector<int>& cores) const {
        U64 closure = 1;
        for (int core : cores) closure = add_core(closure, core);
        return closure;
    }

    int worst_margin(U64 closure) {
        auto found = margin_cache_.find(closure);
        if (found != margin_cache_.end()) return found->second;
        std::array<U64, 3> translated{};
        U64 generated = closure;
        for (int i = 0; i < 3; ++i) {
            translated[i] = translate(closure, orbit_.small_parts[i]);
            generated |= translated[i];
        }
        int weights[2][8]{};
        for (int outside = 0; outside < 64; ++outside) {
            int outside_size = std::popcount(static_cast<unsigned>(outside));
            if (outside_size < 4) continue;
            int mask = 0;
            for (int i = 0; i < 3; ++i) {
                if ((translated[i] >> outside) & 1) mask |= 1 << i;
            }
            int base = (closure >> outside) & 1;
            if (base || mask) weights[base][mask] += 2 * outside_size - 6;
        }
        int top_bonus = ((generated >> 63) & 1) ? 0 : 6;
        int best = 1'000'000;
        for (const auto& sizes : trace_sizes_) {
            int value = top_bonus - 12;
            for (int i = 0; i < 3; ++i) value -= penalties_[i] * sizes[i];
            for (int base = 0; base < 2; ++base) {
                for (int mask = 0; mask < 8; ++mask) {
                    int multiplicity = base ? 3 : 0;
                    for (int i = 0; i < 3; ++i) {
                        if ((mask >> i) & 1) {
                            multiplicity = std::max(multiplicity, sizes[i]);
                        }
                    }
                    value += weights[base][mask] * multiplicity;
                }
            }
            best = std::min(best, value);
        }
        margin_cache_[closure] = best;
        return best;
    }

    void dfs(int start, int depth, U64 closure) {
        if (counterexample_) return;
        nodes_[depth]++;
        int current = worst_margin(closure);
        if (current >= orbit_.expected_minimum) {
            pruned_[depth]++;
            return;
        }
        if (depth == selected_) {
            counterexample_ = true;
            return;
        }
        int need = selected_ - depth;
        int last = static_cast<int>(positive_cores.size()) - need;
        for (int index = start; index <= last; ++index) {
            int core = positive_cores[index];
            U64 child = add_core(closure, core);
            if (worst_margin(child) < current) {
                std::cerr << "monotonicity regression\n";
                std::exit(13);
            }
            chosen_[depth] = core;
            dfs(index + 1, depth + 1, child);
            if (counterexample_) return;
        }
    }
};

int main() {
    for (int mask = 1; mask < 64; ++mask) {
        if (std::popcount(static_cast<unsigned>(mask)) >= 3) {
            positive_cores.push_back(mask);
        }
    }
    std::sort(
        positive_cores.begin(), positive_cores.end(),
        [](int left, int right) {
            int a = std::popcount(static_cast<unsigned>(left));
            int b = std::popcount(static_cast<unsigned>(right));
            return a == b ? left < right : a < b;
        }
    );

    const std::vector<Orbit> orbits = {
        {"O01", {1,2,3}, 0, {7,11,13,14,19,21,25,15,23,27,29}},
        {"O02", {1,3,5}, 6, {7,11,13,14,19,21,25,15,23,27}},
        {"O03", {1,3,6}, 6, {7,11,13,14,19,21,25,15,23,27}},
        {"O04", {1,3,12}, 6, {7,11,13,14,19,21,25,15,23,27}},
        {"O05", {1,6,10}, 6, {7,11,13,14,19,21,25,15,23,27}},
        {"O06", {1,6,24}, 6, {7,11,13,14,25,26,28,15,27,29}},
        {"O07", {3,5,6}, 6, {7,11,13,14,19,15,23,27,31}},
        {"O08", {3,5,9}, 6, {7,11,13,14,19,15,23,27,31}},
        {"O09", {3,5,10}, 6, {7,11,13,14,19,15,23,27,31}},
        {"O10", {3,5,24}, 6, {7,11,13,25,26,15,27,29,31}},
        {"O11", {3,12,48}, 24, {7,11,52,56,15,60,55,59,63}},
    };

    std::cout << "{\n  \"schema_version\": 1,\n  \"orbit_count\": "
              << orbits.size() << ",\n  \"results\": [\n";
    for (std::size_t index = 0; index < orbits.size(); ++index) {
        Verifier verifier(orbits[index]);
        verifier.run();
        std::cout << (index + 1 == orbits.size() ? "\n" : ",\n");
    }
    std::cout
        << "  ],\n"
        << "  \"exact_minima\": [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 24],\n"
        << "  \"status\": \"PASS\",\n"
        << "  \"new_residual\": \"at least four small outside parts\"\n"
        << "}\n";
    return 0;
}
