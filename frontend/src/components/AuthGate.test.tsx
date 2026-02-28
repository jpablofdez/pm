import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";
import { initialData } from "@/lib/kanban";

const mockResponse = (status: number, body: unknown) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as Response;

describe("AuthGate", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows login form when unauthenticated", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      mockResponse(401, { detail: "Not authenticated." })
    );

    render(<AuthGate />);

    await screen.findByRole("heading", { name: "Sign in to continue" });
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/me", {
      credentials: "include",
    });
  });

  it("logs in and shows the board", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(mockResponse(401, { detail: "Not authenticated." }))
      .mockResolvedValueOnce(
        mockResponse(200, { authenticated: true, username: "user" })
      )
      .mockResolvedValueOnce(mockResponse(200, initialData));

    render(<AuthGate />);
    await screen.findByRole("heading", { name: "Sign in to continue" });

    await userEvent.clear(screen.getByLabelText("Username"));
    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await screen.findByRole("heading", { name: "Kanban Studio" });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });
});
