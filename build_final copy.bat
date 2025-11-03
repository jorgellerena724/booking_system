@echo off
chcp 65001 > nul
echo ========================================
echo    CONSTRUYENDO SISTEMA DE RESERVAS
echo    Versión Final - Puerto 9000
echo ========================================
echo.

echo 🗑️  Limpiando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del SistemaReservas.spec 2>nul

echo 🏗️  Construyendo ejecutable...
pyinstaller --onedir --name "SistemaReservas" ^
  --add-data "reservations/templates;reservations/templates" ^
  --add-data "db.sqlite3;." ^
  --add-data "reservations/migrations;reservations/migrations" ^
  --collect-all reportlab ^
  --collect-all xhtml2pdf ^
  --collect-all django ^
  --collect-all reservations ^
  --collect-all pandas ^
  --collect-all openpyxl ^
  --hidden-import asgiref ^
  --hidden-import sqlite3 ^
  main.py

echo.
echo ========================================
if exist "dist\SistemaReservas\SistemaReservas.exe" (
    echo ✅ BUILD EXITOSO
    echo 📁 Ejecutable: dist\SistemaReservas\SistemaReservas.exe
    echo 🌐 Puerto: 9000
    echo 👤 Usuario: admin
    echo 🔑 Contraseña: maXS@sdasd1234
) else (
    echo ❌ BUILD FALLIDO
    echo 💡 Revisa los mensajes de error arriba
)

echo ========================================
pause