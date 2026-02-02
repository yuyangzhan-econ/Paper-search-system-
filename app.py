"""
Paper Search System - Main Flask Application
A beautiful and functional paper management system with local and online search.
"""

import os
import subprocess
import platform
import json
import warnings
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import safe_join, secure_filename

# Suppress warnings
warnings.filterwarnings('ignore')

import database as db
import search
import scanner
import online_search
import doi_service
from version import get_version_info

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['JSON_AS_ASCII'] = False  # Support Chinese characters

# Store the current papers directory
PAPERS_DIR = os.environ.get('PAPERS_DIR', r'E:\研究')

# Scan progress tracking
scan_progress = {
    'running': False,
    'current': 0,
    'total': 0,
    'current_file': '',
    'added': 0,
    'updated': 0,
    'skipped': 0,
    'complete': False,
    'error': None
}

# DOI update progress tracking
doi_progress = {
    'running': False,
    'current': 0,
    'total': 0,
    'current_paper_id': None,
    'current_paper_title': '',
    'updated': 0,
    'failed': 0,
    'complete': False,
    'error': None
}


def open_file_with_default_app(file_path: str) -> bool:
    """Open a file with the system's default application."""
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False


# ============== Web Routes ==============

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/online')
def online():
    """Online search page."""
    return render_template('online.html')


# ============== API Routes ==============

@app.route('/api/search', methods=['GET'])
def api_search():
    """Search papers."""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 100)), 200)

    results = search.search(query, limit=limit)
    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    })


@app.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """Get search suggestions."""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 20)

    if len(query) < 1:
        return jsonify({'suggestions': []})

    suggestions = search.get_suggestions(query, limit=limit)
    return jsonify({'suggestions': suggestions})


@app.route('/api/papers', methods=['GET'])
def api_get_papers():
    """Get all papers."""
    papers = db.get_all_papers()
    return jsonify({
        'success': True,
        'count': len(papers),
        'papers': papers
    })


@app.route('/api/papers', methods=['POST'])
def api_add_paper():
    """Manually add a new paper."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Required fields
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'}), 400

    # Optional file path
    file_path = data.get('file_path', '').strip()
    if file_path and not os.path.exists(file_path):
        return jsonify({'success': False, 'error': f'File not found: {file_path}'}), 400

    # Build paper data
    paper_data = {
        'title': title,
        'file_path': file_path or f'manual_{title[:50]}',
        'file_name': os.path.basename(file_path) if file_path else title[:50],
        'folder_path': os.path.dirname(file_path) if file_path else '',
        'authors': data.get('authors', ''),
        'tags': data.get('tags', ''),
        'keywords': data.get('keywords', ''),
        'year': data.get('year', ''),
        'abstract': data.get('abstract', ''),
    }

    paper_id = db.add_paper(**paper_data)
    paper = db.get_paper(paper_id)

    return jsonify({
        'success': True,
        'paper': paper
    })


@app.route('/api/papers/<int:paper_id>', methods=['GET'])
def api_get_paper(paper_id):
    """Get a specific paper."""
    paper = db.get_paper(paper_id)
    if paper:
        return jsonify({'success': True, 'paper': paper})
    return jsonify({'success': False, 'error': 'Paper not found'}), 404


@app.route('/api/papers/<int:paper_id>', methods=['PUT'])
def api_update_paper(paper_id):
    """Update paper metadata."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    success = db.update_paper(paper_id, **data)
    if success:
        paper = db.get_paper(paper_id)
        return jsonify({'success': True, 'paper': paper})
    return jsonify({'success': False, 'error': 'Update failed'}), 400


@app.route('/api/papers/<int:paper_id>', methods=['DELETE'])
def api_delete_paper(paper_id):
    """Delete a paper from database."""
    success = db.delete_paper(paper_id)
    return jsonify({'success': success})


