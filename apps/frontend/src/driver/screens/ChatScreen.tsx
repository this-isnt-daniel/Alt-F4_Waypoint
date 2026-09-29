import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";

const QUICK_REPLIES = ["I'm 5 minutes away", "At the loading bay", "Can't find parking"];

export function ChatScreen() {
  const { route, back } = useNavigator();
  const outletId = route.params.outletId ?? "OUT047";
  const [messages, setMessages] = useState([
    { id: 1, text: "Morning Nimal. Use the rear bay—main street access is blocked.", sender: "store", time: "06:05" },
    { id: 2, text: "On my way. ETA 12 minutes.", sender: "driver", time: "06:06" },
    { id: 3, text: "I'll meet you at bay B.", sender: "store", time: "06:07" }
  ]);
  const [input, setInput] = useState("");

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    setMessages([...messages, { id: Date.now(), text, sender: "driver", time: "06:08" }]);
    setInput("");
  };

  return (
    <div className="flex flex-col h-screen max-w-[430px] mx-auto bg-slate-50">
      <div className="p-4 bg-white border-b border-slate-200 flex items-center gap-3">
        <button onClick={back} className="p-2 -ml-2 text-slate-500 hover:text-slate-900">
          <AppIcon name="arrow-left" size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-[15px] font-bold text-slate-900">Anjali Silva</h1>
          <p className="text-[12px] text-slate-500">{outletId} · Store manager</p>
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.sender === "driver" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] p-3 rounded-xl text-[13px] ${
              m.sender === "driver" ? "bg-green text-white rounded-tr-sm" : "bg-white border border-slate-200 text-slate-900 rounded-tl-sm"
            }`}>
              {m.text}
              <div className={`text-[10px] mt-1 text-right ${m.sender === "driver" ? "text-green-100" : "text-slate-400"}`}>
                {m.time}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 bg-white border-t border-slate-200 space-y-3">
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {QUICK_REPLIES.map((r) => (
            <button key={r} onClick={() => handleSend(r)} className="whitespace-nowrap px-3 py-1.5 rounded-lg bg-slate-100 text-[12px] text-slate-700 hover:bg-slate-200 font-medium">
              {r}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder="Message store manager..."
            className="flex-1 px-3 py-2 bg-slate-100 border-none rounded-lg text-[13px] text-slate-900 focus:ring-2 focus:ring-green/50 outline-none"
          />
          <button onClick={() => handleSend(input)} disabled={!input.trim()} className="p-2 bg-green text-white rounded-lg disabled:opacity-50 flex items-center justify-center w-10">
            <AppIcon name="send" size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
