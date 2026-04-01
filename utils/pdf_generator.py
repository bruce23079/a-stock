#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 生成器 - 修复中文字体支持版本
"""

import markdown2
import os
from datetime import datetime
import sys
import tempfile

# ================== PDF 引擎检测 ==================
# 按优先级尝试不同的 PDF 生成引擎
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
    WEASYPRINT_ERROR = f"导入失败：{e}"
except Exception as e:
    WEASYPRINT_ERROR = f"初始化失败：{e}"

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
    PDFKIT_ERROR = f"pdfkit 库未安装：{e}"
except Exception as e:
    PDFKIT_ERROR = f"pdfkit 初始化失败：{e}"

# 3. 尝试 reportlab (直接生成 PDF，支持中文换行) - 优先级高于 xhtml2pdf
REPORTLAB_AVAILABLE = False
REPORTLAB_ERROR = None
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
    PDF_ENGINES.append('reportlab')
    print("✓ reportlab 可用", file=sys.stderr)
except ImportError as e:
    REPORTLAB_ERROR = f"导入失败：{e}"
except Exception as e:
    REPORTLAB_ERROR = f"初始化失败：{e}"

# 4. 尝试 xhtml2pdf
XHTML2PDF_AVAILABLE = False
XHTML2PDF_ERROR = None
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
    PDF_ENGINES.append('xhtml2pdf')
    print("✓ xhtml2pdf 可用", file=sys.stderr)
except ImportError as e:
    XHTML2PDF_ERROR = f"导入失败：{e}"
except Exception as e:
    XHTML2PDF_ERROR = f"初始化失败：{e}"

# 5. 尝试 fpdf2 (简单 PDF 生成)
FPDF2_AVAILABLE = False
FPDF2_ERROR = None
try:
    from fpdf import FPDF
    FPDF2_AVAILABLE = True
    PDF_ENGINES.append('fpdf2')
    print("✓ fpdf2 可用", file=sys.stderr)
except ImportError as e:
    FPDF2_ERROR = f"导入失败：{e}"
except Exception as e:
    FPDF2_ERROR = f"初始化失败：{e}"

print(f"可用 PDF 引擎：{PDF_ENGINES if PDF_ENGINES else '无'}", file=sys.stderr)


def get_chinese_font_paths():
    """
    获取系统中可用的中文字体路径
    优先返回 .ttf 单字体文件，避免 .ttc 字体集合文件的兼容性问题
    """
    import platform
    system = platform.system()
    
    if system == "Windows":
        # Windows 系统常见中文字体路径（优先 .ttf 格式）
        return [
            ("C:/Windows/Fonts/simhei.ttf", "SimHei"),        # 黑体（首选，纯 TTF）
            ("C:/Windows/Fonts/simsunb.ttf", "SimSun"),       # 宋体扩展（TTF 格式）
            ("C:/Windows/Fonts/simfang.ttf", "SimFang"),      # 仿宋体
            ("C:/Windows/Fonts/simkai.ttf", "SimKai"),        # 楷体
            ("C:/Windows/Fonts/SIMYOU.TTF", "SimYou"),        # 幼圆体
            # 以下为 TTC 字体集合文件，作为备选
            ("C:/Windows/Fonts/simsun.ttc", "SimSun"),        # 宋体 TTC
            ("C:/Windows/Fonts/msyh.ttc", "MicrosoftYaHei"),  # 微软雅黑 TTC
            ("C:/Windows/Fonts/msyhl.ttc", "MicrosoftYaHeiLight"),  # 微软雅黑轻
        ]
    elif system == "Darwin":  # macOS
        return [
            ("/System/Library/Fonts/PingFang.ttc", "PingFang SC"),
            ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti"),
        ]
    else:  # Linux
        return [
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYi Zen Hei"),
            ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "Noto Sans CJK"),
        ]


def generate_pdf_report(markdown_content: str, symbol: str, output_dir: str = "reports") -> str:
    """
    将 Markdown 内容转换为 PDF 报告

    Args:
        markdown_content: Markdown 格式的分析报告
        symbol: 股票代码，用于生成文件名
        output_dir: 输出目录（默认为 reports）

    Returns:
        生成的 PDF 文件路径（如果 weasyprint 不可用，则返回 HTML 文件路径）
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
    full_html = create_full_html(html_content, symbol)

    # 尝试使用可用的 PDF 引擎生成 PDF
    pdf_generated = False
    pdf_path = None

    # 按优先级尝试各个引擎
    for engine in PDF_ENGINES:
        try:
            if engine == 'weasyprint' and WEASYPRINT_AVAILABLE:
                pdf_path = _generate_with_weasyprint(full_html, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 WeasyPrint 生成 PDF: {pdf_path}")
                    break

            elif engine == 'pdfkit' and PDFKIT_AVAILABLE:
                pdf_path = _generate_with_pdfkit(full_html, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 pdfkit 生成 PDF: {pdf_path}")
                    break

            elif engine == 'reportlab' and REPORTLAB_AVAILABLE:
                print(f"  尝试使用 reportlab 引擎...")
                pdf_path = _generate_with_reportlab(markdown_content, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 reportlab 生成 PDF: {pdf_path}")
                    break
                else:
                    print(f"  reportlab 返回空路径，继续尝试其他引擎")

            elif engine == 'xhtml2pdf' and XHTML2PDF_AVAILABLE:
                print(f"  尝试使用 xhtml2pdf 引擎...")
                pdf_path = _generate_with_xhtml2pdf(full_html, symbol, timestamp, output_dir)
                print(f"  _generate_with_xhtml2pdf 返回：{pdf_path}")
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 xhtml2pdf 生成 PDF: {pdf_path}")
                    break
                else:
                    print(f"  xhtml2pdf 返回空路径，继续尝试其他引擎")

            elif engine == 'fpdf2' and FPDF2_AVAILABLE:
                pdf_path = _generate_with_fpdf2(markdown_content, symbol, timestamp, output_dir)
                if pdf_path:
                    pdf_generated = True
                    print(f"✓ 使用 fpdf2 生成 PDF: {pdf_path}")
                    break

        except Exception as e:
            print(f"⚠ {engine} 引擎失败：{e}", file=sys.stderr)
            continue

    # 如果 PDF 生成成功，返回 PDF 路径
    if pdf_generated and pdf_path:
        # 同时保存 HTML 和 Markdown 版本作为备份
        _save_html_and_markdown(full_html, markdown_content, symbol, timestamp, output_dir)
        return pdf_path

    # PDF 生成失败，保存为 HTML 文件（替代方案）
    return _save_as_html_fallback(full_html, markdown_content, symbol, timestamp, output_dir)


def create_full_html(html_content: str, symbol: str) -> str:
    """创建完整的 HTML 文档"""
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 获取可用的中文字体
    font_paths = get_chinese_font_paths()
    available_fonts = []
    font_face_css = ""
    
    for font_path, font_name in font_paths:
        if os.path.exists(font_path):
            if font_name not in available_fonts:
                available_fonts.append(font_name)
                font_face_css += f'''
            @font-face {{
                font-family: "{font_name}";
                src: url("file:///{font_path.replace(chr(92), '/')}");
            }}'''
    
    # 如果没有找到系统字体，使用默认中文字体名称
    if not available_fonts:
        available_fonts = ["SimHei", "Microsoft YaHei", "SimSun", "sans-serif"]

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>A 股分析报告 - {symbol}</title>
        <style>
            {font_face_css}

            @page {{
                size: A4;
                margin: 1.5cm;
            }}

            /* 优先使用系统中文字体，确保中文正确显示 */
            body {{
                font-family: {', '.join([f'"{f}"' for f in available_fonts])}, sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 12pt;
                max-width: 210mm;
                margin: 0 auto;
                padding: 20mm;
                background-color: white;
                /* 文本自动换行，防止长文本溢出 */
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
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
                /* 标题也需换行 */
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}

            h2 {{
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 10px;
                margin-top: 25px;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}

            h3 {{
                color: #2c3e50;
                margin-top: 20px;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}

            p {{
                margin: 10px 0;
                text-align: justify;
                /* 段落文本自动换行 */
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: pre-wrap;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 11pt;
                /* 表格自动换行 */
                table-layout: fixed;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                /* 单元格文本自动换行 */
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
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
            <h1>A 股金融分析报告</h1>
            <div class="symbol">股票代码：{symbol}</div>
            <div class="timestamp">生成时间：{timestamp_str}</div>
        </div>

        {html_content}

        <div class="footer">
            <p>本报告由 A-Share Financial Analyst Agent 生成</p>
            <p>数据来源：Akshare • 分析模型：DeepSeek Chat • 报告仅供参考，不构成投资建议</p>
        </div>
    </body>
    </html>
    """
    return full_html


# ================== PDF 引擎实现函数 ==================

def _generate_with_weasyprint(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 WeasyPrint 生成 PDF（修复中文字体支持）"""
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    # 配置中文字体
    font_config = FontConfiguration()
    
    # 获取可用的中文字体路径
    font_paths = get_chinese_font_paths()

    # 构建 CSS 字体规则 - 只使用实际存在的字体文件
    font_face_css = ""
    available_fonts = []

    for font_path, font_name in font_paths:
        if os.path.exists(font_path):
            # 避免重复添加相同字体名称
            if font_name not in available_fonts:
                font_face_css += f'''
                @font-face {{
                    font-family: "{font_name}";
                    src: url("file:///{font_path.replace(chr(92), '/')}");
                }}
                '''
                available_fonts.append(font_name)

    # 如果没有找到系统字体，使用系统默认中文字体名称（依赖系统字体缓存）
    if not available_fonts:
        available_fonts = ["SimHei", "Microsoft YaHei", "SimSun", "sans-serif"]

    # 构建完整的 CSS 样式，强制使用可用的中文字体
    css_string = f'''
    {font_face_css}

    @page {{
        size: A4;
        margin: 1.5cm;
    }}

    * {{
        font-family: {', '.join([f'"{f}"' for f in available_fonts])}, sans-serif !important;
    }}

    body {{
        font-family: {', '.join([f'"{f}"' for f in available_fonts])}, sans-serif !important;
        line-height: 1.6;
        color: #333;
        font-size: 12pt;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: {', '.join([f'"{f}"' for f in available_fonts])}, sans-serif !important;
    }}

    p, span, div, td, th, li, table, code, pre {{
        font-family: {', '.join([f'"{f}"' for f in available_fonts])}, sans-serif !important;
    }}
    '''

    # 创建 HTML 文档
    html_doc = HTML(string=html_content)
    css_doc = CSS(string=css_string, font_config=font_config)

    # 生成 PDF，传入字体配置
    html_doc.write_pdf(output_path, stylesheets=[css_doc], font_config=font_config)

    print(f"  WeasyPrint 使用字体：{available_fonts[:3]}")
    return output_path


def _generate_with_pdfkit(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 pdfkit (wkhtmltopdf) 生成 PDF"""
    import pdfkit

    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    # 检测系统并获取中文字体路径
    font_paths = get_chinese_font_paths()
    font_path = ""
    
    # 查找第一个存在的字体
    for path, _ in font_paths:
        if os.path.exists(path):
            font_path = path
            break

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
        # 中文字体支持 - 使用系统字体
        'font-family': '"SimHei", "Microsoft YaHei", "SimSun", sans-serif',
        'print-media-type': None,  # 使用打印媒体类型
        'disable-smart-shrinking': None,  # 禁用智能缩放
        'dpi': 300,  # 高分辨率
    }

    # 如果找到系统字体，添加到选项中
    if font_path:
        options['font'] = font_path

    # 临时保存 HTML 文件，因为 pdfkit 需要文件路径
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

    if font_path:
        print(f"  pdfkit 使用字体：{font_path}")
    return output_path


def _generate_with_xhtml2pdf(html_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 xhtml2pdf 生成 PDF（修复中文字体支持）"""
    from xhtml2pdf import pisa
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import xhtml2pdf.default as default
    import re

    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    # 1. 修改 xhtml2pdf 的默认字体映射，添加中文字体
    # 这样 CSS 中使用这些字体名称时，xhtml2pdf 才能正确识别
    chinese_font_aliases = {
        'simhei': 'SimHei',
        'simsun': 'SimSun',
        'microsoftyahei': 'SimHei',  # 微软雅黑映射到 SimHei
        'msyahei': 'SimHei',
        'simsunbcs': 'SimSun',
        'chinese': 'SimHei',
        'zh': 'SimHei',
        'cn': 'SimHei',
    }
    for alias, real_name in chinese_font_aliases.items():
        default.DEFAULT_FONT[alias] = real_name
    print(f"  已添加中文字体映射：{list(chinese_font_aliases.keys())}")

    # 2. 注册中文字体到 reportlab（使用实际存在的字体文件）
    # 优先使用 .ttf 单字体文件，避免 .ttc 字体集合文件的兼容性问题
    font_paths = get_chinese_font_paths()
    
    registered_fonts = []
    for path, name in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                if name not in registered_fonts:
                    registered_fonts.append(name)
                    print(f"  注册字体：{name} (路径：{path})")
            except Exception as e:
                print(f"  注册字体失败 {name}: {e}")

    if not registered_fonts:
        # 尝试使用报告实验室内置的中文字体支持
        print("  警告：未找到系统中文字体文件，尝试使用内置字体...")
        # xhtml2pdf 有内置的中文字体支持，通过 DEFAULT_FONT 映射
        registered_fonts = ["SimHei"]  # 假设备用字体

    # 3. 确定 CSS 字体族 - 使用注册成功的字体名称（保持大小写一致）
    # xhtml2pdf 在 CSS 中使用字体名称时，会查找 DEFAULT_FONT 映射或已注册的字体
    if "SimHei" in registered_fonts:
        # 使用小写名称匹配 DEFAULT_FONT 映射，同时提供大写作为备选
        css_font_family = 'simhei, SimHei, sans-serif'
    elif "SimSun" in registered_fonts:
        css_font_family = 'simsun, SimSun, sans-serif'
    elif "MicrosoftYaHei" in registered_fonts:
        css_font_family = 'MicrosoftYaHei, sans-serif'
    else:
        css_font_family = 'SimHei, sans-serif'

    # 4. 清理旧的 @font-face 声明（如果有），避免冲突
    # 移除所有 @font-face 块
    html_content = re.sub(r'@font-face\s*\{[^}]*\}', '', html_content)
    print(f"  已移除旧的 @font-face 声明")

    # 5. 添加新的 CSS 样式，强制使用中文字体和自动换行
    font_css = f'''<style>
        body, div, p, h1, h2, h3, h4, h5, h6, li, td, th, span, a, table, code, pre {{
            font-family: {css_font_family} !important;
            /* 文本自动换行，防止长文本溢出 */
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: normal;
        }}
        p {{
            white-space: pre-wrap;
        }}
        table {{
            table-layout: fixed;
        }}
    </style>'''
    
    # 插入到 </head> 之前，确保覆盖之前的样式
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', f'{font_css}</head>')
    elif '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>{font_css}')
    else:
        html_content = font_css + html_content
    print(f"  使用字体：{css_font_family}")

    # 6. (调试) 保存修改后的 HTML 用于检查
    debug_html_path = output_path.replace('.pdf', '_debug.html')
    with open(debug_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  调试：保存 HTML 到 {debug_html_path}")

    # 7. 生成 PDF
    print(f"  生成 PDF: {output_path}")
    with open(output_path, 'wb') as f:
        pisa_status = pisa.CreatePDF(src=html_content, dest=f, encoding='utf-8')

    # 8. 验证
    if not os.path.exists(output_path):
        raise Exception("PDF 文件未创建")
    size = os.path.getsize(output_path)
    if size < 100:
        raise Exception(f"PDF 文件太小：{size} bytes")
    
    if pisa_status.err:
        print(f"  [WARNING] pisa_status.err={pisa_status.err}, 但文件已生成")
    print(f"  [OK] 成功 ({size} bytes)")

    return output_path


def _generate_with_fpdf2(markdown_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 fpdf2 生成简单的 PDF (不支持复杂 HTML，使用纯文本)"""
    from fpdf import FPDF

    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    pdf = FPDF()
    pdf.add_page()
    
    # 尝试添加中文字体
    font_paths = get_chinese_font_paths()
    font_added = False
    
    for font_path, font_name in font_paths:
        if os.path.exists(font_path):
            try:
                pdf.add_font(font_name, '', font_path, uni=True)
                pdf.set_font(font_name, '', 12)
                font_added = True
                print(f"  fpdf2 使用字体：{font_name}")
                break
            except Exception as e:
                print(f"  添加字体失败 {font_name}: {e}")
                continue
    
    if not font_added:
        pdf.set_font('Arial', '', 12)
        print("  fpdf2 使用默认字体（可能不支持中文）")

    # 添加标题
    pdf.set_font(pdf.font_name if hasattr(pdf, 'font_name') else 'Arial', 'B', 16)
    pdf.cell(0, 10, f'A 股分析报告 - {symbol}', 0, 1, 'C')
    pdf.ln(10)

    # 添加生成时间
    pdf.set_font(pdf.font_name if hasattr(pdf, 'font_name') else 'Arial', '', 10)
    pdf.cell(0, 10, f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(10)

    # 添加内容（简化版，只添加文本）
    pdf.set_font(pdf.font_name if hasattr(pdf, 'font_name') else 'Arial', '', 12)

    # 将 markdown 内容转换为纯文本（简单处理）
    lines = markdown_content.split('\n')
    for line in lines[:100]:  # 限制行数
        if line.strip():
            # 移除 markdown 标记
            clean_line = line.replace('#', '').replace('*', '').replace('`', '')
            if len(clean_line) > 80:
                # 自动换行
                pdf.multi_cell(0, 8, clean_line[:200])  # 限制长度
            else:
                pdf.cell(0, 8, clean_line[:200], 0, 1)

    pdf.output(output_path)
    return output_path


def _generate_with_reportlab(markdown_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """使用 reportlab 生成 PDF（支持中文和自动换行）"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    filename = f"Report_{symbol}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # 创建 PDF 文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"A 股分析报告 - {symbol}"
    )
    
    # 注册中文字体
    font_paths = get_chinese_font_paths()
    registered_fonts = []
    
    for path, name in font_paths:
        if os.path.exists(path) and name not in registered_fonts:
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered_fonts.append(name)
                print(f"  reportlab 注册字体：{name}")
            except Exception as e:
                print(f"  注册字体失败 {name}: {e}")
    
    if not registered_fonts:
        raise Exception("未找到中文字体文件")
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 定义中文字体样式
    font_name = registered_fonts[0]  # 使用第一个注册的字体
    
    # 标题样式
    title_style = ParagraphStyle(
        name='ChineseTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=1,  # 居中
        spaceAfter=20,
        wordWrap='CJK'  # 中文换行
    )
    
    # 一级标题样式
    heading1_style = ParagraphStyle(
        name='ChineseHeading1',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceAfter=12,
        spaceBefore=20,
        wordWrap='CJK'
    )
    
    # 二级标题样式
    heading2_style = ParagraphStyle(
        name='ChineseHeading2',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceAfter=10,
        spaceBefore=15,
        wordWrap='CJK'
    )
    
    # 三级标题样式
    heading3_style = ParagraphStyle(
        name='ChineseHeading3',
        parent=styles['Heading4'],
        fontName=font_name,
        fontSize=12,
        leading=16,
        spaceAfter=8,
        spaceBefore=12,
        wordWrap='CJK'
    )
    
    # 正文样式
    normal_style = ParagraphStyle(
        name='ChineseNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=8,
        wordWrap='CJK',
        allowWidows=0,
        allowOrphans=0
    )
    
    # 表格单元格样式
    table_cell_style = ParagraphStyle(
        name='ChineseTableCell',
        parent=normal_style,
        fontSize=10,
        leading=14,
        wordWrap='CJK'
    )
    
    # 构建 PDF 内容
    story = []
    
    # 标题
    story.append(Paragraph(f"A 股分析报告 - 股票代码：{symbol}", title_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 生成时间
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 解析 Markdown 内容
    lines = markdown_content.split('\n')
    in_table = False
    table_data = []
    current_list = []
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行
        if not stripped:
            if in_table and table_data:
                # 添加表格
                table = Table(table_data, colWidths=[doc.width/len(table_data[0])] * len(table_data[0]))
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.3*cm))
                table_data = []
                in_table = False
            if current_list:
                # 添加列表
                for item in current_list:
                    story.append(Paragraph(f"• {item}", normal_style))
                story.append(Spacer(1, 0.2*cm))
                current_list = []
            continue
        
        # 检测标题
        if stripped.startswith('# '):
            story.append(Paragraph(stripped[2:], heading1_style))
        elif stripped.startswith('## '):
            story.append(Paragraph(stripped[3:], heading2_style))
        elif stripped.startswith('### '):
            story.append(Paragraph(stripped[4:], heading3_style))
        
        # 检测表格开始
        elif '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            in_table = True
            row_data = [cell.strip() for cell in stripped.split('|')[1:-1]]
            # 跳过分隔符行（如 |---|---|）
            if not all(cell.replace('-', '').replace(':', '') == '' for cell in row_data):
                table_data.append([Paragraph(cell, table_cell_style) for cell in row_data])
        
        # 检测列表项
        elif stripped.startswith('- '):
            current_list.append(stripped[2:])
        
        # 普通段落
        else:
            # 如果之前在表格中，先结束表格
            if in_table and table_data:
                table = Table(table_data, colWidths=[doc.width/max(len(table_data[0]), 1)] * max(len(table_data[0]), 1))
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.3*cm))
                table_data = []
                in_table = False
            
            # 处理粗体和强调文本
            text = stripped
            text = text.replace('**', '').replace('*', '')
            story.append(Paragraph(text, normal_style))
    
    # 处理剩余的表格
    if in_table and table_data:
        table = Table(table_data, colWidths=[doc.width/max(len(table_data[0]), 1)] * max(len(table_data[0]), 1))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        story.append(table)
    
    # 添加页脚
    story.append(PageBreak())
    footer_style = ParagraphStyle(
        name='ChineseFooter',
        parent=normal_style,
        fontSize=9,
        alignment=1,
        textColor=colors.grey
    )
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("本报告由 A-Share Financial Analyst Agent 生成", footer_style))
    story.append(Paragraph("数据来源：Akshare • 分析模型：DeepSeek Chat • 报告仅供参考，不构成投资建议", footer_style))
    
    # 构建 PDF
    doc.build(story)
    
    # 验证
    if not os.path.exists(output_path):
        raise Exception("PDF 文件未创建")
    size = os.path.getsize(output_path)
    print(f"  reportlab [OK] 成功 ({size} bytes)")
    
    return output_path


def _save_html_and_markdown(html_content: str, markdown_content: str, symbol: str, timestamp: str, output_dir: str):
    """保存 HTML 和 Markdown 版本作为备份"""
    # 保存 HTML 文件
    html_filename = f"Report_{symbol}_{timestamp}.html"
    html_output_path = os.path.join(output_dir, html_filename)
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 保存原始 Markdown
    md_filename = f"Report_{symbol}_{timestamp}.md"
    md_output_path = os.path.join(output_dir, md_filename)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"备份文件：{html_output_path}, {md_output_path}")


def _save_as_html_fallback(html_content: str, markdown_content: str, symbol: str, timestamp: str, output_dir: str) -> str:
    """PDF 生成失败时，保存为 HTML 文件（最终备用方案）"""
    # 保存 HTML 文件
    html_filename = f"Report_{symbol}_{timestamp}.html"
    html_output_path = os.path.join(output_dir, html_filename)

    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 同时保存原始 Markdown
    md_filename = f"Report_{symbol}_{timestamp}.md"
    md_output_path = os.path.join(output_dir, md_filename)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"⚠ 所有 PDF 引擎均失败，已保存为 HTML 格式：{html_output_path}")
    print(f"  原始 Markdown 文件：{md_output_path}")
    print(f"  您可以打开 HTML 文件，按 Ctrl+P，选择'保存为 PDF'来生成 PDF 版本。")

    return html_output_path