@app.route('/api/papers/add-file', methods=['POST'])
def api_add_file():
    """
    Add a single PDF file to the database (for drag-drop quick add).
    Accepts either JSON with 'file_path' or multipart form with file upload.
    """
    # Check if it's a file upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

        # Save file to papers directory
        filename = secure_filename(file.filename)
        # Keep original filename if it's safe
        if file.filename and not file.filename.startswith('.'):
            filename = file.filename

        # Create uploads subfolder in papers directory
        upload_dir = os.path.join(PAPERS_DIR, '_uploads')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)

        # Handle duplicate filenames
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{ext}"
            file_path = os.path.join(upload_dir, filename)
            counter += 1

        file.save(file_path)

        # Scan the uploaded file
        paper = scanner.scan_single_file(file_path, PAPERS_DIR)

        if paper:
            return jsonify({
                'success': True,
                'paper': paper,
                'message': 'Paper uploaded and added successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to scan uploaded file'}), 500

    # Fallback to JSON path method
    data = request.get_json()
    if not data or not data.get('file_path'):
        return jsonify({'success': False, 'error': 'file_path or file upload required'}), 400

    file_path = data['file_path'].strip()

    # Validate file exists
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': f'File not found: {file_path}'}), 404

    # Validate it's a PDF
    if not file_path.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

    # Scan the single file
    paper = scanner.scan_single_file(file_path, PAPERS_DIR)

    if paper:
        return jsonify({
            'success': True,
            'paper': paper,
            'message': 'Paper added successfully'
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to scan file'}), 500


@app.route('/api/papers/<int:paper_id>/fetch-doi', methods=['POST'])
def api_fetch_doi_metadata(paper_id):
    """
    Fetch metadata from CrossRef using paper's DOI.
    Updates the paper in database with fetched metadata.
    """
    paper = scanner.fetch_doi_metadata(paper_id)

    if paper:
        return jsonify({
            'success': True,
            'paper': paper,
            'message': 'Metadata fetched successfully'
        })
    else:
        # Check if paper exists
        existing = db.get_paper(paper_id)
        if not existing:
            return jsonify({'success': False, 'error': 'Paper not found'}), 404
        if not existing.get('doi'):
            return jsonify({'success': False, 'error': 'Paper has no DOI'}), 400
        return jsonify({'success': False, 'error': 'Could not fetch metadata from CrossRef'}), 500


def doi_update_worker():
    """Background worker for updating papers with DOI metadata."""
    global doi_progress
    doi_progress['running'] = True
    doi_progress['complete'] = False
    doi_progress['error'] = None
    doi_progress['current'] = 0
    doi_progress['updated'] = 0
    doi_progress['failed'] = 0

    try:
        # Get all papers with DOI but missing metadata
        all_papers = db.get_all_papers()
        papers_with_doi = [p for p in all_papers if p.get('doi') and (
            not p.get('journal') or  # Missing journal
            p.get('title') == p.get('file_name') or  # Title is just filename
            not p.get('authors')  # Missing authors
        )]

        doi_progress['total'] = len(papers_with_doi)

        for i, paper in enumerate(papers_with_doi):
            if not doi_progress['running']:  # Allow cancellation
                break

            doi_progress['current'] = i + 1
            doi_progress['current_paper_id'] = paper['id']
            doi_progress['current_paper_title'] = paper.get('title', '')[:50]

            try:
                result = scanner.fetch_doi_metadata(paper['id'])
                if result:
                    doi_progress['updated'] += 1
                else:
                    doi_progress['failed'] += 1
            except Exception as e:
                doi_progress['failed'] += 1

            # Rate limiting - be nice to CrossRef API
            time.sleep(0.3)

        doi_progress['complete'] = True

    except Exception as e:
        import traceback
        traceback.print_exc()
        doi_progress['error'] = str(e)
    finally:
        doi_progress['running'] = False
        doi_progress['current_paper_id'] = None


@app.route('/api/doi/update-all', methods=['POST'])
def api_doi_update_all():
    """Start background DOI metadata update for all papers."""
    global doi_progress

    if doi_progress['running']:
        return jsonify({
            'success': False,
            'error': 'DOI update already in progress',
            'progress': doi_progress
        }), 409

    # Start background update
    thread = threading.Thread(target=doi_update_worker)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': 'DOI update started'
    })


@app.route('/api/doi/progress', methods=['GET'])
def api_doi_progress():
    """Get current DOI update progress."""
    return jsonify(doi_progress)


@app.route('/api/doi/cancel', methods=['POST'])
def api_doi_cancel():
    """Cancel running DOI update."""
    global doi_progress
    if doi_progress['running']:
        doi_progress['running'] = False
        return jsonify({'success': True, 'message': 'Cancellation requested'})
    return jsonify({'success': False, 'error': 'No update running'})


@app.route('/api/papers/<int:paper_id>/open', methods=['POST'])
def api_open_paper(paper_id):
    """Open paper with default application."""
    paper = db.get_paper(paper_id)
    if not paper:
        return jsonify({'success': False, 'error': 'Paper not found'}), 404

    file_path = paper['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found on disk'}), 404

    success = open_file_with_default_app(file_path)
    return jsonify({'success': success})


