#!/usr/bin/env python3
"""Замер скорости скачивания: N последовательных запросов к одному адресу."""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024  # читаем ответ кусками по 64 КиБ
BITS_IN_BYTE = 8


def download(url: str, timeout: float) -> tuple[int, float]:
    """Скачивает url целиком. Возвращает (байт получено, секунд затрачено)."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "speedtest-script/1.0",
            "Accept-Encoding": "identity",  # без сжатия, чтобы считать реальный объём
            "Cache-Control": "no-cache",
        },
    )
    received = 0
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            received += len(chunk)
    return received, time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Замер скорости скачивания по N последовательным запросам."
    )
    parser.add_argument("url", help="адрес для скачивания (например, тяжёлая картинка)")
    parser.add_argument("-n", "--requests", type=int, default=10,
                        help="количество запросов (по умолчанию 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30.0,
                        help="таймаут сетевых операций в секундах (по умолчанию 30)")
    args = parser.parse_args()

    if not args.url.lower().startswith(("http://", "https://")):
        parser.error("адрес должен начинаться с http:// или https://")
    if args.requests < 1:
        parser.error("количество запросов должно быть не меньше 1")

    total_bytes = 0
    total_time = 0.0
    ok = 0

    print(f"Адрес: {args.url}")
    print(f"Запросов: {args.requests}\n")

    for i in range(1, args.requests + 1):
        try:
            size, elapsed = download(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  [{i:>2}/{args.requests}] ошибка: {exc}")
            continue
        ok += 1
        total_bytes += size
        total_time += elapsed
        speed = size * BITS_IN_BYTE / elapsed / 1e6 if elapsed > 0 else 0.0
        print(f"  [{i:>2}/{args.requests}] {size / 1e6:8.2f} МБ за {elapsed:6.3f} с  ({speed:7.2f} Мбит/с)")

    if ok == 0 or total_time <= 0:
        print("\nНи один запрос не завершился успешно.")
        return 1

    avg_time = total_time / ok
    mbit_s = total_bytes * BITS_IN_BYTE / total_time / 1e6
    mb_s = total_bytes / total_time / 1e6

    print("\nИтоги")
    print(f"  Успешных запросов:    {ok} из {args.requests}")
    print(f"  Среднее время запроса: {avg_time:.3f} с")
    print(f"  Скачано всего:         {total_bytes / 1e6:.2f} МБ")
    print(f"  Скорость скачивания:   {mbit_s:.2f} Мбит/с ({mb_s:.2f} МБ/с)")
    return 0 if ok == args.requests else 2


if __name__ == "__main__":
    sys.exit(main())
