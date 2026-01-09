@echo off
echo Construyendo con COLECT-ALL (método definitivo)...
echo.

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
echo ✅ Build con COLECT-ALL completado.
pause