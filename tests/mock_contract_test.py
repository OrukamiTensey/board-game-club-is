"""
BoardClub IS — Mock API Contract Tests (Лабораторна робота №4)

Автоматизований набір контрактних тестів, що перевіряє:
- Відповідність відповідей Mock API структурі spec/openapi.yaml
- Позитивні сценарії (Happy Path) для кожного ендпоінту
- Негативні сценарії (ErrorResponse) для кожного бізнес-правила

Запуск:
    pytest tests/mock_contract_test.py -v

Передумови:
    Mock-сервер має бути запущений:
    uvicorn mock.mock_server:app --port 8080
"""

import pytest
import httpx

BASE_URL = "http://localhost:8080"


# =============================================================================
# Допоміжні функції (assertion helpers)
# =============================================================================

def assert_error_response(data: dict, expected_code: str):
    """Перевіряє структуру уніфікованої ErrorResponse."""
    assert "code" in data, f"Відповідь не містить поле 'code': {data}"
    assert "message" in data, f"Відповідь не містить поле 'message': {data}"
    assert "timestamp" in data, f"Відповідь не містить поле 'timestamp': {data}"
    assert data["code"] == expected_code, (
        f"Очікувався код помилки '{expected_code}', отримано '{data['code']}'"
    )


# =============================================================================
# ПОЗИТИВНІ СЦЕНАРІЇ (Happy Path)
# =============================================================================


