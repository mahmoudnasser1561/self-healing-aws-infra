CREATE TABLE IF NOT EXISTS todos (
    id bigserial PRIMARY KEY,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now()
);
