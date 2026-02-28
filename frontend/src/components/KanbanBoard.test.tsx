import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];
const mockResponse = (status: number, body: unknown) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as Response;

describe("KanbanBoard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders five columns", () => {
    render(<KanbanBoard syncEnabled={false} />);
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard syncEnabled={false} />);
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard syncEnabled={false} />);
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("loads board data from API and saves changes", async () => {
    const boardFromApi = {
      ...initialData,
      columns: initialData.columns.map((column, index) =>
        index === 0 ? { ...column, title: "Persisted" } : column
      ),
    };

    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(mockResponse(200, boardFromApi))
      .mockResolvedValue(mockResponse(200, {}));

    render(<KanbanBoard />);
    await screen.findByDisplayValue("Persisted");

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Roadmap");

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({
          method: "PUT",
          credentials: "include",
        })
      );
    });
  });

  it("sends chat prompt and applies AI board updates", async () => {
    const boardFromApi = {
      ...initialData,
    };
    const boardAfterAi = {
      ...initialData,
      columns: initialData.columns.map((column, index) =>
        index === 0 ? { ...column, title: "Roadmap AI" } : column
      ),
    };

    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(mockResponse(200, boardFromApi))
      .mockResolvedValueOnce(
        mockResponse(200, {
          assistantMessage: "Done. Backlog is now Roadmap AI.",
          operations: [
            {
              type: "rename_column",
              columnId: "col-backlog",
              title: "Roadmap AI",
            },
          ],
          boardUpdated: true,
          board: boardAfterAi,
        })
      );

    render(<KanbanBoard />);
    await screen.findByDisplayValue("Backlog");

    await userEvent.type(
      screen.getByLabelText("Message AI assistant"),
      "Rename Backlog to Roadmap AI"
    );
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Done. Backlog is now Roadmap AI.");
    await screen.findByDisplayValue("Roadmap AI");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/ai/chat",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      })
    );
  });
});
