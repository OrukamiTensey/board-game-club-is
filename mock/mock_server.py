"""
BoardClub IS — Mock API Server (Лабораторна робота №4, API-First / SDD)

Легковісний FastAPI mock-сервер, який повертає приклади відповідей (examples)
із spec/openapi.yaml без жодної бізнес-логіки та бази даних.

Запуск:
    uvicorn mock.mock_server:app --port 8080 --reload

Альтернативний запуск через Prism:
    npx @stoplight/prism-cli mock spec/openapi.yaml -p 8080
"""

from datetime import datetime, timezone
from fastapi import FastAPI, Query, Path, Request
from fastapi.responses import JSONResponse
from typing import Optional

app = FastAPI(
    title="BoardClub IS Mock API",
    version="1.0.0-mock",
    description="Mock API для контрактного тестування BoardClub IS (API-First / SDD)",
)


# =============================================================================
# HELPERS
# =============================================================================

def _now_iso() -> str:
    """Повертає поточний час у форматі ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _error(status: int, code: str, message: str, details=None) -> JSONResponse:
    """Формує уніфіковану ErrorResponse."""
    return JSONResponse(
        status_code=status,
        content={
            "code": code,
            "message": message,
            "details": details,
            "timestamp": _now_iso(),
        },
    )


# =============================================================================
# GET /api/v1/games — Каталог ігор (REQ-F-001)
# =============================================================================

GAMES_CATALOG = [
    {
        "id": "bg-001",
        "title": "Dune: Imperium",
        "genre": "Стратегія",
        "publisher": "Dire Wolf Digital",
        "market_price": 2200.00,
        "category": "B",
        "daily_rental_rate": 150.00,
    },
    {
        "id": "bg-002",
        "title": "Каркасон",
        "genre": "Сімейна",
        "publisher": "Hans im Glück",
        "market_price": 800.00,
        "category": "A",
        "daily_rental_rate": 80.00,
    },
    {
        "id": "bg-003",
        "title": "Gloomhaven",
        "genre": "Кооперативна RPG",
        "publisher": "Cephalofair Games",
        "market_price": 4500.00,
        "category": "C",
        "daily_rental_rate": 300.00,
    },
]


@app.get("/api/v1/games")
async def list_games(
    category: Optional[str] = Query(None, description="Фільтр за категорією A/B/C"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Отримати каталог ігор з фільтрацією за категорією (REQ-F-001)."""
    if category and category not in ("A", "B", "C"):
        return _error(
            400,
            "VALIDATION_ERROR",
            f"Невалідне значення параметра 'category'. Допустимі значення: A, B, C.",
            {"field": "category", "rejected_value": category},
        )

    items = GAMES_CATALOG
    if category:
        items = [g for g in items if g["category"] == category]

    return {"items": items, "total": len(items), "page": page, "page_size": page_size}


# =============================================================================
# GET /api/v1/games/{id}/copies — Список примірників (REQ-F-002, REQ-F-003)
# =============================================================================

GAME_COPIES = {
    "bg-001": [
        {"copy_id": "BG-001-R1", "inventory_number": "INV-2024-0042", "game_id": "bg-001", "fund": "RentalFund", "status": "AVAILABLE"},
        {"copy_id": "BG-001-R2", "inventory_number": "INV-2024-0043", "game_id": "bg-001", "fund": "RentalFund", "status": "RENTED"},
        {"copy_id": "BG-001-C1", "inventory_number": "INV-2024-0044", "game_id": "bg-001", "fund": "ClubFund", "status": "AVAILABLE"},
        {"copy_id": "BG-001-R3", "inventory_number": "INV-2024-0045", "game_id": "bg-001", "fund": "RentalFund", "status": "NEEDS_REPAIR"},
    ],
}


@app.get("/api/v1/games/{game_id}/copies")
async def list_game_copies(game_id: str = Path(...)):
    """Список фізичних примірників гри, їх стан та фонд (REQ-F-002, REQ-F-003)."""
    if game_id not in GAME_COPIES:
        return _error(
            404,
            "GAME_NOT_FOUND",
            f"Гру з ідентифікатором '{game_id}' не знайдено в каталозі.",
        )
    copies = GAME_COPIES[game_id]
    return {"items": copies, "total": len(copies)}


# =============================================================================
# POST /api/v1/rentals/calculate — Розрахунок застави (REQ-F-004, REQ-F-005)
# =============================================================================

