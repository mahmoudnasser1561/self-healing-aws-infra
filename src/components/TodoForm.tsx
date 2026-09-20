import { useState, type FormEvent } from "react";

export const MAX_TITLE_LENGTH = 200;

interface Props {
  onAdd: (title: string) => Promise<boolean>;
}

export default function TodoForm({ onAdd }: Props) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const trimmed = title.trim();

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!trimmed || busy) return;
    setBusy(true);
    const added = await onAdd(trimmed);
    setBusy(false);
    if (added) setTitle("");
  }

  return (
    <form className="todo-form" onSubmit={submit}>
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={MAX_TITLE_LENGTH}
        placeholder="What needs doing?"
        aria-label="New todo"
      />
      <button type="submit" disabled={!trimmed || busy}>
        Add
      </button>
    </form>
  );
}
