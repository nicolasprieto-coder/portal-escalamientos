# Portal de Escalamientos · MOVii RED

Portal Django para gestionar escalamientos de incidencias, integrado con Grafana/Elasticsearch, IA (Gemini + Groq) y Gmail.

---

## Requisitos previos

Antes de empezar asegúrate de tener instalado:

- **Python 3.11 o superior**
- **Git**
- Acceso a **Grafana self-hosted** con Elasticsearch
- Cuenta en **Google AI Studio** (para Gemini) o **Groq** (plan B)
- Cuenta **Gmail corporativa** para envío de correos
- *(Opcional)* Credenciales de **Gmail API** para lectura de respuestas

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-org/portal-escalamientos.git
cd portal-escalamientos
```

### 2. Crear y activar entorno virtual

**Linux / Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (cmd):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Agregar el archivo de configuración de variables de entorno en carpeta raiz del proyecto


## En el directorio config en el archivo settings se configuran los servicios que se requieren usar. 
## En este caso Configuración de APIS y SMTP
```bash
# ── Grafana / Elasticsearch ──
GRAFANA_URL=http://192.168.x.x:3000          # URL de tu Grafana
GRAFANA_TOKEN=glsa_xxxxxxxxxxxxxxxxxxxx       # Service Account Token de Grafana
GRAFANA_DATASOURCE_ID=2                       # ID numérico del datasource en Grafana

# ── IA (orden de prioridad: Gemini → Groq → Simulado) ──
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxxxxxx    # Desde aistudio.google.com
GEMINI_MODEL=gemini-2.0-flash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx         # Desde console.groq.com

# ── Correo SMTP ──
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-correo@tuempresa.com
EMAIL_HOST_PASSWORD=tu-app-password           # App Password de Gmail, no la contraseña normal
DEFAULT_FROM_EMAIL=escalamientos@tuempresa.com
```


### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (administrador)

```bash
python manage.py createsuperuser
```


```bash
python catalogo/migrate_json.py
```

### 8. Ejecutar el servidor

```bash
python manage.py runserver
```

Abre el navegador en: **http://localhost:8000**



##  Estructura del proyecto

```
portal-escalamientos/
├── config/                  # Configuración Django
│   ├── settings.py
│   └── urls.py
├── incidencias/             # App principal
│   ├── models.py            # Escalamiento, MensajeNotificado
│   ├── views.py             # Todas las vistas
│   ├── forms.py             # Formularios
│   └── urls.py
├── catalogo/                # Gestión de servicios
│   ├── models.py            # Servicio, Componente, Contacto
│   ├── views.py             # CRUD de servicios
│   ├── utils.py             # Helpers del catálogo
│   └── migrate_json.py      # Migración desde JSON
├── services/                # Integraciones externas
│   ├── grafana.py           # Consulta logs en Elasticsearch
│   ├── ai_service.py        # Gemini + Groq (generación de borradores)
│   ├── gmail_reader.py      # Lectura de respuestas vía Gmail API
│   └── mail.py              # Envío de correos HTML
├── templates/               # Templates HTML
│   ├── base.html
│   ├── registration/
│   │   └── login.html
│   ├── incidencias/
│   │   ├── inicio.html
│   │   ├── previsualizar.html
│   │   ├── historial.html
│   │   ├── detalle.html
│   │   └── dashboard.html
│   └── catalogo/
│       ├── lista.html
│       └── form_servicio.html
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Flujo del sistema

```
1. Operador abre el portal e inicia sesión
2. Selecciona el servicio afectado y la hora de inicio de la novedad
3. El sistema consulta los logs en Grafana/Elasticsearch
4. Detecta automáticamente el error más frecuente
5. Gemini (o Groq como respaldo) redacta el correo formal
6. El operador revisa el borrador, ajusta destinatarios y confirma
7. Se envía el correo con los logs adjuntos
8. El portal detecta respuestas y notifica al equipo
9. El operador cierra el escalamiento cuando se resuelve
```

---