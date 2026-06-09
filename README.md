# BP Tracker

PWA для трекінгу артеріального тиску зі скануванням тонометра камерою.
Користувач фотографує дисплей тонометра — застосунок розпізнає `sys / dia / pulse`
локально в браузері (ONNX) і зберігає замір.

Це **hub-репозиторій**: він тримає спільний план і документацію.
Код кожної частини системи — в окремих репозиторіях (нижче).

## План робіт

[`root_PLAN.md`](./root_PLAN.md) — єдиний master-план для всіх частин,
включно зі схемою архітектури потоку даних.

## Репозиторії системи

| Репозиторій | Стек | Призначення |
|---|---|---|
| [bptracker-backend](https://github.com/Alexsik76/bptracker-backend) | ASP.NET Core 10, PostgreSQL | API, зберігання замірів, проксі до photo-api |
| [bptracker-frontend](https://github.com/Alexsik76/bptracker-frontend) | Vue 3 PWA | UI, локальний OCR у браузері (ONNX) |
| [aivm-photo-api](https://github.com/Alexsik76/aivm-photo-api) | FastAPI, YOLOv8 | Primary OCR, збір датасету |
| [bp-ocr-cnn](https://github.com/Alexsik76/bp-ocr-cnn) | Python, YOLOv8 | Тренування моделі розпізнавання цифр |

## Розгортання

Повна топологія — [`DEPLOY.md`](./DEPLOY.md): хости, домени, Cloudflare Tunnel, секрети, відновлення з нуля.

Коротко:
- **frontend** — GitHub Pages (авто через GitHub Actions)
- **backend**, **aivm-photo-api** — Docker на `treehouse.lan`, деплой вручну
- **bp-ocr-cnn** — локальне тренування, без деплою

## Захист API (Cloudflare WAF)

API-домен `api-bptracker.home.vn.ua` закритий WAF-правилом у Cloudflare:
доступ дозволено **лише з домашньої IP**. Усі інші IP отримують `403`.

- **Правило:** Security → WAF → Custom rules → «Allow only from home»
- **Вираз:** `(ip.src ne <HOME_IP> and http.host contains "api-bptracker.home.vn.ua")` → **Block**
- **Навіщо:** додатковий мережевий бар'єр перед API (поверх passkey/сесій).

### ⚠️ Наслідок: доступ лише з дому
З будь-якої іншої мережі (мобільний інтернет, інша локація) запити до API
блокуються Cloudflare **до того, як дійдуть до бекенду**.

**Симптом:** у браузері помилка CORS
`No 'Access-Control-Allow-Origin' header` на preflight (OPTIONS),
у Network — `403`, `Content-Type: text/html`, `Server: cloudflare`.
Це **не** баг застосунку чи CORS — це WAF-правило.

**Щоб отримати доступ ззовні:** тимчасово вимкнути правило в Cloudflare,
або додати поточну IP у виняток. Через VPN-тунель до дому працює без змін.

> TODO (опційно): замінити IP-allowlist на Cloudflare Access (Zero Trust)
> для захищеного доступу з будь-якої мережі без ручного перемикання.
> Потребує винятку для OPTIONS-preflight.
