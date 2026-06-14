import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("../src/api/members", () => ({ searchPlaces: vi.fn() }));

import { searchPlaces } from "../src/api/members";
import { TripForm } from "../src/components/TripForm";

const LISBON = { city: "Lisbon", country_code: "PT", country_name: "Portugal", lat: 38.72, lng: -9.14 };

describe("TripForm", () => {
  it("disables the city field until a country is chosen, then scopes search to it", async () => {
    (searchPlaces as ReturnType<typeof vi.fn>).mockResolvedValue([LISBON]);
    render(<TripForm onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("City")).toBeDisabled();
    await userEvent.selectOptions(screen.getByLabelText("Country"), "PT");
    expect(screen.getByLabelText("City")).toBeEnabled();

    await userEvent.type(screen.getByLabelText("City"), "Lis");
    await screen.findByText("Lisbon, Portugal");
    expect(searchPlaces).toHaveBeenCalledWith("Lis", "PT");
  });

  it("submits a valid trip selected from the country-scoped search", async () => {
    (searchPlaces as ReturnType<typeof vi.fn>).mockResolvedValue([LISBON]);
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TripForm onSubmit={onSubmit} />);

    await userEvent.selectOptions(screen.getByLabelText("Country"), "PT");
    await userEvent.type(screen.getByLabelText("City"), "Lis");
    fireEvent.click(await screen.findByText("Lisbon, Portugal"));
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-01" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-10" } });
    await userEvent.click(screen.getByRole("button", { name: /add trip/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        place: LISBON,
        start_date: "2026-07-01",
        end_date: "2026-07-10",
        note: null,
      }),
    );
  });

  it("shows an error and does not submit when dates are inverted", async () => {
    (searchPlaces as ReturnType<typeof vi.fn>).mockResolvedValue([LISBON]);
    const onSubmit = vi.fn();
    render(<TripForm onSubmit={onSubmit} />);

    await userEvent.selectOptions(screen.getByLabelText("Country"), "PT");
    await userEvent.type(screen.getByLabelText("City"), "Lis");
    fireEvent.click(await screen.findByText("Lisbon, Portugal"));
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-10" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-01" } });
    await userEvent.click(screen.getByRole("button", { name: /add trip/i }));

    expect(await screen.findByText(/on or after start date/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
