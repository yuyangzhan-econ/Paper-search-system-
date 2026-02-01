/**
 * Paper Search System - Main JavaScript
 * Handles local paper search, preview, and management
 */

// ============== State ==============
let papers = [];
let currentPaper = null;
let searchTimeout = null;
let suggestionIndex = -1;
let allTags = [];
let allAuthors = [];
let isSearching = false;

// Edit modal tag/author state
let editAuthors = [];
let editTags = [];
let editKeywords = [];

// Settings
let autoPreview = localStorage.getItem('autoPreview') !== 'false'; // Default true

// ============== Initialization ==============
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Load stats
    await loadStats();

    // Load all papers
    await loadPapers();

    // Load tags and authors for suggestions
    await loadTagsAndAuthors();

    // Setup event listeners
    setupEventListeners();

    // Setup tag chip inputs
    setupTagInputs();
}

function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');

    // Search input events - only show suggestions, don't search
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

async function loadTagsAndAuthors() {
    try {
        const [tagsRes, authorsRes] = await Promise.all([
            fetch('/api/tags'),
            fetch('/api/authors')
        ]);
        const tagsData = await tagsRes.json();
        const authorsData = await authorsRes.json();
        allTags = tagsData.tags || [];
        allAuthors = authorsData.authors || [];
    } catch (error) {
        console.error('Failed to load tags/authors:', error);
    }
}

// ============== Search ==============
let suggestionTimeout = null;

