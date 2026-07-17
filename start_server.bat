@echo off
cd /d C:\Users\wangh\tcms
set NO_PROXY=*

:loop
echo [%date% %time%] TCMS 服务器启动...
python\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
echo [%date% %time%] 服务器意外停止，5秒后重启...
timeout /t 5 /nobreak
goto loop
