/**
 * Paper Search System - Main JavaScript
 * Handles local paper search, preview, and management
 */

// ============== State ==============
let papers = [];
let currentPaper = null;
let searchTimeout = null;
let suggestionIndex = -1;

// ============== Initialization ==============
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Load stats
    await loadStats();

    // Load all papers
    await loadPapers();

    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');

    // Search input events
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', handleSearchKeydown);
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.length >= 1) {
            showSuggestions();
        }
    });

    // Click outside to close suggestions
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('suggestionsDropdown');
        const searchBox = document.querySelector('.search-box');
        if (!searchBox.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+F or Cmd+F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            searchInput.focus();
        }

        // Escape to clear search
        if (e.key === 'Escape') {
            clearSearch();
        }
    });
}

// ============== Data Loading ==============
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('statPapers').textContent = data.paper_count || 0;
        document.getElementById('statTags').textContent = data.tag_count || 0;
        document.getElementById('statAuthors').textContent = data.author_count || 0;

        // Update settings
        if (data.papers_dir) {
            document.getElementById('settingsPapersDir').value = data.papers_dir;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadPapers() {
    try {
        const response = await fetch('/api/papers');
        const data = await response.json();
        papers = data.papers || [];

        if (papers.length > 0) {
            renderPapers(papers);
        }
    } catch (error) {
        console.error('Failed to load papers:', error);
    }
}

// ============== Search ==============
function handleSearchInput(e) {
    const query = e.target.value.trim();

    // Clear previous timeout
    clearTimeout(searchTimeout);

    // Show suggestions after short delay
    if (query.length >= 1) {
        searchTimeout = setTimeout(() => {
            fetchSuggestions(query);
            performSearch(query);
        }, 200);
    } else {
        hideSuggestions();
        renderPapers(papers);
    }
}

function handleSearchKeydown(e) {
    const dropdown = document.getElementById('suggestionsDropdown');
    const items = dropdown.querySelectorAll('.suggestion-item');

    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            suggestionIndex = Math.min(suggestionIndex + 1, items.length - 1);
            updateSuggestionSelection(items);
            break;

        case 'ArrowUp':
            e.preventDefault();
            suggestionIndex = Math.max(suggestionIndex - 1, -1);
            updateSuggestionSelection(items);
            break;

        case 'Enter':
            e.preventDefault();
            if (suggestionIndex >= 0 && items[suggestionIndex]) {
                selectSuggestion(items[suggestionIndex]);
            } else {
                performSearch(e.target.value);
                hideSuggestions();
            }
            break;

        case 'Escape':
            hideSuggestions();
            break;
    }
}

function updateSuggestionSelection(items) {
    items.forEach((item, index) => {
        item.classList.toggle('selected', index === suggestionIndex);
    });

    if (suggestionIndex >= 0 && items[suggestionIndex]) {
        items[suggestionIndex].scrollIntoView({ block: 'nearest' });
    }
}

async function fetchSuggestions(query) {
    try {
        const response = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        renderSuggestions(data.suggestions || []);
    } catch (error) {
        console.error('Failed to fetch suggestions:', error);
    }
}

function renderSuggestions(suggestions) {
    const dropdown = document.getElementById('suggestionsDropdown');
    suggestionIndex = -1;

    if (suggestions.length === 0) {
        hideSuggestions();
        return;
    }

    dropdown.innerHTML = suggestions.map((s, index) => `
        <div class="suggestion-item" data-text="${escapeHtml(s.text)}" data-type="${s.type}">
            <span class="suggestion-icon">${s.icon || '📄'}</span>
            <span class="suggestion-text">${escapeHtml(s.text)}</span>
            <span class="suggestion-type">${getTypeName(s.type)}</span>
            ${s.count > 1 ? `<span class="suggestion-count">${s.count}</span>` : ''}
        </div>
    `).join('');

    // Add click handlers
    dropdown.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => selectSuggestion(item));
    });

    dropdown.classList.add('active');
}

function selectSuggestion(item) {
    const text = item.dataset.text;
    document.getElementById('searchInput').value = text;
    hideSuggestions();
    performSearch(text);
}

