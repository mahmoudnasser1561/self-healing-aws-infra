import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ApiError, createTodo, deleteTodo, getHealth, listTodos } from "./todos";

const TODO = { id: 7, title: "Buy milk", created_at: "2026-01-02T03:04:05+00:00" };

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("listTodos returns the todos array from the response", async () => {
  fetchMock.mockResolvedValue(json({ todos: [TODO] }));

  await expect(listTodos()).resolves.toEqual([TODO]);
  expect(fetchMock).toHaveBeenCalledWith("/api/todos", undefined);
});

test("createTodo posts the title as JSON and returns the created todo", async () => {
  fetchMock.mockResolvedValue(json(TODO, 201));

  await expect(createTodo("Buy milk")).resolves.toEqual(TODO);

  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe("/api/todos");
  expect(init.method).toBe("POST");
  expect(init.headers).toEqual({ "Content-Type": "application/json" });
  expect(JSON.parse(init.body)).toEqual({ title: "Buy milk" });
});

test("deleteTodo sends DELETE and resolves on an empty 204 response", async () => {
  fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

  await expect(deleteTodo(7)).resolves.toBeUndefined();
  expect(fetchMock).toHaveBeenCalledWith("/api/todos/7", { method: "DELETE" });
});

test("getHealth returns the health payload", async () => {
  const health = { status: "ok", version: "abc123", db_time: "now", todos: 3 };
  fetchMock.mockResolvedValue(json(health));

  await expect(getHealth()).resolves.toEqual(health);
});

test("an error response surfaces the API's message and status", async () => {
  fetchMock.mockResolvedValue(
    json({ error: "title must be 1 to 200 characters" }, 400),
  );

  const failure = createTodo("").catch((error) => error);

  await expect(failure).resolves.toBeInstanceOf(ApiError);
  await expect(failure).resolves.toMatchObject({
    message: "title must be 1 to 200 characters",
    status: 400,
  });
});

test("an error response without a JSON body gets a generic message", async () => {
  fetchMock.mockResolvedValue(new Response("<html>bad gateway</html>", { status: 502 }));

  await expect(listTodos()).rejects.toMatchObject({
    message: "Request failed with status 502",
    status: 502,
  });
});

test("a network failure propagates as-is", async () => {
  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

  await expect(listTodos()).rejects.toThrow("Failed to fetch");
});
