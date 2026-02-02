"""
Advanced search engine with fuzzy matching and Chinese/English name support.
Improved search accuracy and ranking.
"""

import re
from typing import List, Dict, Set, Tuple
from pypinyin import lazy_pinyin, Style
import jieba
import database as db


# Predefined tag synonyms for common research fields
TAG_SYNONYMS = {
    '行为经济学': ['行为经济', 'behavioral economics', 'behavioral', 'behaviour'],
    '政治经济学': ['政经', '政治经济', 'political economy', 'pol econ'],
    '行为政治经济学': ['行为政经', 'behavioral political economy'],
    '决策理论': ['决策', 'decision theory', 'decision making', 'choice theory'],
    '博弈论': ['博弈', 'game theory', 'games'],
    '机制设计': ['mechanism design', 'market design'],
    '发展经济学': ['发展', 'development economics', 'development econ'],
    '劳动经济学': ['劳动', '劳经', 'labor economics', 'labour'],
    '公共经济学': ['公共', '财政', 'public economics', 'public finance'],
    '环境经济学': ['环境', 'environmental economics', 'environment econ'],
    '产业组织': ['IO', 'industrial organization', 'industrial org'],
    '国际贸易': ['贸易', 'international trade', 'trade'],
    '金融': ['finance', '金融学', 'financial economics'],
    '计量经济学': ['计量', 'econometrics', 'metrics'],
    '微观经济学': ['微观', 'microeconomics', 'micro'],
    '宏观经济学': ['宏观', 'macroeconomics', 'macro'],
    '实验经济学': ['实验', 'experimental economics', 'experiment'],
    '教育经济学': ['教育', 'education economics'],
    '健康经济学': ['健康', '卫生', 'health economics'],
    '城市经济学': ['城市', 'urban economics', 'urban'],
}


def normalize_chinese_name(name: str) -> List[str]:
    """
    Generate variations of a Chinese name.
    e.g., "周黎安" -> ["周黎安", "Lian Zhou", "Li'an Zhou", "Zhou Lian", "zhouLian"]
    """
    name = name.strip()
    if not name:
        return []

    variations = [name, name.lower()]

    # Check if it's a Chinese name (contains Chinese characters)
    if re.search(r'[\u4e00-\u9fff]', name):
        # Get pinyin
        pinyin_list = lazy_pinyin(name, style=Style.NORMAL)

        if len(pinyin_list) >= 2:
            surname = pinyin_list[0]
            given_name = ''.join(pinyin_list[1:])
            given_name_parts = pinyin_list[1:]

            # Various English name formats
            variations.extend([
                # Full pinyin
                ''.join(pinyin_list),
                ' '.join(pinyin_list),
                # Surname first
                f"{surname.capitalize()} {given_name.capitalize()}",
                f"{surname.capitalize()}, {given_name.capitalize()}",
                f"{surname} {given_name}",
                # Given name first (Western style)
                f"{given_name.capitalize()} {surname.capitalize()}",
                f"{given_name} {surname}",
                # With apostrophe for multi-character given names
                f"{'\''.join(p.capitalize() for p in given_name_parts)} {surname.capitalize()}",
                f"{surname.capitalize()} {'\''.join(p.capitalize() for p in given_name_parts)}",
                # Hyphenated
                f"{'-'.join(p.capitalize() for p in given_name_parts)} {surname.capitalize()}",
                f"{surname.capitalize()} {'-'.join(p.capitalize() for p in given_name_parts)}",
            ])

            # First letter abbreviations
            if len(given_name_parts) >= 1:
                initials = ''.join(p[0].upper() for p in given_name_parts)
                variations.append(f"{initials} {surname.capitalize()}")
                variations.append(f"{surname.capitalize()}, {initials}")
                variations.append(f"{given_name_parts[0].capitalize()} {surname.capitalize()}")

    return list(set(v.lower() for v in variations if v))