function showSuggestions() {
    const query = document.getElementById('searchInput').value.trim();
    if (query.length >= 1) {
        fetchSuggestions(query);
    }
}

function hideSuggestions() {
    document.getElementById('suggestionsDropdown').classList.remove('active');
    suggestionIndex = -1;
}

async function performSearch(query) {
    if (!query) {
        renderPapers(papers);
        return;
    }

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        renderPapers(data.results || []);
    } catch (error) {
        console.error('Search failed:', error);
        showToast('搜索失败', 'error');
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    hideSuggestions();
    renderPapers(papers);
    currentPaper = null;
    hidePreview();
}

// ============== Rendering ==============
function renderPapers(papersToRender) {
    const grid = document.getElementById('papersGrid');
    const countEl = document.getElementById('resultsCount');

    countEl.textContent = papersToRender.length;

    if (papersToRender.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-title">未找到匹配的论文</div>
                <div class="empty-state-text">
                    尝试使用不同的关键词或检查拼写
                </div>
            </div>
        `;
        return;
    }

    grid.innerHTML = papersToRender.map(paper => `
        <div class="paper-card ${currentPaper?.id === paper.id ? 'active' : ''}"
             data-id="${paper.id}"
             onclick="selectPaper(${paper.id})"
             ondblclick="openPaper(${paper.id})">
            <div class="paper-title">${escapeHtml(paper.title)}</div>
            ${paper.authors ? `<div class="paper-authors">👤 ${escapeHtml(paper.authors)}</div>` : ''}
            <div class="paper-meta">
                ${paper.year ? `<span class="paper-year">${paper.year}</span>` : ''}
            </div>
            ${paper.tags ? `
                <div class="paper-tags">
                    ${paper.tags.split(',').slice(0, 4).map(tag =>
                        `<span class="tag">${escapeHtml(tag.trim())}</span>`
                    ).join('')}
                </div>
            ` : ''}
            <div class="paper-folder">📂 ${escapeHtml(getShortPath(paper.folder_path))}</div>
        </div>
    `).join('');
}

// ============== Paper Actions ==============
function selectPaper(paperId) {
    const paper = papers.find(p => p.id === paperId) ||
                  document.querySelector(`.paper-card[data-id="${paperId}"]`);

    // Fetch paper if not in local cache
    fetch(`/api/papers/${paperId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentPaper = data.paper;
                showPreview(currentPaper);

                // Update card selection
                document.querySelectorAll('.paper-card').forEach(card => {
                    card.classList.toggle('active', parseInt(card.dataset.id) === paperId);
                });
            }
        })
        .catch(err => console.error('Failed to load paper:', err));
}

function showPreview(paper) {
    const placeholder = document.getElementById('previewPlaceholder');
    const info = document.getElementById('previewInfo');
    const pdf = document.getElementById('previewPdf');
    const btnOpen = document.getElementById('btnOpenPaper');
    const btnEdit = document.getElementById('btnEditPaper');

    placeholder.style.display = 'none';
    info.style.display = 'block';
    pdf.style.display = 'block';
    btnOpen.disabled = false;
    btnEdit.disabled = false;

    // Render info
    info.innerHTML = `
        <h3>${escapeHtml(paper.title)}</h3>
        ${paper.authors ? `<p><strong>作者：</strong>${escapeHtml(paper.authors)}</p>` : ''}
        ${paper.year ? `<p><strong>年份：</strong>${paper.year}</p>` : ''}
        ${paper.tags ? `<p><strong>标签：</strong>${escapeHtml(paper.tags)}</p>` : ''}
        ${paper.abstract ? `<p style="margin-top: 0.5rem;"><strong>摘要：</strong>${escapeHtml(paper.abstract.substring(0, 200))}...</p>` : ''}
    `;

    // Load PDF
    pdf.innerHTML = `<iframe src="/api/pdf/${paper.id}#toolbar=0" title="PDF Preview"></iframe>`;
}

