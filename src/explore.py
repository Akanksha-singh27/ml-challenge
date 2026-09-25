import argparse
import os
import re
import sys
import unicodedata
from collections import Counter
import pandas as pd

from config import get_data_dir, train_paths, test_paths

REPORT_LINES = []


def log(line: str = ""):
    print(line)
    REPORT_LINES.append(line)


def load(path: str) -> pd.DataFrame:
    # keep_default_na=False: an empty address/name field should stay "" not NaN,
    # since NaN vs "" matters for our missing-value counts below.
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def has_non_ascii(s: str) -> bool:
    return any(ord(ch) > 127 for ch in s)


def strip_accents(s: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )


LANDMARK_PATTERN = re.compile(
    r"\b(near|opposite|opp\.?|behind|beside|close to|next to|adjacent to)\b",
    re.IGNORECASE,
)


def explore_source(name: str, df: pd.DataFrame):
    log(f"\n## {name}")
    log(f"- rows: {len(df)}")
    log(f"- columns: {list(df.columns)}")

    for col in ("business_name", "business_address", "country"):
        if col not in df.columns:
            continue
        empty = (df[col].str.strip() == "").sum()
        log(f"- empty `{col}`: {empty} ({empty / max(len(df),1):.2%})")

    if "country" in df.columns:
        log("- country value counts:")
        for val, cnt in df["country"].value_counts().items():
            log(f"    {val!r}: {cnt}")

    if "business_name" in df.columns:
        names = df["business_name"]
        non_ascii_names = names.apply(has_non_ascii).sum()
        log(f"- business_name with non-ASCII chars (possible transliteration): "
            f"{non_ascii_names} ({non_ascii_names / max(len(df),1):.2%})")

        # crude legal-suffix scan: last token of each name, lowercased
        last_tokens = Counter()
        for n in names:
            toks = n.strip().split()
            if toks:
                last_tokens[toks[-1].lower().strip(".,")] += 1
        common_suffixes = last_tokens.most_common(20)
        log("- most common last tokens in business_name (legal suffix candidates):")
        for tok, cnt in common_suffixes:
            log(f"    {tok!r}: {cnt}")

        # duplicate exact names within this source (before normalization)
        dup_names = names[names.str.strip() != ""].duplicated().sum()
        log(f"- exact duplicate (non-empty) business_name rows: {dup_names}")

    if "business_address" in df.columns:
        addrs = df["business_address"]
        landmark_count = addrs.apply(lambda a: bool(LANDMARK_PATTERN.search(a))).sum()
        log(f"- addresses with landmark references (near/opposite/behind/...): "
            f"{landmark_count} ({landmark_count / max(len(df),1):.2%})")

        # rough postal code presence: 5-6 consecutive digits anywhere
        has_postal = addrs.apply(lambda a: bool(re.search(r"\b\d{5,6}\b", a))).sum()
        log(f"- addresses with a 5-6 digit number (possible ZIP/PIN): {has_postal} "
            f"({has_postal / max(len(df),1):.2%})")

        non_ascii_addr = addrs.apply(has_non_ascii).sum()
        log(f"- addresses with non-ASCII chars: {non_ascii_addr} "
            f"({non_ascii_addr / max(len(df),1):.2%})")

    # sample of the messiest-looking rows: has landmark OR non-ascii OR very short
    log("- sample rows (name | address | country):")
    sample = df.sample(min(5, len(df)), random_state=42)
    for _, row in sample.iterrows():
        name = row.get("business_name", "")
        addr = row.get("business_address", "")
        country = row.get("country", "")
        log(f"    {name!r} | {addr!r} | {country!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=None, help="Root dataset folder")
    args = parser.parse_args()

    data_dir = get_data_dir(args.data_dir)
    log(f"# Exploration Report\ndata_dir = {data_dir}")

    for split_name, paths_fn in (("TRAIN", train_paths), ("TEST", test_paths)):
        paths = paths_fn(data_dir)
        log(f"\n# {split_name}")
        for source_key in ("source1", "source2", "source3"):
            path = paths[source_key]
            if not os.path.isfile(path):
                log(f"\n## {source_key} — FILE NOT FOUND at {path}, skipping")
                continue
            df = load(path)
            explore_source(f"{split_name} {source_key}", df)

        if split_name == "TRAIN" and os.path.isfile(paths.get("ground_truth", "")):
            gt = load(paths["ground_truth"])
            log(f"\n## TRAIN ground_truth")
            log(f"- rows: {len(gt)}")
            has_match = gt["matched_entity_ids"].str.strip() != ""
            log(f"- S1 entities with at least one match: {has_match.sum()} "
                f"({has_match.mean():.2%})")
            log(f"- singletons (no match): {(~has_match).sum()} "
                f"({(~has_match).mean():.2%})")
            match_counts = gt["matched_entity_ids"].apply(
                lambda s: 0 if not s.strip() else len(s.split(","))
            )
            log(f"- avg matches per S1 entity (incl. singletons): {match_counts.mean():.2f}")
            log(f"- max matches for a single S1 entity: {match_counts.max()}")

    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "exploration_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(REPORT_LINES))
    print(f"\nSaved report to {out_path}")


if __name__ == "__main__":
    main()