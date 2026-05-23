# BP Tracker — топологія та розгортання

Як влаштований і деплоїться весь стек. Технічні деталі кожної частини — у README відповідного репо.

## Огляд

| Сервіс | Репо | Де крутиться | Як деплоїться |
|---|---|---|---|
| frontend | bptracker-frontend | GitHub Pages | GitHub Actions, авто при push у `main` |
| backend | bptracker-backend | `treehouse.lan`, Docker | вручну: `docker compose up --build -d` |
| aivm-photo-api | aivm-photo-api | `treehouse.lan`, Docker | 🛑 **ЗУПИНЕНО** (архів) |
| bp-ocr-cnn | bp-ocr-cnn | — | не деплоїться (локальне тренування моделі) |

## Інфраструктура

Гіпервізор — **Proxmox**. На ньому:

- **`treehouse.lan`** — VM. На ній **Portainer** і **всі Docker-контейнери** (backend-стек + photo-api).
- **`jump.lan`** — LXC-контейнер (CT). На ньому **`cloudflared`** — конектор Cloudflare Tunnel (публічний доступ до API).

Окремо, поза Proxmox:

- **`nas.lan`** — TrueNAS, окрема фізична машина. Використовується лише як **зовнішній диск**: контейнер `aivm-photo-api` монтує SMB-шару `//nas.lan/media/aivm_folder` через CIFS (креденшели `NAS_USER` / `NAS_PASSWORD` з `.env`).

Тобто: контейнери — на `treehouse.lan`; тунель — на `jump.lan`; фото-датасет — на `nas.lan`.

### Backend-стек — `bptracker-backend/docker-compose.yml`

| Контейнер | Образ | Порт (host→container) | Призначення |
|---|---|---|---|
| `bptracker-api` | build з репо | 5000 → 8080 | ASP.NET Core API |
| `bptracker-db` | postgres:16 | 5436 → 5432 | PostgreSQL, volume `pgdata` (на диску `treehouse.lan`) |
| `bptracker-seq` | datalust/seq | 5341 → 80 | Логи (Seq), локально |

### photo-api — `aivm-photo-api/docker-compose.yml`
> **Статус:** Наразі стек `photo-api` вимкнено на постійній основі, оскільки модель CNN вже натренована.
>
> Щоб повністю відключити його на рівні бекенду (і OCR-розпізнавання, і вивантаження фото), встановити в `bptracker-backend/.env`:
> ```
> PHOTO_API_ENABLED=false
> ```
> При цьому endpoint `/api/v1/measurements/analyze` пропускає локальний OCR і одразу йде на Gemini. Детальніше — [bptracker-backend/README.md](bptracker-backend/README.md).

| Контейнер | Образ | Порт | Призначення |
|---|---|---|---|
| `aivm-photo-api` | build з репо | 8010 → 8000 | FastAPI: primary OCR + збір датасету |

Volume `photos` — CIFS-монтування SMB-шари `//nas.lan/media/aivm_folder`.

## Публічний доступ

| URL | Канал | Веде на |
|---|---|---|
| `https://bptracker.home.vn.ua` | GitHub Pages (custom domain, файл `CNAME`) | frontend (статика) |
| `https://api-bptracker.home.vn.ua` | Cloudflare Tunnel | `http://treehouse.lan:5000` → `bptracker-api` |
| `https://aivm-photo.lab.vn.ua` | Cloudflare Tunnel | `http://treehouse.lan:8010` → `aivm-photo-api` |

TLS термінує Cloudflare; усередину локальної мережі йде звичайний HTTP. Окремого reverse-proxy на хості немає — його роль виконує Cloudflare Tunnel. Конектор `cloudflared` працює на LXC-контейнері `jump.lan`.

## Деплой

### frontend
Push у `main` репо `bptracker-frontend` → GitHub Actions (`.github/workflows/deploy.yml`) збирає і публікує на GitHub Pages. Втручання не потрібне.

### backend / photo-api
Вручну на `treehouse.lan` (через Portainer або CLI):
```bash
git pull
docker compose up --build -d
```
Образ збирається на `treehouse.lan` (`build: .` у compose).

> Раніше backend деплоївся авто через Portainer GitOps Webhook — **вимкнено**, бо авто-деплой спрацьовував надто неявно. Тепер деплой свідомий і ручний.

## Секрети

Реальні значення — у `.env` кожного репо. `.env` **не комітяться** в git (тільки `.env.example`). Живуть лише на `treehouse.lan`.

Резервна копія `.env` — у Bitwarden (Secure Note):
- backend `.env` — ✅ збережено
- photo-api `.env` — ⬜ TODO

| Файл | Ключові секрети |
|---|---|
| `bptracker-backend/.env` | `POSTGRES_PASSWORD`, `GEMINI_API_KEY`, `SMTP_PASSWORD`, `PHOTO_API_TOKEN` |
| `aivm-photo-api/.env` | `API_TOKEN`, `NAS_USER`, `NAS_PASSWORD` |

## Бекапи

- **БД (PostgreSQL):** автоматичного бекапу **немає**. Volume `pgdata` лежить на диску `treehouse.lan` — **не** на TrueNAS, тож ZFS-снапшоти TrueNAS його не покривають. Лише ручний `pg_dump` (див. README бекенду). ⚠️ Втрата `treehouse.lan` = втрата всіх замірів.
- **Фото-датасет:** на SMB-шарі `nas.lan` (`//nas.lan/media/aivm_folder`). Покривається ZFS-снапшотами TrueNAS, якщо такі налаштовані.

## Відновлення з нуля

1. На Proxmox підняти VM `treehouse.lan` (Docker + Portainer) і CT `jump.lan` (`cloudflared`).
2. Налаштувати Cloudflare Tunnel на `jump.lan`: `api-bptracker.home.vn.ua` → `treehouse.lan:5000`, `aivm-photo.lab.vn.ua` → `treehouse.lan:8010`.
3. Клонувати 4 репо з `github.com/Alexsik76`.
4. Відновити `.env` бекенду й photo-api з Bitwarden → покласти у відповідні теки.
5. `docker compose up --build -d` для backend і photo-api.
6. БД — відновити з `pg_dump`-бекапу, **якщо такий є** (див. «Бекапи»).
7. frontend — задеплоїться сам при push, або вручну запустити Actions-workflow.
