import argparse
import json
import statistics
import time
import urllib.error
import urllib.request


def _build_request(url: str, method: str, payload: str | None) -> urllib.request.Request:
    if payload is None:
        return urllib.request.Request(url, method=method)
    data = payload.encode("utf-8")
    return urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )


def run(args: argparse.Namespace) -> int:
    durations_ms: list[float] = []
    failures = 0

    for i in range(1, args.iterations + 1):
        start = time.perf_counter()
        try:
            req = _build_request(args.url, args.method, args.payload)
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                resp.read()
                if resp.status >= 400:
                    failures += 1
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            failures += 1
        duration_ms = (time.perf_counter() - start) * 1000
        durations_ms.append(duration_ms)
        if args.sleep > 0:
            time.sleep(args.sleep)

        if args.verbose:
            print(f"{i}/{args.iterations} {duration_ms:.1f}ms")

    total = len(durations_ms)
    avg = statistics.mean(durations_ms) if durations_ms else 0.0
    p95 = statistics.quantiles(durations_ms, n=20)[-1] if total >= 20 else max(durations_ms, default=0.0)
    print(
        f"total={total} failures={failures} "
        f"avg_ms={avg:.1f} p95_ms={p95:.1f} min_ms={min(durations_ms):.1f} max_ms={max(durations_ms):.1f}"
    )
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Light load test for a single endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument("--path", default="/folders", help="API path.")
    parser.add_argument("--method", default="GET", choices=["GET", "POST", "PATCH", "DELETE"])
    parser.add_argument("--payload", default=None, help="Raw JSON string payload.")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between requests.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout seconds.")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.payload is not None:
        json.loads(args.payload)

    args.url = args.base_url.rstrip("/") + "/" + args.path.lstrip("/")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