class TestPositiveScenarios:
    """Позитивні контрактні тести — перевірка 2xx відповідей."""

    # -------------------------------------------------------------------------
    # GET /api/v1/games — REQ-F-001
    # -------------------------------------------------------------------------
    def test_get_games_catalog_returns_200(self):
        """REQ-F-001: Отримання каталогу ігор повертає 200 та список ігор."""
        resp = httpx.get(f"{BASE_URL}/api/v1/games")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        # Перевірка структури кожної гри
        game = data["items"][0]
        for field in ("id", "title", "genre", "publisher", "market_price", "category", "daily_rental_rate"):
            assert field in game, f"Гра не містить обов'язкове поле '{field}'"
        assert game["category"] in ("A", "B", "C")

    def test_get_games_filter_by_category_b(self):
        """REQ-F-001: Фільтрація каталогу за категорією B."""
        resp = httpx.get(f"{BASE_URL}/api/v1/games", params={"category": "B"})

        assert resp.status_code == 200
        data = resp.json()
        for game in data["items"]:
            assert game["category"] == "B"

    # -------------------------------------------------------------------------
    # GET /api/v1/games/{id}/copies — REQ-F-002, REQ-F-003
    # -------------------------------------------------------------------------
    def test_get_game_copies_returns_200(self):
        """REQ-F-002, REQ-F-003: Отримання примірників гри з фондом та статусом."""
        resp = httpx.get(f"{BASE_URL}/api/v1/games/bg-001/copies")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0

        copy = data["items"][0]
        for field in ("copy_id", "inventory_number", "game_id", "fund", "status"):
            assert field in copy, f"Примірник не містить обов'язкове поле '{field}'"
        assert copy["fund"] in ("ClubFund", "RentalFund")
        assert copy["status"] in ("AVAILABLE", "RENTED", "NEEDS_REPAIR", "DECOMMISSIONED")

    # -------------------------------------------------------------------------
    # POST /api/v1/rentals/calculate — REQ-F-004, REQ-F-005
    # -------------------------------------------------------------------------
    def test_calculate_rental_club_member_30_percent(self):
        """REQ-F-004: ClubMember + категорія B → застава 30%."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/calculate",
            json={"game_id": "bg-001", "client_id": "client-007", "rental_days": 3},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_club_member"] is True
        assert data["deposit_percent"] == 30
        assert data["category"] == "B"
        assert data["deposit_amount"] == 660.00  # 2200 * 30%
        assert data["rental_total"] == 450.00  # 150 * 3

        # Перевірка обов'язкових полів відповіді
        for field in (
            "game_id", "client_id", "game_title", "category", "market_price",
            "daily_rental_rate", "rental_days", "rental_total",
            "is_club_member", "deposit_percent", "deposit_amount",
        ):
            assert field in data, f"Відповідь не містить обов'язкове поле '{field}'"

    def test_calculate_rental_regular_client_100_percent(self):
        """REQ-F-004: Звичайний клієнт + категорія B → застава 100%."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/calculate",
            json={"game_id": "bg-001", "client_id": "client-012", "rental_days": 3},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_club_member"] is False
        assert data["deposit_percent"] == 100
        assert data["deposit_amount"] == 2200.00  # 100% від ринкової вартості

    def test_calculate_rental_club_member_category_a_0_percent(self):
        """REQ-F-004: ClubMember + категорія A → застава 0%."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/calculate",
            json={"game_id": "bg-002", "client_id": "client-007", "rental_days": 5},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_club_member"] is True
        assert data["deposit_percent"] == 0
        assert data["deposit_amount"] == 0.00

    # -------------------------------------------------------------------------
    # POST /api/v1/rentals/{id}/return — REQ-F-006, REQ-F-007
    # -------------------------------------------------------------------------
    def test_rental_return_with_overdue_and_defect(self):
        """REQ-F-006, REQ-F-007: Повернення з простроченням та дефектом."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/rental-2024-0158/return",
            json={
                "actual_return_date": "2026-10-31T12:00:00Z",
                "defect_detected": True,
                "defect_fee_percent": 20.0,
            },
        )

        assert resp.status_code == 200
        data = resp.json()

        # Перевірка обов'язкових полів
        for field in (
            "rental_id", "client_id", "game_title", "scheduled_return_date",
            "actual_return_date", "overdue_days", "daily_rental_rate",
            "overdue_penalty", "defect_detected", "defect_fee_percent",
            "defect_fee_amount", "deposit_held", "total_deductions",
            "refund_amount", "copy_status",
            "client_clean_rentals_reset", "client_club_member_revoked",
        ):
            assert field in data, f"Відповідь не містить обов'язкове поле '{field}'"

        # Перевірка бізнес-правил
        assert data["overdue_days"] >= 1
        assert data["overdue_penalty"] == 200.00  # 1 * 2 * 100
        assert data["defect_detected"] is True
        assert data["defect_fee_amount"] == 200.00  # 1000 * 20%
        assert data["total_deductions"] == 400.00
        assert data["refund_amount"] == 600.00  # 1000 - 400
        assert data["copy_status"] == "NEEDS_REPAIR"
        assert data["client_clean_rentals_reset"] is True
        assert data["client_club_member_revoked"] is True

    # -------------------------------------------------------------------------
    # POST /api/v1/tables/bookings — REQ-F-008
    # -------------------------------------------------------------------------
    def test_create_table_booking_returns_201(self):
        """REQ-F-008: Успішне бронювання столу на кратну годину → 201 CONFIRMED."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/tables/bookings",
            json={
                "table_id": "table-05",
                "client_id": "client-015",
                "start_time": "2026-10-30T18:00:00Z",
                "duration_hours": 2,
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "CONFIRMED"
        assert data["duration_hours"] == 2
        assert "booking_id" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "created_at" in data

    # -------------------------------------------------------------------------
    # POST /api/v1/tables/bookings/{id}/no-show — REQ-F-009
    # -------------------------------------------------------------------------
    def test_no_show_trigger_cancels_booking(self):
        """REQ-F-009: Неявка >20 хв → CANCELLED_NO_SHOW, стіл AVAILABLE."""
        resp = httpx.post(f"{BASE_URL}/api/v1/tables/bookings/booking-2024-0312/no-show")

        assert resp.status_code == 200
        data = resp.json()
        assert data["no_show_triggered"] is True
        assert data["status"] == "CANCELLED_NO_SHOW"
        assert data["table_status"] == "AVAILABLE"
        assert data["elapsed_minutes"] > 20

        for field in (
            "booking_id", "table_id", "client_id", "slot_start_time",
            "checked_at", "elapsed_minutes", "no_show_triggered",
            "status", "table_status", "message",
        ):
            assert field in data, f"Відповідь не містить обов'язкове поле '{field}'"


# =============================================================================
# НЕГАТИВНІ СЦЕНАРІЇ (Error Paths)
# =============================================================================


class TestNegativeScenarios:
    """Негативні контрактні тести — перевірка 4xx ErrorResponse."""

    # -------------------------------------------------------------------------
    # 422 — GAME_FUND_RESTRICTION (REQ-F-002)
    # -------------------------------------------------------------------------
    def test_rental_calculate_club_fund_returns_422(self):
        """REQ-F-002: Спроба орендувати з ClubFund → 422 GAME_FUND_RESTRICTION."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/calculate",
            json={
                "game_id": "bg-001",
                "client_id": "client-007",
                "rental_days": 3,
                "copy_id": "BG-001-C1",  # ClubFund copy
                "fund": "ClubFund",
            },
        )

        assert resp.status_code == 422
        data = resp.json()
        assert_error_response(data, "GAME_FUND_RESTRICTION")
        assert data["details"]["fund"] == "ClubFund"

    # -------------------------------------------------------------------------
    # 400 — VALIDATION_ERROR (REQ-F-008, некратний час)
    # -------------------------------------------------------------------------
    def test_booking_invalid_start_time_returns_400(self):
        """REQ-F-008: Час початку не кратний 1 годині (14:30) → 400 VALIDATION_ERROR."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/tables/bookings",
            json={
                "table_id": "table-03",
                "client_id": "client-015",
                "start_time": "2026-10-30T14:30:00Z",  # 14:30 — не кратний!
                "duration_hours": 2,
            },
        )

        assert resp.status_code == 400
        data = resp.json()
        assert_error_response(data, "VALIDATION_ERROR")
        assert "start_time" in str(data.get("details", {}))

    # -------------------------------------------------------------------------
    # 400 — VALIDATION_ERROR (duration < 1)
    # -------------------------------------------------------------------------
    def test_booking_invalid_duration_returns_400(self):
        """REQ-F-008: Тривалість < 1 години → 400 VALIDATION_ERROR."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/tables/bookings",
            json={
                "table_id": "table-03",
                "client_id": "client-015",
                "start_time": "2026-10-30T14:00:00Z",
                "duration_hours": 0,
            },
        )

        assert resp.status_code == 400
        data = resp.json()
        assert_error_response(data, "VALIDATION_ERROR")
        assert data["details"]["field"] == "duration_hours"

    # -------------------------------------------------------------------------
    # 409 — TABLE_OVERBOOKING (REQ-NF-002)
    # -------------------------------------------------------------------------
    def test_booking_slot_conflict_returns_409(self):
        """REQ-NF-002: Конфлікт слотів → 409 TABLE_OVERBOOKING."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/tables/bookings",
            json={
                "table_id": "table-03",
                "client_id": "client-020",
                "start_time": "2026-10-30T14:00:00Z",  # Перетинається з 13:00–15:00
                "duration_hours": 2,
            },
        )

        assert resp.status_code == 409
        data = resp.json()
        assert_error_response(data, "TABLE_OVERBOOKING")
        assert data["details"]["table_id"] == "table-03"
        assert "conflicting_slot" in data["details"]

    # -------------------------------------------------------------------------
    # 404 — GAME_NOT_FOUND (REQ-F-002)
    # -------------------------------------------------------------------------
    def test_get_copies_unknown_game_returns_404(self):
        """REQ-F-002: Запит копій неіснуючої гри → 404 GAME_NOT_FOUND."""
        resp = httpx.get(f"{BASE_URL}/api/v1/games/bg-999/copies")

        assert resp.status_code == 404
        data = resp.json()
        assert_error_response(data, "GAME_NOT_FOUND")
        assert "bg-999" in data["message"]

    # -------------------------------------------------------------------------
    # 404 — BOOKING_NOT_FOUND (REQ-F-009)
    # -------------------------------------------------------------------------
    def test_no_show_unknown_booking_returns_404(self):
        """REQ-F-009: No-Show для неіснуючого бронювання → 404."""
        resp = httpx.post(f"{BASE_URL}/api/v1/tables/bookings/booking-xxx/no-show")

        assert resp.status_code == 404
        data = resp.json()
        assert_error_response(data, "BOOKING_NOT_FOUND")

    # -------------------------------------------------------------------------
    # 404 — RENTAL_NOT_FOUND (REQ-F-006)
    # -------------------------------------------------------------------------
    def test_rental_return_unknown_id_returns_404(self):
        """REQ-F-006: Повернення за неіснуючим ID оренди → 404."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/rental-xxx/return",
            json={"actual_return_date": "2026-10-31T12:00:00Z", "defect_detected": False},
        )

        assert resp.status_code == 404
        data = resp.json()
        assert_error_response(data, "RENTAL_NOT_FOUND")

    # -------------------------------------------------------------------------
    # 400 — VALIDATION_ERROR (відсутні поля в calculate)
    # -------------------------------------------------------------------------
    def test_rental_calculate_missing_fields_returns_400(self):
        """REQ-F-004: Відсутні обов'язкові поля → 400 VALIDATION_ERROR."""
        resp = httpx.post(
            f"{BASE_URL}/api/v1/rentals/calculate",
            json={"game_id": "bg-001"},  # Без client_id та rental_days
        )

        assert resp.status_code == 400
        data = resp.json()
        assert_error_response(data, "VALIDATION_ERROR")
