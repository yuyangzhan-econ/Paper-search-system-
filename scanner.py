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


def has_too_many_digits(text: str) -> bool:
    """Check if text has too many digits (likely not a valid title/author)."""
    if not text or len(text) < 5:
        return True
    digit_count = sum(1 for c in text if c.isdigit())
    return digit_count > len(text) * 0.15


def is_likely_author_line(line: str) -> bool:
    """Check if a line looks like it contains author names."""
    line = line.strip()
    if not line or len(line) < 3 or len(line) > 300:
        return False

    # Skip lines with too many digits
    if has_too_many_digits(line):
        return False

    # Skip lines that look like affiliations or other metadata
    skip_patterns = [
        r'university|institute|college|department|school|center|centre',
        r'大学|学院|研究所|研究院|中心|系',
        r'abstract|摘要|keywords|关键词|jel|doi:|http|www\.|@',
        r'copyright|rights|reserved|journal|volume|issue',
        r'^\d+\.\s',  # Section numbers
        r'introduction|conclusion|reference',
    ]
    line_lower = line.lower()
    for pattern in skip_patterns:
        if re.search(pattern, line_lower):
            return False

    # Good signs for author line:
    # 1. Contains Chinese names (2-4 characters together)
    chinese_name_pattern = r'[\u4e00-\u9fff]{2,4}'
    # 2. Contains Western names (Capitalized words)
    western_name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z]?[a-z]*'
    # 3. Contains common separators for multiple authors
    has_separators = bool(re.search(r'[,，、;；]|\s+and\s+|\s+&\s+', line))

    has_chinese_names = bool(re.search(chinese_name_pattern, line))
    has_western_names = bool(re.search(western_name_pattern, line))

    # Line is likely authors if it has names
    if has_chinese_names or has_western_names:
        # Extra validation: mostly letters and common punctuation
        letter_count = sum(1 for c in line if c.isalpha() or '\u4e00' <= c <= '\u9fff')
        if letter_count > len(line) * 0.5:
            return True

    return False


def extract_authors_from_text(text: str) -> str:
    """
    Extract author names from first page text.
    Authors usually appear in the first 20 lines, after title, before abstract.
    """
    if not text:
        return ''

    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line and len(line) > 2]

    if not lines:
        return ''

    author_candidates = []
    found_title = False

    for i, line in enumerate(lines[:25]):  # Check first 25 lines
        line_lower = line.lower()

        # Stop at abstract or keywords
        if 'abstract' in line_lower or '摘要' in line_lower or 'keywords' in line_lower:
            break

        # Skip very long lines (likely paragraphs)
        if len(line) > 200:
            continue

        # First substantial line is likely the title
        if not found_title and len(line) > 15:
            found_title = True
            continue

        # Check if this looks like an author line
        if is_likely_author_line(line):
            author_candidates.append(line)
            # Usually authors are in 1-3 consecutive lines
            if len(author_candidates) >= 3:
                break

    if not author_candidates:
        return ''

    # Combine and clean up author lines
    combined = ' '.join(author_candidates)

    # Remove superscripts, footnote markers, etc.
    combined = re.sub(r'[*†‡§¶\d]+', '', combined)
    combined = re.sub(r'\s+', ' ', combined).strip()

    # Don't return if result is too short or has too many digits
    if len(combined) < 3 or has_too_many_digits(combined):
        return ''

    return combined[:200]  # Limit length


