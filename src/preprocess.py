"""
Applies normalization.py to every source file (train + test) and writes
cleaned TSVs to processed/, plus an unrecognized-country report so the team
knows if anything besides US/India/France shows up.

Run:
    python3 preprocess.py --data-dir dataset --out-dir processed

Output columns added to each file (originals are kept untouched):
    business_name_norm    - normalize_name()
    business_name_core    - core_name() (legal suffix stripped)
    business_address_norm - normalize_address() (landmark clause removed)
    landmark               - extracted landmark clause, or empty
    postal_code            - extracted postal code, or empty
    country_norm           - normalize_country() ISO code, or original if unrecognized
    country_recognized     - True/False, for auditing unknown country labels
"""

import argparse
import os

import pandas as pd

from config import get_data_dir, train_paths, test_paths
from normalization import (
    normalize_name,
    core_name,
    normalize_address,
    extract_landmark,
    extract_postal_code,
    normalize_country,
)


def process_file(path: str, out_path: str, unrecognized_countries: dict):
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)

    df["business_name_norm"] = df["business_name"].apply(normalize_name)
    df["business_name_core"] = df["business_name"].apply(core_name)

    landmark_pairs = df["business_address"].apply(extract_landmark)
    addr_wo_landmark = landmark_pairs.apply(lambda t: t[0])
    df["landmark"] = landmark_pairs.apply(lambda t: t[1] or "")
    df["business_address_norm"] = addr_wo_landmark.apply(normalize_address)

    country_pairs = df["country"].apply(normalize_country)
    df["country_norm"] = country_pairs.apply(lambda t: t[0] or "")
    df["country_recognized"] = country_pairs.apply(lambda t: t[1])

    df["postal_code"] = [
        extract_postal_code(addr, cc) or ""
        for addr, cc in zip(df["business_address"], df["country_norm"])
    ]

    for val in df.loc[~df["country_recognized"], "country"].unique():
        unrecognized_countries[val] = unrecognized_countries.get(val, 0) + 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, sep="\t", index=False, encoding="utf-8")
    print(f"  wrote {out_path} ({len(df)} rows)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--out-dir", default="processed")
    args = parser.parse_args()

    data_dir = get_data_dir(args.data_dir)
    unrecognized_countries = {}

    for split_name, paths_fn in (("train", train_paths), ("test", test_paths)):
        paths = paths_fn(data_dir)
        print(f"\n{split_name.upper()}")
        for source_key in ("source1", "source2", "source3"):
            in_path = paths[source_key]
            if not os.path.isfile(in_path):
                print(f"  {in_path} not found, skipping")
                continue
            out_path = os.path.join(args.out_dir, split_name, f"{split_name}_{source_key}.tsv")
            process_file(in_path, out_path, unrecognized_countries)

    print("\nUnrecognized country labels (review these — don't silently drop):")
    if unrecognized_countries:
        for val, cnt in sorted(unrecognized_countries.items(), key=lambda x: -x[1]):
            print(f"  {val!r}: {cnt} rows")
    else:
        print("  none — everything matched a known variant")

    print(f"\nDone. Cleaned files are under {args.out_dir}/")


if __name__ == "__main__":
    main()