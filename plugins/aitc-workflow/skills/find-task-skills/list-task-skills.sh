#!/usr/bin/env bash
# list-task-skills.sh — Structured listing of active task SKILLs for AITC workflow
#
# Usage:
#   ./list-task-skills.sh                    # auto-detect, prompt if multiple
#   ./list-task-skills.sh <batch-name>       # target specific batch
#   ./list-task-skills.sh --json             # machine-parseable output
#
# Output modes:
#   (default) Human-readable with sections
#   --json     JSON array for agent consumption

set -uo pipefail
# Note: no 'set -e' — extract_frontmatter grep may return empty, which is OK

SKILLS_DIR="${SKILLS_DIR:-skills}"
BATCH_NAME="${1:-}"
JSON_MODE=false

if [[ "${1:-}" == "--json" ]]; then
    JSON_MODE=true
    BATCH_NAME="${2:-}"
elif [[ "${2:-}" == "--json" ]]; then
    JSON_MODE=true
fi

# ── Discover aitc-task directories ──────────────────────────────────
shopt -s nullglob
DIRS=( "$SKILLS_DIR"/aitc-task-*/ )
shopt -u nullglob

if [[ ${#DIRS[@]} -eq 0 ]]; then
    if $JSON_MODE; then
        echo '{"status":"empty","directories":[],"skills":[]}'
    else
        echo "=== No active task SKILL directories found in $SKILLS_DIR/ ==="
        echo "This is normal if execution hasn't started yet."
    fi
    exit 0
fi

# ── Multiple directories: report all, let agent choose ──────────────
if [[ ${#DIRS[@]} -gt 1 ]] && [[ -z "$BATCH_NAME" ]]; then
    if $JSON_MODE; then
        echo "{"
        echo '  "status": "multiple_directories",'
        echo '  "message": "Multiple aitc-task directories found. Select the active one.",'
        echo '  "directories": ['
        first=true
        for dir in "${DIRS[@]}"; do
            dirname=$(basename "$dir")
            created=$(stat -c '%w' "$dir" 2>/dev/null || stat -f '%SB' "$dir" 2>/dev/null || echo "unknown")
            modified=$(stat -c '%y' "$dir" 2>/dev/null || stat -f '%Sm' "$dir" 2>/dev/null || echo "unknown")
            skill_count=$(ls "$dir"*.md 2>/dev/null | grep -cv 'discovery-hints' || echo 0)
            $first || echo ','
            first=false
            echo -n "    {\"name\": \"$dirname\", \"path\": \"$dir\", \"created\": \"$created\", \"modified\": \"$modified\", \"skill_count\": $skill_count}"
        done
        echo ''
        echo '  ]'
        echo '}'
    else
        echo "=== WARNING: Multiple aitc-task directories found in $SKILLS_DIR/ ==="
        echo ""
        echo "Only ONE should be active. Archived directories belong in archived/."
        echo "Select the active directory by re-running with the batch name:"
        echo ""
        echo "  ./list-task-skills.sh <batch-name>"
        echo ""
        echo "Directories found:"
        echo "─────────────────────────────────────────────────────"
        for dir in "${DIRS[@]}"; do
            dirname=$(basename "$dir")
            created=$(stat -c '%w' "$dir" 2>/dev/null || echo "unknown")
            modified=$(stat -c '%y' "$dir" 2>/dev/null || echo "unknown")
            skill_count=$(ls "$dir"*.md 2>/dev/null | grep -cv 'discovery-hints' || echo 0)
            echo ""
            echo "  [$dirname]"
            echo "    Created:  $created"
            echo "    Modified: $modified"
            echo "    Skills:   $skill_count file(s)"
        done
        echo ""
        echo "─────────────────────────────────────────────────────"
        echo "Ask the Lead which directory is active, or if inactive"
        echo "directories should be moved to archived/."
    fi
    exit 1
fi

# ── Resolve target directory ────────────────────────────────────────
if [[ -n "$BATCH_NAME" ]]; then
    TARGET="$SKILLS_DIR/aitc-task-$BATCH_NAME"
    if [[ ! -d "$TARGET" ]]; then
        if $JSON_MODE; then
            echo "{\"status\":\"not_found\",\"target\":\"$TARGET\",\"skills\":[]}"
        else
            echo "=== Directory not found: $TARGET ==="
            echo "Available: ${DIRS[*]:-(none)}"
        fi
        exit 1
    fi
else
    TARGET="${DIRS[0]%/}"
fi

BATCH_DIRNAME=$(basename "$TARGET")

# ── Extract frontmatter from a SKILL.md ─────────────────────────────
extract_frontmatter() {
    local file="$1"
    local field="$2"
    # Extract frontmatter block between --- delimiters, find field, strip key and quotes
    sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null \
        | { grep -i "^${field}:" 2>/dev/null || true; } \
        | head -1 \
        | sed 's/^[^:]*:[[:space:]]*//' \
        | sed 's/^"//;s/"$//' \
        | sed "s/^'//;s/'$//"
}

# ── List and parse SKILL files ──────────────────────────────────────
SKILL_FILES=()
shopt -s nullglob
for f in "$TARGET"/*.md; do
    [[ "$(basename "$f")" == ".discovery-hints.md" ]] && continue
    SKILL_FILES+=("$f")
done
shopt -u nullglob

if $JSON_MODE; then
    echo "{"
    echo "  \"status\": \"ok\","
    echo "  \"batch\": \"$BATCH_DIRNAME\","
    echo "  \"directory\": \"$TARGET\","
    echo "  \"skill_count\": ${#SKILL_FILES[@]},"
    echo "  \"skills\": ["
    first=true
    for f in "${SKILL_FILES[@]}"; do
        name=$(extract_frontmatter "$f" "name")
        desc=$(extract_frontmatter "$f" "description")
        type=$(extract_frontmatter "$f" "task-type")
        supplements=$(extract_frontmatter "$f" "supplements")
        instance_of=$(extract_frontmatter "$f" "instance-of")
        status=$(extract_frontmatter "$f" "status")
        created=$(extract_frontmatter "$f" "created")
        $first || echo ','
        first=false
        echo -n "    {"
        echo -n "\"file\": \"$(basename "$f")\""
        echo -n ", \"name\": \"$name\""
        echo -n ", \"type\": \"$type\""
        echo -n ", \"status\": \"${status:-active}\""
        echo -n ", \"created\": \"${created:-unknown}\""
        echo -n ", \"description\": \"$desc\""
        [[ -n "$supplements" ]] && echo -n ", \"supplements\": \"$supplements\""
        [[ -n "$instance_of" ]] && echo -n ", \"instance_of\": \"$instance_of\""
        echo -n "}"
    done
    echo ''
    echo '  ]'
    echo '}'
else
    echo "=== Task SKILLs in $TARGET/ ==="
    echo "Batch: $BATCH_DIRNAME"
    echo "Total: ${#SKILL_FILES[@]} skill file(s)"
    echo ""
    if [[ ${#SKILL_FILES[@]} -eq 0 ]]; then
        echo "(empty — no task SKILLs created yet)"
    else
        for f in "${SKILL_FILES[@]}"; do
            name=$(extract_frontmatter "$f" "name")
            desc=$(extract_frontmatter "$f" "description")
            type=$(extract_frontmatter "$f" "task-type")
            supplements=$(extract_frontmatter "$f" "supplements")
            instance_of=$(extract_frontmatter "$f" "instance-of")
            status=$(extract_frontmatter "$f" "status")
            echo "─────────────────────────────────────────────────────"
            echo "  Name:        $name"
            echo "  Type:        ${type:-unknown}"
            [[ -n "$supplements" ]] && echo "  Supplements: $supplements"
            [[ -n "$instance_of" ]] && echo "  Instance of: $instance_of"
            echo "  Status:      ${status:-active}"
            echo "  Description: $desc"
            echo "  File:        $(basename "$f")"
        done
        echo "─────────────────────────────────────────────────────"
    fi
fi
