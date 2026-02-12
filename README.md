# A股金融分析智能体 (A-Share Financial Analyst Agent)

## 项目概述

这是一个本地化的A股金融分析智能体，专为Windows平台设计。通过一个简单的批处理文件，用户可以自动设置Python虚拟环境、通过Akshare获取股票数据、使用LLM（OpenRouter）进行分析，并生成专业的PDF报告。系统集成了完整的配置管理系统，支持雅虎财经接口数据提取和行业比较分析。

## 功能特点

- **一站式解决方案**: 只需运行一个批处理文件即可完成所有设置
- **自动环境管理**: 自动创建和管理Python虚拟环境
- **数据获取**: 通过Akshare获取实时股票数据、财务指标和价格历史
- **AI分析**: 使用OpenRouter API进行智能金融分析
- **PDF报告生成**: 自动生成包含中文支持的PDF报告
- **用户友好**: 交互式CLI界面，引导用户完成分析过程
- **配置管理系统**: 完整的YAML配置，支持模型设定、代理设置、重试机制
- **数据源冗余**: Akshare主数据源 + 雅虎财经备用数据源
- **智能重试机制**: 网络异常时自动重试，提高数据获取成功率
- **行业均值比较**: 基于akshare接口的行业估值和成长性对比分析
- **PDF多引擎支持**: 支持xhtml2pdf(推荐，纯Python)、WeasyPrint(高质量)、pdfkit、fpdf2等多种引擎，自动选择最优方案

### 新增高级功能

1. **上市日期提取**: 从雅虎财经接口提取`firstTradeDateMilliseconds`并转换为datetime对象
2. **重试机制**: 雅虎财经接口支持最多5次重试，智能处理网络异常和数据缺失
3. **经营范围数据整合**: 当akshare接口缺失经营范围时，自动从雅虎财经接口获取`longBusinessSummary`
4. **行业均值分析**: 使用akshare的行业比较接口获取行业平均估值和成长性指标
5. **PDF多引擎支持**: 支持WeasyPrint、pdfkit、xhtml2pdf、fpdf2多种PDF生成引擎，自动选择可用方案，无需手动安装GTK3运行时
6. **配置分离**: 所有配置分离到YAML文件，支持动态调整：
   - 模型API配置（OpenRouter/其他提供商）
   - 雅虎财经代理设置
   - 重试参数配置
   - 超时设置

## 系统要求

- Windows 10/11
- Python 3.10+ (已安装并添加到PATH)
- 网络连接（用于获取股票数据和API调用）

## 快速开始

### 1. 获取OpenRouter API密钥

