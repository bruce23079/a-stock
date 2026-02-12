#!/bin/bash

echo "================================================="
echo "A股金融分析智能体 - Linux启动脚本"
echo "================================================="
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python 3。请安装Python 3.10+ 并确保已添加到PATH。"
    echo "请使用包管理器安装，例如:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  CentOS/RHEL/Fedora: sudo yum install python3 python3-pip"
    echo "  Arch Linux: sudo pacman -S python python-pip"
    exit 1
fi

# 检查venv目录是否存在
if [ -d "venv" ]; then
    echo "激活现有虚拟环境..."
    source venv/bin/activate
    
    if [ $? -ne 0 ]; then
        echo "错误: 无法激活虚拟环境。"
        exit 1
    fi
    echo "虚拟环境已激活。"
else
    echo "创建新的虚拟环境..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "错误: 无法创建虚拟环境。"
        exit 1
    fi
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    if [ $? -ne 0 ]; then
        echo "错误: 无法激活虚拟环境。"
        exit 1
    fi
    
    echo "安装依赖包..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if [ $? -ne 0 ]; then
        echo "警告: 依赖安装失败，但继续运行..."
    fi
    echo "虚拟环境设置完成。"
fi

echo
echo "================================================="
echo "启动A股金融分析智能体..."
echo "================================================="
echo

# 运行主程序
python3 main.py

if [ $? -ne 0 ]; then
    echo
    echo "================================================="
    echo "程序执行失败，请检查以上错误信息。"
    echo "================================================="
    exit 1
fi

echo
echo "================================================="
echo "程序执行完成。"
echo "================================================="
