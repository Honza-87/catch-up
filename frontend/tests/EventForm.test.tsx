import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EventForm } from "../src/components/EventForm";
import type { Place } from "../src/types";

const BERLIN: Place = { city: "Berlin", country_code: "DE", country_name: "Germany", lat: 52.52, lng: 13.4 };

describe("EventForm", () => {
  it("submits a valid event hosted at home", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EventForm homePlace={BERLIN} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Title"), "My birthday");
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-01" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-01" } });
    await userEvent.click(screen.getByRole("button", { name: /add event/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        title: "My birthday",
        start_date: "2026-07-01",
        end_date: "2026-07-01",
        note: null,
      }),
    );
  });

  it("disables submit without a home location", () => {
    render(<EventForm homePlace={null} onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /add event/i })).toBeDisabled();
    expect(screen.getByText(/set your home location/i)).toBeInTheDocument();
  });

  it("rejects inverted dates", async () => {
    const onSubmit = vi.fn();
    render(<EventForm homePlace={BERLIN} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Title"), "Party");
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-07-10" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-07-01" } });
    await userEvent.click(screen.getByRole("button", { name: /add event/i }));

    expect(await screen.findByText(/on or after start date/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
