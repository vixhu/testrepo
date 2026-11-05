from math import ceil


def paginate_query(query, page: int | None = None, limit: int | None = None):
    if page is None:
        return query.all(), None

    page = max(int(page), 1)
    limit = min(max(int(limit or 20), 1), 100)
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": ceil(total / limit) if total else 0,
    }
