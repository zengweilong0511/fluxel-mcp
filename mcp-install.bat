@echo off
chcp 65001 >nul
title ApiCargo MCP Server 安装程序
echo.
echo ============================================
echo   🦀 ApiCargo MCP Server 一键安�?echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  需要管理员权限，正在重新启�?..
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 设置变量
set MCP_DIR=%USERPROFILE%\.ApiCargo\mcp
set OPENCLAW_DIR=%USERPROFILE%\.openclaw
set TOKEN_FILE=%TEMP%\ApiCargo_token.txt

echo 📁 安装目录: %MCP_DIR%
echo.

:: 步骤 1: 检�?Python
echo 🔍 检�?Python 安装...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo �?未检测到 Python�?    echo.
    echo 请先安装 Python 3.10+:
    echo https://python.org/downloads
    echo.
    echo 安装时请务必勾�?"Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo �?Python 已安�?
:: 步骤 2: 创建目录
echo.
echo 📂 创建安装目录...
if not exist "%MCP_DIR%" mkdir "%MCP_DIR%"
if not exist "%OPENCLAW_DIR%" mkdir "%OPENCLAW_DIR%"
echo �?目录创建完成

:: 步骤 3: 下载 MCP Server
echo.
echo 📥 下载 ApiCargo MCP Server...
cd /d "%MCP_DIR%"

:: 使用 PowerShell 下载
echo 正在�?GitHub 下载...

:: ==========================================
:: TODO: 修改下面�?GitHub 用户�?:: ==========================================
set GITHUB_USER=zengweilong0511
:: ==========================================

powershell -Command "Invoke-WebRequest -Uri 'https://github.com/%GITHUB_USER%/apicargo/archive/refs/heads/main.zip' -OutFile 'apicargo.zip'" 2>nul

if exist "apicargo.zip" (
    echo �?下载完成
    echo 📦 解压文件...
    powershell -Command "Expand-Archive -Path 'apicargo.zip' -DestinationPath '.' -Force"
    xcopy /E /I /Y "apicargo-main\*" "." >nul
    rmdir /S /Q "apicargo-main" 2>nul
    del "apicargo.zip" 2>nul
    echo �?解压完成
) else (
    echo ⚠️  下载失败，使用备用方�?..
    echo 请手动下载并解压�? %MCP_DIR%
    echo https://github.com/%GITHUB_USER%/apicargo
    pause
    exit /b 1
)

:: 步骤 4: 安装依赖
echo.
echo 📦 安装 Python 依赖...
pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo �?依赖安装失败
    pause
    exit /b 1
)
echo �?依赖安装完成

:: 步骤 5: 获取 Token
echo.
echo 🔑 配置 Token...
echo.
echo 请打开 ApiCargo，按以下步骤获取 Token�?echo   1. 打开 ApiCargo 窗口
echo   2. 点击顶部菜单 "设置"
echo   3. 选择 "管理 API" 选项�?echo   4. 点击 "复制 Token" 按钮
echo.
set /p TOKEN="请粘�?Token 后按回车: "

if "%TOKEN%"=="" (
    echo �?Token 不能为空�?    pause
    exit /b 1
)

:: 验证 Token 格式
if not "%TOKEN:~0,4%"=="flx_" (
    echo ⚠️  Token 格式不正确，应以 flx_ 开�?    echo 请重新运行安装程�?    pause
    exit /b 1
)

echo �?Token 已接�?
:: 步骤 6: 创建配置文件
echo.
echo 📝 创建 OpenClaw 配置...

:: 转义路径中的反斜�?set MCP_PATH=%MCP_DIR%\server.py
set MCP_PATH=%MCP_PATH:\=\\%

(
echo {
echo   "mcpServers": {
echo     "ApiCargo": {
echo       "command": "python",
echo       "args": [
echo         "%MCP_PATH%"
echo       ],
echo       "env": {
echo         "ApiCargo_API_BASE": "http://localhost:8082",
echo         "ApiCargo_ADMIN_TOKEN": "%TOKEN%"
echo       }
echo     }
echo   }
echo }
) > "%OPENCLAW_DIR%\mcp.json"

echo �?配置文件已创�? %OPENCLAW_DIR%\mcp.json

:: 步骤 7: 创建启动脚本
echo.
echo 🚀 创建启动脚本...

