"""
Proof of Concept: So sanh thoi gian phan hoi - Query DB (SQLite) truc tiep vs Query qua Redis cache
Mo phong day du: DB nguon (co du lieu that) -> Cache layer (Redis) -> Client

Yeu cau:
  - Container Redis dang chay (Ngay 1): docker run -d --name redis-demo -p 6379:6379 redis:latest
  - Cai thu vien redis-py: pip install redis
Cach chay:
  python poc_redis_cache.py
"""

import time
import json
import random
import sqlite3
import statistics
import redis

# ----- Cau hinh -----
REDIS_HOST = "localhost"
REDIS_PORT = 6379
TTL_SECONDS = 60
DB_IO_DELAY = 0.05           # gia lap do tre I/O/network co ban (giay), cong them vao thoi gian SQL that
NUM_USERS = 50_000           # kich thuoc du lieu mo phong - du lon de thay ro chi phi quet bang
NUM_RUNS = 15                # so lan lap lai de lay trung binh
KEY_PREFIX = "poc:user"
TARGET_USER_ID = 777         # user duoc query lap lai nhieu lan de test cache


# =========================================================
# BUOC 1: Tao "DB nguon" bang SQLite + du lieu mau (50,000 dong)
# =========================================================
def setup_mock_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")  # DB tam trong RAM, chi de mo phong - van la SQL that
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)
    # Co tinh khong tao index tren cot 'department' -> mo phong query
    # aggregate (COUNT theo phong ban) phai QUET TOAN BO BANG, giong tinh
    # huong thuc te khi mot dashboard tinh toan thong ke tren dataset lon.
    departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Support", "Product", "Design"]
    random.seed(42)  # de ket qua co the tai lap
    rows = []
    for i in range(1, NUM_USERS + 1):
        dept = departments[i % len(departments)]
        rows.append((i, f"User {i}", f"user{i}@company.com", dept))
    cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    print(f"Da tao DB gia lap voi {NUM_USERS:,} dong du lieu.")
    return conn


