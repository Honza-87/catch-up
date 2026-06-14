import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("../src/api/members", () => ({ searchPlaces: vi.fn() }));

import { searchPlaces } from "../src/api/members";
import { TripForm } from "../src/components/TripForm";

const LISBON = { city: "Lisbon", country_code: "PT", country_name: "Portugal", lat: 38.72, lng: -9.14 };

describe("TripForm", () => {
  it("submits a valid trip selected from search", async () => {
    (searchPlaces as ReturnType<typeof vi.fn>).mockResolvedValue([LISBON]);
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TripForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByPlaceholderText(/search a city/i), "Lis");
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

    await userEvent.type(screen.getByPlaceholderText(/search a city/i), "Lis");
    fireEvent.click(await screen.findByText("Lisbon, Portugal"));
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-10" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-01" } });
    await userEvent.click(screen.getByRole("button", { name: /add trip/i }));

    expect(await screen.findByText(/on or after start date/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("saves via manual entry when the lookup returns no results (FR-007)", async () => {
    (searchPlaces as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TripForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole("button", { name: /add manually/i }));
    fireEvent.change(screen.getByLabelText("City"), { target: { value: "Narnia" } });
    fireEvent.change(screen.getByLabelText(/country code/i), { target: { value: "NA" } });
    fireEvent.change(screen.getByLabelText("Country name"), { target: { value: "Narnia Land" } });
    await userEvent.click(screen.getByRole("button", { name: /use this place/i }));
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-01" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-05" } });
    await userEvent.click(screen.getByRole("button", { name: /add trip/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        place: { city: "Narnia", country_code: "NA", country_name: "Narnia Land", lat: 0, lng: 0 },
        start_date: "2026-07-01",
        end_date: "2026-07-05",
        note: null,
      }),
    );
  });
});
