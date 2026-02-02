"""
DOI Service - Extract DOI from PDFs and fetch metadata from CrossRef.
Designed for speed: local DOI extraction is fast, API calls are optional/async.
"""

import re
import json
import urllib.request
import urllib.error
import time
from typing import Dict, Optional
from functools import lru_cache

# DOI pattern - matches most academic DOIs
DOI_PATTERN = re.compile(
    r'\b(10\.\d{4,}/[^\s\]>\)"\']+)',
    re.IGNORECASE
)

# Alternative patterns for DOIs that might be formatted differently
DOI_URL_PATTERN = re.compile(
    r'(?:doi\.org/|doi:|DOI:?\s*)(10\.\d{4,}/[^\s\]>\)"\']+)',
    re.IGNORECASE
)

# CrossRef API endpoint
CROSSREF_API_URL = "https://api.crossref.org/works/"

# Cache for API results (avoid repeated calls)
_metadata_cache = {}


def extract_doi_from_text(text: str) -> Optional[str]:
    """
    Extract DOI from text (fast, local operation).
    Returns the first valid DOI found, or None.
    """
    if not text:
        return None

    # Try URL pattern first (more specific)
    match = DOI_URL_PATTERN.search(text)
    if match:
        doi = clean_doi(match.group(1))
        if doi:
            return doi

    # Try general pattern
    match = DOI_PATTERN.search(text)
    if match:
        doi = clean_doi(match.group(1))
        if doi:
            return doi

    return None


def clean_doi(doi: str) -> Optional[str]:
    """Clean and validate a DOI string."""
    if not doi:
        return None

    # Remove trailing punctuation that might have been captured
    doi = doi.rstrip('.,;:)\'">')

    # Remove any HTML entities
    doi = doi.replace('&lt;', '<').replace('&gt;', '>')

    # Basic validation
    if not doi.startswith('10.'):
        return None

    if len(doi) < 10:
        return None

    return doi


def fetch_metadata_from_crossref(doi: str, timeout: float = 5.0) -> Optional[Dict]:
    """
    Fetch metadata from CrossRef API.
    Returns dict with title, authors, journal, year, etc.

    This is the slower operation - use sparingly or in background.
    """
    if not doi:
        return None

    # Check cache first
    if doi in _metadata_cache:
        return _metadata_cache[doi]

    try:
        url = CROSSREF_API_URL + urllib.request.quote(doi)
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Paper-Search-System/1.0 (mailto:contact@example.com)',
                'Accept': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('status') != 'ok':
                return None

            message = data.get('message', {})

            # Extract metadata
            result = {
                'doi': doi,
                'title': '',
                'authors': '',
                'journal': '',
                'year': '',
                'volume': '',
                'issue': '',
                'pages': '',
                'publisher': '',
                'url': f'https://doi.org/{doi}',
            }

            # Title
            titles = message.get('title', [])
            if titles:
                result['title'] = titles[0]

            # Authors
            authors_list = message.get('author', [])
            author_names = []
            for author in authors_list[:10]:  # Limit to first 10 authors
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    if given:
                        author_names.append(f"{given} {family}")
                    else:
                        author_names.append(family)
            result['authors'] = ', '.join(author_names)

            # Journal
            container = message.get('container-title', [])
            if container:
                result['journal'] = container[0]

            # Year
            published = message.get('published-print') or message.get('published-online') or message.get('created')
            if published:
                date_parts = published.get('date-parts', [[]])
                if date_parts and date_parts[0]:
                    result['year'] = str(date_parts[0][0])

            # Volume, Issue, Pages
            result['volume'] = message.get('volume', '')
            result['issue'] = message.get('issue', '')
            result['pages'] = message.get('page', '')
            result['publisher'] = message.get('publisher', '')

            # Cache the result
            _metadata_cache[doi] = result

            return result

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # DOI not found in CrossRef
            _metadata_cache[doi] = None
        # For rate limits (429) or other errors, don't cache
        return None
    except Exception:
        return None


def fetch_metadata_batch(dois: list, delay: float = 0.1, timeout: float = 5.0) -> Dict[str, Dict]:
    """
    Fetch metadata for multiple DOIs with rate limiting.
    Returns dict mapping DOI -> metadata.
    """
    results = {}

    for doi in dois:
        if doi in _metadata_cache:
            results[doi] = _metadata_cache[doi]
            continue

        metadata = fetch_metadata_from_crossref(doi, timeout)
        results[doi] = metadata

        # Rate limiting - be nice to CrossRef
        if delay > 0:
            time.sleep(delay)

    return results


def clear_cache():
    """Clear the metadata cache."""
    global _metadata_cache
    _metadata_cache = {}


def get_cache_size() -> int:
    """Get number of cached entries."""
    return len(_metadata_cache)
