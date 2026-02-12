import akshare as ak
import pandas as pd
from typing import Dict, Any
import json
from smolagents import tool
import yfinance as yf
import os
import datetime
import time

"""
本模块提供股票估值和财务信息的工具函数，主要使用akshare接口。
当akshare接口失败或数据缺失时，自动回退到yfinance接口作为备用数据源。
备用接口适用于估值（PE、PB、市值）和财务指标（ROE、毛利率等）。
"""

# 设置代理以改善yfinance连接性（可选）
proxy_url = os.environ.get('YFINANCE_PROXY', 'http://127.0.0.1:10808')
if proxy_url:
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url

def yfinance_with_retry(yf_symbol: str, max_retries: int = 5, retry_delay: float = 1.0):
    """
    带重试机制的yfinance数据获取
    
    Args:
        yf_symbol: yfinance格式的股票代码（如'600519.SS'）
        max_retries: 最大重试次数，默认为5次
        retry_delay: 重试延迟（秒），默认为1秒
    
    Returns:
        (ticker, info) 元组，或 (None, None) 如果所有重试都失败
    """
    ticker = None
    info = None
    
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            # 检查是否返回了有效数据（如果只有trailingPegRatio键，说明数据缺失）
            if len(info) <= 1 and 'trailingPegRatio' in info:
                # 数据不完整，视为失败，需要重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return ticker, info  # 最后一次尝试，返回不完整数据
            # 数据有效，返回
            return ticker, info
            
        except Exception as e:
            # 发生异常，记录并重试
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                # 最后一次尝试仍然失败，返回None
                return None, None
    
    return None, None

def get_industry_averages(symbol: str, industry: str = ""):
    """
    获取行业均值数据，使用akshare的成长性比较和估值比较接口
    
    Args:
        symbol: 股票代码，例如 "600519"
        industry: 行业名称（可选）
    
    Returns:
        包含行业均值数据的字典
    """
    try:
        # 将A股代码转换为akshare格式
        # akshare接口需要格式如 "SZ000895" 或 "SH600519"
        akshare_symbol = symbol
        if symbol.startswith('6'):
            akshare_symbol = f"SH{symbol}"
        elif symbol.startswith(('0', '3')):
            akshare_symbol = f"SZ{symbol}"
        
        # 1. 获取成长性比较数据
        growth_df = ak.stock_zh_growth_comparison_em(symbol=akshare_symbol)
        
        # 2. 获取估值比较数据
        valuation_df = ak.stock_zh_valuation_comparison_em(symbol=akshare_symbol)
        
        # 提取行业平均数据
        industry_avg_growth = {}
        industry_avg_valuation = {}
        
        # 从成长性比较数据中提取行业平均
        if not growth_df.empty:
            # 查找"行业平均"行
            avg_row = growth_df[growth_df['简称'] == '行业平均']
            if not avg_row.empty:
                # 提取关键成长性指标
                industry_avg_growth = {
                    'eps_growth_3y_avg': avg_row.iloc[0].get('基本每股收益增长率-3年复合', 0),
                    'eps_growth_ttm_avg': avg_row.iloc[0].get('基本每股收益增长率-TTM', 0),
                    'revenue_growth_3y_avg': avg_row.iloc[0].get('营业收入增长率-3年复合', 0),
                    'revenue_growth_ttm_avg': avg_row.iloc[0].get('营业收入增长率-TTM', 0),
                    'net_profit_growth_3y_avg': avg_row.iloc[0].get('净利润增长率-3年复合', 0),
                    'net_profit_growth_ttm_avg': avg_row.iloc[0].get('净利润增长率-TTM', 0),
                }
        
        # 从估值比较数据中提取行业平均
        if not valuation_df.empty:
            # 查找"行业平均"行
            avg_row = valuation_df[valuation_df['简称'] == '行业平均']
            if not avg_row.empty:
                # 提取关键估值指标
                industry_avg_valuation = {
                    'pe_ttm_avg': avg_row.iloc[0].get('市盈率-TTM', 0),
                    'pb_mrq_avg': avg_row.iloc[0].get('市净率-MRQ', 0),
                    'ps_ttm_avg': avg_row.iloc[0].get('市销率-TTM', 0),
                    'peg_avg': avg_row.iloc[0].get('PEG', 0),
                    'ev_ebitda_avg': avg_row.iloc[0].get('EV/EBITDA-24A', 0),
                }
        
        # 构建完整的行业均值数据字典
        industry_averages = {
            "industry": industry,
            # 成长性指标
            "eps_growth_3y_avg": industry_avg_growth.get('eps_growth_3y_avg', 0),
            "eps_growth_ttm_avg": industry_avg_growth.get('eps_growth_ttm_avg', 0),
            "revenue_growth_3y_avg": industry_avg_growth.get('revenue_growth_3y_avg', 0),
            "revenue_growth_ttm_avg": industry_avg_growth.get('revenue_growth_ttm_avg', 0),
            "net_profit_growth_3y_avg": industry_avg_growth.get('net_profit_growth_3y_avg', 0),
            "net_profit_growth_ttm_avg": industry_avg_growth.get('net_profit_growth_ttm_avg', 0),
            # 估值指标
            "pe_ttm_avg": industry_avg_valuation.get('pe_ttm_avg', 0),
            "pb_mrq_avg": industry_avg_valuation.get('pb_mrq_avg', 0),
            "ps_ttm_avg": industry_avg_valuation.get('ps_ttm_avg', 0),
            "peg_avg": industry_avg_valuation.get('peg_avg', 0),
            "ev_ebitda_avg": industry_avg_valuation.get('ev_ebitda_avg', 0),
            "data_source": "akshare",
            "note": f"行业均值数据来自akshare接口，基于{symbol}所在行业的同行比较数据"
        }
        
        return industry_averages
        
    except Exception as e:
        # 如果akshare接口失败，返回占位数据
        industry_averages = {
            "industry": industry,
            "eps_growth_3y_avg": 0,
            "eps_growth_ttm_avg": 0,
            "revenue_growth_3y_avg": 0,
            "revenue_growth_ttm_avg": 0,
            "net_profit_growth_3y_avg": 0,
            "net_profit_growth_ttm_avg": 0,
            "pe_ttm_avg": 0,
            "pb_mrq_avg": 0,
            "ps_ttm_avg": 0,
            "peg_avg": 0,
            "ev_ebitda_avg": 0,
            "data_source": "error",
            "note": f"获取行业均值数据失败: {str(e)}，返回默认值"
        }
        return industry_averages

