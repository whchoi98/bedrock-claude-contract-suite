#!/usr/bin/env bash
# verify.sh — interactive launcher for the Bedrock × Anthropic API verification suite.
#
# Run with no arguments for the interactive menu. Direct invocations:
#   ./verify.sh all                     run every test
#   ./verify.sh category caching tools  run named categories
#   ./verify.sh test cache_ttl_1h ...   run named tests
#   ./verify.sh list                    print test inventory and exit
#   ./verify.sh open                    open results/latest.md
#   ./verify.sh -h                      help
#
# Reads:  AWS_BEARER_TOKEN_BEDROCK (required), AWS_REGION, BEDROCK_MODEL_ID
# Writes: results/latest.json, results/latest.md
#
# ─── Token / cost notice (measured 2026-05-03 in ap-northeast-2) ────────────
# A single full matrix run (all 3 models × 57 tests = ~176 messages.create
# calls) consumes approximately:
#
#   Per-model token totals (input | output | 5m create | 1h create | reads):
#     Opus 4.7    : 284K |  2K | 99K | 27K | 126K   (~536K billable input)
#     Opus 4.6    : 208K |  2K | 57K | 15K |  72K   (~352K billable input)
#     Sonnet 4.6  : 206K |  2K | 57K | 15K |  72K   (~351K billable input)
#     Matrix total: 698K |  6K | 213K| 57K | 271K   (~1.24M billable input)
#
#   Approximate USD cost per matrix run (input only, public Bedrock pricing
#   per https://platform.claude.com/docs/en/build-with-claude/prompt-caching
#   and Anthropic model pricing tables):
#     Opus 4.7    : ~$2.40
#     Opus 4.6    : ~$1.60
#     Sonnet 4.6  : ~$0.95
#     Matrix run  : ~$5.00 USD total
#
#   Single-model run (one of ALL_MODELS, 57 tests, ~60 calls): ~$0.95 - $2.40
#   depending on model. Output tokens (~2K per model) are negligible.
#
# `python3 run_all.py [--all-models]` prints a measured token summary at the
# end of every run; the numbers above are anchor estimates only. Streaming
# tests (`tests/streaming/*`) call `messages.stream()` rather than
# `messages.create()`, so their ~15 calls are not included in the live
# summary — those add a negligible <1% to the totals shown.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

INVENTORY_CACHE="${TMPDIR:-/tmp}/.bedrock-opus-inventory.$$.json"
trap 'rm -f "$INVENTORY_CACHE"' EXIT

# ─── Colors ─────────────────────────────────────────────────────────────────
if [[ -t 1 ]] && command -v tput &>/dev/null && [[ -n "${TERM:-}" ]] && [[ "${TERM}" != "dumb" ]]; then
    BOLD=$(tput bold); DIM=$(tput dim)
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4); MAGENTA=$(tput setaf 5); CYAN=$(tput setaf 6)
    RESET=$(tput sgr0)
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; MAGENTA=""; CYAN=""; RESET=""
fi

