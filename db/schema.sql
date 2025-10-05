-- Optional: CREATE DATABASE "LaganaCoach";

CREATE TYPE user_role AS ENUM ('admin', 'coach');
CREATE TYPE skill_level AS ENUM ('beginner', 'intermediate', 'advanced');
CREATE TYPE lesson_type AS ENUM ('club', 'private');
CREATE TYPE lesson_status AS ENUM ('draft', 'set', 'executed', 'invoiced');
CREATE TYPE lesson_payment_status AS ENUM ('open', 'paid');
CREATE TYPE stroke_code AS ENUM ('forehand', 'backhand', 'volley', 'smash', 'serve', 'lob', 'drop_shot', 'bandeja', 'vibora', 'chiquita');
CREATE TYPE invoice_status AS ENUM ('draft', 'issued', 'paid', 'void');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_users_email ON users(email);

CREATE TABLE coaches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postcode VARCHAR(20),
    country VARCHAR(100),
    bank_name VARCHAR(150),
    account_holder_name VARCHAR(150),
    sort_code VARCHAR(20),
    account_number VARCHAR(20),
    iban VARCHAR(34),
    swift_bic VARCHAR(11),
    hourly_rate NUMERIC(10,2),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE clubs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postcode VARCHAR(20),
    country VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    birth_date DATE,
    skill_level skill_level NOT NULL DEFAULT 'beginner',
    notes TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE strokes (
    id SERIAL PRIMARY KEY,
    code stroke_code UNIQUE NOT NULL,
    label VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES coaches(id) ON DELETE CASCADE,
    club_id INTEGER REFERENCES clubs(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    type lesson_type NOT NULL,
    status lesson_status NOT NULL DEFAULT 'draft',
    payment_status lesson_payment_status NOT NULL DEFAULT 'open',
    club_reimbursement_amount NUMERIC(10,2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_lessons_duration_positive CHECK (duration_minutes > 0),
    CONSTRAINT ck_lessons_reimbursement_positive CHECK (club_reimbursement_amount IS NULL OR club_reimbursement_amount >= 0)
);
CREATE INDEX ix_lessons_coach_date ON lessons(coach_id, date);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES coaches(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status invoice_status NOT NULL DEFAULT 'draft',
    total_gross NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_club_reimbursement NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_net NUMERIC(12,2) NOT NULL DEFAULT 0,
    issued_at TIMESTAMPTZ,
    due_date DATE,
    pdf_url VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    metadata JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE player_coach (
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    coach_id INTEGER NOT NULL REFERENCES coaches(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, coach_id)
);
CREATE INDEX ix_player_coach_player_id ON player_coach(player_id);
CREATE INDEX ix_player_coach_coach_id ON player_coach(coach_id);

CREATE TABLE lesson_players (
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (lesson_id, player_id)
);
CREATE INDEX ix_lesson_players_lesson_id ON lesson_players(lesson_id);
CREATE INDEX ix_lesson_players_player_id ON lesson_players(player_id);

CREATE TABLE lesson_strokes (
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    stroke_id INTEGER NOT NULL REFERENCES strokes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (lesson_id, stroke_id)
);
CREATE INDEX ix_lesson_strokes_lesson_id ON lesson_strokes(lesson_id);
CREATE INDEX ix_lesson_strokes_stroke_id ON lesson_strokes(stroke_id);