@tool
def get_market_valuation(symbol: str) -> Dict[str, Any]:
    """
    获取股票的实时市值、PE、PB等信息
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含名称、最新价格、PE-TTM、PB、总市值
    """
    try:
        # 方法1：尝试使用 stock_individual_info_em 获取公司信息（包含市值）
        # 这个接口比 stock_zh_a_spot_em 更稳定
        company_df = ak.stock_individual_info_em(symbol=symbol)
        
        if company_df.empty:
            return {"error": f"未找到股票代码 {symbol} 的公司信息"}
        
        # 转换为字典
        company_info = {}
        for _, row in company_df.iterrows():
            key = row['item']
            value = row['value']
            if pd.isna(value):
                value = ''
            company_info[key] = value
        
        # 提取基础信息
        name = company_info.get('股票简称', '')
        market_cap = company_info.get('总市值', 0)
        circulating_market_cap = company_info.get('流通市值', 0)
        
        # 对于PE/PB数据，由于接口限制，暂时设为0
        # 如果需要这些数据，需要寻找其他数据源或使用备用方法
        pe_ttm = 0  # 暂时设为0，未来可以寻找其他数据源
        pb = 0      # 暂时设为0，未来可以寻找其他数据源
        
        # 尝试从yfinance获取PE/PB作为备用（即使akshare成功）
        try:
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            pe_ttm = info.get('trailingPE', 0)
            pb = info.get('priceToBook', 0)
            eps_ttm = info.get('trailingEps', 0)
            eps_forward = info.get('forwardEps', 0)
        except:
            # 如果yfinance失败，保持0值
            pe_ttm = 0
            pb = 0
            eps_ttm = 0
            eps_forward = 0
        
        # 方法2：尝试获取最新价格
        latest_price = 0
        try:
            # 使用 stock_zh_a_spot 获取最新价格（如果可用）
            spot_df = ak.stock_zh_a_spot()
            target_code = symbol
            if not symbol.startswith(('sh', 'sz')):
                if symbol.startswith('6'):
                    target_code = f'sh{symbol}'
                elif symbol.startswith(('0', '3')):
                    target_code = f'sz{symbol}'
            
            matched_row = spot_df[spot_df['代码'] == target_code]
            if matched_row.empty:
                matched_row = spot_df[spot_df['代码'].str.endswith(symbol)]
            
            if not matched_row.empty:
                latest_price = float(matched_row.iloc[0].get('最新价', 0))
        except:
            # 如果获取失败，使用其他方法或默认值
            pass
        
        # 如果从spot接口获取价格失败，尝试从company_info中获取
        if latest_price == 0:
            latest_price_str = company_info.get('最新', '0')
            try:
                latest_price = float(latest_price_str)
            except:
                latest_price = 0
        
        # 获取行业信息用于行业均值
        industry = company_info.get('行业', '')
        
        # 获取行业均值数据
        industry_averages = get_industry_averages(symbol, industry)
        
        result = {
            "symbol": symbol,
            "name": name,
            "latest_price": latest_price,
            "pe_ttm": pe_ttm,
            "pb": pb,
            "eps_ttm": eps_ttm,
            "eps_forward": eps_forward,
            "market_cap": float(market_cap) if market_cap else 0,
            "circulating_market_cap": float(circulating_market_cap) if circulating_market_cap else 0,
            "industry_averages": industry_averages,
            "note": "PE和PB数据来自yfinance备用接口（若akshare不可用）" if pe_ttm or pb else "PE和PB数据暂时不可用，如需完整估值数据请检查网络连接或使用其他数据源"
        }
        
        return result
        
    except Exception as e:
        # akshare失败，尝试使用yfinance作为备用
        try:
            # 将A股代码转换为yfinance格式
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            
            # 使用带重试的yfinance获取数据
            ticker, info = yfinance_with_retry(yf_symbol, max_retries=5)
            
            if ticker is None or info is None:
                return {"error": f"akshare接口失败，且yfinance重试5次后仍未获取到股票代码 {symbol} 的数据"}
            
            # 检查yfinance是否返回了有效数据（如果只有trailingPegRatio键，说明数据缺失）
            if len(info) <= 1 and 'trailingPegRatio' in info:
                # yfinance没有该股票的数据
                return {"error": f"akshare接口失败，且yfinance也未找到股票代码 {symbol} 的数据"}
            
            # 提取数据
            name = info.get('longName', '') or info.get('shortName', '')
            latest_price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
            pe_ttm = info.get('trailingPE', 0)
            pb = info.get('priceToBook', 0)
            eps_ttm = info.get('trailingEps', 0)
            eps_forward = info.get('forwardEps', 0)
            market_cap = info.get('marketCap', 0)
            circulating_market_cap = info.get('floatShares', 0) * latest_price if info.get('floatShares') else market_cap * 0.7  # 估算
            
            # 获取行业信息
            industry = info.get('industry', '') or info.get('sector', '')
            
            # 获取行业均值数据
            industry_averages = get_industry_averages(symbol, industry)
            
            result = {
                "symbol": symbol,
                "name": name,
                "latest_price": latest_price,
                "pe_ttm": pe_ttm,
                "pb": pb,
                "eps_ttm": eps_ttm,
                "eps_forward": eps_forward,
                "market_cap": float(market_cap) if market_cap else 0,
                "circulating_market_cap": float(circulating_market_cap) if circulating_market_cap else 0,
                "industry_averages": industry_averages,
                "note": "数据来自yfinance备用接口（akshare失败），经过重试机制获取"
            }
            return result
        except Exception as yf_e:
            return {"error": f"获取市值信息失败: {str(e)}，且yfinance备用也失败: {str(yf_e)}"}

