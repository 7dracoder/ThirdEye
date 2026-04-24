"""
ThirdEye — Database Connection Manager
Supports PostgreSQL (production) and SQLite (development fallback).
"""

import os
import json
import uuid
import sqlite3
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("thirdeye.database")

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgresql"))

# SQLite fallback path
SQLITE_PATH = Path(__file__).parent.parent / "data" / "thirdeye.db"


class Database:
    """Unified database interface with PostgreSQL and SQLite backends."""

    def __init__(self):
        self.pool = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._is_postgres = USE_POSTGRES
        self._initialized = False

    async def connect(self):
        """Initialize database connection."""
        if self._initialized:
            return

        if self._is_postgres:
            try:
                import asyncpg
                self.pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                )
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
                self._is_postgres = False

        if not self._is_postgres:
            SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._sqlite_conn = sqlite3.connect(str(SQLITE_PATH))
            self._sqlite_conn.row_factory = sqlite3.Row
            self._sqlite_conn.execute("PRAGMA journal_mode=WAL")
            self._sqlite_conn.execute("PRAGMA foreign_keys=ON")
            await self._init_sqlite_schema()
            logger.info(f"Connected to SQLite database at {SQLITE_PATH}")

        self._initialized = True

    async def _init_sqlite_schema(self):
        """Create SQLite tables matching the PostgreSQL schema."""
        cursor = self._sqlite_conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS persons (
                id              TEXT PRIMARY KEY,
                name            TEXT,
                age             INTEGER,
                gender          TEXT,
                description     TEXT,
                last_known_location TEXT,
                last_known_lat  REAL,
                last_known_lng  REAL,
                contact_info    TEXT,
                photos          TEXT DEFAULT '[]',
                embeddings      TEXT DEFAULT '[]',
                status          TEXT DEFAULT 'active',
                current_radius  REAL DEFAULT 1.0,
                epicenter_lat   REAL,
                epicenter_lng   REAL,
                share_token     TEXT,
                created_at      TEXT,
                updated_at      TEXT,
                last_scan_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS matches (
                id              TEXT PRIMARY KEY,
                person_id       TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                source          TEXT NOT NULL,
                url             TEXT,
                image_url       TEXT,
                image_path      TEXT,
                similarity      REAL NOT NULL,
                confidence_label TEXT NOT NULL,
                location        TEXT,
                lat             REAL,
                lng             REAL,
                raw_text        TEXT,
                metadata        TEXT DEFAULT '{}',
                reviewed        INTEGER DEFAULT 0,
                confirmed       INTEGER DEFAULT 0,
                created_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS locations (
                id              TEXT PRIMARY KEY,
                person_id       TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                match_id        TEXT,
                location        TEXT NOT NULL,
                lat             REAL NOT NULL,
                lng             REAL NOT NULL,
                source          TEXT,
                confidence      REAL,
                timestamp       TEXT NOT NULL,
                created_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS alerts_sent (
                id              TEXT PRIMARY KEY,
                person_id       TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                match_id        TEXT,
                channel         TEXT NOT NULL,
                recipient       TEXT,
                payload         TEXT,
                status          TEXT DEFAULT 'sent',
                error_message   TEXT,
                created_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS crowdsource_sightings (
                id              TEXT PRIMARY KEY,
                person_id       TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
                share_token     TEXT NOT NULL,
                image_path      TEXT,
                location        TEXT,
                lat             REAL,
                lng             REAL,
                description     TEXT,
                similarity      REAL,
                confidence_label TEXT,
                status          TEXT DEFAULT 'pending',
                submitter_ip    TEXT,
                created_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS cameras (
                id              TEXT PRIMARY KEY,
                source          TEXT NOT NULL,
                name            TEXT,
                url             TEXT NOT NULL,
                lat             REAL NOT NULL,
                lng             REAL NOT NULL,
                city            TEXT,
                state           TEXT,
                active          INTEGER DEFAULT 1,
                last_checked_at TEXT,
                created_at      TEXT
            );
        """)
        self._sqlite_conn.commit()

    # ── Generic Query Methods ──

    async def execute(self, query: str, *args) -> Any:
        """Execute a write query (INSERT, UPDATE, DELETE)."""
        if self._is_postgres:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        else:
            cursor = self._sqlite_conn.cursor()
            # Convert PostgreSQL $1, $2 style to ? for SQLite
            sqlite_query = self._convert_query(query)
            cursor.execute(sqlite_query, args)
            self._sqlite_conn.commit()
            return cursor

    async def fetchone(self, query: str, *args) -> Optional[dict]:
        """Fetch a single row."""
        if self._is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        else:
            cursor = self._sqlite_conn.cursor()
            sqlite_query = self._convert_query(query)
            cursor.execute(sqlite_query, args)
            row = cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(self, query: str, *args) -> list[dict]:
        """Fetch all rows."""
        if self._is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        else:
            cursor = self._sqlite_conn.cursor()
            sqlite_query = self._convert_query(query)
            cursor.execute(sqlite_query, args)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        if self._is_postgres:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        else:
            cursor = self._sqlite_conn.cursor()
            sqlite_query = self._convert_query(query)
            cursor.execute(sqlite_query, args)
            row = cursor.fetchone()
            return row[0] if row else None

    def _convert_query(self, query: str) -> str:
        """Convert PostgreSQL parameter style ($1, $2) to SQLite (?)."""
        import re
        return re.sub(r'\$\d+', '?', query)

    # ── Person CRUD ──

    async def create_person(self, **kwargs) -> str:
        """Create a new person profile. Returns the person ID."""
        person_id = str(uuid.uuid4())
        share_token = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        photos = kwargs.get("photos", [])
        embeddings = kwargs.get("embeddings", [])

        if self._is_postgres:
            await self.execute(
                """INSERT INTO persons (id, name, age, gender, description,
                   last_known_location, last_known_lat, last_known_lng,
                   contact_info, photos, embeddings, share_token,
                   epicenter_lat, epicenter_lng, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
                person_id, kwargs.get("name"), kwargs.get("age"),
                kwargs.get("gender"), kwargs.get("description"),
                kwargs.get("last_known_location"),
                kwargs.get("last_known_lat"), kwargs.get("last_known_lng"),
                kwargs.get("contact_info"), photos, embeddings,
                share_token,
                kwargs.get("last_known_lat"), kwargs.get("last_known_lng"),
                now, now
            )
        else:
            await self.execute(
                """INSERT INTO persons (id, name, age, gender, description,
                   last_known_location, last_known_lat, last_known_lng,
                   contact_info, photos, embeddings, share_token,
                   epicenter_lat, epicenter_lng, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
                person_id, kwargs.get("name"), kwargs.get("age"),
                kwargs.get("gender"), kwargs.get("description"),
                kwargs.get("last_known_location"),
                kwargs.get("last_known_lat"), kwargs.get("last_known_lng"),
                kwargs.get("contact_info"),
                json.dumps(photos), json.dumps(embeddings),
                share_token,
                kwargs.get("last_known_lat"), kwargs.get("last_known_lng"),
                now, now
            )

        return person_id

    async def get_person(self, person_id: str) -> Optional[dict]:
        """Get a person profile by ID."""
        row = await self.fetchone(
            "SELECT * FROM persons WHERE id = $1", person_id
        )
        if row and not self._is_postgres:
            row["photos"] = json.loads(row.get("photos", "[]"))
        return row

    async def get_person_by_token(self, token: str) -> Optional[dict]:
        """Get a person by their share token."""
        return await self.fetchone(
            "SELECT * FROM persons WHERE share_token = $1", token
        )

    async def update_person(self, person_id: str, **kwargs):
        """Update person fields."""
        now = datetime.now(timezone.utc).isoformat()
        sets = ["updated_at = $1"]
        values = [now]
        idx = 2
        for key, value in kwargs.items():
            sets.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1
        values.append(person_id)
        query = f"UPDATE persons SET {', '.join(sets)} WHERE id = ${idx}"
        await self.execute(query, *values)

    # ── Match CRUD ──

    async def create_match(self, **kwargs) -> str:
        """Create a new match record. Returns the match ID."""
        match_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await self.execute(
            """INSERT INTO matches (id, person_id, source, url, image_url,
               image_path, similarity, confidence_label, location, lat, lng,
               raw_text, metadata, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
            match_id, kwargs["person_id"], kwargs["source"],
            kwargs.get("url"), kwargs.get("image_url"),
            kwargs.get("image_path"), kwargs["similarity"],
            kwargs["confidence_label"], kwargs.get("location"),
            kwargs.get("lat"), kwargs.get("lng"),
            kwargs.get("raw_text"),
            json.dumps(kwargs.get("metadata", {})),
            now
        )
        return match_id

    async def get_matches(self, person_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get matches for a person, ordered by most recent."""
        return await self.fetchall(
            """SELECT * FROM matches WHERE person_id = $1
               ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
            person_id, limit, offset
        )

    async def get_match_count(self, person_id: str) -> int:
        """Get total match count for a person."""
        result = await self.fetchval(
            "SELECT COUNT(*) FROM matches WHERE person_id = $1", person_id
        )
        return result or 0

    # ── Location CRUD ──

    async def create_location(self, **kwargs) -> str:
        """Create a new location record."""
        loc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await self.execute(
            """INSERT INTO locations (id, person_id, match_id, location, lat, lng,
               source, confidence, timestamp, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            loc_id, kwargs["person_id"], kwargs.get("match_id"),
            kwargs["location"], kwargs["lat"], kwargs["lng"],
            kwargs.get("source"), kwargs.get("confidence"),
            kwargs.get("timestamp", now), now
        )
        return loc_id

    async def get_timeline(self, person_id: str) -> list[dict]:
        """Get location timeline for a person."""
        return await self.fetchall(
            """SELECT * FROM locations WHERE person_id = $1
               ORDER BY timestamp ASC""",
            person_id
        )

    # ── Alert Logging ──

    async def log_alert(self, **kwargs) -> str:
        """Log an alert that was sent."""
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await self.execute(
            """INSERT INTO alerts_sent (id, person_id, match_id, channel,
               recipient, payload, status, error_message, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            alert_id, kwargs["person_id"], kwargs.get("match_id"),
            kwargs["channel"], kwargs.get("recipient"),
            json.dumps(kwargs.get("payload", {})),
            kwargs.get("status", "sent"),
            kwargs.get("error_message"), now
        )
        return alert_id

    # ── Crowdsource ──

    async def create_sighting(self, **kwargs) -> str:
        """Create a crowdsource sighting record."""
        sighting_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await self.execute(
            """INSERT INTO crowdsource_sightings (id, person_id, share_token,
               image_path, location, lat, lng, description, similarity,
               confidence_label, status, submitter_ip, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
            sighting_id, kwargs["person_id"], kwargs["share_token"],
            kwargs.get("image_path"), kwargs.get("location"),
            kwargs.get("lat"), kwargs.get("lng"),
            kwargs.get("description"), kwargs.get("similarity"),
            kwargs.get("confidence_label"),
            kwargs.get("status", "pending"),
            kwargs.get("submitter_ip"), now
        )
        return sighting_id

    # ── Cleanup ──

    async def disconnect(self):
        """Close database connections."""
        if self._is_postgres and self.pool:
            await self.pool.close()
        if self._sqlite_conn:
            self._sqlite_conn.close()
        self._initialized = False


# Singleton instance
db = Database()