def normalize_english_name(name: str) -> List[str]:
    """
    Generate variations of an English name.
    e.g., "Li'an Zhou" -> ["Li'an Zhou", "Zhou Li'an", "Lian Zhou", "Zhou, Li'an"]
    """
    name = name.strip()
    if not name:
        return []

    variations = [name, name.lower()]

    # Remove special characters for matching
    clean_name = re.sub(r"['\-,.]", '', name)
    variations.append(clean_name.lower())
    variations.append(re.sub(r'\s+', '', clean_name.lower()))

    # Split name parts
    parts = name.replace(',', ' ').split()
    if len(parts) >= 2:
        # Try different orderings
        variations.append(' '.join(parts).lower())
        variations.append(' '.join(reversed(parts)).lower())
        variations.append(f"{parts[-1]}, {' '.join(parts[:-1])}".lower())
        variations.append(f"{parts[0]}, {' '.join(parts[1:])}".lower())
        # Without spaces
        variations.append(''.join(parts).lower())
        variations.append(''.join(reversed(parts)).lower())

    return list(set(v for v in variations if v))


def match_author(query: str, author_string: str) -> Tuple[bool, float]:
    """
    Check if query matches any author in the author string.
    Returns (match, score).
    """
    if not query or not author_string:
        return False, 0.0

    query = query.lower().strip()
    query_clean = re.sub(r"['\-,.\s]", '', query)

    # Generate query variations
    query_variations = set()
    query_variations.update(normalize_chinese_name(query))
    query_variations.update(normalize_english_name(query))
    query_variations.add(query)
    query_variations.add(query_clean)

    # Parse authors (split by comma, semicolon, and, &)
    author_string_lower = author_string.lower()
    authors = re.split(r'[,;]|\s+and\s+|\s*&\s*', author_string_lower)
    authors = [a.strip() for a in authors if a.strip()]

    best_score = 0.0

    for author in authors:
        author_clean = re.sub(r"['\-,.\s]", '', author)

        # Generate author variations
        author_variations = set()
        author_variations.update(normalize_chinese_name(author))
        author_variations.update(normalize_english_name(author))
        author_variations.add(author)
        author_variations.add(author_clean)

        # Check for exact match first
        if query in author_variations or query_clean in author_variations:
            return True, 1.0

        if author in query_variations or author_clean in query_variations:
            return True, 1.0

        # Check for partial match
        for qv in query_variations:
            if not qv:
                continue
            for av in author_variations:
                if not av:
                    continue
                # Exact substring match (must be significant portion)
                if len(qv) >= 3 and len(av) >= 3:
                    if qv == av:
                        return True, 1.0
                    if qv in av and len(qv) >= len(av) * 0.5:
                        score = len(qv) / len(av)
                        best_score = max(best_score, score)
                    elif av in qv and len(av) >= len(qv) * 0.5:
                        score = len(av) / len(qv)
                        best_score = max(best_score, score)

    return best_score >= 0.6, best_score


def expand_tag_query(query: str) -> Set[str]:
    """Expand a tag query with synonyms."""
    query = query.lower().strip()
    expanded = {query}

    # Use jieba for Chinese word segmentation
    words = list(jieba.cut(query))
    expanded.update(w for w in words if len(w) > 1)

    # Check predefined synonyms
    for canonical, synonyms in TAG_SYNONYMS.items():
        all_forms = [canonical.lower()] + [s.lower() for s in synonyms]

        # If query matches any form, add all forms
        if any(query == f for f in all_forms):
            expanded.update(all_forms)
        elif any(query in f or f in query for f in all_forms):
            expanded.update(all_forms)

    return expanded


def match_tag(query: str, tag_string: str) -> Tuple[bool, float]:
    """
    Check if query matches any tag.
    Returns (match, score) where score indicates match quality.
    """
    if not query or not tag_string:
        return False, 0.0

    query = query.lower().strip()
    tags = [t.strip().lower() for t in tag_string.split(',') if t.strip()]

    # Expand query with synonyms
    expanded_queries = expand_tag_query(query)

    best_score = 0.0

    for tag in tags:
        # Exact match - highest score
        if query == tag:
            return True, 1.0

        # Check expanded queries for exact match
        for eq in expanded_queries:
            if eq == tag:
                return True, 0.95

        # Direct containment
        if query in tag:
            score = len(query) / len(tag) * 0.8
            best_score = max(best_score, score)
        elif tag in query:
            score = len(tag) / len(query) * 0.7
            best_score = max(best_score, score)

        # Expanded query match
        for eq in expanded_queries:
            if eq in tag:
                score = 0.6 * len(eq) / len(tag)
                best_score = max(best_score, score)
            elif tag in eq:
                score = 0.5 * len(tag) / len(eq)
                best_score = max(best_score, score)

    return best_score >= 0.4, best_score


