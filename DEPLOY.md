# Guía de Despliegue - CASMU News Analyzer

## 1. Despliegue en Streamlit Cloud (Gratuito)

### Paso 1: Crear repositorio en GitHub

```bash
cd casmu_news_analyzer
git init
git add .
git commit -m "Initial commit: CASMU News Analyzer"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/casmu-news-analyzer.git
git push -u origin main
```

### Paso 2: Desplegar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Click en "New app"
4. Selecciona tu repositorio: `casmu-news-analyzer`
5. Branch: `main`
6. Main file path: `app.py`
7. Click en "Deploy"

La app estará disponible en: `https://TU_USUARIO-casmu-news-analyzer-app-XXXXX.streamlit.app`

### Paso 3: Configurar Secrets (para la app)

En Streamlit Cloud, ve a Settings > Secrets y agrega:

```toml
# No se necesitan secrets para la app básica
# La contraseña está hardcodeada en el código
```

---

## 2. Configurar Actualización Semanal con Email

### Configurar GitHub Secrets

Para que el cron semanal funcione con emails, configura estos secrets en tu repositorio:

1. Ve a tu repositorio en GitHub
2. Settings > Secrets and variables > Actions
3. Click "New repository secret" para cada uno:

| Secret Name | Valor | Descripción |
|-------------|-------|-------------|
| `EMAIL_SENDER` | tu-email@gmail.com | Email desde el que se envían reportes |
| `EMAIL_PASSWORD` | xxxx-xxxx-xxxx-xxxx | App Password de Gmail (ver abajo) |
| `EMAIL_RECIPIENT` | pedro@ciudadana.city | Email destino (ya configurado) |
| `SMTP_SERVER` | smtp.gmail.com | Servidor SMTP |
| `SMTP_PORT` | 587 | Puerto SMTP |

### Crear App Password en Gmail

1. Ve a [myaccount.google.com](https://myaccount.google.com)
2. Seguridad > Verificación en 2 pasos (activar si no está)
3. Seguridad > Contraseñas de aplicaciones
4. Selecciona "Otra" y ponle nombre "CASMU Analyzer"
5. Copia la contraseña generada (16 caracteres)
6. Usa esa contraseña como `EMAIL_PASSWORD`

### Ejecutar manualmente

Para probar el workflow:
1. Ve a Actions en tu repositorio
2. Selecciona "Weekly CASMU News Update"
3. Click "Run workflow"

El cron se ejecuta automáticamente cada lunes a las 9:00 AM UTC.

---

## 3. Dominio Personalizado

### Opción A: Subdominio gratuito con Streamlit

Tu app ya tiene un dominio gratuito tipo:
`https://tu-usuario-casmu-news-analyzer-app.streamlit.app`

### Opción B: Dominio personalizado (requiere dominio propio)

Streamlit Cloud soporta dominios personalizados en el plan gratuito:

1. **Compra un dominio** en:
   - Namecheap (~$10/año)
   - Google Domains (~$12/año)
   - Cloudflare Registrar (al costo)
   - Porkbun (~$9/año)

2. **Configura DNS CNAME**:

   En tu proveedor de dominio, agrega un registro CNAME:
   ```
   Tipo: CNAME
   Nombre: @ (o www, o el subdominio que quieras)
   Valor: cname.streamlit.app
   TTL: 3600
   ```

3. **Conecta en Streamlit Cloud**:
   - Ve a tu app en share.streamlit.io
   - Settings > Custom domain
   - Ingresa tu dominio: `casmu-analyzer.tu-dominio.com`
   - Click "Save"

4. **Espera propagación DNS** (puede tomar hasta 48 horas)

### Opción C: Dominio gratuito con servicios externos

Para un dominio 100% gratuito, puedes usar:

1. **Freenom** (dominios .tk, .ml, .ga, .cf, .gq) - No siempre disponible
2. **js.org** (subdominio para proyectos JavaScript/web)
3. **is-a.dev** (para desarrolladores, gratis)

---

## 4. Estructura de Archivos

```
casmu_news_analyzer/
├── app.py                    # Dashboard principal
├── collect_data.py           # Script de recolección + NLP
├── update_news.py            # Actualización semanal
├── requirements.txt          # Dependencias
├── DEPLOY.md                 # Esta guía
├── .gitignore
├── .streamlit/
│   └── config.toml           # Configuración de tema
├── .github/
│   └── workflows/
│       └── weekly_update.yml # GitHub Actions cron
└── data/
    └── noticias_casmu.json   # Base de datos de noticias
```

---

## 5. Mantenimiento

### Actualizar datos manualmente

```bash
python collect_data.py
```

### Ver logs del cron

1. GitHub > tu repositorio > Actions
2. Click en la ejecución que quieras revisar
3. Ver logs de cada paso

### Cambiar la contraseña

Edita `app.py` línea donde dice:
```python
if st.session_state["password"] == "CASMUMediaAnalyzer":
```

### Agregar más medios

Edita `collect_data.py`, diccionario `MEDIOS`:
```python
MEDIOS = {
    'El País': 'elpais.com.uy',
    'El Observador': 'elobservador.com.uy',
    # Agregar más aquí...
}
```

---

## Contacto y Soporte

- Dashboard: `https://TU_URL.streamlit.app`
- Reportes semanales: pedro@ciudadana.city
- Contraseña de acceso: `CASMUMediaAnalyzer`