function handleSearchInput(e) {
    const query = e.target.value.trim();

    // Clear previous timeouts
    clearTimeout(searchTimeout);
    clearTimeout(suggestionTimeout);

    // Only show suggestions after a longer delay to avoid freezing
    if (query.length >= 2) {
        suggestionTimeout = setTimeout(() => {
            fetchSuggestions(query);
        }, 300);  // Increased delay for better performance
    } else if (query.length === 0) {
        hideSuggestions();
        // Show all papers when input is cleared
        renderPapers(papers);
        hideSearchLoading();
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
                // Perform search on Enter
                hideSuggestions();
                performSearch(e.target.value);
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

// Show/hide search loading indicator
function showSearchLoading() {
    const grid = document.getElementById('papersGrid');
    grid.innerHTML = `
        <div class="empty-state">
            <div class="loading-spinner"></div>
            <div class="empty-state-title" style="margin-top: 1rem;">正在搜索...</div>
        </div>
    `;
    isSearching = true;
}

function hideSearchLoading() {
    isSearching = false;
}

// Search button click handler (called from HTML)
function triggerSearch() {
    const query = document.getElementById('searchInput').value.trim();
    hideSuggestions();
    performSearch(query);
}

async function performSearch(query) {
    if (isSearching) return;

    if (!query) {
        renderPapers(papers);
        return;
    }

    showSearchLoading();

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        hideSearchLoading();

        // Use requestAnimationFrame for smoother rendering
        requestAnimationFrame(() => {
            renderPapers(data.results || []);
        });
    } catch (error) {
        console.error('Search failed:', error);
        hideSearchLoading();
        showToast('搜索失败', 'error');
        renderPapers([]);
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    hideSuggestions();
    hideSearchLoading();
    renderPapers(papers);
    currentPaper = null;
    hidePreview();
}

// ============== Rendering ==============
let renderTimeout = null;

function renderPapers(papersToRender) {
    // Cancel any pending render
    if (renderTimeout) {
        cancelAnimationFrame(renderTimeout);
    }

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

    // Limit display to 200 papers for performance
    const papersToShow = papersToRender.slice(0, 200);

    // Use requestAnimationFrame for smoother rendering
    renderTimeout = requestAnimationFrame(() => {
        // Build HTML string
        const html = papersToShow.map(paper => {
            const shortDetails = paper.details ? paper.details.substring(0, 80) : '';
            return `
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
                ${shortDetails ? `<div class="paper-details" style="font-size:0.8rem;color:var(--text-muted);margin-top:0.25rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">📝 ${escapeHtml(shortDetails)}...</div>` : ''}
                <div class="paper-folder">📂 ${escapeHtml(getShortPath(paper.folder_path))}</div>
            </div>
        `}).join('');

        grid.innerHTML = html;

        // Show notice if results were truncated
        if (papersToRender.length > 200) {
            grid.insertAdjacentHTML('beforeend', `
                <div style="text-align:center;padding:1rem;color:var(--text-muted);font-size:0.9rem;">
                    显示前200条结果，共${papersToRender.length}条
                </div>
            `);
        }
    });
}

// ============== Paper Actions ==============
function selectPaper(paperId) {
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

// Track if PDF is loading to prevent multiple loads
let pdfLoadingPaperId = null;

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

    // Format details for display (truncate if too long)
    const detailsText = paper.details ? paper.details.substring(0, 300) : '';
    const hasMoreDetails = paper.details && paper.details.length > 300;

    // Render info with details field
    info.innerHTML = `
        <h3>${escapeHtml(paper.title)}</h3>
        ${paper.authors ? `<p><strong>作者：</strong>${escapeHtml(paper.authors)}</p>` : ''}
        ${paper.year ? `<p><strong>年份：</strong>${paper.year}</p>` : ''}
        ${paper.tags ? `<p><strong>标签：</strong>${escapeHtml(paper.tags)}</p>` : ''}
        ${detailsText ? `
            <div style="margin-top: 0.5rem; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 4px; font-size: 0.85rem;">
                <strong>详情（首页内容）：</strong>
                <span style="color: var(--text-muted);">${escapeHtml(detailsText)}${hasMoreDetails ? '...' : ''}</span>
            </div>
        ` : ''}
        ${paper.abstract ? `<p style="margin-top: 0.5rem;"><strong>摘要：</strong>${escapeHtml(paper.abstract.substring(0, 200))}...</p>` : ''}
    `;

    // Check auto-preview setting
    if (autoPreview) {
        // Auto-load PDF preview
        pdf.innerHTML = `
            <div class="preview-placeholder" id="pdfLoading" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 1rem;">正在加载预览...</p>
            </div>
        `;
        // Slight delay to not block UI
        setTimeout(() => loadPdfPreview(paper.id), 50);
    } else {
        // Show load button (manual mode)
        pdf.innerHTML = `
            <div class="preview-placeholder" id="pdfLoading" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <div class="preview-placeholder-icon">📄</div>
                <p>点击加载PDF预览</p>
                <button class="btn btn-primary btn-sm" onclick="loadPdfPreview(${paper.id})" style="margin-top: 0.5rem;">
                    📄 加载预览
                </button>
            </div>
        `;
    }
}

function loadPdfPreview(paperId) {
    // Prevent double-loading
    if (pdfLoadingPaperId === paperId) return;
    pdfLoadingPaperId = paperId;

    const pdf = document.getElementById('previewPdf');

    // Show loading state
    pdf.innerHTML = `
        <div class="preview-placeholder" id="pdfLoading" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;">
            <div class="loading-spinner"></div>
            <p style="margin-top: 1rem;">正在加载...</p>
        </div>
    `;

    // Create iframe with minimal options for speed
    const iframe = document.createElement('iframe');
    iframe.src = `/api/pdf/${paperId}#toolbar=0&view=FitH`;
    iframe.title = 'PDF Preview';
    iframe.style.cssText = 'width:100%;height:100%;border:none;';

    // Handle load complete
    iframe.onload = () => {
        pdfLoadingPaperId = null;
        const loading = document.getElementById('pdfLoading');
        if (loading) loading.remove();
    };

    iframe.onerror = () => {
        pdfLoadingPaperId = null;
        pdf.innerHTML = `
            <div class="preview-placeholder" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <div class="preview-placeholder-icon">⚠️</div>
                <p>预览加载失败</p>
                <button class="btn btn-secondary btn-sm" onclick="loadPdfPreview(${paperId})" style="margin-top: 0.5rem;">
                    🔄 重新加载
                </button>
            </div>
        `;
    };

    pdf.appendChild(iframe);
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

// ============== Tag Chip Input Setup ==============
function setupTagInputs() {
    setupChipInput('editAuthorsInput', 'authorChips', 'editAuthors', () => editAuthors, v => editAuthors = v);
    setupChipInput('editTagsInput', 'tagChips', 'editTags', () => editTags, v => editTags = v, true);
    setupChipInput('editKeywordsInput', 'keywordChips', 'editKeywords', () => editKeywords, v => editKeywords = v);
}

function setupChipInput(inputId, chipsId, hiddenId, getArray, setArray, showSuggestions = false) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const value = input.value.trim().replace(/,/g, '');
            if (value && !getArray().includes(value)) {
                setArray([...getArray(), value]);
                renderChips(chipsId, getArray(), setArray, hiddenId);
            }
            input.value = '';
        } else if (e.key === 'Backspace' && !input.value) {
            const arr = getArray();
            if (arr.length > 0) {
                setArray(arr.slice(0, -1));
                renderChips(chipsId, getArray(), setArray, hiddenId);
            }
        }
    });

    // Show tag suggestions
    if (showSuggestions) {
        input.addEventListener('input', () => {
            renderTagSuggestions(input.value.trim(), getArray, setArray, chipsId, hiddenId);
        });
        input.addEventListener('focus', () => {
            renderTagSuggestions(input.value.trim(), getArray, setArray, chipsId, hiddenId);
        });
    }

    // Click on container focuses input
    const container = input.closest('.tag-input-container');
    if (container) {
        container.addEventListener('click', () => input.focus());
    }
}

