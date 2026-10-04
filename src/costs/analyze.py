import csv
import io

PROVIDERS = {"gcp", "aws"}

CSV_COLUMNS = {
    "gcp": {"service": "service.description", "cost": "cost", "day": "usage_start_time", "currency": "currency"},
    "aws": {"service": "lineItem/ProductCode", "cost": "lineItem/UnblendedCost", "day": "lineItem/UsageStartDate", "currency": "lineItem/CurrencyCode"},
}


class CostError(ValueError):
    pass


def normalize(row):
    for key in ("provider", "service", "cost"):
        if key not in row or row[key] in (None, ""):
            raise CostError(f"row is missing {key}")
    if row["provider"] not in PROVIDERS:
        raise CostError(f"provider {row['provider']} is not supported")
    try:
        cost = float(row["cost"])
    except (TypeError, ValueError) as exc:
        raise CostError(f"cost is not a number: {row['cost']}") from exc
    return {
        "provider": row["provider"],
        "service": str(row["service"]).strip(),
        "cost": cost,
        "currency": row.get("currency") or "USD",
        "day": str(row.get("day") or "")[:10] or None,
    }


def parse_csv(text, provider):
    if provider not in CSV_COLUMNS:
        raise CostError(f"no CSV mapping for provider {provider}")
    columns = CSV_COLUMNS[provider]
    reader = csv.DictReader(io.StringIO(text.strip()))
    missing = [column for column in (columns["service"], columns["cost"]) if column not in (reader.fieldnames or [])]
    if missing:
        raise CostError(f"CSV is missing column {', '.join(missing)}")
    rows = []
    for raw in reader:
        rows.append(
            {
                "provider": provider,
                "service": raw[columns["service"]],
                "cost": raw[columns["cost"]],
                "currency": raw.get(columns["currency"]) or "USD",
                "day": raw.get(columns["day"]),
            }
        )
    return rows


def summarize(rows, provider=None, budget=None):
    clean = [normalize(row) for row in rows]
    chosen = [row for row in clean if provider is None or row["provider"] == provider]
    currencies = {row["currency"] for row in chosen}
    if len(currencies) > 1:
        raise CostError(f"mixed currencies {sorted(currencies)}; convert before summing")
    totals = {}
    credits = 0.0
    for row in chosen:
        totals[row["service"]] = round(totals.get(row["service"], 0) + row["cost"], 2)
        if row["cost"] < 0:
            credits = round(credits + row["cost"], 2)
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = {"service": ranked[0][0], "cost": ranked[0][1]} if ranked else None
    total = round(sum(totals.values()), 2)
    result = {
        "provider": provider or "all",
        "currency": currencies.pop() if currencies else "USD",
        "total": total,
        "credits": credits,
        "by_service": [{"service": name, "cost": cost, "share": round(cost / total * 100, 1) if total else 0} for name, cost in ranked],
        "top_service": top,
        "spikes": spikes(chosen),
    }
    if budget is not None:
        result["budget"] = {
            "limit": budget,
            "used_percent": round(total / budget * 100, 1) if budget else None,
            "over": total > budget,
            "remaining": round(budget - total, 2),
        }
    return result


def spikes(rows, ratio=1.5):
    by_day = {}
    for row in rows:
        if row["day"]:
            by_day[row["day"]] = round(by_day.get(row["day"], 0) + row["cost"], 2)
    days = sorted(by_day)
    found = []
    for previous, current in zip(days, days[1:]):
        before, after = by_day[previous], by_day[current]
        if before > 0 and after >= before * ratio:
            found.append({"day": current, "previous": before, "cost": after, "ratio": round(after / before, 2)})
    return found
