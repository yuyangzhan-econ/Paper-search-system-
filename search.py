"""
Advanced search engine with fuzzy matching and Chinese/English name support.
"""

import re
from typing import List, Dict, Set, Tuple
from pypinyin import lazy_pinyin, Style
import jieba
import database as db


# Predefined tag synonyms for common research fields
TAG_SYNONYMS = {
    '行为经济学': ['行为经济', '行为', 'behavioral economics', 'behavioral', 'behaviour'],
    '政治经济学': ['政经', '政治经济', 'political economy', 'pol econ'],
    '行为政治经济学': ['行为政经', 'behavioral political economy'],
    '决策理论': ['决策', 'decision theory', 'decision making', 'choice theory'],
    '博弈论': ['博弈', 'game theory', 'games'],
    '机制设计': ['mechanism design', 'market design'],
    '发展经济学': ['发展', 'development economics', 'development'],
    '劳动经济学': ['劳动', '劳经', 'labor economics', 'labour'],
    '公共经济学': ['公共', '财政', 'public economics', 'public finance'],
    '环境经济学': ['环境', 'environmental economics', 'environment'],
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
                # Given name first (Western style)
                f"{given_name.capitalize()} {surname.capitalize()}",
                # With apostrophe for multi-character given names
                f"{'\''.join(p.capitalize() for p in given_name_parts)} {surname.capitalize()}",
                f"{surname.capitalize()} {'\''.join(p.capitalize() for p in given_name_parts)}",
                # Lowercase versions
                f"{surname} {given_name}",
                f"{given_name} {surname}",
            ])

            # First letter abbreviations
            if len(given_name_parts) >= 2:
                initials = ''.join(p[0].upper() for p in given_name_parts)
                variations.append(f"{initials} {surname.capitalize()}")
                variations.append(f"{surname.capitalize()}, {initials}")

    return list(set(v for v in variations if v))


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

    # Split name parts
    parts = name.replace(',', ' ').split()
    if len(parts) >= 2:
        # Try different orderings
        variations.append(' '.join(parts))
        variations.append(' '.join(reversed(parts)))
        variations.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
        variations.append(f"{parts[0]}, {' '.join(parts[1:])}")

    return list(set(v for v in variations if v))


def match_author(query: str, author_string: str) -> bool:
    """Check if query matches any author in the author string."""
    if not query or not author_string:
        return False

    query = query.lower().strip()
    authors = [a.strip().lower() for a in author_string.split(',')]

    # Generate query variations
    query_variations = set()
    query_variations.update(normalize_chinese_name(query))
    query_variations.update(normalize_english_name(query))
    query_variations.add(query)

    # Check each author
    for author in authors:
        # Direct match
        if query in author or author in query:
            return True

        # Generate author variations
        author_variations = set()
        author_variations.update(normalize_chinese_name(author))
        author_variations.update(normalize_english_name(author))
        author_variations.add(author)

        # Check for any match
        for qv in query_variations:
            for av in author_variations:
                if qv and av and (qv in av or av in qv):
                    return True

    return False


def expand_tag_query(query: str) -> Set[str]:
    """Expand a tag query with synonyms."""
    query = query.lower().strip()
    expanded = {query}

    # Use jieba for Chinese word segmentation
    words = list(jieba.cut(query))
    expanded.update(words)

    # Check predefined synonyms
    for canonical, synonyms in TAG_SYNONYMS.items():
        all_forms = [canonical.lower()] + [s.lower() for s in synonyms]

        # If query matches any form, add all forms
        if any(query in f or f in query for f in all_forms):
            expanded.update(all_forms)

        # Partial matching
        for word in words:
            if any(word in f or f in word for f in all_forms):
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
    tags = [t.strip().lower() for t in tag_string.split(',')]

    # Expand query with synonyms
    expanded_queries = expand_tag_query(query)

    best_score = 0.0

    for tag in tags:
        # Exact match
        if query == tag:
            return True, 1.0

        # Direct containment
        if query in tag:
            score = len(query) / len(tag)
            best_score = max(best_score, score)
        elif tag in query:
            score = len(tag) / len(query)
            best_score = max(best_score, score)

        # Expanded query match
        for eq in expanded_queries:
            if eq in tag or tag in eq:
                score = 0.7 * min(len(eq), len(tag)) / max(len(eq), len(tag))
                best_score = max(best_score, score)

    return best_score > 0.3, best_score


def calculate_relevance_score(paper: Dict, query: str) -> float:
    """Calculate relevance score for a paper given a query."""
    score = 0.0
    query = query.lower()

    # Title match (highest weight)
    if query in paper.get('title', '').lower():
        score += 10.0
        if paper.get('title', '').lower().startswith(query):
            score += 5.0

    # Author match
    if match_author(query, paper.get('authors', '')):
        score += 8.0

    # Tag match
    tag_match, tag_score = match_tag(query, paper.get('tags', ''))
    if tag_match:
        score += 6.0 * tag_score

    # Keyword match
    if query in paper.get('keywords', '').lower():
        score += 4.0

    # Filename match
    if query in paper.get('file_name', '').lower():
        score += 2.0

    return score


def search(query: str, limit: int = 50) -> List[Dict]:
    """
    Perform comprehensive search across all papers.
    Combines FTS search with fuzzy matching.
    """
    if not query or not query.strip():
        return db.get_all_papers()[:limit]

    query = query.strip()

    # Get all papers for fuzzy matching
    all_papers = db.get_all_papers()

    # Calculate scores for all papers
    scored_papers = []
    for paper in all_papers:
        score = calculate_relevance_score(paper, query)
        if score > 0:
            paper_with_score = dict(paper)
            paper_with_score['relevance_score'] = score
            scored_papers.append(paper_with_score)

    # Also try FTS search
    fts_results = db.search_papers_fts(query, limit)
    fts_ids = {p['id'] for p in fts_results}

    # Add FTS results that weren't found by fuzzy search
    for paper in fts_results:
        if not any(p['id'] == paper['id'] for p in scored_papers):
            paper_with_score = dict(paper)
            paper_with_score['relevance_score'] = 5.0  # Base score for FTS matches
            scored_papers.append(paper_with_score)

    # Sort by score descending
    scored_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)

    return scored_papers[:limit]


def get_suggestions(query: str, limit: int = 10) -> List[Dict]:
    """
    Get search suggestions with type hints.
    Returns list of {text, type, count} items.
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
        for author in paper.get('authors', '').split(','):
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
        if query in paper.get('title', '').lower():
            titles.append(paper['title'])

    # Build suggestions
    for author, count in sorted(author_counts.items(), key=lambda x: -x[1]):
        suggestions.append({
            'text': author,
            'type': 'author',
            'count': count,
            'icon': '👤'
        })

    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
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
