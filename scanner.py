"""
Paper scanner module for scanning directories and extracting metadata.
Improved error handling and metadata extraction.
"""

import os
import re
import warnings
from typing import List, Dict, Optional, Tuple

# Suppress PDF warnings
warnings.filterwarnings('ignore')

import database as db

# Try to import pypdf, but don't fail if it has issues
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

# Common author name patterns in filenames
AUTHOR_PATTERNS = [
    # "Author1 and Author2 - Title" or "Author1, Author2 - Title"
    r'^([A-Z][a-z]+(?:\s+(?:and|&|,)\s+[A-Z][a-z]+)*)\s*[-–—]\s*(.+)$',
    # "Author (Year) Title" or "Author_Year_Title"
    r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[\(_]\s*(\d{4})\s*[\)_]\s*(.+)$',
    # "Author et al. - Title"
    r'^([A-Z][a-z]+)\s+et\s+al\.?\s*[-–—]\s*(.+)$',
    # "LastName_FirstName_Year_Title"
    r'^([A-Z][a-z]+)[_\s]+([A-Z][a-z]+)[_\s]+(\d{4})[_\s]+(.+)$',
]

# Year patterns
YEAR_PATTERNS = [
    r'\b(19\d{2}|20[0-2]\d)\b',  # Years 1900-2029
    r'[\(_](\d{4})[\)_]',  # Year in parentheses or underscores
]


def should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped."""
    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)

    # Skip hidden files
    if file_name.startswith('.'):
        return True

    # Skip macOS resource forks
    if file_name.startswith('._'):
        return True

    # Skip files in skip folders
    for pattern in SKIP_PATTERNS:
        if pattern in dir_path or pattern in file_name:
            return True

    return False


def extract_info_from_filename(filename: str) -> Dict:
    """Extract title, authors, and year from filename using patterns."""
    info = {'title': '', 'authors': '', 'year': ''}

    # Remove extension
    name = os.path.splitext(filename)[0]

    # Try author patterns
    for pattern in AUTHOR_PATTERNS:
        match = re.match(pattern, name)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                info['authors'] = groups[0].replace('_', ' ').strip()
                info['title'] = groups[-1].replace('_', ' ').strip()
            break

    # Extract year
    for pattern in YEAR_PATTERNS:
        match = re.search(pattern, name)
        if match:
            year = match.group(1)
            if 1950 <= int(year) <= 2030:
                info['year'] = year
                break

    # If no structured pattern found, use filename as title
    if not info['title']:
        # Clean up the filename
        title = name
        # Remove common prefixes
        title = re.sub(r'^\d+[-_.\s]*', '', title)  # Leading numbers
        title = re.sub(r'^\[.*?\]\s*', '', title)   # Bracketed prefixes
        # Replace underscores and clean up
        title = re.sub(r'[_]+', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        # Remove year from title if found
        if info['year']:
            title = title.replace(info['year'], '').strip()
            title = re.sub(r'[\(\)_\-]+\s*$', '', title)
        info['title'] = title.strip()

    return info


def extract_tags_from_path(folder_path: str, base_path: str) -> List[str]:
    """Extract tags from folder structure."""
    if not folder_path or not base_path:
        return []

    # Get relative path from base
    try:
        rel_path = os.path.relpath(folder_path, base_path)
    except ValueError:
        return []

    # Split into folder names
    tags = []
    for part in rel_path.split(os.sep):
        part = part.strip()
        # Skip unwanted folders
        if part and part != '.' and part != '..' and not part.startswith('.'):
            # Skip common non-tag folders
            skip_folders = {'replication', 'data', 'code', 'codes', 'figures', 'tables',
                          'appendix', 'online', 'supplement', 'Replication Package',
                          'results', '__MACOSX', '数据', '工作', '工作研究'}
            if part.lower() not in {s.lower() for s in skip_folders}:
                tags.append(part)

    return tags


def extract_pdf_metadata_safe(file_path: str) -> Dict:
    """
    Extract metadata from PDF file with robust error handling.
    Returns empty dict on any error - we'll use filename instead.
    """
    metadata = {
        'title': '',
        'authors': '',
        'year': '',
        'abstract': '',
    }

    if not PDF_AVAILABLE:
        return metadata

    try:
        # Try to read PDF with strict=False to be more lenient
        reader = PdfReader(file_path, strict=False)

        if reader.metadata:
            # Title - only use if it looks like a real title
            if reader.metadata.title:
                title = str(reader.metadata.title).strip()
                # Skip obviously wrong titles
                if len(title) > 5 and not title.startswith('Microsoft') and title.lower() != 'untitled':
                    metadata['title'] = title

            # Author
            if reader.metadata.author:
                author = str(reader.metadata.author).strip()
                # Skip obvious non-author values
                if len(author) > 2 and not any(x in author.lower() for x in ['latex', 'microsoft', 'adobe', 'acrobat']):
                    metadata['authors'] = author

            # Creation date for year
            if reader.metadata.creation_date:
                try:
                    year = str(reader.metadata.creation_date.year)
                    if 1950 <= int(year) <= 2030:
                        metadata['year'] = year
                except Exception:
                    pass

        # Try to extract abstract from first page (only if PDF is readable)
        try:
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()
                if first_page_text and len(first_page_text) > 100:
                    # Look for abstract section
                    abstract_match = re.search(
                        r'(?:abstract|摘要)[:\s]*(.{50,800}?)(?=\n\s*\n|introduction|1\.\s|keywords|关键词|jel)',
                        first_page_text,
                        re.IGNORECASE | re.DOTALL
                    )
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                        # Clean up abstract
                        abstract = re.sub(r'\s+', ' ', abstract)
                        metadata['abstract'] = abstract[:500]
        except Exception:
            pass

    except Exception:
        # Silently ignore all PDF reading errors
        pass

    return metadata


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
        # Skip hidden and system directories
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
            # Check if already in database
            existing = db.get_paper_by_path(file_path)

            # Extract metadata from PDF (safe, won't crash)
            pdf_meta = extract_pdf_metadata_safe(file_path)

            # Extract info from filename
            filename_info = extract_info_from_filename(file)

            # Combine metadata - prefer PDF metadata if available, else filename
            title = pdf_meta['title'] or filename_info['title'] or file
            authors = pdf_meta['authors'] or filename_info['authors']
            year = pdf_meta['year'] or filename_info['year']

            # Extract tags from folder structure
            tags = extract_tags_from_path(root, base_path)

            # Build paper data
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

            # Add or update in database
            if existing:
                # Update with any new metadata
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
            # Log error but continue scanning
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

    # Extract fresh metadata
    pdf_meta = extract_pdf_metadata_safe(file_path)
    filename_info = extract_info_from_filename(paper['file_name'])

    # Update in database
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