def calculate_relevance_score(paper: Dict, query: str) -> Tuple[float, int]:
    """
    Calculate relevance score for a paper given a query.
    Returns (score, position) where position is the earliest position of query in details.

    Scoring priority (highest to lowest):
    1. Title match (20-25 points)
    2. Author match (15 points)
    3. Journal match (12 points)
    4. Year match (10 points)
    5. Tag match (8 points)
    6. Keyword match (6 points)
    7. Abstract match (4 points)
    8. Details/first page match (2-3 points + small position bonus)
    9. Filename match (1 point)
    """
    score = 0.0
    position = 999999  # Default high position for papers without match in details
    query_lower = query.lower().strip()

    # Empty query returns all
    if not query_lower:
        return 1.0, 0

    title = paper.get('title', '').lower()
    authors = paper.get('authors', '')
    tags = paper.get('tags', '')
    keywords = paper.get('keywords', '').lower()
    filename = paper.get('file_name', '').lower()
    abstract = paper.get('abstract', '').lower()
    details = paper.get('details', '').lower()  # First page content
    journal = paper.get('journal', '').lower()  # Journal name
    year = paper.get('year', '')  # Publication year

    # Title match (highest weight - 20-25 points)
    if query_lower in title:
        # Exact word match in title
        if re.search(r'\b' + re.escape(query_lower) + r'\b', title):
            score += 20.0
            # Title starts with query
            if title.startswith(query_lower):
                score += 5.0
        else:
            score += 12.0

    # Author match (15 points)
    author_match, author_score = match_author(query, authors)
    if author_match:
        score += 15.0 * author_score

    # Journal match (12 points - important for filtering by publication venue)
    if journal and query_lower in journal:
        if re.search(r'\b' + re.escape(query_lower) + r'\b', journal):
            score += 12.0
        else:
            score += 8.0

    # Year match (10 points - searching by year)
    if year and query_lower == year:
        score += 10.0
    elif year and query_lower in year:
        score += 5.0

    # Tag match (8 points)
    tag_match, tag_score = match_tag(query, tags)
    if tag_match:
        score += 8.0 * tag_score

    # Keyword match (6 points)
    if query_lower in keywords:
        if re.search(r'\b' + re.escape(query_lower) + r'\b', keywords):
            score += 6.0
        else:
            score += 3.0

    # Abstract match (4 points)
    if query_lower in abstract:
        if re.search(r'\b' + re.escape(query_lower) + r'\b', abstract):
            score += 4.0
        else:
            score += 2.0

    # Details (first page content) match - lower priority, but still useful for full-text search
    if details and query_lower in details:
        # Find position (excluding leading spaces)
        details_stripped = details.lstrip()
        pos = details_stripped.find(query_lower)
        if pos >= 0:
            position = pos
            # Reduced position-based bonus: max 3 points for position 0
            position_bonus = max(0, 3.0 - (pos / 500.0))
            score += position_bonus

        if re.search(r'\b' + re.escape(query_lower) + r'\b', details):
            score += 2.0  # Reduced weight for details match
        else:
            score += 1.0  # Partial match

    # Filename match (lowest priority - 1 point)
    if query_lower in filename:
        score += 1.0

    return score, position


def parse_advanced_query(query: str) -> dict:
    """
    Parse advanced search query with operators.
    + means OR
    * means AND
    () for grouping

    Returns a structure: {'type': 'and'|'or'|'term', 'terms': [...]}
    """
    query = query.strip()

    # Simple term
    if '+' not in query and '*' not in query and '(' not in query:
        return {'type': 'term', 'value': query}

    # Handle parentheses first (simple level, not nested)
    # For simplicity, we'll handle flat structure

    # Split by OR first (+)
    if '+' in query:
        parts = [p.strip() for p in query.split('+') if p.strip()]
        if len(parts) > 1:
            return {
                'type': 'or',
                'terms': [parse_advanced_query(p) for p in parts]
            }

    # Then split by AND (*)
    if '*' in query:
        parts = [p.strip() for p in query.split('*') if p.strip()]
        if len(parts) > 1:
            return {
                'type': 'and',
                'terms': [parse_advanced_query(p) for p in parts]
            }

    # Remove parentheses if wrapping
    if query.startswith('(') and query.endswith(')'):
        return parse_advanced_query(query[1:-1])

    return {'type': 'term', 'value': query}


