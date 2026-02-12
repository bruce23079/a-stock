import markdown2
import os
from datetime import datetime
import sys

# 尝试导入weasyprint，如果失败则创建替代方案
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
    print("WeasyPrint 可用，将生成PDF报告", file=sys.stderr)
except ImportError as e:
    # WeasyPrint可能由于缺少依赖而无法导入
    print(f"注意: WeasyPrint导入失败 ({e})，将使用HTML替代方案", file=sys.stderr)
except Exception as e:
    # 其他错误，如缺少DLL
    print(f"注意: WeasyPrint初始化失败 ({e})，将使用HTML替代方案", file=sys.stderr)

def generate_pdf_report(markdown_content: str, symbol: str, output_dir: str = "reports") -> str:
    """
    将 Markdown 内容转换为 PDF 报告
    
    Args:
        markdown_content: Markdown 格式的分析报告
        symbol: 股票代码，用于生成文件名
        output_dir: 输出目录（默认为 reports）
        
    Returns:
        生成的 PDF 文件路径（如果weasyprint不可用，则返回HTML文件路径）
    """
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # 将 Markdown 转换为 HTML
    html_content = markdown2.markdown(
        markdown_content,
        extras=["tables", "fenced-code-blocks", "code-friendly"]
    )
    
    # 创建完整的 HTML 文档，包含 CSS 样式
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>A股分析报告 - {symbol}</title>
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
            }}
            
            body {{
                font-family: "Microsoft YaHei", "SimHei", "Source Han Sans CN", sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 12pt;
                max-width: 210mm;
                margin: 0 auto;
                padding: 20mm;
                background-color: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            
            @media print {{
                body {{
                    box-shadow: none;
                    padding: 0;
                }}
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                text-align: center;
            }}
            
            h2 {{
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 10px;
                margin-top: 25px;
            }}
            
            h3 {{
                color: #2c3e50;
                margin-top: 20px;
            }}
            
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 11pt;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px double #3498db;
                padding-bottom: 20px;
            }}
            
            .symbol {{
                color: #e74c3c;
                font-weight: bold;
                font-size: 14pt;
            }}
            
            .timestamp {{
                color: #7f8c8d;
                font-size: 10pt;
                margin-top: 5px;
            }}
            
            .footer {{
                margin-top: 30px;
                padding-top: 10px;
                border-top: 1px solid #ddd;
                font-size: 10pt;
                color: #7f8c8d;
                text-align: center;
            }}
            
            .risk-warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
            
            .recommendation {{
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
            
            code {{
                background-color: #f8f9fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: "Courier New", monospace;
                font-size: 10pt;
            }}
            
            pre {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                font-family: "Courier New", monospace;
                font-size: 10pt;
            }}
            
            ul, ol {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            
            li {{
                margin: 5px 0;
            }}
            
            .print-instruction {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                font-size: 11pt;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>A股金融分析报告</h1>
            <div class="symbol">股票代码: {symbol}</div>
            <div class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <!-- 只在weasyprint不可用时显示打印说明 -->
        {'<div class="print-instruction"><strong>打印说明：</strong> 由于系统环境限制，PDF生成功能不可用。此HTML文件已优化打印格式，请按以下步骤操作：<ol><li>按 <kbd>Ctrl+P</kbd> 打开打印对话框</li><li>选择打印机为 "Microsoft Print to PDF" 或 "另存为PDF"</li><li>设置纸张大小为 A4，边距为 "窄" 或 "无"</li><li>勾选 "背景图形" 选项（确保样式正确）</li><li>点击打印/保存生成PDF文件</li></ol></div>' if not WEASYPRINT_AVAILABLE else ''}
        
        {html_content}
        
        <div class="footer">
            <p>本报告由 A-Share Financial Analyst Agent 生成</p>
            <p>数据来源: Akshare • 分析模型: DeepSeek Chat • 报告仅供参考，不构成投资建议</p>
        </div>
        
        <!-- 只在weasyprint不可用时添加JavaScript -->
        {'''
        <script>
            // 添加打印快捷键提示
            document.addEventListener("keydown", function(e) {
                if (e.ctrlKey && e.key === "p") {
                    e.preventDefault();
                    window.print();
                }
            });
            
            // 页面加载完成后提示打印
            window.addEventListener("load", function() {
                console.log("报告已生成。按 Ctrl+P 打印为PDF。");
            });
        </script>
        ''' if not WEASYPRINT_AVAILABLE else ''}
    </body>
    </html>
    """
    
    # 尝试使用weasyprint生成PDF，如果可用且正常工作
    if WEASYPRINT_AVAILABLE:
        try:
            filename = f"Report_{symbol}_{timestamp}.pdf"
            output_path = os.path.join(output_dir, filename)
            HTML(string=full_html).write_pdf(output_path)
            print(f"PDF报告已生成: {output_path}")
            return output_path
        except Exception as e:
            print(f"警告: WeasyPrint PDF生成失败 ({e})，将保存为HTML文件", file=sys.stderr)
            # 继续执行HTML保存
    
    # 保存为HTML文件（替代方案）
    filename = f"Report_{symbol}_{timestamp}.html"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    # 同时保存原始Markdown
    md_filename = f"Report_{symbol}_{timestamp}.md"
    md_output_path = os.path.join(output_dir, md_filename)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"注意: 由于PDF生成库问题，报告已保存为HTML格式: {output_path}")
    print(f"      原始Markdown文件: {md_output_path}")
    print(f"      您可以打开HTML文件，按Ctrl+P，选择'保存为PDF'来生成PDF版本。")
    
    return output_path