@app.post("/api/v1/rentals/calculate")
async def calculate_rental(request: Request):
    """Розрахунок застави та прокату (REQ-F-004, REQ-F-005, REQ-NF-001)."""
    body = await request.json()

    game_id = body.get("game_id")
    client_id = body.get("client_id")
    rental_days = body.get("rental_days")

    # --- Валідація обов'язкових полів ---
    if not game_id or not client_id or rental_days is None:
        return _error(
            400,
            "VALIDATION_ERROR",
            "Поля 'game_id', 'client_id' та 'rental_days' є обов'язковими.",
            {"missing_fields": [f for f in ("game_id", "client_id", "rental_days") if not body.get(f)]},
        )

    if not isinstance(rental_days, int) or rental_days < 1:
        return _error(
            400,
            "VALIDATION_ERROR",
            "Поле 'rental_days' є обов'язковим і має бути цілим числом ≥ 1.",
            {"field": "rental_days", "constraint": "minimum: 1"},
        )

    # --- Mock: Спроба орендувати з ClubFund → 422 ---
    if body.get("fund") == "ClubFund" or body.get("copy_id", "").endswith("-C1"):
        return _error(
            422,
            "GAME_FUND_RESTRICTION",
            "Екземпляр призначений виключно для гри в залі. Оренда додому копій з ClubFund заборонена.",
            {"game_id": game_id, "copy_id": body.get("copy_id", "BG-001-C1"), "fund": "ClubFund"},
        )

    # --- Mock: Визначення результату за client_id ---
    # client-007 — ClubMember, решта — звичайний клієнт
    is_club_member = client_id in ("client-007", "client-club")
    game = next((g for g in GAMES_CATALOG if g["id"] == game_id), GAMES_CATALOG[0])

    if is_club_member:
        if game["category"] == "A":
            deposit_percent = 0
        else:
            deposit_percent = 30
    else:
        deposit_percent = 100

    deposit_amount = round(game["market_price"] * deposit_percent / 100, 2)
    rental_total = round(game["daily_rental_rate"] * rental_days, 2)

    return {
        "game_id": game["id"],
        "client_id": client_id,
        "game_title": game["title"],
        "category": game["category"],
        "market_price": game["market_price"],
        "daily_rental_rate": game["daily_rental_rate"],
        "rental_days": rental_days,
        "rental_total": rental_total,
        "is_club_member": is_club_member,
        "deposit_percent": deposit_percent,
        "deposit_amount": deposit_amount,
    }


# =============================================================================
# POST /api/v1/rentals/{id}/return — Повернення гри (REQ-F-006, REQ-F-007)
# =============================================================================

ACTIVE_RENTALS = {"rental-2024-0158"}


@app.post("/api/v1/rentals/{rental_id}/return")
async def process_rental_return(rental_id: str, request: Request):
    """Розрахунок повернення гри (REQ-F-006, REQ-F-007)."""
    if rental_id not in ACTIVE_RENTALS:
        return _error(
            404,
            "RENTAL_NOT_FOUND",
            f"Договір оренди з ідентифікатором '{rental_id}' не знайдено.",
        )

    body = await request.json()
    defect_detected = body.get("defect_detected", False)
    defect_fee_percent = body.get("defect_fee_percent", 0.0) if defect_detected else 0.0

    # Mock: фіксовані значення для тестування BDD-сценарію
    daily_rate = 100.00
    deposit = 1000.00
    market_price = 1000.00
    overdue_days = 1
    overdue_penalty = overdue_days * 2 * daily_rate
    defect_fee_amount = round(market_price * defect_fee_percent / 100, 2) if defect_detected else 0.00
    total_deductions = overdue_penalty + defect_fee_amount
    refund = deposit - total_deductions

    return {
        "rental_id": rental_id,
        "client_id": "client-007",
        "game_title": "Dune: Imperium",
        "scheduled_return_date": "2026-10-30T12:00:00Z",
        "actual_return_date": body.get("actual_return_date", "2026-10-31T12:00:00Z"),
        "overdue_days": overdue_days,
        "daily_rental_rate": daily_rate,
        "overdue_penalty": overdue_penalty,
        "defect_detected": defect_detected,
        "defect_fee_percent": defect_fee_percent,
        "defect_fee_amount": defect_fee_amount,
        "deposit_held": deposit,
        "total_deductions": total_deductions,
        "refund_amount": refund,
        "copy_status": "NEEDS_REPAIR" if defect_detected else "AVAILABLE",
        "client_clean_rentals_reset": defect_detected,
        "client_club_member_revoked": defect_detected,
    }


# =============================================================================
# POST /api/v1/tables/bookings — Бронювання столу (REQ-F-008, REQ-NF-002)
# =============================================================================

# Mock: вже зайняті слоти для тестування конфлікту
BOOKED_SLOTS = {
    "table-03": [
        {"start": "2026-10-30T13:00:00Z", "end": "2026-10-30T15:00:00Z", "booking_id": "booking-2024-0300"},
    ],
}


