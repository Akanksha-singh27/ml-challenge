"""
Address blocking + country-aware blocking + hybrid blocking (Person 3's scope).

Design notes, based on what explore.py's report showed about the real data:
  - business_address is free text with NO fixed schema (sometimes
    "street, city, state", sometimes "city, street, state" — order isn't
    consistent within or across sources). Exact-match blocking on the whole
    normalized address will miss almost everything; token overlap is the
    workhorse here.
  - postal_code is only present in ~5-7% of rows (train), so it's a strong
    but SUPPLEMENTARY blocker, not the primary one.
  - country splits train into US/India only; test adds France. Per the team
    plan, country is a partitioning/soft signal, never a hard filter -
    rows with an unrecognized country label are compared against everything
    rather than dropped or bucketed alone.
  - Scale is large (millions of rows per source), so blocking uses pandas
    merge (vectorized hash join) instead of nested Python loops, and prunes
    address tokens that are too common to be useful (e.g. "street", "floor",
    city names that appear in a huge fraction of rows).

Expects input DataFrames to already have the columns produced by
preprocess.py: business_address_norm, postal_code, country_norm,
country_recognized (see preprocess.py). Run preprocess.py first.

CLI:
    python3 blocking_address.py --data-dir dataset --processed-dir processed \
        --out-dir output --min-shared-tokens 2 --max-doc-freq 0.02

Outputs (per S1xS2 and S1xS3):
    output/candidate_pairs_address_s1_s2.tsv
    output/candidate_pairs_address_s1_s3.tsv
And, when train ground truth is available, prints blocking recall /
candidate count / reduction ratio / runtime - the metrics format from the
team's experiment log.
"""

import argparse
import os
import re
import time

import pandas as pd

from config import get_data_dir, train_paths, test_paths

ID_COL = "entity_id"

# Tokens that are too generic to be useful blocking keys on their own.
# Street-type words are already expanded by normalize_address() in
# normalization.py, so we filter the EXPANDED forms here.
ADDRESS_STOPWORDS = {
    "street", "road", "avenue", "lane", "drive", "court", "circle",
    "highway", "parkway", "apartment", "floor", "suite", "building",
    "number", "square", "place", "extension", "boulevard",
}


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def tokenize_address(addr_norm: str):
    """Split a normalized address into blocking-worthy tokens.

    Keeps numeric tokens (street/building numbers are high-signal) and
    alphabetic tokens of length >= 2, minus the generic stopword list.
    """
    if not addr_norm:
        return []
    tokens = addr_norm.split()
    return [t for t in tokens if t not in ADDRESS_STOPWORDS and len(t) >= 2]


# ---------------------------------------------------------------------------
# Token-overlap blocking (vectorized: explode + merge, not nested loops)
# ---------------------------------------------------------------------------

def _exploded_tokens(df: pd.DataFrame, text_col: str, id_col: str = ID_COL) -> pd.DataFrame:
    tokens = df[text_col].apply(tokenize_address)
    exploded = df[[id_col]].assign(token=tokens).explode("token")
    return exploded.dropna(subset=["token"])


def token_blocking_candidates(
    s1_df: pd.DataFrame,
    s2_df: pd.DataFrame,
    text_col: str = "business_address_norm",
    id_col: str = ID_COL,
    min_shared_tokens: int = 2,
    max_doc_freq: float = 0.02,
) -> pd.DataFrame:
    """Candidate pairs where s1 and s2 addresses share >= min_shared_tokens
    non-generic tokens. Tokens appearing in more than max_doc_freq of s2 rows
    are dropped first (too common to discriminate - e.g. a city name that's
    in 30% of rows would otherwise connect nearly everything to everything).

    Returns columns: {id_col}_s1, {id_col}_s2, shared_tokens
    """
    if len(s1_df) == 0 or len(s2_df) == 0:
        return pd.DataFrame(columns=[f"{id_col}_s1", f"{id_col}_s2", "shared_tokens"])

    s1_exp = _exploded_tokens(s1_df, text_col, id_col)
    s2_exp = _exploded_tokens(s2_df, text_col, id_col)

    # Prune overly common tokens using s2's document frequency (the side
    # being searched into). A token kept must be rare enough on both sides
    # to be discriminative, but pruning by s2 alone is enough to bound the
    # merge size and is symmetric in effect since the same tokens vanish
    # from s1_exp's usable set once absent from s2_exp.
    doc_freq = s2_exp["token"].value_counts()
    max_count = max(1, int(max_doc_freq * len(s2_df)))
    keep_tokens = set(doc_freq[doc_freq <= max_count].index)

    s1_exp = s1_exp[s1_exp["token"].isin(keep_tokens)]
    s2_exp = s2_exp[s2_exp["token"].isin(keep_tokens)]

    if len(s1_exp) == 0 or len(s2_exp) == 0:
        return pd.DataFrame(columns=[f"{id_col}_s1", f"{id_col}_s2", "shared_tokens"])

    merged = s1_exp.merge(s2_exp, on="token", suffixes=("_s1", "_s2"))
    pair_counts = (
        merged.groupby([f"{id_col}_s1", f"{id_col}_s2"])
        .size()
        .reset_index(name="shared_tokens")
    )
    return pair_counts[pair_counts["shared_tokens"] >= min_shared_tokens].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Postal code blocking (exact match, supplementary - sparse coverage)
