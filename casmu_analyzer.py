#!/usr/bin/env python3
"""
Analizador de Noticias sobre CASMU en Medios Uruguayos
Categoriza noticias usando NLP (análisis de sentimiento)
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import re
import time

# Intentar importar pysentimiento, si no está disponible usar alternativa
try:
    from pysentimiento import create_analyzer
    USE_PYSENTIMIENTO = True
except ImportError:
    USE_PYSENTIMIENTO = False
    from transformers import pipeline

console = Console()


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


class AnalizadorSentimiento:
    """Analiza el sentimiento de textos en español"""

    def __init__(self):
        console.print("[cyan]Cargando modelo de análisis de sentimiento...[/cyan]")
        if USE_PYSENTIMIENTO:
            self.analyzer = create_analyzer(task="sentiment", lang="es")
        else:
            # Alternativa usando transformers directamente
            self.analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment"
            )
        console.print("[green]Modelo cargado correctamente[/green]")

    def analizar(self, texto: str) -> tuple[str, float]:
        """
        Analiza el sentimiento de un texto.
        Retorna (sentimiento, score) donde sentimiento es POS, NEG o NEU
        """
        # Limitar texto para evitar problemas de memoria
        texto_limpio = texto[:512] if len(texto) > 512 else texto

        if USE_PYSENTIMIENTO:
            resultado = self.analyzer.predict(texto_limpio)
            sentimiento = resultado.output
            score = max(resultado.probas.values())

            # Mapear a categorías estándar
            mapeo = {"POS": "POSITIVO", "NEG": "NEGATIVO", "NEU": "NEUTRO"}
            return mapeo.get(sentimiento, "NEUTRO"), score
        else:
            resultado = self.analyzer(texto_limpio)[0]
            # El modelo nlptown usa estrellas 1-5
            label = resultado["label"]
            score = resultado["score"]

            estrellas = int(label.split()[0])
            if estrellas >= 4:
                return "POSITIVO", score
            elif estrellas <= 2:
                return "NEGATIVO", score
            else:
                return "NEUTRO", score


class ScraperMediosUruguayos:
    """Scraper para diferentes medios uruguayos"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def buscar_en_elpais(self, termino: str) -> list[Noticia]:
        """Busca noticias en El País Uruguay"""
        noticias = []
        try:
            url = f"https://www.elpais.com.uy/buscador?q={termino}"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "lxml")

            articulos = soup.select("article, .article-item, .search-result")
            for art in articulos[:10]:
                titulo_elem = art.select_one("h2, h3, .title, a")
                if titulo_elem:
                    titulo = titulo_elem.get_text(strip=True)
                    link = titulo_elem.get("href", "")
                    if not link.startswith("http"):
                        link = f"https://www.elpais.com.uy{link}"

                    if termino.lower() in titulo.lower():
                        noticias.append(Noticia(
                            titulo=titulo,
                            contenido=titulo,
                            url=link,
                            medio="El País"
                        ))
        except Exception as e:
            console.print(f"[yellow]Error en El País: {e}[/yellow]")

        return noticias

    def buscar_en_elobservador(self, termino: str) -> list[Noticia]:
        """Busca noticias en El Observador"""
        noticias = []
        try:
            url = f"https://www.elobservador.com.uy/buscar?q={termino}"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "lxml")

            articulos = soup.select("article, .nota, .search-item")
            for art in articulos[:10]:
                titulo_elem = art.select_one("h2, h3, .titulo, a")
                if titulo_elem:
                    titulo = titulo_elem.get_text(strip=True)
                    link = titulo_elem.get("href", "")
                    if not link.startswith("http"):
                        link = f"https://www.elobservador.com.uy{link}"

                    if termino.lower() in titulo.lower():
                        noticias.append(Noticia(
                            titulo=titulo,
                            contenido=titulo,
                            url=link,
                            medio="El Observador"
                        ))
        except Exception as e:
            console.print(f"[yellow]Error en El Observador: {e}[/yellow]")

        return noticias

    def buscar_en_ladiaria(self, termino: str) -> list[Noticia]:
        """Busca noticias en La Diaria"""
        noticias = []
        try:
            url = f"https://ladiaria.com.uy/search/?q={termino}"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "lxml")

            articulos = soup.select("article, .article, .result-item")
            for art in articulos[:10]:
                titulo_elem = art.select_one("h2, h3, .title, a")
                if titulo_elem:
                    titulo = titulo_elem.get_text(strip=True)
                    link = titulo_elem.get("href", "")
                    if not link.startswith("http"):
                        link = f"https://ladiaria.com.uy{link}"

                    if termino.lower() in titulo.lower():
                        noticias.append(Noticia(
                            titulo=titulo,
                            contenido=titulo,
                            url=link,
                            medio="La Diaria"
                        ))
        except Exception as e:
            console.print(f"[yellow]Error en La Diaria: {e}[/yellow]")

        return noticias

    def buscar_en_montevideo_portal(self, termino: str) -> list[Noticia]:
        """Busca noticias en Montevideo Portal"""
        noticias = []
        try:
            url = f"https://www.montevideo.com.uy/buscar?texto={termino}"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "lxml")

            articulos = soup.select("article, .noticia, .resultado")
            for art in articulos[:10]:
                titulo_elem = art.select_one("h2, h3, .titulo, a")
                if titulo_elem:
                    titulo = titulo_elem.get_text(strip=True)
                    link = titulo_elem.get("href", "")
                    if not link.startswith("http"):
                        link = f"https://www.montevideo.com.uy{link}"

                    if termino.lower() in titulo.lower():
                        noticias.append(Noticia(
                            titulo=titulo,
                            contenido=titulo,
                            url=link,
                            medio="Montevideo Portal"
                        ))
        except Exception as e:
            console.print(f"[yellow]Error en Montevideo Portal: {e}[/yellow]")

        return noticias

    def buscar_con_google(self, termino: str) -> list[Noticia]:
        """
        Búsqueda alternativa usando Google News RSS para medios uruguayos
        """
        noticias = []
        try:
            # Buscar en Google News con filtro de Uruguay
            query = f"{termino} site:elpais.com.uy OR site:elobservador.com.uy OR site:ladiaria.com.uy OR site:montevideo.com.uy"
            url = f"https://news.google.com/rss/search?q={query}&hl=es-419&gl=UY&ceid=UY:es-419"

            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "xml")

            items = soup.find_all("item")
            for item in items[:15]:
                titulo = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                fuente = item.source.text if item.source else "Desconocido"
                fecha = item.pubDate.text if item.pubDate else ""

                if termino.lower() in titulo.lower():
                    noticias.append(Noticia(
                        titulo=titulo,
                        contenido=titulo,
                        url=link,
                        medio=fuente,
                        fecha=fecha
                    ))
        except Exception as e:
            console.print(f"[yellow]Error en búsqueda Google: {e}[/yellow]")

        return noticias

    def obtener_contenido_articulo(self, noticia: Noticia) -> str:
        """Intenta obtener el contenido completo de un artículo"""
        try:
            response = self.session.get(noticia.url, timeout=10)
            soup = BeautifulSoup(response.text, "lxml")

            # Buscar el contenido principal
            contenido_elem = soup.select_one(
                "article, .article-body, .nota-cuerpo, .content, "
                ".entry-content, .post-content, main"
            )

            if contenido_elem:
                # Remover scripts y estilos
                for tag in contenido_elem.select("script, style, nav, footer, aside"):
                    tag.decompose()

                texto = contenido_elem.get_text(separator=" ", strip=True)
                # Limpiar espacios múltiples
                texto = re.sub(r'\s+', ' ', texto)
                return texto[:2000]  # Limitar longitud
        except Exception:
            pass

        return noticia.titulo

    def buscar_todas(self, termino: str) -> list[Noticia]:
        """Busca en todos los medios disponibles"""
        todas_noticias = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Buscando noticias...", total=5)

            # Buscar en cada medio
            progress.update(task, description="Buscando en El País...")
            todas_noticias.extend(self.buscar_en_elpais(termino))
            progress.advance(task)
            time.sleep(0.5)

            progress.update(task, description="Buscando en El Observador...")
            todas_noticias.extend(self.buscar_en_elobservador(termino))
            progress.advance(task)
            time.sleep(0.5)

            progress.update(task, description="Buscando en La Diaria...")
            todas_noticias.extend(self.buscar_en_ladiaria(termino))
            progress.advance(task)
            time.sleep(0.5)

            progress.update(task, description="Buscando en Montevideo Portal...")
            todas_noticias.extend(self.buscar_en_montevideo_portal(termino))
            progress.advance(task)
            time.sleep(0.5)

            progress.update(task, description="Buscando con Google News...")
            todas_noticias.extend(self.buscar_con_google(termino))
            progress.advance(task)

        # Eliminar duplicados por URL
        vistas = set()
        unicas = []
        for noticia in todas_noticias:
            if noticia.url not in vistas:
                vistas.add(noticia.url)
                unicas.append(noticia)

        return unicas