@tool
def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    获取公司基本信息：行业、上市日期等
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含公司信息
    """
    try:
        # 使用可用的接口 stock_individual_info_em
        # 该接口不需要添加交易所前缀
        df = ak.stock_individual_info_em(symbol=symbol)
        
        # 转换为字典
        info_dict = {}
        for _, row in df.iterrows():
            key = row['item']
            value = row['value']
            if pd.isna(value):
                value = ''
            info_dict[key] = value
        
        # 提取关键信息（根据em接口的字段）
        # 注意：em接口缺少以下字段：法人代表、注册地址、经营范围、公司介绍
        # 尝试从yfinance获取经营范围
        business_scope = ""
        try:
            # 将A股代码转换为yfinance格式
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            
            # 使用带重试的yfinance获取经营范围
            ticker, yf_info = yfinance_with_retry(yf_symbol, max_retries=3, retry_delay=0.5)
            if ticker is not None and yf_info is not None:
                business_scope = yf_info.get('longBusinessSummary', '')
        except Exception:
            # 如果yfinance获取失败，保持空字符串
            business_scope = ""
        
        result = {
            "symbol": symbol,
            "company_name": info_dict.get('股票简称', ''),
            "industry": info_dict.get('行业', ''),
            "company_introduction": "",  # em接口没有此字段
            "listing_date": info_dict.get('上市时间', ''),
            "legal_representative": "",  # em接口没有此字段
            "registered_address": "",    # em接口没有此字段
            "business_scope": business_scope,
            "full_info": info_dict,
            "note": "公司基本信息来自akshare接口，经营范围来自yfinance接口" if business_scope else "公司信息来自akshare接口"
        }
        
        return result
        
    except Exception as e:
        # akshare失败，尝试使用yfinance作为备用
        try:
            # 将A股代码转换为yfinance格式
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            
            # 使用带重试的yfinance获取数据
            ticker, info = yfinance_with_retry(yf_symbol, max_retries=5)
            
            if ticker is None or info is None:
                return {"error": f"akshare接口失败，且yfinance重试5次后仍未获取到股票代码 {symbol} 的公司信息"}
            
            # 检查yfinance是否返回了有效数据（如果只有trailingPegRatio键，说明数据缺失）
            if len(info) <= 1 and 'trailingPegRatio' in info:
                # yfinance没有该股票的数据
                return {"error": f"akshare接口失败，且yfinance也未找到股票代码 {symbol} 的公司信息"}
            
            # 提取公司信息
            company_name = info.get('longName', '') or info.get('shortName', '')
            industry = info.get('industry', '') or info.get('sector', '')
            # 提取上市日期（首次交易日期）
            listing_date = ''
            if 'firstTradeDateMilliseconds' in info:
                try:
                    ms = info['firstTradeDateMilliseconds']
                    if ms and ms > 0:
                        dt = datetime.datetime.fromtimestamp(ms / 1000)
                        listing_date = dt.strftime('%Y-%m-%d')
                except Exception:
                    listing_date = ''
            # 提取额外字段
            description = info.get('longBusinessSummary', '')
            total_employees = info.get('fullTimeEmployees', 0)
            weighted_shares_outstanding = info.get('sharesOutstanding', 0)
            
            result = {
                "symbol": symbol,
                "company_name": company_name,
                "industry": industry,
                "company_introduction": description,
                "listing_date": listing_date,
                "legal_representative": '',
                "registered_address": '',
                "business_scope": description,  # 使用longBusinessSummary作为经营范围
                "description": description,
                "total_employees": total_employees,
                "weighted_shares_outstanding": weighted_shares_outstanding,
                "full_info": info,
                "note": "公司信息来自yfinance备用接口（akshare失败），经过重试机制获取，请注意部分字段为英文，请在报告中翻译为中文"
            }
            return result
        except Exception as yf_e:
            return {"error": f"获取公司信息失败: {str(e)}，且yfinance备用也失败: {str(yf_e)}"}

@tool
def get_financial_indicators(symbol: str) -> Dict[str, Any]:
    """
    获取财务指标：ROE、毛利率、净利润增长率等
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含最近4个报告期的财务指标
    """
    try:
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        if df.empty:
            # akshare返回空数据，尝试使用yfinance作为备用
            try:
                # 将A股代码转换为yfinance格式
                if symbol.startswith('6'):
                    yf_symbol = f"{symbol}.SS"
                elif symbol.startswith(('0', '3')):
                    yf_symbol = f"{symbol}.SZ"
                else:
                    yf_symbol = symbol
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                
                # 检查yfinance是否返回了有效数据（如果只有trailingPegRatio键，说明数据缺失）
                if len(info) <= 1 and 'trailingPegRatio' in info:
                    # yfinance没有该股票的数据
                    return {"error": f"akshare接口无数据，且yfinance也未找到股票代码 {symbol} 的财务指标数据"}
                
                # 提取最新财务指标
                roe = info.get('returnOnEquity', 0)
                gross_margin = info.get('grossMargins', 0)  # 毛利率
                profit_margin = info.get('profitMargins', 0)
                # 净利润增长率需要计算，暂时设为0
                net_profit_growth = 0
                total_revenue = info.get('totalRevenue', 0)
                net_profit = info.get('netIncomeToCommon', 0)
                
                # 创建单个记录（最新期间）
                record = {
                    "date": "",  # yfinance未提供报告日期
                    "roe": float(roe) if roe else 0,
                    "gross_margin": float(gross_margin) if gross_margin else 0,
                    "net_profit_growth": net_profit_growth,
                    "total_revenue": float(total_revenue) if total_revenue else 0,
                    "net_profit": float(net_profit) if net_profit else 0
                }
                
                result = {
                    "symbol": symbol,
                    "financial_indicators": [record],
                    "count": 1,
                    "note": "财务指标来自yfinance备用接口（akshare无数据），仅提供最新数据"
                }
                return result
            except Exception as yf_e:
                return {"error": f"未找到股票代码 {symbol} 的财务指标数据，且yfinance备用也失败: {str(yf_e)}"}
        
        # 按日期降序排序（最新的在前面）
        df = df.sort_values('日期', ascending=False)
        
        # 取最近4条记录
        latest_records = df.head(4)
        
        # 转换为字典列表
        records = []
        for _, row in latest_records.iterrows():
            record = {
                "date": row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else '',
                "roe": float(row.get('净资产收益率', 0)) if pd.notna(row.get('净资产收益率', 0)) else 0,
                "gross_margin": float(row.get('销售毛利率', 0)) if pd.notna(row.get('销售毛利率', 0)) else 0,
                "net_profit_growth": float(row.get('净利润增长率', 0)) if pd.notna(row.get('净利润增长率', 0)) else 0,
                "total_revenue": float(row.get('营业收入', 0)) if pd.notna(row.get('营业收入', 0)) else 0,
                "net_profit": float(row.get('净利润', 0)) if pd.notna(row.get('净利润', 0)) else 0
            }
            records.append(record)
        
        result = {
            "symbol": symbol,
            "financial_indicators": records,
            "count": len(records)
        }
        
        return result
        
    except Exception as e:
        # akshare失败，尝试使用yfinance作为备用
        try:
            # 将A股代码转换为yfinance格式
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            # 检查yfinance是否返回了有效数据（如果只有trailingPegRatio键，说明数据缺失）
            if len(info) <= 1 and 'trailingPegRatio' in info:
                # yfinance没有该股票的数据
                return {"error": f"akshare接口失败，且yfinance也未找到股票代码 {symbol} 的财务指标数据"}
            
            # 提取最新财务指标
            roe = info.get('returnOnEquity', 0)
            gross_margin = info.get('grossMargins', 0)  # 毛利率
            profit_margin = info.get('profitMargins', 0)
            # 净利润增长率需要计算，暂时设为0
            net_profit_growth = 0
            total_revenue = info.get('totalRevenue', 0)
            net_profit = info.get('netIncomeToCommon', 0)
            
            # 创建单个记录（最新期间）
            record = {
                "date": "",  # yfinance未提供报告日期
                "roe": float(roe) if roe else 0,
                "gross_margin": float(gross_margin) if gross_margin else 0,
                "net_profit_growth": net_profit_growth,
                "total_revenue": float(total_revenue) if total_revenue else 0,
                "net_profit": float(net_profit) if net_profit else 0
            }
            
            result = {
                "symbol": symbol,
                "financial_indicators": [record],
                "count": 1,
                "note": "财务指标来自yfinance备用接口（akshare失败），仅提供最新数据"
            }
            return result
        except Exception as yf_e:
            return {"error": f"获取财务指标失败: {str(e)}，且yfinance备用也失败: {str(yf_e)}"}

@tool
def get_price_history(symbol: str) -> Dict[str, Any]:
    """
    获取最近30天的股价历史数据
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含日期、收盘价、成交量
    """
    try:
        # 获取最近30天的数据
        # akshare 的 stock_zh_a_hist 默认返回所有历史数据，我们需要限制为30天
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if df.empty:
            return {"error": f"未找到股票代码 {symbol} 的历史价格数据"}
        
        # 确保数据按日期排序（最新的在前面）
        df = df.sort_values('日期', ascending=False)
        
        # 取最近30条记录
        latest_records = df.head(30)
        
        # 转换为字典列表
        records = []
        for _, row in latest_records.iterrows():
            record = {
                "date": row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else '',
                "close": float(row.get('收盘', 0)) if pd.notna(row.get('收盘', 0)) else 0,
                "volume": float(row.get('成交量', 0)) if pd.notna(row.get('成交量', 0)) else 0,
                "open": float(row.get('开盘', 0)) if pd.notna(row.get('开盘', 0)) else 0,
                "high": float(row.get('最高', 0)) if pd.notna(row.get('最高', 0)) else 0,
                "low": float(row.get('最低', 0)) if pd.notna(row.get('最低', 0)) else 0,
                "change_percent": float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅', 0)) else 0
            }
            records.append(record)
        
        # 计算最新价格（第一条记录的收盘价）
        latest_price = records[0]['close'] if records else 0
        
        result = {
            "symbol": symbol,
            "price_history": records,
            "count": len(records),
            "latest_price": latest_price
        }
        
        return result
        
    except Exception as e:
        # akshare失败，尝试使用yfinance作为备用
        try:
            # 将A股代码转换为yfinance格式
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith(('0', '3')):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            
            # 下载最近30天的数据
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="30d")  # 获取最近30天
            
            if hist.empty:
                return {"error": f"未找到股票代码 {symbol} 的历史价格数据（akshare失败，yfinance无数据）"}
            
            # 获取最新实时价格
            info = ticker.info
            latest_price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
            
            # 转换为字典列表
            records = []
            for date, row in hist.iterrows():
                record = {
                    "date": date.strftime('%Y-%m-%d'),
                    "close": float(row.get('Close', 0)),
                    "volume": float(row.get('Volume', 0)),
                    "open": float(row.get('Open', 0)),
                    "high": float(row.get('High', 0)),
                    "low": float(row.get('Low', 0)),
                    "change_percent": 0  # yfinance不提供涨跌幅，需要计算
                }
                records.append(record)
            
            # 按日期降序排序（最新的在前面）
            records = sorted(records, key=lambda x: x['date'], reverse=True)
            
            result = {
                "symbol": symbol,
                "price_history": records,
                "count": len(records),
                "latest_price": latest_price,
                "note": "价格历史数据来自yfinance备用接口（akshare失败）"
            }
            return result
        except Exception as yf_e:
            return {"error": f"获取价格历史失败: {str(e)}，且yfinance备用也失败: {str(yf_e)}"}

@tool
def get_latest_price(symbol: str) -> Dict[str, Any]:
    """
    获取股票的实时股价数据，用于技术分析
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含最新价格、涨跌幅、成交量、beta等技术指标
    """
    try:
        # 将A股代码转换为yfinance格式
        if symbol.startswith('6'):
            yf_symbol = f"{symbol}.SS"
        elif symbol.startswith(('0', '3')):
            yf_symbol = f"{symbol}.SZ"
        else:
            yf_symbol = symbol
        
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # 检查yfinance是否返回了有效数据
        if len(info) <= 1 and 'trailingPegRatio' in info:
            return {"error": f"未找到股票代码 {symbol} 的实时价格数据"}
        
        # 提取关键价格数据
        latest_price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
        previous_close = info.get('previousClose', 0)
        change_percent = info.get('regularMarketChangePercent', 0) or ((latest_price - previous_close) / previous_close * 100 if previous_close else 0)
        volume = info.get('regularMarketVolume', 0) or info.get('volume', 0)
        beta = info.get('beta', 0)
        avg_volume = info.get('averageVolume', 0)
        market_cap = info.get('marketCap', 0)
        
        # 计算简单技术指标：50日和200日移动平均（如果历史数据可用）
        ma50 = 0
        ma200 = 0
        try:
            hist = ticker.history(period="6mo")
            if not hist.empty:
                ma50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else 0
                ma200 = hist['Close'].tail(200).mean() if len(hist) >= 200 else 0
        except:
            pass
        
        result = {
            "symbol": symbol,
            "latest_price": float(latest_price) if latest_price else 0,
            "change_percent": float(change_percent) if change_percent else 0,
            "volume": int(volume) if volume else 0,
            "beta": float(beta) if beta else 0,
            "avg_volume": int(avg_volume) if avg_volume else 0,
            "market_cap": float(market_cap) if market_cap else 0,
            "moving_average_50": float(ma50) if ma50 else 0,
            "moving_average_200": float(ma200) if ma200 else 0,
            "note": "实时价格数据来自yfinance接口"
        }
        return result
    except Exception as e:
        return {"error": f"获取实时股价数据失败: {str(e)}"}

@tool
def get_risk_indicators(symbol: str) -> Dict[str, Any]:
    """
    获取股票的风险提示相关数据，如beta、波动率、债务权益比等
    
    Args:
        symbol: 股票代码，例如 "600519"
    
    Returns:
        字典包含风险指标
    """
    try:
        # 将A股代码转换为yfinance格式
        if symbol.startswith('6'):
            yf_symbol = f"{symbol}.SS"
        elif symbol.startswith(('0', '3')):
            yf_symbol = f"{symbol}.SZ"
        else:
            yf_symbol = symbol
        
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # 检查yfinance是否返回了有效数据
        if len(info) <= 1 and 'trailingPegRatio' in info:
            return {"error": f"未找到股票代码 {symbol} 的风险指标数据"}
        
        # 提取风险相关指标
        beta = info.get('beta', 0)
        debt_to_equity = info.get('debtToEquity', 0)
        current_ratio = info.get('currentRatio', 0)
        quick_ratio = info.get('quickRatio', 0)
        total_debt = info.get('totalDebt', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        revenue_growth = info.get('revenueGrowth', 0)
        # 波动率：可以用52周价格范围计算或使用默认值
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
        current_price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
        if fifty_two_week_high and fifty_two_week_low and fifty_two_week_high != fifty_two_week_low:
            volatility = (fifty_two_week_high - fifty_two_week_low) / fifty_two_week_low * 100
        else:
            volatility = 0
        
        result = {
            "symbol": symbol,
            "beta": float(beta) if beta else 0,
            "debt_to_equity": float(debt_to_equity) if debt_to_equity else 0,
            "current_ratio": float(current_ratio) if current_ratio else 0,
            "quick_ratio": float(quick_ratio) if quick_ratio else 0,
            "total_debt": float(total_debt) if total_debt else 0,
            "earnings_growth": float(earnings_growth) if earnings_growth else 0,
            "revenue_growth": float(revenue_growth) if revenue_growth else 0,
            "volatility_percent": float(volatility) if volatility else 0,
            "fifty_two_week_high": float(fifty_two_week_high) if fifty_two_week_high else 0,
            "fifty_two_week_low": float(fifty_two_week_low) if fifty_two_week_low else 0,
            "note": "风险指标数据来自yfinance接口"
        }
        return result
    except Exception as e:
        return {"error": f"获取风险指标数据失败: {str(e)}"}
