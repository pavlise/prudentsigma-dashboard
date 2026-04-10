"""
Reorganise all files in AI Project into a single clean folder structure.
- Deduplicates (keeps one copy of each duplicate)
- Maps source folders to destination categories
- Generates a knowledge index (INDEX.md)
"""
import os
import shutil
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(r"C:\Users\Pavlos Elpidorou\Documents\AI Project")
DEST = BASE / "All Documents"
SCRIPTS_DIR = BASE / "scripts"

# Load inventory and duplicates
with open(SCRIPTS_DIR / "inventory.json", encoding="utf-8") as f:
    inventory = json.load(f)
with open(SCRIPTS_DIR / "duplicates.json", encoding="utf-8") as f:
    duplicates = json.load(f)

# Build set of paths to SKIP (all but the first/best copy of each duplicate group)
SKIP_PATHS = set()
for hash_val, paths in duplicates.items():
    if len(paths) <= 1:
        continue
    # Priority: keep copy already in new "Brightpool" folder first,
    # then "IG info", then "Kyriakos", then anything else
    def priority(p):
        if p.startswith("Brightpool\\") and not p.startswith("Brightpool (1)"):
            return 0
        if p.startswith("IG info"):
            return 1
        if p.startswith("Kyriakos"):
            return 2
        return 3
    sorted_paths = sorted(paths, key=priority)
    for p in sorted_paths[1:]:  # skip all but the best copy
        SKIP_PATHS.add(p)

print(f"Files to skip (duplicates): {len(SKIP_PATHS)}")

