#!/usr/bin/env python3
"""
Analizador de Noticias sobre CASMU - Versión Ligera
Usa análisis léxico simple sin necesidad de modelos pesados
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
import re
import time
import csv
from collections import Counter

@dataclass
class Noticia:
    """Representa una noticia extraída"""
    titulo: str
    contenido: str
    url: str
    medio: str
    fecha: Optional[str] = None
    sentimiento: Optional[str] = None
    score: Optional[float] = None


class AnalizadorSentimientoLexico:
    """
    Analizador de sentimiento basado en léxico español
    No requiere modelos de ML pesados
    """

    # Palabras positivas comunes en contexto de salud/empresas
    PALABRAS_POSITIVAS = {
        'excelente', 'bueno', 'mejor', 'mejora', 'mejorar', 'éxito', 'exitoso',
        'avance', 'avances', 'beneficio', 'beneficios', 'calidad', 'innovación',
        'innovador', 'eficiente', 'eficiencia', 'solución', 'solucionado',
        'positivo', 'crecimiento', 'crecer', 'desarrollo', 'logro', 'logros',
        'reconocimiento', 'premio', 'destacado', 'satisfacción', 'satisfecho',
        'acuerdo', 'acuerdos', 'inversión', 'invertir', 'nuevo', 'nuevos',
        'modernización', 'modernizar', 'atención', 'servicio', 'servicios',
        'apertura', 'inauguración', 'inaugurar', 'incorporación', 'incorporar',
        'ampliación', 'ampliar', 'fortalecimiento', 'fortalecer', 'recuperación',
        'recuperar', 'estabilidad', 'estable', 'confianza', 'optimismo',
        'celebrar', 'celebración', 'felicitaciones', 'destacar'
    }

    # Palabras negativas comunes en contexto de salud/empresas
    PALABRAS_NEGATIVAS = {
        'crisis', 'problema', 'problemas', 'denuncia', 'denunciar', 'queja',
        'quejas', 'conflicto', 'conflictos', 'paro', 'huelga', 'protesta',
        'protestas', 'reclamo', 'reclamos', 'demanda', 'demandar', 'pérdida',
        'pérdidas', 'déficit', 'deuda', 'deudas', 'despido', 'despidos',
        'cierre', 'cerrar', 'suspensión', 'suspender', 'investigación',
        'investigar', 'irregularidad', 'irregularidades', 'fraude', 'estafa',
        'mal', 'malo', 'peor', 'grave', 'graves', 'crítico', 'crítica',
        'negligencia', 'negligente', 'error', 'errores', 'falla', 'fallas',
        'fallecimiento', 'muerte', 'muerto', 'víctima', 'víctimas', 'acusación',
        'acusar', 'imputar', 'imputación', 'procesado', 'procesamiento',
        'sanción', 'sancionar', 'multa', 'multar', 'incumplimiento', 'incumplir',
        'abandono', 'abandonar', 'colapso', 'escándalo', 'corrupción', 'fraude',
        'demora', 'demoras', 'falta', 'carencia', 'preocupación', 'preocupante',
        'dificultad', 'dificultades', 'tensión', 'recorte', 'recortes'
    }

    # Intensificadores
    INTENSIFICADORES = {
        'muy', 'mucho', 'extremadamente', 'totalmente', 'completamente',
        'absolutamente', 'bastante', 'demasiado', 'gravemente', 'seriamente'
    }

    # Negadores
    NEGADORES = {'no', 'sin', 'nunca', 'ningún', 'ninguno', 'ninguna', 'tampoco'}

    def analizar(self, texto: str) -> tuple[str, float]:
        """
        Analiza el sentimiento usando conteo de palabras positivas/negativas
        """
        # Normalizar texto
        texto_lower = texto.lower()
        palabras = re.findall(r'\b\w+\b', texto_lower)

        score_positivo = 0
        score_negativo = 0
        intensificador_activo = False
        negador_activo = False

        for i, palabra in enumerate(palabras):
            # Detectar intensificadores y negadores
            if palabra in self.INTENSIFICADORES:
                intensificador_activo = True
                continue
            if palabra in self.NEGADORES:
                negador_activo = True
                continue

            multiplicador = 1.5 if intensificador_activo else 1.0

            if palabra in self.PALABRAS_POSITIVAS:
                if negador_activo:
                    score_negativo += multiplicador
                else:
                    score_positivo += multiplicador
            elif palabra in self.PALABRAS_NEGATIVAS:
                if negador_activo:
                    score_positivo += multiplicador * 0.5  # Negación parcial
                else:
                    score_negativo += multiplicador

            # Reset de modificadores después de usar
            intensificador_activo = False
            negador_activo = False

        # Calcular sentimiento final
        total = score_positivo + score_negativo
        if total == 0:
            return "NEUTRO", 0.5

        ratio = score_positivo / total
        diferencia = abs(score_positivo - score_negativo)

        # Umbral para determinar sentimiento
        if diferencia < 2 or (ratio > 0.4 and ratio < 0.6):
            return "NEUTRO", 0.5
        elif score_positivo > score_negativo:
            confidence = min(0.5 + (diferencia / 10), 0.95)
            return "POSITIVO", confidence
        else:
            confidence = min(0.5 + (diferencia / 10), 0.95)
            return "NEGATIVO", confidence


class ScraperMediosUruguayos:
    """Scraper para diferentes medios uruguayos"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def buscar_google_news(self, termino: str) -> list[Noticia]:
        """Búsqueda usando Google News RSS para medios uruguayos"""
        noticias = []
        try:
            # Múltiples búsquedas para mejor cobertura
            queries = [
                f"{termino} site:elpais.com.uy",
                f"{termino} site:elobservador.com.uy",
                f"{termino} site:ladiaria.com.uy",
                f"{termino} site:montevideo.com.uy",
                f"{termino} Uruguay salud"
            ]

            for query in queries:
                encoded_query = requests.utils.quote(query)
                url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=UY&ceid=UY:es-419"

                try:
                    response = self.session.get(url, timeout=15)
                    soup = BeautifulSoup(response.text, "xml")

                    items = soup.find_all("item")
                    for item in items[:5]:
                        titulo = item.title.text if item.title else ""
                        link = item.link.text if item.link else ""
                        fuente = item.source.text if item.source else "Desconocido"
                        fecha = item.pubDate.text if item.pubDate else ""

                        # Verificar que contiene el término
                        if termino.lower() in titulo.lower():
                            noticias.append(Noticia(
                                titulo=titulo,
                                contenido=titulo,
                                url=link,
                                medio=fuente,
                                fecha=fecha
                            ))
                    time.sleep(0.3)
                except Exception:
                    pass

        except Exception as e:
            print(f"Error en búsqueda: {e}")

        # Eliminar duplicados
        vistas = set()
        unicas = []
        for n in noticias:
            key = n.titulo[:50]
            if key not in vistas:
                vistas.add(key)
                unicas.append(n)

        return unicas

    def buscar_directo_medios(self, termino: str) -> list[Noticia]:
        """Busca directamente en los sitios de medios"""
        noticias = []

        medios = [
            ("El País", f"https://www.elpais.com.uy/buscador?q={termino}"),
            ("El Observador", f"https://www.elobservador.com.uy/buscar?q={termino}"),
            ("La Diaria", f"https://ladiaria.com.uy/search/?q={termino}"),
        ]

        for nombre, url in medios:
            try:
                print(f"  Buscando en {nombre}...")
                response = self.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, "lxml")

                # Selectores genéricos para artículos
                selectores = [
                    "article h2 a", "article h3 a", ".article-title a",
                    ".search-result a", ".nota-titulo a", "h2.title a",
                    ".resultado a", "a.titulo"
                ]

                for selector in selectores:
                    elementos = soup.select(selector)
                    for elem in elementos[:5]:
                        titulo = elem.get_text(strip=True)
                        href = elem.get("href", "")

                        if termino.lower() in titulo.lower():
                            if not href.startswith("http"):
                                href = url.split("/buscar")[0].split("/search")[0] + href

                            noticias.append(Noticia(
                                titulo=titulo,
                                contenido=titulo,
                                url=href,
                                medio=nombre
                            ))
                    if noticias:
                        break

                time.sleep(0.5)
            except Exception as e:
                print(f"    Error: {e}")

        return noticias

    def obtener_contenido(self, url: str) -> str:
        """Intenta obtener el contenido de un artículo"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "lxml")

            # Remover elementos no deseados
            for tag in soup.select("script, style, nav, footer, aside, .publicidad, .ads"):
                tag.decompose()

            # Buscar contenido principal
            for selector in ["article", ".article-body", ".nota-cuerpo", ".entry-content", "main"]:
                elem = soup.select_one(selector)
                if elem:
                    texto = elem.get_text(separator=" ", strip=True)
                    texto = re.sub(r'\s+', ' ', texto)
                    return texto[:1500]

            # Fallback: párrafos
            parrafos = soup.select("p")
            texto = " ".join(p.get_text(strip=True) for p in parrafos[:10])
            return texto[:1500]

        except Exception:
            return ""


def imprimir_tabla(noticias: list[Noticia]):
    """Imprime los resultados en formato tabla"""
    print("\n" + "=" * 80)
    print(" RESULTADOS DEL ANÁLISIS DE SENTIMIENTO")
    print("=" * 80)

    # Resumen
    conteo = Counter(n.sentimiento for n in noticias)
    total = len(noticias)

    print("\n📊 RESUMEN:")
    print("-" * 40)
    for cat in ["POSITIVO", "NEGATIVO", "NEUTRO"]:
        count = conteo.get(cat, 0)
        pct = (count / total * 100) if total > 0 else 0
        emoji = {"POSITIVO": "🟢", "NEGATIVO": "🔴", "NEUTRO": "🟡"}[cat]
        print(f"  {emoji} {cat:10} : {count:3} ({pct:5.1f}%)")
    print(f"  {'─' * 25}")
    print(f"     TOTAL     : {total}")

    # Detalle
    print("\n📰 NOTICIAS ANALIZADAS:")
    print("-" * 80)

    for i, n in enumerate(noticias, 1):
        emoji = {"POSITIVO": "🟢", "NEGATIVO": "🔴", "NEUTRO": "🟡"}.get(n.sentimiento, "⚪")
        titulo_corto = n.titulo[:60] + "..." if len(n.titulo) > 60 else n.titulo
        print(f"\n{i}. {emoji} [{n.sentimiento}] (score: {n.score:.2f})")
        print(f"   Medio: {n.medio}")
        print(f"   Título: {titulo_corto}")
        print(f"   URL: {n.url[:70]}...")

    print("\n" + "=" * 80)


def exportar_csv(noticias: list[Noticia], archivo: str = "casmu_analisis.csv"):
    """Exporta resultados a CSV"""
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'medio', 'titulo', 'sentimiento', 'score', 'url', 'fecha'
        ])
        writer.writeheader()
        for n in noticias:
            writer.writerow({
                'medio': n.medio,
                'titulo': n.titulo,
                'sentimiento': n.sentimiento,
                'score': n.score,
                'url': n.url,
                'fecha': n.fecha or ''
            })
    print(f"\n✅ Resultados exportados a: {archivo}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   ANALIZADOR DE NOTICIAS CASMU - MEDIOS URUGUAYOS            ║
║   Análisis de Sentimiento con NLP (Versión Ligera)           ║
╚══════════════════════════════════════════════════════════════╝
    """)

    termino = "CASMU"
    print(f"🔍 Buscando noticias sobre '{termino}'...")

    scraper = ScraperMediosUruguayos()
    analizador = AnalizadorSentimientoLexico()

    # Buscar noticias
    print("\n📡 Buscando en Google News...")
    noticias = scraper.buscar_google_news(termino)

    print("📡 Buscando directamente en medios...")
    noticias.extend(scraper.buscar_directo_medios(termino))

    # Eliminar duplicados finales
    vistas = set()
    unicas = []
    for n in noticias:
        key = n.titulo[:40].lower()
        if key not in vistas:
            vistas.add(key)
            unicas.append(n)

    noticias = unicas

    if not noticias:
        print("\n⚠️  No se encontraron noticias sobre CASMU")
        print("    Esto puede deberse a restricciones de acceso o falta de noticias recientes.")
        return

    print(f"\n✅ Se encontraron {len(noticias)} noticias únicas")

    # Analizar sentimiento
    print("\n🧠 Analizando sentimiento de cada noticia...")
    for n in noticias:
        # Intentar obtener contenido completo
        if len(n.contenido) < 100:
            contenido_extra = scraper.obtener_contenido(n.url)
            if contenido_extra:
                n.contenido = contenido_extra

        # Analizar
        sentimiento, score = analizador.analizar(n.contenido)
        n.sentimiento = sentimiento
        n.score = score

    # Mostrar resultados
    imprimir_tabla(noticias)

    # Exportar
    exportar_csv(noticias)

    print("\n✅ Análisis completado\n")


if __name__ == "__main__":
    main()
