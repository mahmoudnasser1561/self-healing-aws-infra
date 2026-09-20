import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import TodoForm from "./TodoForm";

test("the add button is disabled until there is a title", async () => {
  render(<TodoForm onAdd={vi.fn()} />);
  const button = screen.getByRole("button", { name: "Add" });

  expect(button).toBeDisabled();

  await userEvent.type(screen.getByLabelText("New todo"), "   ");
  expect(button).toBeDisabled();

  await userEvent.type(screen.getByLabelText("New todo"), "milk");
  expect(button).toBeEnabled();
});

test("submitting sends the trimmed title and clears the field on success", async () => {
  const onAdd = vi.fn().mockResolvedValue(true);
  render(<TodoForm onAdd={onAdd} />);

  await userEvent.type(screen.getByLabelText("New todo"), "  Buy milk  ");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  expect(onAdd).toHaveBeenCalledWith("Buy milk");
  expect(screen.getByLabelText("New todo")).toHaveValue("");
});

test("submitting with the Enter key works", async () => {
  const onAdd = vi.fn().mockResolvedValue(true);
  render(<TodoForm onAdd={onAdd} />);

  await userEvent.type(screen.getByLabelText("New todo"), "Ship it{Enter}");

  expect(onAdd).toHaveBeenCalledWith("Ship it");
});

test("the text is kept when adding fails", async () => {
  render(<TodoForm onAdd={vi.fn().mockResolvedValue(false)} />);

  await userEvent.type(screen.getByLabelText("New todo"), "Keep me");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  expect(screen.getByLabelText("New todo")).toHaveValue("Keep me");
});

test("the title is limited to the backend's 200 characters", () => {
  render(<TodoForm onAdd={vi.fn()} />);

  expect(screen.getByLabelText("New todo")).toHaveAttribute("maxlength", "200");
});
