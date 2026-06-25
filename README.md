<div align="center">

<img src="data/icon.png" width="96" alt="logo"/>

# PDF 双语翻译阅读器

**一款本地的英文 PDF 阅读 + 翻译工具,接入你自己的大模型 / 有道 API,边读边译、划词查词、做标注、攒生词。**

类似「知云文献翻译」,但翻译引擎完全由你掌控,数据本地、引擎直连、无需代理。

</div>

---

## ✨ 功能特性

### 📖 PDF 阅读器
- 全宽渲染、清晰锐利(HiDPI 自适应),滚轮翻页、**Ctrl + 滚轮缩放**、适应宽度
- 全文搜索高亮、**PDF 目录(书签)导航**侧栏一键跳转
- **续读**:每篇自动记住上次读到的页;记住窗口大小
- 自动识别扫描件(无文字层)并提示

### 🖱️ 划词翻译
- **文本流选择**:从起点词拖到终点词,整段按阅读顺序选中(像浏览器一样),实时蓝色选区反馈,自动去除首尾标点
- 结果显示在**跟随选区的浮窗**里(自适应大小、智能避让屏幕边缘),点别处即关闭
- **单词** → 词典卡片:音标、词性释义、固定搭配、例句、🔊 朗读、➕ 加入生词本
- **短语/句子** → 多来源翻译

### 🌐 多翻译来源,各自独立开关
- **大模型**:DeepSeek、智谱 GLM、通义千问、Kimi、豆包、MiniMax,以及任意 **OpenAI 兼容**接口(自定义 base_url);可**实时拉取**账号可用的模型版本
- **有道词典**:传统翻译接口,整句秒出
- **离线词典**:内置完整 [ECDICT](https://github.com/skywind3000/ECDICT)(约 340 万词条),单词查词零延迟、不耗 token
- 两段式:有道/词典先秒出,大模型流式精翻随后;翻译缓存避免重复消耗;429 限流自动退避

### ✏️ 标注(写入 PDF)
- 高亮、删除线,直接写进 PDF 文件;支持撤销;关闭前提示保存

### 📒 生词本 + 复习
- 划词一键收藏;**已收录的词在任何文章里都显示「✓ 已加入」**
- 「不记得」按钮后台计数,用于按**遗忘度**复习
- 生词本面板:浏览 / 搜索 / 删除 / 朗读 / **导出 Anki**;排序支持 遗忘度(默认)/ 首字母 / 收录时间

### 🎨 界面
- 左侧导航栏 + 简洁顶部阅读栏;**首页**(打开 + 最近文件)
- 6 套主题:现代中性(默认)、浅奶白护眼、深褐护眼、纯白、浅色、暗色
- 术语表(自定义术语固定译法,注入提示词保证全文一致)

---

## 🚀 安装与运行

需要 **Python 3.12+**(已在 3.14 验证)。

```bash
git clone <本仓库地址>
cd pdf-translator
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 准备离线词典(可选但推荐)
内置离线词典体积较大,不随仓库分发,需自行生成一次:

```bash
# 1. 下载 ECDICT 的 stardict.csv(完整版,最全)或 ecdict.csv(精简版)
#    https://github.com/skywind3000/ECDICT
# 2. 生成本地词典库 data/ecdict_lite.db
python scripts/prepare_ecdict.py path/to/stardict.csv
```
> 不生成也能用,单词查询会自动回退到大模型/有道。

### 运行
```bash
python -m pdf_translator.main
```

---

## ⚙️ 配置 API

打开应用 → 左侧「设置」：

- **大模型引擎**:选一个(如 DeepSeek / 智谱)→ 填对应 **API Key** → 「模型版本」点「刷新」拉取或手填(翻译建议用 `glm-4-flash`、`deepseek-chat` 等轻量快速的型号)
- **有道词典**(可选,秒出快译):填**应用ID(appKey)**和**应用密钥(appSecret)**
  - ⚠️ 是有道智云控制台的「应用ID + 应用密钥」,不是「API Keys」那串
- **翻译来源**:勾选「使用大模型」「使用有道词典」(可同时开,各自独立)
- 点「测试连接」验证;API Key 存系统凭据管理器(keyring),不落明文

---

## 📦 打包成 exe

详见 [build.md](build.md):

```bash
pip install pyinstaller
pyinstaller pdf_translator.spec
# 产物在 dist/PDFTranslator/
```

---

## 🛠️ 技术栈

Python · PySide6 (Qt6) · PyMuPDF · httpx · SQLite · pyttsx3 · keyring · pytest

所有网络/翻译均在后台线程,界面不卡。72 个单元/集成测试。

---

## 🙏 致谢

- [ECDICT](https://github.com/skywind3000/ECDICT) — 开源英汉词典数据
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF 渲染与解析
- [PySide6](https://doc.qt.io/qtforpython/) — 界面框架

## 📄 许可

MIT License — 个人项目,欢迎自用与改造。
