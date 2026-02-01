"""
Online journal search module for academic papers.
Supports major economics, political science, and statistics journals.
Based on Econ-Paper-Search project structure.
Uses OpenAlex API for comprehensive coverage.
"""

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus

# Complete journal database based on Econ-Paper-Search
JOURNALS = {
    # ========== Economics Top 5 ==========
    'aer': {'name': 'American Economic Review', 'abbr': 'AER', 'category': 'Top 5', 'issn': '0002-8282'},
    'jpe': {'name': 'Journal of Political Economy', 'abbr': 'JPE', 'category': 'Top 5', 'issn': '0022-3808'},
    'qje': {'name': 'Quarterly Journal of Economics', 'abbr': 'QJE', 'category': 'Top 5', 'issn': '0033-5533'},
    'ecta': {'name': 'Econometrica', 'abbr': 'ECMA', 'category': 'Top 5', 'issn': '0012-9682'},
    'restud': {'name': 'Review of Economic Studies', 'abbr': 'RES', 'category': 'Top 5', 'issn': '0034-6527'},

    # ========== AEJ Series ==========
    'aejmac': {'name': 'AEJ: Macroeconomics', 'abbr': 'AEJ:Macro', 'category': 'AEJ', 'issn': '1945-7707'},
    'aejmic': {'name': 'AEJ: Microeconomics', 'abbr': 'AEJ:Micro', 'category': 'AEJ', 'issn': '1945-7669'},
    'aejapp': {'name': 'AEJ: Applied Economics', 'abbr': 'AEJ:Applied', 'category': 'AEJ', 'issn': '1945-7782'},
    'aejpol': {'name': 'AEJ: Economic Policy', 'abbr': 'AEJ:Policy', 'category': 'AEJ', 'issn': '1945-7731'},
    'aeri': {'name': 'AER: Insights', 'abbr': 'AER:I', 'category': 'AEJ', 'issn': '2640-205X'},

    # ========== General Economics ==========
    'restat': {'name': 'Review of Economics and Statistics', 'abbr': 'REStat', 'category': 'General', 'issn': '0034-6535'},
    'jeea': {'name': 'Journal of the European Economic Association', 'abbr': 'JEEA', 'category': 'General', 'issn': '1542-4766'},
    'eer': {'name': 'European Economic Review', 'abbr': 'EER', 'category': 'General', 'issn': '0014-2921'},
    'ej': {'name': 'Economic Journal', 'abbr': 'EJ', 'category': 'General', 'issn': '0013-0133'},
    'qe': {'name': 'Quantitative Economics', 'abbr': 'QE', 'category': 'General', 'issn': '1759-7323'},
    'ier': {'name': 'International Economic Review', 'abbr': 'IER', 'category': 'General', 'issn': '0020-6598'},

    # ========== Survey/Review Journals ==========
    'jep': {'name': 'Journal of Economic Perspectives', 'abbr': 'JEP', 'category': 'Survey', 'issn': '0895-3309'},
    'jel': {'name': 'Journal of Economic Literature', 'abbr': 'JEL', 'category': 'Survey', 'issn': '0022-0515'},
    'are': {'name': 'Annual Review of Economics', 'abbr': 'ARE', 'category': 'Survey', 'issn': '1941-1383'},

    # ========== Field: Labor Economics ==========
    'jole': {'name': 'Journal of Labor Economics', 'abbr': 'JOLE', 'category': 'Labor', 'issn': '0734-306X'},
    'jhr': {'name': 'Journal of Human Resources', 'abbr': 'JHR', 'category': 'Labor', 'issn': '0022-166X'},
    'le': {'name': 'Labour Economics', 'abbr': 'LE', 'category': 'Labor', 'issn': '0927-5371'},

    # ========== Field: Development Economics ==========
    'jde': {'name': 'Journal of Development Economics', 'abbr': 'JDE', 'category': 'Development', 'issn': '0304-3878'},
    'wber': {'name': 'World Bank Economic Review', 'abbr': 'WBER', 'category': 'Development', 'issn': '0258-6770'},
    'edcc': {'name': 'Economic Development and Cultural Change', 'abbr': 'EDCC', 'category': 'Development', 'issn': '0013-0079'},

    # ========== Field: Public Economics ==========
    'jpube': {'name': 'Journal of Public Economics', 'abbr': 'JPubE', 'category': 'Public', 'issn': '0047-2727'},
    'jpope': {'name': 'Journal of Population Economics', 'abbr': 'JPopE', 'category': 'Public', 'issn': '0933-1433'},

    # ========== Field: Health Economics ==========
    'jhe': {'name': 'Journal of Health Economics', 'abbr': 'JHE', 'category': 'Health', 'issn': '0167-6296'},
    'jhc': {'name': 'Journal of Human Capital', 'abbr': 'JHC', 'category': 'Health', 'issn': '1932-8575'},

    # ========== Field: Urban/Regional ==========
    'jue': {'name': 'Journal of Urban Economics', 'abbr': 'JUE', 'category': 'Urban', 'issn': '0094-1190'},
    'rsue': {'name': 'Regional Science and Urban Economics', 'abbr': 'RSUE', 'category': 'Urban', 'issn': '0166-0462'},

    # ========== Field: Environmental ==========
    'jeem': {'name': 'Journal of Environmental Economics and Management', 'abbr': 'JEEM', 'category': 'Environment', 'issn': '0095-0696'},
    'jaere': {'name': 'Journal of the Association of Environmental and Resource Economists', 'abbr': 'JAERE', 'category': 'Environment', 'issn': '2333-5955'},

    # ========== Field: Theory/Micro ==========
    'jet': {'name': 'Journal of Economic Theory', 'abbr': 'JET', 'category': 'Theory', 'issn': '0022-0531'},
    'geb': {'name': 'Games and Economic Behavior', 'abbr': 'GEB', 'category': 'Theory', 'issn': '0899-8256'},
    'ectt': {'name': 'Economic Theory', 'abbr': 'ET', 'category': 'Theory', 'issn': '0938-2259'},

    # ========== Field: Monetary/Macro ==========
    'jme': {'name': 'Journal of Monetary Economics', 'abbr': 'JME', 'category': 'Macro', 'issn': '0304-3932'},
    'jmcb': {'name': 'Journal of Money, Credit and Banking', 'abbr': 'JMCB', 'category': 'Macro', 'issn': '0022-2879'},
    'jedc': {'name': 'Journal of Economic Dynamics and Control', 'abbr': 'JEDC', 'category': 'Macro', 'issn': '0165-1889'},
    'imfer': {'name': 'IMF Economic Review', 'abbr': 'IMFER', 'category': 'Macro', 'issn': '2041-4161'},

    # ========== Field: Finance ==========
    'jf': {'name': 'Journal of Finance', 'abbr': 'JF', 'category': 'Finance', 'issn': '0022-1082'},
    'jfe': {'name': 'Journal of Financial Economics', 'abbr': 'JFE', 'category': 'Finance', 'issn': '0304-405X'},
    'rfs': {'name': 'Review of Financial Studies', 'abbr': 'RFS', 'category': 'Finance', 'issn': '0893-9454'},
    'jbf': {'name': 'Journal of Banking & Finance', 'abbr': 'JBF', 'category': 'Finance', 'issn': '0378-4266'},

    # ========== Field: International ==========
    'jie': {'name': 'Journal of International Economics', 'abbr': 'JIE', 'category': 'International', 'issn': '0022-1996'},

    # ========== Field: Econometrics ==========
    'joe': {'name': 'Journal of Econometrics', 'abbr': 'JoE', 'category': 'Econometrics', 'issn': '0304-4076'},
    'jae': {'name': 'Journal of Applied Econometrics', 'abbr': 'JAE', 'category': 'Econometrics', 'issn': '0883-7252'},
    'jbes': {'name': 'Journal of Business & Economic Statistics', 'abbr': 'JBES', 'category': 'Econometrics', 'issn': '0735-0015'},

    # ========== Field: Behavioral ==========
    'jebo': {'name': 'Journal of Economic Behavior & Organization', 'abbr': 'JEBO', 'category': 'Behavioral', 'issn': '0167-2681'},
    'ee': {'name': 'Experimental Economics', 'abbr': 'EE', 'category': 'Behavioral', 'issn': '1386-4157'},

    # ========== Field: Industrial Organization ==========
    'ijio': {'name': 'International Journal of Industrial Organization', 'abbr': 'IJIO', 'category': 'IO', 'issn': '0167-7187'},
    'jleo': {'name': 'Journal of Law, Economics, and Organization', 'abbr': 'JLEO', 'category': 'IO', 'issn': '8756-6222'},

    # ========== Political Science Top 3 ==========
    'ajps': {'name': 'American Journal of Political Science', 'abbr': 'AJPS', 'category': 'PoliSci', 'issn': '0092-5853'},
    'apsr': {'name': 'American Political Science Review', 'abbr': 'APSR', 'category': 'PoliSci', 'issn': '0003-0554'},
    'jop': {'name': 'Journal of Politics', 'abbr': 'JOP', 'category': 'PoliSci', 'issn': '0022-3816'},

    # ========== Statistics Top ==========
    'jasa': {'name': 'Journal of the American Statistical Association', 'abbr': 'JASA', 'category': 'Stats', 'issn': '0162-1459'},
    'jrssb': {'name': 'Journal of the Royal Statistical Society: Series B', 'abbr': 'JRSS-B', 'category': 'Stats', 'issn': '1369-7412'},
    'aos': {'name': 'Annals of Statistics', 'abbr': 'AoS', 'category': 'Stats', 'issn': '0090-5364'},
}

