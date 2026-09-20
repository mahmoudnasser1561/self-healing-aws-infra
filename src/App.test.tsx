import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import App from "./App";
import type { Todo } from "./types";

const FIRST: Todo = { id: 1, title: "Buy milk", created_at: "2026-01-01T03:04:05+00:00" };
const SECOND: Todo = { id: 2, title: "Write the ADR", created_at: "2026-01-02T03:04:05+00:00" };

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

interface Api {
  todos: Todo[];
  failList?: boolean;
  failHealth?: boolean;
  failCreate?: string;
}

function stubApi(api: Api) {
  let nextId = 100;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    if (url === "/api/health") {
      return api.failHealth
        ? json({ error: "down" }, 503)
        : json({ status: "ok", version: "abcdef1234567", db_time: "now", todos: api.todos.length });
    }
    if (url === "/api/todos" && method === "GET") {
      return api.failList ? json({ error: "database unavailable" }, 500) : json({ todos: api.todos });
    }
    if (url === "/api/todos" && method === "POST") {
      if (api.failCreate) return json({ error: api.failCreate }, 400);
      const { title } = JSON.parse(String(init?.body));
      const todo = { id: nextId++, title, created_at: "2026-02-01T03:04:05+00:00" };
      api.todos = [todo, ...api.todos];
      return json(todo, 201);
    }
    if (method === "DELETE") {
      const id = Number(url.split("/").pop());
      api.todos = api.todos.filter((todo) => todo.id !== id);
      return new Response(null, { status: 204 });
    }
    return json({ error: "not found" }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("loads the todos and shows the running release", async () => {
  stubApi({ todos: [SECOND, FIRST] });
  render(<App />);

  expect(await screen.findByText("Write the ADR")).toBeInTheDocument();
  expect(screen.getByText("Buy milk")).toBeInTheDocument();
  expect(await screen.findByText(/API online · release abcdef1/)).toBeInTheDocument();
});

test("shows an empty state when the API has no todos", async () => {
  stubApi({ todos: [] });
  render(<App />);

  expect(await screen.findByText("No todos yet.")).toBeInTheDocument();
});

test("adding a todo posts it and shows it at the top", async () => {
  const fetchMock = stubApi({ todos: [FIRST] });
  render(<App />);
  await screen.findByText("Buy milk");

  await userEvent.type(screen.getByLabelText("New todo"), "Ship the frontend");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  const items = await screen.findAllByRole("listitem");
  expect(items[0]).toHaveTextContent("Ship the frontend");
  expect(items[1]).toHaveTextContent("Buy milk");
  expect(screen.getByLabelText("New todo")).toHaveValue("");
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toEqual({ title: "Ship the frontend" });
});

test("deleting a todo removes it from the list", async () => {
  stubApi({ todos: [SECOND, FIRST] });
  render(<App />);
  await screen.findByText("Buy milk");

  await userEvent.click(screen.getByRole("button", { name: "Delete Buy milk" }));

  await waitFor(() => expect(screen.queryByText("Buy milk")).not.toBeInTheDocument());
  expect(within(screen.getByRole("list")).getAllByRole("listitem")).toHaveLength(1);
});

test("shows the API's message and keeps the text when a create is rejected", async () => {
  stubApi({ todos: [], failCreate: "title must be 1 to 200 characters" });
  render(<App />);
  await screen.findByText("No todos yet.");

  await userEvent.type(screen.getByLabelText("New todo"), "x");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("title must be 1 to 200 characters");
  expect(screen.getByLabelText("New todo")).toHaveValue("x");
});

test("shows an error when the list cannot be loaded", async () => {
  stubApi({ todos: [], failList: true });
  render(<App />);

  expect(await screen.findByRole("alert")).toHaveTextContent("database unavailable");
});

test("says so when the API is unreachable", async () => {
  stubApi({ todos: [], failHealth: true });
  render(<App />);

  expect(await screen.findByText("API unreachable")).toBeInTheDocument();
});
