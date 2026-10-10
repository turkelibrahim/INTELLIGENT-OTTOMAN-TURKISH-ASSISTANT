"use client";

import React, { useState, useEffect, useRef } from "react";
import { chatApi } from "@/lib/api";
import { AlertTriangle } from 'lucide-react';


interface Message {
  id: string | number;
  role: "user" | "assistant" | "error";
  content: string;
  originalInput?: string;
}

function renderFormattedText(text: string) {
  if (!text) return null;
  const lines = text.split('\n');
  return lines.map((line, lineIdx) => {
    const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
    const cleanLine = isBullet ? line.trim().substring(2).trim() : line;
    
    const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
    const renderedParts = parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="font-semibold text-[var(--ota-gold)]">{part.slice(2, -2)}</strong>;
      }
      return <React.Fragment key={index}>{part}</React.Fragment>;
    });

    if (isBullet) {
      return (
        <div key={lineIdx} className="flex items-start gap-2 mb-1">
          <span className="text-[var(--ota-gold)] mt-0.5">•</span>
          <span>{renderedParts}</span>
        </div>
      );
    }
    
    return (
      <span key={lineIdx} className="block mb-1 last:mb-0">
        {renderedParts}
      </span>
    );
  });
}

export default function ChatWidget({ documentId, isOpen, onToggle }: { documentId: number | null, isOpen: boolean, onToggle: (open: boolean) => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && documentId && !sessionId && !error) {
      chatApi.createSession(documentId, "Document Chat")
        .then((session) => {
          setSessionId(session.id);
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: "Merhaba, ben Belge Asistanı. Osmanlıca belgenizle ilgili sormak istediğiniz bir şey var mı?"
          }]);
        })
        .catch((err) => {
          setError("Asistan bağlantısı kurulamadı. Lütfen sayfayı yenileyin.");
          console.error(err);
        });
    }
  }, [isOpen, documentId, sessionId, error]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  const handleSend = async (userMsg: string, isRetry: boolean = false) => {
    if (!userMsg.trim() || !sessionId || loading) return;

    if (!isRetry) {
      setMessages(prev => [...prev, { id: Date.now(), role: "user", content: userMsg }]);
    }
    setLoading(true);
    
    try {
      const response = await chatApi.sendMessage(sessionId, userMsg);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: "assistant", 
        content: response.content 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "error",
        content: "Mesaj gönderilemedi.",
        originalInput: userMsg
      }]);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    const val = input.trim();
    if (val) {
      setInput("");
      handleSend(val);
    }
  };

  const retryMessage = (msgId: string | number, originalInput?: string) => {
    if (!originalInput) return;
    setMessages(prev => prev.filter(m => m.id !== msgId));
    handleSend(originalInput, true);
  };

  if (!documentId) return null;

  return (
    <>
      {/* Floating Chat Button (Only visible when closed) */}
      {!isOpen && (
        <button
          onClick={() => onToggle(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center text-[var(--ota-obsidian)] transition-all duration-300 shadow-[0_0_20px_var(--ota-imperial-gold)] hover:scale-110 bg-gradient-to-r from-[var(--ota-imperial-gold)] to-[var(--ota-gold-light)] hover:shadow-[0_0_25px_var(--ota-imperial-gold)]"
          aria-label="Belge Asistanı"
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
      )}

      {/* Chat Drawer Overlay - Fixed positioned on right side */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-end pointer-events-none">
          {/* Drawer Panel */}
          <div className="relative z-10 w-full sm:w-[380px] max-w-full h-[100dvh] sm:h-[calc(100vh-80px)] sm:mb-4 sm:mr-4 sm:rounded-2xl bg-[var(--ota-bg-2)] border border-[var(--ota-border)] shadow-[-10px_0_30px_rgba(0,0,0,0.5)] flex flex-col animate-in slide-in-from-right duration-300 pointer-events-auto overflow-hidden">
            
            <div className="bg-[var(--ota-bg-2)] px-5 py-4 border-b border-[var(--ota-border)] flex items-center justify-between shadow-md shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--ota-bg)] flex items-center justify-center border border-[var(--ota-border-hover)]">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--ota-gold)]">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-[var(--ota-text)] text-sm tracking-wide">Belge Asistanı</h3>
                  <p className="text-[9px] text-[var(--ota-gold)] font-bold tracking-wider uppercase">YAPAY ZEKA DESTEKLİ</p>
                </div>
              </div>
              <button onClick={() => onToggle(false)} className="text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] transition-colors p-2 rounded-lg bg-[var(--ota-bg-1)] border border-[var(--ota-border)] hover:bg-[var(--ota-border)]">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-[var(--ota-bg-1)]/50 custom-scrollbar min-h-0">
              {error && (
                <div className="bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/20 text-[var(--ota-ruby)] text-xs p-3 rounded-xl text-center shrink-0 shadow-sm font-medium">
                  <span className="mr-2"><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>{error}
                </div>
              )}
              
              {messages.map((msg) => {
                if (msg.role === 'error') {
                  return (
                    <div key={msg.id} className="flex flex-col items-center my-1 shrink-0">
                      <div className="bg-[var(--ota-ruby)]/5 border border-[var(--ota-ruby)]/20 px-3 py-2 rounded-xl flex flex-wrap sm:flex-nowrap items-center justify-between gap-3 shadow-sm text-xs max-w-[90%] w-full">
                        <span className="text-[var(--ota-ruby)] font-medium flex items-center gap-1.5 shrink-0">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                          {msg.content}
                        </span>
                        <button 
                          onClick={() => retryMessage(msg.id, msg.originalInput)} 
                          className="bg-[var(--ota-ruby)]/10 hover:bg-[var(--ota-ruby)]/20 text-[var(--ota-ruby)] font-bold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap border border-[var(--ota-ruby)]/20 shadow-sm shrink-0"
                        >
                          Tekrar Dene
                        </button>
                      </div>
                    </div>
                  );
                }

                return (
                  <div 
                    key={msg.id} 
                    className={`flex flex-col max-w-[85%] shrink-0 ${msg.role === 'user' ? 'self-end' : 'self-start'}`}
                  >
                    <div 
                      className={`px-4 py-2.5 rounded-2xl ${
                        msg.role === 'user' 
                          ? 'bg-gradient-to-br from-[var(--ota-imperial-gold)] to-[var(--ota-gold)] text-[#0A202A] rounded-tr-sm shadow-md' 
                          : 'glass-card border border-[var(--ota-border)] text-[var(--ota-text)] rounded-tl-sm shadow-sm'
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap leading-relaxed font-medium">{renderFormattedText(msg.content)}</div>
                    </div>
                    <span className={`text-[9px] font-semibold tracking-wider text-[var(--ota-text-muted)] mt-1.5 uppercase ${msg.role === 'user' ? 'text-right mr-1' : 'ml-1'}`}>
                      {msg.role === 'user' ? 'Siz' : 'Belge Asistanı'}
                    </span>
                  </div>
                );
              })}
              
              {loading && (
                <div className="self-start glass-card border border-[var(--ota-border)] px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2 shrink-0 shadow-sm">
                  <div className="flex gap-1.5">
                    <span className="w-1.5 h-1.5 bg-[var(--ota-gold)] rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-[var(--ota-gold)] rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                    <span className="w-1.5 h-1.5 bg-[var(--ota-gold)] rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="h-1" />
            </div>

            <div className="p-4 bg-[var(--ota-bg-2)]/80 border-t border-[var(--ota-border)] shrink-0">
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
        </div>
      )}
    </>
  );
}