# Category shortcuts for quick selection
CATEGORY_SHORTCUTS = {
    'top5': ['aer', 'jpe', 'qje', 'ecta', 'restud'],
    'general': ['aer', 'jpe', 'qje', 'ecta', 'restud', 'aeri', 'restat', 'jeea', 'eer', 'ej', 'qe'],
    'survey': ['jep', 'jel', 'are'],
    'finance_top': ['jf', 'jfe', 'rfs'],
    'polisci': ['ajps', 'apsr', 'jop'],
    'stats': ['jasa', 'jrssb', 'aos'],
}

HEADERS = {
    'User-Agent': 'PaperSearch/1.0 (mailto:research@example.com)',
    'Accept': 'application/json',
}


def search_openalex(query: str, limit: int = 50, journals: List[str] = None, year_from: int = None, year_to: int = None) -> List[Dict]:
    """
    Search papers using OpenAlex API.
    """
    base_url = 'https://api.openalex.org/works'

    # Build filters
    filters = []

    if journals:
        issns = [JOURNALS[j]['issn'] for j in journals if j in JOURNALS and JOURNALS[j].get('issn')]
        if issns:
            filters.append(f"primary_location.source.issn:{'|'.join(issns)}")

    if year_from and year_to:
        filters.append(f"publication_year:{year_from}-{year_to}")
    elif year_from:
        filters.append(f"publication_year:>{year_from - 1}")
    elif year_to:
        filters.append(f"publication_year:<{year_to + 1}")

    params = {
        'search': query,
        'per_page': min(limit, 100),
        'sort': 'relevance_score:desc',
        'select': 'id,title,authorships,publication_year,primary_location,abstract_inverted_index,cited_by_count,doi,open_access',
    }

    if filters:
        params['filter'] = ','.join(filters)

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
            if len(work.get('authorships', [])) > 5:
                authors_str += ' et al.'

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
        print(f"OpenAlex search error: {e}")
        return []