# ---------------------------------------------------------------------------

def postal_code_candidates(
    s1_df: pd.DataFrame, s2_df: pd.DataFrame, id_col: str = ID_COL
) -> pd.DataFrame:
    """Exact postal_code match. High precision when present, but only
    covers ~5-7% of rows per explore.py's report - meant to be UNIONed with
    token blocking, not used alone.
    """
    s1_pc = s1_df.loc[s1_df["postal_code"] != "", [id_col, "postal_code"]]
    s2_pc = s2_df.loc[s2_df["postal_code"] != "", [id_col, "postal_code"]]
    if len(s1_pc) == 0 or len(s2_pc) == 0:
        return pd.DataFrame(columns=[f"{id_col}_s1", f"{id_col}_s2", "shared_tokens"])

    merged = s1_pc.merge(s2_pc, on="postal_code", suffixes=("_s1", "_s2"))
    merged["shared_tokens"] = -1  # sentinel: matched by postal code, not token count
    return merged[[f"{id_col}_s1", f"{id_col}_s2", "shared_tokens"]].drop_duplicates()


# ---------------------------------------------------------------------------
# Country-aware blocking
# ---------------------------------------------------------------------------

def country_aware_block(
    s1_df: pd.DataFrame,
    s2_df: pd.DataFrame,
    id_col: str = ID_COL,
    country_col: str = "country_norm",
    **token_kwargs,
) -> pd.DataFrame:
    """Partition by recognized country, then run token blocking within each
    partition (cuts comparison space roughly by the number of countries).

    Rows with an unrecognized country label are NEVER dropped or isolated:
    they're blocked against the FULL opposite source (not just their own
    label's partition), since we can't trust the label. This is what makes
    it "country-aware" rather than "country-filtered" - a hard filter would
    silently lose matches when country is noisy or unseen (e.g. France
    appearing only in test).
    """
    results = []

    recognized_countries = set(s1_df.loc[s1_df["country_recognized"], country_col]) & set(
        s2_df.loc[s2_df["country_recognized"], country_col]
    )
    for country in recognized_countries:
        s1_part = s1_df[(s1_df[country_col] == country) & s1_df["country_recognized"]]
        s2_part = s2_df[(s2_df[country_col] == country) & s2_df["country_recognized"]]
        results.append(token_blocking_candidates(s1_part, s2_part, id_col=id_col, **token_kwargs))

    # Unrecognized-country rows on either side: block against the whole
    # opposite source rather than assuming they belong nowhere.
    s1_unrec = s1_df[~s1_df["country_recognized"]]
    s2_unrec = s2_df[~s2_df["country_recognized"]]
    if len(s1_unrec) > 0:
        results.append(token_blocking_candidates(s1_unrec, s2_df, id_col=id_col, **token_kwargs))
    if len(s2_unrec) > 0:
        results.append(token_blocking_candidates(s1_df, s2_unrec, id_col=id_col, **token_kwargs))

    if not results:
        return pd.DataFrame(columns=[f"{id_col}_s1", f"{id_col}_s2", "shared_tokens"])
    return pd.concat(results, ignore_index=True).drop_duplicates([f"{id_col}_s1", f"{id_col}_s2"])


# ---------------------------------------------------------------------------
# Hybrid blocking: union multiple blockers' candidates
# ---------------------------------------------------------------------------

def union_candidates(*candidate_dfs: pd.DataFrame, id_col: str = ID_COL) -> pd.DataFrame:
    """Union candidate-pair DataFrames from different blockers (address
    token blocking, postal blocking, country-aware blocking, and - once
    integrated - Person 2's name blocking). A pair survives if ANY blocker
    proposed it, matching the team plan's "if one blocker misses a true
    match, another might catch it" rationale.
    """
    non_empty = [df for df in candidate_dfs if len(df) > 0]
    if not non_empty:
        return pd.DataFrame(columns=[f"{id_col}_s1", f"{id_col}_s2"])
    combined = pd.concat(non_empty, ignore_index=True)
    return combined[[f"{id_col}_s1", f"{id_col}_s2"]].drop_duplicates().reset_index(drop=True)


