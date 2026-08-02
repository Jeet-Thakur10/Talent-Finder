import re

def normalize_job_location(raw_location: str | None) -> tuple[str | None, bool, bool]:
    """Parses a raw job location string to extract remote/hybrid flags and a clean location name.

    Args:
        raw_location: Raw location string (e.g. "Hybrid - Bangalore", "Remote, US").

    Returns:
        tuple[clean_location, is_remote, is_hybrid]
        - clean_location: The physical location string, stripped of remote/hybrid qualifiers (or None).
        - is_remote: True if the raw location contains remote/wfh keywords.
        - is_hybrid: True if the raw location contains hybrid keywords.
    """
    if not raw_location or not raw_location.strip():
        return None, False, False

    loc_lower = raw_location.lower()

    # Determine remote status
    is_remote = any(
        term in loc_lower
        for term in ["remote", "wfh", "work from home", "work-from-home", "telecommute"]
    )

    # Determine hybrid status
    is_hybrid = "hybrid" in loc_lower

    # Clean the physical location string
    clean_loc = raw_location

    # Regex replacements (case-insensitive) for all qualifiers
    qualifiers = [
        r"\bremote\b",
        r"\bwfh\b",
        r"\bwork\s+from\s+home\b",
        r"\bwork-from-home\b",
        r"\btelecommute\b",
        r"\bhybrid\b",
        r"\bon-site\b",
        r"\bonsite\b",
        r"\bon\s+site\b",
        r"\boffice\b",
    ]

    for pattern in qualifiers:
        clean_loc = re.sub(pattern, "", clean_loc, flags=re.IGNORECASE)

    # Remove empty parentheticals or brackets left behind (e.g. "()" or "[]")
    clean_loc = re.sub(r"\(\s*\)|\[\s*\]", "", clean_loc)

    # Clean up multiple spaces, hyphens, slashes, commas, and strip whitespace
    clean_loc = re.sub(r"[\-\–\/\\,]+", " ", clean_loc)
    clean_loc = re.sub(r"\s+", " ", clean_loc).strip()


    # If the resulting string contains no alphanumeric characters or is empty, return None
    if not clean_loc or not any(c.isalnum() for c in clean_loc):
        return None, is_remote, is_hybrid

    return clean_loc, is_remote, is_hybrid
