"""
Online journal search module for academic papers.
Supports major economics, political science, and statistics journals.
Uses OpenAlex, Semantic Scholar, CrossRef, and arXiv APIs.
"""

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus, urljoin


# Journal configurations with OpenAlex source IDs
JOURNALS = {
    # Economics Top 5
    'aer': {
        'name': 'American Economic Review',
        'abbr': 'AER',
        'category': 'Economics Top 5',
        'issn': '0002-8282',
    },
    'qje': {
        'name': 'Quarterly Journal of Economics',
        'abbr': 'QJE',
        'category': 'Economics Top 5',
        'issn': '0033-5533',
    },
    'ecma': {
        'name': 'Econometrica',
        'abbr': 'ECMA',
        'category': 'Economics Top 5',
        'issn': '0012-9682',
    },
    'jpe': {
        'name': 'Journal of Political Economy',
        'abbr': 'JPE',
        'category': 'Economics Top 5',
        'issn': '0022-3808',
    },
    'res': {
        'name': 'Review of Economic Studies',
        'abbr': 'RES',
        'category': 'Economics Top 5',
        'issn': '0034-6527',
    },

    # Economics Near-Top
    'ej': {
        'name': 'Economic Journal',
        'abbr': 'EJ',
        'category': 'Economics Near-Top',
        'issn': '0013-0133',
    },
    'jeea': {
        'name': 'Journal of the European Economic Association',
        'abbr': 'JEEA',
        'category': 'Economics Near-Top',
        'issn': '1542-4766',
    },
    'restat': {
        'name': 'Review of Economics and Statistics',
        'abbr': 'REStat',
        'category': 'Economics Near-Top',
        'issn': '0034-6535',
    },

    # AEJ Series
    'aej-applied': {
        'name': 'AEJ: Applied Economics',
        'abbr': 'AEJ:Applied',
        'category': 'AEJ Series',
        'issn': '1945-7782',
    },
    'aej-policy': {
        'name': 'AEJ: Economic Policy',
        'abbr': 'AEJ:Policy',
        'category': 'AEJ Series',
        'issn': '1945-7731',
    },
    'aej-macro': {
        'name': 'AEJ: Macroeconomics',
        'abbr': 'AEJ:Macro',
        'category': 'AEJ Series',
        'issn': '1945-7707',
    },
    'aej-micro': {
        'name': 'AEJ: Microeconomics',
        'abbr': 'AEJ:Micro',
        'category': 'AEJ Series',
        'issn': '1945-7669',
    },

    # Top Field Journals
    'jpube': {
        'name': 'Journal of Public Economics',
        'abbr': 'JPubE',
        'category': 'Top Field',
        'issn': '0047-2727',
    },
    'jde': {
        'name': 'Journal of Development Economics',
        'abbr': 'JDE',
        'category': 'Top Field',
        'issn': '0304-3878',
    },
    'jhe': {
        'name': 'Journal of Health Economics',
        'abbr': 'JHE',
        'category': 'Top Field',
        'issn': '0167-6296',
    },
    'jet': {
        'name': 'Journal of Economic Theory',
        'abbr': 'JET',
        'category': 'Top Field',
        'issn': '0022-0531',
    },
    'geb': {
        'name': 'Games and Economic Behavior',
        'abbr': 'GEB',
        'category': 'Top Field',
        'issn': '0899-8256',
    },
    'jue': {
        'name': 'Journal of Urban Economics',
        'abbr': 'JUE',
        'category': 'Top Field',
        'issn': '0094-1190',
    },
    'jeem': {
        'name': 'Journal of Environmental Economics and Management',
        'abbr': 'JEEM',
        'category': 'Top Field',
        'issn': '0095-0696',
    },
    'jole': {
        'name': 'Journal of Labor Economics',
        'abbr': 'JOLE',
        'category': 'Top Field',
        'issn': '0734-306X',
    },
    'et': {
        'name': 'Economic Theory',
        'abbr': 'ET',
        'category': 'Top Field',
        'issn': '0938-2259',
    },
    'eer': {
        'name': 'European Economic Review',
        'abbr': 'EER',
        'category': 'Top Field',
        'issn': '0014-2921',
    },
    'ier': {
        'name': 'International Economic Review',
        'abbr': 'IER',
        'category': 'Top Field',
        'issn': '0020-6598',
    },
    'jie': {
        'name': 'Journal of International Economics',
        'abbr': 'JIE',
        'category': 'Top Field',
        'issn': '0022-1996',
    },
    'joe': {
        'name': 'Journal of Econometrics',
        'abbr': 'JoE',
        'category': 'Top Field',
        'issn': '0304-4076',
    },
    'jf': {
        'name': 'Journal of Finance',
        'abbr': 'JF',
        'category': 'Top Field',
        'issn': '0022-1082',
    },
    'jfe': {
        'name': 'Journal of Financial Economics',
        'abbr': 'JFE',
        'category': 'Top Field',
        'issn': '0304-405X',
    },
    'rfs': {
        'name': 'Review of Financial Studies',
        'abbr': 'RFS',
        'category': 'Top Field',
        'issn': '0893-9454',
    },

    # Political Science Top 3
    'ajps': {
        'name': 'American Journal of Political Science',
        'abbr': 'AJPS',
        'category': 'Political Science Top 3',
        'issn': '0092-5853',
    },
    'apsr': {
        'name': 'American Political Science Review',
        'abbr': 'APSR',
        'category': 'Political Science Top 3',
        'issn': '0003-0554',
    },
    'jop': {
        'name': 'Journal of Politics',
        'abbr': 'JOP',
        'category': 'Political Science Top 3',
        'issn': '0022-3816',
    },

    # Statistics Top 3
    'jasa': {
        'name': 'Journal of the American Statistical Association',
        'abbr': 'JASA',
        'category': 'Statistics Top 3',
        'issn': '0162-1459',
    },
    'jrssb': {
        'name': 'Journal of the Royal Statistical Society: Series B',
        'abbr': 'JRSS-B',
        'category': 'Statistics Top 3',
        'issn': '1369-7412',
    },
    'aos': {
        'name': 'Annals of Statistics',
        'abbr': 'AoS',
        'category': 'Statistics Top 3',
        'issn': '0090-5364',
    },
}


