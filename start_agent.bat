@echo off
echo ================================================
echo A股金融分析智能体 - Windows启动脚本
echo ================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python。请安装Python 3.10+ 并确保已添加到PATH。
    echo 请访问 https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查venv目录是否存在
if exist venv (
    echo 激活现有虚拟环境...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo 错误: 无法激活虚拟环境。
        pause
        exit /b 1
    )
    echo 虚拟环境已激活。
    echo 安装/更新依赖包...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo 警告: 依赖安装失败，但继续运行...
    )
) else (
    echo 创建新的虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 无法创建虚拟环境。
        pause
        exit /b 1
    )
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo 错误: 无法激活虚拟环境。
        pause
        exit /b 1
    )
    echo 安装依赖包...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo 警告: 依赖安装失败，但继续运行...
    )
    echo 虚拟环境设置完成。
)

echo.
echo ================================================
echo 启动A股金融分析智能体...
echo ================================================
echo.

:: 运行主程序
python main.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo 程序执行失败，请检查以上错误信息。
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo 程序执行完成。
echo ================================================
pause
