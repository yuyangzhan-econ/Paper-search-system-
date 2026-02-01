"""
Paper scanner module for scanning directories and extracting metadata.
Improved with advanced title/author extraction from PDF first page.
"""

import os
import re
import warnings
from typing import List, Dict, Optional, Tuple

# Suppress PDF warnings
warnings.filterwarnings('ignore')

import database as db

# Try to import pypdf
try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    PdfReadError = Exception


# Common paper file extensions
PAPER_EXTENSIONS = {'.pdf', '.PDF'}

# Folders/files to skip
SKIP_PATTERNS = [
    '__MACOSX',
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    '数据',
    '工作',
    '工作研究',
    'data',
    'code',
    'codes',
    'replication',
    'Replication',
    'appendix',
    'supplement',
    'figures',
    'tables',
    'results',
]

# Common institutions/affiliations keywords
AFFILIATION_KEYWORDS = [
    'university', 'institute', 'college', 'school', 'department', 'center', 'centre',
    'research', 'economics', 'business', 'faculty', 'nber', 'cepr', 'iza',
    '大学', '学院', '研究所', '研究院', '中心', '系'
]

# Common non-author patterns to filter out
NON_AUTHOR_PATTERNS = [
    r'^abstract$', r'^introduction$', r'^keywords?$', r'^jel\s*codes?$',
    r'^\d+$', r'^volume\s+\d+', r'^issue\s+\d+', r'^pages?\s+\d+',
    r'^doi:', r'^http', r'^www\.', r'@', r'\.edu$', r'\.org$',
    r'^copyright', r'^all\s+rights', r'^\*', r'^†', r'^‡',
]

# Journal name patterns to detect first-page publisher info
JOURNAL_PATTERNS = [
    r'american\s+economic\s+review', r'quarterly\s+journal\s+of\s+economics',
    r'econometrica', r'journal\s+of\s+political\s+economy', r'review\s+of\s+economic\s+studies',
    r'journal\s+of\s+finance', r'journal\s+of\s+financial\s+economics',
    r'jstor', r'wiley', r'elsevier', r'springer', r'oxford\s+university\s+press',
    r'cambridge\s+university\s+press', r'nber\s+working\s+paper',
]