box() {
    local title="$1"
    local width=72
    local pad=$(( width - ${#title} - 4 ))
    printf '%s╔%s╗%s\n' "$BOLD" "$(printf '═%.0s' $(seq 1 $((width-2))))" "$RESET"
    printf '%s║ %s%s%s%*s ║%s\n' "$BOLD" "$CYAN" "$title" "$RESET$BOLD" "$pad" "" "$RESET"
    printf '%s╚%s╝%s\n' "$BOLD" "$(printf '═%.0s' $(seq 1 $((width-2))))" "$RESET"
}

hr() { printf '%s%s%s\n' "$DIM" "$(printf '─%.0s' $(seq 1 72))" "$RESET"; }

# ─── Pre-flight ─────────────────────────────────────────────────────────────
preflight() {
    if ! command -v python3 &>/dev/null; then
        echo "${RED}error: python3 not found${RESET}" >&2; exit 1
    fi
    if ! python3 -c "import anthropic" 2>/dev/null; then
        echo "${RED}error: anthropic SDK not installed (pip install anthropic)${RESET}" >&2; exit 1
    fi
}

mask_token() {
    local t="${1:-}"
    if [[ -z "$t" ]]; then
        printf '%snot set%s' "$RED" "$RESET"
    else
        local len=${#t}
        if (( len <= 12 )); then
            printf '%s****%s' "$DIM" "$RESET"
        else
            printf '%s%s…%s%s' "$DIM" "${t:0:6}" "${t: -4}" "$RESET"
        fi
    fi
}

prompt_token() {
    echo -n "Paste Bedrock API key (input hidden, Enter to keep current): "
    local new
    read -s new
    echo
    if [[ -n "$new" ]]; then
        export AWS_BEARER_TOKEN_BEDROCK="$new"
        echo "${GREEN}✓ API key updated for this session.${RESET}"
    else
        echo "${DIM}(unchanged)${RESET}"
    fi
}

prompt_model() {
    local current="${BEDROCK_MODEL_ID:-global.anthropic.claude-opus-4-7}"
    echo "Available model IDs:"
    printf '  %s1)%s %sOpus 4.7%s    %sglobal.anthropic.claude-opus-4-7%s    %s(default)%s\n' \
        "$BOLD" "$RESET" "$BOLD" "$RESET" "$CYAN" "$RESET" "$DIM" "$RESET"
    printf '  %s2)%s %sOpus 4.6%s    %sglobal.anthropic.claude-opus-4-6-v1%s\n' \
        "$BOLD" "$RESET" "$BOLD" "$RESET" "$CYAN" "$RESET"
    printf '  %s3)%s %sSonnet 4.6%s  %sglobal.anthropic.claude-sonnet-4-6%s\n' \
        "$BOLD" "$RESET" "$BOLD" "$RESET" "$CYAN" "$RESET"
    printf '  %s4)%s custom (paste an inference-profile-prefixed ID)\n\n' "$BOLD" "$RESET"
    echo -n "Choose 1-4 (Enter to keep '${current}'): "
    local pick
    read -r pick
    case "$pick" in
        1) export BEDROCK_MODEL_ID="global.anthropic.claude-opus-4-7" ;;
        2) export BEDROCK_MODEL_ID="global.anthropic.claude-opus-4-6-v1" ;;
        3) export BEDROCK_MODEL_ID="global.anthropic.claude-sonnet-4-6" ;;
        4)
            echo -n "Custom model ID > "
            local custom; read -r custom
            [[ -n "$custom" ]] && export BEDROCK_MODEL_ID="$custom"
            ;;
        "") : ;;
        *) printf '%sinvalid choice — keeping current%s\n' "$YELLOW" "$RESET" ;;
    esac
    if [[ -n "${BEDROCK_MODEL_ID:-}" ]]; then
        echo "${GREEN}✓ Model: ${BEDROCK_MODEL_ID}${RESET}"
    fi
    rm -f "$INVENTORY_CACHE"  # model name shown in inventory header should refresh
}

prompt_region() {
    local current="${AWS_REGION:-ap-northeast-2}"
    echo "Common regions:"
    printf '  %s1)%s ap-northeast-2 (Seoul) %s(default)%s\n' "$BOLD" "$RESET" "$DIM" "$RESET"
    printf '  %s2)%s us-west-2  (Oregon)\n' "$BOLD" "$RESET"
    printf '  %s3)%s us-east-1  (N. Virginia)\n' "$BOLD" "$RESET"
    printf '  %s4)%s us-east-2  (Ohio)\n' "$BOLD" "$RESET"
    printf '  %s5)%s custom\n\n' "$BOLD" "$RESET"
    echo -n "Choose 1-5 (Enter to keep '${current}'): "
    local pick
    read -r pick
    case "$pick" in
        1) export AWS_REGION="ap-northeast-2" ;;
        2) export AWS_REGION="us-west-2" ;;
        3) export AWS_REGION="us-east-1" ;;
        4) export AWS_REGION="us-east-2" ;;
        5)
            echo -n "Custom region > "
            local custom; read -r custom
            [[ -n "$custom" ]] && export AWS_REGION="$custom"
            ;;
        "") : ;;
        *) printf '%sinvalid choice — keeping current%s\n' "$YELLOW" "$RESET" ;;
    esac
    rm -f "$INVENTORY_CACHE"
}

