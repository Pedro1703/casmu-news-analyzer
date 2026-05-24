#!/usr/bin/env python3
"""
Script de actualización semanal de noticias CASMU
- Busca noticias nuevas de la última semana
- Analiza sentimiento con NLP fine-tuned
- Actualiza el archivo JSON
- Envía email con resumen o "sin novedades"
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Importar el analizador del módulo existente
from collect_data import AnalizadorSentimientoFineTuned, MEDIOS, HEADERS


# Configuración de email (usar variables de entorno para seguridad)
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "pedro@ciudadana.city")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

DATA_FILE = "data/noticias_casmu.json"


def cargar_noticias_existentes():
    """Carga las noticias existentes del archivo JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def guardar_noticias(noticias):
    """Guarda las noticias en el archivo JSON"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)


def buscar_noticias_semana(analizador):
    """Busca noticias de CASMU de la última semana"""
    session = requests.Session()
    session.headers.update(HEADERS)
    noticias = []

    # Fechas de la última semana
    hoy = datetime.now()
    hace_una_semana = hoy - timedelta(days=7)

    fecha_inicio = hace_una_semana.strftime("%Y-%m-%d")
    fecha_fin = hoy.strftime("%Y-%m-%d")

    print(f"Buscando noticias del {fecha_inicio} al {fecha_fin}...")

    for nombre_medio, dominio in MEDIOS.items():
        try:
            query = f"CASMU site:{dominio} after:{fecha_inicio}"
            encoded_query = requests.utils.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=UY&ceid=UY:es-419"

            response = session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "xml")

            items = soup.find_all("item")
            for item in items[:10]:
                titulo = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                fecha_str = item.pubDate.text if item.pubDate else ""

                if "casmu" in titulo.lower():
                    try:
                        fecha = datetime.strptime(fecha_str[:16], "%a, %d %b %Y")
                        año = fecha.year
                        mes = fecha.month
                    except:
                        fecha = hoy
                        año = hoy.year
                        mes = hoy.month

                    # Analizar sentimiento
                    sentimiento, score, detalles = analizador.analizar(titulo)

                    noticias.append({
                        'titulo': titulo,
                        'url': link,
                        'medio': nombre_medio,
                        'año': año,
                        'mes': mes,
                        'fecha': fecha.isoformat() if fecha else hoy.isoformat(),
                        'sentimiento': sentimiento,
                        'score': score,
                        'palabras_positivas': detalles['positivas'],
                        'palabras_negativas': detalles['negativas'],
                    })

        except Exception as e:
            print(f"Error en {nombre_medio}: {e}")

    return noticias


def filtrar_noticias_nuevas(noticias_nuevas, noticias_existentes):
    """Filtra solo las noticias que no existen ya en el dataset"""
    titulos_existentes = {n['titulo'][:40].lower() for n in noticias_existentes}

    nuevas_filtradas = []
    for n in noticias_nuevas:
        key = n['titulo'][:40].lower()
        if key not in titulos_existentes:
            nuevas_filtradas.append(n)

    return nuevas_filtradas


def generar_html_email(noticias_nuevas):
    """Genera el HTML del email con las noticias encontradas"""
    if not noticias_nuevas:
        return """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">📰 CASMU News Analyzer - Reporte Semanal</h2>
            <p style="font-size: 16px;">Sin novedades esta semana.</p>
            <p style="color: #666; font-size: 14px;">No se encontraron noticias nuevas sobre CASMU en los medios monitoreados.</p>
            <hr style="border-color: #eee;">
            <p style="color: #999; font-size: 12px;">Este es un mensaje automático del CASMU News Analyzer.</p>
        </body>
        </html>
        """

    # Contar por sentimiento
    pos = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'POSITIVO')
    neg = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'NEGATIVO')
    neu = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'NEUTRO')

    # Generar lista de noticias
    noticias_html = ""
    for n in noticias_nuevas:
        color = "#22c55e" if n['sentimiento'] == 'POSITIVO' else "#ef4444" if n['sentimiento'] == 'NEGATIVO' else "#f59e0b"
        emoji = "🟢" if n['sentimiento'] == 'POSITIVO' else "🔴" if n['sentimiento'] == 'NEGATIVO' else "🟡"

        noticias_html += f"""
        <div style="margin-bottom: 15px; padding: 15px; background: #f8fafc; border-radius: 8px; border-left: 4px solid {color};">
            <span style="font-size: 12px; color: {color}; font-weight: bold;">{emoji} {n['sentimiento']}</span>
            <h3 style="margin: 5px 0; font-size: 14px;">
                <a href="{n['url']}" style="color: #333; text-decoration: none;">{n['titulo']}</a>
            </h3>
            <p style="margin: 0; color: #666; font-size: 12px;">{n['medio']} | {n['fecha'][:10]}</p>
        </div>
        """

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #f1f5f9;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px;">
            <h2 style="color: #667eea; margin-top: 0;">📰 CASMU News Analyzer - Reporte Semanal</h2>

            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <div style="flex: 1; padding: 15px; background: #dcfce7; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #22c55e;">{pos}</div>
                    <div style="font-size: 12px; color: #166534;">Positivas</div>
                </div>
                <div style="flex: 1; padding: 15px; background: #fee2e2; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #ef4444;">{neg}</div>
                    <div style="font-size: 12px; color: #991b1b;">Negativas</div>
                </div>
                <div style="flex: 1; padding: 15px; background: #fef3c7; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">{neu}</div>
                    <div style="font-size: 12px; color: #92400e;">Neutras</div>
                </div>
            </div>

            <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                📋 Noticias Encontradas ({len(noticias_nuevas)})
            </h3>

            {noticias_html}

            <hr style="border-color: #eee; margin-top: 30px;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                Este es un mensaje automático del CASMU News Analyzer.<br>
                <a href="https://casmu-analyzer.streamlit.app" style="color: #667eea;">Ver dashboard completo</a>
            </p>
        </div>
    </body>
    </html>
    """


