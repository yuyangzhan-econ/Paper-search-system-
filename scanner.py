"""
Paper scanner module for scanning directories and extracting metadata.
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from pypdf import PdfReader
import database as db


# Common paper file extensions
PAPER_EXTENSIONS = {'.pdf', '.PDF'}


def extract_title_from_filename(filename: str) -> str:
    """Extract a clean title from filename."""
    # Remove extension
    name = os.path.splitext(filename)[0]

    # Remove common prefixes/suffixes
    patterns = [
        r'^\d+[-_\s]*',  # Leading numbers
        r'[-_]\d{4}$',   # Year suffix
        r'\s*\(\d+\)$',  # Copy numbers
        r'^\[.*?\]\s*',  # Bracketed prefixes
    ]

    for pattern in patterns:
        name = re.sub(pattern, '', name)

    # Replace underscores and multiple spaces
    name = re.sub(r'[_]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()


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
        if part and part != '.' and part != '..':
            tags.append(part)

    return tags


def extract_pdf_metadata(file_path: str) -> Dict:
    """Extract metadata from PDF file."""
    metadata = {
        'title': '',
        'authors': '',
        'year': '',
        'abstract': '',
    }

    try:
        reader = PdfReader(file_path)

        if reader.metadata:
            # Title
            if reader.metadata.title:
                metadata['title'] = str(reader.metadata.title).strip()

            # Author
            if reader.metadata.author:
                metadata['authors'] = str(reader.metadata.author).strip()

            # Creation date for year
            if reader.metadata.creation_date:
                try:
                    year = str(reader.metadata.creation_date.year)
                    if 1900 <= int(year) <= 2100:
                        metadata['year'] = year
                except Exception:
                    pass

        # Try to extract abstract from first page
        if len(reader.pages) > 0:
            try:
                first_page_text = reader.pages[0].extract_text()
                if first_page_text:
                    # Look for abstract section
                    abstract_match = re.search(
                        r'(?:abstract|摘要)[:\s]*(.{100,1000}?)(?=\n\n|introduction|1\.|keywords|关键词)',
                        first_page_text,
                        re.IGNORECASE | re.DOTALL
                    )
                    if abstract_match:
                        metadata['abstract'] = abstract_match.group(1).strip()[:500]
            except Exception:
                pass

    except Exception as e:
        print(f"Error reading PDF metadata: {file_path}, {e}")

    return metadata


def scan_directory(base_path: str, progress_callback=None) -> Tuple[int, int]:
    """
    Scan a directory for papers and add them to the database.
    Returns (added_count, updated_count).
    """
    if not os.path.exists(base_path):
        raise ValueError(f"Directory not found: {base_path}")

    added_count = 0
    updated_count = 0
    total_files = 0

    # First count total files
    for root, _, files in os.walk(base_path):
        for file in files:
            if os.path.splitext(file)[1] in PAPER_EXTENSIONS:
                total_files += 1

    processed = 0

    # Process files
    for root, _, files in os.walk(base_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext not in PAPER_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)
            processed += 1

            if progress_callback:
                progress_callback(processed, total_files, file)

            # Check if already in database
            existing = db.get_paper_by_path(file_path)

            # Extract metadata
            pdf_meta = extract_pdf_metadata(file_path)

            # Use PDF title if available, otherwise filename
            title = pdf_meta['title'] or extract_title_from_filename(file)

            # Extract tags from folder structure
            tags = extract_tags_from_path(root, base_path)

            # Build paper data
            paper_data = {
                'title': title,
                'file_path': file_path,
                'file_name': file,
                'folder_path': root,
                'authors': pdf_meta['authors'],
                'tags': ', '.join(tags),
                'keywords': '',
                'year': pdf_meta['year'],
                'abstract': pdf_meta['abstract'],
            }

            # Add or update in database
            if existing:
                # Only update if metadata is richer
                if not existing['authors'] and pdf_meta['authors']:
                    db.update_paper(existing['id'], authors=pdf_meta['authors'])
                if not existing['abstract'] and pdf_meta['abstract']:
                    db.update_paper(existing['id'], abstract=pdf_meta['abstract'])
                updated_count += 1
            else:
                db.add_paper(**paper_data)
                added_count += 1

    return added_count, updated_count


def rescan_paper(paper_id: int) -> bool:
    """Rescan a single paper to update its metadata."""
    paper = db.get_paper(paper_id)
    if not paper:
        return False

    file_path = paper['file_path']
    if not os.path.exists(file_path):
        return False

    # Extract fresh metadata
    pdf_meta = extract_pdf_metadata(file_path)

    # Update in database
    updates = {}
    if pdf_meta['title'] and not paper['title']:
        updates['title'] = pdf_meta['title']
    if pdf_meta['authors']:
        updates['authors'] = pdf_meta['authors']
    if pdf_meta['abstract']:
        updates['abstract'] = pdf_meta['abstract']
    if pdf_meta['year']:
        updates['year'] = pdf_meta['year']

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
