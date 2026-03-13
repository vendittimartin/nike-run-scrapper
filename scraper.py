#!/usr/bin/env python3
"""
Nike Run Buenos Aires — Event Monitor
Scrapes available running events and sends email alerts via Resend.
"""
import json
import os
import re
import sys
from pathlib import Path

import resend
from playwright.sync_api import sync_playwright

NOTIFIED_FILE = "notified_events.json"
TARGET_URL = "https://www.nike.com.ar/run-buenos-aires"
RECIPIENT_EMAIL = "vendittimartin@gmail.com"


def load_notified() -> set:
    if Path(NOTIFIED_FILE).exists():
        with open(NOTIFIED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_notified(notified: set):
    with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(notified)), f, indent=2, ensure_ascii=False)


def normalize_id(text: str) -> str:
    """Create a stable, filesystem-safe ID from event date text."""
    text = re.sub(r"\s+", "_", text.strip().upper())
    text = re.sub(r"[^A-Z0-9_]", "", text)
    return text


def scrape_available_events() -> list[dict]:
    """
    Returns list of events with 'Inscribirme ahora' status.
    Each item: {"id": "17_DE_MARZO_DE_19_A_21_HS", "date": "17 DE MARZO | DE 19 A 21 HS"}
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        try:
            print(f"  Loading {TARGET_URL} ...")
            page.goto(TARGET_URL, wait_until="load", timeout=60_000)

            # Wait until the event cards render (VTEX loads content async)
            # We poll until "Inscribirme" or "Finalizado" appears in the visible DOM
            print("  Waiting for event cards to render...")
            try:
                page.wait_for_function(
                    """() => {
                        const text = document.body.innerText || '';
                        return text.includes('Inscribirme') || text.includes('Finalizado');
                    }""",
                    timeout=30_000,
                )
            except Exception:
                print("  WARNING: event cards did not appear within 30s, trying anyway...")
            page.wait_for_timeout(2_000)

            # Each card has an <a class="*infoCardButton"> with:
            #   - "Finalizado"      → href="/login?returnUrl="  (no experience UUID)
            #   - "Inscribirme ahora" / "Hacete miembro" → href="/login?returnUrl=/experiences/UUID"
            # We use the experience UUID as the stable unique ID.
            events_data = page.evaluate(
                """
                () => {
                    const seen = new Set();
                    const results = [];
                    const buttons = document.querySelectorAll('[class*="infoCardButton"]');

                    for (const btn of buttons) {
                        const status = (btn.textContent || '').trim();
                        if (!status || status === 'Finalizado') continue;

                        const href = btn.getAttribute('href') || '';
                        const match = href.match(/experiences\\/([a-f0-9\\-]+)/i);
                        if (!match) continue;

                        const experienceId = match[1];
                        if (seen.has(experienceId)) continue;
                        seen.add(experienceId);

                        results.push({
                            id: experienceId,
                            status: status,
                            url: 'https://www.nike.com.ar/experiences/' + experienceId
                        });
                    }
                    return results;
                }
                """
            )

            return events_data

        finally:
            browser.close()


def send_notification(event: dict):
    resend.api_key = os.environ["RESEND_API_KEY"]

    status = event["status"]   # "Inscribirme ahora" | "Hacete miembro" | etc.
    url = event["url"]

    html = f"""
    <div style="font-family: Arial, sans-serif; background: #000; color: #fff;
                padding: 40px; max-width: 600px; margin: 0 auto; border-radius: 8px;">

        <h1 style="color: #e5183a; font-size: 2em; margin-bottom: 4px; letter-spacing: 2px;">
            NIKE RUN BUENOS AIRES
        </h1>
        <h2 style="color: #fff; margin-top: 0; font-weight: 300;">
            ¡Hay un nuevo evento disponible!
        </h2>

        <div style="background: #1a1a1a; border-left: 4px solid #e5183a;
                    border-radius: 4px; padding: 20px; margin: 28px 0;">
            <p style="font-size: 1em; color: #aaa; margin: 0 0 8px 0;">Estado del evento</p>
            <p style="font-size: 1.5em; font-weight: bold; color: #fff; margin: 0;">
                {status}
            </p>
        </div>

        <a href="{url}"
           style="display: inline-block; background-color: #fff; color: #000;
                  padding: 14px 32px; text-decoration: none; border-radius: 30px;
                  font-weight: bold; font-size: 1em; letter-spacing: 1px; margin-bottom: 12px;">
            IR AL EVENTO →
        </a>
        <br>
        <a href="{TARGET_URL}"
           style="display: inline-block; color: #aaa; font-size: 0.85em; text-decoration: underline;">
            Ver todos los eventos
        </a>

        <p style="color: #555; font-size: 0.75em; margin-top: 36px; border-top: 1px solid #222; padding-top: 16px;">
            Nike Running Monitor · Notificación automática.<br>
            Recibirás este mail solo una vez por evento.
        </p>
    </div>
    """

    params = resend.Emails.SendParams(
        from_="Nike Monitor <onboarding@resend.dev>",
        to=[RECIPIENT_EMAIL],
        subject=f"Nike Run BA — Nuevo evento disponible ({status})",
        html=html,
    )
    resend.Emails.send(params)
    print(f"  Email sent for event: {event['id']} ({status})")


def main():
    print("[Nike Monitor] Starting check...")

    notified = load_notified()
    print(f"[Nike Monitor] Already notified events: {len(notified)}")

    try:
        available = scrape_available_events()
    except Exception as e:
        print(f"[Nike Monitor] ERROR during scraping: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[Nike Monitor] Available events found: {[(e['id'], e['status']) for e in available]}")

    new_events = [e for e in available if e["id"] not in notified]
    print(f"[Nike Monitor] New events to notify: {len(new_events)}")

    for event in new_events:
        try:
            send_notification(event)
            notified.add(event["id"])
        except Exception as exc:
            print(f"[Nike Monitor] Failed to notify '{event['id']}': {exc}", file=sys.stderr)

    save_notified(notified)
    print("[Nike Monitor] Done.")


if __name__ == "__main__":
    main()
