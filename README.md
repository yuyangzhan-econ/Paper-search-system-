# Paper Search System

一个美观、强大的本地论文管理系统，支持中英文作者姓名和研究领域的模糊搜索。

[English](#english) | [中文说明](#中文说明)

## 致谢 / Credits

本项目的在线学术搜索功能参考了 [Econ-Paper-Search](https://github.com/Alalalalaki/Econ-Paper-Search) 项目的设计思路，特此致谢。

The online academic search functionality of this project was inspired by the [Econ-Paper-Search](https://github.com/Alalalalaki/Econ-Paper-Search) project. We appreciate their contribution to the academic community.

---

# 中文说明

## 为什么需要这个系统？

### 传统文件夹管理的痛点

如果你用文件夹整理文献，可能会遇到以下问题：

1. **按作者检索困难**：想找某位作者的所有论文？需要一个个文件夹翻找，或者用 Windows 搜索慢慢等待
2. **按关键词检索困难**：想找关于"制度经济学"的论文？文件名里不一定有这个词，搜不到
3. **中英文名不统一**：同一个作者可能有"周黎安"、"Li-An Zhou"、"Zhou, Lian"等多种写法，无法统一检索
4. **跨文件夹检索繁琐**：论文可能分散在"微观经济学"、"公共经济学"等多个文件夹，难以汇总
5. **忘记论文内容**：时间久了，只看文件名想不起论文具体讲什么

### 本系统的解决方案

- **首页文字索引**：自动提取 PDF 首页文字作为"详情"字段，即使文件名不包含关键词，也能通过论文内容检索
- **智能作者匹配**：搜索"周黎安"能找到"Li-An Zhou"、"Zhou Lian"等所有变体
- **标签自动生成**：根据文件夹结构自动打标签，搜索"行为"能找到"行为经济学"文件夹下的所有论文
- **模糊搜索**：输入拼音、部分词语都能匹配
- **PDF 预览**：点击即可预览，无需打开外部软件

## 功能特点

### 本地论文管理
- **智能文件夹扫描**：自动扫描论文目录，从 PDF 中提取标题、作者和首页文字
- **全文模糊搜索**：按标题、作者、关键词或首页内容搜索
- **中英文姓名匹配**：搜索"周黎安"、"Li'an Zhou"或"Zhou Lian"都能找到同一作者
- **基于标签的组织**：论文根据文件夹结构自动打标签
- **领域同义词匹配**：搜索"行为政经"可找到"行为经济学"或"政治经济学"的论文
- **位置优先排序**：关键词在论文首页出现越靠前，搜索结果排名越高
- **PDF 预览**：直接在应用中预览论文，可设置自动预览或手动加载
- **快速打开**：双击使用默认 PDF 阅读器（WPS、Adobe 等）打开论文

### 在线学术搜索
- **多源搜索**：跨 Semantic Scholar、CrossRef 和 arXiv 搜索
- **作者档案**：查看作者统计信息，包括论文数、引用数和 h 指数
- **期刊筛选**：按经济学顶刊（AER、QJE、ECMA、JPE、RES）、政治学期刊（AJPS、APSR、JOP）等筛选

## 运行方式

本系统提供两种运行方式，请根据需求选择：

### 方式一：浏览器模式（推荐新手使用）

使用系统浏览器访问，界面清晰，兼容性好。

**操作步骤：**

1. **确保已安装依赖**
   - 首次使用请先运行 `install.bat` 安装依赖

2. **启动服务器**
   - 双击运行 `start.bat`
   - 等待命令行窗口显示启动信息

3. **打开浏览器**
   - 当命令行显示 `Open browser: http://localhost:5000` 时，表示服务器已启动
   - 打开浏览器，在地址栏输入：`http://localhost:5000`
   - 按回车键访问

4. **使用系统**
   - 浏览器中将显示论文检索界面
   - 首次使用请先在"设置"中配置论文文件夹路径，然后点击"扫描文件夹"

5. **关闭系统**
   - 在命令行窗口按 `Ctrl + C` 停止服务器
   - 或直接关闭命令行窗口

**注意事项：**
- 服务器运行时请勿关闭命令行窗口
- 如需更换端口，可编辑 `app.py` 文件中的 `port` 参数

### 方式二：本地窗口模式（推荐日常使用）

使用独立桌面窗口运行，无需打开浏览器，体验更接近原生应用。

**操作步骤：**

1. **确保已安装依赖**
   - 首次使用请先运行 `install.bat` 安装依赖
   - 本模式需要 `pywebview` 库，安装脚本会自动安装

2. **启动应用**

   **方法 A：使用快捷方式（最简单）**
   - 双击桌面上的 "Paper Search" 快捷方式（由 `install.bat` 创建）

   **方法 B：使用批处理文件**
   - 双击运行 `PaperSearch.bat`
   - 应用窗口将自动打开

   **方法 C：命令行启动**
   ```cmd
   :: 激活虚拟环境（如有）
   venv\Scripts\activate

   :: 运行桌面应用
   python desktop_app.py
   ```

3. **使用系统**
   - 独立窗口将显示论文检索界面
   - 首次使用请先在"设置"中配置论文文件夹路径，然后点击"扫描文件夹"

4. **关闭系统**
   - 直接关闭窗口即可

**窗口模式的优势：**
- 独立窗口，不与浏览器标签混淆
- 启动更快，无需手动打开浏览器
- 后台服务自动管理，关闭窗口即停止

## 安装说明

### 方法一：一键安装（推荐）

1. **下载并解压**
   - 下载项目 ZIP 文件或克隆仓库
   - 解压到任意文件夹（如 `D:\PaperSearch`）

2. **运行安装程序**
   - 双击 `install.bat`
   - 等待安装完成（首次安装需要 2-3 分钟）

3. **选择运行方式**
   - 浏览器模式：双击 `start.bat`，然后打开 `http://localhost:5000`
   - 窗口模式：双击 `PaperSearch.bat` 或桌面快捷方式

### 方法二：手动安装

1. **安装 Python**（如果尚未安装）
   - 从 https://www.python.org/downloads/ 下载 Python 3.8+
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
   :: 浏览器模式
   python app.py

   :: 或窗口模式
   python desktop_app.py
   ```

## 首次使用设置

1. **设置论文目录**
   - 点击 ⚙️ 设置按钮
   - 输入论文文件夹路径（如 `E:\研究`）
   - 点击"保存"

2. **扫描论文**
   - 点击"扫描文件夹"按钮
   - 等待扫描完成（进度条会显示扫描进度）
   - 扫描完成后论文列表将显示出来

3. **开始搜索**
   - 在搜索框中输入作者、标题或关键词
   - 搜索结果会实时显示
   - 点击论文可预览，双击用默认软件打开

## 使用技巧

### 搜索技巧

- **按作者搜索**：输入作者姓名的任意形式
  - "周黎安" → 找到该作者的所有论文
  - "Li'an Zhou" → 相同结果
  - "Zhou, Lian" → 相同结果

- **按关键词搜索**：输入论文相关词语
  - "官员晋升" → 找到标题或首页包含该词的论文
  - "锦标赛" → 同上

- **按标签搜索**：输入研究领域
  - "行为" → 找到"行为经济学"文件夹下的所有论文
  - "政治" → 找到"政治经济学"、"企业政治联系"等标签的论文

### 预览设置

- 点击"设置"按钮
- 在"预览设置"中可选择：
  - **自动加载预览**：点击论文即显示 PDF 预览
  - **手动加载预览**：点击论文后需要再点"加载预览"按钮

## 常见问题

### "Python 未安装"
- 从 https://www.python.org/downloads/ 下载 Python
- 安装时必须勾选 "Add Python to PATH"

### 应用无法启动
- 尝试重新运行 `install.bat`
- 确保杀毒软件没有阻止 Python
- 检查命令行窗口是否有错误信息

### 论文不显示
- 检查论文目录路径是否正确
- 确保论文是 PDF 格式
- 点击"扫描文件夹"刷新

### 窗口模式无法启动
- 确保已安装 pywebview：`pip install pywebview`
- 尝试使用浏览器模式作为替代

### 搜索结果不准确
- 确保已完成扫描
- 尝试用不同的关键词搜索
- 检查"详情"字段是否包含相关内容

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite + FTS5 全文搜索
- **桌面窗口**：pywebview
- **前端**：原生 HTML/CSS/JavaScript
- **PDF 处理**：pypdf
- **中文处理**：pypinyin, jieba
- **在线搜索**：Semantic Scholar API, CrossRef API, arXiv API

## 项目结构

```
Paper-search-system-/
├── install.bat         # 一键安装脚本
├── start.bat           # 浏览器模式启动脚本
├── PaperSearch.bat     # 窗口模式启动脚本
├── desktop_app.py      # 桌面应用启动器
├── app.py              # Flask 后端服务
├── database.py         # SQLite 数据库
├── scanner.py          # PDF 扫描器
├── search.py           # 模糊搜索引擎
├── online_search.py    # 在线学术搜索
├── requirements.txt    # Python 依赖
├── static/             # CSS 和 JavaScript
├── templates/          # HTML 模板
└── data/               # 数据库文件（首次运行时创建）
```

## 许可证

MIT License

---

# English

## Why This System?

### Pain Points of Folder-Based Organization

If you organize papers using folders, you may encounter these problems:

1. **Difficult to search by author**: Want to find all papers by a specific author? You need to browse through folders one by one
2. **Difficult to search by keyword**: Want to find papers about "institutional economics"? The filename may not contain this keyword
3. **Inconsistent name formats**: The same author might appear as "Li-An Zhou", "Zhou, Lian", or "周黎安" - impossible to search uniformly
4. **Cross-folder search is tedious**: Papers may be scattered across multiple folders
5. **Forgetting paper content**: Over time, you can't remember what a paper is about just from the filename

### Our Solution

- **First-page text indexing**: Automatically extracts text from the first page of PDFs for content-based search
- **Smart author matching**: Search "周黎安" finds "Li-An Zhou", "Zhou Lian", and all variants
- **Auto-generated tags**: Tags are created based on folder structure
- **Fuzzy search**: Match by pinyin, partial words, or any variation
- **PDF preview**: Preview papers without opening external software

## Features

### Local Paper Management
- **Smart Folder Scanning**: Automatically scan directories and extract metadata from PDFs
- **Full-text Fuzzy Search**: Search by title, author, keywords, or first-page content
- **Chinese-English Name Matching**: Search "周黎安", "Li'an Zhou", or "Zhou Lian" - all find the same author
- **Tag-based Organization**: Papers are automatically tagged based on folder structure
- **Field Synonym Matching**: Search "行为政经" finds "行为经济学" or "政治经济学"
- **Position-based Ranking**: Keywords appearing earlier in the paper rank higher
- **PDF Preview**: Preview papers directly in the app, with auto or manual loading options
- **Quick Open**: Double-click to open with your default PDF reader (WPS, Adobe, etc.)

### Online Academic Search
- **Multi-source Search**: Search across Semantic Scholar, CrossRef, and arXiv
- **Author Profiles**: View author statistics including paper count, citations, and h-index
- **Journal Filtering**: Filter by top journals (AER, QJE, ECMA, JPE, RES, AJPS, APSR, JOP, etc.)

## Running the Application

This system offers two running modes:

### Mode 1: Browser Mode (Recommended for beginners)

Access via your system browser with a clean interface and good compatibility.

**Steps:**

1. **Ensure dependencies are installed**
   - Run `install.bat` first if this is your first time

2. **Start the server**
   - Double-click `start.bat`
   - Wait for the command window to show startup information

3. **Open browser**
   - When the command line shows `Open browser: http://localhost:5000`, the server is ready
   - Open your browser and enter: `http://localhost:5000`
   - Press Enter to access

4. **Use the system**
   - The paper search interface will appear
   - First-time users: configure the papers folder in "Settings", then click "Scan Papers"

5. **Close the system**
   - Press `Ctrl + C` in the command window to stop the server
   - Or simply close the command window

### Mode 2: Desktop Window Mode (Recommended for daily use)

Run in a standalone desktop window without opening a browser.

**Steps:**

1. **Ensure dependencies are installed**
   - Run `install.bat` first
   - This mode requires `pywebview`, which is installed automatically

2. **Launch the application**

   **Method A: Desktop Shortcut (Easiest)**
   - Double-click the "Paper Search" shortcut on your desktop (created by `install.bat`)

   **Method B: Batch File**
   - Double-click `PaperSearch.bat`
   - The application window will open automatically

   **Method C: Command Line**
   ```cmd
   :: Activate virtual environment (if exists)
   venv\Scripts\activate

   :: Run desktop application
   python desktop_app.py
   ```

3. **Use the system**
   - The paper search interface will appear in a standalone window
   - First-time users: configure the papers folder in "Settings", then click "Scan Papers"

4. **Close the system**
   - Simply close the window

**Advantages of Window Mode:**
- Standalone window, doesn't mix with browser tabs
- Faster startup, no need to manually open browser
- Background service is managed automatically

## Installation

### Method 1: One-Click Installation (Recommended)

1. **Download and Extract**
   - Download the project ZIP or clone the repository
   - Extract to any folder (e.g., `D:\PaperSearch`)

2. **Run the Installer**
   - Double-click `install.bat`
   - Wait for installation to complete (2-3 minutes for first time)

3. **Choose Running Mode**
   - Browser mode: Double-click `start.bat`, then open `http://localhost:5000`
   - Window mode: Double-click `PaperSearch.bat` or desktop shortcut

### Method 2: Manual Installation

1. **Install Python** (if not already installed)
   - Download Python 3.8+ from https://www.python.org/downloads/
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
   :: Browser mode
   python app.py

   :: Or window mode
   python desktop_app.py
   ```

## First-Time Setup

1. **Set Papers Directory**
   - Click the ⚙️ Settings button
   - Enter your papers folder path (e.g., `E:\研究`)
   - Click "Save"

2. **Scan Papers**
   - Click "Scan Papers" button
   - Wait for scanning to complete (progress bar shows status)
   - Your papers will appear in the list

3. **Start Searching**
   - Type author names, titles, or keywords in the search box
   - Results appear in real-time
   - Click to preview, double-click to open with default app

## Troubleshooting

### "Python is not installed"
- Download Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### App doesn't start
- Try running `install.bat` again
- Make sure antivirus isn't blocking Python
- Check the command window for error messages

### Papers not showing
- Check that the papers directory path is correct
- Make sure your papers are PDF files
- Click "Scan Papers" to refresh

### Window mode doesn't work
- Ensure pywebview is installed: `pip install pywebview`
- Try browser mode as an alternative

## License

MIT License
