import { useCallback, useEffect, useState } from "react";
import { createTodo, deleteTodo, listTodos } from "../api/todos";
import type { Todo } from "../types";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong";
}

export function useTodos() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listTodos()
      .then((items) => {
        if (!cancelled) setTodos(items);
      })
      .catch((failure) => {
        if (!cancelled) setError(messageOf(failure));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const add = useCallback(async (title: string) => {
    setError(null);
    try {
      const todo = await createTodo(title);
      setTodos((current) => [todo, ...current]);
      return true;
    } catch (failure) {
      setError(messageOf(failure));
      return false;
    }
  }, []);

  const remove = useCallback(async (id: number) => {
    setError(null);
    try {
      await deleteTodo(id);
      setTodos((current) => current.filter((todo) => todo.id !== id));
    } catch (failure) {
      setError(messageOf(failure));
    }
  }, []);

  return { todos, loading, error, add, remove };
}
