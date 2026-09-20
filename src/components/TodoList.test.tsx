import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import type { Todo } from "../types";
import TodoList from "./TodoList";

const TODOS: Todo[] = [
  { id: 2, title: "Write the ADR", created_at: "2026-01-02T03:04:05+00:00" },
  { id: 1, title: "Buy milk", created_at: "2026-01-01T03:04:05+00:00" },
];

test("shows an empty state when there are no todos", () => {
  render(<TodoList todos={[]} onDelete={vi.fn()} />);

  expect(screen.getByText("No todos yet.")).toBeInTheDocument();
});

test("renders every todo with its title, in the order given", () => {
  render(<TodoList todos={TODOS} onDelete={vi.fn()} />);

  const items = screen.getAllByRole("listitem");
  expect(items).toHaveLength(2);
  expect(items[0]).toHaveTextContent("Write the ADR");
  expect(items[1]).toHaveTextContent("Buy milk");
});

test("clicking delete reports the id of that todo", async () => {
  const onDelete = vi.fn();
  render(<TodoList todos={TODOS} onDelete={onDelete} />);

  await userEvent.click(screen.getByRole("button", { name: "Delete Buy milk" }));

  expect(onDelete).toHaveBeenCalledTimes(1);
  expect(onDelete).toHaveBeenCalledWith(1);
});
