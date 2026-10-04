"use client";

import { useState, useEffect, useRef } from "react";
import { chatApi } from "@/lib/api";

interface Message {
  id: string | number;
  role: "user" | "assistant";
  content: string;
}

export default function ChatWidget({ documentId }: { documentId: number | null }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && documentId && !sessionId) {
      chatApi.createSession(documentId, "Document Chat")
        .then((session) => {
          setSessionId(session.id);
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: "Merhaba, ben Belge Asistanıı. Osmanlıca belgenizle ilgili sormak istediğiniz bir şey var mı?"
          }]);
        })
        .catch((err) => {
          setError("Asistanı bağlantısı kurulamadı.");
          console.error(err);
        });
    }
  }, [isOpen, documentId, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId || loading) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: userMsg }]);
    setLoading(true);
    
    try {
      const response = await chatApi.sendMessage(sessionId, userMsg);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: "assistant", 
        content: response.content 
      }]);
    } catch (err) {
      setError("Mesaj gönderilemedi.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!documentId) return null;

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center text-[var(--ota-obsidian)] transition-all duration-300 shadow-[0_0_20px_var(--ota-imperial-gold)] hover:scale-110 ${isOpen ? 'bg-[var(--ota-deep-emerald)] text-[var(--ota-imperial-gold)] border border-[var(--ota-imperial-gold)]' : 'bg-gradient-to-r from-[var(--ota-imperial-gold)] to-[var(--ota-gold-light)] hover:shadow-[0_0_25px_var(--ota-imperial-gold)]'}`}
        aria-label="Belge Asistanı"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-[380px] h-[550px] max-h-[75vh] glass-panel rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-300">
          
          <div className="bg-[var(--ota-bg-2)]/80 px-5 py-4 border-b border-[var(--ota-border)] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--ota-teal-active)] flex items-center justify-center border border-[var(--ota-border-hover)]">
                <span className="text-lg">🤖</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--ota-text)] text-sm">Belge Asistanı</h3>
                <p className="text-[10px] text-[var(--ota-gold)] font-medium tracking-wide uppercase">Yapay Zeka Destekli</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] transition-colors">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-[var(--ota-bg-1)]/50 custom-scrollbar">
            {error && (
              <div className="bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/20 text-[var(--ota-ruby)] text-xs p-2 rounded-lg text-center">
                ⚠️ {error}
              </div>
            )}
            
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}
              >
                <div 
                  className={`px-4 py-2.5 rounded-2xl ${
                    msg.role === 'user' 
                      ? 'bg-[var(--ota-imperial-gold)] text-[var(--ota-obsidian)] rounded-tr-sm' 
                      : 'glass-card border border-[var(--ota-border)] text-[var(--ota-text)] rounded-tl-sm'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
                <span className={`text-[10px] text-[var(--ota-text-muted)] mt-1 ${msg.role === 'user' ? 'text-right mr-1' : 'ml-1'}`}>
                  {msg.role === 'user' ? 'Siz' : 'Asistan'}
                </span>
              </div>
            ))}
            
            {loading && (
              <div className="self-start glass-card border border-[var(--ota-border)] px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-[var(--ota-imperial-gold)] rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-[var(--ota-imperial-gold)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  <span className="w-1.5 h-1.5 bg-[var(--ota-imperial-gold)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-[var(--ota-bg-2)]/80 border-t border-[var(--ota-border)]">
            <form onSubmit={sendMessage} className="flex items-center gap-2">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Bir soru sorun..." 
                className="flex-1 bg-[var(--ota-bg-1)] border border-[var(--ota-border)] rounded-full px-4 py-2.5 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)]/50 placeholder-[var(--ota-text-muted)] transition-all"
                disabled={loading || !sessionId}
              />
              <button 
                type="submit" 
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                  !input.trim() || loading || !sessionId 
                    ? 'bg-[var(--ota-card)] text-[var(--ota-text-muted)] cursor-not-allowed' 
                    : 'bg-[var(--ota-imperial-gold)] text-[var(--ota-obsidian)] hover:bg-[var(--ota-gold-light)] shadow-[0_0_10px_var(--ota-imperial-gold)]'
                }`}
                disabled={loading || !input.trim() || !sessionId}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="ml-0.5">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
