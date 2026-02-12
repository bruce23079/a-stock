# Role: Senior Python Architect & Quant Developer (Windows Specialist)
# Project: A-Share Financial Analyst Agent (Windows Portable Edition)

## 1. Project Overview
We are building a local financial analysis agent for **Windows**.
**Goal:** A "one-click" application where the user runs a `.bat` file, which automatically handles the Python virtual environment, fetches stock data via Akshare, analyzes it using an LLM (OpenRouter), and generates a professional PDF report.

## 2. Tech Stack & Environment
- **OS:** Windows 10/11.
- **Language:** Python 3.10+ (Assumed installed and added to PATH).
- **Virtualization:** Native `venv` module (Local directory `./venv`).
- **Entry Point:** Windows Batch Script (`start_agent.bat`).
- **Core Libraries:** - `smolagents` (HuggingFace Agent Framework)
  - `akshare` (Financial Data)
  - `markdown2` (Report conversion)
  - `weasyprint` (PDF Generation)
  - `pyyaml`, `python-dotenv` (Config)

## 3. Directory Structure
Create the following structure:
/project_root
  ├── /config
  │     ├── settings.yaml      # Model config (base_url, model_name)
  │     └── .env               # API Key storage (OPENROUTER_API_KEY)
  ├── /tools
  │     ├── __init__.py
  │     └── akshare_tools.py   # STRICT Akshare wrappers
  ├── /agent
  │     ├── __init__.py
  │     └── analyst.py         # CodeAgent logic
  ├── /utils
  │     ├── __init__.py
  │     └── pdf_generator.py   # Windows-compatible PDF converter
  ├── main.py                  # Main CLI entry point
  ├── requirements.txt         # Dependencies
  └── start_agent.bat          # Windows Launcher

## 4. Implementation Specifications

### Step 1: The Windows Launcher (`start_agent.bat`)
Create a batch script with the following logic:
1. Turn off echo.
2. Check if the folder `venv` exists.
   - **If NOT exists:** Print "Initializing Environment...", run `python -m venv venv`, activate it, then run `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`.
   - **If exists:** Activate it (`call venv\Scripts\activate`).
3. Run `python main.py`.
4. Add `pause` at the end to keep the window open on error.

### Step 2: Configuration Management
- **`config/settings.yaml`**:
  ```yaml
  model:
    base_url: "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"
    model_name: "deepseek/deepseek-chat"  # Or your preferred model
config/.env:

OPENROUTER_API_KEY=your_key_here
main.py Logic: If .env is missing or key is empty, prompt user to input the key in the console and save it to .env.

Step 3: Akshare Tool Wrappers (CRITICAL & STRICT)
File: tools/akshare_tools.py Constraint: You MUST wrap these specific Akshare functions using smolagents.tool. Output Format: All tools must return a String or JSON String. Do not return raw DataFrames.

Tool 1: get_market_valuation(symbol: str)
Purpose: Get real-time Price, PE, PB, Market Cap.

Akshare Function: ak.stock_zh_a_spot_em()

CRITICAL LOGIC: This function returns data for ALL stocks. You CANNOT pass a symbol to it. You must fetch all and filter by symbol in Python.

Return Fields: Name, Latest Price, PE-TTM, PB, Total Market Cap.

Tool 2: get_company_info(symbol: str)
Purpose: Get industry, listing date, business scope, company introduction, legal representative, registered address.

Akshare Function: ak.stock_individual_info_em(symbol=symbol)

Logic: Convert the returned DataFrame (columns: item, value) into a Dictionary. Extract key information:
- Company name: 股票简称
- Industry: 行业
- Listing date: 上市时间
- Note: The following fields are not available in stock_individual_info_em and are set to empty strings:
  - Company introduction
  - Legal representative  
  - Registered address
  - Business scope

Tool 3: get_financial_indicators(symbol: str)
Purpose: Get ROE, Gross Margin, Net Profit Growth.

Akshare Function: ak.stock_financial_analysis_indicator(symbol=symbol)

Logic: 1. Sort by date (descending). 2. Take only the top 4 rows (latest year data) to save Tokens. 3. Convert to JSON/Dict.

Tool 4: get_price_history(symbol: str)
Purpose: Get recent price trend.

Akshare Function: ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq", ...)

Logic: Fetch last 30 days. Return columns: Date, Close, Volume.

Step 4: The Analyst Agent (agent/analyst.py)
Initialize OpenAIServerModel using config from settings.yaml.

Initialize CodeAgent with the tools above.

System Prompt: "You are an expert A-Share financial analyst. Output Language: Chinese (Simplified). Report Structure:

Company Profile (公司概况)

Financial Analysis (财务分析): Analyze Profitability (ROE), Solvency, and Growth.

Valuation (估值分析): Assess current PE/PB.

Risk Warnings (风险提示).

Investment Advice (投资建议).

Process: 1. Call tools to get data. 2. Think about the data. 3. Write the final report in Markdown format."

Step 5: Windows PDF Generator (utils/pdf_generator.py)
Use markdown2 to convert MD -> HTML.

Use weasyprint for HTML -> PDF.

WINDOWS FONT FIX (CRITICAL): In the CSS, you MUST explicitly set the font family to support Chinese, or the PDF will show squares.

CSS
body {
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    line-height: 1.6;
}
Filename format: Report_{symbol}_{YYYYMMDD}.pdf.

5. Execution Flow (main.py)
Init: Load Config & Check API Key.

Input: Ask user for Stock Code (e.g., "600519").

Run: Pass the code to the Agent.

Generate: Receive Markdown from Agent -> Pass to pdf_generator.

Finish: Print "PDF Report saved to [path]".

6. Instructions for Developer
Create requirements.txt first.

Create start_agent.bat.

Implement the tools module strictly following the Akshare specs above.

Implement the agent and utils.

Finish with main.py.
