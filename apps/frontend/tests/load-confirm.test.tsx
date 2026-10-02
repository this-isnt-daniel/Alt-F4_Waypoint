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

    expect(screen.getByText("Load confirmation")).toBeInTheDocument();
    
    // Check initial state
    const departBtn = screen.getByRole("button", { name: /confirm & depart/i });
    expect(departBtn).toBeDisabled();

    // Tap "Confirm all match"
    const confirmAllBtn = screen.getByRole("button", { name: /confirm all match/i });
    fireEvent.click(confirmAllBtn);

    // Modal opens
    const modalConfirm = screen.getByRole("button", { name: /^confirm$/i });
    fireEvent.click(modalConfirm);

    // Now all 7 stops are confirmed and OUT058 is flagged, so canDepart is true!
    expect(departBtn).not.toBeDisabled();

    // Click depart
    fireEvent.click(departBtn);
  });
});
