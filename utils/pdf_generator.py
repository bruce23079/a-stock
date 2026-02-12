import markdown2
import os
from datetime import datetime
import sys
import tempfile

# ================== PDF 引擎检测 ==================
# 按优先级尝试不同的PDF生成引擎
PDF_ENGINES = []

# 1. 尝试 WeasyPrint
WEASYPRINT_AVAILABLE = False
WEASYPRINT_ERROR = None
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
    PDF_ENGINES.append('weasyprint')
    print("✓ WeasyPrint 可用", file=sys.stderr)
except ImportError as e:
    WEASYPRINT_ERROR = f"导入失败: {e}"
except Exception as e:
    WEASYPRINT_ERROR = f"初始化失败: {e}"

# 2. 尝试 pdfkit (需要 wkhtmltopdf)
PDFKIT_AVAILABLE = False
PDFKIT_ERROR = None
try:
    import pdfkit
    # 检查 wkhtmltopdf 是否在 PATH 中
    import subprocess
    try:
        # 尝试查找 wkhtmltopdf
        result = subprocess.run(['wkhtmltopdf', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            PDFKIT_AVAILABLE = True
            PDF_ENGINES.append('pdfkit')
            print("✓ pdfkit + wkhtmltopdf 可用", file=sys.stderr)
        else:
            PDFKIT_ERROR = "wkhtmltopdf 未安装或不在 PATH 中"
    except (FileNotFoundError, subprocess.SubprocessError):
        PDFKIT_ERROR = "wkhtmltopdf 未安装"
except ImportError as e:
    PDFKIT_ERROR = f"pdfkit 库未安装: {e}"
except Exception as e:
    PDFKIT_ERROR = f"pdfkit 初始化失败: {e}"

# 3. 尝试 xhtml2pdf
XHTML2PDF_AVAILABLE = False
XHTML2PDF_ERROR = None
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
    PDF_ENGINES.append('xhtml2pdf')
    print("✓ xhtml2pdf 可用", file=sys.stderr)
except ImportError as e:
    XHTML2PDF_ERROR = f"导入失败: {e}"
except Exception as e:
    XHTML2PDF_ERROR = f"初始化失败: {e}"

# 4. 尝试 fpdf2 (简单PDF生成)
FPDF2_AVAILABLE = False
FPDF2_ERROR = None
try:
    from fpdf import FPDF
    FPDF2_AVAILABLE = True
    PDF_ENGINES.append('fpdf2')
    print("✓ fpdf2 可用", file=sys.stderr)
except ImportError as e:
    FPDF2_ERROR = f"导入失败: {e}"
except Exception as e:
    FPDF2_ERROR = f"初始化失败: {e}"

print(f"可用 PDF 引擎: {PDF_ENGINES if PDF_ENGINES else '无'}", file=sys.stderr)

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
    
    # 尝试使用可用的PDF引擎生成PDF
    pdf_generated = False
    pdf_path = None
    
    # 按优先级尝试各个引擎
    for engine in PDF_ENGINES:
        try:
            if engine == 'weasyprint' and WEASYPRINT_AVAILABLE:
                pdf_path = _generate_with_weasyprint(full_html, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 WeasyPrint 生成PDF: {pdf_path}")
                    break
                    
            elif engine == 'pdfkit' and PDFKIT_AVAILABLE:
                pdf_path = _generate_with_pdfkit(full_html, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 pdfkit 生成PDF: {pdf_path}")
                    break
                    
            elif engine == 'xhtml2pdf' and XHTML2PDF_AVAILABLE:
                pdf_path = _generate_with_xhtml2pdf(full_html, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 xhtml2pdf 生成PDF: {pdf_path}")
                    break
                    
            elif engine == 'fpdf2' and FPDF2_AVAILABLE:
                pdf_path = _generate_with_fpdf2(markdown_content, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 fpdf2 生成PDF: {pdf_path}")
                    break
                    
        except Exception as e:
            print(f"⚠ {engine} 引擎失败: {e}", file=sys.stderr)
            continue
    
    # 如果PDF生成成功，返回PDF路径
    if pdf_generated and pdf_path:
        # 同时保存HTML和Markdown版本作为备份
        _save_html_and_markdown(full_html, markdown_content, symbol, timestamp, output_dir)
        return pdf_path
    
    # PDF生成失败，保存为HTML文件（替代方案）
    return _save_as_html_fallback(full_html, markdown_content, symbol, timestamp, output_dir)

# ================== PDF 引擎实现函数 ==================

def _generate_with_weasyprint(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 WeasyPrint 生成 PDF"""
    from weasyprint import HTML
    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    HTML(string=html_content).write_pdf(output_path)
    return output_path

def _generate_with_pdfkit(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 pdfkit (wkhtmltopdf) 生成 PDF"""
    import pdfkit
    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # 配置选项
    options = {
        'page-size': 'A4',
        'margin-top': '1.5cm',
        'margin-right': '1.5cm',
        'margin-bottom': '1.5cm',
        'margin-left': '1.5cm',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
    }
    
    # 临时保存HTML文件，因为pdfkit需要文件路径
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        temp_html_path = f.name
        f.write(html_content)
    
    try:
        pdfkit.from_file(temp_html_path, output_path, options=options)
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_html_path)
        except:
            pass
    
    return output_path

def _generate_with_xhtml2pdf(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 xhtml2pdf 生成 PDF"""
    from xhtml2pdf import pisa
    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'wb') as f:
        pisa_status = pisa.CreatePDF(html_content, dest=f, encoding='UTF-8')
    
    if pisa_status.err:
        raise Exception(f"xhtml2pdf 生成失败: {pisa_status.err}")
    
    return output_path

def _generate_with_fpdf2(markdown_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 fpdf2 生成简单的 PDF (不支持复杂HTML，使用纯文本)"""
    from fpdf import FPDF
    
    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('SimHei', '', 'simhei.ttf', uni=True)  # 尝试添加中文字体
    pdf.set_font('Arial', '', 12)
    
    # 添加标题
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'A股分析报告 - {symbol}', 0, 1, 'C')
    pdf.ln(10)
    
    # 添加生成时间
    pdf.set_font('Arial', '', 10)
    from datetime import datetime
    pdf.cell(0, 10, f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(10)
    
    # 添加内容（简化版，只添加文本）
    pdf.set_font('Arial', '', 12)
    
    # 将markdown内容转换为纯文本（简单处理）
    lines = markdown_content.split('\n')
    for line in lines[:100]:  # 限制行数
        if line.strip():
            # 移除markdown标记
            clean_line = line.replace('#', '').replace('*', '').replace('`', '')
            if len(clean_line) > 80:
                # 自动换行
                pdf.multi_cell(0, 8, clean_line[:200])  # 限制长度
            else:
                pdf.cell(0, 8, clean_line[:200], 0, 1)
    
    pdf.output(output_path)
    return output_path

def _save_html_and_markdown(html_content: str, markdown_content: str, symbol: str, timestamp: str, output_dir: str):
    """保存HTML和Markdown版本作为备份"""
    # 保存HTML文件
    html_filename = f"Report_{symbol}_{timestamp}.html"
    html_output_path = os.path.join(output_dir, html_filename)
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 保存原始Markdown
    md_filename = f"Report_{symbol}_{timestamp}.md"
    md_output_path = os.path.join(output_dir, md_filename)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"备份文件: {html_output_path}, {md_output_path}")

def _save_as_html_fallback(html_content: str, markdown_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """PDF生成失败时，保存为HTML文件（最终备用方案）"""
    # 保存HTML文件
    html_filename = f"Report_{symbol}_{timestamp}.html"
    html_output_path = os.path.join(output_dir, html_filename)
    
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 同时保存原始Markdown
    md_filename = f"Report_{symbol}_{timestamp}.md"
    md_output_path = os.path.join(output_dir, md_filename)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"⚠ 所有PDF引擎均失败，已保存为HTML格式: {html_output_path}")
    print(f"  原始Markdown文件: {md_output_path}")
    print(f"  您可以打开HTML文件，按Ctrl+P，选择'保存为PDF'来生成PDF版本。")
    
    return html_output_path
