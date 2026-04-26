from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from json import JSONDecodeError
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
STATIC_DIR = ROOT / "static"
DB_PATH = Path(os.environ.get("OLFACTORY_DB_PATH", PROJECT_ROOT / "data" / "olfactory_warehouse.sqlite3"))

SAMPLE_TYPES = {"单体", "组合"}
DIFFUSION_LEVELS = {"弱", "中", "强"}
VOLATILITY_SPEEDS = {"快", "中", "慢"}
RELATIVE_INTENSITIES = {"", "强", "弱", "相近"}
HARMONY_VALUES = {"", "是", "否", "部分"}
MAX_TEXT_LENGTH = 500


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, factory=ManagedConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dim_sample (
                sample_key INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT NOT NULL UNIQUE,
                sample_type TEXT NOT NULL CHECK (sample_type IN ('单体', '组合')),
                material_name TEXT NOT NULL,
                scientific_name TEXT,
                brand_source TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dim_odor_class (
                odor_class_key INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_category TEXT NOT NULL,
                secondary_category TEXT,
                UNIQUE (primary_category, secondary_category)
            );

            CREATE TABLE IF NOT EXISTS dim_anchor (
                anchor_key INTEGER PRIMARY KEY AUTOINCREMENT,
                anchor_name TEXT NOT NULL UNIQUE,
                anchor_type TEXT
            );

            CREATE TABLE IF NOT EXISTS fact_smell_session (
                session_key INTEGER PRIMARY KEY AUTOINCREMENT,
                smell_date TEXT NOT NULL,
                sample_key INTEGER NOT NULL,
                odor_class_key INTEGER NOT NULL,
                intensity INTEGER NOT NULL CHECK (intensity BETWEEN 1 AND 5),
                diffusion TEXT NOT NULL CHECK (diffusion IN ('弱', '中', '强')),
                volatility_speed TEXT NOT NULL CHECK (volatility_speed IN ('快', '中', '慢')),
                preference_score INTEGER CHECK (preference_score BETWEEN 1 AND 5),
                usage_scene TEXT,
                association_desc TEXT,
                free_note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sample_key) REFERENCES dim_sample(sample_key),
                FOREIGN KEY (odor_class_key) REFERENCES dim_odor_class(odor_class_key)
            );

            CREATE TABLE IF NOT EXISTS bridge_session_keyword (
                session_key INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                PRIMARY KEY (session_key, keyword),
                FOREIGN KEY (session_key) REFERENCES fact_smell_session(session_key) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS fact_volatility_note (
                session_key INTEGER NOT NULL,
                minute_mark INTEGER NOT NULL,
                stage_label TEXT NOT NULL,
                odor_note TEXT,
                PRIMARY KEY (session_key, minute_mark),
                FOREIGN KEY (session_key) REFERENCES fact_smell_session(session_key) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS fact_comparison (
                comparison_key INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key INTEGER NOT NULL,
                compared_sample TEXT,
                difference_desc TEXT,
                relative_intensity TEXT CHECK (relative_intensity IN ('', '强', '弱', '相近')),
                anchor_key INTEGER,
                FOREIGN KEY (session_key) REFERENCES fact_smell_session(session_key) ON DELETE CASCADE,
                FOREIGN KEY (anchor_key) REFERENCES dim_anchor(anchor_key)
            );

            CREATE TABLE IF NOT EXISTS fact_blend_experiment (
                blend_key INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key INTEGER NOT NULL,
                formula_ratio TEXT,
                harmonious TEXT CHECK (harmonious IN ('', '是', '否', '部分')),
                conflict_desc TEXT,
                improvement_suggestion TEXT,
                FOREIGN KEY (session_key) REFERENCES fact_smell_session(session_key) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_session_date ON fact_smell_session(smell_date);
            CREATE INDEX IF NOT EXISTS idx_keyword ON bridge_session_keyword(keyword);
            """
        )


def json_response(handler: SimpleHTTPRequestHandler, payload: object, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    try:
        payload = json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, JSONDecodeError) as exc:
        raise ValueError(f"请求 JSON 无效: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")
    return payload


def normalize_keywords(value: str) -> list[str]:
    for separator in [",", "，", "、", ";", "；", "\n"]:
        value = value.replace(separator, "|")
    return sorted({part.strip() for part in value.split("|") if part.strip()})


def as_text(payload: dict, field: str, *, required: bool = False, max_length: int = MAX_TEXT_LENGTH) -> str:
    value = payload.get(field, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"{field} 必须是文本")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{field} 不能为空")
    if len(value) > max_length:
        raise ValueError(f"{field} 不能超过 {max_length} 个字符")
    return value


def as_enum(payload: dict, field: str, allowed: set[str], *, required: bool = True) -> str:
    value = as_text(payload, field, required=required, max_length=30)
    if value not in allowed:
        allowed_values = "、".join(sorted(item for item in allowed if item)) or "空"
        raise ValueError(f"{field} 必须是以下值之一: {allowed_values}")
    return value


def as_int_range(payload: dict, field: str, minimum: int, maximum: int, *, required: bool = True) -> int | None:
    raw_value = payload.get(field, "")
    if raw_value in (None, "") and not required:
        return None
    if isinstance(raw_value, bool):
        raise ValueError(f"{field} 必须是 {minimum}-{maximum} 的整数")
    if isinstance(raw_value, int):
        value = raw_value
    elif isinstance(raw_value, str) and raw_value.strip().isdigit():
        value = int(raw_value.strip())
    else:
        raise ValueError(f"{field} 必须是 {minimum}-{maximum} 的整数")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} 必须在 {minimum}-{maximum} 之间")
    return value


def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("smell_date 格式应为 YYYY-MM-DD") from exc
    return value


def sanitize_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")
    return {
        "smell_date": validate_date(as_text(payload, "smell_date", required=True, max_length=10)),
        "sample_id": as_text(payload, "sample_id", required=True, max_length=40),
        "sample_type": as_enum(payload, "sample_type", SAMPLE_TYPES),
        "material_name": as_text(payload, "material_name", required=True, max_length=120),
        "scientific_name": as_text(payload, "scientific_name", max_length=160),
        "brand_source": as_text(payload, "brand_source", max_length=160),
        "primary_category": as_text(payload, "primary_category", required=True, max_length=80),
        "secondary_category": as_text(payload, "secondary_category", max_length=80),
        "keywords": as_text(payload, "keywords", max_length=240),
        "intensity": as_int_range(payload, "intensity", 1, 5),
        "diffusion": as_enum(payload, "diffusion", DIFFUSION_LEVELS),
        "note_0m": as_text(payload, "note_0m"),
        "note_10m": as_text(payload, "note_10m"),
        "note_30m": as_text(payload, "note_30m"),
        "note_2h": as_text(payload, "note_2h"),
        "volatility_speed": as_enum(payload, "volatility_speed", VOLATILITY_SPEEDS),
        "compared_sample": as_text(payload, "compared_sample", max_length=120),
        "difference_desc": as_text(payload, "difference_desc"),
        "relative_intensity": as_enum(payload, "relative_intensity", RELATIVE_INTENSITIES, required=False),
        "anchor_name": as_text(payload, "anchor_name", max_length=120),
        "formula_ratio": as_text(payload, "formula_ratio", max_length=240),
        "harmonious": as_enum(payload, "harmonious", HARMONY_VALUES, required=False),
        "conflict_desc": as_text(payload, "conflict_desc", max_length=240),
        "improvement_suggestion": as_text(payload, "improvement_suggestion"),
        "preference_score": as_int_range(payload, "preference_score", 1, 5, required=False),
        "usage_scene": as_text(payload, "usage_scene", max_length=160),
        "association_desc": as_text(payload, "association_desc"),
        "free_note": as_text(payload, "free_note"),
    }


def validate(payload: dict) -> list[str]:
    try:
        sanitize_payload(payload)
    except ValueError as exc:
        return [str(exc)]
    return []


def get_or_create_sample(conn: sqlite3.Connection, payload: dict) -> int:
    row = conn.execute("SELECT sample_key FROM dim_sample WHERE sample_id = ?", (payload["sample_id"],)).fetchone()
    if row:
        conn.execute(
            """
            UPDATE dim_sample
               SET sample_type = ?, material_name = ?, scientific_name = ?, brand_source = ?
             WHERE sample_key = ?
            """,
            (payload["sample_type"], payload["material_name"], payload["scientific_name"], payload["brand_source"], row["sample_key"]),
        )
        return int(row["sample_key"])
    cursor = conn.execute(
        """
        INSERT INTO dim_sample (sample_id, sample_type, material_name, scientific_name, brand_source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload["sample_id"], payload["sample_type"], payload["material_name"], payload["scientific_name"], payload["brand_source"]),
    )
    return int(cursor.lastrowid)


def get_or_create_odor_class(conn: sqlite3.Connection, payload: dict) -> int:
    primary = payload["primary_category"]
    secondary = payload["secondary_category"]
    row = conn.execute(
        "SELECT odor_class_key FROM dim_odor_class WHERE primary_category = ? AND secondary_category = ?",
        (primary, secondary),
    ).fetchone()
    if row:
        return int(row["odor_class_key"])
    cursor = conn.execute(
        "INSERT INTO dim_odor_class (primary_category, secondary_category) VALUES (?, ?)",
        (primary, secondary),
    )
    return int(cursor.lastrowid)


def get_or_create_anchor(conn: sqlite3.Connection, anchor_name: str) -> int | None:
    if not anchor_name:
        return None
    row = conn.execute("SELECT anchor_key FROM dim_anchor WHERE anchor_name = ?", (anchor_name,)).fetchone()
    if row:
        return int(row["anchor_key"])
    cursor = conn.execute("INSERT INTO dim_anchor (anchor_name, anchor_type) VALUES (?, ?)", (anchor_name, "归属锚点"))
    return int(cursor.lastrowid)


def create_record(payload: dict) -> int:
    payload = sanitize_payload(payload)
    with connect() as conn:
        sample_key = get_or_create_sample(conn, payload)
        odor_class_key = get_or_create_odor_class(conn, payload)
        cursor = conn.execute(
            """
            INSERT INTO fact_smell_session (
                smell_date, sample_key, odor_class_key, intensity, diffusion,
                volatility_speed, preference_score, usage_scene, association_desc, free_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["smell_date"], sample_key, odor_class_key, payload["intensity"], payload["diffusion"],
                payload["volatility_speed"], payload["preference_score"], payload["usage_scene"],
                payload["association_desc"], payload["free_note"],
            ),
        )
        session_key = int(cursor.lastrowid)
        for keyword in normalize_keywords(payload["keywords"]):
            conn.execute("INSERT OR IGNORE INTO bridge_session_keyword (session_key, keyword) VALUES (?, ?)", (session_key, keyword))
        conn.executemany(
            "INSERT INTO fact_volatility_note (session_key, minute_mark, stage_label, odor_note) VALUES (?, ?, ?, ?)",
            [
                (session_key, 0, "0分钟", payload["note_0m"]),
                (session_key, 10, "10分钟", payload["note_10m"]),
                (session_key, 30, "30分钟", payload["note_30m"]),
                (session_key, 120, "2小时", payload["note_2h"]),
            ],
        )
        anchor_key = get_or_create_anchor(conn, payload["anchor_name"])
        conn.execute(
            """
            INSERT INTO fact_comparison (session_key, compared_sample, difference_desc, relative_intensity, anchor_key)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_key, payload["compared_sample"], payload["difference_desc"], payload["relative_intensity"], anchor_key),
        )
        if payload["sample_type"] == "组合" or any(payload[key] for key in ["formula_ratio", "harmonious", "conflict_desc", "improvement_suggestion"]):
            conn.execute(
                """
                INSERT INTO fact_blend_experiment (session_key, formula_ratio, harmonious, conflict_desc, improvement_suggestion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_key, payload["formula_ratio"], payload["harmonious"], payload["conflict_desc"], payload["improvement_suggestion"]),
            )
        return session_key


def list_records() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            WITH keyword_rollup AS (
                SELECT session_key, GROUP_CONCAT(keyword, '、') AS keywords
                  FROM bridge_session_keyword GROUP BY session_key
            ),
            volatility_rollup AS (
                SELECT session_key,
                       MAX(CASE WHEN minute_mark = 0 THEN odor_note END) AS note_0m,
                       MAX(CASE WHEN minute_mark = 10 THEN odor_note END) AS note_10m,
                       MAX(CASE WHEN minute_mark = 30 THEN odor_note END) AS note_30m,
                       MAX(CASE WHEN minute_mark = 120 THEN odor_note END) AS note_2h
                  FROM fact_volatility_note GROUP BY session_key
            )
            SELECT s.session_key, s.smell_date, ds.sample_id, ds.sample_type, ds.material_name,
                   ds.scientific_name, ds.brand_source, oc.primary_category, oc.secondary_category,
                   s.intensity, s.diffusion, s.volatility_speed, s.preference_score, s.usage_scene,
                   s.association_desc, s.free_note, c.compared_sample, c.difference_desc,
                   c.relative_intensity, a.anchor_name, b.formula_ratio, b.harmonious,
                   b.conflict_desc, b.improvement_suggestion, k.keywords,
                   v.note_0m, v.note_10m, v.note_30m, v.note_2h
              FROM fact_smell_session s
              JOIN dim_sample ds ON ds.sample_key = s.sample_key
              JOIN dim_odor_class oc ON oc.odor_class_key = s.odor_class_key
              LEFT JOIN keyword_rollup k ON k.session_key = s.session_key
              LEFT JOIN volatility_rollup v ON v.session_key = s.session_key
              LEFT JOIN fact_comparison c ON c.session_key = s.session_key
              LEFT JOIN dim_anchor a ON a.anchor_key = c.anchor_key
              LEFT JOIN fact_blend_experiment b ON b.session_key = s.session_key
             ORDER BY s.smell_date DESC, s.session_key DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def model_description() -> dict:
    return {
        "dim_sample": "样本维表：样本ID、类型、原料名称、学名、品牌/来源。",
        "dim_odor_class": "气味分类维表：一级分类、二级分类。",
        "dim_anchor": "标准化锚点维表：用于记录更接近哪个标准。",
        "fact_smell_session": "闻香事实表：一次闻香记录的日期、强度、扩散性、挥发速度和主观评价。",
        "bridge_session_keyword": "关键词桥表：一条记录可以有多个可对比关键词。",
        "fact_volatility_note": "挥发变化明细事实：0分钟、10分钟、30分钟、2小时。",
        "fact_comparison": "对比事实：对比样本、差异描述、相对强度、归属锚点。",
        "fact_blend_experiment": "组合实验事实：配方比例、是否和谐、冲突和改进建议。",
    }


def csv_export() -> bytes:
    rows = list_records()
    output = io.StringIO()
    fieldnames = [
        "smell_date", "sample_id", "material_name", "sample_type", "scientific_name", "brand_source",
        "primary_category", "secondary_category", "keywords", "intensity", "diffusion", "note_0m",
        "note_10m", "note_30m", "note_2h", "volatility_speed", "compared_sample", "difference_desc",
        "relative_intensity", "anchor_name", "formula_ratio", "harmonious", "conflict_desc",
        "improvement_suggestion", "preference_score", "usage_scene", "association_desc", "free_note",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        if parsed.path.startswith("/static/"):
            return str(ROOT / parsed.path.lstrip("/"))
        if parsed.path in {"/", "/index.html"}:
            return str(STATIC_DIR / "index.html")
        return str(STATIC_DIR / parsed.path.lstrip("/"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/records":
            json_response(self, {"records": list_records()})
        elif parsed.path == "/api/model":
            json_response(self, model_description())
        elif parsed.path == "/api/export.csv":
            body = csv_export()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="olfactory-records.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/records":
            json_response(self, {"error": "Not found"}, 404)
            return
        try:
            session_key = create_record(read_json(self))
            json_response(self, {"ok": True, "session_key": session_key}, 201)
        except ValueError as exc:
            json_response(self, {"error": str(exc)}, 400)
        except Exception as exc:
            json_response(self, {"error": f"保存失败: {exc}"}, 500)

    def do_DELETE(self) -> None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "records"]:
            json_response(self, {"error": "Not found"}, 404)
            return
        try:
            session_key = int(parts[2])
        except ValueError:
            json_response(self, {"error": "记录ID无效"}, 400)
            return
        with connect() as conn:
            cursor = conn.execute("DELETE FROM fact_smell_session WHERE session_key = ?", (session_key,))
            if cursor.rowcount == 0:
                json_response(self, {"error": "记录不存在"}, 404)
                return
        json_response(self, {"ok": True})


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"闻香记录系统已启动: http://{host}:{port}")
    print(f"数据库文件: {DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    run(host=os.environ.get("OLFACTORY_HOST", "127.0.0.1"), port=int(os.environ.get("OLFACTORY_PORT", "8765")))