def extract_metadata_from_text(text: str) -> Dict:
    """
    Extract metadata from first page text.
    Stores full first page text in 'details' for comprehensive searching.
    Also attempts to extract title and authors from text.
    """
    result = {'title': '', 'authors': '', 'abstract': '', 'year': '', 'details': ''}

    if not text:
        return result

    # ALWAYS store first page text for searching (even if garbage)
    # This ensures search never misses papers
    clean_text = re.sub(r'\s+', ' ', text).strip()
    result['details'] = clean_text[:5000]  # Store up to 5000 chars for better search

    # Try to extract year regardless of text quality
    year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text)
    if year_match:
        year = year_match.group(1)
        if 1950 <= int(year) <= 2030:
            result['year'] = year

    # Check if text is garbage - if so, skip title/author extraction
    if is_garbage_text(text):
        return result

    # Split into lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line and len(line) > 3]

    if not lines:
        return result

    # Extract authors from text
    result['authors'] = extract_authors_from_text(text)

    # Try to find title (usually first substantial line)
    for line in lines[:15]:
        # Skip journal headers
        if is_journal_header(line):
            continue

        # Skip very short or very long lines
        if len(line) < 10 or len(line) > 200:
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
        if has_too_many_digits(line):
            continue

        # Skip if it looks like an author line (we already extracted authors)
        if is_likely_author_line(line) and len(line) < 80:
            continue

        # This might be a title
        result['title'] = line
        break

    # Extract abstract
    abstract_match = re.search(
        r'(?:abstract|摘要)[:\s]*\n*(.{50,1500}?)(?=\n\s*\n|introduction|1\.\s|keywords|关键词|jel)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        result['abstract'] = abstract[:500]

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
    Combines data from filename, PDF text, and PDF metadata.

    Strategy:
    1. Extract from first page text (for details, authors, title, abstract)
    2. Supplement with filename info
    3. PDF metadata as last resort
    """
    result = {
        'title': '',
        'authors': '',
        'year': '',
        'abstract': '',
        'details': '',  # First page text for searching - ALWAYS populate this
    }

    # Get filename info first
    filename_info = extract_info_from_filename(file_name)

    if not PDF_AVAILABLE:
        result['title'] = filename_info.get('title', '') or clean_title_from_filename(file_name)
        result['authors'] = filename_info.get('authors', '')
        result['year'] = filename_info.get('year', '')
        return result

    try:
        # Strategy 1: Extract from first page text (most important for searching)
        first_page_text = extract_pdf_first_page_text(file_path)
        if first_page_text:
            text_info = extract_metadata_from_text(first_page_text)

            # ALWAYS store first page text for searching
            result['details'] = text_info.get('details', '')

            # Get authors from PDF text (often more complete than filename)
            pdf_authors = text_info.get('authors', '')

            # Get title from PDF text
            pdf_title = text_info.get('title', '')

            # Get abstract from PDF text
            result['abstract'] = text_info.get('abstract', '')

            # Get year from PDF text
            pdf_year = text_info.get('year', '')

            # Combine authors: prefer PDF text if valid, otherwise use filename
            if pdf_authors and not has_too_many_digits(pdf_authors):
                result['authors'] = pdf_authors
            elif filename_info.get('authors'):
                result['authors'] = filename_info['authors']

            # For title: prefer filename (more reliable) unless it's just the raw filename
            filename_title = filename_info.get('title', '')
            if filename_title and filename_title != file_name and len(filename_title) > 5:
                result['title'] = filename_title
            elif pdf_title and not has_too_many_digits(pdf_title):
                result['title'] = pdf_title
            else:
                result['title'] = clean_title_from_filename(file_name)

            # Year from either source
            result['year'] = filename_info.get('year', '') or pdf_year

        else:
            # No PDF text extracted, use filename info
            result['title'] = filename_info.get('title', '') or clean_title_from_filename(file_name)
            result['authors'] = filename_info.get('authors', '')
            result['year'] = filename_info.get('year', '')

        # Strategy 2: Fill in missing info from PDF metadata
        try:
            reader = PdfReader(file_path, strict=False)
            if reader.metadata:
                # Only use PDF metadata if we still don't have data
                if not result['title'] and reader.metadata.title:
                    title = str(reader.metadata.title).strip()
                    if len(title) > 5 and title.lower() != 'untitled' and not is_garbage_text(title) and not has_too_many_digits(title):
                        result['title'] = title

                if not result['authors'] and reader.metadata.author:
                    author = str(reader.metadata.author).strip()
                    if len(author) > 2 and 'latex' not in author.lower() and not is_garbage_text(author) and not has_too_many_digits(author):
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

    # Final validation: ensure title/authors don't have too many digits
    if has_too_many_digits(result['title']):
        result['title'] = clean_title_from_filename(file_name)
    if has_too_many_digits(result['authors']):
        result['authors'] = ''

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
