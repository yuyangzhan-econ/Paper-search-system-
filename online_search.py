"""
Online journal search module for academic papers.
Supports major economics, political science, and statistics journals.
"""

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus, urljoin


# Journal configurations
JOURNALS = {
    # Economics Top 5
    'aer': {
        'name': 'American Economic Review',
        'abbr': 'AER',
        'category': 'Economics Top 5',
        'base_url': 'https://www.aeaweb.org/journals/aer',
        'search_url': 'https://www.aeaweb.org/research/search',
    },
    'qje': {
        'name': 'Quarterly Journal of Economics',
        'abbr': 'QJE',
        'category': 'Economics Top 5',
        'base_url': 'https://academic.oup.com/qje',
    },
    'ecma': {
        'name': 'Econometrica',
        'abbr': 'ECMA',
        'category': 'Economics Top 5',
        'base_url': 'https://www.econometricsociety.org/publications/econometrica',
    },
    'jpe': {
        'name': 'Journal of Political Economy',
        'abbr': 'JPE',
        'category': 'Economics Top 5',
        'base_url': 'https://www.journals.uchicago.edu/toc/jpe/current',
    },
    'res': {
        'name': 'Review of Economic Studies',
        'abbr': 'RES',
        'category': 'Economics Top 5',
        'base_url': 'https://academic.oup.com/restud',
    },

    # Economics Near-Top
    'ej': {
        'name': 'Economic Journal',
        'abbr': 'EJ',
        'category': 'Economics Near-Top',
    },
    'jeea': {
        'name': 'Journal of the European Economic Association',
        'abbr': 'JEEA',
        'category': 'Economics Near-Top',
    },
    'restat': {
        'name': 'Review of Economics and Statistics',
        'abbr': 'REStat',
        'category': 'Economics Near-Top',
    },

    # AEJ Series
    'aej-applied': {
        'name': 'AEJ: Applied Economics',
        'abbr': 'AEJ:Applied',
        'category': 'AEJ Series',
    },
    'aej-policy': {
        'name': 'AEJ: Economic Policy',
        'abbr': 'AEJ:Policy',
        'category': 'AEJ Series',
    },
    'aej-macro': {
        'name': 'AEJ: Macroeconomics',
        'abbr': 'AEJ:Macro',
        'category': 'AEJ Series',
    },
    'aej-micro': {
        'name': 'AEJ: Microeconomics',
        'abbr': 'AEJ:Micro',
        'category': 'AEJ Series',
    },

    # Top Field Journals
    'jpube': {
        'name': 'Journal of Public Economics',
        'abbr': 'JPubE',
        'category': 'Top Field',
    },
    'jde': {
        'name': 'Journal of Development Economics',
        'abbr': 'JDE',
        'category': 'Top Field',
    },
    'jhe': {
        'name': 'Journal of Health Economics',
        'abbr': 'JHE',
        'category': 'Top Field',
    },
    'jet': {
        'name': 'Journal of Economic Theory',
        'abbr': 'JET',
        'category': 'Top Field',
    },
    'geb': {
        'name': 'Games and Economic Behavior',
        'abbr': 'GEB',
        'category': 'Top Field',
    },
    'jue': {
        'name': 'Journal of Urban Economics',
        'abbr': 'JUE',
        'category': 'Top Field',
    },
    'jeem': {
        'name': 'Journal of Environmental Economics and Management',
        'abbr': 'JEEM',
        'category': 'Top Field',
    },
    'jole': {
        'name': 'Journal of Labor Economics',
        'abbr': 'JOLE',
        'category': 'Top Field',
    },
    'et': {
        'name': 'Economic Theory',
        'abbr': 'ET',
        'category': 'Top Field',
    },
    'eer': {
        'name': 'European Economic Review',
        'abbr': 'EER',
        'category': 'Top Field',
    },
    'ier': {
        'name': 'International Economic Review',
        'abbr': 'IER',
        'category': 'Top Field',
    },
    'jie': {
        'name': 'Journal of International Economics',
        'abbr': 'JIE',
        'category': 'Top Field',
    },
    'joe': {
        'name': 'Journal of Econometrics',
        'abbr': 'JoE',
        'category': 'Top Field',
    },

    # Political Science Top 3
    'ajps': {
        'name': 'American Journal of Political Science',
        'abbr': 'AJPS',
        'category': 'Political Science Top 3',
    },
    'apsr': {
        'name': 'American Political Science Review',
        'abbr': 'APSR',
        'category': 'Political Science Top 3',
    },
    'jop': {
        'name': 'Journal of Politics',
        'abbr': 'JOP',
        'category': 'Political Science Top 3',
    },

    # Statistics Top 3
    'jasa': {
        'name': 'Journal of the American Statistical Association',
        'abbr': 'JASA',
        'category': 'Statistics Top 3',
    },
    'jrssb': {
        'name': 'Journal of the Royal Statistical Society: Series B',
        'abbr': 'JRSS-B',
        'category': 'Statistics Top 3',
    },
    'aos': {
        'name': 'Annals of Statistics',
        'abbr': 'AoS',
        'category': 'Statistics Top 3',
    },

    # Mathematics Top 4
    'annals': {
        'name': 'Annals of Mathematics',
        'abbr': 'Annals',
        'category': 'Mathematics Top 4',
    },
    'inventiones': {
        'name': 'Inventiones Mathematicae',
        'abbr': 'Inventiones',
        'category': 'Mathematics Top 4',
    },
    'acta': {
        'name': 'Acta Mathematica',
        'abbr': 'Acta',
        'category': 'Mathematics Top 4',
    },
    'jams': {
        'name': 'Journal of the American Mathematical Society',
        'abbr': 'JAMS',
        'category': 'Mathematics Top 4',
    },
}


