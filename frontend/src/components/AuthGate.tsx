"use client";

import { type FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

type AuthState = "checking" | "authenticated" | "unauthenticated";

export const AuthGate = () => {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch("/api/auth/me", {
          credentials: "include",
        });
        setAuthState(response.ok ? "authenticated" : "unauthenticated");
      } catch {
        setAuthState("unauthenticated");
      }
    };

    void checkSession();
  }, []);

  const handleSignIn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username,
          password,
        }),
      });

      if (!response.ok) {
        setErrorMessage("Invalid credentials. Use user / password.");
        return;
      }

      setPassword("");
      setAuthState("authenticated");
    } catch {
      setErrorMessage("Unable to sign in right now.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      setPassword("");
      setErrorMessage("");
      setAuthState("unauthenticated");
      setIsLoggingOut(false);
    }
  };

  if (authState === "authenticated") {
    return <KanbanBoard onLogout={handleLogout} isLoggingOut={isLoggingOut} />;
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[480px] items-center px-6 py-16">
      <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)]">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          Project Manager MVP
        </p>
        <h1 className="mt-4 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Sign in to continue
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Use the demo credentials to access your board.
        </p>
        <p className="mt-2 text-sm font-semibold text-[var(--primary-blue)]">
          user / password
        </p>

        {authState === "checking" ? (
          <p className="mt-8 text-sm text-[var(--gray-text)]">Checking session...</p>
        ) : (
          <form className="mt-8 space-y-4" onSubmit={handleSignIn}>
            <label className="block text-sm font-medium text-[var(--navy-dark)]">
              Username
              <input
                className="mt-1 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                placeholder="user"
              />
            </label>
            <label className="block text-sm font-medium text-[var(--navy-dark)]">
              Password
              <input
                className="mt-1 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="password"
              />
            </label>
            {errorMessage ? (
              <p className="text-sm font-medium text-[var(--secondary-purple)]" role="alert">
                {errorMessage}
              </p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
};
