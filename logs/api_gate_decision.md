# Протокол контрольної точки API-GATE

- **Проєкт:** BoardClub IS  
- **Контрольна точка:** API-GATE (Лабораторна робота №4, API-First / SDD)  
- **Дата перевірки:** 2026-10-30  
- **Відповідальний:** Системний інженер / API-архітектор  

---

## 1. Чек-ліст критеріїв API-GATE

| № | Критерій | Статус | Коментар |
|:-:|:---------|:------:|:---------|
| 1 | **Файл `spec/openapi.yaml` створено** і відповідає стандарту OpenAPI 3.0.3 | ✅ PASS | Файл створено, версія: `openapi: 3.0.3` |
| 2 | **Валідація контракту пройшла без помилок** (Redocly lint / Spectral) | ✅ PASS | `redocly lint`: 0 errors, 2 warnings (допустимі — `example.com` URL серверів) |
| 3 | **Усі функціональні вимоги (REQ-F-001 — REQ-F-009)** покриті ендпоінтами з явною прив'язкою REQ-ID у `description` | ✅ PASS | 6 ендпоінтів, 6 операцій, кожна містить REQ-ID у описі |
| 4 | **Уніфікована модель помилки `ErrorResponse`** містить поля `code`, `message`, `details`, `timestamp` | ✅ PASS | Схема `ErrorResponse` у `components/schemas`, `details` — nullable object |
| 5 | **Машиночитні коди помилок** визначені для кожного бізнес-правила: `VALIDATION_ERROR`, `GAME_FUND_RESTRICTION`, `TABLE_OVERBOOKING`, `GAME_NOT_FOUND`, `RENTAL_NOT_FOUND`, `BOOKING_NOT_FOUND` | ✅ PASS | Коди використовуються у прикладах 4xx/422 відповідей |
| 6 | **Реалістичні приклади (`example`/`examples`)** надані для всіх схем та ендпоінтів, придатні для Mock API | ✅ PASS | Кожен ендпоінт має `example` або `examples` з реальними даними (BDD-сценарії) |
| 7 | **Валідація типів та обмежень**: `required`, `enum`, `minimum`, `format` визначені для всіх полів | ✅ PASS | `category: enum [A,B,C]`, `deposit_percent: enum [0,30,100]`, `duration_hours: minimum 1`, `status: enum`, `format: date-time` |
| 8 | **Mock API сервер запускається та коректно повертає відповіді** відповідно до контракту | ✅ PASS | FastAPI mock-сервер (`mock/mock_server.py`) запущено на порту 8080, всі ендпоінти функціональні |
| 9 | **Контрактні тести (16 сценаріїв)** пройшли успішно: 8 позитивних + 8 негативних | ✅ PASS | `pytest tests/mock_contract_test.py -v`: 16 passed, 0 failed |
| 10 | **Матриця простежуваності оновлена** з прив'язкою кожної вимоги до API ендпоінту, HTTP-методу та контрактного тесту | ✅ PASS | `spec/traceability_matrix.md` v2.0 — додано колонки API Ендпоінт, HTTP Метод, Коди відповіді, Mock Contract Test |

---

## 2. Перелік створених артефактів

| Артефакт | Шлях | Опис |
|:---------|:-----|:-----|
| OpenAPI контракт | `spec/openapi.yaml` | API-First специфікація, OpenAPI 3.0.3, 6 ендпоінтів, 12 схем |
| Mock API сервер | `mock/mock_server.py` | Легковісний FastAPI mock без бізнес-логіки та БД |
| Залежності mock | `mock/requirements.txt` | `fastapi`, `uvicorn`, `httpx`, `pytest` |
| Контрактні тести | `tests/mock_contract_test.py` | 16 тестів (8 positive + 8 negative), httpx + pytest |
| Матриця простежуваності | `spec/traceability_matrix.md` | v2.0 — з колонками API, HTTP, тестів |
| Протокол API-GATE | `logs/api_gate_decision.md` | Цей документ |

---

## 3. Покриття вимог API-контрактом

```
REQ-F-001 ──► GET  /api/v1/games                          ✅
REQ-F-002 ──► GET  /api/v1/games/{id}/copies               ✅
              POST /api/v1/rentals/calculate (422 ClubFund) ✅
REQ-F-003 ──► GET  /api/v1/games/{id}/copies               ✅
REQ-F-004 ──► POST /api/v1/rentals/calculate               ✅
REQ-F-005 ──► POST /api/v1/rentals/calculate               ✅
REQ-F-006 ──► POST /api/v1/rentals/{id}/return             ✅
REQ-F-007 ──► POST /api/v1/rentals/{id}/return             ✅
REQ-F-008 ──► POST /api/v1/tables/bookings                 ✅
REQ-F-009 ──► POST /api/v1/tables/bookings/{id}/no-show    ✅
REQ-NF-001 ─► POST /api/v1/rentals/calculate (≤100мс)     ✅
REQ-NF-002 ─► POST /api/v1/tables/bookings (409)          ✅
REQ-NF-003 ─► POST /api/v1/rentals/{id}/return (audit)    ✅
REQ-NF-004 ─► spec/openapi.yaml (Git-версіонування)       ✅
```

---

## 4. Підсумковий вердикт

| Параметр | Значення |
|:---------|:---------|
| **Вердикт** | **🟢 GO (СХВАЛЕНО ДО РЕАЛІЗАЦІЇ)** |
| **Критерії пройдено** | 10 / 10 |
| **Критерії провалено** | 0 / 10 |
| **Контрактні тести** | 16 passed / 0 failed |
| **Блокуючі зауваження** | Відсутні |
| **Рекомендації** | Перейти до етапу реалізації бізнес-логіки (Лабораторна робота №5) |

---

> **Рішення:** API-контракт `spec/openapi.yaml` відповідає всім вимогам SRS v1.0,
> валідовано лінтером, перевірено через Mock API та 16 контрактних тестів.
> Система **СХВАЛЕНА ДО РЕАЛІЗАЦІЇ**.
