@echo off
chcp 65001 > nul
echo ========================================
echo    CONSTRUYENDO SISTEMA DE RESERVAS
echo    Versión Final - Puerto 9000
echo ========================================
echo.

echo 🔍 Verificando entorno Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado en el PATH
    echo 💡 Asegúrate de que Python esté instalado y en el PATH
    pause
    exit /b 1
)

echo 🗑️  Limpiando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo 📦 Recolectando archivos estáticos...
python manage.py collectstatic --noinput --clear
if errorlevel 1 (
    echo ❌ Error al recolectar static files
    echo 💡 Verifica que Django esté configurado correctamente
    pause
    exit /b 1
)

echo 📁 Verificando carpeta staticfiles...
if not exist "staticfiles" (
    echo ❌ Carpeta staticfiles no encontrada después de collectstatic
    pause
    exit /b 1
)

echo 🏗️  Construyendo ejecutable...
pyinstaller --onedir --name "SistemaReservas" ^
  --add-data "reservations/templates;reservations/templates" ^
  --add-data "staticfiles;staticfiles" ^
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
  --hidden-import django.template.loaders.app_directories ^
  --hidden-import django.contrib.staticfiles.finders ^
  main.py

echo.
echo ========================================
if exist "dist\SistemaReservas\SistemaReservas.exe" (
    echo ✅ BUILD EXITOSO
    echo 📁 Ejecutable: dist\SistemaReservas\SistemaReservas.exe
    echo 📊 Static files: Incluidos ✓ (desde staticfiles)
    echo 🎨 Bootstrap/Icons: Incluidos ✓
    echo 📈 Gráficos: Incluidos ✓
    echo 🌐 Puerto: 9000
    echo 👤 Usuario: admin
    echo 🔑 Contraseña: maXS@sdasd1234
    echo.
    echo 💡 Para distribuir: Copia toda la carpeta 'dist\SistemaReservas'
) else (
    echo ❌ BUILD FALLIDO
    echo 💡 Revisa los mensajes de error arriba
)

echo ========================================
pause