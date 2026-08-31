# Cron Syntax & Timer Triggers Reference Guide

This reference provides syntax rules, formatting guidelines, and examples for configuring background worker triggers in Antigravity.

---

## 1. Standard 5-Field Cron Syntax

The scheduler parses standard 5-field UNIX cron expressions:

```
┌───────────── Minute (0 - 59)
│ ┌───────────── Hour (0 - 23)
│ │ ┌───────────── Day of Month (1 - 31)
│ │ │ ┌───────────── Month (1 - 12 or JAN - DEC)
│ │ │ │ ┌───────────── Day of Week (0 - 7, 0 and 7 both represent Sunday, or SUN - SAT)
│ │ │ │ │
* * * * *
```

### Supported Operators:
| Operator | Description | Example | Meaning |
| :--- | :--- | :--- | :--- |
| `*` | Any value / wildcard | `* * * * *` | Every minute of every day |
| `,` | Value list separator | `15,45 * * * *` | At minute 15 and minute 45 |
| `-` | Range of values | `9-17 * * * *` | Every hour from 09:00 to 17:00 |
| `/` | Step / frequency | `*/10 * * * *` | Every 10 minutes |

---

## 2. Common Cron Schedules

| Schedule Description | Cron Expression | Example Use Case |
| :--- | :--- | :--- |
| **Every minute** | `* * * * *` | High-frequency telemetry |
| **Every 5 minutes** | `*/5 * * * *` | Standard API health checks |
| **Every 15 minutes** | `*/15 * * * *` | Queue depth monitoring |
| **Hourly (at top of hour)** | `0 * * * *` | Hourly metric aggregation |
| **Every 6 hours** | `0 */6 * * *` | Periodic checkpoint sync |
| **Daily at midnight (00:00)** | `0 0 * * *` | Daily cleanup & archiving |
| **Daily at 03:30 AM** | `30 3 * * *` | Low-traffic batch processing |
| **Weekdays at 08:00 AM** | `0 8 * * 1-5` | Business day morning reports |
| **Weekly on Sunday at 00:00** | `0 0 * * 0` | Weekly database vacuum |

---

## 3. Duration & Timer Trigger Formatting

When configuring a `trigger_type: "timer"`, the `trigger_spec` defines the interval before execution fires.

### Supported Timer Formats:
1. **Raw Seconds (Integer or Float)**:
   - `"30"` -> 30 seconds
   - `"0.5"` -> 500 milliseconds
   - `"3600"` -> 1 hour
2. **Suffixed Duration Strings**:
   - `"15s"` -> 15 seconds
   - `"10m"` -> 10 minutes (600 seconds)
   - `"2h"`  -> 2 hours (7200 seconds)
   - `"1d"`  -> 1 day (86400 seconds)

---

## 4. Edge Cases & Handling Rules

1. **Sunday Representation**: Both `0` and `7` correspond to Sunday in Day of Week.
2. **Month Representation**: Numbers `1` to `12` or standard 3-letter abbreviations (`JAN`, `FEB`, ..., `DEC`) are accepted.
3. **Leap Years & Month Lengths**: The scheduler accounts for month boundaries (28/29/30/31 days) when computing `next_run_at`.
4. **Max Iterations Limit**: When `max_iterations` is set (e.g. `5`), the scheduler automatically marks the task as `COMPLETED` after 5 successful or failed runs and stops scheduling future executions.
5. **Execution Concurrency**: Multiple workers run concurrently up to the configured daemon semaphore limit.
