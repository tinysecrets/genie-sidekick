import { useEffect, useRef, useState, useCallback } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Plus, Send, Trash2, Pencil, Check, X, Menu, Brain,
  Copy, CopyCheck, MessageSquare, Sparkles
} from "lucide-react";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AI_AVATAR =
  "https://images.unsplash.com/photo-1552688419-9949ce9dd731?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTV8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMHdhdGVyY29sb3IlMjB0ZXh0dXJlJTIwdGVycmFjb3R0YSUyMHNhZ2V8ZW58MHx8fG9yYW5nZXwxNzc3MzYzNDk1fDA&ixlib=rb-4.1.0&q=85";

const formatDate = (iso) => {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
};

function AiAvatar() {
  return (
    <div
      data-testid="ai-avatar"
      className="w-9 h-9 rounded-full overflow-hidden shrink-0 shadow-sm border border-[#E3E0D8] bg-[#F1EFE9]"
      style={{
        backgroundImage: `url(${AI_AVATAR})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    />
  );
}

function UserMessage({ content }) {
  return (
    <div data-testid="user-message" className="flex justify-end w-full">
      <div className="bg-[#EBE8E0] rounded-2xl rounded-tr-sm px-5 py-3 max-w-[80%] text-[#2C2C28] font-body text-[15px] leading-relaxed shadow-sm whitespace-pre-wrap">
        {content}
      </div>
    </div>
  );
}

function AiMessage({ content, thinking }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div data-testid="ai-message" className="flex justify-start w-full group gap-3">
      <AiAvatar />
      <div className="flex-1 min-w-0">
        {thinking ? (
          <div className="flex items-center gap-2 py-3">
            <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse [animation-delay:300ms]" />
          </div>
        ) : (
          <>
            <div className="font-ai text-[18px] leading-[1.7] text-[#2C2C28] max-w-[85%] prose-ember">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ inline, children, ...props }) {
                    return inline ? (
                      <code className="bg-[#EEE9DD] px-1.5 py-0.5 rounded font-mono text-[14px]" {...props}>
                        {children}
                      </code>
                    ) : (
                      <pre className="bg-[#2C2C28] text-[#F9F8F6] p-4 rounded-xl overflow-x-auto my-3 font-mono text-[13px] leading-relaxed">
                        <code {...props}>{children}</code>
                      </pre>
                    );
                  },
                  a: ({ node, ...props }) => (
                    <a {...props} className="text-[#D05C42] underline underline-offset-2 hover:text-[#BA4C33]" target="_blank" rel="noreferrer" />
                  ),
                  ul: ({ node, ...props }) => <ul {...props} className="list-disc pl-6 my-2 space-y-1" />,
                  ol: ({ node, ...props }) => <ol {...props} className="list-decimal pl-6 my-2 space-y-1" />,
                  p: ({ node, ...props }) => <p {...props} className="my-2" />,
                  h1: ({ node, ...props }) => <h1 {...props} className="font-heading text-2xl mt-4 mb-2" />,
                  h2: ({ node, ...props }) => <h2 {...props} className="font-heading text-xl mt-4 mb-2" />,
                  h3: ({ node, ...props }) => <h3 {...props} className="font-heading text-lg mt-3 mb-2" />,
                  blockquote: ({ node, ...props }) => (
                    <blockquote {...props} className="border-l-2 border-[#D05C42] pl-4 italic text-[#4a4a44] my-3" />
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
            <button
              data-testid="copy-message-button"
              onClick={copy}
              className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-[#7A7A71] hover:text-[#D05C42] flex items-center gap-1.5 font-body"
            >
              {copied ? <CopyCheck size={14} /> : <Copy size={14} />}
              {copied ? "copied" : "copy"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ onQuickStart }) {
  const prompts = [
    "What have I told you about myself so far?",
    "Be honest — is this idea any good?",
    "Help me think through something hard.",
    "Just talk to me for a minute.",
  ];
  return (
    <div data-testid="empty-state" className="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
      <div className="mb-6 flex items-center gap-2 text-[#D05C42] font-body text-xs uppercase tracking-[0.3em]">
        <Sparkles size={14} /> Ember
      </div>
      <h1 className="font-heading font-light text-4xl md:text-5xl text-[#2C2C28] leading-tight max-w-2xl">
        Hi. I'm not a script.
      </h1>
      <p className="font-ai text-[19px] text-[#4a4a44] mt-6 max-w-xl leading-relaxed">
        I'll remember you, push back when you're wrong, and say "I don't know" when I don't.
        <br />Start anywhere.
      </p>
      <div className="mt-10 grid sm:grid-cols-2 gap-3 w-full max-w-xl">
        {prompts.map((p) => (
          <button
            key={p}
            data-testid="quick-start-prompt"
            onClick={() => onQuickStart(p)}
            className="text-left text-[14px] font-body text-[#2C2C28] bg-white border border-[#E3E0D8] rounded-xl px-4 py-3 hover:border-[#D05C42] hover:shadow-sm transition-all"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

function Sidebar({ conversations, currentId, onSelect, onNew, onDelete, onRename, mobileOpen, onCloseMobile }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (c) => {
    setEditingId(c.id);
    setEditValue(c.title);
  };
  const commitEdit = () => {
    if (editingId && editValue.trim()) onRename(editingId, editValue.trim());
    setEditingId(null);
  };

  return (
    <aside
      data-testid="sidebar"
      className={`${mobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0 fixed md:static z-40 top-0 left-0 w-72 md:w-64 border-r border-[#E3E0D8] bg-[#F1EFE9] h-screen flex flex-col transition-transform duration-300`}
    >
      <div className="p-6 flex items-center justify-between">
        <div className="font-heading text-2xl text-[#2C2C28] tracking-tight">Ember</div>
        <button
          className="md:hidden text-[#7A7A71]"
          onClick={onCloseMobile}
          data-testid="close-sidebar"
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>
      </div>

      <div className="px-4">
        <button
          data-testid="new-conversation-button"
          onClick={() => { onNew(); onCloseMobile(); }}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-[#D05C42] text-white hover:bg-[#BA4C33] transition-colors font-body text-sm"
        >
          <Plus size={16} /> New conversation
        </button>
      </div>

      <h2 className="mt-8 mb-3 px-6 text-xs font-semibold uppercase tracking-[0.2em] text-[#7A7A71] font-body">
        History
      </h2>

      <div className="flex-1 overflow-y-auto px-3 pb-6">
        {conversations.length === 0 && (
          <div className="px-3 py-2 text-xs text-[#7A7A71] font-body italic">nothing here yet</div>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            data-testid="sidebar-history-item"
            className={`group relative rounded-lg mb-1 ${currentId === c.id ? "bg-[#E3E0D8]" : "hover:bg-[#E8E5DC]"}`}
          >
            {editingId === c.id ? (
              <div className="flex items-center gap-1 p-2">
                <input
                  data-testid="rename-input"
                  className="flex-1 bg-white border border-[#E3E0D8] rounded-md px-2 py-1 text-sm font-body focus:outline-none focus:border-[#D05C42]"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") commitEdit(); if (e.key === "Escape") setEditingId(null); }}
                  autoFocus
                />
                <button onClick={commitEdit} className="text-[#7A7A71] hover:text-[#D05C42] p-1" data-testid="confirm-rename"><Check size={14} /></button>
                <button onClick={() => setEditingId(null)} className="text-[#7A7A71] hover:text-[#2C2C28] p-1"><X size={14} /></button>
              </div>
            ) : (
              <button
                onClick={() => { onSelect(c.id); onCloseMobile(); }}
                className="w-full text-left px-3 py-2 pr-14 rounded-lg text-sm text-[#2C2C28] font-body truncate flex items-center gap-2"
                title={c.title}
              >
                <MessageSquare size={13} className="text-[#7A7A71] shrink-0" />
                <span className="truncate">{c.title}</span>
              </button>
            )}
            {editingId !== c.id && (
              <div className="absolute right-1 top-1/2 -translate-y-1/2 flex opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => { e.stopPropagation(); startEdit(c); }}
                  className="p-1.5 text-[#7A7A71] hover:text-[#D05C42]"
                  data-testid="rename-conversation"
                  aria-label="Rename"
                >
                  <Pencil size={12} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
                  className="p-1.5 text-[#7A7A71] hover:text-[#D05C42]"
                  data-testid="delete-conversation"
                  aria-label="Delete"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-6 border-t border-[#E3E0D8] text-[11px] text-[#7A7A71] font-body leading-relaxed">
        Honest. Direct. Yours.
        <br />Powered by Claude Sonnet 4.5
      </div>
    </aside>
  );
}

function MemoryPanel({ memories, onAdd, onDelete, onEdit, mobileOpen, onCloseMobile }) {
  const [newMem, setNewMem] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const submit = () => {
    if (!newMem.trim()) return;
    onAdd(newMem.trim());
    setNewMem("");
  };

  const commitEdit = () => {
    if (editingId && editValue.trim()) onEdit(editingId, editValue.trim());
    setEditingId(null);
  };

  return (
    <aside
      data-testid="memory-panel"
      className={`${mobileOpen ? "translate-x-0" : "translate-x-full"} md:translate-x-0 fixed md:static z-40 top-0 right-0 w-80 md:w-72 border-l border-[#E3E0D8] bg-[#EEF1EC] h-screen flex flex-col transition-transform duration-300`}
    >
      <div className="p-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-[#D05C42]" />
          <h3 className="font-heading text-lg text-[#2C2C28]">Memory</h3>
        </div>
        <button
          className="md:hidden text-[#7A7A71]"
          onClick={onCloseMobile}
          aria-label="Close memory"
          data-testid="close-memory"
        >
          <X size={18} />
        </button>
      </div>

      <p className="px-6 text-xs text-[#7A7A71] font-body leading-relaxed -mt-2 mb-4">
        What Ember remembers about you. Edit or delete freely — this is yours.
      </p>

      <div className="px-6 pb-4">
        <div className="flex gap-2">
          <input
            data-testid="memory-input"
            value={newMem}
            onChange={(e) => setNewMem(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
            placeholder="Add a fact..."
            className="flex-1 bg-white border border-[#E3E0D8] rounded-lg px-3 py-2 text-sm font-body focus:outline-none focus:border-[#D05C42] placeholder:text-[#A0A095]"
          />
          <button
            data-testid="add-memory-button"
            onClick={submit}
            className="px-3 py-2 rounded-lg bg-[#D05C42] text-white hover:bg-[#BA4C33] transition-colors text-sm font-body"
          >
            <Plus size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {memories.length === 0 && (
          <div className="text-sm text-[#7A7A71] italic font-body">Nothing remembered yet. Start a conversation.</div>
        )}
        {memories.map((m) => (
          <div
            key={m.id}
            data-testid="memory-card"
            className="bg-white/70 backdrop-blur-sm border border-[#E3E0D8] rounded-xl p-3 mb-2 shadow-sm hover:shadow-md transition-shadow group relative"
          >
            {editingId === m.id ? (
              <div className="flex flex-col gap-2">
                <textarea
                  data-testid="memory-edit-input"
                  className="w-full bg-white border border-[#E3E0D8] rounded-md px-2 py-1 text-sm font-body focus:outline-none focus:border-[#D05C42] resize-none"
                  rows={2}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                />
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setEditingId(null)} className="text-xs text-[#7A7A71] px-2 py-1">Cancel</button>
                  <button onClick={commitEdit} data-testid="confirm-memory-edit" className="text-xs text-white bg-[#D05C42] hover:bg-[#BA4C33] px-2 py-1 rounded">Save</button>
                </div>
              </div>
            ) : (
              <>
                <div className="text-sm text-[#2C2C28] font-body leading-relaxed pr-12">{m.content}</div>
                <div className="absolute right-2 top-2 flex opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => { setEditingId(m.id); setEditValue(m.content); }}
                    className="p-1.5 text-[#7A7A71] hover:text-[#D05C42]"
                    data-testid="edit-memory"
                    aria-label="Edit"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={() => onDelete(m.id)}
                    className="p-1.5 text-[#7A7A71] hover:text-[#D05C42]"
                    data-testid="delete-memory"
                    aria-label="Delete"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}

function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");
  const taRef = useRef(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [value]);

  const submit = () => {
    const v = value.trim();
    if (!v || disabled) return;
    onSend(v);
    setValue("");
  };

  return (
    <div className="max-w-3xl mx-auto w-full px-4 md:px-8 pb-6 pt-2">
      <div className="relative flex items-end w-full bg-white rounded-3xl border border-[#E3E0D8] shadow-sm focus-within:ring-2 focus-within:ring-[#D05C42]/20 focus-within:border-[#D05C42] transition-all p-2 pl-5">
        <textarea
          ref={taRef}
          data-testid="chat-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          rows={1}
          placeholder="Say anything. I'm here."
          className="flex-1 max-h-40 min-h-[44px] bg-transparent border-none focus:outline-none resize-none py-3 font-body text-[15px] text-[#2C2C28] placeholder:text-[#A0A095]"
        />
        <button
          data-testid="send-button"
          onClick={submit}
          disabled={disabled || !value.trim()}
          className="w-10 h-10 rounded-full bg-[#D05C42] text-white flex items-center justify-center hover:bg-[#BA4C33] transition-colors shrink-0 m-1 disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Send"
        >
          <Send size={16} />
        </button>
      </div>
      <div className="text-[11px] text-[#A0A095] font-body mt-2 text-center">
        Ember speaks honestly and can still be wrong. Verify anything important.
      </div>
    </div>
  );
}

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [memories, setMemories] = useState([]);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const scrollRef = useRef(null);

  const loadConversations = useCallback(async () => {
    const { data } = await axios.get(`${API}/conversations`);
    setConversations(data);
  }, []);

  const loadMessages = useCallback(async (id) => {
    if (!id) { setMessages([]); return; }
    const { data } = await axios.get(`${API}/conversations/${id}/messages`);
    setMessages(data);
  }, []);

  const loadMemories = useCallback(async () => {
    const { data } = await axios.get(`${API}/memory`);
    setMemories(data);
  }, []);

  useEffect(() => {
    loadConversations();
    loadMemories();
  }, [loadConversations, loadMemories]);

  useEffect(() => {
    loadMessages(currentId);
  }, [currentId, loadMessages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const handleNew = () => {
    setCurrentId(null);
    setMessages([]);
  };

  const handleDelete = async (id) => {
    await axios.delete(`${API}/conversations/${id}`);
    if (currentId === id) {
      setCurrentId(null);
      setMessages([]);
    }
    loadConversations();
  };

  const handleRename = async (id, title) => {
    await axios.patch(`${API}/conversations/${id}`, { title });
    loadConversations();
  };

  const sendMessage = async (text) => {
    if (sending) return;
    setSending(true);
    const optimisticUser = {
      id: `temp-${Date.now()}`,
      conversation_id: currentId || "new",
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimisticUser]);

    try {
      const { data } = await axios.post(`${API}/chat`, {
        conversation_id: currentId,
        message: text,
      });
      const newConvId = data.conversation_id;
      if (!currentId) setCurrentId(newConvId);
      setMessages((m) => {
        const withoutTemp = m.filter((x) => x.id !== optimisticUser.id);
        return [...withoutTemp, data.user_message, data.assistant_message];
      });
      loadConversations();
      // refresh memories after a short delay (extraction is async)
      setTimeout(loadMemories, 2500);
    } catch (e) {
      console.error(e);
      setMessages((m) => [
        ...m,
        {
          id: `err-${Date.now()}`,
          conversation_id: currentId || "new",
          role: "assistant",
          content: "Something went wrong on my end. Try again?",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const addMemory = async (content) => {
    const { data } = await axios.post(`${API}/memory`, { content });
    setMemories((m) => [data, ...m]);
  };

  const deleteMemory = async (id) => {
    await axios.delete(`${API}/memory/${id}`);
    setMemories((m) => m.filter((x) => x.id !== id));
  };

  const editMemory = async (id, content) => {
    const { data } = await axios.patch(`${API}/memory/${id}`, { content });
    setMemories((m) => m.map((x) => (x.id === id ? data : x)));
  };

  return (
    <div className="App flex h-screen w-screen bg-[#F9F8F6] overflow-hidden font-body text-[#2C2C28]">
      <Sidebar
        conversations={conversations}
        currentId={currentId}
        onSelect={setCurrentId}
        onNew={handleNew}
        onDelete={handleDelete}
        onRename={handleRename}
        mobileOpen={sidebarOpen}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col h-screen relative min-w-0">
        {/* Mobile top bar */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-[#E3E0D8] bg-[#F9F8F6]">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-[#2C2C28]"
            data-testid="open-sidebar"
            aria-label="Open sidebar"
          >
            <Menu size={20} />
          </button>
          <div className="font-heading text-lg">Ember</div>
          <button
            onClick={() => setMemoryOpen(true)}
            className="text-[#2C2C28]"
            data-testid="open-memory"
            aria-label="Open memory"
          >
            <Brain size={20} />
          </button>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {messages.length === 0 && !sending ? (
            <EmptyState onQuickStart={sendMessage} />
          ) : (
            <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-10 flex flex-col gap-7">
              {messages.map((m) =>
                m.role === "user" ? (
                  <UserMessage key={m.id} content={m.content} />
                ) : (
                  <AiMessage key={m.id} content={m.content} />
                )
              )}
              {sending && <AiMessage thinking />}
            </div>
          )}
        </div>

        <ChatInput onSend={sendMessage} disabled={sending} />
      </main>

      <MemoryPanel
        memories={memories}
        onAdd={addMemory}
        onDelete={deleteMemory}
        onEdit={editMemory}
        mobileOpen={memoryOpen}
        onCloseMobile={() => setMemoryOpen(false)}
      />

      {/* Mobile overlays */}
      {(sidebarOpen || memoryOpen) && (
        <div
          className="md:hidden fixed inset-0 bg-black/20 z-30"
          onClick={() => { setSidebarOpen(false); setMemoryOpen(false); }}
        />
      )}
    </div>
  );
}

export default App;
