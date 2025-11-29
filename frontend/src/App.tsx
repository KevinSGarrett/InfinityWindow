import React, { useEffect, useState, KeyboardEvent } from "react";
import "./App.css";

// ---------- Types ----------

type Project = {
  id: number;
  name: string;
  description?: string | null;
};

type Conversation = {
  id: number;
  project_id: number;
  title?: string | null;
};

type Message = {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
};

type ChatResponse = {
  conversation_id: number;
  reply: string;
};

type MessageSearchHit = {
  message_id: number;
  conversation_id: number;
  project_id: number;
  role: string;
  content: string;
  distance: number;
};

type DocSearchHit = {
  chunk_id: number;
  document_id: number;
  project_id: number;
  chunk_index: number;
  content: string;
  distance: number;
};

type ProjectDocument = {
  id: number;
  project_id: number;
  name: string;
  description?: string | null;
};

const BACKEND_BASE = "http://127.0.0.1:8000";

function App() {
  // Backend / projects
  const [backendVersion, setBackendVersion] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );

  // Conversations / messages
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<
    number | null
  >(null);
  const [messages, setMessages] = useState<Message[]>([]);

  // Chat input + mode
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [chatMode, setChatMode] = useState<
    "auto" | "fast" | "deep" | "budget" | "research" | "code"
  >("auto");

  // Project documents
  const [projectDocs, setProjectDocs] = useState<ProjectDocument[]>([]);

  // Text doc ingestion
  const [newDocName, setNewDocName] = useState("");
  const [newDocDescription, setNewDocDescription] = useState("");
  const [newDocText, setNewDocText] = useState("");
  const [isIngestingTextDoc, setIsIngestingTextDoc] = useState(false);

  // Repo ingestion
  const [repoRootPath, setRepoRootPath] = useState("C:\\InfinityWindow");
  const [repoNamePrefix, setRepoNamePrefix] = useState("InfinityWindow/");
  const [isIngestingRepo, setIsIngestingRepo] = useState(false);

  // Search
  const [searchTab, setSearchTab] = useState<"messages" | "docs">("messages");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchMessageHits, setSearchMessageHits] = useState<
    MessageSearchHit[]
  >([]);
  const [searchDocHits, setSearchDocHits] = useState<DocSearchHit[]>([]);

  // Convenience
  const selectedProject =
    projects.find((p) => p.id === selectedProjectId) ?? null;
  const selectedConversation =
    conversations.find((c) => c.id === selectedConversationId) ?? null;

  // ---------- Helpers ----------

  const loadProjectDocs = async (projectId: number) => {
    try {
      const res = await fetch(`${BACKEND_BASE}/projects/${projectId}/docs`);
      if (!res.ok) return;
      const docsJson: ProjectDocument[] = await res.json();
      setProjectDocs(docsJson);
    } catch (e) {
      console.error("Fetching project docs failed:", e);
    }
  };

  const refreshConversations = async (projectId: number) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/conversations`
      );
      if (!res.ok) return;
      const convs: Conversation[] = await res.json();
      setConversations(convs);

      if (convs.length > 0) {
        const existing = convs.find((c) => c.id === selectedConversationId);
        setSelectedConversationId(existing ? existing.id : convs[0].id);
      } else {
        setSelectedConversationId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error("Fetching conversations failed:", e);
    }
  };

  const refreshMessages = async (conversationId: number) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/conversations/${conversationId}/messages`
      );
      if (!res.ok) return;
      const msgs: Message[] = await res.json();
      setMessages(msgs);
    } catch (e) {
      console.error("Fetching messages failed:", e);
    }
  };

  // ---------- Initial load (health + projects) ----------

  useEffect(() => {
    const load = async () => {
      try {
        const healthRes = await fetch(`${BACKEND_BASE}/health`);
        if (healthRes.ok) {
          const h = await healthRes.json();
          if (h?.version) setBackendVersion(h.version);
        }
      } catch (e) {
        console.error("Health check failed:", e);
      }

      try {
        const projRes = await fetch(`${BACKEND_BASE}/projects`);
        if (projRes.ok) {
          const projJson: Project[] = await projRes.json();
          setProjects(projJson);
          if (projJson.length > 0) {
            const firstId = projJson[0].id;
            setSelectedProjectId(firstId);
            // Preload conversations + docs for first project
            refreshConversations(firstId);
            loadProjectDocs(firstId);
          }
        }
      } catch (e) {
        console.error("Fetching projects failed:", e);
      }
    };

    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------- When project changes, load its conversations + docs ----------

  useEffect(() => {
    if (selectedProjectId == null) {
      setConversations([]);
      setMessages([]);
      setProjectDocs([]);
      return;
    }
    refreshConversations(selectedProjectId);
    loadProjectDocs(selectedProjectId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId]);

  // ---------- When conversation changes, load its messages ----------

  useEffect(() => {
    if (selectedConversationId != null) {
      refreshMessages(selectedConversationId);
    } else {
      setMessages([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConversationId]);

  // ---------- Chat handlers ----------

  const handleSend = async () => {
    if (!chatInput.trim()) return;
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }

    const userText = chatInput.trim();
    setChatInput("");
    setIsSending(true);

    const convIdBefore = selectedConversationId;

    // Optimistic user bubble
    const tempUserMsg: Message = {
      id: Date.now(),
      conversation_id: convIdBefore ?? -1,
      role: "user",
      content: userText,
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`${BACKEND_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: convIdBefore,
          message: userText,
          mode: chatMode,
          model: null,
        }),
      });

      if (!res.ok) {
        console.error("Chat error:", res.status);
        alert("Chat failed – check backend logs.");
        return;
      }

      const data: ChatResponse = await res.json();
      const convId = data.conversation_id;

      if (!convIdBefore || convIdBefore !== convId) {
        setSelectedConversationId(convId);

        if (selectedProjectId != null) {
          await refreshConversations(selectedProjectId);
        }
      }

      await refreshMessages(convId);
    } catch (e) {
      console.error("Chat request threw:", e);
      alert("Unexpected error talking to backend. See console.");
    } finally {
      setIsSending(false);
    }
  };

  const handleChatKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) {
        handleSend();
      }
    }
  };

  const handleNewChatClick = () => {
    setSelectedConversationId(null);
    setMessages([]);
  };

  const handleProjectChange: React.ChangeEventHandler<HTMLSelectElement> = (
    e
  ) => {
    const val = e.target.value;
    if (!val) {
      setSelectedProjectId(null);
      setConversations([]);
      setSelectedConversationId(null);
      setMessages([]);
      setProjectDocs([]);
      return;
    }
    setSelectedProjectId(parseInt(val, 10));
  };

  // ---------- Text doc ingestion handlers ----------

  const handleIngestTextDoc = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!newDocName.trim()) {
      alert("Please enter a document name.");
      return;
    }
    if (!newDocText.trim()) {
      alert("Please enter some document text.");
      return;
    }

    setIsIngestingTextDoc(true);
    try {
      const res = await fetch(`${BACKEND_BASE}/docs/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId,
          name: newDocName.trim(),
          description: newDocDescription.trim() || null,
          text: newDocText,
        }),
      });

      if (!res.ok) {
        console.error("Ingest text doc failed:", res.status);
        alert("Text document ingestion failed; see backend logs.");
        return;
      }

      // Clear fields and refresh docs
      setNewDocName("");
      setNewDocDescription("");
      setNewDocText("");
      await loadProjectDocs(selectedProjectId);
    } catch (e) {
      console.error("Ingest text doc threw:", e);
      alert("Unexpected error while ingesting text document.");
    } finally {
      setIsIngestingTextDoc(false);
    }
  };

  // ---------- Repo ingestion handlers ----------

  const handleIngestRepo = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!repoRootPath.trim()) {
      alert("Please enter a repo root path.");
      return;
    }

    setIsIngestingRepo(true);
    try {
      const res = await fetch(`${BACKEND_BASE}/github/ingest_local_repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId,
          root_path: repoRootPath.trim(),
          name_prefix: repoNamePrefix.trim() || "",
          include_globs: null,
        }),
      });

      if (!res.ok) {
        console.error("Repo ingestion failed:", res.status);
        alert("Repo ingestion failed; see backend logs.");
        return;
      }

      await loadProjectDocs(selectedProjectId);
    } catch (e) {
      console.error("Repo ingestion threw:", e);
      alert("Unexpected error while ingesting repo.");
    } finally {
      setIsIngestingRepo(false);
    }
  };

  // ---------- Search handlers ----------

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }

    setIsSearching(true);

    try {
      if (searchTab === "messages") {
        const res = await fetch(`${BACKEND_BASE}/search/messages`, {
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
          console.error("Search messages failed:", res.status);
          return;
        }

        const data: { hits: MessageSearchHit[] } = await res.json();
        setSearchMessageHits(data.hits ?? []);
      } else {
        const res = await fetch(`${BACKEND_BASE}/search/docs`, {
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
          console.error("Search docs failed:", res.status);
          return;
        }

        const data: { hits: DocSearchHit[] } = await res.json();
        setSearchDocHits(data.hits ?? []);
      }
    } catch (e) {
      console.error("Search threw:", e);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isSearching) handleSearch();
    }
  };

  // ---------- Render ----------

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-title-block">
          <h1 className="app-title">InfinityWindow</h1>
          <div className="app-subtitle">
            Personal AI workbench with long-term memory
          </div>
        </div>
        <div className="app-header-right">
          <div className="backend-pill">
            Backend:{" "}
            <span className="backend-pill-version">
              {backendVersion ? `InfinityWindow v${backendVersion}` : "…"}
            </span>
          </div>
        </div>
      </header>

      <main className="app-main">
        {/* LEFT: Projects + conversations */}
        <section className="column column-left">
          <div className="left-header">
            <div className="left-header-title">Conversations</div>
            <button
              className="btn-primary small"
              type="button"
              onClick={handleNewChatClick}
            >
              + New chat
            </button>
          </div>

          <div className="project-selector">
            <div className="project-label">Project</div>
            <select
              value={selectedProjectId ?? ""}
              onChange={handleProjectChange}
            >
              {projects.length === 0 && (
                <option value="">(No projects found)</option>
              )}
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            {selectedProject && selectedProject.description && (
              <div className="project-description">
                {selectedProject.description}
              </div>
            )}
          </div>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="conversation-empty">
                No conversations yet. Start a new chat.
              </div>
            ) : (
              <ul>
                {conversations.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      className={
                        "conversation-item" +
                        (c.id === selectedConversationId ? " active" : "")
                      }
                      onClick={() => setSelectedConversationId(c.id)}
                    >
                      {c.title || `Chat conversation #${c.id}`}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* MIDDLE: Chat */}
        <section className="column column-middle">
          <div className="chat-header">
            {selectedConversation
              ? selectedConversation.title || "Chat conversation"
              : "Start a conversation with your InfinityWindow assistant."}
          </div>

          <div className="chat-messages">
            {messages.length === 0 && !isSending ? (
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
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
            />
            <div className="chat-right-controls">
              <div className="chat-mode-selector">
                <label>Mode</label>
                <select
                  value={chatMode}
                  onChange={(e) =>
                    setChatMode(
                      e.target.value as
                        | "auto"
                        | "fast"
                        | "deep"
                        | "budget"
                        | "research"
                        | "code"
                    )
                  }
                >
                  <option value="auto">Auto</option>
                  <option value="fast">Fast</option>
                  <option value="deep">Deep</option>
                  <option value="budget">Budget</option>
                  <option value="research">Research</option>
                  <option value="code">Code</option>
                </select>
              </div>
              <button
                className="btn-primary"
                type="button"
                onClick={handleSend}
                disabled={isSending || !chatInput.trim()}
              >
                {isSending ? "Sending…" : "Send"}
              </button>
            </div>
          </div>
        </section>

        {/* RIGHT: Docs + ingestion + search */}
        <section className="column column-right">
          {/* Project documents */}
          <div className="docs-header">Project documents</div>
          <div className="project-docs-list">
            {selectedProjectId == null ? (
              <div className="docs-empty">No project selected.</div>
            ) : projectDocs.length === 0 ? (
              <div className="docs-empty">
                No documents yet. Ingest one below.
              </div>
            ) : (
              <ul>
                {projectDocs.map((doc) => (
                  <li key={doc.id} className="project-doc-item">
                    <div className="project-doc-name">{doc.name}</div>
                    {doc.description && (
                      <div className="project-doc-description">
                        {doc.description}
                      </div>
                    )}
                    <div className="project-doc-id">Doc ID {doc.id}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Ingest text document */}
          <div className="ingest-section">
            <div className="ingest-title">Ingest text document</div>
            <div className="ingest-textdoc-form">
              <input
                className="ingest-input"
                type="text"
                placeholder="Name"
                value={newDocName}
                onChange={(e) => setNewDocName(e.target.value)}
              />
              <input
                className="ingest-input"
                type="text"
                placeholder="Description (optional)"
                value={newDocDescription}
                onChange={(e) => setNewDocDescription(e.target.value)}
              />
              <textarea
                className="ingest-textarea"
                placeholder="Paste document text here..."
                value={newDocText}
                onChange={(e) => setNewDocText(e.target.value)}
              />
              <button
                className="btn-secondary"
                type="button"
                onClick={handleIngestTextDoc}
                disabled={isIngestingTextDoc}
              >
                {isIngestingTextDoc ? "Ingesting…" : "Ingest text doc"}
              </button>
            </div>
          </div>

          {/* Ingest local repo */}
          <div className="ingest-section">
            <div className="ingest-title">Ingest local repo</div>
            <div className="ingest-repo-form">
              <input
                className="ingest-input"
                type="text"
                placeholder="Root path (e.g. C:\\InfinityWindow)"
                value={repoRootPath}
                onChange={(e) => setRepoRootPath(e.target.value)}
              />
              <input
                className="ingest-input"
                type="text"
                placeholder="Name prefix (e.g. InfinityWindow/)"
                value={repoNamePrefix}
                onChange={(e) => setRepoNamePrefix(e.target.value)}
              />
              <button
                className="btn-secondary"
                type="button"
                onClick={handleIngestRepo}
                disabled={isIngestingRepo}
              >
                {isIngestingRepo ? "Ingesting…" : "Ingest repo"}
              </button>
            </div>
          </div>

          {/* Search memory */}
          <div className="search-header">Search memory</div>

          <div className="search-tabs">
            <button
              className={
                "search-tab" + (searchTab === "messages" ? " active" : "")
              }
              type="button"
              onClick={() => setSearchTab("messages")}
            >
              Messages
            </button>
            <button
              className={
                "search-tab" + (searchTab === "docs" ? " active" : "")
              }
              type="button"
              onClick={() => setSearchTab("docs")}
            >
              Docs
            </button>
          </div>

          <div className="search-box">
            <textarea
              className="search-input"
              placeholder={
                searchTab === "messages"
                  ? "Search in chat history..."
                  : "Search in ingested documents..."
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
            <button
              className="btn-secondary"
              type="button"
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
            >
              {isSearching ? "Searching…" : "Search"}
            </button>
          </div>

          <div className="search-results">
            {searchTab === "messages" ? (
              searchMessageHits.length === 0 ? (
                <div className="search-empty">
                  No message results yet. Try a query.
                </div>
              ) : (
                <ul>
                  {searchMessageHits.map((hit) => (
                    <li key={hit.message_id} className="search-result-item">
                      <div className="search-result-meta">
                        Conversation {hit.conversation_id} · {hit.role}
                      </div>
                      <div className="search-result-content">
                        {hit.content}
                      </div>
                      <div className="search-result-distance">
                        distance {hit.distance.toFixed(3)}
                      </div>
                    </li>
                  ))}
                </ul>
              )
            ) : searchDocHits.length === 0 ? (
              <div className="search-empty">
                No doc results yet. Try a query.
              </div>
            ) : (
              <ul>
                {searchDocHits.map((hit) => (
                  <li key={hit.chunk_id} className="search-result-item">
                    <div className="search-result-meta">
                      Doc {hit.document_id} · chunk {hit.chunk_index}
                    </div>
                    <div className="search-result-content">
                      {hit.content}
                    </div>
                    <div className="search-result-distance">
                      distance {hit.distance.toFixed(3)}
                    </div>
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