def search_econ_papers(query: str, limit: int = 50, year_from: int = None, year_to: int = None) -> List[Dict]:
    """Search economics papers (Top 5 + General journals)."""
    journals = CATEGORY_SHORTCUTS['general']
    return search_openalex(query, limit, journals, year_from, year_to)


def search_semantic_scholar(query: str, limit: int = 20) -> List[Dict]:
    """Search papers using Semantic Scholar API."""
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
    """Search papers using CrossRef API."""
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
            title = item.get('title', [''])[0] if item.get('title') else ''

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

            year = ''
            pub_date = item.get('published-print', item.get('published-online', {}))
            date_parts = pub_date.get('date-parts', [[]])
            if date_parts and date_parts[0]:
                year = str(date_parts[0][0])

            venue = item.get('container-title', [''])[0] if item.get('container-title') else ''

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
    """Search papers on arXiv."""
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
    """Search for an author and their publications."""
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

            author_info = {
                'name': author.get('display_name', ''),
                'paper_count': author.get('works_count', 0),
                'citation_count': author.get('cited_by_count', 0),
                'h_index': author.get('summary_stats', {}).get('h_index', 0),
            }

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


def search_by_journal(query: str, journal_keys: List[str], limit: int = 50, year_from: int = None, year_to: int = None) -> List[Dict]:
    """Search papers filtered by specific journals."""
    return search_openalex(query, limit, journal_keys, year_from, year_to)


def search_all(query: str, limit: int = 50, source: str = 'all') -> List[Dict]:
    """
    Search across multiple sources and combine results.
    source can be: 'all', 'openalex', 'semantic_scholar', 'crossref', 'arxiv', 'econ'
    """
    results = []

    if source == 'all' or source == 'openalex':
        oa_results = search_openalex(query, limit=limit)
        results.extend(oa_results)

    if source == 'all' or source == 'semantic_scholar':
        time.sleep(0.3)
        ss_results = search_semantic_scholar(query, limit=min(limit, 20))
        results.extend(ss_results)

    if source == 'crossref':
        cr_results = search_crossref(query, limit=limit)
        results.extend(cr_results)

    if source == 'arxiv':
        ar_results = search_arxiv(query, limit=limit)
        results.extend(ar_results)

    if source == 'econ':
        return search_econ_papers(query, limit=limit)

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

    # Sort categories in a preferred order
    order = ['Top 5', 'AEJ', 'General', 'Survey', 'Finance', 'Labor', 'Development',
             'Public', 'Health', 'Urban', 'Environment', 'Theory', 'Macro', 'International',
             'Econometrics', 'Behavioral', 'IO', 'PoliSci', 'Stats']

    sorted_categories = {}
    for cat in order:
        if cat in categories:
            sorted_categories[cat] = categories[cat]

    # Add any remaining categories
    for cat in categories:
        if cat not in sorted_categories:
            sorted_categories[cat] = categories[cat]

    return sorted_categories


def get_category_shortcuts() -> Dict[str, List[str]]:
    """Get category shortcuts for quick selection."""
    return CATEGORY_SHORTCUTS
