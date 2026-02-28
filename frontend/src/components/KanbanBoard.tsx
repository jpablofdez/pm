"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type AIChatResponse = {
  assistantMessage: string;
  operations: unknown[];
  boardUpdated: boolean;
  board: BoardData;
};

type KanbanBoardProps = {
  onLogout?: () => void | Promise<void>;
  isLoggingOut?: boolean;
  syncEnabled?: boolean;
};

export const KanbanBoard = ({
  onLogout,
  isLoggingOut = false,
  syncEnabled = true,
}: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoadingBoard, setIsLoadingBoard] = useState(syncEnabled);
  const [isSavingBoard, setIsSavingBoard] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const persistBoard = useCallback(
    async (nextBoard: BoardData) => {
      if (!syncEnabled) {
        return;
      }

      setIsSavingBoard(true);
      setSyncError(null);

      try {
        const response = await fetch("/api/board", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(nextBoard),
        });

        if (!response.ok) {
          throw new Error("Failed to save board.");
        }
      } catch {
        setSyncError("Unable to save changes.");
      } finally {
        setIsSavingBoard(false);
      }
    },
    [syncEnabled]
  );

  const updateBoard = useCallback(
    (updater: (current: BoardData) => BoardData) => {
      setBoard((prev) => {
        const next = updater(prev);
        void persistBoard(next);
        return next;
      });
    },
    [persistBoard]
  );

  useEffect(() => {
    if (!syncEnabled) {
      setIsLoadingBoard(false);
      return;
    }

    let isCancelled = false;

    const loadBoard = async () => {
      setIsLoadingBoard(true);
      setSyncError(null);

      try {
        const response = await fetch("/api/board", {
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error("Failed to load board.");
        }

        const payload = (await response.json()) as BoardData;
        if (!isCancelled) {
          setBoard(payload);
        }
      } catch {
        if (!isCancelled) {
          setSyncError("Unable to load saved board.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingBoard(false);
        }
      }
    };

    void loadBoard();

    return () => {
      isCancelled = true;
    };
  }, [syncEnabled]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    updateBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    updateBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    updateBoard((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
          ? {
              ...column,
              cardIds: column.cardIds.filter((id) => id !== cardId),
            }
          : column
        ),
      };
    });
  };

  const handleSendToAssistant = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const message = chatInput.trim();
    if (!message || isSendingChat) {
      return;
    }

    const historyPayload = chatMessages.map((entry) => ({
      role: entry.role,
      content: entry.content,
    }));

    setChatInput("");
    setChatError(null);
    setIsSendingChat(true);
    setChatMessages((prev) => [...prev, { role: "user", content: message }]);

    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message,
          history: historyPayload,
        }),
      });

      if (!response.ok) {
        throw new Error("AI request failed.");
      }

      const payload = (await response.json()) as AIChatResponse;
      if (
        typeof payload.assistantMessage !== "string" ||
        payload.assistantMessage.trim() === ""
      ) {
        throw new Error("Invalid AI response.");
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: payload.assistantMessage },
      ]);

      if (payload.boardUpdated) {
        setBoard(payload.board);
        setSyncError(null);
      }
    } catch {
      setChatError("Unable to get AI response.");
    } finally {
      setIsSendingChat(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Focus
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  One board. Five columns. Zero clutter.
                </p>
                <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                  {isLoadingBoard
                    ? "Loading board..."
                    : isSavingBoard
                      ? "Saving..."
                      : syncError
                        ? syncError
                        : "Changes synced"}
                </p>
              </div>
              {onLogout ? (
                <button
                  type="button"
                  className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={onLogout}
                  disabled={isLoggingOut}
                >
                  {isLoggingOut ? "Logging out..." : "Log out"}
                </button>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="min-w-0">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
              <DragOverlay>
                {activeCard ? (
                  <div className="w-[260px]">
                    <KanbanCardPreview card={activeCard} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          </div>

          <aside
            className="flex min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-5 shadow-[var(--shadow)]"
            data-testid="ai-sidebar"
          >
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                AI Assistant
              </p>
              <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
                Chat with your board
              </h2>
              <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
                Ask for edits like renaming columns, creating cards, or moving work
                between stages.
              </p>
            </div>

            <div className="mt-4 flex-1 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-white p-3">
              {chatMessages.length === 0 ? (
                <p className="text-sm leading-6 text-[var(--gray-text)]">
                  Try: Rename Backlog to Roadmap and move card-1 to Review.
                </p>
              ) : (
                <ul className="space-y-3" aria-label="AI conversation">
                  {chatMessages.map((message, index) => (
                    <li
                      key={`${message.role}-${index}`}
                      className={`rounded-2xl px-3 py-2 text-sm leading-6 ${
                        message.role === "user"
                          ? "bg-[var(--surface)] text-[var(--navy-dark)]"
                          : "bg-[rgba(32,157,215,0.12)] text-[var(--navy-dark)]"
                      }`}
                    >
                      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                        {message.role === "user" ? "You" : "Assistant"}
                      </p>
                      <p className="mt-1 whitespace-pre-wrap">{message.content}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <form className="mt-4 space-y-3" onSubmit={handleSendToAssistant}>
              <label
                htmlFor="ai-message"
                className="text-sm font-semibold text-[var(--navy-dark)]"
              >
                Message AI assistant
              </label>
              <textarea
                id="ai-message"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Example: Add a card in Discovery called Customer interview prep."
                className="w-full rounded-2xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                rows={4}
                disabled={isSendingChat}
              />
              {chatError ? (
                <p className="text-sm font-medium text-[var(--secondary-purple)]" role="alert">
                  {chatError}
                </p>
              ) : null}
              <button
                type="submit"
                className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSendingChat || chatInput.trim() === ""}
              >
                {isSendingChat ? "Sending..." : "Send"}
              </button>
            </form>
          </aside>
        </section>
      </main>
    </div>
  );
};
