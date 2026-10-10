"use client";

import { useState, useEffect, useRef } from "react";
import { chatApi } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";

interface Message {
  id: string | number;
  role: "user" | "assistant";
  content: string;
}

export default function ChatTab({ documentId }: { documentId: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
        setError("Asistanı bağlantısı kurulamadı.");
        console.error(err);
      });
  }, [documentId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId || loading) return;

    const userMsg = input;
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
      setError("Mesaj gönderilemedi.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ota-tab-panel ota-flex-col" style={{ height: "100%", maxHeight: "500px", padding: "16px" }}>
      <h3 className="ota-text-lg ota-font-medium mb-4">Belge Asistanıı</h3>
      
      {error && (
        <div className="mb-4">
          <StatusBadge variant="error" label={error} />
        </div>
      )}

      <div className="flex-1 overflow-y-auto mb-4" style={{ display: "flex", flexDirection: "column", gap: "12px", flexGrow: 1 }}>
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            style={{ 
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "var(--ota-gold)" : "var(--ota-surface-2)",
              color: msg.role === "user" ? "#05090B" : "var(--ota-text)",
              padding: "12px 16px",
              borderRadius: "12px",
              border: msg.role === "user" ? "none" : "1px solid var(--ota-border)",
              maxWidth: "80%"
            }}
          >
            <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: "flex-start", padding: "12px 16px", color: "var(--ota-text-secondary)" }}>
            <span className="ota-spinner small"></span> Düşünüyor...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} style={{ display: "flex", gap: "8px", marginTop: "auto" }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Soru sorun..." 
          className="ota-input" 
          style={{ flex: 1 }}
          disabled={loading || !sessionId}
        />
        <button 
          type="submit" 
          className="ota-btn-primary" 
          disabled={loading || !input.trim() || !sessionId}
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
