import { formatDate } from "../format";
import type { Todo } from "../types";

interface Props {
  todos: Todo[];
  onDelete: (id: number) => void;
}

export default function TodoList({ todos, onDelete }: Props) {
  if (todos.length === 0) {
    return <p className="empty">No todos yet.</p>;
  }

  return (
    <ul className="todo-list">
      {todos.map((todo) => (
        <li key={todo.id}>
          <div>
            <span className="title">{todo.title}</span>
            <time dateTime={todo.created_at}>{formatDate(todo.created_at)}</time>
          </div>
          <button
            type="button"
            className="delete"
            aria-label={`Delete ${todo.title}`}
            onClick={() => onDelete(todo.id)}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
