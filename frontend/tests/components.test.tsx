import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../src/api/auth", () => ({ requestLink: vi.fn().mockResolvedValue({ status: "ok" }) }));
vi.mock("../src/api/members", () => ({
  fetchMembers: vi.fn().mockResolvedValue([
    {
      id: "1",
      display_name: "Eva",
      photo_url: null,
      home_place: null,
      job_title: "Dev",
      company: "Acme",
      whatsapp_e164: null,
    },
  ]),
}));

import { requestLink } from "../src/api/auth";
import { WhatsAppButton } from "../src/components/WhatsAppButton";
import { Directory } from "../src/pages/Directory";
import { Login } from "../src/pages/Login";

function withProviders(ui: React.ReactNode) {
  const client = new QueryClient();
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("WhatsAppButton", () => {
  it("links to wa.me with digits only", () => {
    render(<WhatsAppButton e164="+420777123456" />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "https://wa.me/420777123456");
  });

  it("renders nothing without a number", () => {
    const { container } = render(<WhatsAppButton e164={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Login", () => {
  it("requests a link and shows confirmation", async () => {
    render(<Login />);
    await userEvent.type(screen.getByLabelText(/email/i), "a@example.com");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(requestLink).toHaveBeenCalledWith("a@example.com");
    expect(await screen.findByText(/check your inbox/i)).toBeInTheDocument();
  });
});

describe("Directory", () => {
  it("renders joined members", async () => {
    render(withProviders(<Directory />));
    expect(await screen.findByText("Eva")).toBeInTheDocument();
  });
});
