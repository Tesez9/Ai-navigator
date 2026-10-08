import sqlite3
from datetime import datetime

graph = {
    "A": {"B": (5, 7, 3, 2), "D": (6, 9, 2, 1)},
    "B": {"A": (5, 7, 3, 2), "C": (4, 6, 2, 2), "D": (4, 6, 2, 2), "E": (6, 9, 4, 3)},
    "C": {"B": (4, 6, 2, 2), "D": (5, 8, 2, 1), "F": (6, 9, 2, 2), "G": (12, 18, 3, 2)},
    "D": {"A": (6, 9, 2, 1), "B": (4, 6, 2, 2), "C": (5, 8, 2, 1), "F": (7, 10, 2, 1)},
    "E": {"B": (6, 9, 4, 3), "F": (5, 8, 3, 2), "G": (7, 11, 3, 2)},
    "F": {"C": (6, 9, 2, 2), "D": (7, 10, 2, 1), "E": (5, 8, 3, 2), "G": (6, 9, 2, 1)},
    "G": {"C": (12, 18, 3, 2), "E": (7, 11, 3, 2), "F": (6, 9, 2, 1)}
}

db = sqlite3.connect("navigator.db")
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS routes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_point TEXT,
    finish_point TEXT,
    route TEXT,
    distance REAL,
    time REAL,
    traffic REAL,
    actual_time REAL,
    actual_distance REAL,
    created_at TEXT)""")
db.commit()

def dijkstra(start, finish):
    dist = {v: float("inf") for v in graph}
    prev = {}
    used = set()
    dist[start] = 0
    while True:
        current = None
        for v in graph:
            if v not in used and (current is None or dist[v] < dist[current]):
                current = v
        if current is None or current == finish:
            break
        used.add(current)
        for neighbor, road in graph[current].items():
            new_dist = dist[current] + road[1]
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = current
    if dist[finish] == float("inf"):
        return None
    route = [finish]
    while route[-1] != start:
        route.append(prev[route[-1]])
    route.reverse()
    return route

def find_all_routes(start, finish, route=None):
    if route is None:
        route = [start]
    if start == finish:
        return [route]
    routes = []
    for neighbor in graph[start]:
        if neighbor not in route:
            routes += find_all_routes(neighbor, finish, route + [neighbor])
    return routes

def route_info(route):
    distance = 0
    time = 0
    traffic = 0
    for i in range(len(route) - 1):
        road = graph[route[i]][route[i + 1]]
        distance += road[0]
        time += road[1]
        traffic += road[2]
    parts = len(route) - 1
    return (distance, time, traffic / parts)

def ai_text(route_str, count, expected, actual):
    if count < 3:
        return "Маршрут " + route_str.replace(",", " -> ") + ": проходжень лише " + str(count) + ". Даних мало, треба мінімум 3-5 проходжень"
    if actual is None:
        return "Маршрут " + route_str.replace(",", " -> ") + " використано " + str(count) + " разів. Прогноз " + str(round(expected, 1)) + " хв. Факту ще нема, додайте через пункт 2"
    diff = actual - expected
    if expected != 0:
        pct = diff / expected * 100
    else:
        pct = 0
    if diff > 1:
        low = int(pct - 5)
        if low < 5:
            low = 5
        high = int(pct + 5)
        return "Маршрут " + route_str.replace(",", " -> ") + " часто займає більше часу, ніж прогноз. Проходжень " + str(count) + ", факт " + str(round(actual, 1)) + " хв, прогноз " + str(round(expected, 1)) + " хв (+" + str(int(pct)) + "%). Треба закладати додаткові " + str(low) + "-" + str(high) + "% часу"
    if diff < -1:
        return "Маршрут " + route_str.replace(",", " -> ") + " швидший за прогноз. Факт " + str(round(actual, 1)) + " хв, прогноз " + str(round(expected, 1)) + " хв. Можна рекомендувати"
    return "Маршрут " + route_str.replace(",", " -> ") + " точний: факт " + str(round(actual, 1)) + " хв, прогноз " + str(round(expected, 1)) + " хв"

def find_route():
    start = input("Початкова точка: ").upper()
    finish = input("Кінцева точка: ").upper()
    if start not in graph or finish not in graph:
        print("Невірна точка.")
        return
    if start == finish:
        print("Початок і кінець однакові")
        return
    best = dijkstra(start, finish)
    print("\nDijkstra рекомендує:")
    print(" -> ".join(best))
    distance, time, traffic = route_info(best)
    print(str(distance) + " км | " + str(time) + " хв")
    routes = find_all_routes(start, finish)
    routes.sort(key=lambda r: route_info(r)[1])
    routes = routes[:3]
    print("\nМожливі маршрути:")
    for i, route in enumerate(routes, 1):
        d, t, tr = route_info(route)
        print(f"{i}. {' -> '.join(route)} | {d} км | {t} хв")
    choice = int(input("\nЯким маршрутом поїхали? ")) - 1
    if choice < 0 or choice >= len(routes):
        print("Нема такого маршруту, введіть число від 1 до " + str(len(routes)))
        return
    route = routes[choice]
    d, t, tr = route_info(route)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO routes (start_point, finish_point, route, distance, time, traffic, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (start, finish, ",".join(route), d, t, tr, now))
    db.commit()
    print("Маршрут збережено.")
    print("ID поїздки:", cur.lastrowid)

def add_result():
    route_id = int(input("ID поїздки: "))
    actual_time = float(input("Фактичний час: "))
    s = input("Фактична відстань (Enter пропустити): ").strip().replace(",", ".")
    row = cur.execute("SELECT distance FROM routes WHERE id=?", (route_id,)).fetchone()
    if row is None:
        print("Такого id нема")
        return
    if s == "":
        actual_distance = row[0]
    else:
        actual_distance = float(s)
    cur.execute("UPDATE routes SET actual_time=?, actual_distance=? WHERE id=?", (actual_time, actual_distance, route_id))
    db.commit()
    print("Результат збережено.")

def history():
    rows = cur.execute("SELECT id, start_point, finish_point, route, distance, time, actual_time, actual_distance, created_at FROM routes").fetchall()
    if len(rows) == 0:
        print("Історія пуста")
        return
    for r in rows:
        print(f"ID: {r[0]} | {r[1]} -> {r[2]} | {r[3].replace(',', ' -> ')} | прогноз: {r[5]} хв | факт: {r[6]}")

def statistics():
    rows = cur.execute("SELECT route, COUNT(*), AVG(time), AVG(actual_time), AVG(distance), MIN(actual_time), MAX(actual_time) FROM routes GROUP BY route").fetchall()
    if len(rows) == 0:
        print("База пуста")
        return
    print("\n===== СТАТИСТИКА =====")
    for r in rows:
        print("\nМаршрут:", r[0].replace(",", " -> "))
        print("Поїздок:", r[1])
        print("Середній прогноз:", round(r[2], 1))
        if r[3] is None:
            print("Середній факт: нема")
        else:
            print("Середній факт:", round(r[3], 1))
        print("Середня відстань:", round(r[4], 1))
        print("Найшвидший час:", r[5])
        print("Найповільніший час:", r[6])
    row = cur.execute("SELECT AVG(time), AVG(actual_time) FROM routes WHERE actual_time IS NOT NULL").fetchone()
    if row[1] is not None:
        print("\nПрогноз:", round(row[0], 1), "хв")
        print("Факт:", round(row[1], 1), "хв")
        print("Різниця:", round(row[1] - row[0], 1), "хв")

def ai_recommendation():
    start = input("Початкова точка: ").upper()
    finish = input("Кінцева точка: ").upper()
    if start not in graph or finish not in graph:
        print("Невірна точка.")
        return
    dijkstra_route = dijkstra(start, finish)
    rows = cur.execute("SELECT route, COUNT(*), AVG(time), AVG(actual_time) FROM routes WHERE start_point=? AND finish_point=? AND actual_time IS NOT NULL GROUP BY route", (start, finish)).fetchall()
    print("\n===== АНАЛІЗ СИСТЕМИ =====")
    print("Dijkstra:", " -> ".join(dijkstra_route))
    d0, t0, tr0 = route_info(dijkstra_route)
    print(str(d0) + " км | " + str(t0) + " хв прогноз")
    if not rows:
        print("Історичних даних поки немає.")
        print("Рекомендація: використати маршрут Dijkstra.")
        return
    best_route = None
    best_actual_time = float("inf")
    for route, count, expected, actual in rows:
        difference = actual - expected
        coefficient = actual / expected
        print("\nМаршрут:", route.replace(",", " -> "))
        print("Поїздок:", count)
        print("Прогноз:", round(expected, 1), "хв")
        print("Факт:", round(actual, 1), "хв")
        print("Різниця:", round(difference, 1), "хв")
        print("Коефіцієнт:", round(coefficient, 2))
        print(ai_text(route, count, expected, actual))
        if actual < best_actual_time:
            best_actual_time = actual
            best_route = route
    print("\n===== РЕКОМЕНДАЦІЯ =====")
    if best_route is None:
        print("Недостатньо даних для впевненої рекомендації.")
        print("Поки що використовуйте:", " -> ".join(dijkstra_route))
    else:
        print("Рекомендований маршрут:", best_route.replace(",", " -> "))
        print("Середній фактичний час:", round(best_actual_time, 1), "хв")
        if best_route == ",".join(dijkstra_route):
            print("Маршрут Dijkstra підтверджується історичними даними.")
        else:
            print("За історичними даними цей маршрут швидший за стандартний маршрут Dijkstra.")

while True:
    print("""===== AI NAVIGATOR =====
