-- =============================================
-- ThirdEye — PostgreSQL Database Schema
-- =============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Persons Table ──
-- Stores missing person profiles and their face embeddings
CREATE TABLE IF NOT EXISTS persons (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255),
    age             INTEGER,
    gender          VARCHAR(50),
    description     TEXT,
    last_known_location TEXT,
    last_known_lat  DOUBLE PRECISION,
    last_known_lng  DOUBLE PRECISION,
    contact_info    TEXT,
    photos          TEXT[],               -- Array of photo file paths
    embeddings      BYTEA[],              -- Array of 512D face embedding blobs
    status          VARCHAR(50) DEFAULT 'active',  -- active, found, closed
    current_radius  DOUBLE PRECISION DEFAULT 1.0,  -- Current search radius in miles
    epicenter_lat   DOUBLE PRECISION,
    epicenter_lng   DOUBLE PRECISION,
    share_token     UUID DEFAULT uuid_generate_v4(),  -- For crowdsource link
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scan_at    TIMESTAMP WITH TIME ZONE
);

-- ── Matches Table ──
-- Every potential match found across all sources
CREATE TABLE IF NOT EXISTS matches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id       UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    source          VARCHAR(100) NOT NULL,   -- instagram, twitter, nyc_dot_cam, etc.
    url             TEXT,                     -- Direct link to source
    image_url       TEXT,                     -- URL of matched image
    image_path      TEXT,                     -- Local cached image path
    similarity      DOUBLE PRECISION NOT NULL,
    confidence_label VARCHAR(50) NOT NULL,    -- DEFINITE, HIGH, PROBABLE, POSSIBLE, WEAK
    location        TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    raw_text        TEXT,                     -- Post caption, article text, etc.
    metadata        JSONB DEFAULT '{}',       -- Extra source-specific data
    reviewed        BOOLEAN DEFAULT FALSE,
    confirmed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Locations Table ──
-- Deduplicated location timeline per person
CREATE TABLE IF NOT EXISTS locations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id       UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    match_id        UUID REFERENCES matches(id) ON DELETE SET NULL,
    location        TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lng             DOUBLE PRECISION NOT NULL,
    source          VARCHAR(100),
    confidence      DOUBLE PRECISION,
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Alerts Sent Table ──
-- Log of all alert notifications dispatched
CREATE TABLE IF NOT EXISTS alerts_sent (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id       UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    match_id        UUID REFERENCES matches(id) ON DELETE SET NULL,
    channel         VARCHAR(50) NOT NULL,    -- email, sms, push, websocket
    recipient       TEXT,
    payload         JSONB,
    status          VARCHAR(50) DEFAULT 'sent',  -- sent, failed, pending
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Crowdsource Sightings Table ──
-- Volunteer-submitted sighting reports
CREATE TABLE IF NOT EXISTS crowdsource_sightings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id       UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    share_token     UUID NOT NULL,
    image_path      TEXT,
    location        TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    description     TEXT,
    similarity      DOUBLE PRECISION,
    confidence_label VARCHAR(50),
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, accepted, rejected
    submitter_ip    VARCHAR(45),                     -- For rate limiting
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Cameras Table ──
-- Registry of active camera sources per radius
CREATE TABLE IF NOT EXISTS cameras (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          VARCHAR(100) NOT NULL,   -- nyc_dot, 511ny, shodan, earthcam
    name            TEXT,
    url             TEXT NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lng             DOUBLE PRECISION NOT NULL,
    city            VARCHAR(255),
    state           VARCHAR(100),
    active          BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_matches_person_id ON matches(person_id);
CREATE INDEX IF NOT EXISTS idx_matches_similarity ON matches(similarity DESC);
CREATE INDEX IF NOT EXISTS idx_matches_created_at ON matches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_source ON matches(source);
CREATE INDEX IF NOT EXISTS idx_locations_person_id ON locations(person_id);
CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_person_id ON alerts_sent(person_id);
CREATE INDEX IF NOT EXISTS idx_cameras_active ON cameras(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_cameras_location ON cameras(lat, lng);
CREATE INDEX IF NOT EXISTS idx_crowdsource_person_id ON crowdsource_sightings(person_id);
CREATE INDEX IF NOT EXISTS idx_crowdsource_status ON crowdsource_sightings(status);
CREATE INDEX IF NOT EXISTS idx_persons_status ON persons(status);
CREATE INDEX IF NOT EXISTS idx_persons_share_token ON persons(share_token);