# ---------------------------------------------------------------------------
# MAPPING RULES
# Each rule: (source_fragment_list, destination_subfolder)
# The first matching rule wins. Fragments matched against the relative path.
# ---------------------------------------------------------------------------
RULES = [
    # --- 01 Compliance & AML ---
    (["03_AMLCO Report"],                         "01 - Compliance & AML/AMLCO Reports"),
    (["amlipol"],                                  "01 - Compliance & AML/AML Policies"),
    (["counter.docx"],                             "01 - Compliance & AML/AML Policies"),
    (["DD Policies"],                              "01 - Compliance & AML/DD Policies"),
    (["Dealing Policies"],                         "01 - Compliance & AML/Dealing Policies"),
    (["Dealing services"],                         "01 - Compliance & AML/Dealing Services"),
    (["besexeb"],                                  "01 - Compliance & AML/Best Execution"),
    (["Best Execution Policy"],                    "01 - Compliance & AML/Best Execution"),
    (["Order Execution Policy"],                   "01 - Compliance & AML/Order Execution"),
    (["complo"],                                   "01 - Compliance & AML/Compliance"),
    (["ramop"],                                    "01 - Compliance & AML/Compliance"),
    (["recap.docx"],                               "01 - Compliance & AML/Compliance"),
    (["Finance.docx"],                             "01 - Compliance & AML/Finance Policy"),
    (["policies manual"],                          "01 - Compliance & AML/Policies Manual"),
    (["Policies\\"],                               "01 - Compliance & AML/General Policies"),

    # --- 02 Risk Management ---
    (["7_Risk Management Reports"],               "02 - Risk Management/Risk Reports"),
    (["8_Market Risk"],                            "02 - Risk Management/Market Risk"),
    (["Market Risk Policy"],                       "02 - Risk Management/Market Risk"),
    (["marrispol"],                                "02 - Risk Management/Market Risk"),
    (["3_Opertional Risk"],                        "02 - Risk Management/Operational Risk"),
    (["11_Counterparty Credit Risk"],              "02 - Risk Management/Counterparty Credit Risk"),
    (["13_RCSA"],                                  "02 - Risk Management/RCSA"),
    (["RCSA.xlsx"],                                "02 - Risk Management/RCSA"),
    (["15_ KRI Dashboard"],                        "02 - Risk Management/KRI Dashboard"),
    (["16_Technology Risk Dashboard"],             "02 - Risk Management/Technology Risk"),
    (["17_Risk Acceptance Process"],               "02 - Risk Management/Risk Acceptance"),
    (["20_Risk Oddities"],                         "02 - Risk Management/Risk Oddities"),
    (["Entity RM Policy"],                         "02 - Risk Management/Risk Framework"),
    (["6_LE Limits"],                              "02 - Risk Management/LE Limits"),
    (["Risk Training"],                            "02 - Risk Management/Training"),
    (["anrispol"],                                 "02 - Risk Management/Risk Framework"),
    (["risapet"],                                  "02 - Risk Management/Risk Appetite"),
    (["Risk Appetite"],                            "02 - Risk Management/Risk Appetite"),
    (["Risk Management Framework"],               "02 - Risk Management/Risk Framework"),
    (["Exchange of Variation Margin"],             "02 - Risk Management/Variation Margin"),
    (["Groups Liquidity"],                         "02 - Risk Management/Liquidity"),

    # --- 03 Regulatory & Capital ---
    (["07_Pillar III"],                            "03 - Regulatory & Capital/Pillar III"),
    (["1_Capital Adequacy"],                       "03 - Regulatory & Capital/Capital Adequacy"),
    (["Regulatory Capital"],                       "03 - Regulatory & Capital/Capital Adequacy"),
    (["12_Audited Financial"],                     "03 - Regulatory & Capital/Audited Financials"),
    (["Audited Financial"],                        "03 - Regulatory & Capital/Audited Financials"),
    (["46_Regulatory Reporting"],                  "03 - Regulatory & Capital/Regulatory Reporting"),
    (["12_ERC Papers"],                            "03 - Regulatory & Capital/ERC Papers"),
    (["IFR\\"],                                    "03 - Regulatory & Capital/IFR"),
    (["CIF378"],                                   "03 - Regulatory & Capital/CySEC Submissions"),

    # --- 04 Algo & Pricing ---
    (["Python new algo"],                          "04 - Algo & Pricing/Pricing Algorithm"),
    (["Python Scripts"],                           "04 - Algo & Pricing/Analysis Scripts"),
    (["21_Algo Assessment"],                       "04 - Algo & Pricing/Algo Assessment"),
    (["Algo Self assesment"],                      "04 - Algo & Pricing/Algo Assessment"),
    (["Algo assesmnet"],                           "04 - Algo & Pricing/Algo Assessment"),
    (["24_Algo Trading"],                          "04 - Algo & Pricing/Algo Trading"),
    (["New Algo BAT"],                             "04 - Algo & Pricing/New Algo BAT"),
    (["Equities Tool"],                            "04 - Algo & Pricing/Equities Tool"),
    (["Performance Optimization"],                 "04 - Algo & Pricing/Performance Optimization"),
    (["CySEC_BPL_Algo"],                           "04 - Algo & Pricing/CySEC Algo Presentation"),
    (["Algo assesment"],                           "04 - Algo & Pricing/Algo Assessment"),
    (["New Equity Pricing"],                       "04 - Algo & Pricing/Pricing Data"),
    (["SPREAD_COMPARISON"],                        "04 - Algo & Pricing/Analysis Scripts"),
    (["PREMIUM_COMPARISON"],                       "04 - Algo & Pricing/Analysis Scripts"),
    (["PREMIUM_REPORT"],                           "04 - Algo & Pricing/Analysis Scripts"),
    (["strike adjustment"],                        "04 - Algo & Pricing/Analysis Scripts"),
    (["repor.xlsx"],                               "04 - Algo & Pricing/Pricing Data"),

    # --- 05 Trading Operations ---
    (["Corporate Actions"],                        "05 - Trading Operations/Corporate Actions"),
    (["Reconciliation of Strike"],                 "05 - Trading Operations/Strike & Dividend Reconciliation"),
    (["Dividend Reconciliation"],                  "05 - Trading Operations/Dividend Reconciliation"),
    (["dvd.xlsx"],                                 "05 - Trading Operations/Dividend Reconciliation"),
    (["roll.xlsx"],                                "05 - Trading Operations/Rollovers"),
    (["issua.xlsx"],                               "05 - Trading Operations/Issuance"),
    (["Issuance\\"],                               "05 - Trading Operations/Issuance"),
    (["Hedging Procedure"],                        "05 - Trading Operations/Hedging"),
    (["Hedging Providers"],                        "05 - Trading Operations/Hedging"),
    (["Futures Hedging"],                          "05 - Trading Operations/Hedging"),
    (["Bucket Refill"],                            "05 - Trading Operations/Procedures"),
    (["Earnings Announcement"],                    "05 - Trading Operations/Procedures"),
    (["Reuters Price Check"],                      "05 - Trading Operations/Procedures"),
    (["Extended Hours Check"],                     "05 - Trading Operations/Procedures"),
    (["IG- CMC Funding"],                          "05 - Trading Operations/Procedures"),
    (["Constructed Pricing during Holidays"],      "05 - Trading Operations/Holiday Pricing"),
    (["Indices Dividends"],                        "05 - Trading Operations/Indices & FX Funding"),
    (["Disorderly Trading"],                       "05 - Trading Operations/Monitoring"),
    (["Raydius Monitoring"],                       "05 - Trading Operations/Monitoring"),
    (["MTF Trading Hours"],                        "05 - Trading Operations/MTF"),
    (["8. MTF"],                                   "05 - Trading Operations/MTF"),
    (["Quarterly Statistics"],                     "05 - Trading Operations/Statistics"),
    (["Gap Loss"],                                 "05 - Trading Operations/PnL Reports"),
    (["OOH PNL"],                                  "05 - Trading Operations/PnL Reports"),
    (["MTD Premium"],                              "05 - Trading Operations/Premium Reports"),
    (["Net_Size"],                                 "05 - Trading Operations/Net Size Reports"),
    (["NCFs"],                                     "05 - Trading Operations/NCF Reports"),
    (["Rejections and Clients"],                   "05 - Trading Operations/Client Stats"),
    (["Daily Funding Report"],                     "05 - Trading Operations/Daily Reports"),
    (["Summary_Tab"],                              "05 - Trading Operations/Daily Reports"),
    (["DOW NCFs"],                                 "05 - Trading Operations/NCF Reports"),
    (["NASDAQ NCFs"],                              "05 - Trading Operations/NCF Reports"),
    (["NEW STEPLY"],                               "05 - Trading Operations/Procedures"),

    # --- 06 Products ---
    (["Cryptos\\"],                                "06 - Products/Cryptos"),
    (["Extended Hours\\"],                         "06 - Products/Extended Hours"),
    (["New Undelryings"],                          "06 - Products/New Underlyings"),
    (["New Underlyings"],                          "06 - Products/New Underlyings"),
    (["New Underlyin"],                            "06 - Products/New Underlyings"),
    (["IG & Turbo"],                               "06 - Products/Turbos"),
    (["turbo.pptx"],                               "06 - Products/Turbos"),
    (["ABNB.O"],                                   "06 - Products/Equity Data"),
    (["18. New product"],                          "06 - Products/New Products"),
    (["Macquarie\\"],                              "06 - Products/Macquarie"),
    (["Mini futures"],                             "06 - Products/New Products"),

    # --- 07 Business & Strategy ---
    (["4. Board"],                                 "07 - Business & Strategy/Board"),
    (["19. IG BOD"],                               "07 - Business & Strategy/Board"),
    (["1. Revenue budgets"],                       "07 - Business & Strategy/Revenue & Budgets"),
    (["Commercial\\"],                             "07 - Business & Strategy/Commercial"),
    (["06_IG Group items"],                        "07 - Business & Strategy/IG Group"),
    (["2. European town hall"],                    "07 - Business & Strategy/Events"),
    (["9. BPL Projects"],                          "07 - Business & Strategy/Projects"),
    (["T24 Presentations"],                        "07 - Business & Strategy/Presentations"),
    (["11. BrightPool intro"],                     "07 - Business & Strategy/Presentations"),
    (["12. Spectrum"],                             "07 - Business & Strategy/Presentations"),
    (["IMPORTANT PRESENTATIONS"],                  "07 - Business & Strategy/Presentations"),
    (["Presentations\\"],                          "07 - Business & Strategy/Presentations"),

    # --- 08 Data & Reports ---
    (["20232024"],                                 "08 - Data & Reports/2023-2024"),
    (["2025\\"],                                   "08 - Data & Reports/2025"),
    (["Market Holidays"],                          "08 - Data & Reports/Market Info"),
    (["Asset Analysis"],                           "08 - Data & Reports/Asset Analysis"),
    (["Income tax"],                               "08 - Data & Reports/Finance"),

    # --- 09 HR & Admin ---
    (["NEED\\Recruitment"],                        "09 - HR & Admin/Recruitment"),
    (["Newsletter\\"],                             "09 - HR & Admin/Newsletters"),
    (["Onedrive -work"],                           "09 - HR & Admin/OneDrive Work"),
    (["Salary.xlsx"],                              "09 - HR & Admin/Personal"),
    (["KH 2"],                                     "09 - HR & Admin/KH Files"),
    (["NEED\\"],                                   "09 - HR & Admin/NEED"),

    # --- 10 Technology ---
    (["22_ICT"],                                   "10 - Technology/ICT"),
    (["66_Business Continuity"],                   "10 - Technology/Business Continuity"),
    (["Other Info"],                               "10 - Technology/Other Info"),

    # --- Brightpool already-organised (keep structure) ---
    (["Brightpool\\01 - Policies"],                "01 - Compliance & AML"),
    (["Brightpool\\02 - Pricing"],                 "04 - Algo & Pricing/Pricing Algorithm"),
    (["Brightpool\\03 - Analysis"],                "04 - Algo & Pricing/Analysis Scripts"),
    (["Brightpool\\04 - Data"],                    "08 - Data & Reports"),
    (["Brightpool\\05 - Presentations"],           "07 - Business & Strategy/Presentations"),
]

