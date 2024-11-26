
-- Create ENUMs
CREATE TYPE event_type_enum AS ENUM (
    'birthday', 'personal', 'professional', 'national', 
    'religious', 'cultural', 'reminder', 'other'
);

CREATE TYPE recurrence_type_enum AS ENUM (
    'none', 'yearly', 'monthly', 'weekly', 'custom'
);

-- Create base tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,
    password VARCHAR,
    telegram_id BIGINT UNIQUE NOT NULL,
    refresh_token VARCHAR
);

CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    date_of_birth TIMESTAMP,
    interests VARCHAR[],
    contacts JSONB,
    user_id INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE giftlists (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR UNIQUE NOT NULL,
    owner_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE gifts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    price FLOAT NOT NULL,
    owner_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE userlists (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR NOT NULL,
    description VARCHAR,
    user_id INTEGER NOT NULL,
    gift_list_id INTEGER,
    added_user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (gift_list_id) REFERENCES giftlists(id) ON DELETE CASCADE,
    FOREIGN KEY (added_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    gift_id INTEGER NOT NULL,
    telegram_payment_charge_id VARCHAR,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (gift_id) REFERENCES gifts(id)
);

CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    event_type event_type_enum NOT NULL DEFAULT 'birthday',
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    recurrence_type recurrence_type_enum NOT NULL DEFAULT 'none',
    recurrence_rule JSONB,
    owner_id INTEGER NOT NULL,
    tags VARCHAR[],
    reminder_days INTEGER[],
    budget FLOAT,
    currency VARCHAR(3),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    contact_telegram_id BIGINT NOT NULL,
    username VARCHAR,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, contact_telegram_id)
);

-- Create association tables
CREATE TABLE gift_list_gift (
    giftlist_id INTEGER,
    gift_id INTEGER,
    PRIMARY KEY (giftlist_id, gift_id),
    FOREIGN KEY (giftlist_id) REFERENCES giftlists(id) ON DELETE CASCADE,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
);

CREATE TABLE calendar_participants (
    calendar_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (calendar_id, user_id),
    FOREIGN KEY (calendar_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE calendar_gift (
    calendar_id INTEGER,
    gift_id INTEGER,
    PRIMARY KEY (calendar_id, gift_id),
    FOREIGN KEY (calendar_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_giftlists_updated_at BEFORE UPDATE ON giftlists FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gifts_updated_at BEFORE UPDATE ON gifts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_userlists_updated_at BEFORE UPDATE ON userlists FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON calendar_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
