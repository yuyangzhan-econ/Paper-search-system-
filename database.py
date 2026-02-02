"""
Database module for paper management.
Uses SQLite with FTS5 for full-text search.
"""

import sqlite3
import os
import json
from typing import List, Dict, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'papers.db')


def get_db_connection():
    """Create database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Main papers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            folder_path TEXT,
            authors TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            keywords TEXT DEFAULT '',
            year TEXT DEFAULT '',
            abstract TEXT DEFAULT '',
            details TEXT DEFAULT '',
            doi TEXT DEFAULT '',
            journal TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add new columns if they don't exist (for existing databases)
    for col_name in ['details', 'doi', 'journal']:
        try:
            cursor.execute(f'ALTER TABLE papers ADD COLUMN {col_name} TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Full-text search virtual table (includes details for deep searching)
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            title, authors, tags, keywords, abstract, file_name, details,
            content='papers',
            content_rowid='id',
            tokenize='unicode61'
        )
    ''')

    # Drop old triggers first to recreate with details field
    cursor.execute('DROP TRIGGER IF EXISTS papers_ai')
    cursor.execute('DROP TRIGGER IF EXISTS papers_ad')
    cursor.execute('DROP TRIGGER IF EXISTS papers_au')

    # Triggers to keep FTS in sync (including details field)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
            INSERT INTO papers_fts(rowid, title, authors, tags, keywords, abstract, file_name, details)
            VALUES (new.id, new.title, new.authors, new.tags, new.keywords, new.abstract, new.file_name, new.details);
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
            INSERT INTO papers_fts(papers_fts, rowid, title, authors, tags, keywords, abstract, file_name, details)
            VALUES ('delete', old.id, old.title, old.authors, old.tags, old.keywords, old.abstract, old.file_name, old.details);
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
            INSERT INTO papers_fts(papers_fts, rowid, title, authors, tags, keywords, abstract, file_name, details)
            VALUES ('delete', old.id, old.title, old.authors, old.tags, old.keywords, old.abstract, old.file_name, old.details);
            INSERT INTO papers_fts(rowid, title, authors, tags, keywords, abstract, file_name, details)
            VALUES (new.id, new.title, new.authors, new.tags, new.keywords, new.abstract, new.file_name, new.details);
        END
    ''')

    # Author aliases table (for name variations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS author_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL,
            alias TEXT NOT NULL,
            UNIQUE(canonical_name, alias)
        )
    ''')

    # Tag synonyms table (for fuzzy tag matching)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tag_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_tag TEXT NOT NULL,
            synonym TEXT NOT NULL,
            UNIQUE(canonical_tag, synonym)
        )
    ''')

    conn.commit()
    conn.close()


def add_paper(title: str, file_path: str, file_name: str, folder_path: str = '',
              authors: str = '', tags: str = '', keywords: str = '',
              year: str = '', abstract: str = '', details: str = '',
              doi: str = '', journal: str = '') -> int:
    """Add a paper to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO papers (title, file_path, file_name, folder_path, authors, tags, keywords, year, abstract, details, doi, journal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, file_path, file_name, folder_path, authors, tags, keywords, year, abstract, details, doi, journal))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Paper already exists, update it
        cursor.execute('''
            UPDATE papers SET title=?, file_name=?, folder_path=?, authors=?, tags=?,
                             keywords=?, year=?, abstract=?, details=?, doi=?, journal=?, updated_at=CURRENT_TIMESTAMP
            WHERE file_path=?
        ''', (title, file_name, folder_path, authors, tags, keywords, year, abstract, details, doi, journal, file_path))
        conn.commit()
        cursor.execute('SELECT id FROM papers WHERE file_path=?', (file_path,))
        return cursor.fetchone()['id']
    finally:
        conn.close()


def update_paper(paper_id: int, **kwargs) -> bool:
    """Update paper metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()

    allowed_fields = ['title', 'authors', 'tags', 'keywords', 'year', 'abstract', 'details', 'doi', 'journal']
    updates = [(k, v) for k, v in kwargs.items() if k in allowed_fields]

    if not updates:
        return False

    set_clause = ', '.join([f'{k}=?' for k, _ in updates])
    values = [v for _, v in updates] + [paper_id]

    cursor.execute(f'''
        UPDATE papers SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?
    ''', values)

    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def delete_paper(paper_id: int) -> bool:
    """Delete a paper from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM papers WHERE id=?', (paper_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def get_paper(paper_id: int) -> Optional[Dict]:
    """Get a paper by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM papers WHERE id=?', (paper_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_paper_by_path(file_path: str) -> Optional[Dict]:
    """Get a paper by file path."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM papers WHERE file_path=?', (file_path,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_papers() -> List[Dict]:
    """Get all papers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM papers ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_papers_fts(query: str, limit: int = 100) -> List[Dict]:
    """Full-text search using FTS5 - searches all indexed fields including details."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Escape special FTS characters
    escaped_query = query.replace('"', '""').replace("'", "''")

    try:
        # Try prefix matching first (more flexible)
        cursor.execute('''
            SELECT p.*, bm25(papers_fts) as score
            FROM papers p
            JOIN papers_fts ON p.id = papers_fts.rowid
            WHERE papers_fts MATCH ?
            ORDER BY score
            LIMIT ?
        ''', (f'{escaped_query}*', limit))

        rows = cursor.fetchall()
        if rows:
            conn.close()
            return [dict(row) for row in rows]
    except:
        pass

    # Fallback to phrase search
    try:
        cursor.execute('''
            SELECT p.*, bm25(papers_fts) as score
            FROM papers p
            JOIN papers_fts ON p.id = papers_fts.rowid
            WHERE papers_fts MATCH ?
            ORDER BY score
            LIMIT ?
        ''', (f'"{escaped_query}"', limit))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []


