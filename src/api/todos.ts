import type { Health, Todo } from "../types";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message =
      typeof body?.error === "string"
        ? body.error
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function listTodos(): Promise<Todo[]> {
  const body = await request<{ todos: Todo[] }>("/api/todos");
  return body.todos;
}

export function createTodo(title: string): Promise<Todo> {
  return request<Todo>("/api/todos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function deleteTodo(id: number): Promise<void> {
  return request<void>(`/api/todos/${id}`, { method: "DELETE" });
}

export function getHealth(): Promise<Health> {
  return request<Health>("/api/health");
}
