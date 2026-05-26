# Архитектура дипломного проекта

## Архитектура MVP

```mermaid
flowchart LR
    Client[Клиент / Swagger] --> Booking[Booking Service]
    Booking --> BookingPG[(PostgreSQL)]
```

## Архитектура в общем контуре онлайн-кинотеатра

```mermaid
flowchart LR
    Client[Клиент] --> Auth[Auth Service]
    Client --> MoviesAPI[Movies API]
    Client --> Booking[Booking Service]

    Booking --> BookingPG[(PostgreSQL)]
    Booking -. проверка JWT .-> Auth
    Booking -. проверка фильма .-> MoviesAPI

    MoviesAPI --> ES[(Elasticsearch)]
    MoviesAPI --> Redis[(Redis)]
    Auth --> AuthPG[(PostgreSQL)]
```

## Компоненты

### Booking Service

Новый дипломный сервис. Отвечает за события совместных просмотров и бронирования мест.

### PostgreSQL

Основное хранилище сервиса бронирования. Хранит события и бронирования.

### Auth Service

Внешняя зависимость общего контура онлайн-кинотеатра. В MVP booking_service проверяет JWT по секрету из переменных окружения.

### Movies API

Внешняя зависимость общего контура онлайн-кинотеатра. В MVP booking_service хранит `movie_id`, а проверка фильма может быть включена через `MOVIES_API_VALIDATE=true`.

## Главный технический риск

Основной риск — конкурентное бронирование последнего места несколькими пользователями одновременно.

Решение:

1. открыть транзакцию;
2. заблокировать строку события через `SELECT ... FOR UPDATE`;
3. посчитать активные бронирования;
4. если мест нет — вернуть 409;
5. если место есть — создать бронь;
6. завершить транзакцию.