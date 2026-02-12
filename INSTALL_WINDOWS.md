# Windows 安装指南

## PDF 生成支持

A股金融分析智能体现在支持**多种PDF生成引擎**，无需手动安装GTK3运行时。系统会自动检测并选择可用的最佳方案：

### PDF 引擎优先级

1. **WeasyPrint** (需要GTK3运行时) - 最高质量
2. **pdfkit** (需要wkhtmltopdf) - 中等质量
3. **xhtml2pdf** (纯Python) - 基本质量
4. **fpdf2** (纯Python) - 简单文本PDF
5. **HTML + 浏览器打印** (无需额外安装) - 最终备选方案

### 推荐安装方案

#### ✅ 方案A：安装xhtml2pdf (推荐，最简单)
```cmd
# 纯Python实现，无需外部依赖，安装即用
pip install xhtml2pdf
```
**优点**: 安装简单，无需配置，跨平台兼容性好  
**质量**: 良好，支持中文和CSS样式

#### 方案B：安装WeasyPrint + GTK3 (最佳质量)
```cmd
# 1. 安装GTK3运行时 (从 https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer 下载)
# 2. 然后安装WeasyPrint
pip install weasyprint
```
**优点**: PDF质量最高，CSS支持最好  
**缺点**: 需要安装GTK3运行时，配置较复杂

#### 方案C：安装pdfkit + wkhtmltopdf (中等质量)
```cmd
# 1. 下载wkhtmltopdf并添加到PATH (https://wkhtmltopdf.org/downloads.html)
# 2. 安装pdfkit
pip install pdfkit
```
**优点**: 无需GTK3，PDF质量较好  
**缺点**: 需要安装wkhtmltopdf并配置PATH

#### 方案D：不安装任何PDF库 (使用浏览器打印)
- 无需安装任何额外库
- 程序会自动生成HTML文件
- 打开HTML文件，按Ctrl+P选择"保存为PDF"

> **注意**: 程序会自动检测可用引擎并选择最佳方案。推荐安装 **xhtml2pdf**，它安装最简单且功能完善。

## 完整的安装步骤

### 1. 安装 Python 3.10+
- 从 https://www.python.org/downloads/ 下载 Python 3.10+
- 安装时勾选 "Add Python to PATH"

### 2. 设置项目

```cmd
cd d:\code\stock
.\start_agent.bat
```

或者手动设置：

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖（使用清华镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果 WeasyPrint 安装失败，可以跳过：
pip install smolagents akshare markdown2 pyyaml python-dotenv pandas requests openai
```

### 3. 配置 API 密钥

1. 打开 `config/.env` 文件
2. 将 `OPENROUTER_API_KEY=your_key_here` 替换为您的 OpenRouter API 密钥
3. 保存文件

### 4. 运行程序

```cmd
python main.py
```

或者直接双击 `start_agent.bat`

## 故障排除

### 问题 1：WeasyPrint 导入错误

**错误信息：**
```
WeasyPrint could not import some external libraries...
OSError: cannot load library 'libgobject-2.0-0': error 0x7e
```

**解决方案：**
- 按照上面的 "解决方案 1" 安装 GTK3 运行时
- 或者使用 HTML 替代方案（程序会自动处理）

### 问题 2：Python 找不到模块

**错误信息：**
```
ModuleNotFoundError: No module named 'akshare'
```

**解决方案：**
- 确保虚拟环境已激活：`venv\Scripts\activate`
- 重新安装依赖：`pip install -r requirements.txt`

### 问题 3：API 密钥错误

**错误信息：**
```
ValueError: OPENROUTER_API_KEY 环境变量未设置
```

**解决方案：**
- 确保 `config/.env` 文件中有正确的 API 密钥
- 或运行程序时按照提示输入 API 密钥

### 问题 4：股票数据获取失败

**错误信息：**
```
获取市值信息失败: ...
```

**解决方案：**
- 检查网络连接
- 确保股票代码正确（6位数字，如 600519）
- Akshare 可能需要网络访问权限

## 使用 HTML 替代方案

如果不想安装 GTK3 运行时，程序会自动使用 HTML 替代方案：

1. 程序会生成 `.html` 文件
2. 同时生成 `.md`（Markdown）文件
3. 打开 `.html` 文件，按 `Ctrl+P` 选择 "打印为 PDF"

## 测试安装

运行测试脚本检查环境：

```cmd
python test_basic.py
```

如果一切正常，您将看到：
```
✓ tools.akshare_tools 导入成功
✓ agent.analyst 导入成功
✓ utils.pdf_generator 导入成功
✓ yaml 导入成功
✓ markdown2 导入成功
✓ akshare 导入成功
✓ smolagents 导入成功
```

## 开始分析股票

1. 运行 `.\start_agent.bat` 或 `python main.py`
2. 输入 OpenRouter API 密钥（如果没有配置）
3. 输入股票代码（如 600519）
4. 等待分析完成
5. 查看生成的报告（PDF 或 HTML）

## 报告位置

生成的报告保存在 `reports/` 目录下：
- `Report_股票代码_日期.pdf` - PDF 格式（如果 WeasyPrint 可用）
- `Report_股票代码_日期.html` - HTML 格式（如果 WeasyPrint 不可用）
- `Report_股票代码_日期.md` - Markdown 原始格式
