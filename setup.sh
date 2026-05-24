#!/bin/bash
# Script de instalación para el Analizador de Noticias CASMU

echo "Instalando dependencias..."

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Entorno virtual creado"
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Instalación completada!"
echo ""
echo "Para ejecutar el analizador:"
echo "  source venv/bin/activate"
echo "  python casmu_analyzer.py"
