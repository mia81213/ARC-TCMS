@echo off
cd /d C:\Users\wangh\tcms
set NO_PROXY=*

echo ========================================
echo   TCMS 公网访问服务
echo ========================================

:start_uvicorn
echo [%time%] 启动本地服务器...
start "TCMS-Server" /min python\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak

:start_tunnel
echo [%time%] 启动公网隧道...
npx --yes localtunnel --port 8000 --subdomain tcms-carplay > C:\Users\wangh\tcms\tunnel_url.txt 2>&1

echo [%time%] 隧道断开，10秒后重连...
timeout /t 10 /nobreak
goto start_tunnel
