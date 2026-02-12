# Windows 安装指南

## 解决 WeasyPrint 依赖问题

在 Windows 上运行 A股金融分析智能体时，可能会遇到 WeasyPrint 依赖问题。这是因为 WeasyPrint 需要 GTK3 运行时库。

### 解决方案 1：安装 GTK3 运行时（推荐）

1. **下载并安装 GTK3 运行时**
   - 访问 https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
   - 下载最新版本的 GTK3 运行时安装程序
   - 运行安装程序，按照提示安装

2. **或者使用以下命令安装（如果已安装 Chocolatey）：**
   ```cmd
   choco install gtk3
   ```

3. **或者手动安装：**
   - 从 https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases 下载 `gtk3-runtime-*.exe`
   - 运行安装程序
   - 确保安装目录添加到系统 PATH 环境变量

### 解决方案 2：使用 HTML 替代方案（无需额外安装）

程序已经内置了优雅降级功能。如果 WeasyPrint 无法工作，程序会自动生成 HTML 格式的报告，您可以：

1. 打开生成的 `.html` 文件
2. 按 `Ctrl + P` 打开打印对话框
3. 选择 "Microsoft Print to PDF" 或 "另存为 PDF"
4. 点击打印/保存生成 PDF 文件

### 解决方案 3：安装 WeasyPrint 的 Windows 版本

```cmd
# 激活虚拟环境后运行
pip install weasyprint
# WeasyPrint 会自动尝试安装必要的依赖
```

如果遇到错误，尝试：

```cmd
# 先安装必要的依赖
pip install cairocffi
pip install cffi
pip install weasyprint
```

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