@app.post("/api/v1/tables/bookings", status_code=201)
async def create_table_booking(request: Request):
    """Бронювання ігрового столу (REQ-F-008, REQ-NF-002)."""
    body = await request.json()

    table_id = body.get("table_id")
    client_id = body.get("client_id")
    start_time = body.get("start_time", "")
    duration_hours = body.get("duration_hours")

    # --- Валідація duration_hours ---
    if duration_hours is None or not isinstance(duration_hours, int) or duration_hours < 1:
        return _error(
            400,
            "VALIDATION_ERROR",
            "Тривалість бронювання має бути цілим числом ≥ 1 годину.",
            {"field": "duration_hours", "rejected_value": duration_hours, "constraint": "minimum: 1, type: integer"},
        )

    # --- Валідація кратності 1 годині (REQ-F-008) ---
    try:
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if dt.minute != 0 or dt.second != 0:
            return _error(
                400,
                "VALIDATION_ERROR",
                f"Час початку бронювання повинен бути кратним 1 годині (хвилини = 00). Отримано: {dt.strftime('%H:%M')}.",
                {"field": "start_time", "rejected_value": start_time, "constraint": "Хвилини та секунди повинні дорівнювати 00"},
            )
    except (ValueError, TypeError):
        return _error(
            400,
            "VALIDATION_ERROR",
            "Невалідний формат часу 'start_time'. Очікується ISO 8601.",
            {"field": "start_time", "rejected_value": start_time},
        )

    # --- Перевірка конфлікту слотів (REQ-NF-002) ---
    if table_id in BOOKED_SLOTS:
        for slot in BOOKED_SLOTS[table_id]:
            # Спрощена mock-перевірка: якщо start_time потрапляє між існуючим слотом
            slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
            slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
            booking_end = dt.replace(hour=dt.hour + duration_hours) if (dt.hour + duration_hours) < 24 else dt
            if dt < slot_end and booking_end > slot_start:
                return _error(
                    409,
                    "TABLE_OVERBOOKING",
                    f"Стіл '{table_id}' вже заброньовано на вказаний часовий слот. Оберіть інший час або стіл.",
                    {
                        "table_id": table_id,
                        "conflicting_slot": {
                            "start_time": slot["start"],
                            "end_time": slot["end"],
                            "booking_id": slot["booking_id"],
                        },
                    },
                )

    # --- Успішне бронювання ---
    end_dt = dt.replace(hour=dt.hour + duration_hours)
    return JSONResponse(
        status_code=201,
        content={
            "booking_id": "booking-2024-0312",
            "table_id": table_id,
            "client_id": client_id,
            "start_time": start_time,
            "end_time": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_hours": duration_hours,
            "status": "CONFIRMED",
            "created_at": _now_iso(),
        },
    )


# =============================================================================
# POST /api/v1/tables/bookings/{id}/no-show — No-Show (REQ-F-009)
# =============================================================================

ACTIVE_BOOKINGS = {
    "booking-2024-0312": {
        "table_id": "table-03",
        "client_id": "client-015",
        "slot_start_time": "2026-10-30T14:00:00Z",
    },
}


@app.post("/api/v1/tables/bookings/{booking_id}/no-show")
async def trigger_no_show_check(booking_id: str):
    """Тригер перевірки неявки гостя (REQ-F-009)."""
    if booking_id not in ACTIVE_BOOKINGS:
        return _error(
            404,
            "BOOKING_NOT_FOUND",
            f"Бронювання з ідентифікатором '{booking_id}' не знайдено.",
        )

    booking = ACTIVE_BOOKINGS[booking_id]
    slot_start = datetime.fromisoformat(booking["slot_start_time"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    # Mock: Для тестування використовуємо фіксований час = +21 хв
    elapsed = 21
    no_show_triggered = elapsed > 20

    return {
        "booking_id": booking_id,
        "table_id": booking["table_id"],
        "client_id": booking["client_id"],
        "slot_start_time": booking["slot_start_time"],
        "checked_at": _now_iso(),
        "elapsed_minutes": elapsed,
        "no_show_triggered": no_show_triggered,
        "status": "CANCELLED_NO_SHOW" if no_show_triggered else "CONFIRMED",
        "table_status": "AVAILABLE" if no_show_triggered else "RESERVED",
        "message": (
            "Бронювання скасовано через неявку клієнта (No-Show). Стіл вивільнено."
            if no_show_triggered
            else "Час очікування ще не минув."
        ),
    }


# =============================================================================
# Healthcheck
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "ok", "server": "BoardClub IS Mock API", "timestamp": _now_iso()}
