#!/bin/bash

echo "========================================"
echo "   CONSTRUYENDO SISTEMA DE RESERVAS"
echo "   Versión Final - Puerto 9000"
echo "========================================"
echo ""

echo "🔍 Verificando entorno Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    echo "💡 Instala Python3: sudo dnf install python3"
    exit 1
fi

echo "🗑️  Limpiando builds anteriores..."
rm -rf build dist 2>/dev/null

echo "📦 Recolectando archivos estáticos..."
python3 manage.py collectstatic --noinput --clear
if [ $? -ne 0 ]; then
    echo "❌ Error al recolectar static files"
    echo "💡 Verifica que Django esté configurado correctamente"
    exit 1
fi

echo "📁 Verificando carpeta staticfiles..."
if [ ! -d "staticfiles" ]; then
    echo "❌ Carpeta staticfiles no encontrada después de collectstatic"
    exit 1
fi

echo "🏗️  Construyendo ejecutable..."
pyinstaller --onedir --name "SistemaReservas" \
  --add-data "reservations/templates:reservations/templates" \
  --add-data "staticfiles:staticfiles" \
  --add-data "db.sqlite3:." \
  --add-data "reservations/migrations:reservations/migrations" \
  --collect-all reportlab \
  --collect-all xhtml2pdf \
  --collect-all django \
  --collect-all reservations \
  --collect-all pandas \
  --collect-all openpyxl \
  --hidden-import asgiref \
  --hidden-import sqlite3 \
  --hidden-import django.template.loaders.app_directories \
  --hidden-import django.contrib.staticfiles.finders \
  main.py

echo ""
echo "========================================"
if [ -f "dist/SistemaReservas/SistemaReservas" ]; then
    echo "✅ BUILD EXITOSO"
    echo "📁 Ejecutable: dist/SistemaReservas/SistemaReservas"
    echo "📊 Static files: Incluidos ✓ (desde staticfiles)"
    echo "🎨 Bootstrap/Icons: Incluidos ✓"
    echo "📈 Gráficos: Incluidos ✓"
    echo "🌐 Puerto: 9000"
    echo "👤 Usuario: admin"
    echo "🔑 Contraseña: maXS@sdasd1234"
    echo ""
    echo "💡 Para distribuir: Copia toda la carpeta 'dist/SistemaReservas'"
    echo ""
    echo "🚀 Para ejecutar: ./dist/SistemaReservas/SistemaReservas"
else
    echo "❌ BUILD FALLIDO"
    echo "💡 Revisa los mensajes de error arriba"
fi

echo "========================================"
read -p "Presiona Enter para continuar..."
