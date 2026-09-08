import { useEffect, useRef, useState } from "react";
import { Bot, MessageCircle, Send, X } from "lucide-react";
import { api } from "../api/client.js";

const SUGGESTIONS = [
  "Summarize today's AI insights",
  "What's the top defect contributor?",
  "Which batches are HIGH risk right now?",
  "Any lines with camera coverage gaps?",
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, busy, open]);

  async function send(text) {
    const question = (text ?? input).trim();
    if (!question || busy) return;
    const next = [...messages, { role: "user", content: question }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setError(null);
    try {
      const reply = await api.chat(next);
      setMessages([...next, reply]);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="chat-fab"
        aria-label={open ? "Close CellMind Assistant" : "Open CellMind Assistant"}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <X className="icon" /> : <MessageCircle className="icon" />}
      </button>

      {open && (
        <div className="chat-panel">
          <div className="chat-panel-head">
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Bot className="icon" style={{ width: 16, height: 16 }} />
              <b style={{ fontSize: 13 }}>CellMind Assistant</b>
            </span>
            <span style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>read-only</span>
          </div>

          <div className="chat-panel-body" ref={listRef}>
            {messages.length === 0 && !busy && (
              <div>
                <p style={{ fontSize: 12, color: "var(--ink-mute)", margin: "0 0 10px" }}>
                  Ask about batches, equipment, cameras, investigations, recommendations, or the latest AI insights.
                  I can look things up, not change them.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {SUGGESTIONS.map((s) => (
                    <button key={s} type="button" className="btn btn-secondary" style={{ fontSize: 11.5, justifyContent: "flex-start" }} onClick={() => send(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`}>
                {m.content}
              </div>
            ))}

            {busy && <div className="chat-bubble chat-bubble-assistant chat-typing">Thinking…</div>}

            {error && (
              <div className="chat-bubble chat-bubble-error">
                {error.status === 503
                  ? `Assistant unavailable right now — try again shortly. (${error.message})`
                  : `Something went wrong: ${error.message}`}
              </div>
            )}
          </div>

          <form
            className="chat-panel-input"
            onSubmit={(e) => { e.preventDefault(); send(); }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the plant…"
              disabled={busy}
            />
            <button type="submit" className="btn btn-primary" disabled={busy || !input.trim()} aria-label="Send">
              <Send className="icon" style={{ width: 14, height: 14 }} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
