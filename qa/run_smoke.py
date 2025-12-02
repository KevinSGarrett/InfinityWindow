from __future__ import annotations

import traceback

from . import message_search_probe, mode_routing_probe, tasks_autoloop_probe


PROBES = [
    ("Message search", message_search_probe.run),
    ("Autonomous tasks", tasks_autoloop_probe.run),
    ("Mode routing", mode_routing_probe.run),
]


def main() -> int:
    print("Running QA smoke suite...\n")
    failures: list[str] = []
    for label, probe in PROBES:
        print(f"→ {label}… ", end="", flush=True)
        try:
            probe()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{label}: {exc}")
            print("FAIL")
            traceback.print_exc()
        else:
            print("OK")

    if failures:
        print("\nSmoke suite finished with failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nSmoke suite PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

