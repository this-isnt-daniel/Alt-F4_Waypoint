import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "@/theme/ThemeProvider";
import { ThemeToggle } from "@/theme/ThemeToggle";

describe("Theme System", () => {
  it("defaults to dark mode and toggles to light mode", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    const button = screen.getByRole("button", { name: /switch to light mode/i });
    expect(button).toBeInTheDocument();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    fireEvent.click(button);

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(screen.getByRole("button", { name: /switch to dark mode/i })).toBeInTheDocument();
  });
});
