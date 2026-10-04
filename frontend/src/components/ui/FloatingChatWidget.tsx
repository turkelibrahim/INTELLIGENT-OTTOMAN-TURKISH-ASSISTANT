import React, { useState, useEffect, useRef } from "react";
import { chatApi } from "@/lib/api";
import { Icons } from "@/components/Icons";

interface Message {
  id: string | number;
  role: "user" | "assistant";
  content: string;
}

interface FloatingChatWidgetProps {
  documentId: number | null;
}

export function FloatingChatWidget({ documentId }: FloatingChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    if (isOpen) {
      timeoutId = setTimeout(scrollToBottom, 100);
    }
    return () => clearTimeout(timeoutId);
  }, [messages, isOpen]);

  useEffect(() => {
    if (documentId && isOpen && !sessionId && !error) {
      chatApi.createSession(documentId, "Document Chat")
        .then((session) => {
          setSessionId(session.id);
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: "Merhaba, bu belge ile ilgili merak ettiğiniz nedir?"
          }]);
        })
        .catch((err) => {
          setError("Asistanı bağlantısı kurulamadı. Lütfen sayfayı yenileyin.");
          console.error(err);
        });
    }
  }, [documentId, isOpen, sessionId, error]);

  const sendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || !sessionId || loading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: userMsg }]);
    setLoading(true);
    setError("");
    
    try {
      const response = await chatApi.sendMessage(sessionId, userMsg);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: "assistant", 
        content: response.content 
      }]);
    } catch (err) {
      setError("Mesaj gönderilemedi. Lütfen tekrar deneyin.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!documentId) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      <div 
        className={`mb-4 transition-all duration-300 ease-in-out transform origin-bottom-right overflow-hidden ${
          isOpen ? 'scale-100 opacity-100' : 'scale-0 opacity-0 pointer-events-none'
        }`}
        style={{ height: '500px', width: '380px', maxHeight: 'calc(100vh - 120px)' }}
      >
        <div className="flex flex-col h-full bg-slate-900 border border-amber-500/30 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-amber-500/20 shadow-sm">
            <div className="flex items-center gap-3 text-amber-500">
              {Icons.chat}
              <div>
                <h3 className="font-semibold text-slate-100 text-sm">Belge Asistanıı</h3>
                <p className="text-[10px] text-emerald-400 font-medium tracking-wider uppercase">Çevrimiçi</p>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg p-1.5 transition-colors"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 custom-scrollbar bg-slate-900/60">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`max-w-[85%] rounded-xl px-4 py-2.5 shadow-sm ${
                  msg.role === "user" 
                    ? "bg-amber-500/90 text-slate-900 self-end rounded-tr-sm" 
                    : "bg-slate-800 text-slate-200 self-start border border-slate-700 rounded-tl-sm"
                }`}
              >
                <p className="whitespace-pre-wrap text-[14px] leading-relaxed font-medium">{msg.content}</p>
              </div>
            ))}
            
            {loading && (
              <div className="bg-slate-800 text-slate-400 self-start border border-slate-700 rounded-xl rounded-tl-sm px-4 py-3 max-w-[85%] flex items-center gap-2 shadow-sm">
                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
              </div>
            )}
            
            {error && (
              <div className="self-center bg-red-900/30 text-red-400 border border-red-900/50 rounded-lg px-3 py-2 text-xs text-center w-full font-medium">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} className="h-1" />
          </div>

          {/* Input Area */}
          <div className="p-3 bg-slate-800 border-t border-amber-500/20">
            <form onSubmit={sendMessage} className="relative flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Belge ile ilgili sorunuz..."
                className="w-full bg-slate-900 text-slate-100 placeholder:text-slate-500 border border-slate-700 rounded-xl px-4 py-3 min-h-[44px] max-h-[120px] resize-none focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-all custom-scrollbar text-[14px]"
                rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
                disabled={loading || (!sessionId && !error)}
              />
              <button
                type="submit"
                disabled={loading || !input.trim() || !sessionId}
                className="flex-shrink-0 w-11 h-11 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 rounded-xl flex items-center justify-center transition-all disabled:cursor-not-allowed mb-[1px] shadow-sm active:scale-95"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </form>
            <div className="text-center mt-2">
              <span className="text-[10px] text-slate-500 font-medium">Shift + Enter yeni satır, Enter gönder</span>
            </div>
          </div>
        </div>
      </div>

      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.2)] transition-all duration-300 hover:scale-110 active:scale-95 z-50 ${
          isOpen 
            ? 'bg-slate-800 text-amber-500 border border-amber-500/30' 
            : 'bg-amber-500 text-slate-900 hover:bg-amber-400'
        }`}
        aria-label="Belge Asistanıı"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        ) : (
          Icons.chat
        )}
      </button>
    </div>
  );
}
