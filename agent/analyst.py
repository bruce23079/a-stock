import yaml
import os
from typing import Dict, Any
from smolagents import CodeAgent, OpenAIServerModel
from tools.akshare_tools import (
    get_market_valuation,
    get_company_info,
    get_financial_indicators,
    get_price_history,
    get_latest_price,
    get_risk_indicators
)

class AnalystAgent:
    """A股金融分析智能体"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化分析智能体
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.model = None
        self.agent = None
        self._load_config()
        self._init_model()
        self._init_agent()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def _init_model(self) -> None:
        """初始化OpenAI兼容模型"""
        # 从环境变量获取API密钥
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY 环境变量未设置。请在 config/.env 文件中设置。")
        
        base_url = self.config['model']['base_url']
        model_name = self.config['model']['model_name']
        
        self.model = OpenAIServerModel(
            model_id=model_name,
            api_base=base_url,
            api_key=api_key,
            max_tokens=4000,
            temperature=0.1
        )
    
    def _init_agent(self) -> None:
        """初始化代码智能体"""
        # 定义工具列表
        tools = [
            get_market_valuation,
            get_company_info,
            get_financial_indicators,
            get_price_history,
            get_latest_price,
            get_risk_indicators
        ]

        # 创建智能体 - 使用默认的prompt_templates
        # 在smolagents 1.24.0中，我们可以让CodeAgent使用默认的prompt_templates
        # 并通过其他方式设置系统提示（在task中包含）
        self.agent = CodeAgent(
            tools=tools,
            model=self.model,
            max_steps=15,
            additional_authorized_imports=["pandas", "json", "typing", "datetime"],
            planning_interval=3
        )
    
    def analyze_stock(self, symbol: str) -> str:
        """
        分析指定股票代码并生成报告
        
        Args:
            symbol: 股票代码，例如 "600519"
            
        Returns:
            Markdown格式的分析报告
        """
        if not self.agent:
            raise RuntimeError("智能体未正确初始化")
        
        # 构建分析任务，将系统提示包含在任务中
        task = f"""你是一位专业的A股金融分析师。请基于提供的数据生成详细的分析报告。

输出语言：简体中文。

报告结构：
1. 公司概况 (Company Profile)
   - 基本信息（公司名称、所属行业、上市日期）
   - 经营范围
   - 最新市值和股价信息

2. 财务分析 (Financial Analysis)
   - 盈利能力分析（ROE、毛利率）
   - 成长性分析（净利润增长率）
   - 财务状况评估
   - EPS分析（每股收益TTM和预测）

3. 估值分析 (Valuation Analysis)
   - PE（市盈率）分析
   - PB（市净率）分析
   - EPS分析（每股收益）
   - 与行业平均值的比较（如有数据）

4. 技术分析 (Technical Analysis)
   - 近期价格走势
   - 成交量分析
   - 关键支撑/阻力位
   - 实时股价及技术指标（移动平均线、beta等）

5. 风险提示 (Risk Warnings)
   - 财务风险（债务权益比、流动比率等）
   - 市场风险（beta、波动率）
   - 行业特定风险

6. 投资建议 (Investment Advice)
   - 综合评估
   - 投资评级（买入/持有/卖出）
   - 目标价格区间（如有）

请分析股票代码 {symbol} (A股)。
请使用提供的工具获取以下信息：
1. 公司基本信息
2. 市场估值数据（PE、PB、市值、EPS）
3. 财务指标（ROE、毛利率、净利润增长率）
4. 最近30天的价格历史
5. 实时股价及技术指标
6. 风险指标（beta、债务权益比、波动率等）

基于这些数据，生成一份完整的分析报告。
如果数据源是雅虎财经（yfinance）接口，部分字段可能是英文，请将其翻译为中文后呈现在报告中。
请使用 markdown 格式输出报告，确保内容专业、数据驱动、逻辑清晰。
"""
        
        try:
            print(f"开始分析股票 {symbol}...")
            response = self.agent.run(task)
            print("分析完成！")
            return response
        except Exception as e:
            error_msg = f"股票分析过程中出错: {str(e)}"
            print(error_msg)
            return f"# 分析错误\n\n{error_msg}\n\n请检查股票代码是否正确，或网络连接是否正常。"
