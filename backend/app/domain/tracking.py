import math

Point = tuple[float, float]


def haversine_km(a: Point, b: Point) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def build_route(start: Point, end: Point) -> list[Point]:
    mid_lat = start[0] + (end[0] - start[0]) * 0.45
    mid_lng = start[1] + (end[1] - start[1]) * 0.6
    return [start, (mid_lat, start[1]), (mid_lat, mid_lng), (end[0], mid_lng), end]


def position_on_route(route: list[Point], progress: float) -> Point:
    progress = min(max(progress, 0.0), 1.0)
    segments = [haversine_km(route[i], route[i + 1]) for i in range(len(route) - 1)]
    total = sum(segments)
    if total == 0:
        return route[-1]
    target = total * progress
    for i, seg in enumerate(segments):
        if target <= seg or i == len(segments) - 1:
            ratio = 0.0 if seg == 0 else min(target / seg, 1.0)
            a, b = route[i], route[i + 1]
            return (a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio)
        target -= seg
    return route[-1]
