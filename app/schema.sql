CREATE TABLE IF NOT EXISTS todos (
    id bigserial PRIMARY KEY,
    title text NOT NULL
        CHECK (char_length(btrim(title)) BETWEEN 1 AND 200),
    notes text NOT NULL DEFAULT ''
        CHECK (char_length(notes) <= 2000),
    status text NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'done')),
    priority smallint NOT NULL DEFAULT 2
        CHECK (priority BETWEEN 1 AND 3),
    due_date date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    CONSTRAINT todos_completed_iff_done
        CHECK ((status = 'done') = (completed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS todos_status_due_idx ON todos (status, due_date);