function renderChips(containerId, items, setArray, hiddenId) {
    const container = document.getElementById(containerId);
    const hidden = document.getElementById(hiddenId);

    container.innerHTML = items.map((item, index) => `
        <span class="tag-chip">
            ${escapeHtml(item)}
            <span class="tag-chip-remove" onclick="removeChip(event, ${index}, '${containerId}', '${hiddenId}')">&times;</span>
        </span>
    `).join('');

    hidden.value = items.join(', ');
}

function removeChip(event, index, containerId, hiddenId) {
    event.stopPropagation();

    if (containerId === 'authorChips') {
        editAuthors.splice(index, 1);
        renderChips(containerId, editAuthors, v => editAuthors = v, hiddenId);
    } else if (containerId === 'tagChips') {
        editTags.splice(index, 1);
        renderChips(containerId, editTags, v => editTags = v, hiddenId);
    } else if (containerId === 'keywordChips') {
        editKeywords.splice(index, 1);
        renderChips(containerId, editKeywords, v => editKeywords = v, hiddenId);
    }
}

function renderTagSuggestions(query, getArray, setArray, chipsId, hiddenId) {
    const suggestionsContainer = document.getElementById('tagSuggestions');
    if (!suggestionsContainer) return;

    const currentTags = getArray();
    const filtered = allTags.filter(tag =>
        !currentTags.includes(tag) &&
        (query === '' || tag.toLowerCase().includes(query.toLowerCase()))
    ).slice(0, 10);

    if (filtered.length === 0) {
        suggestionsContainer.innerHTML = '';
        return;
    }

    suggestionsContainer.innerHTML = filtered.map(tag => `
        <span class="tag-suggestion" onclick="addSuggestedTag('${escapeHtml(tag)}', '${chipsId}', '${hiddenId}')">${escapeHtml(tag)}</span>
    `).join('');
}

function addSuggestedTag(tag, chipsId, hiddenId) {
    if (chipsId === 'tagChips' && !editTags.includes(tag)) {
        editTags.push(tag);
        renderChips(chipsId, editTags, v => editTags = v, hiddenId);
        document.getElementById('editTagsInput').value = '';
        renderTagSuggestions('', () => editTags, v => editTags = v, chipsId, hiddenId);
    }
}

