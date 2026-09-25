"""
Normalization functions for business_name, business_address, and country.

These dictionaries are starting points based on the noise patterns named in
the problem statement (Corp/Corporation, Pvt/Private, Rd/Road, etc.). Treat
them as living documents: after you run explore.py, feed back whatever new
abbreviations/patterns you actually see in the data. That's the "dataset
knowledge" the team strategy depends on.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    """Convert accented / transliterated Latin characters to plain ASCII where
    possible (e.g. 'Café' -> 'Cafe'). This is algorithmic (stdlib unicodedata),
    not a lookup against any external transliteration service.
    """
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_punct_keep_alnum(text: str) -> str:
    """Remove punctuation but keep letters, digits, and spaces."""
    return re.sub(r"[^\w\s]", " ", text)


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

# Legal-suffix / abbreviation expansions. Keys are matched as WHOLE TOKENS
# (case-insensitive) after punctuation stripping. Extend this from explore.py's
# "most common last tokens" output.
NAME_ABBREVIATIONS = {
    "corp": "corporation",
    "co": "company",
    "inc": "incorporated",
    "ltd": "limited",
    "llc": "llc",  # kept as-is, already a standard token
    "pvt": "private",
    "pte": "private",
    "intl": "international",
    "mfg": "manufacturing",
    "assn": "association",
    "assoc": "association",
    "bros": "brothers",
    "grp": "group",
    "svcs": "services",
    "svc": "service",
    "dept": "department",
    "&": "and",
}

# Legal suffix tokens worth optionally stripping off entirely for a
# "core name" comparison (e.g. name matching ignoring corporate form).
LEGAL_SUFFIX_TOKENS = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "ltd",
    "limited", "llc", "llp", "pvt", "private", "pte", "gmbh", "sa", "srl",
    "plc",
}


def normalize_name(name: str) -> str:
    """Full normalization for comparison/blocking: lowercase, expand
    abbreviations, strip punctuation, collapse whitespace.
    """
    if not name:
        return ""
    text = strip_accents(name)
    text = text.lower()
    text = text.replace("&", " and ")
    text = strip_punct_keep_alnum(text)
    tokens = text.split()
    expanded = [NAME_ABBREVIATIONS.get(tok, tok) for tok in tokens]
    return collapse_whitespace(" ".join(expanded))


def core_name(name: str) -> str:
    """normalize_name() with trailing legal-suffix tokens removed, for a
    'business identity ignoring corporate form' comparison. Useful as a
    separate feature/blocking key alongside the full normalized name.
    """
    normalized = normalize_name(name)
    tokens = normalized.split()
    while tokens and tokens[-1] in LEGAL_SUFFIX_TOKENS:
        tokens.pop()
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Address normalization
# ---------------------------------------------------------------------------

ADDRESS_ABBREVIATIONS = {
    "rd": "road",
    "st": "street",
    "str": "street",
    "ave": "avenue",
    "av": "avenue",
    "blvd": "boulevard",
    "dr": "drive",
    "ln": "lane",
    "ct": "court",
    "cir": "circle",
    "hwy": "highway",
    "pkwy": "parkway",
    "apt": "apartment",
    "fl": "floor",
    "flr": "floor",
    "ste": "suite",
    "bldg": "building",
    "no": "number",
    "nr": "number",
    "sq": "square",
    "pl": "place",
    "ext": "extension",
}

LANDMARK_PATTERN = re.compile(
    r"\b(near|opposite|opp\.?|behind|beside|close to|next to|adjacent to)\b\s*(.*)$",
    re.IGNORECASE,
)

# Loose postal-code patterns; extend per-country as you observe real formats.
POSTAL_PATTERNS = {
    "US": re.compile(r"\b(\d{5})(-\d{4})?\b"),
    "IN": re.compile(r"\b(\d{6})\b"),
}


def extract_landmark(address: str):
    """Return (address_without_landmark_clause, landmark_text_or_None)."""
    match = LANDMARK_PATTERN.search(address)
    if not match:
        return address, None
    landmark_text = match.group(0).strip()
    cleaned = (address[: match.start()] + address[match.end():]).strip(" ,")
    return cleaned, landmark_text


def extract_postal_code(address: str, country_code: str = None):
    """Try the pattern for the given normalized country_code first, then fall
    back to trying all known patterns. Returns the matched code or None.
    """
    patterns = []
    if country_code and country_code in POSTAL_PATTERNS:
        patterns.append(POSTAL_PATTERNS[country_code])
    patterns.extend(p for p in POSTAL_PATTERNS.values() if p not in patterns)
    for pattern in patterns:
        m = pattern.search(address)
        if m:
            return m.group(1)
    return None


def normalize_address(address: str) -> str:
    """Full normalization for comparison/blocking: strip landmark clause,
    lowercase, expand street abbreviations, strip punctuation, collapse
    whitespace. Landmark and postal code are extracted separately — see
    extract_landmark() / extract_postal_code() — since they're useful as their
    own features rather than being folded into the string.
    """
    if not address:
        return ""
    text, _landmark = extract_landmark(address)
    text = strip_accents(text)
    text = text.lower()
    text = strip_punct_keep_alnum(text)
    tokens = text.split()
    expanded = [ADDRESS_ABBREVIATIONS.get(tok, tok) for tok in tokens]
    return collapse_whitespace(" ".join(expanded))


# ---------------------------------------------------------------------------
# Country normalization
# ---------------------------------------------------------------------------

# Known variants -> ISO 3166-1 alpha-2. Treat this as an OPEN set: anything
# not recognized is passed through cleaned (stripped/title-cased) rather than
# dropped or defaulted, because the test set includes France (not in training)
# and there may be other unseen labels or noisy variants of these three.
COUNTRY_VARIANTS = {
    "us": "US", "u.s.": "US", "u.s.a.": "US", "usa": "US",
    "united states": "US", "united states of america": "US",
    "india": "IN", "in": "IN", "bharat": "IN",
    "france": "FR", "fr": "FR",
}


def normalize_country(country: str):
    """Return (iso_code_or_None, was_recognized: bool).

    was_recognized=False means the value didn't match a known variant —
    worth logging/reviewing rather than silently guessing, since the point
    of this challenge is to handle an open set of country labels correctly.
    """
    if not country or not country.strip():
        return None, False
    key = collapse_whitespace(country).strip().lower().rstrip(".")
    if key in COUNTRY_VARIANTS:
        return COUNTRY_VARIANTS[key], True
    # Unrecognized: return a cleaned-up version of the original, flagged.
    return collapse_whitespace(country).strip(), False