ensure_token() {
    # Called before every test run. Auto-prompts when missing.
    if [[ -z "${AWS_BEARER_TOKEN_BEDROCK:-}" ]]; then
        echo "${YELLOW}AWS_BEARER_TOKEN_BEDROCK is not set.${RESET}"
        prompt_token
        if [[ -z "${AWS_BEARER_TOKEN_BEDROCK:-}" ]]; then
            echo "${RED}no token provided — aborting.${RESET}" >&2; exit 1
        fi
    fi
}

# ─── Inventory loader (caches once) ─────────────────────────────────────────
load_inventory() {
    if [[ ! -s "$INVENTORY_CACHE" ]]; then
        AWS_BEARER_TOKEN_BEDROCK="${AWS_BEARER_TOKEN_BEDROCK:-dummy}" \
            python3 run_all.py --list-json > "$INVENTORY_CACHE"
    fi
}

inventory_field() {  # path: e.g. .model
    python3 -c "import json,sys; d=json.load(open('$INVENTORY_CACHE')); print(d['$1'])"
}

categories() {
    python3 -c "
import json
d = json.load(open('$INVENTORY_CACHE'))
for c in d['categories']:
    print(f\"{c['name']}\t{c['count']}\")
"
}

tests_in_category() {
    python3 -c "
import json, sys
d = json.load(open('$INVENTORY_CACHE'))
for c in d['categories']:
    if c['name'] == '$1':
        for t in c['tests']:
            print(f\"{t['name']}\t{t['description']}\")
        break
"
}

all_categories_array() {
    python3 -c "
import json
d = json.load(open('$INVENTORY_CACHE'))
print(' '.join(c['name'] for c in d['categories']))
"
}

# ─── Pretty inventory printer ───────────────────────────────────────────────
print_inventory() {
    load_inventory
    local model region totals
    model=$(inventory_field model)
    region=$(inventory_field region)
    totals=$(inventory_field totals)
    box "Test inventory  ·  $totals tests"
    printf '  %sModel:%s  %s\n' "$DIM" "$RESET" "$model"
    printf '  %sRegion:%s %s\n\n' "$DIM" "$RESET" "$region"
    while IFS=$'\t' read -r cat count; do
        printf '%s● %s%s%s %s(%d tests)%s\n' "$CYAN" "$BOLD" "$cat" "$RESET" "$DIM" "$count" "$RESET"
        while IFS=$'\t' read -r name desc; do
            printf '    %s%-40s%s %s%s%s\n' "$GREEN" "$name" "$RESET" "$DIM" "$desc" "$RESET"
        done < <(tests_in_category "$cat")
        echo
    done < <(categories)
}

# ─── Run wrappers ───────────────────────────────────────────────────────────
print_cost_notice_single() {
    printf "${DIM}Token cost (measured 2026-05-03, single-model run, 57 tests, ~60 calls):${RESET}\n"
    printf "${DIM}  ~280K-340K total billable input tokens, ~2K output.${RESET}\n"
    printf "${DIM}  Approx USD: ~\$0.95 (Sonnet 4.6) | ~\$1.60 (Opus 4.6) | ~\$2.40 (Opus 4.7).${RESET}\n"
    printf "${DIM}  Per-call summary printed at end of run.${RESET}\n"
}

print_cost_notice_matrix() {
    printf "${DIM}Token cost (measured 2026-05-03, full matrix, 3 models × 57 tests, ~176 calls):${RESET}\n"
    printf "${DIM}  ~1.24M total billable input tokens, ~6K output.${RESET}\n"
    printf "${DIM}  Approx USD: ~\$5.00 total (Opus 4.7 \$2.40 + Opus 4.6 \$1.60 + Sonnet 4.6 \$0.95).${RESET}\n"
    printf "${DIM}  Per-model + matrix-wide summary printed at end of run.${RESET}\n"
    printf "${DIM}NOTE: Running matrix mode with both providers (--providers bedrock cpaws)${RESET}\n"
    printf "${DIM}  charges BOTH bills:${RESET}\n"
    printf "${DIM}    - Bedrock         → standard Bedrock invoke pricing${RESET}\n"
    printf "${DIM}    - Claude Platform → AWS Marketplace subscription pricing${RESET}\n"
    printf "${DIM}  A full matrix is ~2x the single-provider cost.${RESET}\n"
}

run_all_tests() {
    ensure_token
    box "Running ALL tests"
    print_cost_notice_single
    echo
    python3 run_all.py
    show_results_paths
}

run_matrix() {
    ensure_token
    # CPaws credentials check — warns only; does not block.
    if [ -z "${ANTHROPIC_AWS_API_KEY:-}" ] || [ -z "${ANTHROPIC_AWS_WORKSPACE_ID:-}" ]; then
        printf "${YELLOW}WARNING: ANTHROPIC_AWS_API_KEY or ANTHROPIC_AWS_WORKSPACE_ID is not set.${RESET}\n"
        printf "${YELLOW}         Claude Platform on AWS (CPaws) runs will fail if --providers cpaws is used.${RESET}\n"
        printf "${YELLOW}         CPaws billing is via AWS Marketplace, separate from Bedrock.${RESET}\n"
        echo
    fi
    local models
    models=$(python3 -c "from config import ALL_MODELS; print('\n'.join(ALL_MODELS))")
    box "Run across ALL models (matrix)"
    echo "Models that will be tested:"
    while IFS= read -r m; do
        printf '  %s•%s %s\n' "$CYAN" "$RESET" "$m"
    done <<< "$models"
    echo
    print_cost_notice_matrix
    echo
    printf "${YELLOW}This runs the full suite once per model (≈3× time/cost).${RESET}\n"
    echo -n "Continue? [y/N] "
    local c; read -r c
    if [[ ! "$c" =~ ^[yY] ]]; then
        echo "${DIM}cancelled${RESET}"
        return 0
    fi
    python3 run_all.py --all-models
    show_matrix_results_paths
}

show_matrix_results_paths() {
    echo
    hr
    if [[ -f results/matrix.md ]]; then
        printf '%sMatrix results%s\n' "$BOLD" "$RESET"
        printf '  %s%s\n' "$DIM" "results/matrix.md"
        printf '  %s%s\n' "results/matrix.json"
        printf "${RESET}"
    fi
}

run_categories() {  # $@ are category names
    ensure_token
    box "Running categories: $*"
    python3 run_all.py --only "$@"
    show_results_paths
}

run_tests() {  # $@ are test names
    ensure_token
    box "Running tests: $*"
    python3 run_all.py --only-tests "$@"
    show_results_paths
}

show_results_paths() {
    echo
    hr
    if [[ -f results/latest.md ]]; then
        printf '%sResults%s\n' "$BOLD" "$RESET"
        printf '  %s%s\n' "$DIM" "results/latest.md"
        printf '  %s%s\n' "results/latest.json"
        printf "${RESET}"
    fi
}

# ─── Selection menus ────────────────────────────────────────────────────────
select_categories() {
    load_inventory
    local -a cats=()
    while IFS=$'\t' read -r cat count; do
        cats+=("$cat|$count")
    done < <(categories)

    box "Pick categories"
    local i=1
    for entry in "${cats[@]}"; do
        local name="${entry%|*}" count="${entry##*|}"
        # Show sample tests as preview
        local preview
        preview=$(tests_in_category "$name" | head -2 | awk -F$'\t' '{printf "%s, ", $1}' | sed 's/, $//')
        local more=""
        if (( count > 2 )); then more=" $DIM…+$((count-2))$RESET"; fi
        printf '  %s[%2d]%s %s%-15s%s %s%2d tests%s  %s%s%s%s\n' \
            "$BOLD" "$i" "$RESET" "$CYAN" "$name" "$RESET" "$DIM" "$count" "$RESET" \
            "$DIM" "$preview" "$RESET" "$more"
        ((i++))
    done
    printf '  %s[a]%s All categories\n' "$BOLD" "$RESET"
    printf '  %s[b]%s Back\n\n' "$BOLD" "$RESET"

    echo -n "Enter numbers (comma-separated, e.g. 1,3,5), 'a', or 'b': "
    local choice; read -r choice
    case "$choice" in
        a|A) run_categories $(all_categories_array) ;;
        b|B|"") return 0 ;;
        *)
            local -a names=()
            IFS=',' read -ra parts <<< "$choice"
            for p in "${parts[@]}"; do
                p=$(echo "$p" | tr -d '[:space:]')
                if [[ "$p" =~ ^[0-9]+$ ]] && (( p >= 1 && p <= ${#cats[@]} )); then
                    names+=("${cats[$((p-1))]%|*}")
                fi
            done
            if (( ${#names[@]} > 0 )); then
                run_categories "${names[@]}"
            else
                printf '%sno valid selection%s\n' "$RED" "$RESET"
            fi
            ;;
    esac
}

select_individual_tests() {
    load_inventory
    box "Pick a category to drill into"
    local -a cats=()
    while IFS=$'\t' read -r cat count; do
        cats+=("$cat")
    done < <(categories)
    local i=1
    for c in "${cats[@]}"; do
        printf '  %s[%2d]%s %s\n' "$BOLD" "$i" "$RESET" "$c"
        ((i++))
    done
    printf '  %s[b]%s Back\n\n' "$BOLD" "$RESET"
    echo -n "Choose category number: "
    local idx; read -r idx
    [[ "$idx" =~ ^[bB]$|^$ ]] && return 0
    [[ "$idx" =~ ^[0-9]+$ ]] || { printf '%sinvalid%s\n' "$RED" "$RESET"; return 0; }
    (( idx >= 1 && idx <= ${#cats[@]} )) || { printf '%sout of range%s\n' "$RED" "$RESET"; return 0; }
    local cat="${cats[$((idx-1))]}"

    box "Tests in '$cat'"
    local -a tnames=()
    local j=1
    while IFS=$'\t' read -r name desc; do
        tnames+=("$name")
        printf '  %s[%2d]%s %s%s%s\n      %s%s%s\n' \
            "$BOLD" "$j" "$RESET" "$GREEN" "$name" "$RESET" "$DIM" "$desc" "$RESET"
        ((j++))
    done < <(tests_in_category "$cat")
    printf '\n  %s[a]%s All tests in this category\n' "$BOLD" "$RESET"
    printf '  %s[b]%s Back\n\n' "$BOLD" "$RESET"

    echo -n "Enter numbers (e.g. 1,3,5), 'a', or 'b': "
    local choice; read -r choice
    case "$choice" in
        a|A) run_categories "$cat" ;;
        b|B|"") return 0 ;;
        *)
            local -a picks=()
            IFS=',' read -ra parts <<< "$choice"
            for p in "${parts[@]}"; do
                p=$(echo "$p" | tr -d '[:space:]')
                if [[ "$p" =~ ^[0-9]+$ ]] && (( p >= 1 && p <= ${#tnames[@]} )); then
                    picks+=("${tnames[$((p-1))]}")
                fi
            done
            if (( ${#picks[@]} > 0 )); then
                run_tests "${picks[@]}"
            else
                printf '%sno valid selection%s\n' "$RED" "$RESET"
            fi
            ;;
    esac
}

configure_runtime() {
    while true; do
        box "Configure runtime"
        printf '  %sBedrock API key%s : %s\n' "$DIM" "$RESET" "$(mask_token "${AWS_BEARER_TOKEN_BEDROCK:-}")"
        printf '  %sModel ID       %s : %s%s%s\n' "$DIM" "$RESET" "$CYAN" \
            "${BEDROCK_MODEL_ID:-global.anthropic.claude-opus-4-7}" "$RESET"
        printf '  %sAWS region     %s : %s%s%s\n\n' "$DIM" "$RESET" "$CYAN" \
            "${AWS_REGION:-ap-northeast-2}" "$RESET"
        printf '  %s[1]%s Set Bedrock API key\n' "$BOLD" "$RESET"
        printf '  %s[2]%s Set Model ID\n' "$BOLD" "$RESET"
        printf '  %s[3]%s Set AWS region\n' "$BOLD" "$RESET"
        printf '  %s[b]%s Back\n\n' "$BOLD" "$RESET"
        echo -n "Choice: "
        local c; read -r c
        case "$c" in
            1) prompt_token ;;
            2) prompt_model ;;
            3) prompt_region ;;
            b|B|"") return 0 ;;
            *) printf '%sinvalid choice%s\n' "$RED" "$RESET" ;;
        esac
        echo
    done
}

view_latest() {
    if [[ ! -f results/latest.md ]]; then
        printf '%sno latest results — run a single-model verification first%s\n' "$YELLOW" "$RESET"
        return 0
    fi
    if command -v less &>/dev/null; then
        less -R results/latest.md
    else
        cat results/latest.md
    fi
}

view_matrix() {
    if [[ ! -f results/matrix.md ]]; then
        printf '%sno matrix results — run "Run across ALL models" first%s\n' "$YELLOW" "$RESET"
        return 0
    fi
    if command -v less &>/dev/null; then
        less -R results/matrix.md
    else
        cat results/matrix.md
    fi
}

about() {
    box "About"
    cat <<EOF
${BOLD}Bedrock × Anthropic Messages API verification suite${RESET}

Verifies the Anthropic Messages API surface on Amazon Bedrock against the
official "Build with Claude" documentation.

  ${CYAN}Categories${RESET}    13 (messages, streaming, vision, documents, citations,
                tools, thinking, caching, context, multilingual, client,
                token_counting, unsupported)
  ${CYAN}Tests${RESET}         57 in total
  ${CYAN}Result kinds${RESET}  🟢 Supported   ⛔ Rejected   🟡 Mixed   ❌ Fail

  ${CYAN}Reports${RESET}       results/latest.json   results/latest.md

  ${CYAN}Reuse${RESET}         set BEDROCK_MODEL_ID to verify a future model
                without modifying any test code.

EOF
}

# ─── Main menu ──────────────────────────────────────────────────────────────
main_menu() {
    # First-run convenience: if no token, take the user straight to the key prompt.
    if [[ -z "${AWS_BEARER_TOKEN_BEDROCK:-}" ]]; then
        clear || true
        box "First-time setup"
        echo "${YELLOW}AWS_BEARER_TOKEN_BEDROCK is not set.${RESET}"
        echo "Bedrock authentication is required for every test run."
        echo
        prompt_token
        echo
        echo "${DIM}Tip: you can also set BEDROCK_MODEL_ID and AWS_REGION before launching"
        echo "this script to avoid re-entering them each session.${RESET}"
        sleep 1
    fi

    while true; do
        load_inventory
        local model region totals
        model=$(inventory_field model)
        region=$(inventory_field region)
        totals=$(inventory_field totals)
        clear || true
        box "Bedrock × Anthropic API Verification"
        printf '  %sAPI key:%s %s\n' "$DIM" "$RESET" "$(mask_token "${AWS_BEARER_TOKEN_BEDROCK:-}")"
        printf '  %sModel:%s   %s\n' "$DIM" "$RESET" "$model"
        printf '  %sRegion:%s  %s\n' "$DIM" "$RESET" "$region"
        printf '  %sTests:%s   %s\n\n' "$DIM" "$RESET" "$totals"

        printf '  %s[1]%s Run %sALL%s tests (%s)\n' "$BOLD" "$RESET" "$GREEN" "$RESET" "$totals"
        printf '  %s[2]%s Run by category\n' "$BOLD" "$RESET"
        printf '  %s[3]%s Run individual tests\n' "$BOLD" "$RESET"
        printf '  %s[4]%s View test inventory (no run)\n' "$BOLD" "$RESET"
        printf '  %s[5]%s Configure (key / model / region)\n' "$BOLD" "$RESET"
        printf '  %s[6]%s View latest results\n' "$BOLD" "$RESET"
        printf '  %s[7]%s About\n' "$BOLD" "$RESET"
        printf '  %s[8]%s Run %smatrix%s — across ALL models in config.ALL_MODELS\n' \
            "$BOLD" "$RESET" "$MAGENTA" "$RESET"
        printf '  %s[9]%s View matrix results\n' "$BOLD" "$RESET"
        printf '  %s[k]%s ↳ quick: set Bedrock API key\n' "$BOLD" "$RESET"
        printf '  %s[m]%s ↳ quick: set Model ID\n' "$BOLD" "$RESET"
        printf '  %s[q]%s Quit\n\n' "$BOLD" "$RESET"

        echo -n "Choice: "; local c; read -r c
        case "$c" in
            1) run_all_tests; pause ;;
            2) select_categories; pause ;;
            3) select_individual_tests; pause ;;
            4) print_inventory; pause ;;
            5) configure_runtime ;;
            6) view_latest ;;
            7) about; pause ;;
            8) run_matrix; pause ;;
            9) view_matrix ;;
            k|K) prompt_token; pause ;;
            m|M) prompt_model; pause ;;
            q|Q|"") echo "bye"; exit 0 ;;
            *) printf '%sinvalid choice%s\n' "$RED" "$RESET"; sleep 1 ;;
        esac
    done
}

