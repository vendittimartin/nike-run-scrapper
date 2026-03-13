# Nike Run Buenos Aires — Monitor de Eventos

Bot que revisa automáticamente [nike.com.ar/run-buenos-aires](https://www.nike.com.ar/run-buenos-aires) cada 30 minutos y te manda un mail cuando aparece un evento disponible ("Inscribirme ahora").

- **Hosting**: GitHub Actions (gratis, sin servidor)
- **Email**: Resend (gratis, 3000 mails/mes)
- **Estado persistente**: `notified_events.json` se commitea automáticamente → no te llega el mismo evento dos veces

---

## Setup (una sola vez)

### 1. Crear repo en GitHub

1. Andá a [github.com/new](https://github.com/new)
2. Nombre: `nike-monitor` (o el que quieras)
3. **Visibility: Public** ← importante para tener minutos ilimitados gratis
4. No inicialices con README
5. Crealo

### 2. Subir este código al repo

Desde la carpeta del proyecto en tu terminal:

```bash
git init
git add .
git commit -m "feat: Nike running monitor"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/nike-monitor.git
git push -u origin main
```

### 3. Crear cuenta en Resend y obtener API Key

1. Andá a [resend.com](https://resend.com) y registrate con `vendittimartin@gmail.com`
2. Verificá tu email
3. En el dashboard, andá a **API Keys** → **Create API Key**
4. Copiá la key (empieza con `re_...`)

### 4. Agregar el secret en GitHub

1. En tu repo de GitHub: **Settings** → **Secrets and variables** → **Actions**
2. Click en **New repository secret**
3. Name: `RESEND_API_KEY`
4. Value: pegá la key de Resend
5. Click **Add secret**

### 5. Habilitar Actions y hacer un test manual

1. En tu repo: tab **Actions**
2. Click en **Nike Running Monitor** en la lista de la izquierda
3. Click en **Run workflow** → **Run workflow** (botón verde)
4. Esperá ~2 minutos y revisá los logs

Si hay eventos disponibles, te va a llegar el mail. Si no, igual vas a ver en los logs cuántos eventos encontró.

---

## Cómo funciona

```
Cada 30 min
    ↓
GitHub Actions ejecuta scraper.py
    ↓
Playwright carga nike.com.ar/run-buenos-aires (headless Chromium)
    ↓
Busca botones "Inscribirme ahora"
    ↓
Compara con notified_events.json (IDs ya notificados)
    ↓
Por cada evento NUEVO → envía mail via Resend
    ↓
Guarda los nuevos IDs en notified_events.json
    ↓
Commitea el JSON al repo (para persistir entre runs)
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `scraper.py` | Lógica principal: scraping + email |
| `requirements.txt` | Dependencias Python |
| `.github/workflows/monitor.yml` | Cron job en GitHub Actions |
| `notified_events.json` | IDs de eventos ya notificados (se actualiza automáticamente) |

---

## Troubleshooting

**No recibo mails**
- Revisá los logs del Action en la tab Actions de GitHub
- Verificá que `RESEND_API_KEY` esté bien cargado en Secrets
- Revisá la carpeta Spam

**El Action falla**
- Mirá el log del step que falla en la tab Actions
- Si falla el scraping, puede ser que Nike cambió la estructura del sitio

**Quiero recibir notificaciones de todos los eventos desde cero**
- Editá `notified_events.json` y dejalo como `[]`
- Commitealo y el próximo run te va a notificar todos los disponibles
