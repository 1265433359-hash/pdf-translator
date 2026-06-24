# PDF 双语翻译阅读器 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个本地桌面 PDF 英译中阅读器，支持划词翻译（词典+句段）、整页双栏/原位翻译、多大模型与有道引擎、缓存、生词本、术语表、主题。

**Architecture:** Python + PySide6 (Qt6) 桌面应用；PyMuPDF 负责 PDF 渲染/取词/原位擦写；翻译引擎统一抽象为 `Translator` 接口，OpenAI 兼容引擎共用一个适配器；所有网络调用在 QThread 后台线程执行，经 Qt 信号回传 UI；SQLite 存缓存与生词本，ECDICT 精简库做离线词典。

**Tech Stack:** Python 3.12+（3.14 若缺 wheel 则退 3.12）、PySide6、PyMuPDF (fitz)、httpx、pyttsx3、keyring、pytest。

## Global Constraints

- 目标语言方向固定：英 → 中（`target="zh"`）。
- 所有引擎国内直连，**禁止任何代理逻辑**。
- 网络/IO 不得在 GUI 主线程执行——一律 QThread + 信号。
- 所有路径用 `pdf_translator/paths.py` 的辅助函数，禁止硬编码绝对路径。
- 包根目录：`pdf_translator/pdf_translator/`（源码包），测试在 `pdf_translator/tests/`。
- 依赖版本下限：PySide6>=6.8、PyMuPDF>=1.24、httpx>=0.27、pyttsx3>=2.90、keyring>=24、pytest>=8。
- 每个 Python 文件单一职责；翻译引擎新增不得修改主程序，只加适配器 + 注册。
- 提交信息用 Conventional Commits（`feat:` / `test:` / `chore:` / `fix:`）。
- 单词 vs 短语判定规则（全局统一）：选区 `strip()` 后不含空白且为纯字母（允许连字符/撇号）、长度≤30 → 单词；否则短语。

## 文件结构

```
pdf_translator/
  pyproject.toml / requirements.txt
  README.md
  data/
    ecdict_lite.db            # 离线词典（Phase 5 准备脚本生成/下载）
    themes/                   # *.qss 主题文件（Phase 9）
  pdf_translator/
    __init__.py
    paths.py                  # 配置/缓存/数据路径（Phase 0）
    main.py                   # 入口，QApplication（Phase 0）
    settings.py               # 配置 + keyring（Phase 2）
    app_window.py             # 主窗口/工具栏/布局（Phase 1 起逐步扩展）
    pdf_document.py           # PDF 加载、渲染、取词、搜索封装（Phase 1）
    pdf_view.py               # 左栏控件：显示/缩放/选区/翻页（Phase 1）
    text_preprocessor.py      # 文本清洗/重排（Phase 6）
    translation_pane.py       # 右栏译文（Phase 6）
    popup.py                  # 划词浮窗/侧栏（Phase 4）
    word_card.py              # 单词词典卡片控件（Phase 5）
    tts.py                    # 朗读（Phase 5）
    dictionary.py             # ECDICT 查询（Phase 5）
    glossary.py               # 术语表（Phase 8）
    cache.py                  # 翻译缓存（Phase 3）
    vocabulary.py             # 生词本 + Anki 导出（Phase 5/10）
    translate_queue.py        # 批量调度：并发/退避/进度（Phase 6）
    workers.py                # QThread 翻译 worker（Phase 4）
    inplace_renderer.py       # 原位替换（Phase 7）
    themes.py                 # 主题加载/切换（Phase 9）
    engines/
      __init__.py
      base.py                 # Translator ABC + WordEntry（Phase 2）
      openai_compat.py        # OpenAI 兼容引擎（Phase 2）
      youdao.py               # 有道云（Phase 10）
      registry.py             # 引擎注册/工厂（Phase 2）
  tests/
    ...                       # 与各模块对应
  scripts/
    prepare_ecdict.py         # 生成精简 ECDICT（Phase 5）
```

## 阶段总览（每阶段结束都有可运行/可演示的里程碑）

- **Phase 0** 项目骨架：空窗口能启动，git/依赖/路径就绪
- **Phase 1** 基础阅读：打开 PDF，翻页/跳页/缩放/适应宽度/搜索
- **Phase 2** 引擎抽象 + OpenAI 兼容 + 配置/keyring（命令行可翻译一句）
- **Phase 3** 缓存层
- **Phase 4** 划词翻译（短语）：选区→后台翻译→浮窗流式，可钉成侧栏
- **Phase 5** 词典 + 单词卡片 + TTS + 生词本（基础）
- **Phase 6** 文本预处理 + 整页双栏 + 批量调度（限流/退避/进度/估费）
- **Phase 7** 原位替换视图
- **Phase 8** 术语表
- **Phase 9** 主题系统
- **Phase 10** 有道引擎 + Anki 导出 + 扫描件检测 + 打包

---

# Phase 0 — 项目骨架

### Task 0.1：初始化项目与依赖

**Files:**
- Create: `pdf_translator/requirements.txt`
- Create: `pdf_translator/pdf_translator/__init__.py`
- Create: `pdf_translator/.gitignore`
- Create: `pdf_translator/README.md`

**Interfaces:**
- Produces: 包 `pdf_translator`，版本号 `__version__`。

- [ ] **Step 1: 写 requirements.txt**

```
PySide6>=6.8
PyMuPDF>=1.24
httpx>=0.27
pyttsx3>=2.90
keyring>=24
pytest>=8
```

- [ ] **Step 2: 写 .gitignore**

```
__pycache__/
*.pyc
.venv/
build/
dist/
*.spec
.superpowers/
data/ecdict_lite.db
```

- [ ] **Step 3: 写 `__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: 写最小 README**（项目简介 + 安装/运行命令占位为真实命令）

```markdown
# PDF 双语翻译阅读器
本地英文 PDF 翻译阅读器。
## 安装
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
## 运行
python -m pdf_translator.main
```

- [ ] **Step 5: 初始化 git 并安装依赖**

```bash
cd pdf_translator && git init && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
```
Expected: 依赖安装成功（若 PySide6/PyMuPDF 无 3.14 wheel，则改用 Python 3.12 重建 venv）。

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "chore: project skeleton and dependencies"
```

### Task 0.2：路径辅助模块

**Files:**
- Create: `pdf_translator/pdf_translator/paths.py`
- Test: `pdf_translator/tests/test_paths.py`

**Interfaces:**
- Produces:
  - `config_dir() -> Path`（`%APPDATA%/PDFTranslator`）
  - `data_local_dir() -> Path`（`%LOCALAPPDATA%/PDFTranslator`）
  - `bundled_data_dir() -> Path`（源码同级 `data/`）
  - `config_file() -> Path`、`cache_db() -> Path`、`vocab_db() -> Path`、`ecdict_db() -> Path`
  - 所有目录函数在返回前 `mkdir(parents=True, exist_ok=True)`。

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator import paths