1. 访问 [OpenRouter网站](https://openrouter.ai/)
2. 注册账号并获取API密钥
3. 免费额度足够进行测试

### 2. 设置API密钥

编辑 `config/.env` 文件，将 `your_key_here` 替换为你的OpenRouter API密钥：

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 运行智能体

双击 `start_agent.bat` 或在命令行中运行：

```cmd
.\start_agent.bat
```

首次运行时会：
1. 检查Python安装
2. 创建虚拟环境（如果不存在）
3. 安装所有依赖包
4. 启动分析程序

### 4. 分析股票

按照程序提示输入A股股票代码（如 `600519` 代表贵州茅台），系统将自动：
1. 获取股票数据（包含行业均值分析）
2. 进行AI分析
3. 生成PDF报告

## 项目结构

```
project_root/
├── config/
│   ├── config_manager.py  # 配置管理核心模块
│   ├── settings.yaml      # 完整系统配置
│   └── .env               # API密钥存储（环境变量）
├── tools/
│   ├── __init__.py
│   └── akshare_tools.py   # Akshare数据工具封装 + 雅虎财经备用接口
├── agent/
│   ├── __init__.py
│   └── analyst.py         # 智能体逻辑（集成配置管理）
├── utils/
│   ├── __init__.py
│   ├── pdf_generator.py   # PDF生成器
│   └── pdf_generator_fallback.py  # PDF备用生成器
├── main.py                # 主程序入口
├── start_agent.bat        # Windows启动脚本
├── start_agent.sh         # Linux/Mac启动脚本
├── requirements.txt       # Python依赖
├── develop.md             # 开发文档
├── INSTALL_WINDOWS.md     # Windows安装说明
├── test_yfinance_fields.py  # 雅虎财经字段测试工具
└── README.md              # 项目说明文档
```

## 核心组件说明

### 1. Akshare工具 (tools/akshare_tools.py)

包含6个核心数据获取工具：

- `get_market_valuation()`: 获取实时市值、PE、PB信息 + 行业均值数据
- `get_company_info()`: 获取公司基本信息 + 上市日期 + 经营范围
- `get_financial_indicators()`: 获取财务指标（ROE、毛利率等）
- `get_price_history()`: 获取最近30天价格历史
- `yfinance_with_retry()`: 带重试机制的雅虎财经数据获取
- `get_industry_averages()`: 获取行业均值数据（估值和成长性指标）

#### 数据源策略：
- **主数据源**: Akshare（中国A股数据最完整）
- **备用数据源**: 雅虎财经（用于补充缺失字段：上市日期、经营范围）
- **智能回退**: Akshare失败时自动切换到雅虎财经
- **重试机制**: 网络异常时最多重试5次

### 2. 配置管理系统 (config/config_manager.py)

统一管理所有系统配置：
- **三层配置结构**：默认值 → 配置文件 → 环境变量
- **配置验证**：自动检查必要配置项
- **热重载支持**：修改配置文件无需重启程序
- **向后兼容**：保持对现有环境变量的支持

核心配置项：
- 模型API设置（OpenRouter/其他提供商）
- 雅虎财经代理设置（支持HTTP/HTTPS代理）
- 重试参数（最大重试次数、延迟时间）
- 超时设置（akshare接口超时）

### 3. 分析智能体 (agent/analyst.py)

使用smolagents框架构建，包含：
- OpenAI兼容的OpenRouter API集成
- 中文优化的系统提示词
- 多步骤分析流程
- 集成配置管理，动态加载模型设置

### 4. PDF生成器 (utils/pdf_generator.py)

智能PDF报告生成系统，支持多引擎自动选择：
- **智能引擎检测**: 自动检测xhtml2pdf(推荐)、WeasyPrint、pdfkit、fpdf2等PDF生成库
- **优先级选择**: 按引擎质量和可用性自动选择最优方案，无需用户干预
- **推荐方案**: 默认使用xhtml2pdf（纯Python，无需外部依赖，安装即用）
- **优雅降级**: 所有引擎均不可用时自动生成HTML报告，支持浏览器打印为PDF
- **中文支持**: 包含中文字体配置（Microsoft YaHei），确保中文显示正常
- **备份文件**: 同时生成HTML和Markdown格式备份，确保数据不丢失

## 配置说明

### 完整配置结构 (config/settings.yaml)

```yaml
version: "1.0"

model:
  provider: "openrouter"            # 模型提供商
  base_url: "https://openrouter.ai/api/v1"
  model_name: "deepseek/deepseek-chat"  # 可替换为其他模型
  api_key_env: "OPENROUTER_API_KEY"     # API密钥环境变量名
  parameters:
    max_tokens: 4000
    temperature: 0.1
    top_p: 0.9

yfinance:
  proxy:
    enabled: false                     # 是否启用代理
    http_proxy: "http://127.0.0.1:10808"
    https_proxy: "http://127.0.0.1:10808"
  retry:
    max_retries: 5                     # 最大重试次数
    retry_delay: 1.0                   # 重试延迟（秒）

akshare:
  timeout: 30                          # 接口超时（秒）
  retry_count: 3                       # 重试次数
```

### 支持的模型

支持OpenRouter上的任何模型，如：
- `deepseek/deepseek-chat`（默认）
- `meta-llama/llama-3.3-70b-instruct`
- `google/gemma-2-9b-it`
- `qwen/qwen2.5-32b-instruct`

### 环境变量配置 (config/.env)

```
OPENROUTER_API_KEY=your_key_here
# 可选：雅虎财经代理设置（优先使用配置文件）
YFINANCE_PROXY=http://127.0.0.1:10808
```

## 新功能详细说明

### 1. 上市日期提取

系统从雅虎财经接口的`firstTradeDateMilliseconds`字段提取上市日期，自动转换为Python datetime对象：

```python
# 实现逻辑
if 'firstTradeDateMilliseconds' in info:
    ms = info['firstTradeDateMilliseconds']
    dt = datetime.datetime.fromtimestamp(ms / 1000)
    listing_date = dt.strftime('%Y-%m-%d')
```

### 2. 智能重试机制

雅虎财经接口内置5次重试，智能区分网络异常和数据缺失：

```python
def yfinance_with_retry(yf_symbol: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            # 检查数据有效性
            if len(info) <= 1 and 'trailingPegRatio' in info:
                continue  # 数据不完整，重试
            return ticker, info
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
```

### 3. 经营范围数据整合

当akshare接口缺失经营范围时，自动从雅虎财经获取：

```python
# 尝试从yfinance获取经营范围
try:
    ticker, yf_info = yfinance_with_retry(yf_symbol, max_retries=3)
    if ticker is not None:
        business_scope = yf_info.get('longBusinessSummary', '')
```

### 4. 行业均值分析

使用akshare的专业接口进行行业对比：

```python
# 获取成长性比较数据
growth_df = ak.stock_zh_growth_comparison_em(symbol=akshare_symbol)
# 获取估值比较数据
valuation_df = ak.stock_zh_valuation_comparison_em(symbol=akshare_symbol)
# 提取"行业平均"行数据
avg_row = growth_df[growth_df['简称'] == '行业平均']
```

### 5. 配置管理系统

```python
from config.config_manager import get_config_manager

config = get_config_manager()
model_config = config.get_model_config()
yfinance_config = config.get_yfinance_config()

# 应用代理设置
config.apply_yfinance_settings()
```

## 依赖安装

项目依赖在 `requirements.txt` 中：

```txt
smolagents>=0.6.0      # AI代理框架
akshare>=1.12.0         # 金融数据
yfinance>=0.2.0         # 雅虎财经数据（备用数据源）
markdown2>=2.4.0        # Markdown转换
weasyprint>=60.0        # PDF生成
pyyaml>=6.0            # YAML配置
python-dotenv>=1.0.0   # 环境变量
pandas>=2.0.0          # 数据处理
requests>=2.31.0       # HTTP请求
openai>=1.0.0          # OpenAI兼容客户端
```

## 使用示例

### 基本使用

1. 运行启动脚本：
   ```cmd
   .\start_agent.bat
   ```

2. 首次运行时会自动安装依赖

3. 输入股票代码（如 `600519`）

4. 程序将：
   - 获取股票数据（包含行业均值对比）
   - 进行AI分析
   - 生成PDF报告

### 直接运行

如果已安装依赖，可以直接运行：
```cmd
python main.py
```

### 配置自定义

1. 编辑 `config/settings.yaml` 文件
2. 调整模型设置、代理配置等
3. 重新运行程序，配置自动生效

### 测试新功能

```python
# 测试雅虎财经字段
python test_yfinance_fields.py

# 查看完整配置
python -c "from config.config_manager import get_config_manager; config = get_config_manager(); config.print_config_summary()"
```

## 故障排除

### 1. Python/pip问题

如果遇到Python或pip问题：
1. 确保Python 3.10+已安装并添加到PATH
2. 手动安装依赖：
   ```cmd
   pip install -r requirements.txt
   ```

### 2. API密钥错误

如果遇到API密钥错误：
1. 检查 `config/.env` 文件中的API密钥
2. 确保OpenRouter账户有可用额度
3. 运行程序时会提示输入API密钥

### 3. 网络连接问题

如果数据获取失败：
1. 检查网络连接
2. Akshare可能需要稳定的网络连接
3. 启用代理设置（如果需要）：
   ```yaml
   yfinance:
     proxy:
       enabled: true
       http_proxy: "http://your-proxy:port"
   ```

### 4. 雅虎财经数据缺失

如果雅虎财经无法获取数据：
1. 检查代理设置是否正确
2. 确保雅虎财经支持该股票代码
3. 系统会自动回退到akshare数据

### 5. PDF生成问题

如果PDF生成失败：
1. 确保已安装weasyprint依赖
2. Windows用户可能需要安装GTK3运行时
3. 报告会保存为Markdown格式作为备选

## 报告示例

生成的PDF报告包含以下部分：

1. **公司概况** - 基本信息、行业、上市日期、经营范围
2. **财务分析** - 盈利能力、成长性分析、行业对比
3. **估值分析** - PE/PB分析、行业均值比较、相对估值
4. **技术分析** - 价格走势、成交量分析
5. **行业对比** - 成长性指标行业排名、估值指标行业位置
6. **风险提示** - 财务风险、市场风险、行业风险
7. **投资建议** - 综合评估、评级建议、目标价位

## 注意事项

1. **数据准确性**: 数据来自Akshare和雅虎财经，仅供参考
2. **投资建议**: 报告内容不构成投资建议
3. **API限制**: OpenRouter API有调用频率限制
4. **网络依赖**: 需要互联网连接获取数据和API调用
5. **代理设置**: 如需访问雅虎财经，可能需要配置代理
6. **配置管理**: 配置文件修改后立即生效，无需重启

## 许可证

本项目仅供学习和研究使用。

## 支持与反馈

如有问题或建议，请检查代码注释或创建issue。

## 版本历史

### v1.2.0 (当前版本)
- 新增配置管理系统
- 集成雅虎财经接口重试机制
- 添加行业均值分析功能
- 分离所有配置到YAML文件

### v1.1.0
- 添加雅虎财经备用数据源
- 实现上市日期提取
- 添加经营范围数据整合
- 优化数据源冗余策略

### v1.0.0
- 初始版本发布
- 基础Akshare数据获取
- OpenRouter AI分析
- PDF报告生成

---

**技术栈**: Python, Akshare, yfinance, OpenRouter API, smolagents, WeasyPrint  
**适用场景**: A股金融分析、投资研究、数据可视化、自动化报告生成
