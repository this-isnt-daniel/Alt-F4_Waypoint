import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { CHAT_QUICK_REPLIES, TRIP_1_STOPS } from "@/driver/data/driverContent";
import { sanitizeText } from "@/lib/security";

export function ChatScreen() {
  const { route, push } = useNavigator();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const [messages, setMessages] = useState<Array<{ sender: "store" | "driver"; text: string; time: string }>>([
    {
      sender: "store",
      text: "Morning Nimal. Use the rear bay—main street access is blocked.",
      time: "06:05",
    },
    {
      sender: "driver",
      text: "On my way. ETA 12 minutes.",
      time: "06:06",
    },
    {
      sender: "store",
      text: "I’ll meet you at bay B.",
      time: "06:07",
    },
  ]);
  const [inputText, setInputText] = useState<string>("");

  const handleSend = (textToSend?: string) => {
    const raw = textToSend ?? inputText;
    if (!raw.trim()) return;
    const clean = sanitizeText(raw);

    setMessages((prev) => [
      ...prev,
      {
        sender: "driver",
        text: clean,
        time: new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
      },
    ]);
    setInputText("");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 flex flex-col min-h-[calc(100vh-60px)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line pb-3">
        <div>
          <h1 className="text-base font-extrabold text-ink">{stop.manager}</h1>
          <p className="text-xs text-ink-muted">
            {stop.outletId} · Store manager · <span className="text-success font-medium">Available</span>
          </p>
        </div>
        <Button
          variant="secondary"
          size="md"
          fullWidth={false}
          onClick={() => push("call-overlay", { outletId: stop.outletId })}
        >
          📞 Call
        </Button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 space-y-3 overflow-y-auto py-2">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.sender === "driver" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-btn text-xs leading-relaxed ${
                msg.sender === "driver"
                  ? "bg-green text-green-ink font-medium"
                  : "bg-surface border border-line text-ink"
              }`}
            >
              {msg.text}
            </div>
            <span className="text-2xs text-ink-muted mt-1 px-1">{msg.time}</span>
          </div>
        ))}
      </div>

      {/* Quick Replies */}
      <div className="space-y-1.5 pt-2 border-t border-line">
        <span className="text-2xs font-extrabold uppercase text-ink-muted">Quick Replies</span>
        <div className="flex flex-wrap gap-1.5">
          {CHAT_QUICK_REPLIES.map((reply, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(reply)}
              className="text-xs bg-raised border border-line hover:bg-surface text-ink px-2.5 py-1.5 rounded-pill transition-colors font-medium"
            >
              {reply}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="flex gap-2 pt-1">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Message store manager..."
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 p-3 bg-surface border border-line rounded-btn text-xs text-ink focus:outline-2 focus:outline-green"
        />
        <Button variant="primary" size="md" fullWidth={false} onClick={() => handleSend()}>
          Send
        </Button>
      </div>
    </div>
  );
}
