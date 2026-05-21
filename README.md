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
