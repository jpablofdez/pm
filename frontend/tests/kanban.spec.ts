import { expect, test, type Page } from "@playwright/test";

const createBoardFixture = () => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    {
      id: "col-progress",
      title: "In Progress",
      cardIds: ["card-4", "card-5"],
    },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
});

const mockAuthenticatedSession = async (page: Page, board = createBoardFixture()) => {
  let boardState = board;

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true, username: "user" }),
    });
  });
  await page.route("**/api/auth/logout", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false }),
    });
  });
  await page.route("**/api/board", async (route) => {
    const method = route.request().method();

    if (method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(boardState),
      });
      return;
    }

    if (method === "PUT") {
      boardState = route.request().postDataJSON() as typeof boardState;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(boardState),
      });
      return;
    }

    await route.fulfill({
      status: 405,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Method not allowed." }),
    });
  });
  await page.route("**/api/ai/chat", async (route) => {
    const payload = route.request().postDataJSON() as {
      message?: string;
      history?: Array<{ role: string; content: string }>;
    };

    const prompt = payload.message?.toLowerCase().trim() ?? "";

    if (prompt.includes("rename backlog")) {
      boardState = {
        ...boardState,
        columns: boardState.columns.map((column) =>
          column.id === "col-backlog"
            ? { ...column, title: "Roadmap AI" }
            : column
        ),
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          assistantMessage: "Done. Renamed Backlog to Roadmap AI.",
          operations: [
            {
              type: "rename_column",
              columnId: "col-backlog",
              title: "Roadmap AI",
            },
          ],
          boardUpdated: true,
          board: boardState,
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistantMessage: "No board changes needed.",
        operations: [],
        boardUpdated: false,
        board: boardState,
      }),
    });
  });
};

test("loads the kanban board", async ({ page }) => {
  await mockAuthenticatedSession(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await mockAuthenticatedSession(page);
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await mockAuthenticatedSession(page);
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("requires login and supports logout", async ({ page }) => {
  const board = createBoardFixture();

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Not authenticated." }),
    });
  });
  await page.route("**/api/auth/login", async (route) => {
    const payload = route.request().postDataJSON() as {
      username: string;
      password: string;
    };
    if (payload.username === "user" && payload.password === "password") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: true, username: "user" }),
      });
      return;
    }
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Invalid credentials." }),
    });
  });
  await page.route("**/api/auth/logout", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false }),
    });
  });
  await page.route("**/api/board", async (route) => {
    const method = route.request().method();

    if (method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(board),
      });
      return;
    }

    if (method === "PUT") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(route.request().postDataJSON()),
      });
      return;
    }

    await route.fulfill({
      status: 405,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Method not allowed." }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
});

test("persists board updates across reload", async ({ page }) => {
  await mockAuthenticatedSession(page);

  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const titleInput = firstColumn.getByLabel("Column title");

  await titleInput.clear();
  await titleInput.fill("Roadmap");
  await expect(titleInput).toHaveValue("Roadmap");

  await page.reload();
  await expect(firstColumn.getByLabel("Column title")).toHaveValue("Roadmap");
});

test("updates board from AI sidebar response", async ({ page }) => {
  await mockAuthenticatedSession(page);

  await page.goto("/");
  await page
    .getByLabel("Message AI assistant")
    .fill("Please rename Backlog to Roadmap AI");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Done. Renamed Backlog to Roadmap AI.")).toBeVisible();
  await expect(
    page.getByTestId("column-col-backlog").getByLabel("Column title")
  ).toHaveValue("Roadmap AI");
});
