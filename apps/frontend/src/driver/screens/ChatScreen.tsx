import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { ArrowLeft, Send } from "lucide-react";

const STORE_QUICK_REPLIES = ["I'm 5 minutes away", "At the loading bay", "Can't find parking"];
const DISPATCH_QUICK_REPLIES = [
  "Proceeding with run",
  "Need roadside assistance",
  "Waiting for replacement",
  "Issue resolved",
];

export function ChatScreen() {
  const { route, back } = useNavigator();
  const isDispatch = route.params.recipient === "dispatch";
  const outletId = route.params.outletId ?? "OUT047";
  const topic = route.params.topic;

  const [messages, setMessages] = useState(() => {
    if (isDispatch) {
      const topicText = topic ? `Flagged: ${topic}` : "Vehicle issue";
      return [
        {
          id: 1,
          text: `${topicText} on VEH014 (Kandy hub). Requesting assistance.`,
          sender: "driver",
          time: "06:10",
        },
        {
          id: 2,
          text: "Received Daniru. Fleet maintenance has logged the report for VEH014. If safe to proceed, continue your run; otherwise stand by.",
          sender: "dispatch",
          time: "06:11",
        },
      ];
    }
    return [
      { id: 1, text: "Morning Daniru. Use the rear bay—main street access is blocked.", sender: "store", time: "06:05" },
      { id: 2, text: "On my way. ETA 12 minutes.", sender: "driver", time: "06:06" },
      { id: 3, text: "I'll meet you at bay B.", sender: "store", time: "06:07" }
    ];
  });
  const [input, setInput] = useState("");

  const quickReplies = isDispatch ? DISPATCH_QUICK_REPLIES : STORE_QUICK_REPLIES;
  const placeholder = isDispatch ? "Message dispatch..." : "Message store manager...";

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), text, sender: "driver", time: "06:12" },
    ]);
    setInput("");
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-slate-50">
      <div className="px-5 py-4 bg-white border-b border-slate-200 flex items-center gap-3 shrink-0">
        <button
          onClick={back}
          className="p-2 -ml-2 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Back"
        >
          <ArrowLeft size={22} />
        </button>
        <div className="flex-1">
          <h1 className="text-[16px] font-bold text-slate-900">
            {isDispatch ? "Central Dispatch" : "Joseph Vijay"}
          </h1>
          <p className="text-[13px] text-slate-500">
            {isDispatch
              ? "Stephan Anthony · Kandy Hub Dispatcher"
              : `${outletId} · Store manager`}
          </p>
        </div>
      </div>

      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.sender === "driver" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] p-3.5 rounded-2xl text-[14px] leading-relaxed shadow-sm ${
              m.sender === "driver" 
                ? "bg-emerald-600 text-white rounded-tr-sm" 
                : "bg-white border border-slate-200 text-slate-900 rounded-tl-sm"
            }`}>
              {m.text}
              <div className={`text-[11px] mt-1.5 text-right font-medium ${m.sender === "driver" ? "text-emerald-100" : "text-slate-400"}`}>
                {m.time}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 bg-white border-t border-slate-200 space-y-3 shrink-0 pb-safe">
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar px-1">
          {quickReplies.map((r) => (
            <button key={r} onClick={() => handleSend(r)} className="whitespace-nowrap px-4 py-2 rounded-full bg-slate-100 text-[13px] text-slate-700 hover:bg-slate-200 font-medium transition-colors border border-slate-200">
              {r}
            </button>
          ))}
        </div>
        <div className="flex gap-2 px-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder={placeholder}
            className="flex-1 px-4 py-3 bg-slate-100 border-none rounded-xl text-[14px] text-slate-900 focus:ring-2 focus:ring-emerald-500/50 outline-none"
          />
          <button onClick={() => handleSend(input)} disabled={!input.trim()} className="p-3 bg-emerald-600 text-white rounded-xl disabled:opacity-50 flex items-center justify-center w-12 hover:bg-emerald-700 transition-colors shadow-sm">
            <Send size={18} className="ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
}
