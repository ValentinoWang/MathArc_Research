-- MathArc administrator/access persistence baseline.
-- This migration is intentionally additive and safe to run more than once.

CREATE TABLE IF NOT EXISTS admin_users (
    admin_user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'access_admin',
    password_hash TEXT,
    mfa_secret_ref TEXT,
    disabled_at BIGINT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    subject TEXT,
    auth_method TEXT,
    CONSTRAINT admin_users_email_lower CHECK (email = lower(email)),
    CONSTRAINT admin_users_role_check CHECK (role IN ('access_admin', 'access_reviewer', 'security_admin')),
    CONSTRAINT admin_users_timestamps_check CHECK (updated_at >= created_at)
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    admin_session_id TEXT PRIMARY KEY,
    admin_user_id TEXT REFERENCES admin_users(admin_user_id) ON DELETE RESTRICT,
    session_token_hash_sha256 TEXT NOT NULL UNIQUE,
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    last_activity_at BIGINT NOT NULL,
    revoked_at BIGINT,
    device_fingerprint_sha256 TEXT,
    source_ip_hash_sha256 TEXT,
    session_id TEXT UNIQUE,
    subject TEXT,
    email TEXT,
    role TEXT,
    auth_method TEXT,
    token_hash_sha256 TEXT UNIQUE,
    CONSTRAINT admin_sessions_token_hash_check CHECK (session_token_hash_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT admin_sessions_time_check CHECK (expires_at > created_at AND last_activity_at >= created_at),
    CONSTRAINT admin_sessions_hash_lengths_check CHECK (
        (device_fingerprint_sha256 IS NULL OR device_fingerprint_sha256 ~ '^[0-9a-f]{64}$')
        AND (source_ip_hash_sha256 IS NULL OR source_ip_hash_sha256 ~ '^[0-9a-f]{64}$')
    )
);

CREATE TABLE IF NOT EXISTS applications (
    application_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'PENDING',
    email TEXT NOT NULL,
    institution TEXT NOT NULL,
    research_role TEXT NOT NULL,
    research_direction TEXT NOT NULL,
    purpose TEXT NOT NULL,
    submitted_at BIGINT NOT NULL,
    created_at BIGINT NOT NULL DEFAULT 0,
    updated_at BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT applications_status_check CHECK (status = 'PENDING'),
    CONSTRAINT applications_email_lower CHECK (email = lower(email))
);

CREATE TABLE IF NOT EXISTS invitations (
    invitation_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    topic_scopes JSONB NOT NULL,
    code_hash_sha256 TEXT NOT NULL UNIQUE,
    issued_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    redeemed_at BIGINT,
    revoked_at BIGINT,
    issued_by TEXT,
    CONSTRAINT invitations_email_lower CHECK (email = lower(email)),
    CONSTRAINT invitations_code_hash_check CHECK (code_hash_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT invitations_time_check CHECK (expires_at > issued_at),
    CONSTRAINT invitations_terminal_state_check CHECK (NOT (redeemed_at IS NOT NULL AND revoked_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS access_sessions (
    access_session_id TEXT PRIMARY KEY,
    invitation_id TEXT NOT NULL UNIQUE REFERENCES invitations(invitation_id) ON DELETE RESTRICT,
    email TEXT NOT NULL,
    topic_scopes JSONB NOT NULL,
    token_hash_sha256 TEXT NOT NULL UNIQUE,
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    logged_out_at BIGINT,
    CONSTRAINT access_sessions_email_lower CHECK (email = lower(email)),
    CONSTRAINT access_sessions_token_hash_check CHECK (token_hash_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT access_sessions_time_check CHECK (expires_at > created_at),
    CONSTRAINT access_sessions_logout_check CHECK (logged_out_at IS NULL OR logged_out_at >= created_at)
);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_event_id TEXT PRIMARY KEY,
    chain_sequence BIGINT NOT NULL UNIQUE,
    occurred_at BIGINT NOT NULL,
    actor_admin_user_id TEXT REFERENCES admin_users(admin_user_id) ON DELETE RESTRICT,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT,
    result TEXT NOT NULL,
    reason TEXT,
    request_source TEXT,
    event_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    previous_event_hash_sha256 TEXT,
    event_hash_sha256 TEXT NOT NULL UNIQUE,
    sequence BIGINT UNIQUE,
    event_id TEXT UNIQUE,
    event_type TEXT,
    actor_subject TEXT,
    payload JSONB,
    idempotency_key TEXT UNIQUE,
    previous_hash TEXT,
    event_hash TEXT UNIQUE,
    created_at BIGINT,
    CONSTRAINT audit_events_result_check CHECK (result IN ('success', 'failure', 'rejected')),
    CONSTRAINT audit_events_hash_check CHECK (
        event_hash_sha256 ~ '^[0-9a-f]{64}$'
        AND (previous_event_hash_sha256 IS NULL OR previous_event_hash_sha256 ~ '^[0-9a-f]{64}$')
    )
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    idempotency_record_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash_sha256 TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_payload JSONB NOT NULL,
    created_at BIGINT NOT NULL,
    expires_at BIGINT,
    UNIQUE (scope, idempotency_key),
    CONSTRAINT idempotency_request_hash_check CHECK (request_hash_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT idempotency_response_status_check CHECK (response_status BETWEEN 100 AND 599),
    CONSTRAINT idempotency_time_check CHECK (expires_at IS NULL OR expires_at >= created_at)
);

CREATE INDEX IF NOT EXISTS admin_sessions_user_idx ON admin_sessions (admin_user_id, expires_at);
CREATE INDEX IF NOT EXISTS admin_sessions_active_idx ON admin_sessions (expires_at) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS applications_status_submitted_idx ON applications (status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS applications_email_idx ON applications (email);
CREATE INDEX IF NOT EXISTS invitations_email_status_idx ON invitations (email, expires_at, revoked_at, redeemed_at);
CREATE INDEX IF NOT EXISTS access_sessions_email_idx ON access_sessions (email);
CREATE INDEX IF NOT EXISTS access_sessions_active_idx ON access_sessions (expires_at) WHERE logged_out_at IS NULL;
CREATE INDEX IF NOT EXISTS audit_events_time_idx ON audit_events (occurred_at DESC, chain_sequence DESC);
CREATE INDEX IF NOT EXISTS audit_events_actor_idx ON audit_events (actor_admin_user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_object_idx ON audit_events (object_type, object_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idempotency_expiry_idx ON idempotency_records (expires_at);