def evaluate_query(paper: Dict, parsed_query: dict) -> Tuple[float, int]:
    """Evaluate a parsed query against a paper. Returns (score, position)."""
    if parsed_query['type'] == 'term':
        return calculate_relevance_score(paper, parsed_query['value'])
    elif parsed_query['type'] == 'and':
        # All terms must match
        results = [evaluate_query(paper, term) for term in parsed_query['terms']]
        scores = [r[0] for r in results]
        positions = [r[1] for r in results]
        if all(s > 0 for s in scores):
            return sum(scores), min(positions)
        return 0.0, 999999
    elif parsed_query['type'] == 'or':
        # Any term can match
        results = [evaluate_query(paper, term) for term in parsed_query['terms']]
        if results:
            # Return result with highest score
            best = max(results, key=lambda x: x[0])
            return best
        return 0.0, 999999

    return 0.0, 999999


def search(query: str, limit: int = 100) -> List[Dict]:
    """
    Perform comprehensive search across all papers.
    Returns papers sorted by relevance score.

    Advanced syntax:
    - Use + for OR (matches any term)
    - Use * for AND (must match all terms)
    - Use () for grouping (basic support)

    Examples:
    - "行为经济 + 决策" - matches either term
    - "周黎安 * 行为" - must match both
    - "经济 * (行为 + 决策)" - matches 经济 AND (行为 OR 决策)
    """
    query = query.strip() if query else ''

    # Get all papers
    all_papers = db.get_all_papers()

    if not query:
        # Return all papers sorted by updated_at
        return all_papers[:limit]

    # Check for advanced syntax
    has_advanced = '+' in query or '*' in query or '(' in query

    # Calculate scores for all papers
    scored_papers = []

    if has_advanced:
        parsed = parse_advanced_query(query)
        for paper in all_papers:
            score, position = evaluate_query(paper, parsed)
            if score > 0:
                paper_copy = dict(paper)
                paper_copy['relevance_score'] = score
                paper_copy['details_position'] = position
                scored_papers.append(paper_copy)
    else:
        for paper in all_papers:
            score, position = calculate_relevance_score(paper, query)
            if score > 0:
                paper_copy = dict(paper)
                paper_copy['relevance_score'] = score
                paper_copy['details_position'] = position
                scored_papers.append(paper_copy)

    # Sort by score descending, then by position in details ascending, then by title
    scored_papers.sort(key=lambda p: (-p.get('relevance_score', 0), p.get('details_position', 999999), p.get('title', '').lower()))

    return scored_papers[:limit]


def get_suggestions(query: str, limit: int = 10) -> List[Dict]:
    """
    Get search suggestions with type hints.
    Returns list of {text, type, count, icon} items.
    """
    if not query or len(query) < 1:
        return []

    query = query.lower().strip()
    suggestions = []

    # Get all unique values
    all_papers = db.get_all_papers()

    # Collect unique authors
    author_counts = {}
    for paper in all_papers:
        for author in re.split(r'[,;]|\s+and\s+|\s*&\s*', paper.get('authors', '')):
            author = author.strip()
            if author and query in author.lower():
                author_counts[author] = author_counts.get(author, 0) + 1

    # Collect unique tags
    tag_counts = {}
    for paper in all_papers:
        for tag in paper.get('tags', '').split(','):
            tag = tag.strip()
            if tag and query in tag.lower():
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Collect matching titles
    titles = []
    for paper in all_papers:
        title = paper.get('title', '')
        if query in title.lower():
            titles.append(title)

    # Build suggestions - prioritize by count
    for author, count in sorted(author_counts.items(), key=lambda x: -x[1])[:limit]:
        suggestions.append({
            'text': author,
            'type': 'author',
            'count': count,
            'icon': '👤'
        })

    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:limit]:
        suggestions.append({
            'text': tag,
            'type': 'tag',
            'count': count,
            'icon': '🏷️'
        })

    for title in titles[:5]:
        suggestions.append({
            'text': title,
            'type': 'title',
            'count': 1,
            'icon': '📄'
        })

    # Sort by count and limit
    suggestions.sort(key=lambda x: -x['count'])
    return suggestions[:limit]


def init_default_synonyms():
    """Initialize default tag synonyms in database."""
    for canonical, synonyms in TAG_SYNONYMS.items():
        for synonym in synonyms:
            db.add_tag_synonym(canonical, synonym)


# Initialize default synonyms
init_default_synonyms()
