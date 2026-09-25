import os
import pandas as pd
import re


PROCESSED_TRAIN = "processed/train"

POSTAL_PATTERN = re.compile(r"\b\d{5}(?:-\d{4})?\b|\b\d{6}\b")


def audit_file(path, chunksize=100_000):
    total_rows = 0
    rows_with_number = 0
    rows_with_postal = 0
    number_but_no_postal = 0

    examples = []

    for chunk in pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize,
    ):
        total_rows += len(chunk)

        number_mask = chunk["business_address"].str.contains(
            POSTAL_PATTERN,
            na=False,
            regex=True,
        )

        postal_mask = chunk["postal_code"].str.strip().ne("")

        rows_with_number += number_mask.sum()
        rows_with_postal += postal_mask.sum()

        failed_mask = number_mask & ~postal_mask
        number_but_no_postal += failed_mask.sum()

        if len(examples) < 10:
            failed_examples = chunk.loc[
                failed_mask,
                ["business_name", "business_address", "country", "postal_code"]
            ]

            for _, row in failed_examples.iterrows():
                examples.append({
                    "business_name": row["business_name"],
                    "address": row["business_address"],
                    "country": row["country"],
                    "postal_code": row["postal_code"],
                })

                if len(examples) >= 10:
                    break

    return {
        "rows": total_rows,
        "raw_number": rows_with_number,
        "extracted_postal": rows_with_postal,
        "number_but_no_postal": number_but_no_postal,
        "examples": examples,
    }


def main():
    files = [
        "train_source1.tsv",
        "train_source2.tsv",
        "train_source3.tsv",
    ]

    print("POSTAL CODE EXTRACTION AUDIT")
    print("=" * 60)

    for filename in files:
        path = os.path.join(PROCESSED_TRAIN, filename)

        if not os.path.isfile(path):
            print(f"\n{filename}: NOT FOUND")
            continue

        print(f"\nChecking {filename}...")

        result = audit_file(path)

        print(f"Total rows:              {result['rows']:,}")
        print(f"Rows with number:        {result['raw_number']:,}")
        print(f"Rows with postal_code:   {result['extracted_postal']:,}")
        print(f"Number but no postal:     {result['number_but_no_postal']:,}")

        if result["raw_number"]:
            coverage = (
                result["extracted_postal"]
                / result["raw_number"]
                * 100
            )

            print(f"Extraction coverage:     {coverage:.2f}%")

        if result["examples"]:
            print("\nExamples where a number was found but no postal code was extracted:")

            for i, example in enumerate(result["examples"], 1):
                print(f"\n{i}. {example['business_name']}")
                print(f"   Country: {example['country']}")
                print(f"   Address: {example['address']}")
                print(f"   Postal:  {example['postal_code']!r}")


if __name__ == "__main__":
    main()