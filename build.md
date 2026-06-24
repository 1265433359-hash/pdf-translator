# 打包说明 (Building PDFTranslator)

将本应用打包成 Windows 可分发的 `.exe`（使用 [PyInstaller](https://pyinstaller.org/)）。

> 仅支持 Windows 打包产物。命令在 Git Bash / PowerShell / cmd 下均可，注意 `--add-data`
> 的分隔符在 Windows 上是分号 `;`（Linux/macOS 为冒号 `:`）。

---

## 1. 前置准备

### 1.1 激活虚拟环境并安装依赖

```bash
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pip install pyinstaller
```

### 1.2 准备离线词典 (可选但推荐)

应用通过 `pdf_translator/paths.py` 的 `bundled_data_dir()` 读取 `data/ecdict_lite.db`
作为离线英汉词典。该文件 **未纳入版本控制**（见 `.gitignore`），构建前若不存在需自行生成：

```bash
# 1. 从 https://github.com/skywind3000/ECDICT 下载 ecdict.csv (或 stardict.csv)
# 2. 生成精简词典到 data/ecdict_lite.db
.venv/Scripts/python scripts/prepare_ecdict.py path/to/ecdict.csv
```

- 若 **不生成** `ecdict_lite.db`，应用仍可正常打包与运行，查词时会自动回退到
  LLM（在线大模型）翻译，只是没有本地离线词典。
- `data/themes/*.qss`（界面主题）已随仓库提供，无需额外准备。

### 1.3 中文字体

原位替换译文用到的 `china-s` 字体是 **PyMuPDF 内置** 的，无需额外打包任何 TTF 字体文件。

---

## 2. 打包

### 方式 A：使用 spec 文件（推荐）

仓库提供了 `pdf_translator.spec`，已配置好 `data/` 打包、窗口模式、隐藏导入：

```bash
.venv/Scripts/pyinstaller --noconfirm pdf_translator.spec
```

### 方式 B：直接用命令行

```bash
.venv/Scripts/pyinstaller --noconfirm --windowed --name PDFTranslator \
  --add-data "data;data" \
  --hidden-import pyttsx3.drivers.sapi5 \
  --hidden-import keyring.backends.Windows \
  pdf_translator/main.py
```

说明：

- `--windowed`：GUI 应用，运行时不弹出控制台黑窗。
- `--add-data "data;data"`：把仓库根目录的 `data/` 整个打进包内。运行时
  `bundled_data_dir()` 会在解包目录 `_MEIPASS/data` 下找到主题与词典，路径自动对齐。
- `--hidden-import`：`pyttsx3` 的 Windows 朗读驱动 (`sapi5`) 和 `keyring` 的 Windows
  凭据后端在运行时动态加载，PyInstaller 静态分析发现不了，需显式声明（spec 文件已含）。

---

## 3. 产物与运行

打包完成后，产物位于：

```
dist/PDFTranslator/
├── PDFTranslator.exe        ← 双击运行
└── _internal/               ← 依赖、data/ 等随附资源
```

运行：直接双击 `dist/PDFTranslator/PDFTranslator.exe`，或：

```bash
./dist/PDFTranslator/PDFTranslator.exe
```

分发时把整个 `dist/PDFTranslator/` 文件夹打包发送（不要只拷贝 .exe）。

---

## 4. 手动验收 (打包后自测)

1. 双击 `PDFTranslator.exe` 能正常启动主窗口。
2. 打开一个 PDF，能正常显示分页。
3. 触发翻译，译文面板正常返回（需先在「设置」里配置好 API Key）。
4. 划词查词：若已打包 `ecdict_lite.db`，应显示离线释义；否则回退在线翻译。
5. 切换主题（light / dark / sepia / cream / white）界面样式生效。

---

## 5. 常见问题

- **启动即闪退 / 报缺模块**：多半是某个运行时动态加载的后端没被打进去，按
  `--hidden-import` 方式补充对应模块名后重新打包。
- **找不到主题或词典**：确认打包时带了 `--add-data "data;data"`（或用 spec 文件）。
- **Python 版本**：若 3.14 下某些依赖缺少 wheel，回退到 3.12 重建 `.venv` 再打包。
- **体积较大属正常**：PySide6 + PyMuPDF 体积本身较大，可考虑 UPX 压缩（spec 已开启 `upx=True`，需系统装有 UPX）。