pause() {
    echo
    echo -n "${DIM}Press Enter to continue…${RESET}"
    read -r _
}

usage() {
    cat <<EOF
Usage: $(basename "$0") [command]

  (no args)                     interactive menu
  all                           run every test (single model)
  matrix                        run every test across ALL_MODELS
  category <name> [<name>...]   run named categories
  test <name> [<name>...]       run named tests
  list                          print inventory and exit
  open                          show results/latest.md
  open-matrix                   show results/matrix.md
  -h | help                     this message

Token / cost notice (measured 2026-05-03 in ap-northeast-2):
  single-model run (57 tests):       ~0.30M billable input, ~2K output
                                     ~\$0.95 (Sonnet 4.6) ... ~\$2.40 (Opus 4.7)
  matrix run (3 models × 57 tests):  ~1.24M billable input, ~6K output
                                     ~\$5.00 USD total
  Token summary printed at the end of every run_all.py invocation.

Provider billing (--providers bedrock cpaws):
  Bedrock         charges standard Bedrock invoke pricing.
  Claude Platform charges via AWS Marketplace subscription (separate bill).
  Running both providers in matrix mode is ~2x the single-provider cost.
  Requires: ANTHROPIC_AWS_API_KEY and ANTHROPIC_AWS_WORKSPACE_ID for CPaws.
EOF
}

# ─── Entry ──────────────────────────────────────────────────────────────────
preflight

if [[ $# -eq 0 ]]; then
    main_menu
    exit 0
fi

case "$1" in
    all) shift; run_all_tests ;;
    matrix) shift; run_matrix ;;
    category|cat) shift; run_categories "$@" ;;
    test|tests) shift; run_tests "$@" ;;
    list) shift; print_inventory ;;
    open) shift; view_latest ;;
    open-matrix) shift; view_matrix ;;
    -h|--help|help) usage ;;
    *) usage; exit 2 ;;
esac
