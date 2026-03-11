"""
Adds sheet: "1.x" property to every question in the quiz pool.
Determines worksheet by tracking section-comment headers.
The NUMBERS: ADDITIONAL section is mixed, so questions are classified
by whether the number they test is <=21 (1.1) or >=22 (1.2).
"""
import re

HTML_FILE = "C:/Users/alanr/OneDrive/Documents/ClaudeCode/ItalianLessons/index.html"

with open(HTML_FILE, encoding="utf-8") as f:
    content = f.read()

# ── section comment → sheet ──────────────────────────────────────────────────
# Keyed on substrings that appear in the comment line (ORDER MATTERS for
# overlapping keys — more specific first).
SECTION_RULES = [
    # 1.1 sections
    ("GREETINGS: ADDITIONAL",  "1.1"),
    ("GREETINGS",              "1.1"),
    ("ASKING NAMES",           "1.1"),
    ("WHERE ARE YOU FROM",     "1.1"),
    ("ESSERE: ADDITIONAL",     "1.1"),
    ("ESSERE",                 "1.1"),
    ("NUMBERS 0",              "1.1"),   # "NUMBERS 0–21"
    ("COUNTRIES: ADDITIONAL",  "1.1"),
    ("COUNTRIES",              "1.1"),
    ("COGNATES",               "1.1"),
    ("VOCABULARY",             "1.1"),
    # 1.2 sections
    ("HOW ARE YOU: ADDITIONAL","1.2"),
    ("HOW ARE YOU",            "1.2"),
    ("NUMBERS 22",             "1.2"),   # "NUMBERS 22–100"
    ("WHERE DO YOU LIVE",      "1.2"),
    ("ARTICLES: ADDITIONAL",   "1.2"),
    ("ARTICLES",               "1.2"),
    ("VERBS: AVERE ADDITIONAL","1.2"),
    ("VERBS: VOLERE ADDITIONAL","1.2"),
    ("VERBS: PARLARE ADDITIONAL","1.2"),
    ("VERBS",                  "1.2"),
    ("LANGUAGES",              "1.2"),
    ("MEALS",                  "1.2"),
    ("HUNGER",                 "1.2"),
    ("-ARE VERBS: ADDITIONAL", "1.2"),
    ("-ARE VERBS",             "1.2"),
    ("CONVERSATION: ADDITIONAL","1.2"),
    ("CONVERSATION",           "1.2"),
    # NUMBERS: ADDITIONAL is mixed — handled separately
    ("NUMBERS: ADDITIONAL",    "MIXED"),
]

# Numbers <=21 belong to worksheet 1.1; >=22 to 1.2.
# These are the Italian number words tested in NUMBERS: ADDITIONAL,
# in the order they appear in the file.
NUMBERS_ADDITIONAL_ORDER = [
    ("cinque",      "1.1"),  # 5
    ("otto",        "1.1"),  # 8
    ("undici",      "1.1"),  # 11
    ("sedici",      "1.1"),  # 16
    ("dicianove",   "1.1"),  # 19
    ("trenta",      "1.2"),  # 30
    ("cinquanta",   "1.2"),  # 50
    ("ottanta",     "1.2"),  # 80
    ("ventidue",    "1.2"),  # 22
    ("ventotto",    "1.2"),  # 28
]

# ── locate the pool ───────────────────────────────────────────────────────────
POOL_START_MARKER = "const pool = ["
POOL_END_MARKER   = "]; // end pool"

pool_start = content.index(POOL_START_MARKER)
pool_end   = content.index(POOL_END_MARKER) + len(POOL_END_MARKER)
pool_block = content[pool_start:pool_end]

# ── process line by line ──────────────────────────────────────────────────────
lines        = pool_block.split("\n")
result_lines = []
current_sheet        = None
in_mixed_section     = False
mixed_q_count        = 0     # how many questions have started in MIXED section

def classify_section(comment_line):
    """Return sheet string for a section comment line, or None if not a header."""
    upper = comment_line.upper()
    for key, sheet in SECTION_RULES:
        if key in upper:
            return sheet
    return None

for line in lines:
    stripped = line.strip()

    # Detect section comment header
    if stripped.startswith("// ──") or stripped.startswith("// ─"):
        sheet = classify_section(stripped)
        if sheet is not None:
            current_sheet  = sheet
            in_mixed_section = (sheet == "MIXED")
            mixed_q_count  = 0

    # Detect start of a new question object (opening brace at depth 0)
    if stripped == "{":
        if in_mixed_section:
            mixed_q_count += 1   # first brace = first question, etc.

    # Before the exp: line, inject the sheet property
    if stripped.startswith("exp:"):
        if in_mixed_section:
            # Use the pre-built order list (1-indexed by question start count)
            idx = mixed_q_count - 1
            if 0 <= idx < len(NUMBERS_ADDITIONAL_ORDER):
                effective_sheet = NUMBERS_ADDITIONAL_ORDER[idx][1]
            else:
                effective_sheet = "1.1"   # fallback
        else:
            effective_sheet = current_sheet

        if effective_sheet and effective_sheet != "MIXED":
            indent = len(line) - len(line.lstrip())
            result_lines.append(" " * indent + f'sheet: "{effective_sheet}",')

    result_lines.append(line)

new_pool_block = "\n".join(result_lines)
new_content    = content[:pool_start] + new_pool_block + content[pool_end:]

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(new_content)

# ── verify ────────────────────────────────────────────────────────────────────
sheet_counts = {}
for match in re.finditer(r'sheet:\s*"(\d+\.\d+)"', new_content):
    s = match.group(1)
    sheet_counts[s] = sheet_counts.get(s, 0) + 1

total = sum(sheet_counts.values())
print(f"Done. Sheet tags added: {sheet_counts}  (total: {total})")
