#!/usr/bin/env python3
"""
Script para recolectar datos históricos de noticias CASMU
con análisis de sentimiento mejorado (fine-tuned)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

MEDIOS = {
    'El País': 'elpais.com.uy',
    'El Observador': 'elobservador.com.uy',
    'La Diaria': 'ladiaria.com.uy',
    'Montevideo Portal': 'montevideo.com.uy',
    'Subrayado': 'subrayado.com.uy',
}


class AnalizadorSentimientoFineTuned:
    """
    Analizador de sentimiento optimizado para noticias uruguayas sobre CASMU.
    Fine-tuned para capturar mejor el contexto de salud, relaciones laborales
    y eventos institucionales.
    """

    # =========================================================================
    # PALABRAS POSITIVAS CON PESOS
    # =========================================================================
    PALABRAS_POSITIVAS = {
        # Agregar servicios / sumar
        'suma': 2.0, 'sumar': 1.8, 'sumó': 2.0, 'sumo': 2.0,
        'agrega': 1.8, 'agregar': 1.5, 'agregó': 1.8,
        'incorpora': 1.8, 'incorporar': 1.5, 'incorporó': 2.0,
        'ofrece': 1.5, 'ofrecer': 1.5, 'brinda': 1.8, 'brindar': 1.5,
        'implementa': 1.8, 'implementar': 1.5, 'implementó': 2.0,

        # Pionero / novedoso / inédito
        'pionero': 2.5, 'pionera': 2.5, 'pioneros': 2.5,
        'novedoso': 2.0, 'novedosa': 2.0, 'novedosos': 2.0,
        'inédito': 2.5, 'inédita': 2.5, 'inedito': 2.5, 'inedita': 2.5,
        'incursiona': 2.0, 'incursionar': 1.8,
        'lidera': 2.0, 'liderar': 1.8, 'liderando': 1.8,

        # Concientización / prevención
        'concientiza': 1.8, 'concientizar': 1.5, 'concientizó': 2.0,
        'promueve': 1.8, 'promover': 1.5, 'promovió': 2.0,
        'fomenta': 1.5, 'fomentar': 1.5,

        # Distinciones
        'distinguido': 2.5, 'distinguida': 2.5, 'distinción': 2.5,

        # Balance positivo
        'positivo': 2.0, 'positiva': 2.0, 'positivos': 2.0,
        'superávit': 2.5, 'superavit': 2.5, 'ganancia': 2.0, 'ganancias': 2.0,

        # Restitución (contexto positivo)
        'restituyó': 1.8, 'restituyo': 1.8, 'restitución': 1.8, 'restitucion': 1.8,
        'reintegro': 1.5, 'reintegrar': 1.5,

        # Relaciones y diálogo
        'diálogo': 2.0, 'dialogo': 2.0, 'acuerdo': 1.8, 'acuerdos': 1.8,
        'negociación': 1.5, 'negociacion': 1.5, 'consenso': 2.0,
        'entendimiento': 1.8, 'armonía': 2.0, 'armonia': 2.0,
        'reconciliación': 2.0, 'reconciliacion': 2.0,
        'colaboración': 1.8, 'colaboracion': 1.8, 'cooperación': 1.8,
        'cooperacion': 1.8, 'alianza': 1.8, 'alianzas': 1.8,
        'unión': 1.5, 'union': 1.5, 'unidos': 1.5,

        # Mejoras y cambios positivos
        'mejora': 1.8, 'mejoras': 1.8, 'mejorar': 1.8, 'mejoría': 2.0,
        'mejoria': 2.0, 'mejor': 1.5, 'mejores': 1.5,
        'avance': 1.8, 'avances': 1.8, 'avanzar': 1.5,
        'progreso': 1.8, 'progresos': 1.8, 'progresando': 1.5,
        'recuperación': 2.0, 'recuperacion': 2.0, 'recuperar': 1.8,
        'recuperado': 2.0, 'recupera': 1.8,
        'fortalecimiento': 1.8, 'fortalecer': 1.8, 'fortalece': 1.8,
        'crecimiento': 1.8, 'crecer': 1.5, 'crece': 1.5,
        'desarrollo': 1.5, 'desarrollar': 1.5,

        # Éxito y logros
        'éxito': 2.5, 'exito': 2.5, 'exitoso': 2.5, 'exitosa': 2.5,
        'logro': 2.0, 'logros': 2.0, 'lograr': 1.8, 'logrado': 2.0,
        'conquista': 1.8, 'conseguir': 1.5, 'conseguido': 1.8,
        'triunfo': 2.0, 'victoria': 2.0,

        # Calidad y excelencia
        'excelente': 2.5, 'excelencia': 2.5, 'calidad': 1.8,
        'destacado': 1.8, 'destacada': 1.8, 'destacar': 1.5,
        'sobresaliente': 2.0, 'ejemplar': 2.0, 'modelo': 1.5,
        'referente': 1.8, 'líder': 1.8, 'lider': 1.8, 'liderazgo': 1.8,

        # Innovación y modernización
        'innovación': 2.0, 'innovacion': 2.0, 'innovador': 2.0, 'innovadora': 2.0,
        'moderno': 1.5, 'moderna': 1.5, 'modernización': 1.8, 'modernizacion': 1.8,
        'tecnología': 1.5, 'tecnologia': 1.5, 'digitalización': 1.5,
        'nuevo': 1.2, 'nueva': 1.2, 'nuevos': 1.2, 'nuevas': 1.2,

        # Eventos positivos / nacimientos
        'bebé': 2.5, 'bebe': 2.5, 'bebés': 2.5, 'bebes': 2.5,
        'nacimiento': 2.5, 'nacimientos': 2.5, 'nacer': 2.0, 'nació': 2.5,
        'nacio': 2.5, 'recién nacido': 3.0, 'recien nacido': 3.0,
        'madre': 1.5, 'mamá': 1.5, 'mama': 1.5,
        'familia': 1.5, 'familias': 1.5, 'familiar': 1.2,
        'felicidad': 2.5, 'feliz': 2.0, 'felices': 2.0,
        'alegría': 2.0, 'alegria': 2.0, 'celebración': 2.0, 'celebracion': 2.0,
        'fiesta': 1.5, 'festejo': 1.8,

        # Regalos y gestos
        'regalo': 2.0, 'regalos': 2.0, 'regalar': 2.0, 'regalando': 2.0,
        'obsequio': 1.8, 'obsequiar': 1.8, 'sorpresa': 1.8,
        'suite': 1.5, 'presidencial': 1.5, 'premium': 1.5, 'especial': 1.5,
        'gratis': 1.8, 'gratuito': 1.8, 'gratuita': 1.8,
        'beneficio': 1.8, 'beneficios': 1.8, 'beneficiar': 1.5,
        'bonificación': 1.5, 'bonificacion': 1.5, 'descuento': 1.5,

        # Paz y tranquilidad laboral
        'paz': 2.5, 'tranquilidad': 2.0, 'calma': 1.8, 'estabilidad': 2.0,
        'estable': 1.8, 'normalidad': 1.8, 'normal': 1.2,
        'clima': 1.0,  # se potencia con "buen" o "mejor"
        'ambiente': 1.0,  # se potencia con contexto

        # Apertura y expansión
        'inauguración': 2.0, 'inauguracion': 2.0, 'inaugurar': 1.8,
        'apertura': 1.8, 'abrir': 1.2, 'abre': 1.2, 'abrió': 1.5,
        'expansión': 1.8, 'expansion': 1.8, 'expandir': 1.5,
        'ampliación': 1.8, 'ampliacion': 1.8, 'ampliar': 1.5,

        # Inversión y recursos
        'inversión': 1.8, 'inversion': 1.8, 'invertir': 1.5, 'invierte': 1.5,
        'financiamiento': 1.5, 'capitalización': 1.8, 'capitalizacion': 1.8,
        'recursos': 1.2, 'fondos': 1.2,

        # Convenios y acuerdos formales
        'convenio': 1.8, 'convenios': 1.8, 'firmar': 1.2, 'firma': 1.2,
        'suscribir': 1.5, 'suscribe': 1.5, 'suscripción': 1.5,
        'contrato': 1.2, 'contratos': 1.2,

        # Reconocimientos
        'premio': 2.0, 'premios': 2.0, 'premiado': 2.0, 'premiada': 2.0,
        'reconocimiento': 2.0, 'reconocimientos': 2.0, 'reconocer': 1.5,
        'distinción': 2.0, 'distincion': 2.0, 'homenaje': 1.8,
        'galardón': 2.0, 'galardon': 2.0,

        # Salud positiva
        'curación': 2.0, 'curacion': 2.0, 'curar': 1.8, 'curado': 2.0,
        'sanación': 2.0, 'sanacion': 2.0, 'sanar': 1.8,
        'alta': 1.5, 'dado de alta': 2.0,
        'bienestar': 2.0, 'salud': 1.0, 'saludable': 1.8,
        'prevención': 1.5, 'prevencion': 1.5, 'prevenir': 1.5,
        'vacunación': 1.5, 'vacunacion': 1.5, 'vacunar': 1.5, 'vacuna': 1.2,

        # Operaciones exitosas
        'operación exitosa': 3.0, 'operacion exitosa': 3.0,
        'cirugía exitosa': 3.0, 'cirugia exitosa': 3.0,
        'trasplante': 1.5, 'trasplante exitoso': 3.0,

        # Compromiso
        'compromiso': 1.8, 'comprometido': 1.8, 'comprometida': 1.8,
        'dedicación': 1.8, 'dedicacion': 1.8, 'dedicado': 1.5,
        'vocación': 1.8, 'vocacion': 1.8,
        'esfuerzo': 1.5, 'esfuerzos': 1.5,

        # Apuesta y confianza
        'apuesta': 1.5, 'apostar': 1.5, 'apuestan': 1.5,
        'confianza': 1.8, 'confiar': 1.5, 'confía': 1.5, 'confia': 1.5,
        'optimismo': 2.0, 'optimista': 2.0,
        'esperanza': 1.8, 'esperanzador': 2.0,

        # Soluciones
        'solución': 2.0, 'solucion': 2.0, 'soluciones': 2.0,
        'resolver': 1.8, 'resuelto': 2.0, 'resuelve': 1.8,
        'solucionado': 2.0, 'solucionar': 1.8,

        # Primero / hitos
        'primero': 1.5, 'primera': 1.5, 'primer': 1.8,
        'histórico': 2.0, 'historico': 2.0, 'hito': 2.0,
        'récord': 1.8, 'record': 1.8,

        # Atención y servicio
        'atención': 1.2, 'atencion': 1.2, 'atender': 1.0,
        'servicio': 1.2, 'servicios': 1.2, 'asistencia': 1.2,
        'cuidado': 1.5, 'cuidados': 1.5, 'cuidar': 1.2,

        # Reafirmación positiva
        'reafirma': 1.5, 'reafirmar': 1.5, 'ratifica': 1.5, 'ratificar': 1.5,
        'confirma': 1.2, 'confirmar': 1.2,
        'mantiene': 1.2, 'sostiene': 1.2,
    }

    # =========================================================================
    # PALABRAS NEGATIVAS CON PESOS
    # =========================================================================
    PALABRAS_NEGATIVAS = {
        # Paros y medidas sindicales (NO incluir "para" solo, causa falsos positivos)
        'parar': 2.0, 'paran': 2.5,
        'retoma': 1.5, 'retomar': 1.2,  # retoma medida

        # Auditorías y sospechas (contexto negativo)
        'auditoría': 1.8, 'auditoria': 1.8, 'auditorías': 1.8, 'auditorias': 1.8,
        'revela': 1.8, 'revelar': 1.5, 'revelación': 2.0,
        'exponencial': 1.5,  # aumento exponencial = sospechoso
        'sobrecompras': 3.0, 'sobrecompra': 3.0,
        'sobreprecio': 3.0, 'sobreprecios': 3.0,
        'sobrefacturación': 3.0, 'sobrefacturacion': 3.0,

        # Fragilidad financiera
        'fragilidad': 2.5, 'frágil': 2.0, 'fragil': 2.0,
        'pasivo': 2.0, 'pasivos': 2.0,  # deuda
        'adelanto': 1.8, 'adelantos': 1.8,  # adelanto de dinero = problema liquidez
        'exigidos': 1.5, 'exigido': 1.5, 'exigir': 1.5,
        'ahorros': 1.2,  # "ahorros exigidos" = presión

        # Indignación y malestar
        'indignación': 2.5, 'indignacion': 2.5, 'indignado': 2.0, 'indignados': 2.0,

        # Suicidio
        'suicidio': 3.0, 'suicida': 2.5, 'suicidarse': 2.5,
        'femicidio': 3.0, 'femicida': 3.0,

        # Omisiones y negligencia
        'omisión': 2.5, 'omision': 2.5, 'omisiones': 2.5,
        'omitir': 2.0, 'omitió': 2.5,

        # Despidos (variantes)
        'despedida': 2.5, 'despedidas': 2.5,

        # Expulsión
        'expulsión': 2.5, 'expulsion': 2.5, 'expulsar': 2.0, 'expulsado': 2.5,

        # Ilícito
        'ilícito': 3.0, 'ilicito': 3.0, 'ilícita': 3.0, 'ilicita': 3.0,
        'ilegal': 3.0, 'ilegales': 3.0, 'ilegalidad': 3.0,

        # Deterioro
        'deterioro': 2.5, 'deteriora': 2.0, 'deteriorado': 2.5, 'deteriorando': 2.0,

        # Alertas
        'alerta': 2.0, 'alertar': 1.8, 'alertan': 2.0, 'alertó': 2.0,

        # Desapego a normas
        'desapego': 2.5,

        # Involucrados (contexto negativo)
        'involucrados': 2.0, 'involucrado': 2.0, 'involucrada': 2.0,

        # En la mira
        'mira': 1.5,  # "en la mira" = bajo sospecha

        # Cesar (despedir)
        'cesó': 2.0, 'ceso': 2.0, 'cesar': 1.8, 'cesado': 2.0, 'cesaron': 2.0,
        'cese': 2.0,

        # Controversia adicional
        'críticas': 2.0, 'criticó': 1.8, 'criticar': 1.5,

        # Crisis y problemas
        'crisis': 3.0, 'colapso': 3.0, 'colapsar': 2.5,
        'problema': 1.8, 'problemas': 1.8, 'problemático': 2.0, 'problematico': 2.0,
        'dificultad': 1.8, 'dificultades': 1.8, 'difícil': 1.5, 'dificil': 1.5,
        'complicación': 1.8, 'complicacion': 1.8, 'complicaciones': 1.8,
        'complicado': 1.5, 'complicada': 1.5,
        'obstáculo': 1.8, 'obstaculo': 1.8, 'obstáculos': 1.8, 'obstaculos': 1.8,
        'fracaso': 2.5, 'fracasar': 2.0, 'fracasado': 2.5,

        # Finanzas negativas
        'déficit': 3.0, 'deficit': 3.0, 'deuda': 2.5, 'deudas': 2.5,
        'pérdida': 2.5, 'perdida': 2.5, 'pérdidas': 2.5, 'perdidas': 2.5,
        'perder': 1.8, 'perdió': 2.0, 'perdio': 2.0,
        'quiebra': 3.5, 'quebrar': 3.0, 'bancarrota': 3.5,
        'insolvencia': 3.0, 'insolvente': 3.0,
        'deudor': 2.0, 'deudores': 2.0, 'moroso': 2.0, 'morosos': 2.0,
        'riesgo': 2.0, 'riesgos': 2.0, 'riesgoso': 2.0,
        'escasa': 1.8, 'escaso': 1.8, 'escasez': 2.0,
        'falta': 1.5, 'faltar': 1.5, 'faltante': 1.8,

        # Conflictos laborales
        'conflicto': 2.5, 'conflictos': 2.5, 'conflictivo': 2.0,
        'paro': 2.5, 'paros': 2.5, 'huelga': 2.5, 'huelgas': 2.5,
        'protesta': 2.0, 'protestas': 2.0, 'protestar': 1.8,
        'manifestación': 1.8, 'manifestacion': 1.8, 'manifestaciones': 1.8,
        'tensión': 2.0, 'tension': 2.0, 'tensiones': 2.0,
        'enfrentamiento': 2.0, 'enfrentamientos': 2.0,
        'disputa': 2.0, 'disputas': 2.0,
        'pelea': 2.0, 'peleas': 2.0,

        # Despidos y recortes
        'despido': 2.5, 'despidos': 2.5, 'despedir': 2.0, 'despedido': 2.5,
        'recorte': 2.0, 'recortes': 2.0, 'recortar': 1.8,
        'reducción': 1.5, 'reduccion': 1.5, 'reducir': 1.2,
        'ajuste': 1.5, 'ajustes': 1.5,

        # Denuncias y legal
        'denuncia': 2.5, 'denuncias': 2.5, 'denunciar': 2.0, 'denunciado': 2.5,
        'demanda': 2.0, 'demandas': 2.0, 'demandar': 1.8, 'demandado': 2.0,
        'acusación': 2.5, 'acusacion': 2.5, 'acusaciones': 2.5,
        'acusar': 2.0, 'acusado': 2.5, 'acusada': 2.5,
        'imputar': 2.5, 'imputación': 2.5, 'imputacion': 2.5, 'imputado': 2.5,
        'investigación': 1.5, 'investigacion': 1.5, 'investigar': 1.2, 'investigado': 1.8,
        'procesado': 2.5, 'procesamiento': 2.0, 'procesar': 2.0,
        'juicio': 2.0, 'juicios': 2.0, 'judicial': 1.5,
        'irregularidad': 2.5, 'irregularidades': 2.5, 'irregular': 2.0,
        'fraude': 3.5, 'fraudulento': 3.0, 'estafa': 3.5, 'estafar': 3.0,
        'corrupción': 3.5, 'corrupcion': 3.5, 'corrupto': 3.0,

        # Sanciones
        'sanción': 2.5, 'sancion': 2.5, 'sanciones': 2.5,
        'sancionar': 2.0, 'sancionado': 2.5,
        'multa': 2.0, 'multas': 2.0, 'multar': 1.8, 'multado': 2.0,
        'penalización': 2.0, 'penalizacion': 2.0, 'penalizar': 1.8,
        'castigo': 2.0, 'castigar': 1.8,
        'incumplimiento': 2.0, 'incumplir': 1.8,

        # Quejas
        'queja': 2.0, 'quejas': 2.0, 'quejar': 1.5,
        'reclamo': 1.8, 'reclamos': 1.8, 'reclamar': 1.5, 'reclaman': 1.8,
        'disconformidad': 1.8, 'disconforme': 1.8,
        'malestar': 2.0, 'descontento': 2.0,

        # Cierre y suspensión
        'cierre': 2.5, 'cerrar': 2.0, 'cerrado': 2.0, 'cierra': 2.0,
        'clausura': 2.5, 'clausurar': 2.0, 'clausurado': 2.5,
        'suspensión': 2.5, 'suspension': 2.5, 'suspender': 2.0, 'suspendido': 2.5,
        'cancelación': 2.0, 'cancelacion': 2.0, 'cancelar': 1.8, 'cancelado': 2.0,

        # Intervención (contexto negativo en CASMU)
        'intervención': 2.0, 'intervencion': 2.0, 'intervenir': 1.8,
        'intervenido': 2.0, 'interventor': 1.8,

        # Negligencia y errores
        'negligencia': 3.0, 'negligente': 3.0,
        'mala praxis': 3.5, 'malapraxis': 3.5,
        'error': 1.8, 'errores': 1.8, 'erróneo': 1.8, 'erroneo': 1.8,
        'falla': 2.0, 'fallas': 2.0, 'fallar': 1.8, 'falló': 2.0, 'fallo': 2.0,
        'deficiencia': 2.0, 'deficiencias': 2.0, 'deficiente': 2.0,

        # Malo / negativo
        'malo': 2.0, 'mala': 2.0, 'malos': 2.0, 'malas': 2.0,
        'mal': 1.8, 'peor': 2.5, 'peores': 2.5,
        'pésimo': 3.0, 'pesimo': 3.0, 'pésima': 3.0, 'pesima': 3.0,
        'terrible': 2.5, 'horrible': 2.5, 'desastroso': 3.0, 'catastrófico': 3.0,
        'negativo': 1.8, 'negativa': 1.8,

        # Salud negativa
        'fallecimiento': 2.5, 'fallecer': 2.0, 'fallecido': 2.5, 'fallece': 2.0,
        'muerte': 2.5, 'muerto': 2.5, 'murió': 2.5, 'murio': 2.5, 'morir': 2.0,
        'víctima': 2.0, 'victima': 2.0, 'víctimas': 2.0, 'victimas': 2.0,
        'grave': 2.0, 'graves': 2.0, 'gravedad': 2.0,
        'crítico': 2.0, 'critico': 2.0, 'crítica': 1.5,  # "crítica" puede ser neutral
        'emergencia': 1.5, 'urgencia': 1.5, 'urgente': 1.5,

        # Abandono y carencias
        'abandono': 2.5, 'abandonar': 2.0, 'abandonado': 2.5,
        'carencia': 2.0, 'carencias': 2.0, 'carecer': 1.8,
        'precario': 2.0, 'precaria': 2.0, 'precariedad': 2.0,
        'deterioro': 2.0, 'deteriorar': 1.8, 'deteriorado': 2.0,

        # Demoras
        'demora': 1.8, 'demoras': 1.8, 'demorar': 1.5, 'demorado': 1.8,
        'retraso': 1.8, 'retrasos': 1.8, 'retrasar': 1.5, 'retrasado': 1.8,
        'espera': 1.2, 'esperas': 1.5,

        # Preocupación
        'preocupación': 1.8, 'preocupacion': 1.8, 'preocupante': 2.0,
        'preocupado': 1.5, 'preocupada': 1.5, 'preocupar': 1.5,
        'alarma': 2.0, 'alarmante': 2.5, 'alarmar': 1.8,
        'inquietud': 1.8, 'inquietante': 2.0,

        # Escándalo y controversia
        'escándalo': 2.5, 'escandalo': 2.5, 'escándalos': 2.5, 'escandalos': 2.5,
        'escándalo': 2.5, 'escandaloso': 2.5,
        'polémica': 2.0, 'polemica': 2.0, 'polémico': 2.0, 'polemico': 2.0,
        'controversia': 2.0, 'controversial': 2.0,
        'sospecha': 2.0, 'sospechas': 2.0, 'sospechoso': 2.0, 'sospechar': 1.8,
    }

    # =========================================================================
    # FRASES COMPUESTAS
    # =========================================================================
    FRASES_POSITIVAS = [
        # Prevención de enfermedades (positivo aunque mencione enfermedad)
        ('evitar la', 2.5),  # evitar la muerte súbita
        ('busca evitar', 2.5),
        ('para detectar', 2.0),  # para detectar enfermedades = servicio
        ('para prevenir', 2.5),
        ('aplica', 1.5),  # aplica tratamiento/estudio
        ('detectar osteoporosis', 2.0),
        ('detectar', 1.2),

        # Nuevos servicios médicos
        ('suma cti', 2.5),
        ('suma unidad', 2.5),
        ('suma una unidad', 2.5),
        ('suma servicio', 2.5),
        ('ofrece estudio', 2.0),
        ('ofrece tratamiento', 2.0),
        ('brinda tratamiento', 2.5),
        ('brinda tratamientos', 2.5),

        # Pionero / innovación
        ('fue pionera', 3.0),
        ('fue pionero', 3.0),
        ('es pionera', 2.5),
        ('es pionero', 2.5),
        ('novedoso concepto', 2.5),

        # Incursionar / liderar
        ('incursiona en', 2.5),
        ('lidera tratamiento', 3.0),
        ('lidera el tratamiento', 3.0),

        # Cirugías exitosas / inéditas
        ('realizó inédita', 3.0),
        ('inédita cirugía', 3.0),
        ('compleja cirugía', 2.0),
        ('cirugía de tumor', 1.5),  # generalmente exitosa si se reporta

        # Distinciones
        ('fue distinguido', 3.0),
        ('fue distinguida', 3.0),

        # Concientización
        ('concientizó sobre', 2.5),
        ('promovió la adopción', 2.5),
        ('hábitos saludables', 2.0),

        # Balance positivo
        ('balance positivo', 3.5),
        ('tuvo balance positivo', 3.5),
        ('anunció balance positivo', 3.5),

        # Consolidación
        ('se consolida', 2.5),
        ('consolida como', 2.5),

        # Especialización
        ('especializada en', 2.0),
        ('unidad especializada', 2.5),

        # 90 años (celebración)
        ('90 años', 2.0),
        ('aniversario', 2.0),

        # Relaciones laborales
        ('sin conflictos', 3.0),
        ('sin conflicto', 3.0),
        ('sin problemas', 2.5),
        ('sin inconvenientes', 2.5),
        ('buen clima', 2.5),
        ('mejor clima', 2.5),
        ('clima interno', 1.5),  # generalmente positivo en contexto
        ('clima positivo', 3.0),
        ('paz laboral', 3.0),
        ('armonía laboral', 3.0),
        ('diálogo social', 2.5),
        ('mesa de diálogo', 2.0),
        ('apuesta al diálogo', 2.5),
        ('apuesta fuerte', 2.0),

        # Nacimientos y familia
        ('primer bebé', 3.5),
        ('primer bebe', 3.5),
        ('primera bebé', 3.5),
        ('primera bebe', 3.5),
        ('bebé del año', 3.0),
        ('bebe del año', 3.0),
        ('recién nacido', 2.5),
        ('suite presidencial', 2.0),
        ('regalando la suite', 2.5),

        # Convenios y alianzas
        ('firma convenio', 2.0),
        ('firman convenio', 2.0),
        ('firmó convenio', 2.0),
        ('nuevo convenio', 2.0),
        ('nueva alianza', 2.5),
        ('alianza estratégica', 2.5),
        ('acuerdo estratégico', 2.5),
        ('acuerdo histórico', 3.0),

        # Mejoras
        ('mejora continua', 2.0),
        ('plan de mejora', 2.0),
        ('en recuperación', 2.0),
        ('buena noticia', 3.0),
        ('buenas noticias', 3.0),
        ('paso adelante', 2.0),
        ('avance significativo', 2.5),

        # Compromiso
        ('compromiso con', 1.8),
        ('reafirma compromiso', 2.0),
        ('reafirma su compromiso', 2.0),

        # Atención médica
        ('atención de calidad', 2.5),
        ('servicio de excelencia', 3.0),
        ('operación exitosa', 3.0),
        ('cirugía exitosa', 3.0),
        ('intervención exitosa', 3.0),
        ('compleja operación', 1.5),  # generalmente exitosa si se reporta

        # Estabilidad
        ('situación estable', 2.0),
        ('se estabiliza', 2.0),
        ('logra estabilidad', 2.5),

        # Inauguraciones
        ('nueva sede', 2.0),
        ('nuevo centro', 2.0),
        ('nueva unidad', 2.0),
    ]

    FRASES_NEGATIVAS = [
        # Paros sindicales
        ('para por', 3.0),
        ('paro por', 3.0),
        ('retoma la medida', 2.5),
        ('retoma medida', 2.5),

        # Auditorías y sospechas
        ('auditoría revela', 3.0),
        ('auditoria revela', 3.0),
        ('aumento exponencial', 2.5),
        ('aumento de', 1.5),  # en contexto de pagos sospechosos
        ('en la mira', 2.5),
        ('estuvieron en la mira', 3.0),
        ('bajo la mira', 2.5),

        # Fragilidad financiera
        ('números rojos', 3.5),
        ('numeros rojos', 3.5),
        ('adelanto al', 2.0),
        ('otro adelanto', 2.5),
        ('pasivo de', 2.0),
        ('pasivo volvió a subir', 3.0),
        ('ahorros exigidos', 2.5),

        # Indignación
        ('expresó indignación', 2.5),
        ('hay indignación', 2.5),

        # Suicidio
        ('suicidio de', 3.0),
        ('suicidio femicida', 3.5),

        # Omisiones
        ('hubo omisiones', 3.0),
        ('precedido de omisiones', 3.0),

        # Despidos
        ('médicos despedidos', 3.0),
        ('pediatra despedida', 3.0),
        ('fue despedida', 2.5),
        ('fue despedido', 2.5),

        # Expulsión
        ('expulsión de', 2.5),
        ('fue ilícita', 3.0),

        # Deterioro
        ('alerta por deterioro', 3.0),
        ('deterioro en', 2.5),

        # Desapego a normas
        ('desapego a las normas', 3.5),
        ('desapego a normas', 3.5),

        # Conflicto de intereses
        ('compiten con', 2.0),
        ('que compiten', 2.0),
        ('conflicto de interés', 3.0),
        ('conflicto de intereses', 3.0),

        # Desmiente / defensiva
        ('desmiente cifra', 2.0),
        ('desmiente', 1.5),
        ('manifestó sorpresa', 2.0),

        # Irregularidades y denuncias
        ('denunciará irregularidades', 3.0),
        ('denunciar irregularidades', 3.0),

        # Despedidos + reclamos
        ('despedidos reclaman', 3.0),
        ('no cumplió con', 2.5),

        # Liquidez problemática
        ('dar liquidez', 2.0),
        ('para dar liquidez', 2.5),
        ('nuevo adelanto', 2.5),

        # Reestructura (indica problemas)
        ('reestructura', 2.0),
        ('reestructuración', 2.0),
        ('reestructuracion', 2.0),
        ('profundización de medidas', 2.5),
        ('profundizacion de medidas', 2.5),

        # Veedores / interventores en contexto
        ('trabajo con interventores', 2.0),
        ('trabajar con veedores', 1.8),

        # Críticas
        ('críticas de', 2.0),
        ('controversia en', 2.0),

        # Cesantía
        ('cesó al gerente', 3.0),
        ('cesó al', 2.5),

        # Involucrados
        ('involucrados con', 2.5),
        ('involucrados en', 2.5),

        # Crisis financiera
        ('riesgo asistencial', 3.5),
        ('escasa liquidez', 3.0),
        ('falta de liquidez', 3.0),
        ('déficit de', 3.0),
        ('déficit millonario', 3.5),
        ('pérdida de', 2.5),
        ('pérdidas millonarias', 3.5),
        ('situación crítica', 3.0),
        ('situación grave', 3.0),
        ('en crisis', 3.0),
        ('crisis financiera', 3.5),
        ('al borde', 2.5),
        ('en quiebra', 3.5),

        # Conflictos
        ('en conflicto', 2.5),
        ('conflicto laboral', 3.0),
        ('conflicto sindical', 3.0),
        ('en disputa', 2.5),
        ('bajo sospecha', 2.5),
        ('si no te gusta', 2.0),
        ('te vas', 2.0),

        # Legal
        ('denuncia contra', 2.5),
        ('denuncias contra', 2.5),
        ('mala praxis', 3.5),
        ('demanda judicial', 3.0),
        ('proceso judicial', 2.5),

        # Intervención
        ('mutualista intervenida', 2.5),
        ('fue intervenida', 2.5),
        ('bajo intervención', 2.5),

        # Cierre
        ('cierre del', 3.0),
        ('cierre de', 2.5),
        ('riesgo de cierre', 3.5),
        ('podría cerrar', 3.0),

        # Otros
        ('no hay solución', 3.0),
        ('sin solución', 3.0),
        ('empeora', 2.5),
        ('se agrava', 2.5),
    ]

    # =========================================================================
    # INTENSIFICADORES Y NEGADORES
    # =========================================================================
    INTENSIFICADORES = {
        'muy': 1.6, 'mucho': 1.5, 'muchísimo': 2.0, 'muchisimo': 2.0,
        'extremadamente': 2.0, 'totalmente': 1.8, 'completamente': 1.7,
        'absolutamente': 1.8, 'bastante': 1.4, 'demasiado': 1.5,
        'gravemente': 1.8, 'seriamente': 1.6, 'profundamente': 1.6,
        'altamente': 1.5, 'sumamente': 1.7, 'increíblemente': 1.8,
        'enormemente': 1.6, 'tremendamente': 1.7, 'fuertemente': 1.5,
        'fuerte': 1.3, 'gran': 1.3, 'grande': 1.3, 'enorme': 1.5,
    }

    NEGADORES = {
        'no', 'sin', 'nunca', 'ningún', 'ningun', 'ninguno', 'ninguna',
        'tampoco', 'jamás', 'jamas', 'ni', 'nada', 'nadie',
    }

    def __init__(self):
        # Compilar patrones de frases para búsqueda eficiente
        self.frases_pos_pattern = [(f.lower(), w) for f, w in self.FRASES_POSITIVAS]
        self.frases_neg_pattern = [(f.lower(), w) for f, w in self.FRASES_NEGATIVAS]

    def analizar(self, texto: str) -> tuple[str, float, dict]:
        """
        Analiza el sentimiento del texto.
        Retorna: (sentimiento, score, detalles)
        """
        texto_lower = texto.lower()
        palabras = re.findall(r'\b[\w]+\b', texto_lower)

        score_pos = 0.0
        score_neg = 0.0
        encontradas_pos = []
        encontradas_neg = []

        # 1. Buscar frases compuestas primero (tienen prioridad)
        for frase, peso in self.frases_pos_pattern:
            if frase in texto_lower:
                score_pos += peso
                encontradas_pos.append(f'"{frase}"')

        for frase, peso in self.frases_neg_pattern:
            if frase in texto_lower:
                score_neg += peso
                encontradas_neg.append(f'"{frase}"')

        # 2. Analizar palabras individuales con contexto
        i = 0
        while i < len(palabras):
            palabra = palabras[i]

            # Detectar negadores
            if palabra in self.NEGADORES:
                # Buscar la siguiente palabra significativa
                j = i + 1
                multiplicador = 1.0

                # Saltar intensificadores después del negador
                while j < len(palabras) and palabras[j] in self.INTENSIFICADORES:
                    multiplicador *= self.INTENSIFICADORES[palabras[j]]
                    j += 1

                if j < len(palabras):
                    siguiente = palabras[j]

                    # Negación de negativo = positivo (ej: "sin conflictos")
                    if siguiente in self.PALABRAS_NEGATIVAS:
                        peso = self.PALABRAS_NEGATIVAS[siguiente] * multiplicador * 0.8
                        score_pos += peso
                        encontradas_pos.append(f'{palabra} {siguiente}')
                        i = j + 1
                        continue

                    # Negación de positivo = parcialmente negativo
                    elif siguiente in self.PALABRAS_POSITIVAS:
                        peso = self.PALABRAS_POSITIVAS[siguiente] * multiplicador * 0.5
                        score_neg += peso
                        encontradas_neg.append(f'{palabra} {siguiente}')
                        i = j + 1
                        continue

            # Detectar intensificadores
            multiplicador = 1.0
            if palabra in self.INTENSIFICADORES:
                multiplicador = self.INTENSIFICADORES[palabra]
                i += 1
                if i < len(palabras):
                    palabra = palabras[i]
                else:
                    break

            # Evaluar palabra
            if palabra in self.PALABRAS_POSITIVAS:
                peso = self.PALABRAS_POSITIVAS[palabra] * multiplicador
                score_pos += peso
                if multiplicador > 1:
                    encontradas_pos.append(f'{palabras[i-1]} {palabra}')
                else:
                    encontradas_pos.append(palabra)

            elif palabra in self.PALABRAS_NEGATIVAS:
                peso = self.PALABRAS_NEGATIVAS[palabra] * multiplicador
                score_neg += peso
                if multiplicador > 1:
                    encontradas_neg.append(f'{palabras[i-1]} {palabra}')
                else:
                    encontradas_neg.append(palabra)

            i += 1

        # 3. Calcular resultado final
        total = score_pos + score_neg
        diferencia = score_pos - score_neg

        detalles = {
            'positivas': list(set(encontradas_pos)),
            'negativas': list(set(encontradas_neg)),
            'score_positivo': round(score_pos, 2),
            'score_negativo': round(score_neg, 2),
        }

        # Umbral más sensible: diferencia > 1.0 ya no es neutro
        if total == 0:
            return "NEUTRO", 0.5, detalles

        if abs(diferencia) < 1.0:
            return "NEUTRO", 0.5, detalles
        elif diferencia > 0:
            confianza = min(0.5 + (diferencia / (total * 1.5)), 0.95)
            return "POSITIVO", round(confianza, 2), detalles
        else:
            confianza = min(0.5 + (abs(diferencia) / (total * 1.5)), 0.95)
            return "NEGATIVO", round(confianza, 2), detalles


def buscar_noticias(termino, año, analizador):
    """Busca noticias de un año específico"""
    session = requests.Session()
    session.headers.update(HEADERS)
    noticias = []

    for nombre_medio, dominio in MEDIOS.items():
        try:
            query = f"{termino} site:{dominio} after:{año}-01-01 before:{año}-12-31"
            encoded_query = requests.utils.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=UY&ceid=UY:es-419"

            response = session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "xml")

            items = soup.find_all("item")
            for item in items[:15]:
                titulo = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                fecha_str = item.pubDate.text if item.pubDate else ""

                if termino.lower() in titulo.lower():
                    try:
                        fecha = datetime.strptime(fecha_str[:16], "%a, %d %b %Y")
                        mes = fecha.month
                    except:
                        fecha = None
                        mes = 6

                    # Analizar sentimiento
                    sentimiento, score, detalles = analizador.analizar(titulo)

                    noticias.append({
                        'titulo': titulo,
                        'url': link,
                        'medio': nombre_medio,
                        'año': año,
                        'mes': mes,
                        'fecha': fecha.isoformat() if fecha else f"{año}-06-15",
                        'sentimiento': sentimiento,
                        'score': score,
                        'palabras_positivas': detalles['positivas'],
                        'palabras_negativas': detalles['negativas'],
                    })

            time.sleep(0.3)
        except Exception as e:
            print(f"  Error en {nombre_medio}: {e}")

    return noticias


def main():
    print("=" * 60)
    print("RECOLECTANDO NOTICIAS CASMU 2022-2026")
    print("Con análisis de sentimiento fine-tuned")
    print("=" * 60)

    analizador = AnalizadorSentimientoFineTuned()
    todas = []

    for año in range(2022, 2027):
        print(f"\n🔍 Buscando año {año}...")
        noticias = buscar_noticias("CASMU", año, analizador)
        print(f"   Encontradas: {len(noticias)}")

        # Mostrar distribución
        pos = sum(1 for n in noticias if n['sentimiento'] == 'POSITIVO')
        neg = sum(1 for n in noticias if n['sentimiento'] == 'NEGATIVO')
        neu = sum(1 for n in noticias if n['sentimiento'] == 'NEUTRO')
        print(f"   📊 POS: {pos} | NEG: {neg} | NEU: {neu}")

        todas.extend(noticias)
        time.sleep(1)

    # Eliminar duplicados
    vistas = set()
    unicas = []
    for n in todas:
        key = n['titulo'][:40].lower()
        if key not in vistas:
            vistas.add(key)
            unicas.append(n)

    print("\n" + "=" * 60)
    print(f"✅ Total noticias únicas: {len(unicas)}")

    # Distribución final
    pos = sum(1 for n in unicas if n['sentimiento'] == 'POSITIVO')
    neg = sum(1 for n in unicas if n['sentimiento'] == 'NEGATIVO')
    neu = sum(1 for n in unicas if n['sentimiento'] == 'NEUTRO')
    print(f"\n📊 DISTRIBUCIÓN FINAL:")
    print(f"   🟢 POSITIVO: {pos} ({100*pos/len(unicas):.1f}%)")
    print(f"   🔴 NEGATIVO: {neg} ({100*neg/len(unicas):.1f}%)")
    print(f"   🟡 NEUTRO:   {neu} ({100*neu/len(unicas):.1f}%)")

    # Guardar
    import os
    os.makedirs('data', exist_ok=True)

    with open('data/noticias_casmu.json', 'w', encoding='utf-8') as f:
        json.dump(unicas, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Datos guardados en data/noticias_casmu.json")
    print("=" * 60)

    # Mostrar algunos ejemplos
    print("\n📰 EJEMPLOS DE CLASIFICACIÓN:")
    print("-" * 60)

    for sent in ['POSITIVO', 'NEGATIVO', 'NEUTRO']:
        ejemplos = [n for n in unicas if n['sentimiento'] == sent][:2]
        for n in ejemplos:
            print(f"\n{sent}: {n['titulo'][:70]}...")
            if n['palabras_positivas']:
                print(f"   ✅ {', '.join(n['palabras_positivas'][:5])}")
            if n['palabras_negativas']:
                print(f"   ❌ {', '.join(n['palabras_negativas'][:5])}")


if __name__ == "__main__":
    main()