def hybrid_block(
    s1_df: pd.DataFrame,
    s2_df: pd.DataFrame,
    id_col: str = ID_COL,
    min_shared_tokens: int = 2,
    max_doc_freq: float = 0.02,
) -> pd.DataFrame:
    """Person 3's full candidate set: union of country-aware address-token
    blocking and postal-code blocking.
    """
    address_candidates = country_aware_block(
        s1_df, s2_df, id_col=id_col,
        min_shared_tokens=min_shared_tokens, max_doc_freq=max_doc_freq,
    )
    postal_candidates = postal_code_candidates(s1_df, s2_df, id_col=id_col)
    return union_candidates(address_candidates, postal_candidates, id_col=id_col)


# ---------------------------------------------------------------------------
# Evaluation (blocking recall / reduction ratio) - the team's metrics format
# ---------------------------------------------------------------------------

def evaluate_blocking(
    candidates: pd.DataFrame,
    ground_truth: pd.DataFrame,
    n_s1: int,
    n_other: int,
    id_col: str = ID_COL,
) -> dict:
    """Blocking recall against train ground_truth: matched_entity_ids is a
    comma-separated list of true-match ids for each S1 entity_id (may point
    into source2 and/or source3). Recall = fraction of true match pairs that
    appear among the candidates.
    """
    gt = ground_truth[ground_truth["matched_entity_ids"].str.strip() != ""].copy()
    gt_pairs = gt.assign(
        matched=gt["matched_entity_ids"].str.split(",")
    ).explode("matched")
    gt_pairs["matched"] = gt_pairs["matched"].str.strip()
    true_pairs = set(zip(gt_pairs[id_col], gt_pairs["matched"]))

    cand_pairs = set(zip(candidates[f"{id_col}_s1"], candidates[f"{id_col}_s2"]))
    # only score true pairs whose target actually lives in this "other" source
    other_ids_in_gt = {b for (_, b) in true_pairs}
    relevant_true_pairs = true_pairs  # scored per-call against whichever source was passed in

    found = cand_pairs & relevant_true_pairs
    recall = len(found) / len(relevant_true_pairs) if relevant_true_pairs else float("nan")

    total_possible = n_s1 * n_other
    reduction_ratio = 1 - (len(candidates) / total_possible) if total_possible else float("nan")

    return {
        "n_candidates": len(candidates),
        "n_true_pairs_scored": len(relevant_true_pairs),
        "n_true_pairs_found": len(found),
        "blocking_recall": recall,
        "reduction_ratio": reduction_ratio,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_processed(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=None, help="Raw dataset root (for ground_truth)")
    parser.add_argument("--processed-dir", default="processed", help="Output dir from preprocess.py")
    parser.add_argument("--split", default="train", choices=["train", "test"])
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--min-shared-tokens", type=int, default=2)
    parser.add_argument("--max-doc-freq", type=float, default=0.02)
    parser.add_argument("--sample", type=int, default=None,
                         help="Optional row cap per source, for a quick local run")
    args = parser.parse_args()

    split_dir = os.path.join(args.processed_dir, args.split)
    s1 = _load_processed(os.path.join(split_dir, f"{args.split}_source1.tsv"))
    s2 = _load_processed(os.path.join(split_dir, f"{args.split}_source2.tsv"))
    s3 = _load_processed(os.path.join(split_dir, f"{args.split}_source3.tsv"))

    if args.sample:
        s1 = s1.sample(min(args.sample, len(s1)), random_state=42)
        s2 = s2.sample(min(args.sample, len(s2)), random_state=42)
        s3 = s3.sample(min(args.sample, len(s3)), random_state=42)

    os.makedirs(args.out_dir, exist_ok=True)

    ground_truth = None
    if args.split == "train":
        data_dir = get_data_dir(args.data_dir)
        gt_path = train_paths(data_dir)["ground_truth"]
        if os.path.isfile(gt_path):
            ground_truth = _load_processed(gt_path)
            if args.sample:
                ground_truth = ground_truth[ground_truth[ID_COL].isin(s1[ID_COL])]

    for other_name, other_df in (("s2", s2), ("s3", s3)):
        print(f"\n=== {args.split} source1 x {other_name} ===")
        t0 = time.time()
        candidates = hybrid_block(
            s1, other_df,
            min_shared_tokens=args.min_shared_tokens,
            max_doc_freq=args.max_doc_freq,
        )
        runtime = time.time() - t0

        out_path = os.path.join(args.out_dir, f"candidate_pairs_address_s1_{other_name}.tsv")
        candidates.to_csv(out_path, sep="\t", index=False)
        print(f"  candidates: {len(candidates)}  runtime: {runtime:.1f}s  -> {out_path}")

        if ground_truth is not None:
            metrics = evaluate_blocking(candidates, ground_truth, len(s1), len(other_df))
            print(f"  blocking_recall: {metrics['blocking_recall']:.4f}  "
                  f"(found {metrics['n_true_pairs_found']}/{metrics['n_true_pairs_scored']} true pairs)")
            print(f"  reduction_ratio: {metrics['reduction_ratio']:.6f}")


if __name__ == "__main__":
    main()
