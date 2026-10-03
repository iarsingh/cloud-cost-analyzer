def summarize(rows, provider=None):
    chosen = [row for row in rows if provider is None or row["provider"] == provider]
    totals = {}
    for row in chosen:
        totals[row["service"]] = round(totals.get(row["service"], 0) + float(row["cost"]), 2)
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = {"service": ranked[0][0], "cost": ranked[0][1]} if ranked else None
    return {
        "provider": provider or "all",
        "currency": "USD",
        "total": round(sum(totals.values()), 2),
        "by_service": [{"service": name, "cost": cost} for name, cost in ranked],
        "top_service": top,
    }