# =========================================================
# BUOC 2: Ham query "that" xuong DB - mo phong 1 query dashboard
# thuc te: lay ho so user + tinh so dong nghiep cung phong ban
# (aggregate query khong co index -> phai quet toan bang)
# =========================================================
def db_query_user(conn: sqlite3.Connection, user_id: int) -> dict:
    """Truy van that bang SQL (gom 1 lookup + 1 aggregate quet bang),
    cong them delay de mo phong do tre disk/network cua production DB."""
    time.sleep(DB_IO_DELAY)
    cur = conn.cursor()

    cur.execute("SELECT id, full_name, email, department FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        return None
    user = {"id": row[0], "full_name": row[1], "email": row[2], "department": row[3]}

    # Query "nang": dem so dong nghiep cung phong ban - khong co index
    # nen SQLite phai quet toan bo NUM_USERS dong. Day la dang query
    # ma trong thuc te huong loi nhieu nhat tu caching.
    cur.execute("SELECT COUNT(*) FROM users WHERE department = ?", (user["department"],))
    user["team_size"] = cur.fetchone()[0]

    return user


# =========================================================
# BUOC 3: Cache-aside pattern
# =========================================================
def query_no_cache(conn, user_id: int) -> tuple[dict, float]:
    """Luon di thang xuong DB, khong dung cache."""
    start = time.time()
    data = db_query_user(conn, user_id)
    elapsed_ms = (time.time() - start) * 1000
    return data, elapsed_ms


def query_with_cache(r: redis.Redis, conn, user_id: int) -> tuple[dict, float, str]:
    """Kiem tra Redis truoc; MISS thi query DB roi luu ket qua (that) vao Redis duoi dang JSON."""
    key = f"{KEY_PREFIX}:{user_id}"
    start = time.time()

    cached_json = r.get(key)
    if cached_json is not None:
        data = json.loads(cached_json)
        elapsed_ms = (time.time() - start) * 1000
        return data, elapsed_ms, "HIT"

    data = db_query_user(conn, user_id)
    r.setex(key, TTL_SECONDS, json.dumps(data))  # luu dung "query result" that, khong phai string gia
    elapsed_ms = (time.time() - start) * 1000
    return data, elapsed_ms, "MISS"


def main():
    print("Dang khoi tao DB gia lap (SQLite) va du lieu mau...")
    conn = setup_mock_database()

    print("Dang ket noi Redis...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=3)
        r.ping()
    except redis.exceptions.ConnectionError:
        print("LOI: Khong ket noi duoc Redis. Hay chac chan container 'redis-demo' dang chay (docker ps).")
        return

    r.flushdb()

    # ---- Demo nhanh: chung minh caching mechanism hoat dong dung ----
    print(f"\n--- DEMO: Cache-aside pattern voi user id={TARGET_USER_ID} ---")
    data1, t1, status1 = query_with_cache(r, conn, TARGET_USER_ID)
    print(f"Lan 1 [{status1}]: {t1:.2f} ms | Data: {data1}")
    data2, t2, status2 = query_with_cache(r, conn, TARGET_USER_ID)
    print(f"Lan 2 [{status2}]: {t2:.2f} ms | Data: {data2}")
    assert data1 == data2, "Du lieu tu cache phai khop voi du lieu goc tu DB!"
    print("=> Du lieu tu Redis khop 100% voi du lieu goc trong DB. Caching hoat dong dung.\n")

    r.flushdb()  # reset lai de do PoC cho cong bang

    # ---- PoC: do va so sanh thoi gian phan hoi qua nhieu lan lap ----
    print(f"--- PROOF OF CONCEPT: So sanh thoi gian phan hoi ({NUM_RUNS} lan lap) ---\n")
    no_cache_times = []
    cache_hit_times = []

    for i in range(1, NUM_RUNS + 1):
        _, t_no_cache = query_no_cache(conn, TARGET_USER_ID)
        no_cache_times.append(t_no_cache)

        _, t_cache, status = query_with_cache(r, conn, TARGET_USER_ID)
        if status == "HIT":
            cache_hit_times.append(t_cache)

        print(f"Lan {i:2d} | No-cache: {t_no_cache:7.2f} ms | Cache ({status}): {t_cache:7.2f} ms")

    print("\n" + "=" * 55)
    print("KET QUA TONG HOP")
    print("=" * 55)

    avg_no_cache = statistics.mean(no_cache_times)
    avg_cache_hit = statistics.mean(cache_hit_times) if cache_hit_times else 0

    print(f"{'Phuong thuc':<25}{'Thoi gian trung binh (ms)':>25}")
    print("-" * 55)
    print(f"{'DB (SQLite, khong cache)':<25}{avg_no_cache:>25.2f}")
    print(f"{'Redis (cache hit)':<25}{avg_cache_hit:>25.2f}")

    if avg_cache_hit > 0:
        improvement = (1 - avg_cache_hit / avg_no_cache) * 100
        speedup = avg_no_cache / avg_cache_hit
        print("-" * 55)
        print(f"\nKet luan: Redis cache giup GIAM {improvement:.1f}% thoi gian phan hoi")
        print(f"(nhanh hon xap xi {speedup:.0f} lan so voi query truc tiep tu DB).")

    # ---- Ve bieu do cot so sanh (luu ra file PNG) ----
    try:
        import matplotlib
        matplotlib.use("Agg")  # khong can man hinh, chi luu file
        import matplotlib.pyplot as plt

        labels = ["DB (khong cache)", "Redis (cache hit)"]
        values = [avg_no_cache, avg_cache_hit]
        colors = ["#e74c3c", "#2ecc71"]

        plt.figure(figsize=(6, 5))
        bars = plt.bar(labels, values, color=colors)
        plt.ylabel("Thoi gian phan hoi trung binh (ms)")
        plt.title(f"So sanh thoi gian phan hoi ({NUM_USERS:,} dong du lieu, {NUM_RUNS} lan lap)")
        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.1f} ms",
                      ha="center", va="bottom", fontsize=10)
        plt.tight_layout()
        plt.savefig("response_time_comparison.png", dpi=150)
        print("\nDa luu bieu do so sanh vao file: response_time_comparison.png")
    except ImportError:
        print("\n(Bo qua ve bieu do vi chua cai matplotlib. Chay 'pip install matplotlib' neu muon co bieu do PNG.)")

    conn.close()


if __name__ == "__main__":
    main()
