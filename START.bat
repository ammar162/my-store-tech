@echo off
echo.
echo  ╔══════════════════════════════════╗
echo  ║     AM05 TECH — Demarrage       ║
echo  ╚══════════════════════════════════╝
echo.
echo  Installation des dependances...
pip install flask flask-socketio flask-cors eventlet qrcode pillow requests -q
echo.
echo  Lancement du serveur...
echo  Ouvre: http://localhost:5000
echo.
python app.py
pause