(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%MCP_DIR%"
echo set ApiCargo_API_BASE=http://localhost:8082
echo set ApiCargo_ADMIN_TOKEN=%TOKEN%
echo start /b pythonw server.py
echo exit
) > "%MCP_DIR%\start.bat"

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run chr^(34^) ^& "%MCP_DIR%\start.bat" ^& Chr^(34^), 0
echo Set WshShell = Nothing
) > "%MCP_DIR%\start.vbs"

echo �?启动脚本已创�?
:: 步骤 8: 创建管理脚本
echo.
echo 🛠�? 创建管理工具...

(
echo # ApiCargo MCP 管理脚本
echo param^([string]$Action = "status"^)
echo.
echo $Port = 3000
echo.
echo function Get-ServerProcess ^{
echo     try ^{
echo         $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
echo         return Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
echo     } catch ^{
echo         return $null
echo     }
echo }
echo.
echo if ^($Action -eq "status"^) ^{
echo     $p = Get-ServerProcess
echo     if ^($p^) ^{
echo         Write-Host "[OK] MCP Server 运行�?(PID: $($p.Id))" -ForegroundColor Green
echo     } else ^{
echo         Write-Host "[STOPPED] MCP Server 未运�? -ForegroundColor Red
echo     }
echo }
echo elseif ^($Action -eq "start"^) ^{
echo     $p = Get-ServerProcess
echo     if ^($p^) ^{
echo         Write-Host "[WARN] 已在运行 (PID: $($p.Id))"
echo     } else ^{
echo         Start-Process wscript -ArgumentList "`"%MCP_DIR%\start.vbs`"" -WindowStyle Hidden
echo         Start-Sleep 2
echo         $p = Get-ServerProcess
echo         if ^($p^) ^{
echo             Write-Host "[OK] 已启�?(PID: $($p.Id))" -ForegroundColor Green
        } else {
            Write-Host "[ERR] 启动失败" -ForegroundColor Red
        }
    }
}
elseif ($Action -eq "stop") {
    $p = Get-ServerProcess
    if ($p) {
        Stop-Process -Id $p.Id -Force
        Write-Host "[OK] 已停�? -ForegroundColor Green
    } else {
        Write-Host "[WARN] 未运�?
    }
}
elseif ($Action -eq "restart") {
    & $PSCommandPath -Action stop
    Start-Sleep 1
    & $PSCommandPath -Action start
}
) > "%MCP_DIR%\mcp.ps1"

echo �?管理工具已创�?
:: 步骤 9: 添加到开机启动（可选）
echo.
echo 💡 是否添加到开机启动？
set /p AUTO_START="输入 Y 添加，N 跳过 (Y/N): "

if /I "%AUTO_START%"=="Y" (
    echo 正在添加开机启�?..
    copy "%MCP_DIR%\start.vbs" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\" >nul
    echo �?已添加到开机启�?) else (
    echo ⏭️  跳过开机启�?)

:: 步骤 10: 启动 MCP Server
echo.
echo 🚀 启动 ApiCargo MCP Server...
cd /d "%MCP_DIR%"
start /b pythonw server.py

timeout /t 2 /nobreak >nul

:: 检查是否启动成�?netstat -ano | findstr ":3000" >nul
if %errorLevel% equ 0 (
    echo �?MCP Server 启动成功�?) else (
    echo ⚠️  可能启动失败，请手动运行 start.bat
)

:: 完成
echo.
echo ============================================
echo   🎉 安装完成�?echo ============================================
echo.
echo 下一步：
echo   1. 完全关闭 OpenClaw
echo   2. 重新打开 OpenClaw
echo   3. �?AI �? "帮我看看 ApiCargo 里有哪些服务�?
echo.
echo 常用命令�?echo   查看状�? 双击 mcp.ps1
echo   启动:     powershell -File mcp.ps1 -Action start
echo   停止:     powershell -File mcp.ps1 -Action stop
echo   重启:     powershell -File mcp.ps1 -Action restart
echo.
echo 安装目录: %MCP_DIR%
echo 配置文件: %OPENCLAW_DIR%\mcp.json
echo.
echo 遇到问题�?echo   📖 文档: https://docs.ApiCargo.io/mcp
echo   💬 客服: ApiCargoHelper
echo.
pause