# User agent for requests
HEADERS = {
    'User-Agent': 'PaperSearch/1.0 (mailto:research@example.com)',
    'Accept': 'application/json',
}


def search_openalex(query: str, limit: int = 25, filter_econ: bool = False) -> List[Dict]:
    """
    Search papers using OpenAlex API (free, comprehensive).
    OpenAlex is the successor to Microsoft Academic Graph.
    """
    base_url = 'https://api.openalex.org/works'

    # Build filter for economics-related works
    filters = [f'default.search:{query}']
    if filter_econ:
        # Filter by economics concept
        filters.append('concepts.id:C162324750')  # Economics concept ID

    params = {
        'search': query,
        'per_page': limit,
        'sort': 'relevance_score:desc',
        'select': 'id,title,authorships,publication_year,primary_location,abstract_inverted_index,cited_by_count,doi,open_access',
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for work in data.get('results', []):
            # Extract authors
            authors = []
            for authorship in work.get('authorships', [])[:5]:  # Limit to first 5 authors
                author = authorship.get('author', {})
                name = author.get('display_name', '')
                if name:
                    authors.append(name)
            authors_str = ', '.join(authors)
            if len(work.get('authorships', [])) > 5:
                authors_str += ' et al.'

            # Extract venue
            location = work.get('primary_location', {}) or {}
            source = location.get('source', {}) or {}
            venue = source.get('display_name', '')

            # Reconstruct abstract from inverted index
            abstract = ''
            abstract_inv = work.get('abstract_inverted_index', {})
            if abstract_inv:
                # Reconstruct abstract
                word_positions = []
                for word, positions in abstract_inv.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = ' '.join(word for _, word in word_positions)[:500]

            # Get URL
            doi = work.get('doi', '')
            url = doi if doi else work.get('id', '')

            # Check for open access PDF
            pdf_url = None
            oa = work.get('open_access', {})
            if oa.get('is_oa') and oa.get('oa_url'):
                pdf_url = oa.get('oa_url')

            papers.append({
                'title': work.get('title', ''),
                'authors': authors_str,
                'year': str(work.get('publication_year', '')),
                'abstract': abstract,
                'venue': venue,
                'url': url,
                'doi': doi.replace('https://doi.org/', '') if doi else '',
                'citations': work.get('cited_by_count', 0),
                'pdf_url': pdf_url,
                'source': 'OpenAlex',
            })

        return papers

    except Exception as e:
        print(f"OpenAlex search error: {e}")
        return []


def search_econ_papers(query: str, limit: int = 25) -> List[Dict]:
    """
    Search specifically for economics papers using OpenAlex with economics filter.
    """
    return search_openalex(query, limit, filter_econ=True)


def search_semantic_scholar(query: str, limit: int = 20) -> List[Dict]:
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
                'year': str(paper.get('year', '')),
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
    Search for an author and their publications using OpenAlex.
    """
    # First, search for the author
    author_url = 'https://api.openalex.org/authors'
    params = {
        'search': author_name,
        'per_page': 5,
    }

    author_info = None
    papers = []

    try:
        response = requests.get(author_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            author = data['results'][0]
            author_id = author.get('id', '').split('/')[-1]

            author_info = {
                'name': author.get('display_name', ''),
                'paper_count': author.get('works_count', 0),
                'citation_count': author.get('cited_by_count', 0),
                'h_index': author.get('summary_stats', {}).get('h_index', 0),
            }

            # Get author's papers
            works_url = 'https://api.openalex.org/works'
            works_params = {
                'filter': f'author.id:{author.get("id")}',
                'per_page': limit,
                'sort': 'cited_by_count:desc',
                'select': 'id,title,publication_year,primary_location,cited_by_count,doi,open_access',
            }

            works_response = requests.get(works_url, params=works_params, headers=HEADERS, timeout=10)
            if works_response.ok:
                works_data = works_response.json()
                for work in works_data.get('results', []):
                    location = work.get('primary_location', {}) or {}
                    source = location.get('source', {}) or {}
                    venue = source.get('display_name', '')

                    doi = work.get('doi', '')
                    url = doi if doi else work.get('id', '')

                    pdf_url = None
                    oa = work.get('open_access', {})
                    if oa.get('is_oa') and oa.get('oa_url'):
                        pdf_url = oa.get('oa_url')

                    papers.append({
                        'title': work.get('title', ''),
                        'year': str(work.get('publication_year', '')),
                        'venue': venue,
                        'url': url,
                        'citations': work.get('cited_by_count', 0),
                        'pdf_url': pdf_url,
                    })

    except Exception as e:
        print(f"Author search error: {e}")

    return {
        'author': author_info,
        'papers': papers,
    }


def search_by_journal(query: str, journal_keys: Optional[List[str]] = None, limit: int = 25) -> List[Dict]:
    """
    Search papers filtered by specific journals using OpenAlex.
    """
    base_url = 'https://api.openalex.org/works'

    # Build ISSN filter
    issn_filter = None
    if journal_keys:
        issns = [JOURNALS[k].get('issn') for k in journal_keys if k in JOURNALS and JOURNALS[k].get('issn')]
        if issns:
            issn_filter = '|'.join(issns)

    params = {
        'search': query,
        'per_page': limit,
        'sort': 'relevance_score:desc',
        'select': 'id,title,authorships,publication_year,primary_location,abstract_inverted_index,cited_by_count,doi,open_access',
    }

    if issn_filter:
        params['filter'] = f'primary_location.source.issn:{issn_filter}'

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for work in data.get('results', []):
            # Extract authors
            authors = []
            for authorship in work.get('authorships', [])[:5]:
                author = authorship.get('author', {})
                name = author.get('display_name', '')
                if name:
                    authors.append(name)
            authors_str = ', '.join(authors)

            # Extract venue
            location = work.get('primary_location', {}) or {}
            source = location.get('source', {}) or {}
            venue = source.get('display_name', '')

            # Reconstruct abstract
            abstract = ''
            abstract_inv = work.get('abstract_inverted_index', {})
            if abstract_inv:
                word_positions = []
                for word, positions in abstract_inv.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = ' '.join(word for _, word in word_positions)[:500]

            doi = work.get('doi', '')
            url = doi if doi else work.get('id', '')

            pdf_url = None
            oa = work.get('open_access', {})
            if oa.get('is_oa') and oa.get('oa_url'):
                pdf_url = oa.get('oa_url')

            papers.append({
                'title': work.get('title', ''),
                'authors': authors_str,
                'year': str(work.get('publication_year', '')),
                'abstract': abstract,
                'venue': venue,
                'url': url,
                'doi': doi.replace('https://doi.org/', '') if doi else '',
                'citations': work.get('cited_by_count', 0),
                'pdf_url': pdf_url,
                'source': 'OpenAlex',
            })

        return papers

    except Exception as e:
        print(f"Journal search error: {e}")
        return []


def search_all(query: str, limit: int = 25) -> List[Dict]:
    """
    Search across multiple sources and combine results.
    Prioritizes OpenAlex for comprehensive coverage.
    """
    results = []

    # Primary search with OpenAlex (most comprehensive)
    oa_results = search_openalex(query, limit=limit)
    results.extend(oa_results)

    # Add Semantic Scholar results
    time.sleep(0.3)
    ss_results = search_semantic_scholar(query, limit=min(limit, 15))
    results.extend(ss_results)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_results = []

    for paper in results:
        title = paper.get('title', '')
        if not title:
            continue
        title_key = re.sub(r'[^\w]', '', title.lower())[:50]
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(paper)

    # Sort by citations (descending), then by year (descending)
    unique_results.sort(key=lambda x: (-(x.get('citations', 0) or 0), -(int(x.get('year') or 0) if x.get('year') else 0)))

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