// ============== Edit Modal ==============
function editCurrentPaper() {
    if (!currentPaper) return;

    document.getElementById('editPaperId').value = currentPaper.id;
    document.getElementById('editTitle').value = currentPaper.title || '';
    document.getElementById('editYear').value = currentPaper.year || '';
    document.getElementById('editAbstract').value = currentPaper.abstract || '';

    // Parse comma-separated values into arrays
    editAuthors = (currentPaper.authors || '').split(',').map(s => s.trim()).filter(s => s);
    editTags = (currentPaper.tags || '').split(',').map(s => s.trim()).filter(s => s);
    editKeywords = (currentPaper.keywords || '').split(',').map(s => s.trim()).filter(s => s);

    // Render chips
    renderChips('authorChips', editAuthors, v => editAuthors = v, 'editAuthors');
    renderChips('tagChips', editTags, v => editTags = v, 'editTags');
    renderChips('keywordChips', editKeywords, v => editKeywords = v, 'editKeywords');

    // Clear inputs
    document.getElementById('editAuthorsInput').value = '';
    document.getElementById('editTagsInput').value = '';
    document.getElementById('editKeywordsInput').value = '';

    // Show tag suggestions
    renderTagSuggestions('', () => editTags, v => editTags = v, 'tagChips', 'editTags');

    document.getElementById('editModal').classList.add('active');
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
}

async function savePaper() {
    const paperId = document.getElementById('editPaperId').value;

    const data = {
        title: document.getElementById('editTitle').value,
        authors: editAuthors.join(', '),
        tags: editTags.join(', '),
        keywords: editKeywords.join(', '),
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
            await loadTagsAndAuthors();

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

    // Show progress modal
    const modal = document.getElementById('scanModal');
    const progressBar = document.getElementById('scanProgressBar');
    const statusEl = document.getElementById('scanStatus');
    const detailEl = document.getElementById('scanDetail');

    modal.classList.add('active');
    progressBar.style.width = '0%';
    statusEl.textContent = '正在启动扫描...';
    detailEl.textContent = '';

    try {
        // Start scan
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path || undefined })
        });

        const data = await response.json();

        if (!data.success && data.error !== 'Scan already in progress') {
            modal.classList.remove('active');
            showToast(`扫描失败：${data.error}`, 'error');
            return;
        }

        // Poll for progress
        pollScanProgress(modal, progressBar, statusEl, detailEl);

    } catch (error) {
        console.error('Scan failed:', error);
        modal.classList.remove('active');
        showToast('扫描失败', 'error');
    }
}

async function pollScanProgress(modal, progressBar, statusEl, detailEl) {
    const poll = async () => {
        try {
            const response = await fetch('/api/scan/progress');
            const progress = await response.json();

            if (progress.total > 0) {
                const percent = Math.round((progress.current / progress.total) * 100);
                progressBar.style.width = `${percent}%`;
                statusEl.textContent = `正在扫描 ${progress.current}/${progress.total} (${percent}%)`;
            } else if (progress.running) {
                statusEl.textContent = progress.current_file || '正在准备...';
            }

            if (progress.current_file) {
                detailEl.textContent = progress.current_file;
            }

            if (progress.complete) {
                progressBar.style.width = '100%';
                statusEl.textContent = `扫描完成！新增 ${progress.added} 篇，更新 ${progress.updated} 篇`;
                detailEl.textContent = progress.skipped > 0 ? `跳过 ${progress.skipped} 个文件` : '';

                setTimeout(async () => {
                    modal.classList.remove('active');
                    await loadPapers();
                    await loadStats();
                    await loadTagsAndAuthors();
                    showToast(`扫描完成：新增 ${progress.added} 篇，更新 ${progress.updated} 篇`, 'success');
                }, 1500);
                return;
            }

            if (progress.error) {
                statusEl.textContent = `扫描出错：${progress.error}`;
                setTimeout(() => modal.classList.remove('active'), 2000);
                return;
            }

            if (progress.running) {
                setTimeout(poll, 300);
            } else if (!progress.complete) {
                // Scan finished without complete flag
                setTimeout(async () => {
                    modal.classList.remove('active');
                    await loadPapers();
                    await loadStats();
                }, 500);
            }
        } catch (error) {
            console.error('Progress poll failed:', error);
            setTimeout(poll, 1000);
        }
    };

    poll();
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
    // Sync auto-preview checkbox
    const checkbox = document.getElementById('settingsAutoPreview');
    if (checkbox) checkbox.checked = autoPreview;
}

function closeSettings() {
    document.getElementById('settingsModal').classList.remove('active');
}

function toggleAutoPreview() {
    const checkbox = document.getElementById('settingsAutoPreview');
    autoPreview = checkbox.checked;
    localStorage.setItem('autoPreview', autoPreview);
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