def should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped."""
    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)

    if file_name.startswith('.') or file_name.startswith('._'):
        return True

    for pattern in SKIP_PATTERNS:
        if pattern in dir_path or pattern in file_name:
            return True

    return False


def is_likely_author_name(text: str) -> bool:
    """Check if text looks like an author name."""
    text = text.strip()

    if not text or len(text) < 3 or len(text) > 100:
        return False

    # Filter out obvious non-names
    for pattern in NON_AUTHOR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # Should contain mostly letters
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < len(text) * 0.5:
        return False

    # Check for name-like patterns
    # Western names: "John Smith", "J. Smith", "John D. Smith", "John Smith Jr."
    # Chinese names: "张三", "Li Ming", "Lian Zhou"

    # Has capitalized words (Western names)
    if re.search(r'[A-Z][a-z]+', text):
        return True

    # Has Chinese characters
    if re.search(r'[\u4e00-\u9fff]', text):
        return True

    return False


def extract_title_and_authors_from_text(text: str) -> Dict:
    """
    Extract title and authors from first page text using heuristics.

    Strategy:
    1. Split text into lines
    2. First substantial lines (before abstract/affiliations) are likely title
    3. Lines with name patterns after title are authors
    4. Stop when we hit abstract, affiliations, or main content
    """
    result = {'title': '', 'authors': '', 'abstract': '', 'year': ''}

    if not text:
        return result

    # Clean and split into lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]  # Remove empty lines

    if not lines:
        return result

    # Skip publisher/journal header lines
    start_idx = 0
    for i, line in enumerate(lines[:10]):
        line_lower = line.lower()
        # Check if this is a publisher/journal header line
        is_header = False
        for pattern in JOURNAL_PATTERNS:
            if re.search(pattern, line_lower):
                is_header = True
                break
        # Also skip lines with volume/issue info
        if re.search(r'vol\.\s*\d+|issue\s*\d+|pp?\.\s*\d+|doi:', line_lower):
            is_header = True
        # Skip very short lines at the start
        if len(line) < 5:
            is_header = True

        if is_header:
            start_idx = i + 1
        else:
            break

    lines = lines[start_idx:]
    if not lines:
        return result

    # Phase 1: Find title
    # Title is usually the first substantial text, may span multiple lines
    title_lines = []
    title_end_idx = 0

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Stop conditions for title
        if any([
            line_lower.startswith('abstract'),
            line_lower.startswith('摘要'),
            'jel classification' in line_lower,
            'jel code' in line_lower,
            'keywords' in line_lower,
            '关键词' in line_lower,
            re.search(r'^\d+\.\s+introduction', line_lower),
            re.search(r'^1\s+introduction', line_lower),
        ]):
            break

        # Check if this line looks like author names
        if i > 0 and is_likely_author_name(line):
            # Check if multiple comma-separated names
            potential_names = [n.strip() for n in re.split(r'[,，、;；]', line) if n.strip()]
            if len(potential_names) >= 2 or (len(potential_names) == 1 and is_likely_author_name(potential_names[0])):
                # Likely author line, stop title collection
                if title_lines:
                    title_end_idx = i
                    break

        # Check if line looks like an affiliation
        if any(keyword in line.lower() for keyword in AFFILIATION_KEYWORDS):
            if title_lines:
                title_end_idx = i
                break

        # Add to title if it looks like title text
        if len(line) > 3:
            # Title lines are usually not too long (not a paragraph)
            if len(line) < 300:
                title_lines.append(line)
                title_end_idx = i + 1
            else:
                # Long line - might be abstract or content
                break

        # Don't let title be too long
        if len(title_lines) >= 5:
            break

    # Build title
    if title_lines:
        result['title'] = ' '.join(title_lines)
        # Clean up title
        result['title'] = re.sub(r'\s+', ' ', result['title']).strip()
        # Remove trailing punctuation that doesn't belong
        result['title'] = re.sub(r'[*†‡]+$', '', result['title']).strip()

    # Phase 2: Find authors
    # Authors usually follow title, before abstract/affiliations
    remaining_lines = lines[title_end_idx:]
    author_candidates = []

    for i, line in enumerate(remaining_lines[:15]):  # Check next 15 lines
        line_lower = line.lower()

        # Stop conditions
        if any([
            line_lower.startswith('abstract'),
            line_lower.startswith('摘要'),
            'jel classification' in line_lower,
            'jel code' in line_lower,
            len(line) > 500,  # Too long, probably content
            re.search(r'^\d+\.\s+\w+', line_lower),  # Section number
        ]):
            break

        # Skip affiliation lines (but don't stop)
        if any(keyword in line.lower() for keyword in AFFILIATION_KEYWORDS):
            continue

        # Skip lines with email addresses
        if '@' in line or re.search(r'^\*|^†|^‡', line):
            continue

        # Check if this looks like author names
        # Split by common separators
        potential_names = re.split(r'[,，、;；]|\s+and\s+|\s+&\s+', line)
        potential_names = [n.strip() for n in potential_names if n.strip()]

        # Check each potential name
        valid_names = []
        for name in potential_names:
            # Clean up name
            name = re.sub(r'[*†‡\d]+', '', name).strip()
            name = re.sub(r'\s+', ' ', name)

            if is_likely_author_name(name) and len(name) > 2:
                valid_names.append(name)

        if valid_names:
            author_candidates.extend(valid_names)

    # Deduplicate and join authors
    seen = set()
    unique_authors = []
    for name in author_candidates:
        name_lower = name.lower()
        if name_lower not in seen and len(name) > 2:
            seen.add(name_lower)
            unique_authors.append(name)

    if unique_authors:
        result['authors'] = ', '.join(unique_authors[:10])  # Max 10 authors

    # Phase 3: Find abstract
    abstract_match = re.search(
        r'(?:abstract|摘要)[:\s]*\n*(.{50,1500}?)(?=\n\s*\n|introduction|1\.\s|keywords|关键词|jel)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        result['abstract'] = abstract[:800]

    # Phase 4: Find year
    year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text)
    if year_match:
        year = year_match.group(1)
        if 1950 <= int(year) <= 2030:
            result['year'] = year

    return result


def extract_pdf_first_page_text(file_path: str) -> str:
    """Extract text from the first page of a PDF."""
    if not PDF_AVAILABLE:
        return ''

    try:
        reader = PdfReader(file_path, strict=False)
        if len(reader.pages) > 0:
            text = reader.pages[0].extract_text()
            return text if text else ''
    except Exception:
        pass

    return ''


def extract_pdf_metadata_safe(file_path: str) -> Dict:
    """
    Extract metadata from PDF using multiple strategies:
    1. First page text analysis (most reliable)
    2. PDF metadata (often incomplete/wrong)
    3. Filename analysis (fallback)
    """
    result = {
        'title': '',
        'authors': '',
        'year': '',
        'abstract': '',
    }

    if not PDF_AVAILABLE:
        return result

    try:
        # Strategy 1: Extract from first page text (most reliable)
        first_page_text = extract_pdf_first_page_text(file_path)
        if first_page_text:
            text_info = extract_title_and_authors_from_text(first_page_text)
            result['title'] = text_info.get('title', '')
            result['authors'] = text_info.get('authors', '')
            result['abstract'] = text_info.get('abstract', '')
            result['year'] = text_info.get('year', '')

        # Strategy 2: Fill in missing info from PDF metadata
        try:
            reader = PdfReader(file_path, strict=False)
            if reader.metadata:
                # Only use PDF metadata if we don't have data from text
                if not result['title'] and reader.metadata.title:
                    title = str(reader.metadata.title).strip()
                    if len(title) > 5 and title.lower() != 'untitled':
                        result['title'] = title

                if not result['authors'] and reader.metadata.author:
                    author = str(reader.metadata.author).strip()
                    if len(author) > 2 and 'latex' not in author.lower():
                        result['authors'] = author

                if not result['year'] and reader.metadata.creation_date:
                    try:
                        year = str(reader.metadata.creation_date.year)
                        if 1950 <= int(year) <= 2030:
                            result['year'] = year
                    except Exception:
                        pass
        except Exception:
            pass

    except Exception:
        pass

    return result


def extract_info_from_filename(filename: str) -> Dict:
    """Extract title, authors, and year from filename."""
    info = {'title': '', 'authors': '', 'year': ''}

    name = os.path.splitext(filename)[0]

    # Common patterns
    patterns = [
        r'^([A-Z][a-z]+(?:\s+(?:and|&|,)\s+[A-Z][a-z]+)*)\s*[-–—]\s*(.+)$',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[\(_]\s*(\d{4})\s*[\)_]\s*(.+)$',
        r'^([A-Z][a-z]+)\s+et\s+al\.?\s*[-–—]\s*(.+)$',
    ]

    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                info['authors'] = groups[0].replace('_', ' ').strip()
                info['title'] = groups[-1].replace('_', ' ').strip()
            break

    # Extract year
    year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', name)
    if year_match:
        year = year_match.group(1)
        if 1950 <= int(year) <= 2030:
            info['year'] = year

    # Use filename as title if nothing found
    if not info['title']:
        title = name
        title = re.sub(r'^\d+[-_.\s]*', '', title)
        title = re.sub(r'^\[.*?\]\s*', '', title)
        title = re.sub(r'[_]+', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        if info['year']:
            title = title.replace(info['year'], '').strip()
        info['title'] = title.strip()

    return info


def extract_tags_from_path(folder_path: str, base_path: str) -> List[str]:
    """Extract tags from folder structure."""
    if not folder_path or not base_path:
        return []

    try:
        rel_path = os.path.relpath(folder_path, base_path)
    except ValueError:
        return []

    tags = []
    skip_folders = {'replication', 'data', 'code', 'codes', 'figures', 'tables',
                    'appendix', 'online', 'supplement', 'Replication Package',
                    'results', '__MACOSX', '数据', '工作', '工作研究'}

    for part in rel_path.split(os.sep):
        part = part.strip()
        if part and part != '.' and part != '..' and not part.startswith('.'):
            if part.lower() not in {s.lower() for s in skip_folders}:
                tags.append(part)

    return tags


def scan_directory(base_path: str, progress_callback=None) -> Tuple[int, int, int]:
    """
    Scan a directory for papers and add them to the database.
    Returns (added_count, updated_count, skipped_count).
    """
    if not os.path.exists(base_path):
        raise ValueError(f"Directory not found: {base_path}")

    added_count = 0
    updated_count = 0
    skipped_count = 0

    # Collect all PDF files first
    all_files = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_PATTERNS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext == '.pdf':
                file_path = os.path.join(root, file)
                if not should_skip_file(file_path):
                    all_files.append((root, file, file_path))

    total_files = len(all_files)

    # Process files
    for idx, (root, file, file_path) in enumerate(all_files):
        if progress_callback:
            progress_callback(idx + 1, total_files, file)

        try:
            existing = db.get_paper_by_path(file_path)

            # Extract metadata from PDF
            pdf_meta = extract_pdf_metadata_safe(file_path)

            # Extract info from filename as fallback
            filename_info = extract_info_from_filename(file)

            # Combine - prefer PDF first page extraction
            title = pdf_meta['title'] or filename_info['title'] or file
            authors = pdf_meta['authors'] or filename_info['authors']
            year = pdf_meta['year'] or filename_info['year']

            # Extract tags from folder structure
            tags = extract_tags_from_path(root, base_path)

            paper_data = {
                'title': title,
                'file_path': file_path,
                'file_name': file,
                'folder_path': root,
                'authors': authors,
                'tags': ', '.join(tags),
                'keywords': '',
                'year': year,
                'abstract': pdf_meta['abstract'],
            }

            if existing:
                updates = {}
                if not existing['title'] or existing['title'] == existing['file_name']:
                    updates['title'] = title
                if not existing['authors'] and authors:
                    updates['authors'] = authors
                if not existing['year'] and year:
                    updates['year'] = year
                if not existing['abstract'] and pdf_meta['abstract']:
                    updates['abstract'] = pdf_meta['abstract']
                if not existing['tags'] and tags:
                    updates['tags'] = ', '.join(tags)

                if updates:
                    db.update_paper(existing['id'], **updates)
                updated_count += 1
            else:
                db.add_paper(**paper_data)
                added_count += 1

        except Exception as e:
            print(f"Warning: Could not process {file}: {e}")
            skipped_count += 1
            continue

    return added_count, updated_count, skipped_count


def rescan_paper(paper_id: int) -> bool:
    """Rescan a single paper to update its metadata."""
    paper = db.get_paper(paper_id)
    if not paper:
        return False

    file_path = paper['file_path']
    if not os.path.exists(file_path):
        return False

    pdf_meta = extract_pdf_metadata_safe(file_path)
    filename_info = extract_info_from_filename(paper['file_name'])

    updates = {}
    if pdf_meta['title'] or filename_info['title']:
        updates['title'] = pdf_meta['title'] or filename_info['title']
    if pdf_meta['authors'] or filename_info['authors']:
        updates['authors'] = pdf_meta['authors'] or filename_info['authors']
    if pdf_meta['abstract']:
        updates['abstract'] = pdf_meta['abstract']
    if pdf_meta['year'] or filename_info['year']:
        updates['year'] = pdf_meta['year'] or filename_info['year']

    if updates:
        return db.update_paper(paper_id, **updates)

    return True


def verify_papers() -> List[Dict]:
    """Check for papers in database that no longer exist on disk."""
    missing = []
    all_papers = db.get_all_papers()

    for paper in all_papers:
        if not os.path.exists(paper['file_path']):
            missing.append(paper)

    return missing


def remove_missing_papers() -> int:
    """Remove papers from database that no longer exist on disk."""
    missing = verify_papers()
    for paper in missing:
        db.delete_paper(paper['id'])
    return len(missing)
