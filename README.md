# Paper Search System

A beautiful and powerful local paper management system with fuzzy search support for Chinese/English author names and research fields. Runs as a native desktop application.

[中文说明](#中文说明)

## Features

### Local Paper Management
- **Smart Folder Scanning**: Automatically scan your paper directories and extract metadata from PDFs
- **Fuzzy Search**: Search by title, author name (supports multiple name formats), or keywords
- **Chinese-English Name Matching**: Search "周黎安", "Li'an Zhou", or "Zhou Lian" - all find the same author
- **Tag-based Organization**: Papers are automatically tagged based on folder structure
- **Field Synonym Matching**: Search "行为政经" finds papers tagged with "行为经济学" or "政治经济学"
- **PDF Preview**: Preview papers directly in the app
- **Quick Open**: Double-click to open papers with your default PDF reader (WPS, Adobe, etc.)
- **Native Desktop Window**: No browser required!

### Online Academic Search
- **Multi-source Search**: Search across Semantic Scholar, CrossRef, and arXiv
- **Author Profiles**: View author statistics including paper count, citations, and h-index
- **Journal Filtering**: Filter by top economics journals (AER, QJE, ECMA, JPE, RES), political science journals (AJPS, APSR, JOP), and more

## Quick Start (Windows)

### Method 1: One-Click Installation (Recommended)

1. **Download and Extract**
   - Download the project ZIP file or clone the repository
   - Extract to any folder (e.g., `D:\PaperSearch`)

2. **Run the Installer**
   - Double-click `install.bat`
   - Wait for installation to complete (first time takes 2-3 minutes)

3. **Launch the App**
   - Double-click the "Paper Search" shortcut on your desktop
   - Or double-click `PaperSearch.bat` in the project folder

### Method 2: Manual Installation

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - **IMPORTANT**: Check "Add Python to PATH" during installation!

2. **Open Command Prompt**
   - Press `Win + R`, type `cmd`, press Enter

3. **Navigate to project folder**
   ```cmd
   cd D:\PaperSearch
   ```

4. **Create virtual environment**
   ```cmd
   python -m venv venv
   ```

5. **Activate virtual environment**
   ```cmd
   venv\Scripts\activate
   ```

6. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

7. **Run the application**
   ```cmd
   python desktop_app.py
   ```

## First-Time Setup

1. **Set Papers Directory**
   - Click ⚙️ Settings button
   - Enter your papers folder path (e.g., `E:\研究`)
   - Click "Save"

2. **Scan Papers**
   - Click "Scan Papers" button
   - Wait for scanning to complete
   - Your papers will appear in the list

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
- **Double-click** to open with default application (WPS, Adobe, etc.)
- **Edit** button to modify metadata (authors, tags, keywords)
- **Scan** button to refresh from disk

### Online Search

Click "Online Search" tab to:
- Search across academic databases
- Look up author profiles
- Filter by specific journals

## Project Structure

```
Paper-search-system-/
├── install.bat         # One-click installer (Windows)
├── PaperSearch.bat     # Launch app (Windows)
├── desktop_app.py      # Desktop application launcher
├── app.py              # Flask backend
├── database.py         # SQLite database
├── scanner.py          # Paper scanning
├── search.py           # Fuzzy search engine
├── online_search.py    # Online academic search
├── requirements.txt    # Python dependencies
├── static/             # CSS and JavaScript
├── templates/          # HTML templates
└── data/               # Database (created on first run)
```

## Troubleshooting

### "Python is not installed"
- Download Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### App doesn't start
- Try running `install.bat` again
- Make sure antivirus isn't blocking Python

### Papers not showing
- Check that the papers directory path is correct
- Make sure your papers are PDF files
- Click "Scan Papers" to refresh

## License

MIT License

---

# 中文说明

一个美观、强大的本地论文管理系统，支持中英文作者姓名和研究领域的模糊搜索。作为独立桌面应用运行，无需浏览器。

## 功能特点

### 本地论文管理
- **智能文件夹扫描**：自动扫描论文目录，从PDF中提取元数据
- **模糊搜索**：按标题、作者姓名（支持多种格式）或关键词搜索
- **中英文姓名匹配**：搜索"周黎安"、"Li'an Zhou"或"Zhou Lian"都能找到同一作者
- **基于标签的组织**：论文根据文件夹结构自动打标签
- **领域同义词匹配**：搜索"行为政经"可找到标记为"行为经济学"或"政治经济学"的论文
- **PDF预览**：直接在应用中预览论文
- **快速打开**：双击使用默认PDF阅读器（WPS、Adobe等）打开论文
- **独立桌面窗口**：无需打开浏览器！

### 在线学术搜索
- **多源搜索**：跨Semantic Scholar、CrossRef和arXiv搜索
- **作者档案**：查看作者统计信息，包括论文数、引用数和h指数
- **期刊筛选**：按经济学顶刊（AER、QJE、ECMA、JPE、RES）、政治学期刊（AJPS、APSR、JOP）等筛选

## 快速开始 (Windows)

### 方法一：一键安装（推荐）

1. **下载并解压**
   - 下载项目 ZIP 文件或克隆仓库
   - 解压到任意文件夹（如 `D:\PaperSearch`）

2. **运行安装程序**
   - 双击 `install.bat`
   - 等待安装完成（首次安装需要2-3分钟）

3. **启动应用**
   - 双击桌面上的 "Paper Search" 快捷方式
   - 或双击项目文件夹中的 `PaperSearch.bat`

### 方法二：手动安装

1. **安装 Python**（如果尚未安装）
   - 从 https://www.python.org/downloads/ 下载
   - **重要**：安装时务必勾选 "Add Python to PATH"！

2. **打开命令提示符**
   - 按 `Win + R`，输入 `cmd`，按回车

3. **进入项目文件夹**
   ```cmd
   cd D:\PaperSearch
   ```

4. **创建虚拟环境**
   ```cmd
   python -m venv venv
   ```

5. **激活虚拟环境**
   ```cmd
   venv\Scripts\activate
   ```

6. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   ```

7. **运行应用**
   ```cmd
   python desktop_app.py
   ```

## 首次使用设置

1. **设置论文目录**
   - 点击 ⚙️ 设置按钮
   - 输入论文文件夹路径（如 `E:\研究`）
   - 点击"保存"

2. **扫描论文**
   - 点击"扫描文件夹"按钮
   - 等待扫描完成
   - 论文列表将显示出来

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
- **双击** 用默认应用打开（WPS、Adobe等）
- **编辑** 按钮修改元数据（作者、标签、关键词）
- **扫描** 按钮从磁盘刷新

### 在线搜索

点击"在线搜索"标签页：
- 跨学术数据库搜索
- 查询作者档案
- 按特定期刊筛选

## 常见问题

### "Python 未安装"
- 从 https://www.python.org/downloads/ 下载 Python
- 安装时必须勾选 "Add Python to PATH"

### 应用无法启动
- 尝试重新运行 `install.bat`
- 确保杀毒软件没有阻止 Python

### 论文不显示
- 检查论文目录路径是否正确
- 确保论文是 PDF 格式
- 点击"扫描文件夹"刷新

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite + FTS5全文搜索
- **桌面窗口**：pywebview
- **前端**：原生HTML/CSS/JavaScript
- **PDF处理**：pypdf
- **中文处理**：pypinyin, jieba
- **在线搜索**：Semantic Scholar API, CrossRef API, arXiv API

## 许可证

MIT License
