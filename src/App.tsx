import ApiStatus from "./components/ApiStatus";
import TodoForm from "./components/TodoForm";
import TodoList from "./components/TodoList";
import { useTodos } from "./hooks/useTodos";
import "./App.css";

export default function App() {
  const { todos, loading, error, add, remove } = useTodos();

  return (
    <main>
      <header>
        <h1>Todos</h1>
        <ApiStatus />
      </header>
      <TodoForm onAdd={add} />
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {loading ? (
        <p className="empty">Loading…</p>
      ) : (
        <TodoList todos={todos} onDelete={remove} />
      )}
    </main>
  );
}