def get_destination(rel_path):
    """Return destination subfolder for a file, or None if no rule matches."""
    for fragments, dest in RULES:
        if all(frag.lower() in rel_path.lower() for frag in fragments):
            return dest
    return "00 - Unsorted"

# ---------------------------------------------------------------------------
# Execute reorganisation
# ---------------------------------------------------------------------------
moved = 0
skipped_dup = 0
errors = []
dest_map = defaultdict(list)  # dest_folder -> [filenames] for index

for entry in inventory:
    rel_path = entry["path"]

    # Skip scripts folder itself
    if rel_path.startswith("scripts\\") or rel_path.startswith("scripts/"):
        continue

    # Skip duplicate copies
    if rel_path in SKIP_PATHS:
        skipped_dup += 1
        continue

    # Skip already-in-destination files
    if rel_path.startswith("All Documents\\") or rel_path.startswith("All Documents/"):
        continue

    src = BASE / rel_path
    dest_sub = get_destination(rel_path)
    dest_folder = DEST / dest_sub
    dest_folder.mkdir(parents=True, exist_ok=True)

    dest_file = dest_folder / entry["name"]

    # Handle filename collisions (different files, same name)
    if dest_file.exists():
        stem = Path(entry["name"]).stem
        suffix = Path(entry["name"]).suffix
        counter = 1
        while dest_file.exists():
            dest_file = dest_folder / f"{stem}_{counter}{suffix}"
            counter += 1

    try:
        shutil.copy2(str(src), str(dest_file))
        moved += 1
        dest_map[dest_sub].append(entry["name"])
    except Exception as e:
        errors.append(f"ERROR: {rel_path} -> {e}")

print(f"\nDone!")
print(f"  Files copied: {moved}")
print(f"  Duplicates skipped: {skipped_dup}")
print(f"  Errors: {len(errors)}")
for e in errors[:20]:
    print(f"  {e}")

# ---------------------------------------------------------------------------
# Generate INDEX.md
# ---------------------------------------------------------------------------
index_lines = [
    "# All Documents — Knowledge Index",
    "",
    "This index maps every folder to its contents.",
    "Use it to quickly find documents and understand what each section covers.",
    "",
]

for folder in sorted(dest_map.keys()):
    files = sorted(set(dest_map[folder]))
    index_lines.append(f"## {folder}")
    index_lines.append("")
    for f in files:
        index_lines.append(f"- {f}")
    index_lines.append("")

index_path = DEST / "INDEX.md"
with open(index_path, "w", encoding="utf-8") as f:
    f.write("\n".join(index_lines))

print(f"\nKnowledge index saved to: {index_path}")
