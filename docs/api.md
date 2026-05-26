# API booking_service

## Health

### GET /health

Проверка состояния сервиса.

## Events

### POST /api/v1/events

Создать событие просмотра.

Требуется авторизация.

Тело запроса:

```json
{
  "movie_id": "string",
  "movie_title": "string",
  "starts_at": "2026-06-01T19:00:00Z",
  "place": "Москва, кинотеатр",
  "seats_limit": 5,
  "description": "Совместный просмотр фильма"
}
```

### GET /api/v1/events

Получить список активных событий.

### GET /api/v1/events/{event_id}

Получить одно событие.

### PATCH /api/v1/events/{event_id}/cancel

Отменить событие.

Требуется авторизация. Доступно только владельцу события.

## Bookings

### POST /api/v1/events/{event_id}/booking

Забронировать место.

Требуется авторизация.

Возможные ошибки:

- 404 — событие не найдено;
- 409 — мест больше нет;
- 409 — пользователь уже бронировал это событие.

### DELETE /api/v1/events/{event_id}/booking

Отменить свою бронь.

Требуется авторизация.

### GET /api/v1/events/bookings/me

Получить свои бронирования.

Требуется авторизация.