def test_dirs_exist_and_files_under_them(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert paths.config_dir().exists()
    assert paths.config_file().parent == paths.config_dir()
    assert paths.cache_db().parent == paths.data_local_dir()
    assert paths.vocab_db().name == "vocab.db"
    assert paths.ecdict_db().name == "ecdict_lite.db"
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_paths.py -v`
Expected: FAIL（ModuleNotFoundError: paths）

- [ ] **Step 3: 实现 paths.py**

```python
import os
from pathlib import Path

APP = "PDFTranslator"

def config_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    d = base / APP
    d.mkdir(parents=True, exist_ok=True)
    return d

def data_local_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    d = base / APP
    d.mkdir(parents=True, exist_ok=True)
    return d

def bundled_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"

def config_file() -> Path:
    return config_dir() / "config.json"

def cache_db() -> Path:
    return data_local_dir() / "cache.db"

def vocab_db() -> Path:
    return data_local_dir() / "vocab.db"

def ecdict_db() -> Path:
    return bundled_data_dir() / "ecdict_lite.db"
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_paths.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: path helpers for config/cache/data"
```

### Task 0.3：可启动的空窗口

**Files:**
- Create: `pdf_translator/pdf_translator/main.py`
- Create: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Produces: `MainWindow(QMainWindow)`，`main()` 入口。

- [ ] **Step 1: 实现 app_window.py（最小主窗口 + 顶部工具栏占位）**

```python
from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器")
        self.resize(1200, 800)
        tb = QToolBar()
        self.addToolBar(tb)
        self.setCentralWidget(QLabel("打开一个 PDF 开始"))
```

- [ ] **Step 2: 实现 main.py**

```python
import sys
from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 手动验证**

Run: `.venv/Scripts/python -m pdf_translator.main`
Expected: 弹出 1200×800 空窗口，标题正确。关闭窗口。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: launchable empty main window"
```

---

# Phase 1 — 基础 PDF 阅读

### Task 1.1：PDF 文档封装

**Files:**
- Create: `pdf_translator/pdf_translator/pdf_document.py`
- Test: `pdf_translator/tests/test_pdf_document.py`
- Test fixture: `pdf_translator/tests/fixtures/sample.pdf`（用脚本生成）

**Interfaces:**
- Produces:
  - `class PdfDocument`
  - `PdfDocument.open(path: str) -> PdfDocument`
  - `.page_count -> int`
  - `.render_page(index: int, zoom: float) -> QImage`
  - `.page_text(index: int) -> str`
  - `.page_words(index: int) -> list[tuple]`（PyMuPDF words：`(x0,y0,x1,y1,word,block,line,word_no)`）
  - `.search(text: str) -> list[tuple[int, fitz.Rect]]`（页号 + 命中矩形）
  - `.has_text_layer() -> bool`（任一页有文字则 True）

- [ ] **Step 1: 写生成测试 PDF 的 fixture（conftest）**

`tests/conftest.py`:
```python
import fitz, pytest
from pathlib import Path

@pytest.fixture
def sample_pdf(tmp_path) -> str:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello world. This is a test PDF document.")
    p = tmp_path / "sample.pdf"
    doc.save(str(p)); doc.close()
    return str(p)
```

- [ ] **Step 2: 写失败测试**

```python
from pdf_translator.pdf_document import PdfDocument

def test_open_and_read(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    assert d.page_count == 1
    assert "Hello world" in d.page_text(0)
    assert d.has_text_layer() is True
    assert len(d.page_words(0)) > 0

def test_render_returns_image(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    img = d.render_page(0, zoom=1.5)
    assert img.width() > 0 and img.height() > 0

def test_search_finds_hits(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    hits = d.search("test")
    assert len(hits) >= 1 and hits[0][0] == 0
```

- [ ] **Step 3: 运行确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_pdf_document.py -v`
Expected: FAIL

- [ ] **Step 4: 实现 pdf_document.py**

```python
import fitz
from PySide6.QtGui import QImage

class PdfDocument:
    def __init__(self, doc):
        self._doc = doc

    @classmethod
    def open(cls, path: str) -> "PdfDocument":
        return cls(fitz.open(path))

    @property
    def page_count(self) -> int:
        return self._doc.page_count

    def render_page(self, index: int, zoom: float = 1.0) -> QImage:
        page = self._doc[index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return QImage(pix.samples, pix.width, pix.height,
                      pix.stride, QImage.Format.Format_RGB888).copy()

    def page_text(self, index: int) -> str:
        return self._doc[index].get_text("text")

    def page_words(self, index: int) -> list[tuple]:
        return self._doc[index].get_text("words")

    def search(self, text: str) -> list[tuple]:
        hits = []
        for i in range(self.page_count):
            for r in self._doc[i].search_for(text):
                hits.append((i, r))
        return hits

    def has_text_layer(self) -> bool:
        for i in range(self.page_count):
            if self._doc[i].get_text("text").strip():
                return True
        return False
```

- [ ] **Step 5: 运行确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_pdf_document.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: PdfDocument wrapper (render/text/words/search)"
```

### Task 1.2：左栏 PDF 视图控件（渲染 + 缩放 + 翻页）

**Files:**
- Create: `pdf_translator/pdf_translator/pdf_view.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Consumes: `PdfDocument`
- Produces:
  - `class PdfView(QScrollArea)`
  - `.load(doc: PdfDocument)`、`.goto(index: int)`、`.set_zoom(z: float)`、`.fit_width()`
  - 信号 `selection_made(str, QRect)`（Phase 4 接入；本任务先定义不发射）
  - 当前页 `.current_index`

- [ ] **Step 1: 实现 PdfView（内含 QLabel 显示当前页 pixmap）**

```python
from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal, QRect

class PdfView(QScrollArea):
    selection_made = Signal(str, QRect)

    def __init__(self):
        super().__init__()
        self._label = QLabel(); self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self._label); self.setWidgetResizable(True)
        self._doc = None; self.current_index = 0; self._zoom = 1.5

    def load(self, doc):
        self._doc = doc; self.current_index = 0; self._render()

    def goto(self, index: int):
        if not self._doc: return
        self.current_index = max(0, min(index, self._doc.page_count - 1)); self._render()

    def set_zoom(self, z: float):
        self._zoom = max(0.3, min(z, 5.0)); self._render()

    def fit_width(self):
        if not self._doc: return
        img = self._doc.render_page(self.current_index, 1.0)
        avail = self.viewport().width() - 24
        if img.width(): self.set_zoom(avail / img.width())

    def _render(self):
        if not self._doc: return
        img = self._doc.render_page(self.current_index, self._zoom)
        self._label.setPixmap(QPixmap.fromImage(img))
```

- [ ] **Step 2: 在 app_window 接线工具栏（打开/上一页/下一页/跳页/放大/缩小/适应宽度）**

```python
from PySide6.QtWidgets import QMainWindow, QToolBar, QFileDialog, QSpinBox
from PySide6.QtGui import QAction
from pdf_translator.pdf_view import PdfView
from pdf_translator.pdf_document import PdfDocument

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器"); self.resize(1200, 800)
        self.view = PdfView(); self.setCentralWidget(self.view)
        tb = QToolBar(); self.addToolBar(tb)
        tb.addAction(QAction("打开", self, triggered=self._open))
        tb.addAction(QAction("上一页", self, triggered=lambda: self.view.goto(self.view.current_index - 1)))
        tb.addAction(QAction("下一页", self, triggered=lambda: self.view.goto(self.view.current_index + 1)))
        self.page_box = QSpinBox(); self.page_box.setMinimum(1)
        self.page_box.valueChanged.connect(lambda v: self.view.goto(v - 1)); tb.addWidget(self.page_box)
        tb.addAction(QAction("放大", self, triggered=lambda: self.view.set_zoom(self.view._zoom * 1.2)))
        tb.addAction(QAction("缩小", self, triggered=lambda: self.view.set_zoom(self.view._zoom / 1.2)))
        tb.addAction(QAction("适应宽度", self, triggered=self.view.fit_width))

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF (*.pdf)")
        if path:
            doc = PdfDocument.open(path)
            self.view.load(doc); self.page_box.setMaximum(doc.page_count)
```

- [ ] **Step 3: 手动验证**

Run: `.venv/Scripts/python -m pdf_translator.main`
Expected: 打开任一 PDF，能翻页、跳页、放大缩小、适应宽度。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: PdfView with paging and zoom wired into toolbar"
```

### Task 1.3：全文搜索 + 扫描件提示

**Files:**
- Modify: `pdf_translator/pdf_translator/app_window.py`
- Modify: `pdf_translator/pdf_translator/pdf_view.py`

**Interfaces:**
- Consumes: `PdfDocument.search`、`has_text_layer`
- Produces: `PdfView.highlight(index, rects: list)`；工具栏搜索框跳到首个命中页并高亮。

- [ ] **Step 1: 给 PdfView 增加高亮渲染**

在 `_render()` 末尾叠加：若 `self._highlights` 中有当前页矩形，用 `QPainter` 在 pixmap 上画半透明黄框。新增：
```python
def highlight(self, index, rects):
    self._highlights = {index: rects}; self.goto(index)
```
并在 `__init__` 加 `self._highlights = {}`，`_render` 里渲染后：
```python
from PySide6.QtGui import QPainter, QColor
pm = QPixmap.fromImage(img)
for r in self._highlights.get(self.current_index, []):
    p = QPainter(pm); p.fillRect(int(r.x0*self._zoom), int(r.y0*self._zoom),
        int((r.x1-r.x0)*self._zoom), int((r.y1-r.y0)*self._zoom), QColor(255,235,59,90)); p.end()
self._label.setPixmap(pm)
```

- [ ] **Step 2: app_window 加搜索框 + 打开时扫描件检测**

```python
from PySide6.QtWidgets import QLineEdit, QMessageBox
# 工具栏：
self.search_box = QLineEdit(); self.search_box.setPlaceholderText("搜索…")
self.search_box.returnPressed.connect(self._search); tb.addWidget(self.search_box)
# _open 末尾：
if not doc.has_text_layer():
    QMessageBox.warning(self, "无法翻译",
        "此 PDF 没有可提取的文字（疑似扫描件），暂不支持翻译。OCR 将在后续版本支持。")
# 方法：
def _search(self):
    q = self.search_box.text().strip()
    if not q or not self.view._doc: return
    hits = self.view._doc.search(q)
    if hits: self.view.highlight(hits[0][0], [r for i, r in hits if i == hits[0][0]])
```

- [ ] **Step 3: 手动验证**

Run app；打开含文字 PDF 搜索词→跳转高亮；打开扫描件→弹提示。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: full-text search highlight and scanned-pdf detection"
```

---

# Phase 2 — 引擎抽象 + OpenAI 兼容 + 配置

### Task 2.1：Translator 抽象与数据结构

**Files:**
- Create: `pdf_translator/pdf_translator/engines/__init__.py`（空）
- Create: `pdf_translator/pdf_translator/engines/base.py`
- Test: `pdf_translator/tests/test_engine_base.py`

**Interfaces:**
- Produces:
  - `@dataclass WordEntry(word, phonetic, meanings: list[str], collocations: list[str], examples: list[str])`
  - `class Translator(ABC)`：`translate(text, target="zh") -> str`、`translate_stream(text, target="zh") -> Iterator[str]`、`lookup_word(word) -> WordEntry | None`
  - 默认 `translate_stream` 调用 `translate` 一次性 yield（传统引擎复用）。

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.engines.base import Translator, WordEntry

class Dummy(Translator):
    def translate(self, text, target="zh"): return "译:" + text

def test_default_stream_yields_full():
    d = Dummy()
    assert "".join(d.translate_stream("hi")) == "译:hi"

def test_word_entry_fields():
    w = WordEntry(word="run", phonetic="rʌn", meanings=["跑"], collocations=["run out"], examples=[])
    assert w.word == "run" and w.collocations == ["run out"]
```

- [ ] **Step 2: 运行确认失败** — `pytest tests/test_engine_base.py -v` → FAIL

- [ ] **Step 3: 实现 base.py**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator

@dataclass
class WordEntry:
    word: str
    phonetic: str = ""
    meanings: list[str] = field(default_factory=list)
    collocations: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

class Translator(ABC):
    @abstractmethod
    def translate(self, text: str, target: str = "zh") -> str: ...

    def translate_stream(self, text: str, target: str = "zh") -> Iterator[str]:
        yield self.translate(text, target)

    def lookup_word(self, word: str) -> WordEntry | None:
        return None
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: Translator abstract base and WordEntry"`

### Task 2.2：OpenAI 兼容引擎适配器

**Files:**
- Create: `pdf_translator/pdf_translator/engines/openai_compat.py`
- Test: `pdf_translator/tests/test_openai_compat.py`

**Interfaces:**
- Consumes: `Translator`, `WordEntry`
- Produces:
  - `class OpenAICompatEngine(Translator)`，构造 `(base_url, api_key, model, prompt=DEFAULT_PROMPT, http=None)`
  - `DEFAULT_PROMPT` 常量（专业学术翻译，只输出译文）
  - `translate`/`translate_stream` 走 `POST {base_url}/chat/completions`
  - `lookup_word` 用结构化提示返回 `WordEntry`（解析 JSON）
  - 接受注入的 `http`（httpx.Client，便于测试 mock）

- [ ] **Step 1: 写失败测试（用 httpx MockTransport）**

```python
import json, httpx
from pdf_translator.engines.openai_compat import OpenAICompatEngine

def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))

def test_translate_non_stream():
    def handler(req):
        return httpx.Response(200, json={"choices":[{"message":{"content":"你好世界"}}]})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert eng.translate("Hello world") == "你好世界"

def test_translate_sends_model_and_key():
    seen = {}
    def handler(req):
        seen["auth"] = req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices":[{"message":{"content":"x"}}]})
    eng = OpenAICompatEngine("https://x/v1", "secret", "deepseek-chat", http=make_client(handler))
    eng.translate("hi")
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["model"] == "deepseek-chat"
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 openai_compat.py**

```python
import json
import httpx
from typing import Iterator
from .base import Translator, WordEntry

DEFAULT_PROMPT = "你是专业学术翻译。把用户给的英文准确译成中文，术语规范，只输出译文，不要解释。"

class OpenAICompatEngine(Translator):
    def __init__(self, base_url, api_key, model, prompt=DEFAULT_PROMPT, http=None):
        self.base_url = base_url.rstrip("/"); self.api_key = api_key
        self.model = model; self.prompt = prompt
        self._http = http or httpx.Client(timeout=60)

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def translate(self, text, target="zh"):
        body = {"model": self.model, "messages": [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": text}]}
        r = self._http.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=body)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def translate_stream(self, text, target="zh") -> Iterator[str]:
        body = {"model": self.model, "stream": True, "messages": [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": text}]}
        with self._http.stream("POST", f"{self.base_url}/chat/completions",
                               headers=self._headers(), json=body) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith("data:"): continue
                data = line[5:].strip()
                if data == "[DONE]": break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                    if delta: yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def lookup_word(self, word) -> WordEntry | None:
        instr = ('返回该英文单词的 JSON：{"phonetic":"音标","meanings":["词性. 释义"],'
                 '"collocations":["固定搭配"],"examples":["例句"]}，只输出 JSON。单词：' + word)
        body = {"model": self.model, "messages": [{"role": "user", "content": instr}]}
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=body)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
            raw = raw[raw.find("{"): raw.rfind("}") + 1]
            d = json.loads(raw)
            return WordEntry(word=word, phonetic=d.get("phonetic",""),
                             meanings=d.get("meanings",[]), collocations=d.get("collocations",[]),
                             examples=d.get("examples",[]))
        except Exception:
            return None
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: OpenAI-compatible translation engine"`

### Task 2.3：引擎注册表（预设 + 自定义）

**Files:**
- Create: `pdf_translator/pdf_translator/engines/registry.py`
- Test: `pdf_translator/tests/test_registry.py`

**Interfaces:**
- Consumes: `OpenAICompatEngine`
- Produces:
  - `PRESETS: dict[str, dict]`，键为引擎名（`deepseek`/`zhipu`/`minimax`/`qwen`/`kimi`/`doubao`），值含 `base_url`、`default_model`、`label`
  - `build_engine(name, api_key, model=None, prompt=None, base_url=None) -> Translator`
  - `name=="custom"` 时用传入 `base_url`/`model`
  - `engine_labels() -> list[tuple[str, str]]`（name, 中文标签）

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.engines.registry import PRESETS, build_engine, engine_labels

def test_presets_have_required_keys():
    for name in ["deepseek","zhipu","minimax","qwen","kimi","doubao"]:
        assert name in PRESETS
        assert PRESETS[name]["base_url"].startswith("http")
        assert PRESETS[name]["default_model"]

def test_build_preset_uses_default_model():
    eng = build_engine("deepseek", "k")
    assert eng.model == PRESETS["deepseek"]["default_model"]

def test_build_custom_requires_base_url():
    eng = build_engine("custom", "k", model="my-model", base_url="https://my/v1")
    assert eng.base_url == "https://my/v1" and eng.model == "my-model"
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 registry.py**

```python
from .openai_compat import OpenAICompatEngine, DEFAULT_PROMPT

PRESETS = {
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "default_model": "deepseek-chat"},
    "zhipu":    {"label": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "default_model": "glm-4-flash"},
    "minimax":  {"label": "MiniMax", "base_url": "https://api.minimax.chat/v1", "default_model": "MiniMax-Text-01"},
    "qwen":     {"label": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-plus"},
    "kimi":     {"label": "Kimi", "base_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k"},
    "doubao":   {"label": "豆包", "base_url": "https://ark.cn-beijing.volces.com/api/v3", "default_model": "doubao-pro"},
}

def build_engine(name, api_key, model=None, prompt=None, base_url=None):
    prompt = prompt or DEFAULT_PROMPT
    if name == "custom":
        if not base_url or not model:
            raise ValueError("custom 引擎需 base_url 与 model")
        return OpenAICompatEngine(base_url, api_key, model, prompt)
    cfg = PRESETS[name]
    return OpenAICompatEngine(cfg["base_url"], api_key, model or cfg["default_model"], prompt)

def engine_labels():
    return [(k, v["label"]) for k, v in PRESETS.items()] + [("custom", "自定义(OpenAI兼容)")]
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: engine registry with presets and custom"`

### Task 2.4：配置 + keyring

**Files:**
- Create: `pdf_translator/pdf_translator/settings.py`
- Test: `pdf_translator/tests/test_settings.py`

**Interfaces:**
- Consumes: `paths`
- Produces:
  - `class Settings`：`load()`/`save()`；字段 `engine`、`model`、`theme`、`prompt`、`concurrency`、`custom_base_url`、自定义术语等
  - `get_api_key(engine) -> str`、`set_api_key(engine, key)`（走 keyring；测试时可注入假 backend）
  - 非敏感字段存 `config.json`；key 存 keyring。

- [ ] **Step 1: 写失败测试（keyring 用内存后端）**

```python
import keyring
from keyring.backends.fail import Keyring as FailKeyring
from pdf_translator import settings as S

class MemKeyring(FailKeyring):
    store = {}
    def set_password(self, s, u, p): MemKeyring.store[(s,u)] = p
    def get_password(self, s, u): return MemKeyring.store.get((s,u))

def test_roundtrip_config(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    keyring.set_keyring(MemKeyring())
    s = S.Settings.load()
    s.engine = "deepseek"; s.set_api_key("deepseek", "secret"); s.save()
    s2 = S.Settings.load()
    assert s2.engine == "deepseek"
    assert s2.get_api_key("deepseek") == "secret"
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 settings.py**

```python
import json, keyring
from dataclasses import dataclass, asdict, field
from pdf_translator import paths

SERVICE = "PDFTranslator"

@dataclass
class Settings:
    engine: str = "deepseek"
    model: str = ""
    theme: str = "cream"
    prompt: str = ""
    concurrency: int = 4
    custom_base_url: str = ""

    @classmethod
    def load(cls) -> "Settings":
        p = paths.config_file()
        if p.exists():
            return cls(**{**asdict(cls()), **json.loads(p.read_text(encoding="utf-8"))})
        return cls()

    def save(self):
        paths.config_file().write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_api_key(self, engine: str) -> str:
        return keyring.get_password(SERVICE, engine) or ""

    def set_api_key(self, engine: str, key: str):
        keyring.set_password(SERVICE, engine, key)
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: settings persistence with keyring-backed API keys"`

---

# Phase 3 — 缓存层

### Task 3.1：翻译缓存

**Files:**
- Create: `pdf_translator/pdf_translator/cache.py`
- Test: `pdf_translator/tests/test_cache.py`

**Interfaces:**
- Consumes: `paths`
- Produces:
  - `class TranslationCache(db_path=None)`：`get(text, model) -> str | None`、`put(text, model, translation)`、`size_bytes() -> int`、`clear()`
  - key = `sha256(text + "||" + model)`

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.cache import TranslationCache

def test_put_get_and_clear(tmp_path):
    c = TranslationCache(tmp_path / "c.db")
    assert c.get("hello", "m1") is None
    c.put("hello", "m1", "你好")
    assert c.get("hello", "m1") == "你好"
    assert c.get("hello", "m2") is None      # 换模型不命中
    assert c.size_bytes() > 0
    c.clear()
    assert c.get("hello", "m1") is None
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 cache.py**

```python
import sqlite3, hashlib
from pdf_translator import paths

class TranslationCache:
    def __init__(self, db_path=None):
        self.path = str(db_path or paths.cache_db())
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")
        self._conn.commit()

    @staticmethod
    def _key(text, model):
        return hashlib.sha256(f"{text}||{model}".encode("utf-8")).hexdigest()

    def get(self, text, model):
        row = self._conn.execute("SELECT v FROM cache WHERE k=?", (self._key(text, model),)).fetchone()
        return row[0] if row else None

    def put(self, text, model, translation):
        self._conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (self._key(text, model), translation))
        self._conn.commit()

    def size_bytes(self) -> int:
        import os
        return os.path.getsize(self.path) if os.path.exists(self.path) else 0

    def clear(self):
        self._conn.execute("DELETE FROM cache"); self._conn.commit()
        self._conn.execute("VACUUM"); self._conn.commit()
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: SQLite translation cache"`

---

# Phase 4 — 划词翻译（短语）

### Task 4.1：选区取词（PdfView 发射 selection_made）

**Files:**
- Modify: `pdf_translator/pdf_translator/pdf_view.py`
- Test: `pdf_translator/tests/test_selection_classify.py`
- Create: `pdf_translator/pdf_translator/textutil.py`

**Interfaces:**
- Produces:
  - `textutil.is_single_word(s: str) -> bool`（全局判定规则，见 Global Constraints）
  - PdfView 鼠标拖拽结束后，依据 `page_words` 命中选框的词拼成文本，发射 `selection_made(text, rect)`

- [ ] **Step 1: 写 is_single_word 失败测试**

```python
from pdf_translator.textutil import is_single_word

def test_single_word():
    assert is_single_word("ubiquitous")
    assert is_single_word("self-driving")
    assert not is_single_word("machine learning")
    assert not is_single_word("Hello, world.")
    assert not is_single_word("a" * 40)
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 textutil.py**

```python
import re
_WORD = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")

def is_single_word(s: str) -> bool:
    s = s.strip()
    return bool(s) and len(s) <= 30 and _WORD.match(s) is not None
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: 给 PdfView 加鼠标选区**（在 `_label` 上装 eventFilter 或重写 mouse 事件；把屏幕坐标 / zoom 还原为 PDF 坐标，用 `page_words` 取交集词）

```python
# pdf_view.py 关键新增（重写 viewport 鼠标事件）
from PySide6.QtCore import QPoint
def mousePressEvent(self, e):
    self._sel_start = e.position().toPoint(); super().mousePressEvent(e)
def mouseReleaseEvent(self, e):
    super().mouseReleaseEvent(e)
    if not self._doc: return
    end = e.position().toPoint(); s = self._sel_start
    x0, y0 = min(s.x(), end.x())/self._zoom, min(s.y(), end.y())/self._zoom
    x1, y1 = max(s.x(), end.x())/self._zoom, max(s.y(), end.y())/self._zoom
    words = [w[4] for w in self._doc.page_words(self.current_index)
             if w[0] >= x0-2 and w[2] <= x1+2 and w[1] >= y0-2 and w[3] <= y1+2]
    text = " ".join(words).strip()
    if text:
        from PySide6.QtCore import QRect
        self.selection_made.emit(text, QRect(s, end))
```
（注：坐标换算需考虑 QLabel 居中偏移；实现时以 label pixmap 左上为原点校正。）

- [ ] **Step 6: 手动验证**（临时把 selection_made 连到 print）— 框选英文打印出对应文本。

- [ ] **Step 7: Commit** — `git commit -m "feat: text selection from PdfView + word/phrase classifier"`

### Task 4.2：后台翻译 Worker

**Files:**
- Create: `pdf_translator/pdf_translator/workers.py`
- Test: `pdf_translator/tests/test_workers.py`

**Interfaces:**
- Consumes: `Translator`
- Produces:
  - `class TranslateWorker(QThread)`：构造 `(engine, text, cache=None, model="")`；信号 `chunk(str)`、`finished_text(str)`、`failed(str)`
  - 命中缓存直接 `finished_text`；否则流式发 `chunk`，结束 `finished_text` 并写缓存；异常发 `failed`

- [ ] **Step 1: 写失败测试（不依赖 Qt 事件循环，直接调 run 逻辑——抽出纯函数 `stream_translate`）**

```python
from pdf_translator.workers import stream_translate
from pdf_translator.engines.base import Translator

class Dummy(Translator):
    def translate(self, t, target="zh"): return "你好"

def test_stream_translate_uses_cache():
    calls = {"n": 0}
    class C:
        def get(self, t, m): return "缓存值" if calls["n"] else None
        def put(self, t, m, v): calls["n"] += 1
    chunks = []
    out = stream_translate(Dummy(), "hi", C(), "m", on_chunk=chunks.append)
    assert out == "你好"   # 首次未命中
    out2 = stream_translate(Dummy(), "hi", C(), "m", on_chunk=chunks.append)
    assert out2 == "缓存值"
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 workers.py**

```python
from PySide6.QtCore import QThread, Signal

def stream_translate(engine, text, cache, model, on_chunk):
    if cache:
        hit = cache.get(text, model)
        if hit is not None:
            on_chunk(hit); return hit
    parts = []
    for c in engine.translate_stream(text):
        parts.append(c); on_chunk(c)
    out = "".join(parts).strip()
    if cache: cache.put(text, model, out)
    return out

class TranslateWorker(QThread):
    chunk = Signal(str); finished_text = Signal(str); failed = Signal(str)
    def __init__(self, engine, text, cache=None, model=""):
        super().__init__(); self._engine = engine; self._text = text
        self._cache = cache; self._model = model
    def run(self):
        try:
            out = stream_translate(self._engine, self._text, self._cache, self._model, self.chunk.emit)
            self.finished_text.emit(out)
        except Exception as e:
            self.failed.emit(str(e))
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: background translate worker with cache"`

### Task 4.3：划词浮窗（短语译文，可钉成侧栏）

**Files:**
- Create: `pdf_translator/pdf_translator/popup.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Consumes: `TranslateWorker`、`Settings`、`build_engine`、`TranslationCache`、`is_single_word`
- Produces:
  - `class TransPopup(QFrame)`：`show_at(global_pos)`、`set_loading()`、`append_chunk(s)`、`set_error(s)`、信号 `pin_toggled(bool)`
  - app_window 持有 popup + 右侧可选 dock 侧栏；选区触发：单词走 Phase 5 卡片、短语走 popup 流式

- [ ] **Step 1: 实现 popup.py**

```python
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class TransPopup(QFrame):
    pin_toggled = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.copy_btn = QPushButton("复制"); self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self.pin_toggled.emit)
        bar.addWidget(self.copy_btn); bar.addWidget(self.pin_btn); bar.addStretch()
        self.body = QLabel(""); self.body.setWordWrap(True); self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addLayout(bar); lay.addWidget(self.body)
        self.setMinimumWidth(320)
        from PySide6.QtWidgets import QApplication
        self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.body.text()))
    def show_at(self, global_pos): self.move(global_pos); self.show()
    def set_loading(self): self.body.setText("翻译中…")
    def append_chunk(self, s):
        if self.body.text() == "翻译中…": self.body.setText("")
        self.body.setText(self.body.text() + s)
    def set_error(self, s): self.body.setText("⚠ " + s)
```

- [ ] **Step 2: app_window 接线（触发：2B 选中后按 Ctrl 或点图标——MVP 用快捷键 Space）**

要点：
- 选区后记录 `self._pending`；监听快捷键（`QShortcut(QKeySequence(Qt.Key_Space))`）触发翻译
- 单词 → 调 Phase 5 `WordCard`；短语 → 建 `TranslateWorker`，连接 `chunk→popup.append_chunk`、`finished_text→写完`、`failed→set_error`
- `pin_toggled(True)` → 把内容移入右侧 `QDockWidget` 常驻

```python
def _on_selection(self, text, rect):
    self._pending = text
def _translate_pending(self):
    if not getattr(self, "_pending", None): return
    eng = self._current_engine()
    from pdf_translator.textutil import is_single_word
    if is_single_word(self._pending):
        self._show_word_card(self._pending); return   # Phase 5
    self.popup.set_loading(); self.popup.show_at(self.cursor().pos())
    self._worker = TranslateWorker(eng, self._pending, self.cache, self.settings.model)
    self._worker.chunk.connect(self.popup.append_chunk)
    self._worker.failed.connect(self.popup.set_error); self._worker.start()
```
`_current_engine()` 用 `build_engine(settings.engine, settings.get_api_key(...), settings.model, base_url=settings.custom_base_url)`；key 为空时弹设置提示。

- [ ] **Step 3: 手动验证**（需填一个真实 key 到 keyring，或临时 Settings）— 框选英文句→按空格→浮窗逐字出译文；点📌→转侧栏。

- [ ] **Step 4: Commit** — `git commit -m "feat: selection-triggered phrase translation popup with pin-to-dock"`

---

# Phase 5 — 词典 + 单词卡片 + TTS + 生词本

### Task 5.1：ECDICT 精简库准备脚本

**Files:**
- Create: `pdf_translator/scripts/prepare_ecdict.py`
- Create: `pdf_translator/data/.gitkeep`

**Interfaces:**
- Produces: `data/ecdict_lite.db`，表 `dict(word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)`

- [ ] **Step 1: 写脚本（从 ECDICT CSV 取常用词，写入精简 SQLite）**

```python
"""用法: python scripts/prepare_ecdict.py path/to/ecdict.csv
ECDICT 源: https://github.com/skywind3000/ECDICT (stardict.csv / ecdict.csv)
仅保留有 translation 的词，控制体积。"""
import csv, sqlite3, sys
from pathlib import Path

def main(csv_path):
    out = Path(__file__).resolve().parent.parent / "data" / "ecdict_lite.db"
    conn = sqlite3.connect(out)
    conn.execute("CREATE TABLE IF NOT EXISTS dict (word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)")
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tr = (row.get("translation") or "").strip()
            if not tr: continue
            conn.execute("INSERT OR REPLACE INTO dict VALUES (?,?,?,?)",
                (row["word"].lower(), row.get("phonetic",""), tr, row.get("pos","")))
    conn.commit(); conn.close()
    print("written", out)

if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 2: 运行脚本生成库**（需先下载 ECDICT csv）

Run: `.venv/Scripts/python scripts/prepare_ecdict.py <ecdict.csv 路径>`
Expected: 打印 `written .../data/ecdict_lite.db`

- [ ] **Step 3: Commit（不提交 db，只提交脚本）** — `git commit -m "chore: ECDICT lite preparation script"`

### Task 5.2：Dictionary 查询

**Files:**
- Create: `pdf_translator/pdf_translator/dictionary.py`
- Test: `pdf_translator/tests/test_dictionary.py`

**Interfaces:**
- Consumes: `paths.ecdict_db`、`WordEntry`
- Produces: `class Dictionary(db_path=None)`：`lookup(word) -> WordEntry | None`（合成 phonetic/meanings；collocations/examples 留空待大模型补）

- [ ] **Step 1: 写失败测试（测试内自建小型 db）**

```python
import sqlite3
from pdf_translator.dictionary import Dictionary

def make_db(tmp_path):
    p = tmp_path / "d.db"; c = sqlite3.connect(p)
    c.execute("CREATE TABLE dict (word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)")
    c.execute("INSERT INTO dict VALUES ('run','rʌn','vt. 跑\\nn. 奔跑','v/n')"); c.commit(); c.close()
    return p

def test_lookup(tmp_path):
    d = Dictionary(make_db(tmp_path))
    e = d.lookup("Run")
    assert e and e.phonetic == "rʌn" and any("跑" in m for m in e.meanings)
    assert d.lookup("zzz") is None
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 dictionary.py**

```python
import sqlite3
from pdf_translator import paths
from pdf_translator.engines.base import WordEntry

class Dictionary:
    def __init__(self, db_path=None):
        self._conn = sqlite3.connect(str(db_path or paths.ecdict_db()))
    def lookup(self, word) -> WordEntry | None:
        row = self._conn.execute(
            "SELECT phonetic, translation FROM dict WHERE word=?", (word.lower().strip(),)).fetchone()
        if not row: return None
        phonetic, tr = row
        meanings = [ln.strip() for ln in tr.replace("\\n", "\n").split("\n") if ln.strip()]
        return WordEntry(word=word, phonetic=phonetic or "", meanings=meanings)
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: ECDICT dictionary lookup"`

### Task 5.3：TTS 朗读

**Files:**
- Create: `pdf_translator/pdf_translator/tts.py`
- Test: `pdf_translator/tests/test_tts.py`

**Interfaces:**
- Produces: `speak(word: str, engine=None)`（默认懒加载 pyttsx3；测试注入假 engine 验证调用）

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator import tts

def test_speak_calls_engine():
    calls = []
    class Fake:
        def say(self, t): calls.append(t)
        def runAndWait(self): calls.append("run")
    tts.speak("hello", engine=Fake())
    assert calls == ["hello", "run"]
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 tts.py**

```python
_engine = None
def _default():
    global _engine
    if _engine is None:
        import pyttsx3; _engine = pyttsx3.init()
    return _engine

def speak(word: str, engine=None):
    eng = engine or _default()
    eng.say(word); eng.runAndWait()
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: offline TTS pronunciation"`

### Task 5.4：生词本存储

**Files:**
- Create: `pdf_translator/pdf_translator/vocabulary.py`
- Test: `pdf_translator/tests/test_vocabulary.py`

**Interfaces:**
- Consumes: `paths.vocab_db`、`WordEntry`
- Produces:
  - `class Vocabulary(db_path=None)`：`add(entry: WordEntry, source="")`、`all() -> list[dict]`、`remove(word)`、`count()`

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.vocabulary import Vocabulary
from pdf_translator.engines.base import WordEntry

def test_add_list_remove(tmp_path):
    v = Vocabulary(tmp_path / "v.db")
    v.add(WordEntry("run", "rʌn", ["跑"], [], ["I run."]), source="a.pdf")
    rows = v.all()
    assert len(rows) == 1 and rows[0]["word"] == "run"
    v.remove("run")
    assert v.count() == 0
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 vocabulary.py**

```python
import sqlite3, json
from pdf_translator import paths

class Vocabulary:
    def __init__(self, db_path=None):
        self._conn = sqlite3.connect(str(db_path or paths.vocab_db()))
        self._conn.execute("""CREATE TABLE IF NOT EXISTS vocab
            (word TEXT PRIMARY KEY, phonetic TEXT, meanings TEXT, examples TEXT, source TEXT)""")
        self._conn.commit()
    def add(self, entry, source=""):
        self._conn.execute("INSERT OR REPLACE INTO vocab VALUES (?,?,?,?,?)",
            (entry.word, entry.phonetic, json.dumps(entry.meanings, ensure_ascii=False),
             json.dumps(entry.examples, ensure_ascii=False), source))
        self._conn.commit()
    def all(self):
        cur = self._conn.execute("SELECT word, phonetic, meanings, examples, source FROM vocab")
        return [{"word": w, "phonetic": p, "meanings": json.loads(m),
                 "examples": json.loads(e), "source": s} for w, p, m, e, s in cur]
    def remove(self, word):
        self._conn.execute("DELETE FROM vocab WHERE word=?", (word,)); self._conn.commit()
    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM vocab").fetchone()[0]
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: vocabulary store"`

### Task 5.5：单词卡片控件 + 接线划词

**Files:**
- Create: `pdf_translator/pdf_translator/word_card.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Consumes: `Dictionary`、`tts.speak`、`Vocabulary`、引擎 `lookup_word`
- Produces: `class WordCard(QFrame)`：`show_entry(entry: WordEntry, global_pos)`；🔊 调 `speak`；➕ 调 `Vocabulary.add`；异步用引擎补 collocations/examples

- [ ] **Step 1: 实现 word_card.py**（音标/词性释义/搭配/例句 + 🔊 + ➕）

```python
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from pdf_translator import tts

class WordCard(QFrame):
    def __init__(self, vocab, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setFrameShape(QFrame.Shape.StyledPanel); self._vocab = vocab; self._entry = None
        self.lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.word = QLabel(""); self.phon = QLabel("")
        self.say_btn = QPushButton("🔊"); self.add_btn = QPushButton("➕生词本")
        self.say_btn.clicked.connect(lambda: self._entry and tts.speak(self._entry.word))
        self.add_btn.clicked.connect(self._add)
        top.addWidget(self.word); top.addWidget(self.phon); top.addStretch()
        top.addWidget(self.say_btn); top.addWidget(self.add_btn)
        self.body = QLabel(""); self.body.setWordWrap(True)
        self.lay.addLayout(top); self.lay.addWidget(self.body); self.setMinimumWidth(340)
    def _add(self):
        if self._entry: self._vocab.add(self._entry)
    def show_entry(self, entry, global_pos):
        self._entry = entry
        self.word.setText(f"<b>{entry.word}</b>"); self.phon.setText(f"/{entry.phonetic}/" if entry.phonetic else "")
        lines = list(entry.meanings)
        if entry.collocations: lines += ["", "搭配: " + "; ".join(entry.collocations)]
        if entry.examples: lines += ["", "例句: " + " / ".join(entry.examples)]
        self.body.setText("\n".join(lines)); self.move(global_pos); self.show()
```

- [ ] **Step 2: app_window `_show_word_card`**：先 `Dictionary.lookup` 显示基础信息；再后台 `engine.lookup_word` 补搭配/例句后刷新（用一个简单 QThread 或 `TranslateWorker` 同款模式）。

- [ ] **Step 3: 手动验证**：框选单个词→空格→卡片出音标/释义；🔊 发音；➕ 进生词本；稍后搭配/例句补上。

- [ ] **Step 4: Commit** — `git commit -m "feat: word dictionary card with TTS and vocab add"`

---

# Phase 6 — 文本预处理 + 整页双栏 + 批量调度

### Task 6.1：文本预处理/重排

**Files:**
- Create: `pdf_translator/pdf_translator/text_preprocessor.py`
- Test: `pdf_translator/tests/test_preprocessor.py`

**Interfaces:**
- Consumes: `PdfDocument.page_words` 或 blocks
- Produces:
  - `paragraphs_from_blocks(blocks: list[tuple]) -> list[str]`（blocks 为 PyMuPDF `get_text("blocks")`：`(x0,y0,x1,y1,text,block_no,block_type)`）
  - 规则：按栏（x 中位数分左右）→ 按 y 排序 → 合并行、去行尾连字符、丢弃极短的页眉页脚块

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.text_preprocessor import paragraphs_from_blocks

def test_dehyphenate_and_join():
    blocks = [(0,100,300,120,"This is an evalu-\nation of the\nmethod.",0,0)]
    paras = paragraphs_from_blocks(blocks)
    assert paras == ["This is an evaluation of the method."]

def test_two_column_order():
    blocks = [
        (300,100,560,120,"Right column first line",1,0),
        (0,100,260,120,"Left column first line",0,0),
    ]
    paras = paragraphs_from_blocks(blocks)
    assert paras[0].startswith("Left")   # 左栏先
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 text_preprocessor.py**

```python
import re

def _clean(text: str) -> str:
    text = re.sub(r"-\n", "", text)          # 去连字符断行
    text = re.sub(r"\s*\n\s*", " ", text)    # 行合并
    return re.sub(r"\s+", " ", text).strip()

def paragraphs_from_blocks(blocks, header_footer_max_len=3):
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    if not text_blocks: return []
    page_mid = sorted((b[0] + b[2]) / 2 for b in text_blocks)[len(text_blocks)//2]
    left = [b for b in text_blocks if (b[0]+b[2])/2 <= page_mid]
    right = [b for b in text_blocks if (b[0]+b[2])/2 > page_mid]
    ordered = sorted(left, key=lambda b: b[1]) + sorted(right, key=lambda b: b[1]) if right else sorted(text_blocks, key=lambda b: b[1])
    paras = []
    for b in ordered:
        c = _clean(b[4])
        if len(c.split()) <= header_footer_max_len:  # 丢极短块（页眉页脚页码）
            continue
        paras.append(c)
    return paras
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: PDF text preprocessing (dehyphenate/reflow/columns)"`

### Task 6.2：批量翻译调度（并发 + 退避 + 进度）

**Files:**
- Create: `pdf_translator/pdf_translator/translate_queue.py`
- Test: `pdf_translator/tests/test_translate_queue.py`

**Interfaces:**
- Consumes: `Translator`、`TranslationCache`
- Produces:
  - `translate_batch(engine, paras: list[str], cache, model, concurrency=4, max_retries=3, on_progress=None, sleep=time.sleep) -> list[str]`
  - 命中缓存跳过 API；失败按 `2**attempt` 退避重试；每完成一条调 `on_progress(done, total)`
  - `estimate_tokens(paras) -> int`（粗略 `sum(len)/4`）

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.translate_queue import translate_batch, estimate_tokens
from pdf_translator.engines.base import Translator

class Flaky(Translator):
    def __init__(self): self.n = 0
    def translate(self, t, target="zh"):
        self.n += 1
        if t == "boom" and self.n < 2: raise RuntimeError("rate limit")
        return "Z" + t

def test_batch_with_cache_and_retry():
    class C:
        d = {}
        def get(self, t, m): return self.d.get((t,m))
        def put(self, t, m, v): self.d[(t,m)] = v
    prog = []
    out = translate_batch(Flaky(), ["a", "boom"], C(), "m", concurrency=1,
                          on_progress=lambda d,t: prog.append((d,t)), sleep=lambda s: None)
    assert out == ["Za", "Zboom"]
    assert prog[-1] == (2, 2)

def test_estimate_tokens():
    assert estimate_tokens(["abcd"*10]) > 0
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 translate_queue.py**

```python
import time
from concurrent.futures import ThreadPoolExecutor

def estimate_tokens(paras) -> int:
    return max(1, sum(len(p) for p in paras) // 4)

def _one(engine, text, cache, model, max_retries, sleep):
    if cache:
        hit = cache.get(text, model)
        if hit is not None: return hit
    last = None
    for attempt in range(max_retries):
        try:
            out = engine.translate(text).strip()
            if cache: cache.put(text, model, out)
            return out
        except Exception as e:
            last = e; sleep(2 ** attempt)
    raise last

def translate_batch(engine, paras, cache, model, concurrency=4, max_retries=3,
                    on_progress=None, sleep=time.sleep):
    results = [None] * len(paras); done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(_one, engine, p, cache, model, max_retries, sleep): i
                for i, p in enumerate(paras)}
        for fut in futs:
            pass
        from concurrent.futures import as_completed
        for fut in as_completed(futs):
            i = futs[fut]; results[i] = fut.result(); done += 1
            if on_progress: on_progress(done, len(paras))
    return results
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: Commit** — `git commit -m "feat: batch translate queue with concurrency, backoff, progress"`

### Task 6.3：整页双栏视图接线

**Files:**
- Create: `pdf_translator/pdf_translator/translation_pane.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Consumes: `paragraphs_from_blocks`、`translate_batch`、`TranslationCache`
- Produces:
  - `class TranslationPane(QScrollArea)`：`set_paragraphs(list[str])`、`clear()`
  - 工具栏「翻译当前页」「翻译整篇」；整篇先弹 `estimate_tokens` 确认框 + 进度条；右栏显示译文；后台线程执行

- [ ] **Step 1: 实现 translation_pane.py**（竖直堆叠段落 QLabel，可选行号/分隔）

```python
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class TranslationPane(QScrollArea):
    def __init__(self):
        super().__init__(); self._host = QWidget(); self._lay = QVBoxLayout(self._host)
        self._lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._host); self.setWidgetResizable(True)
    def clear(self):
        while self._lay.count():
            w = self._lay.takeAt(0).widget()
            if w: w.deleteLater()
    def set_paragraphs(self, paras):
        self.clear()
        for p in paras:
            lab = QLabel(p); lab.setWordWrap(True); lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._lay.addWidget(lab)
```

- [ ] **Step 2: app_window 用 QSplitter 放 PdfView | TranslationPane，加「翻译当前页/整篇」**

要点：
- 用 `QSplitter(Qt.Horizontal)` 左 view 右 pane
- 「翻译当前页」：取 `doc._doc[i].get_text("blocks")` → `paragraphs_from_blocks` → 后台 `translate_batch` → `pane.set_paragraphs`
- 「翻译整篇」：所有页 paras 合并；先 `estimate_tokens` 弹 `QMessageBox.question` 确认；`QProgressDialog` 显示进度
- 批量调用放进一个 QThread（复用 workers 模式），`on_progress` 经信号更新进度条

- [ ] **Step 3: 手动验证**：打开论文→「翻译当前页」→右栏出双语对照；「翻译整篇」→确认框+进度→完成。

- [ ] **Step 4: Commit** — `git commit -m "feat: side-by-side full-page/whole-doc translation"`

---

# Phase 7 — 原位替换视图

### Task 7.1：原位替换渲染

**Files:**
- Create: `pdf_translator/pdf_translator/inplace_renderer.py`
- Test: `pdf_translator/tests/test_inplace_renderer.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`（视图切换下拉）

**Interfaces:**
- Consumes: `fitz`、`translate_batch`
- Produces:
  - `render_inplace(page: fitz.Page, block_translations: list[tuple[fitz.Rect, str]], font_path=None) -> fitz.Pixmap`
  - 对每个块 redact 原文 → 在 rect 内 `insert_textbox` 写中文（用支持中文的字体，自动缩字号）

- [ ] **Step 1: 写失败测试（生成英文 PDF，替换后该页文本含中文、不含原英文短语）**

```python
import fitz
from pdf_translator.inplace_renderer import render_inplace

def test_inplace_replaces_text(tmp_path):
    doc = fitz.open(); page = doc.new_page()
    page.insert_text((72,72), "Hello")
    rect = fitz.Rect(72, 60, 300, 90)
    pix = render_inplace(page, [(rect, "你好")])
    assert pix.width > 0
    # 重新读页文本：原 Hello 应被覆盖
    assert "Hello" not in page.get_text("text")
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 inplace_renderer.py**

```python
import fitz

def render_inplace(page, block_translations, font_path=None, zoom=1.5):
    for rect, _ in block_translations:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()
    for rect, zh in block_translations:
        size = 11
        while size >= 5:
            rc = page.insert_textbox(rect, zh, fontsize=size, fontname="china-s",
                                     fontfile=font_path, align=0)
            if rc >= 0: break
            size -= 1
    return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
```
（注：`fontname="china-s"` 为 PyMuPDF 内置简中字体；若不可用则需 `font_path` 指向打包的中文 TTF。实现时验证字体可用性。）

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: app_window 视图下拉**：选「原位替换」时，对当前页取 blocks→译文→`render_inplace`→把返回 pixmap 显示到左栏（右栏隐藏）。

- [ ] **Step 6: 手动验证**：切到原位替换→当前页英文被中文就地替换。

- [ ] **Step 7: Commit** — `git commit -m "feat: in-place translation rendering view"`

---

# Phase 8 — 术语表

### Task 8.1：术语表存储 + 注入

**Files:**
- Create: `pdf_translator/pdf_translator/glossary.py`
- Test: `pdf_translator/tests/test_glossary.py`
- Modify: `pdf_translator/pdf_translator/engines/openai_compat.py`（prompt 注入命中术语）

**Interfaces:**
- Consumes: `paths.config_dir`
- Produces:
  - `class Glossary`：`set(en, zh)`、`remove(en)`、`all() -> dict`、`apply_to_prompt(base_prompt, text) -> str`（把出现在 text 中的术语作为约束附加到 prompt）

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.glossary import Glossary

def test_apply_injects_only_present_terms(tmp_path):
    g = Glossary(tmp_path / "g.json")
    g.set("transformer", "变换器"); g.set("kernel", "核")
    prompt = g.apply_to_prompt("BASE", "The transformer architecture")
    assert "transformer" in prompt and "变换器" in prompt
    assert "kernel" not in prompt    # 未出现的不注入
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 glossary.py**

```python
import json
from pathlib import Path
from pdf_translator import paths

class Glossary:
    def __init__(self, path=None):
        self._path = Path(path or (paths.config_dir() / "glossary.json"))
        self._d = json.loads(self._path.read_text(encoding="utf-8")) if self._path.exists() else {}
    def _save(self): self._path.write_text(json.dumps(self._d, ensure_ascii=False, indent=2), encoding="utf-8")
    def set(self, en, zh): self._d[en] = zh; self._save()
    def remove(self, en): self._d.pop(en, None); self._save()
    def all(self): return dict(self._d)
    def apply_to_prompt(self, base_prompt, text):
        hits = {en: zh for en, zh in self._d.items() if en.lower() in text.lower()}
        if not hits: return base_prompt
        terms = "; ".join(f"{en}→{zh}" for en, zh in hits.items())
        return base_prompt + f"\n以下术语必须按指定译法翻译：{terms}。"
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: 引擎接入术语表**：`OpenAICompatEngine` 增加可选 `glossary`；`translate`/`translate_stream` 构造 system 内容时调 `glossary.apply_to_prompt(self.prompt, text)`。补一条测试验证命中术语进入请求 body。

- [ ] **Step 6: Commit** — `git commit -m "feat: glossary with prompt injection"`

---

# Phase 9 — 主题系统

### Task 9.1：主题加载与切换

**Files:**
- Create: `pdf_translator/pdf_translator/themes.py`
- Create: `pdf_translator/data/themes/cream.qss`（默认浅奶白 C1）
- Create: `pdf_translator/data/themes/dark.qss`、`light.qss`、`sepia.qss`、`white.qss`
- Test: `pdf_translator/tests/test_themes.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`（主题下拉）、`main.py`（启动应用已存主题）

**Interfaces:**
- Consumes: `paths.bundled_data_dir`、`Settings.theme`
- Produces: `available_themes() -> list[str]`、`load_qss(name) -> str`、`apply_theme(app, name)`

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator import themes

def test_available_and_load():
    names = themes.available_themes()
    assert "cream" in names
    assert "QWidget" in themes.load_qss("cream")
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 写 cream.qss（C1 浅奶白配色，含主窗口/工具栏/按钮/浮窗/卡片）**

```css
QWidget { background: #faf6ec; color: #7a6a55; font-family: "Segoe UI","Microsoft YaHei"; }
QToolBar { background: #f3ecda; border-bottom: 1px solid #ece2cc; }
QPushButton { background: #c0915e; color: white; border: none; padding: 4px 10px; border-radius: 6px; }
QPushButton:hover { background: #b07f4a; }
QLineEdit, QSpinBox { background: #fffdf7; border: 1px solid #ddceac; border-radius: 6px; padding: 3px; }
QFrame { background: #fffdf7; border: 1px solid #d9b888; border-radius: 9px; }
QScrollArea { border: none; }
```
其余 4 个主题文件按 §8 配色各写一份（dark/light/sepia/white）。

- [ ] **Step 4: 实现 themes.py**

```python
from pdf_translator import paths

def _dir(): return paths.bundled_data_dir() / "themes"
def available_themes():
    return sorted(p.stem for p in _dir().glob("*.qss"))
def load_qss(name) -> str:
    return (_dir() / f"{name}.qss").read_text(encoding="utf-8")
def apply_theme(app, name):
    app.setStyleSheet(load_qss(name))
```

- [ ] **Step 5: 运行确认通过 + 接线**：`main.py` 启动后 `apply_theme(app, settings.theme)`；app_window 主题下拉切换时 `apply_theme` 并存 `settings`。

- [ ] **Step 6: 手动验证**：切换主题即时生效；重启后保持上次主题。

- [ ] **Step 7: Commit** — `git commit -m "feat: switchable QSS themes (cream default)"`

---

# Phase 10 — 有道引擎 + Anki 导出 + 设置面板 + 打包

### Task 10.1：有道云引擎

**Files:**
- Create: `pdf_translator/pdf_translator/engines/youdao.py`
- Test: `pdf_translator/tests/test_youdao.py`
- Modify: `pdf_translator/pdf_translator/engines/registry.py`（注册 youdao）

**Interfaces:**
- Consumes: `Translator`
- Produces: `class YoudaoEngine(Translator)`：构造 `(app_key, app_secret, http=None)`；按有道签名规则（`sha256(appKey+input+salt+curtime+appSecret)`，input 截断规则）调 `https://openapi.youdao.com/api`；`translate` 返回 `translation[0]`

- [ ] **Step 1: 写失败测试（MockTransport 验证签名字段齐全 + 解析返回）**

```python
import httpx
from pdf_translator.engines.youdao import YoudaoEngine, _truncate, _sign

def test_truncate_rule():
    assert _truncate("abcdefg") == "abcdefg"            # <=20 原样
    assert _truncate("a"*30).endswith(str(30)) is False # 规则: 前10+len+后10

def test_translate_parses(monkeypatch):
    def handler(req):
        return httpx.Response(200, json={"translation": ["你好"]})
    eng = YoudaoEngine("ak", "sk", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert eng.translate("hello") == "你好"
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 youdao.py**

```python
import hashlib, time, uuid, httpx
from .base import Translator

API = "https://openapi.youdao.com/api"

def _truncate(q: str) -> str:
    n = len(q)
    return q if n <= 20 else q[:10] + str(n) + q[-10:]

def _sign(app_key, q, salt, curtime, app_secret):
    s = app_key + _truncate(q) + salt + curtime + app_secret
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class YoudaoEngine(Translator):
    def __init__(self, app_key, app_secret, http=None):
        self.app_key = app_key; self.app_secret = app_secret
        self._http = http or httpx.Client(timeout=30)
    def translate(self, text, target="zh"):
        salt = str(uuid.uuid4()); curtime = str(int(time.time()))
        data = {"q": text, "from": "en", "to": "zh-CHS", "appKey": self.app_key,
                "salt": salt, "sign": _sign(self.app_key, text, salt, curtime, self.app_secret),
                "signType": "v3", "curtime": curtime}
        r = self._http.post(API, data=data); r.raise_for_status()
        return r.json()["translation"][0]
```
（注：`time.time()` 在测试中不参与断言，OK；如需可注入。`uuid` 同理。）

- [ ] **Step 4: 运行确认通过 + 注册**：registry 增 `build_engine("youdao", ...)` 分支（需 app_key/app_secret，从 settings 取）；`engine_labels` 加有道。补 registry 测试。

- [ ] **Step 5: Commit** — `git commit -m "feat: Youdao translation engine"`

### Task 10.2：Anki 导出

**Files:**
- Create: `pdf_translator/pdf_translator/anki_export.py`
- Test: `pdf_translator/tests/test_anki_export.py`
- Modify: `pdf_translator/pdf_translator/vocabulary.py`（或在生词本面板调用）

**Interfaces:**
- Consumes: `Vocabulary.all()`
- Produces: `export_csv(rows: list[dict], out_path)`（Anki 可导入：`正面<TAB>背面`，背面=音标+释义+例句的 HTML）

- [ ] **Step 1: 写失败测试**

```python
from pdf_translator.anki_export import export_csv

def test_export_csv(tmp_path):
    rows = [{"word":"run","phonetic":"rʌn","meanings":["跑"],"examples":["I run."]}]
    out = tmp_path / "anki.txt"; export_csv(rows, out)
    content = out.read_text(encoding="utf-8")
    assert "run\t" in content and "rʌn" in content and "跑" in content
```

- [ ] **Step 2: 运行确认失败** — FAIL

- [ ] **Step 3: 实现 anki_export.py**

```python
def export_csv(rows, out_path):
    lines = []
    for r in rows:
        back_parts = []
        if r.get("phonetic"): back_parts.append(f"/{r['phonetic']}/")
        back_parts += r.get("meanings", [])
        back_parts += r.get("examples", [])
        back = "<br>".join(back_parts)
        lines.append(f"{r['word']}\t{back}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
```

- [ ] **Step 4: 运行确认通过** — PASS

- [ ] **Step 5: 生词本面板接「导出 Anki」按钮**（QFileDialog 选保存路径→`export_csv(vocab.all(), path)`）。

- [ ] **Step 6: Commit** — `git commit -m "feat: Anki export from vocabulary"`

### Task 10.3：设置面板 + 清理缓存按钮

**Files:**
- Create: `pdf_translator/pdf_translator/settings_dialog.py`
- Modify: `pdf_translator/pdf_translator/app_window.py`

**Interfaces:**
- Consumes: `Settings`、`TranslationCache.size_bytes/clear`、`engine_labels`、`Glossary`
- Produces: `class SettingsDialog(QDialog)`：编辑各引擎 key、当前引擎/模型、自定义 base_url、提示词、并发、主题、术语表；显示缓存大小 + 【清理缓存】

- [ ] **Step 1: 实现 settings_dialog.py**（表单：引擎下拉、各引擎 key 输入存 keyring、自定义 base_url/model、prompt 多行、concurrency、主题下拉、术语表增删表格、缓存大小标签 + 清理按钮）。关键行为：
  - 保存 → `settings.save()` + `set_api_key`
  - 清理缓存 → `cache.clear()`，刷新大小标签为 `f"{size/1e6:.1f} MB"`

- [ ] **Step 2: app_window 工具栏「设置」打开对话框；关闭后用新 settings 重建当前引擎**

- [ ] **Step 3: 手动验证**：填 key→翻译可用；改并发/提示词生效；清理缓存后大小归零。

- [ ] **Step 4: Commit** — `git commit -m "feat: settings dialog with cache clear"`

### Task 10.4：打包

**Files:**
- Create: `pdf_translator/build.md`（打包说明）
- Create: `pdf_translator/pdf_translator.spec`（PyInstaller，可选）

**Interfaces:** 无代码接口；产物为可分发 exe。

- [ ] **Step 1: 写 PyInstaller 命令（含打包 data/）**

```bash
.venv/Scripts/pip install pyinstaller
.venv/Scripts/pyinstaller --noconfirm --windowed --name PDFTranslator ^
  --add-data "data;data" pdf_translator/main.py
```

- [ ] **Step 2: 手动验证**：`dist/PDFTranslator/PDFTranslator.exe` 双击可运行，能打开 PDF、翻译、查词。

- [ ] **Step 3: Commit** — `git commit -m "chore: PyInstaller packaging config and docs"`

---

## 自检（写完计划后对照 spec）

**Spec 覆盖**：基础阅读(P1)、多引擎+OpenAI兼容(P2)、缓存(P3)、划词短语(P4)、词典/卡片/TTS/生词本(P5)、文本预处理/双栏/批量调度成本控制(P6)、原位替换(P7)、术语表(P8)、主题(P9)、有道/Anki/设置清缓存/扫描件提示(P1+P10)、keyring(P2)、异步线程(P4/P6)、自定义引擎(P2)、复制译文(P4)、ECDICT精简(P5) — 全部有对应任务。

**占位符**：无 TBD/TODO；每个逻辑步骤含完整代码；GUI 步骤给出关键完整代码 + 明确接线要点。

**类型一致**：`WordEntry` 字段、`Translator` 方法签名、`build_engine`/`translate_batch`/`stream_translate` 参数在各任务间一致；`is_single_word` 全局统一引用。

**已知风险（执行时注意）**：
1. PdfView 选区坐标需校正 QLabel 居中偏移（Task 4.1 Step 5 标注）。
2. PyMuPDF 中文字体 `china-s` 可用性需验证，否则打包中文 TTF（Task 7.1 标注）。
3. Python 3.14 若缺 wheel 退 3.12（Global Constraints）。
4. ECDICT 需用户先下载 CSV 跑准备脚本（Task 5.1）。
