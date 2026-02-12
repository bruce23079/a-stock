#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股金融分析智能体 - 主入口点
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agent.analyst import AnalystAgent
from utils.pdf_generator import generate_pdf_report

def check_api_key() -> str:
    """
    检查API密钥，如果不存在则提示用户输入
    
    Returns:
        API密钥字符串
    """
    env_path = Path("config/.env")
    
    # 加载环境变量
    if env_path.exists():
        load_dotenv(env_path)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # 如果API密钥不存在或为空
    if not api_key or api_key == "your_key_here":
        print("=" * 60)
        print("欢迎使用 A股金融分析智能体")
        print("=" * 60)
        print("\n检测到未配置 OpenRouter API 密钥。")
        print("请前往 https://openrouter.ai/ 注册账号并获取API密钥。")
        
        while True:
            try:
                user_key = input("\n请输入您的 OpenRouter API 密钥: ").strip()
                if user_key:
                    # 保存到 .env 文件
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.write(f"OPENROUTER_API_KEY={user_key}\n")
                    
                    print(f"API密钥已保存到 {env_path}")
                    return user_key
                else:
                    print("API密钥不能为空，请重新输入。")
            except KeyboardInterrupt:
                print("\n\n用户取消操作。")
                sys.exit(1)
            except Exception as e:
                print(f"保存API密钥时出错: {e}")
                sys.exit(1)
    
    return api_key

def main():
    """主函数"""
    try:
        # 检查并获取API密钥
        api_key = check_api_key()
        
        # 重新加载环境变量以确保最新密钥生效
        load_dotenv(Path("config/.env"))
        
        print("\n" + "=" * 60)
        print("A股金融分析智能体")
        print("=" * 60)
        print("功能: 获取股票数据 -> AI分析 -> 生成PDF报告")
        print("=" * 60)
        
        # 获取股票代码输入
        while True:
            symbol = input("\n请输入A股股票代码 (例如: 600519 贵州茅台): ").strip()
            
            if not symbol:
                print("股票代码不能为空，请重新输入。")
                continue
            
            # 简单验证股票代码格式
            if not symbol.isdigit():
                print("股票代码应为数字，请重新输入。")
                continue
            
            # A股代码通常为6位数字
            if len(symbol) != 6:
                print("股票代码应为6位数字，请重新输入。")
                continue
            
            confirm = input(f"确认分析股票 {symbol}？(y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                break
            elif confirm in ['n', 'no', '否']:
                continue
            else:
                print("输入无效，请重新输入股票代码。")
        
        print(f"\n开始分析股票 {symbol}...")
        print("正在初始化分析智能体...")
        
        # 初始化分析智能体
        try:
            analyst = AnalystAgent("config/settings.yaml")
        except ValueError as e:
            print(f"初始化失败: {e}")
            print("请确保已正确设置API密钥。")
            sys.exit(1)
        except Exception as e:
            print(f"初始化时发生错误: {e}")
            print("请检查配置文件是否正确。")
            sys.exit(1)
        
        print("智能体初始化成功！")
        print("正在获取数据并进行分析...")
        print("-" * 60)
        
        # 分析股票
        markdown_report = analyst.analyze_stock(symbol)
        
        print("-" * 60)
        print("分析完成！正在生成报告...")
        
        # 生成报告（PDF或HTML）
        try:
            pdf_path = generate_pdf_report(markdown_report, symbol)
            # 检查文件类型
            if pdf_path.endswith('.pdf'):
                print(f"✓ PDF报告已生成: {pdf_path}")
                print(f"  文件大小: {os.path.getsize(pdf_path) / 1024:.1f} KB")
            elif pdf_path.endswith('.html'):
                print(f"✓ HTML报告已生成: {pdf_path}")
                print(f"  注：由于PDF引擎不可用，已生成HTML格式报告")
                print(f"  您可以打开此HTML文件，按Ctrl+P选择'保存为PDF'")
            else:
                print(f"报告已保存: {pdf_path}")
        except Exception as e:
            print(f"生成报告时出错: {e}")
            print("正在保存Markdown版本...")
            
            # 保存Markdown版本作为备选
            timestamp = datetime.now().strftime("%Y%m%d")
            md_path = f"reports/Report_{symbol}_{timestamp}.md"
            os.makedirs("reports", exist_ok=True)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            print(f"Markdown报告已保存到: {md_path}")
            pdf_path = md_path
        
        print("\n" + "=" * 60)
        print(f"分析完成！报告已保存到: {pdf_path}")
        print("=" * 60)
        
        # 询问用户是否继续分析其他股票
        while True:
            continue_analysis = input("\n是否继续分析其他股票？(y/n): ").strip().lower()
            if continue_analysis in ['y', 'yes', '是']:
                # 重新运行主函数（递归调用）
                return main()
            elif continue_analysis in ['n', 'no', '否']:
                print("\n感谢使用 A股金融分析智能体！")
                print("再见！")
                sys.exit(0)
            else:
                print("请输入 'y' 或 'n'")
    
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序运行时发生错误: {e}")
        print("请检查网络连接或配置是否正确。")
        sys.exit(1)

if __name__ == "__main__":
    # 添加当前目录到路径，确保模块可以导入
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 确保 reports 目录存在
    os.makedirs("reports", exist_ok=True)
    
    # 运行主函数
    main()
