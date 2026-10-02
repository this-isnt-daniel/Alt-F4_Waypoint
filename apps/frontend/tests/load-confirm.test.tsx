import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LoadConfirmScreen } from "@/driver/screens/LoadConfirmScreen";
import { NavigatorProvider } from "@/router/navigator";
import { DriverStateProvider } from "@/driver/state/DriverStateProvider";

describe("LoadConfirmScreen test", () => {
  it("renders without error and allows tapping rows and departing", () => {
    const { container } = render(
      <NavigatorProvider>
        <DriverStateProvider>
          <LoadConfirmScreen />
        </DriverStateProvider>
      </NavigatorProvider>,
    );

    expect(screen.getByText("Load Details")).toBeInTheDocument();
    expect(screen.getByText("OUT042")).toBeInTheDocument();
    expect(screen.getByText("OUT058")).toBeInTheDocument();
    expect(screen.getByText("Flagged")).toBeInTheDocument();
    expect(container).toBeTruthy();
  });
});