1. Знайти маршрут
2. Додати результат проходження
3. Історія маршрутів
4. Статистика
5. AI-рекомендація
6. Показати карту
0. Вихід""")
    choice = input("> ")
    if choice == "1":
        find_route()
    elif choice == "2":
        add_result()
    elif choice == "3":
        history()
    elif choice == "4":
        statistics()
    elif choice == "5":
        ai_recommendation()
    elif choice == "6":
        print("A - B: 5 км, 7 хв, затори 3, складність 2")
        print("A - D: 6 км, 9 хв, затори 2, складність 1")
        print("B - C: 4 км, 6 хв, затори 2, складність 2")
        print("B - D: 4 км, 6 хв, затори 2, складність 2")
        print("B - E: 6 км, 9 хв, затори 4, складність 3")
        print("C - D: 5 км, 8 хв, затори 2, складність 1")
        print("C - F: 6 км, 9 хв, затори 2, складність 2")
        print("C - G: 12 км, 18 хв, затори 3, складність 2")
        print("D - F: 7 км, 10 хв, затори 2, складність 1")
        print("E - F: 5 км, 8 хв, затори 3, складність 2")
        print("E - G: 7 км, 11 хв, затори 3, складність 2")
        print("F - G: 6 км, 9 хв, затори 2, складність 1")
    elif choice == "0":
        break
    else:
        print("Нема такого пункту")

db.close()