function hidePreview() {
    const placeholder = document.getElementById('previewPlaceholder');
    const info = document.getElementById('previewInfo');
    const pdf = document.getElementById('previewPdf');
    const btnOpen = document.getElementById('btnOpenPaper');
    const btnEdit = document.getElementById('btnEditPaper');

    placeholder.style.display = 'flex';
    info.style.display = 'none';
    pdf.style.display = 'none';
    pdf.innerHTML = '';
    btnOpen.disabled = true;
    btnEdit.disabled = true;
}

async function openPaper(paperId) {
    try {
        const response = await fetch(`/api/papers/${paperId}/open`, { method: 'POST' });
        const data = await response.json();

        if (!data.success) {
            showToast('无法打开文件', 'error');
        }
    } catch (error) {
        console.error('Failed to open paper:', error);
        showToast('打开失败', 'error');
    }
}

function openCurrentPaper() {
    if (currentPaper) {
        openPaper(currentPaper.id);
    }
}

// ============== Edit Modal ==============
function editCurrentPaper() {
    if (!currentPaper) return;

    document.getElementById('editPaperId').value = currentPaper.id;
    document.getElementById('editTitle').value = currentPaper.title || '';
    document.getElementById('editAuthors').value = currentPaper.authors || '';
    document.getElementById('editTags').value = currentPaper.tags || '';
    document.getElementById('editKeywords').value = currentPaper.keywords || '';
    document.getElementById('editYear').value = currentPaper.year || '';
    document.getElementById('editAbstract').value = currentPaper.abstract || '';

    document.getElementById('editModal').classList.add('active');
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
}

async function savePaper() {
    const paperId = document.getElementById('editPaperId').value;

    const data = {
        title: document.getElementById('editTitle').value,
        authors: document.getElementById('editAuthors').value,
        tags: document.getElementById('editTags').value,
        keywords: document.getElementById('editKeywords').value,
        year: document.getElementById('editYear').value,
        abstract: document.getElementById('editAbstract').value,
    };

    try {
        const response = await fetch(`/api/papers/${paperId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            currentPaper = result.paper;
            showPreview(currentPaper);

            // Reload papers
            await loadPapers();
            await loadStats();

            closeEditModal();
            showToast('保存成功', 'success');
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        console.error('Failed to save paper:', error);
        showToast('保存失败', 'error');
    }
}

// ============== Scan & Management ==============
async function scanPapers() {
    const path = document.getElementById('settingsPapersDir')?.value;

    showToast('正在扫描论文文件夹...', 'info');

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path || undefined })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`扫描完成：新增 ${data.added} 篇，更新 ${data.updated} 篇`, 'success');
            await loadPapers();
            await loadStats();
        } else {
            showToast(`扫描失败：${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Scan failed:', error);
        showToast('扫描失败', 'error');
    }
}

async function verifyPapers() {
    try {
        const response = await fetch('/api/verify', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            if (data.missing_count > 0) {
                showToast(`发现 ${data.missing_count} 个失效文件`, 'warning');
            } else {
                showToast('所有文件均有效', 'success');
            }
        }
    } catch (error) {
        console.error('Verify failed:', error);
        showToast('验证失败', 'error');
    }
}

async function cleanupPapers() {
    if (!confirm('确定要清理所有失效的论文记录吗？')) return;

    try {
        const response = await fetch('/api/cleanup', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showToast(`已清理 ${data.removed} 条失效记录`, 'success');
            await loadPapers();
            await loadStats();
        }
    } catch (error) {
        console.error('Cleanup failed:', error);
        showToast('清理失败', 'error');
    }
}

// ============== Settings ==============
function openSettings() {
    document.getElementById('settingsModal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settingsModal').classList.remove('active');
}

async function saveSettings() {
    const papersDir = document.getElementById('settingsPapersDir').value;

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ papers_dir: papersDir })
        });

        const data = await response.json();

        if (data.success) {
            closeSettings();
            showToast('设置已保存', 'success');
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        showToast('保存失败', 'error');
    }
}

// ============== Utilities ==============
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getShortPath(path) {
    if (!path) return '';
    const parts = path.split(/[/\\]/);
    return parts.slice(-2).join('/');
}

function getTypeName(type) {
    const names = {
        'author': '作者',
        'tag': '标签',
        'title': '标题'
    };
    return names[type] || type;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
