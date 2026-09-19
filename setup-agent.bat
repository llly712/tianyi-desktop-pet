@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  Tianyi Pet - Agent 运行环境安装 (Open Interpreter)
echo ============================================
where py >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python 启动器 py，请先安装 Python 3.12 并勾选 Add Python to PATH。
  pause
  exit /b 1
)

echo [1/4] 创建虚拟环境 .venv-agent ...
py -3.12 -m venv .venv-agent
if errorlevel 1 (
  echo [错误] 创建虚拟环境失败。
  pause
  exit /b 1
)

echo [2/4] 安装依赖 ...
".venv-agent\Scripts\python.exe" -m pip install --upgrade pip
".venv-agent\Scripts\python.exe" -m pip install -r requirements-agent.txt
if errorlevel 1 (
  echo [错误] 依赖安装失败。
  pause
  exit /b 1
)

echo [3/4] 安装 Open Interpreter ...
".venv-agent\Scripts\python.exe" -m pip install --no-deps open-interpreter==0.4.3
if errorlevel 1 (
  echo [错误] Open Interpreter 安装失败。
  pause
  exit /b 1
)

echo [4/4] 安装 setuptools ...
".venv-agent\Scripts\python.exe" -m pip install "setuptools<81"

echo.
echo 完成！重启桌宠即可使用 "agent: 你的任务"。
pause
