"""
Paper scanner module for scanning directories and extracting metadata.
Improved with garbage text detection and filename fallback for reliable display.
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

# Garbage/invalid text patterns that indicate PDF extraction failed
GARBAGE_PATTERNS = [
    r'[\u0080-\u009f]',  # Control characters
    r'[\u0530-\u058f]',  # Armenian (unlikely in paper titles)
    r'[\u0d00-\u0d7f]',  # Malayalam
    r'[\u0e80-\u0eff]',  # Lao
    r'[\u1000-\u109f]',  # Myanmar
    r'[\u1100-\u11ff]',  # Hangul Jamo (unlikely standalone)
    r'[թԥൊ໾đၛᄝ]',  # Specific garbage chars seen in bad extractions
]

# Chinese journal/volume patterns to filter out
CHINESE_JOURNAL_PATTERNS = [
    r'第\s*\d+\s*卷',
    r'第\s*\d+\s*期',
    r'\d{4}\s*年\s*\d+\s*月',
    r'Vol\.\s*\d+',
    r'No\.\s*\d+',
    r'期刊',
    r'学报',
    r'经济研究',
    r'经济学',
    r'管理世界',
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


def is_garbage_text(text: str) -> bool:
    """
    Check if text contains garbage/garbled characters indicating PDF extraction failed.
    This happens often with Chinese PDFs that use embedded fonts.
    """
    if not text or len(text) < 5:
        return True

    # Count garbage characters
    garbage_count = 0
    for pattern in GARBAGE_PATTERNS:
        garbage_count += len(re.findall(pattern, text))

    # If more than 10% garbage, consider it bad
    if garbage_count > len(text) * 0.1:
        return True

    # Count printable vs non-printable
    printable = sum(1 for c in text if c.isprintable() or c.isspace())
    if printable < len(text) * 0.7:
        return True

    # Count valid characters (Chinese + ASCII letters/numbers)
    valid_chars = sum(1 for c in text if (
        '\u4e00' <= c <= '\u9fff' or  # Chinese
        c.isascii() and (c.isalnum() or c.isspace() or c in '.,;:!?-()[]{}"\'/') or
        c in '，。；：！？、（）【】""''《》'
    ))

    if valid_chars < len(text) * 0.5:
        return True

    return False


def is_journal_header(text: str) -> bool:
    """Check if text looks like a journal/volume header, not a title."""
    text_lower = text.lower()

    # Chinese journal patterns
    for pattern in CHINESE_JOURNAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Very short text with mostly numbers
    if len(text) < 20:
        digit_count = sum(1 for c in text if c.isdigit())
        if digit_count > len(text) * 0.3:
            return True

    return False


def clean_title_from_filename(filename: str) -> str:
    """Extract a clean title from filename."""
    name = os.path.splitext(filename)[0]

    # Remove common prefixes like "[Journal Name]", "(2020)", etc.
    name = re.sub(r'^\[.*?\]\s*', '', name)
    name = re.sub(r'^\(.*?\)\s*', '', name)
    name = re.sub(r'^\d+[-_.\s]+', '', name)

    # Remove year patterns
    name = re.sub(r'\s*[\(_]\s*(19|20)\d{2}\s*[\)_]?\s*', ' ', name)
    name = re.sub(r'\s*(19|20)\d{2}\s*$', '', name)

    # Replace underscores with spaces
    name = re.sub(r'[_]+', ' ', name)

    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # If name looks like "Author - Title", extract the title part
    if ' - ' in name:
        parts = name.split(' - ', 1)
        if len(parts) == 2 and len(parts[1]) > 10:
            name = parts[1]

    return name


def extract_authors_from_filename(filename: str) -> str:
    """Try to extract author names from filename patterns."""
    name = os.path.splitext(filename)[0]

    # Common pattern: "Author1, Author2 - Title"
    if ' - ' in name:
        author_part = name.split(' - ')[0].strip()
        # Check if it looks like authors
        if re.match(r'^[A-Z][a-z]+', author_part):
            return author_part

    # Pattern: "Author (Year) Title"
    match = re.match(r'^([A-Z][a-z]+(?:\s+(?:and|&|,)\s+[A-Z][a-z]+)*)\s*[\(_]', name)
    if match:
        return match.group(1)

    # Pattern: "Author et al"
    match = re.match(r'^([A-Z][a-z]+)\s+et\s+al', name)
    if match:
        return match.group(1) + ' et al.'

    return ''


def extract_metadata_from_text(text: str) -> Dict:
    """
    Extract metadata from first page text with simple, reliable heuristics.
    Focuses on getting year and abstract only - title/authors come from filename.
    The full first page text is stored in 'details' for searching.
    """
    result = {'title': '', 'authors': '', 'abstract': '', 'year': '', 'details': ''}

    if not text:
        return result

    # Store first page text for searching (even if garbage - user might search for it)
    clean_text = re.sub(r'\s+', ' ', text).strip()
    result['details'] = clean_text[:2000]  # Limit to 2000 chars

    # Check if text is garbage - if so, don't try to extract title
    if is_garbage_text(text):
        # Still try to extract year from the text
        year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text)
        if year_match:
            year = year_match.group(1)
            if 1950 <= int(year) <= 2030:
                result['year'] = year
        return result

    # Split into lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line and len(line) > 3]

    if not lines:
        return result

    # Try to find a good title - but be very conservative
    for line in lines[:15]:  # Check first 15 lines
        # Skip journal headers
        if is_journal_header(line):
            continue

        # Skip very short or very long lines
        if len(line) < 15 or len(line) > 150:
            continue

        # Skip lines that look like metadata
        line_lower = line.lower()
        skip_keywords = [
            'abstract', '摘要', 'keywords', '关键词', 'jel',
            'doi:', 'http', 'www.', '@', 'copyright',
            'university', 'institute', 'college', 'department',
            '大学', '学院', '研究所', '研究院', '中心'
        ]
        if any(keyword in line_lower for keyword in skip_keywords):
            continue

        # Skip lines with too many numbers
        digit_ratio = sum(1 for c in line if c.isdigit()) / len(line)
        if digit_ratio > 0.2:
            continue

        # This might be a title
        result['title'] = line
        break

    # Extract abstract
    abstract_match = re.search(
        r'(?:abstract|摘要)[:\s]*\n*(.{50,1000}?)(?=\n\s*\n|introduction|1\.\s|keywords|关键词|jel)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        result['abstract'] = abstract[:500]

    # Extract year
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


def extract_pdf_metadata_safe(file_path: str, file_name: str) -> Dict:
    """
    Extract metadata from PDF using multiple strategies.
    PRIORITY: Filename > PDF text (to avoid garbage display)

    Strategy:
    1. Filename analysis (most reliable for display)
    2. First page text for abstract, year, and searchable details
    3. PDF metadata as last resort
    """
    result = {
        'title': '',
        'authors': '',
        'year': '',
        'abstract': '',
        'details': '',  # First page text for searching
    }

    # Strategy 1: Extract from filename FIRST (most reliable for display)
    filename_info = extract_info_from_filename(file_name)
    result['title'] = filename_info.get('title', '')
    result['authors'] = filename_info.get('authors', '')
    result['year'] = filename_info.get('year', '')

    if not PDF_AVAILABLE:
        return result

    try:
        # Strategy 2: Extract from first page text
        first_page_text = extract_pdf_first_page_text(file_path)
        if first_page_text:
            text_info = extract_metadata_from_text(first_page_text)

            # Store first page text for searching
            result['details'] = text_info.get('details', '')

            # Only use PDF text for title if filename didn't give us one AND text is not garbage
            if not result['title'] and text_info.get('title'):
                result['title'] = text_info['title']

            # Get abstract from PDF text
            if text_info.get('abstract'):
                result['abstract'] = text_info['abstract']

            # Get year from PDF text if not from filename
            if not result['year'] and text_info.get('year'):
                result['year'] = text_info['year']

        # Strategy 3: Fill in missing info from PDF metadata
        try:
            reader = PdfReader(file_path, strict=False)
            if reader.metadata:
                # Only use PDF metadata if we still don't have data
                if not result['title'] and reader.metadata.title:
                    title = str(reader.metadata.title).strip()
                    # Only use if it looks valid
                    if len(title) > 5 and title.lower() != 'untitled' and not is_garbage_text(title):
                        result['title'] = title

                if not result['authors'] and reader.metadata.author:
                    author = str(reader.metadata.author).strip()
                    if len(author) > 2 and 'latex' not in author.lower() and not is_garbage_text(author):
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

            # Extract metadata from PDF (now prioritizes filename for display)
            pdf_meta = extract_pdf_metadata_safe(file_path, file)

            # Get title - use filename-based extraction if PDF gave garbage or nothing
            title = pdf_meta['title'] or clean_title_from_filename(file) or file

            # Get authors from filename (more reliable than PDF extraction)
            authors = pdf_meta['authors'] or extract_authors_from_filename(file)

            # Year from either source
            year = pdf_meta['year']

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
                'details': pdf_meta.get('details', ''),  # First page text for searching
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
                # Always update details for searching
                if pdf_meta.get('details'):
                    updates['details'] = pdf_meta['details']

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
    file_name = paper['file_name']
    if not os.path.exists(file_path):
        return False

    # Use the new extraction that prioritizes filename
    pdf_meta = extract_pdf_metadata_safe(file_path, file_name)

    updates = {}
    if pdf_meta['title']:
        updates['title'] = pdf_meta['title']
    if pdf_meta['authors']:
        updates['authors'] = pdf_meta['authors']
    if pdf_meta['abstract']:
        updates['abstract'] = pdf_meta['abstract']
    if pdf_meta['year']:
        updates['year'] = pdf_meta['year']
    if pdf_meta.get('details'):
        updates['details'] = pdf_meta['details']

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
