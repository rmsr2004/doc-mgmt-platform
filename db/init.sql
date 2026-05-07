CREATE TABLE
    users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_disabled BOOLEAN DEFAULT FALSE,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until TIMESTAMP DEFAULT NULL
    );

CREATE TABLE
    documents (
        id SERIAL PRIMARY KEY,
        owner_id INTEGER REFERENCES users (id),
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        uuid_filename TEXT NOT NULL,
        metadata TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    document_shares (
        id SERIAL PRIMARY KEY,
        document_id INTEGER REFERENCES documents (id),
        shared_with INTEGER REFERENCES users (id)
    );
    
-- ---------------------------------------------------------------------------
-- AUDIT LOG TABLE
--
-- Records every auditable event in the system:
--   • Authentication events (login, logout, failed login)
--   • Document access and sharing operations
--   • Administrative actions (enable/disable accounts, role changes)
--
-- Fields:
--   event_category  — 'auth' | 'document' | 'admin'
--   actor_id        — the user who performed the action (NULL for pre-auth failures)
--   actor_username  — snapshot of username at time of event (preserved if deleted)
--   target_user_id  — affected user (for admin events)
--   document_id     — affected document (for document events)
--   action          — e.g. 'login_success', 'login_failed', 'logout',
--                         'document_view', 'document_upload', 'document_download',
--                         'document_share', 'user_enabled', 'user_disabled'
--   outcome         — 'success' | 'failure'
--   source_ip       — remote IP address of the request
--   timestamp       — UTC timestamp of the event
-- ---------------------------------------------------------------------------
CREATE TABLE
    audit_log (
        id SERIAL PRIMARY KEY,
        event_category TEXT NOT NULL,
        actor_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
        actor_username TEXT,
        target_user_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
        document_id INTEGER REFERENCES documents (id) ON DELETE SET NULL,
        action TEXT NOT NULL,
        outcome TEXT NOT NULL DEFAULT 'success',
        source_ip TEXT,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

-- ---------------------------------------------------------------------------
-- IMPORTANT — VALIDATOR ACCOUNTS
--
-- The following user accounts are required for the automated validation
-- system used in the course. These accounts MUST always exist in the system.
--
-- The usernames and logical identities of these accounts must NOT be removed
-- or changed, as the validator depends on them to execute security tests.
--
-- The validator authenticates using the plaintext credentials defined below.
-- Therefore:
--
--  • These credentials must remain valid for authentication.
--  • The passwords themselves must not be changed.
--
-- You are free to improve the authentication system (e.g., password hashing,
-- stronger password policies, etc.). If you implement password hashing or
-- other changes to the login mechanism, ensure that the credentials below
-- still successfully authenticate.
--
-- In other words: the authentication implementation may change, but the
-- following username/password combinations must continue to work.
--
-- These accounts are used by the automated validator to test:
--   • authentication
--   • authorization
--   • document sharing
--   • access control
--   • administrative operations
--
-- Removing or altering these accounts will cause automated validation to fail.
-- ---------------------------------------------------------------------------
INSERT INTO
    users (username, password, is_disabled)
VALUES
    ('admin', 'L|fP1D%327mB', FALSE),
    ('alice', 'tth1mJj5?£58', FALSE),
    ('bob', 'De586:Iq6}?!', FALSE);