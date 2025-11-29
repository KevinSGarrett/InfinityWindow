import { useEffect, useState, KeyboardEvent } from "react";
import "./App.css";

// ---------- Types ----------

interface Project {
  id: number;
  name: string;
  description?: string | null;
}

interface Conversation {
  id: number;
  project_id: number;
  title?: string | null;
}

interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
}

interface ChatResponse {
  conversation_id: number;
  reply: string;
}

interface MessageSearchHit {
  message_id: number;
  conversation_id: number;
  project_id: number;
  role: string;
  content: string;
  distance: number;
}

interface DocSearchHit {
  chunk_id: number;
  document_id: number;
  project_id: number;
  chunk_index: number;
  content: string;
  distance: number;
}

// ---------- Component ----------

const BACKEND_BASE_URL = "http://127.0.0.1:8000";

function App() {
  // Backend health
  const [backendVersion, setBackendVersion] = useState<string | null>(null);

  // Projects & conversations
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<
    number | null
  >(null);

  // Chat
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  // Memory search (right‑hand panel)
  const [searchTab, setSearchTab] = useState<"messages" | "docs">("messages");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [messageSearchResults, setMessageSearchResults] = useState<
    MessageSearchHit[]
  >([]);
  const [docSearchResults, setDocSearchResults] = useState<DocSearchHit[]>([]);

  // ---------- Helpers ----------

  const currentProject = projects.find((p) => p.id === selectedProjectId);
  const currentConversation = conversations.find(
    (c) => c.id === selectedConversationId
  );

  // ---------- Initial load ----------

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        // Health
        const healthRes = await fetch(`${BACKEND_BASE_URL}/health`);
        if (healthRes.ok) {
          const h = await healthRes.json();
          if (h?.version) {
            setBackendVersion(h.version);
          }
        }

        // Projects
        const projRes = await fetch(`${BACKEND_BASE_URL}/projects`);
        if (projRes.ok) {
          const projJson: Project[] = await projRes.json();
          setProjects(projJson);
          if (projJson.length > 0) {
            const firstId = projJson[0].id;
            setSelectedProjectId(firstId);
          }
        }
      } catch (err) {
        console.error("Error fetching initial data:", err);
      }
    };

    fetchInitial();
  }, []);

  // When project changes, load that project’s conversations
  useEffect(() => {
    const loadConversations = async () => {
      if (!selectedProjectId) return;
      try {
        const res = await fetch(
          `${BACKEND_BASE_URL}/projects/${selectedProjectId}/conversations`
        );
        if (res.ok) {
          const convJson: Conversation[] = await res.json();
          setConversations(convJson);
          if (convJson.length > 0) {
            setSelectedConversationId(convJson[0].id);
          } else {
            setSelectedConversationId(null);
            setMessages([]);
          }
        }
      } catch (err) {
        console.error("Error loading conversations:", err);
      }
    };

    loadConversations();
  }, [selectedProjectId]);

  // When conversation changes, load its messages
  useEffect(() => {
    const loadMessages = async () => {
      if (!selectedConversationId) {
        setMessages([]);
        return;
      }
      try {
        const res = await fetch(
          `${BACKEND_BASE_URL}/conversations/${selectedConversationId}/messages`
        );
        if (res.ok) {
          const msgs: Message[] = await res.json();
          setMessages(msgs);
        }
      } catch (err) {
        console.error("Error loading messages:", err);
      }
    };

    loadMessages();
  }, [selectedConversationId]);

  // ---------- Chat actions ----------

  const handleSend = async () => {
    if (!input.trim()) return;
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }

    setIsSending(true);

    const userText = input.trim();
    setInput("");

    const previousConversationId = selectedConversationId;

    // Optimistic local user message
    const tempUserMessage: Message = {
      id: Date.now(),
      conversation_id: previousConversationId ?? -1,
      role: "user",
      content: userText,
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const res = await fetch(`${BACKEND_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: previousConversationId,
          message: userText,
        }),
      });

      if (!res.ok) {
        throw new Error(`Chat request failed with status ${res.status}`);
      }

      const data: ChatResponse = await res.json();

      // If a new conversation was created, refresh conversation list
      if (!previousConversationId || data.conversation_id !== previousConversationId) {
        setSelectedConversationId(data.conversation_id);

        const convRes = await fetch(
          `${BACKEND_BASE_URL}/projects/${selectedProjectId}/conversations`
        );
        if (convRes.ok) {
          const convJson: Conversation[] = await convRes.json();
          setConversations(convJson);
        }

        // Reload messages for that conversation from the server
        const msgsRes = await fetch(
          `${BACKEND_BASE_URL}/conversations/${data.conversation_id}/messages`
        );
        if (msgsRes.ok) {
          const msgs: Message[] = await msgsRes.json();
          setMessages(msgs);
          return;
        }
      } else {
        // Append assistant reply to messages
        const assistantMessage: Message = {
          id: Date.now() + 1,
          conversation_id: data.conversation_id,
          role: "assistant",
          content: data.reply,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err) {
      console.error("Error sending chat message:", err);
      alert("There was an error talking to the backend. Check the dev console.");
    } finally {
      setIsSending(false);
    }
  };

  const handleInputKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) {
        handleSend();
      }
    }
  };

  const handleNewChat = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    setSelectedConversationId(null);
    setMessages([]);
  };

  // ---------- Memory search actions ----------

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }

    setIsSearching(true);

    try {
      if (searchTab === "messages") {
        const res = await fetch(`${BACKEND_BASE_URL}/search/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: selectedProjectId,
            query: searchQuery.trim(),
            conversation_id: selectedConversationId,
            limit: 10,
          }),
        });

        if (!res.ok) {
          throw new Error(`Message search failed with status ${res.status}`);
        }

        const data: { hits: MessageSearchHit[] } = await res.json();
        setMessageSearchResults(data.hits ?? []);
      } else {
        const res = await fetch(`${BACKEND_BASE_URL}/search/docs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: selectedProjectId,
            query: searchQuery.trim(),
            document_id: null,
            limit: 10,
          }),
        });

        if (!res.ok) {
          throw new Error(`Doc search failed with status ${res.status}`);
        }

        const data: { hits: DocSearchHit[] } = await res.json();
        setDocSearchResults(data.hits ?? []);
      }
    } catch (err) {
      console.error("Error searching memory:", err);
      alert("There was an error searching memory. Check the dev console.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSearching) {
        handleSearch();
      }
    }
  };

  // ---------- Render ----------

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="brand">
          <div className="brand-title">InfinityWindow</div>
          <div className="brand-subtitle">
            Personal AI workbench with long-term memory
          </div>
        </div>
        <div className="backend-status">
          Backend:
          <span className="backend-pill">
            InfinityWindow {backendVersion ?? "loading..."}
          </span>
        </div>
      </header>

      <main className="app-main">
        {/* Left column – Conversations */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>Conversations</h2>
            <button
              className="btn-secondary small"
              type="button"
              onClick={handleNewChat}
            >
              + New chat
            </button>
          </div>

          {currentProject && (
            <div className="project-label">{currentProject.name}</div>
          )}

          {conversations.length === 0 ? (
            <div className="sidebar-empty">
              No conversations yet. Start one using the chat box.
            </div>
          ) : (
            <ul className="conversation-list">
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <button
                    type="button"
                    className={
                      "conversation-item" +
                      (conv.id === selectedConversationId ? " active" : "")
                    }
                    onClick={() => setSelectedConversationId(conv.id)}
                  >
                    {conv.title || `Conversation #${conv.id}`}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Middle column – Chat */}
        <section className="chat-panel">
          {currentConversation ? (
            <div className="chat-header">
              <div className="chat-title">
                {currentConversation.title || "Chat conversation"}
              </div>
            </div>
          ) : (
            <div className="chat-header">
              <div className="chat-title">
                Start a conversation with your InfinityWindow assistant.
              </div>
              <div className="chat-subtitle">
                Your messages and documents are stored and used as context
                automatically.
              </div>
            </div>
          )}

          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-empty">
                No messages yet. Ask something in the box below.
              </div>
            ) : (
              <>
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={
                      "chat-message " +
                      (m.role === "user" ? "from-user" : "from-assistant")
                    }
                  >
                    <div className="chat-message-role">
                      {m.role === "user" ? "You" : "Assistant"}
                    </div>
                    <div className="chat-message-content">{m.content}</div>
                  </div>
                ))}

                {isSending && (
                  <div className="chat-message from-assistant thinking">
                    <div className="chat-message-role">Assistant</div>
                    <div className="chat-message-content">
                      InfinityWindow is thinking…
                    </div>
                  </div>
                )}
              </>
            )}
          </div>


          <div className="chat-input-row">
            <textarea
              className="chat-input"
              placeholder="Ask InfinityWindow something..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              rows={3}
            />
            <button
              className="btn-primary"
              type="button"
              onClick={handleSend}
              disabled={isSending || !input.trim()}
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
        </section>

        {/* Right column – Memory search */}
        <section className="memory-panel">
          <div className="memory-header">
            <h2>Search memory</h2>
          </div>

          <div className="memory-tabs">
            <button
              type="button"
              className={
                "memory-tab" + (searchTab === "messages" ? " active" : "")
              }
              onClick={() => setSearchTab("messages")}
            >
              Messages
            </button>
            <button
              type="button"
              className={
                "memory-tab" + (searchTab === "docs" ? " active" : "")
              }
              onClick={() => setSearchTab("docs")}
            >
              Docs
            </button>
          </div>

          <textarea
            className="memory-input"
            placeholder={
              searchTab === "messages"
                ? "Search in chat history..."
                : "Search in ingested documents..."
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            rows={2}
          />

          <button
            className="btn-secondary full-width"
            type="button"
            onClick={handleSearch}
            disabled={isSearching || !searchQuery.trim()}
          >
            {isSearching ? "Searching..." : "Search"}
          </button>

          <div className="memory-results">
            {searchTab === "messages" ? (
              messageSearchResults.length === 0 ? (
                <div className="memory-empty">
                  No results yet. Try a query.
                </div>
              ) : (
                <ul className="memory-list">
                  {messageSearchResults.map((hit) => (
                    <li key={hit.message_id} className="memory-item">
                      <div className="memory-meta">
                        <span className="memory-tag">
                          Conv #{hit.conversation_id} · {hit.role}
                        </span>
                        <span className="memory-distance">
                          score {hit.distance.toFixed(3)}
                        </span>
                      </div>
                      <div className="memory-content">{hit.content}</div>
                    </li>
                  ))}
                </ul>
              )
            ) : docSearchResults.length === 0 ? (
              <div className="memory-empty">
                No document results yet. Try a query.
              </div>
            ) : (
              <ul className="memory-list">
                {docSearchResults.map((hit) => (
                  <li key={hit.chunk_id} className="memory-item">
                    <div className="memory-meta">
                      <span className="memory-tag">
                        Doc #{hit.document_id} · chunk {hit.chunk_index}
                      </span>
                      <span className="memory-distance">
                        score {hit.distance.toFixed(3)}
                      </span>
                    </div>
                    <div className="memory-content">{hit.content}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
