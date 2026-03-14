# Nike Run Buenos Aires — Monitor de Eventos

Bot que revisa automáticamente [nike.com.ar/run-buenos-aires](https://www.nike.com.ar/run-buenos-aires) a través de un mail cuando aparece un evento disponible

- **Hosting**: GitHub Actions (event)
- **Email**: Resend

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