def search_papers_like(query: str, limit: int = 100) -> List[Dict]:
    """Fallback LIKE search for fuzzy matching - includes all searchable fields."""
    conn = get_db_connection()
    cursor = conn.cursor()

    search_pattern = f'%{query}%'

    # Search in ALL fields including details and abstract
    cursor.execute('''
        SELECT * FROM papers
        WHERE title LIKE ? OR authors LIKE ? OR tags LIKE ?
              OR keywords LIKE ? OR file_name LIKE ? OR abstract LIKE ? OR details LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
    ''', (search_pattern, search_pattern, search_pattern, search_pattern,
          search_pattern, search_pattern, search_pattern, limit))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_tags() -> List[str]:
    """Get all unique tags."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT tags FROM papers WHERE tags != ""')
    rows = cursor.fetchall()
    conn.close()

    all_tags = set()
    for row in rows:
        tags = row['tags'].split(',')
        for tag in tags:
            tag = tag.strip()
            if tag:
                all_tags.add(tag)
    return sorted(list(all_tags))


def get_all_authors() -> List[str]:
    """Get all unique authors."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT authors FROM papers WHERE authors != ""')
    rows = cursor.fetchall()
    conn.close()

    all_authors = set()
    for row in rows:
        authors = row['authors'].split(',')
        for author in authors:
            author = author.strip()
            if author:
                all_authors.add(author)
    return sorted(list(all_authors))


def add_author_alias(canonical_name: str, alias: str):
    """Add an author name alias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO author_aliases (canonical_name, alias)
            VALUES (?, ?)
        ''', (canonical_name, alias))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_author_aliases(name: str) -> List[str]:
    """Get all aliases for an author name."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Search both directions
    cursor.execute('''
        SELECT canonical_name, alias FROM author_aliases
        WHERE canonical_name LIKE ? OR alias LIKE ?
    ''', (f'%{name}%', f'%{name}%'))

    rows = cursor.fetchall()
    conn.close()

    aliases = set()
    for row in rows:
        aliases.add(row['canonical_name'])
        aliases.add(row['alias'])
    return list(aliases)


def add_tag_synonym(canonical_tag: str, synonym: str):
    """Add a tag synonym."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO tag_synonyms (canonical_tag, synonym)
            VALUES (?, ?)
        ''', (canonical_tag, synonym))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_tag_synonyms(tag: str) -> List[str]:
    """Get all synonyms for a tag."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT canonical_tag, synonym FROM tag_synonyms
        WHERE canonical_tag LIKE ? OR synonym LIKE ?
    ''', (f'%{tag}%', f'%{tag}%'))

    rows = cursor.fetchall()
    conn.close()

    synonyms = set()
    for row in rows:
        synonyms.add(row['canonical_tag'])
        synonyms.add(row['synonym'])
    return list(synonyms)


def get_suggestions(query: str, limit: int = 10) -> Dict[str, List[str]]:
    """Get search suggestions (authors, tags, titles)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    pattern = f'%{query}%'

    # Get matching titles
    cursor.execute('''
        SELECT DISTINCT title FROM papers WHERE title LIKE ? LIMIT ?
    ''', (pattern, limit))
    titles = [row['title'] for row in cursor.fetchall()]

    # Get matching authors
    cursor.execute('''
        SELECT DISTINCT authors FROM papers WHERE authors LIKE ? LIMIT ?
    ''', (pattern, limit * 2))

    authors = set()
    for row in cursor.fetchall():
        for author in row['authors'].split(','):
            author = author.strip()
            if query.lower() in author.lower():
                authors.add(author)

    # Get matching tags
    cursor.execute('''
        SELECT DISTINCT tags FROM papers WHERE tags LIKE ? LIMIT ?
    ''', (pattern, limit * 2))

    tags = set()
    for row in cursor.fetchall():
        for tag in row['tags'].split(','):
            tag = tag.strip()
            if query.lower() in tag.lower():
                tags.add(tag)

    conn.close()

    return {
        'titles': titles[:limit],
        'authors': sorted(list(authors))[:limit],
        'tags': sorted(list(tags))[:limit]
    }


def get_stats() -> Dict:
    """Get database statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM papers')
    paper_count = cursor.fetchone()['count']

    tags = get_all_tags()
    authors = get_all_authors()

    conn.close()

    return {
        'paper_count': paper_count,
        'tag_count': len(tags),
        'author_count': len(authors)
    }


# Initialize database on module import
init_db()
