# Paper Search System

A beautiful and powerful local paper management system with fuzzy search support for Chinese/English author names and research fields.

[中文说明](#中文说明)

## Features

### Local Paper Management
- **Smart Folder Scanning**: Automatically scan your paper directories and extract metadata from PDFs
- **Fuzzy Search**: Search by title, author name (supports multiple name formats), or keywords
- **Chinese-English Name Matching**: Search "周黎安", "Li'an Zhou", or "Zhou Lian" - all find the same author
- **Tag-based Organization**: Papers are automatically tagged based on folder structure
- **Field Synonym Matching**: Search "行为政经" finds papers tagged with "行为经济学" or "政治经济学"
- **PDF Preview**: Preview papers directly in the browser
- **Quick Open**: Double-click to open papers with your default PDF reader (WPS, Adobe, etc.)

### Online Academic Search
- **Multi-source Search**: Search across Semantic Scholar, CrossRef, and arXiv
- **Author Profiles**: View author statistics including paper count, citations, and h-index
- **Journal Filtering**: Filter by top economics journals (AER, QJE, ECMA, JPE, RES), political science journals (AJPS, APSR, JOP), and more

## Screenshots

The interface features an elegant, minimalist design with:
- Clean serif typography (Georgia, Noto Serif SC)
- Smooth animations and transitions
- Responsive layout with PDF preview panel
- Smart search suggestions

## Installation

### Requirements
- Python 3.8+
- Windows / macOS / Linux

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Paper-search-system-.git
cd Paper-search-system-
```

2. Create virtual environment (optional but recommended):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to: `http://localhost:5000`

### Configuration

Set your papers directory before first use:
- Click the ⚙️ Settings button
- Enter your papers folder path (e.g., `E:\研究` or `/home/user/papers`)
- Click "Save" and then "Scan Papers"

## Usage

### Searching Papers

Type in the search box to find papers by:
- **Title**: Full or partial title match
- **Author**: Chinese name, English name, or any variation
  - "周黎安" → finds all papers by this author
  - "Li'an Zhou" → same result
  - "Zhou, Lian" → same result
- **Tags/Fields**: Including synonyms
  - "行为" → finds "行为经济学", "行为政治经济学"
  - "决策理论" → finds related papers

### Managing Papers

- **Click** a paper to preview it
- **Double-click** to open with default application
- **Edit** button to modify metadata (authors, tags, keywords)
- **Scan** button to refresh from disk

### Online Search

Navigate to the "Online Search" tab to:
- Search across academic databases
- Look up author profiles
- Filter by specific journals

## Project Structure

```
Paper-search-system-/
├── app.py              # Flask application
├── database.py         # SQLite database operations
├── scanner.py          # Paper scanning and metadata extraction
├── search.py           # Fuzzy search engine
├── online_search.py    # Online academic search
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css   # Styles
│   └── js/
│       └── app.js      # Frontend JavaScript
├── templates/
│   ├── index.html      # Main page
│   └── online.html     # Online search page
└── data/
    └── papers.db       # SQLite database
```

## API Reference

### Local Search API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search?q=query` | GET | Search papers |
| `/api/suggestions?q=query` | GET | Get search suggestions |
| `/api/papers` | GET | List all papers |
| `/api/papers/<id>` | GET/PUT/DELETE | Paper CRUD |
| `/api/papers/<id>/open` | POST | Open with default app |
| `/api/pdf/<id>` | GET | Get PDF for preview |
| `/api/scan` | POST | Scan papers directory |

### Online Search API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/online/search?q=query` | GET | Search online databases |
| `/api/online/author?name=name` | GET | Search author profile |
| `/api/online/journals` | GET | List supported journals |

## License

MIT License

---

# 中文说明

一个美观、强大的本地论文管理系统，支持中英文作者姓名和研究领域的模糊搜索。

## 功能特点

### 本地论文管理
- **智能文件夹扫描**：自动扫描论文目录，从PDF中提取元数据
- **模糊搜索**：按标题、作者姓名（支持多种格式）或关键词搜索
- **中英文姓名匹配**：搜索"周黎安"、"Li'an Zhou"或"Zhou Lian"都能找到同一作者
- **基于标签的组织**：论文根据文件夹结构自动打标签
- **领域同义词匹配**：搜索"行为政经"可找到标记为"行为经济学"或"政治经济学"的论文
- **PDF预览**：直接在浏览器中预览论文
- **快速打开**：双击使用默认PDF阅读器（WPS、Adobe等）打开论文

### 在线学术搜索
- **多源搜索**：跨Semantic Scholar、CrossRef和arXiv搜索
- **作者档案**：查看作者统计信息，包括论文数、引用数和h指数
- **期刊筛选**：按经济学顶刊（AER、QJE、ECMA、JPE、RES）、政治学期刊（AJPS、APSR、JOP）等筛选

## 安装

### 环境要求
- Python 3.8+
- Windows / macOS / Linux

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/Paper-search-system-.git
cd Paper-search-system-
```

2. 创建虚拟环境（可选但推荐）：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行应用：
```bash
python app.py
```

5. 打开浏览器访问：`http://localhost:5000`

### 配置

首次使用前设置论文目录：
- 点击 ⚙️ 设置按钮
- 输入论文文件夹路径（如 `E:\研究` 或 `/home/user/papers`）
- 点击"保存"，然后点击"扫描文件夹"

## 使用方法

### 搜索论文

在搜索框中输入以下内容查找论文：
- **标题**：完整或部分标题匹配
- **作者**：中文名、英文名或任何变体
  - "周黎安" → 找到该作者的所有论文
  - "Li'an Zhou" → 相同结果
  - "Zhou, Lian" → 相同结果
- **标签/领域**：包括同义词
  - "行为" → 找到"行为经济学"、"行为政治经济学"
  - "决策理论" → 找到相关论文

### 管理论文

- **单击** 论文预览
- **双击** 用默认应用打开
- **编辑** 按钮修改元数据（作者、标签、关键词）
- **扫描** 按钮从磁盘刷新

### 在线搜索

导航到"在线搜索"标签页：
- 跨学术数据库搜索
- 查询作者档案
- 按特定期刊筛选

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite + FTS5全文搜索
- **前端**：原生HTML/CSS/JavaScript
- **PDF处理**：pypdf
- **中文处理**：pypinyin, jieba
- **在线搜索**：Semantic Scholar API, CrossRef API, arXiv API

## 许可证

MIT License