class AnalizadorCASMU:
    """Clase principal para analizar noticias de CASMU"""

    def __init__(self):
        self.scraper = ScraperMediosUruguayos()
        self.analizador = None  # Se inicializa lazy

    def _inicializar_analizador(self):
        if self.analizador is None:
            self.analizador = AnalizadorSentimiento()

    def analizar_noticias(self, termino: str = "CASMU") -> list[Noticia]:
        """
        Busca y analiza noticias sobre el término especificado
        """
        console.print(f"\n[bold blue]Buscando noticias sobre '{termino}'...[/bold blue]\n")

        # Buscar noticias
        noticias = self.scraper.buscar_todas(termino)

        if not noticias:
            console.print("[yellow]No se encontraron noticias[/yellow]")
            return []

        console.print(f"\n[green]Se encontraron {len(noticias)} noticias[/green]\n")

        # Inicializar analizador de sentimiento
        self._inicializar_analizador()

        # Obtener contenido y analizar sentimiento
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analizando sentimiento...", total=len(noticias))

            for noticia in noticias:
                progress.update(task, description=f"Analizando: {noticia.titulo[:40]}...")

                # Obtener contenido completo si es posible
                contenido = self.scraper.obtener_contenido_articulo(noticia)
                noticia.contenido = contenido

                # Analizar sentimiento
                sentimiento, score = self.analizador.analizar(contenido)
                noticia.sentimiento = sentimiento
                noticia.score = score

                progress.advance(task)
                time.sleep(0.2)  # Evitar sobrecarga

        return noticias

    def mostrar_resultados(self, noticias: list[Noticia]):
        """Muestra los resultados en una tabla formateada"""
        if not noticias:
            return

        # Contar por categoría
        conteo = {"POSITIVO": 0, "NEGATIVO": 0, "NEUTRO": 0}
        for n in noticias:
            if n.sentimiento in conteo:
                conteo[n.sentimiento] += 1

        # Mostrar resumen
        console.print("\n[bold]═══ RESUMEN DEL ANÁLISIS ═══[/bold]\n")

        resumen = Table(show_header=True, header_style="bold")
        resumen.add_column("Categoría", style="cyan")
        resumen.add_column("Cantidad", justify="right")
        resumen.add_column("Porcentaje", justify="right")

        total = len(noticias)
        for cat, count in conteo.items():
            color = {"POSITIVO": "green", "NEGATIVO": "red", "NEUTRO": "yellow"}[cat]
            pct = (count / total * 100) if total > 0 else 0
            resumen.add_row(f"[{color}]{cat}[/{color}]", str(count), f"{pct:.1f}%")

        resumen.add_row("[bold]TOTAL[/bold]", f"[bold]{total}[/bold]", "100%")
        console.print(resumen)

        # Mostrar noticias detalladas
        console.print("\n[bold]═══ NOTICIAS DETALLADAS ═══[/bold]\n")

        tabla = Table(show_header=True, header_style="bold magenta")
        tabla.add_column("Medio", style="cyan", width=15)
        tabla.add_column("Título", width=50)
        tabla.add_column("Sentimiento", justify="center", width=12)
        tabla.add_column("Score", justify="right", width=8)

        for noticia in noticias:
            color = {
                "POSITIVO": "green",
                "NEGATIVO": "red",
                "NEUTRO": "yellow"
            }.get(noticia.sentimiento, "white")

            titulo_corto = noticia.titulo[:47] + "..." if len(noticia.titulo) > 50 else noticia.titulo

            tabla.add_row(
                noticia.medio[:15],
                titulo_corto,
                f"[{color}]{noticia.sentimiento}[/{color}]",
                f"{noticia.score:.2f}" if noticia.score else "N/A"
            )

        console.print(tabla)

    def exportar_csv(self, noticias: list[Noticia], archivo: str = "casmu_noticias.csv"):
        """Exporta los resultados a un archivo CSV"""
        if not noticias:
            return

        df = pd.DataFrame([
            {
                "medio": n.medio,
                "titulo": n.titulo,
                "url": n.url,
                "fecha": n.fecha,
                "sentimiento": n.sentimiento,
                "score": n.score,
                "contenido": n.contenido[:500]
            }
            for n in noticias
        ])

        df.to_csv(archivo, index=False, encoding="utf-8")
        console.print(f"\n[green]Resultados exportados a: {archivo}[/green]")


def main():
    """Función principal"""
    console.print("""
[bold blue]╔════════════════════════════════════════════════════════════╗
║     ANALIZADOR DE NOTICIAS CASMU - MEDIOS URUGUAYOS        ║
║        Análisis de Sentimiento con NLP                      ║
╚════════════════════════════════════════════════════════════╝[/bold blue]
    """)

    analizador = AnalizadorCASMU()

    # Analizar noticias sobre CASMU
    noticias = analizador.analizar_noticias("CASMU")

    # Mostrar resultados
    analizador.mostrar_resultados(noticias)

    # Exportar a CSV
    if noticias:
        analizador.exportar_csv(noticias)

    console.print("\n[bold green]Análisis completado[/bold green]\n")


if __name__ == "__main__":
    main()