@app.route('/api/pdf/<int:paper_id>')
def api_get_pdf(paper_id):
    """Serve PDF file for preview."""
    paper = db.get_paper(paper_id)
    if not paper:
        return jsonify({'success': False, 'error': 'Paper not found'}), 404

    file_path = paper['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404

    return send_file(file_path, mimetype='application/pdf')


def scan_worker(path):
    """Background worker for scanning papers."""
    global scan_progress
    scan_progress['running'] = True
    scan_progress['complete'] = False
    scan_progress['error'] = None
    scan_progress['current'] = 0
    scan_progress['total'] = 0
    scan_progress['added'] = 0
    scan_progress['updated'] = 0
    scan_progress['skipped'] = 0
    scan_progress['current_file'] = '正在计算文件数量...'

    def progress_callback(current, total, filename):
        scan_progress['current'] = current
        scan_progress['total'] = total
        scan_progress['current_file'] = filename

    try:
        added, updated, skipped = scanner.scan_directory(path, progress_callback)
        scan_progress['added'] = added
        scan_progress['updated'] = updated
        scan_progress['skipped'] = skipped
        scan_progress['complete'] = True
    except Exception as e:
        import traceback
        traceback.print_exc()
        scan_progress['error'] = str(e)
    finally:
        scan_progress['running'] = False


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Scan directory for papers (async with progress)."""
    global PAPERS_DIR, scan_progress

    # If scan is already running, return status
    if scan_progress['running']:
        return jsonify({
            'success': False,
            'error': 'Scan already in progress',
            'progress': scan_progress
        }), 409

    data = request.get_json() or {}
    path = data.get('path', PAPERS_DIR)

    if not os.path.exists(path):
        return jsonify({'success': False, 'error': f'Directory not found: {path}'}), 400

    # Update global papers dir
    PAPERS_DIR = path

    # Start background scan
    thread = threading.Thread(target=scan_worker, args=(path,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Scan started',
        'path': path
    })


@app.route('/api/scan/progress', methods=['GET'])
def api_scan_progress():
    """Get current scan progress."""
    return jsonify(scan_progress)


@app.route('/api/scan/stream', methods=['GET'])
def api_scan_stream():
    """Stream scan progress via Server-Sent Events."""
    def generate():
        while True:
            data = json.dumps(scan_progress)
            yield f"data: {data}\n\n"
            if scan_progress['complete'] or scan_progress['error'] or not scan_progress['running']:
                break
            time.sleep(0.3)
        # Final update
        yield f"data: {json.dumps(scan_progress)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/verify', methods=['POST'])
def api_verify():
    """Verify papers exist on disk."""
    missing = scanner.verify_papers()
    return jsonify({
        'success': True,
        'missing_count': len(missing),
        'missing': missing
    })


@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    """Remove papers that no longer exist on disk."""
    removed = scanner.remove_missing_papers()
    return jsonify({
        'success': True,
        'removed': removed
    })


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get database statistics."""
    stats = db.get_stats()
    stats['papers_dir'] = PAPERS_DIR
    return jsonify(stats)


@app.route('/api/tags', methods=['GET'])
def api_get_tags():
    """Get all tags."""
    tags = db.get_all_tags()
    return jsonify({'tags': tags})


@app.route('/api/authors', methods=['GET'])
def api_get_authors():
    """Get all authors."""
    authors = db.get_all_authors()
    return jsonify({'authors': authors})


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current configuration."""
    return jsonify({
        'papers_dir': PAPERS_DIR
    })


@app.route('/api/version', methods=['GET'])
def api_version():
    """Get version information."""
    return jsonify(get_version_info())


@app.route('/api/config', methods=['PUT'])
def api_set_config():
    """Update configuration."""
    global PAPERS_DIR
    data = request.get_json()
    if data and 'papers_dir' in data:
        PAPERS_DIR = data['papers_dir']
        return jsonify({'success': True, 'papers_dir': PAPERS_DIR})
    return jsonify({'success': False, 'error': 'No papers_dir provided'}), 400


# ============== Online Search API Routes ==============

@app.route('/api/online/search', methods=['GET'])
def api_online_search():
    """Search papers online."""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 50)
    source = request.args.get('source', 'all')

    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    try:
        if source == 'semantic_scholar':
            results = online_search.search_semantic_scholar(query, limit)
        elif source == 'crossref':
            results = online_search.search_crossref(query, limit)
        elif source == 'arxiv':
            results = online_search.search_arxiv(query, limit)
        elif source == 'econ':
            results = online_search.search_econ_papers(query, limit)
        else:
            results = online_search.search_all(query, limit)

        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/online/author', methods=['GET'])
def api_online_author():
    """Search for an author."""
    name = request.args.get('name', '').strip()
    limit = min(int(request.args.get('limit', 30)), 50)

    if not name:
        return jsonify({'success': False, 'error': 'Author name required'}), 400

    try:
        result = online_search.search_author(name, limit)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/online/journals', methods=['GET'])
def api_online_journals():
    """Get journal list by category."""
    categories = online_search.get_journal_categories()
    return jsonify({'categories': categories})


@app.route('/api/online/journal-search', methods=['GET'])
def api_online_journal_search():
    """Search within specific journals."""
    query = request.args.get('q', '').strip()
    journals = request.args.get('journals', '').split(',')
    journals = [j.strip() for j in journals if j.strip()]
    limit = min(int(request.args.get('limit', 20)), 50)

    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    try:
        results = online_search.search_by_journal(query, journals if journals else None, limit)
        return jsonify({
            'success': True,
            'query': query,
            'journals': journals,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Static Files ==============

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'success': False, 'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({'success': False, 'error': 'Server error'}), 500


# ============== Main ==============

if __name__ == '__main__':
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                  Paper Search System                       ║
    ║                     论文检索系统                            ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Local:   http://localhost:5000                            ║
    ║  Papers:  {PAPERS_DIR:<45} ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Initialize database
    db.init_db()

    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