# User agent for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def search_semantic_scholar(query: str, limit: int = 20, fields: Optional[List[str]] = None) -> List[Dict]:
    """
    Search papers using Semantic Scholar API (free, no auth required).
    """
    base_url = 'https://api.semanticscholar.org/graph/v1/paper/search'

    params = {
        'query': query,
        'limit': limit,
        'fields': 'title,authors,year,abstract,venue,url,citationCount,openAccessPdf',
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        papers = []
        for paper in data.get('data', []):
            authors = ', '.join([a.get('name', '') for a in paper.get('authors', [])])

            pdf_url = None
            if paper.get('openAccessPdf'):
                pdf_url = paper['openAccessPdf'].get('url')

            papers.append({
                'title': paper.get('title', ''),
                'authors': authors,
                'year': paper.get('year', ''),
                'abstract': paper.get('abstract', '') or '',
                'venue': paper.get('venue', ''),
                'url': paper.get('url', ''),
                'citations': paper.get('citationCount', 0),
                'pdf_url': pdf_url,
                'source': 'Semantic Scholar',
            })

        return papers

    except Exception as e:
        print(f"Semantic Scholar search error: {e}")
        return []


def search_crossref(query: str, limit: int = 20) -> List[Dict]:
    """
    Search papers using CrossRef API (free, no auth required).
    """
    base_url = 'https://api.crossref.org/works'

    params = {
        'query': query,
        'rows': limit,
        'select': 'title,author,published-print,abstract,container-title,DOI,URL',
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get('message', {}).get('items', []):
            # Extract title
            title = item.get('title', [''])[0] if item.get('title') else ''

            # Extract authors
            authors = []
            for author in item.get('author', []):
                name_parts = []
                if author.get('given'):
                    name_parts.append(author['given'])
                if author.get('family'):
                    name_parts.append(author['family'])
                if name_parts:
                    authors.append(' '.join(name_parts))
            authors_str = ', '.join(authors)

            # Extract year
            year = ''
            pub_date = item.get('published-print', item.get('published-online', {}))
            date_parts = pub_date.get('date-parts', [[]])
            if date_parts and date_parts[0]:
                year = str(date_parts[0][0])

            # Extract venue
            venue = item.get('container-title', [''])[0] if item.get('container-title') else ''

            # DOI link
            doi = item.get('DOI', '')
            url = f"https://doi.org/{doi}" if doi else item.get('URL', '')

            papers.append({
                'title': title,
                'authors': authors_str,
                'year': year,
                'abstract': item.get('abstract', '') or '',
                'venue': venue,
                'url': url,
                'doi': doi,
                'source': 'CrossRef',
            })

        return papers

    except Exception as e:
        print(f"CrossRef search error: {e}")
        return []


def search_arxiv(query: str, limit: int = 20) -> List[Dict]:
    """
    Search papers on arXiv.
    """
    base_url = 'http://export.arxiv.org/api/query'

    params = {
        'search_query': f'all:{query}',
        'start': 0,
        'max_results': limit,
        'sortBy': 'relevance',
        'sortOrder': 'descending',
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Parse XML response
        soup = BeautifulSoup(response.content, 'xml')
        entries = soup.find_all('entry')

        papers = []
        for entry in entries:
            title = entry.find('title')
            title = title.text.strip().replace('\n', ' ') if title else ''

            authors = []
            for author in entry.find_all('author'):
                name = author.find('name')
                if name:
                    authors.append(name.text.strip())
            authors_str = ', '.join(authors)

            published = entry.find('published')
            year = published.text[:4] if published else ''

            abstract = entry.find('summary')
            abstract = abstract.text.strip().replace('\n', ' ') if abstract else ''

            # Get PDF link
            pdf_url = None
            for link in entry.find_all('link'):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href')
                    break

            arxiv_id = entry.find('id')
            url = arxiv_id.text if arxiv_id else ''

            papers.append({
                'title': title,
                'authors': authors_str,
                'year': year,
                'abstract': abstract[:500] if abstract else '',
                'venue': 'arXiv',
                'url': url,
                'pdf_url': pdf_url,
                'source': 'arXiv',
            })

        return papers

    except Exception as e:
        print(f"arXiv search error: {e}")
        return []


def search_author(author_name: str, limit: int = 30) -> Dict:
    """
    Search for an author and their publications.
    Returns author info and their papers.
    """
    # Use Semantic Scholar for author search
    base_url = 'https://api.semanticscholar.org/graph/v1/author/search'

    params = {
        'query': author_name,
        'limit': 5,
        'fields': 'name,paperCount,citationCount,hIndex',
    }

    author_info = None
    papers = []

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('data'):
            author = data['data'][0]
            author_id = author.get('authorId')

            author_info = {
                'name': author.get('name', ''),
                'paper_count': author.get('paperCount', 0),
                'citation_count': author.get('citationCount', 0),
                'h_index': author.get('hIndex', 0),
            }

            # Get author's papers
            if author_id:
                papers_url = f'https://api.semanticscholar.org/graph/v1/author/{author_id}/papers'
                papers_params = {
                    'limit': limit,
                    'fields': 'title,year,abstract,venue,url,citationCount,openAccessPdf',
                }

                papers_response = requests.get(papers_url, params=papers_params, headers=HEADERS, timeout=10)
                if papers_response.ok:
                    papers_data = papers_response.json()
                    for paper in papers_data.get('data', []):
                        pdf_url = None
                        if paper.get('openAccessPdf'):
                            pdf_url = paper['openAccessPdf'].get('url')

                        papers.append({
                            'title': paper.get('title', ''),
                            'year': paper.get('year', ''),
                            'abstract': paper.get('abstract', '') or '',
                            'venue': paper.get('venue', ''),
                            'url': paper.get('url', ''),
                            'citations': paper.get('citationCount', 0),
                            'pdf_url': pdf_url,
                        })

    except Exception as e:
        print(f"Author search error: {e}")

    return {
        'author': author_info,
        'papers': papers,
    }


def search_by_journal(query: str, journal_keys: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
    """
    Search papers filtered by specific journals.
    Uses CrossRef with container-title filter.
    """
    if journal_keys:
        journal_names = [JOURNALS[k]['name'] for k in journal_keys if k in JOURNALS]
    else:
        journal_names = None

    # Search CrossRef with query
    base_url = 'https://api.crossref.org/works'

    params = {
        'query': query,
        'rows': limit * 2,  # Get more to filter
        'select': 'title,author,published-print,abstract,container-title,DOI,URL',
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get('message', {}).get('items', []):
            venue = item.get('container-title', [''])[0] if item.get('container-title') else ''

            # Filter by journal if specified
            if journal_names:
                if not any(jn.lower() in venue.lower() for jn in journal_names):
                    continue

            # Extract title
            title = item.get('title', [''])[0] if item.get('title') else ''

            # Extract authors
            authors = []
            for author in item.get('author', []):
                name_parts = []
                if author.get('given'):
                    name_parts.append(author['given'])
                if author.get('family'):
                    name_parts.append(author['family'])
                if name_parts:
                    authors.append(' '.join(name_parts))
            authors_str = ', '.join(authors)

            # Extract year
            year = ''
            pub_date = item.get('published-print', item.get('published-online', {}))
            date_parts = pub_date.get('date-parts', [[]])
            if date_parts and date_parts[0]:
                year = str(date_parts[0][0])

            # DOI link
            doi = item.get('DOI', '')
            url = f"https://doi.org/{doi}" if doi else item.get('URL', '')

            papers.append({
                'title': title,
                'authors': authors_str,
                'year': year,
                'abstract': item.get('abstract', '') or '',
                'venue': venue,
                'url': url,
                'doi': doi,
                'source': 'CrossRef',
            })

            if len(papers) >= limit:
                break

        return papers

    except Exception as e:
        print(f"Journal search error: {e}")
        return []


def search_all(query: str, limit: int = 20) -> List[Dict]:
    """
    Search across multiple sources and combine results.
    """
    results = []

    # Search multiple sources
    ss_results = search_semantic_scholar(query, limit=limit)
    results.extend(ss_results)

    # Add delay to avoid rate limiting
    time.sleep(0.5)

    cr_results = search_crossref(query, limit=limit)
    results.extend(cr_results)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_results = []

    for paper in results:
        title_key = re.sub(r'[^\w]', '', paper['title'].lower())[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(paper)

    # Sort by year descending
    unique_results.sort(key=lambda x: x.get('year', ''), reverse=True)

    return unique_results[:limit]


def get_journal_categories() -> Dict[str, List[Dict]]:
    """Get journals organized by category."""
    categories = {}

    for key, journal in JOURNALS.items():
        category = journal['category']
        if category not in categories:
            categories[category] = []

        categories[category].append({
            'key': key,
            'name': journal['name'],
            'abbr': journal['abbr'],
        })

    return categories