def enviar_email(noticias_nuevas):
    """Envía el email con el reporte"""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("⚠️  Credenciales de email no configuradas.")
        print("   Configure las variables de entorno:")
        print("   - EMAIL_SENDER: dirección de email del remitente")
        print("   - EMAIL_PASSWORD: contraseña o app password")
        print("   - SMTP_SERVER: servidor SMTP (default: smtp.gmail.com)")
        print("   - SMTP_PORT: puerto SMTP (default: 587)")
        return False

    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📰 CASMU News - {'Sin novedades' if not noticias_nuevas else f'{len(noticias_nuevas)} noticia(s) nueva(s)'}"
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT

        # Contenido HTML
        html_content = generar_html_email(noticias_nuevas)
        msg.attach(MIMEText(html_content, 'html'))

        # Enviar
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email enviado a {EMAIL_RECIPIENT}")
        return True

    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False


def main():
    print("=" * 60)
    print("ACTUALIZACIÓN SEMANAL - CASMU NEWS ANALYZER")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Inicializar analizador
    analizador = AnalizadorSentimientoFineTuned()

    # Cargar noticias existentes
    noticias_existentes = cargar_noticias_existentes()
    print(f"\n📊 Noticias existentes en base de datos: {len(noticias_existentes)}")

    # Buscar noticias nuevas
    print("\n🔍 Buscando noticias de la última semana...")
    noticias_semana = buscar_noticias_semana(analizador)
    print(f"   Encontradas en búsqueda: {len(noticias_semana)}")

    # Filtrar solo las nuevas
    noticias_nuevas = filtrar_noticias_nuevas(noticias_semana, noticias_existentes)
    print(f"   Nuevas (no duplicadas): {len(noticias_nuevas)}")

    # Mostrar resumen de nuevas
    if noticias_nuevas:
        pos = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'POSITIVO')
        neg = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'NEGATIVO')
        neu = sum(1 for n in noticias_nuevas if n['sentimiento'] == 'NEUTRO')
        print(f"\n📈 Distribución de noticias nuevas:")
        print(f"   🟢 POSITIVO: {pos}")
        print(f"   🔴 NEGATIVO: {neg}")
        print(f"   🟡 NEUTRO: {neu}")

        # Agregar al dataset existente
        noticias_existentes.extend(noticias_nuevas)
        guardar_noticias(noticias_existentes)
        print(f"\n💾 Dataset actualizado: {len(noticias_existentes)} noticias totales")

        # Mostrar títulos nuevos
        print("\n📰 Noticias nuevas encontradas:")
        for n in noticias_nuevas:
            emoji = "🟢" if n['sentimiento'] == 'POSITIVO' else "🔴" if n['sentimiento'] == 'NEGATIVO' else "🟡"
            print(f"   {emoji} {n['titulo'][:60]}...")
    else:
        print("\n📭 Sin novedades esta semana.")

    # Enviar email
    print("\n📧 Enviando reporte por email...")
    enviar_email(noticias_nuevas)

    print("\n" + "=" * 60)
    print("✅ Actualización completada")
    print("=" * 60)

    return len(noticias_nuevas)


if __name__ == "__main__":
    main()
