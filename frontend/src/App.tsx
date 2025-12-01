import React, { useEffect, useState, KeyboardEvent } from "react";
import "./App.css";

// ---------- Types ----------

type Project = {
  id: number;
  name: string;
  description?: string | null;
  instruction_text?: string | null;
  instruction_updated_at?: string | null;
  local_root_path?: string | null;
};

type Conversation = {
  id: number;
  project_id: number;
  title?: string | null;
  folder_id?: number | null;
  folder_name?: string | null;
  folder_color?: string | null;
};
type ConversationFolder = {
  id: number;
  project_id: number;
  name: string;
  color?: string | null;
  sort_order: number;
  is_default: boolean;
  is_archived: boolean;
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

type Task = {
  id: number;
  project_id: number;
  description: string;
  status: string; // "open" | "done"
};

type UsageRecord = {
  id: number;
  project_id: number;
  conversation_id: number | null;
  message_id: number | null;
  model: string;
  tokens_in: number | null;
  tokens_out: number | null;
  cost_estimate: number | null;
  created_at: string;
};

type ConversationUsage = {
  conversation_id: number;
  total_tokens_in: number | null;
  total_tokens_out: number | null;
  total_cost_estimate: number | null;
  records: UsageRecord[];
};

type ProjectDecision = {
  id: number;
  project_id: number;
  title: string;
  details?: string | null;
  category?: string | null;
  source_conversation_id?: number | null;
  created_at: string;
};

type FileEditProposal = {
  type: "file_edit_proposal";
  file_path: string;
  instruction: string;
  reason: string;
};

type TerminalCommandProposal = {
  type: "terminal_command_proposal";
  cwd?: string | null;
  command: string;
  reason?: string | null;
};

type TerminalRunResult = {
  project_id: number;
  cwd: string | null;
  command: string;
  exit_code: number | null;
  stdout: string;
  stderr: string;
  started_at?: string;
  finished_at?: string;
  duration_seconds?: number;
  timed_out?: boolean;
};

// Filesystem types
type FileEntry = {
  name: string;
  is_dir: boolean;
  size: number | null;
  modified_at: string;
  rel_path: string;
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

  // Renaming conversation
  const [renamingConversationId, setRenamingConversationId] = useState<
    number | null
  >(null);
  const [renameTitle, setRenameTitle] = useState("");

  // Conversation folders
  const [folders, setFolders] = useState<ConversationFolder[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<
    number | "all" | "none"
  >("all");
  const [isLoadingFolders, setIsLoadingFolders] = useState(false);
  const [folderModalOpen, setFolderModalOpen] = useState(false);
  const [editingFolder, setEditingFolder] =
    useState<ConversationFolder | null>(null);
  const [folderFormName, setFolderFormName] = useState("");
  const [folderFormColor, setFolderFormColor] = useState("#4F46E5");
  const [folderFormSortOrder, setFolderFormSortOrder] = useState(0);
  const [folderFormIsDefault, setFolderFormIsDefault] = useState(false);
  const [folderFormIsArchived, setFolderFormIsArchived] = useState(false);
  const [folderFormError, setFolderFormError] = useState<string | null>(null);

  // Chat input + mode
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [chatMode, setChatMode] = useState<
    "auto" | "fast" | "deep" | "budget" | "research" | "code"
  >("auto");

  // Project documents
  const [projectDocs, setProjectDocs] = useState<ProjectDocument[]>([]);

  // Project tasks
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [isSavingTask, setIsSavingTask] = useState(false);

  // Usage (per conversation)
  const [usage, setUsage] = useState<ConversationUsage | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

  // Project instructions
  const [projectInstructions, setProjectInstructions] = useState("");
  const [projectInstructionsUpdatedAt, setProjectInstructionsUpdatedAt] =
    useState<string | null>(null);
  const [isSavingInstructions, setIsSavingInstructions] = useState(false);
  const [projectInstructionsError, setProjectInstructionsError] =
    useState<string | null>(null);

  // Project decisions
  const [projectDecisions, setProjectDecisions] = useState<ProjectDecision[]>(
    []
  );
  const [newDecisionTitle, setNewDecisionTitle] = useState("");
  const [newDecisionDetails, setNewDecisionDetails] = useState("");
  const [newDecisionCategory, setNewDecisionCategory] = useState("");
  const [linkDecisionToConversation, setLinkDecisionToConversation] =
    useState(true);
  const [isSavingDecision, setIsSavingDecision] = useState(false);
  const [decisionsError, setDecisionsError] = useState<string | null>(null);

  // AI file edit proposals
  const [fileEditProposal, setFileEditProposal] =
    useState<FileEditProposal | null>(null);
  const [isApplyingFileEdit, setIsApplyingFileEdit] = useState(false);
  const [fileEditStatus, setFileEditStatus] = useState<string | null>(null);

  // AI terminal command proposals + results
  const [terminalProposal, setTerminalProposal] =
    useState<TerminalCommandProposal | null>(null);
  const [isRunningTerminalCommand, setIsRunningTerminalCommand] =
    useState(false);
  const [terminalResult, setTerminalResult] =
    useState<TerminalRunResult | null>(null);
  const [terminalError, setTerminalError] = useState<string | null>(null);
  const [manualTerminalCwd, setManualTerminalCwd] = useState("");
  const [manualTerminalCommand, setManualTerminalCommand] = useState("");
  const [manualTerminalSendToChat, setManualTerminalSendToChat] =
    useState(true);
  const [isRunningManualTerminal, setIsRunningManualTerminal] =
    useState(false);
  const [manualTerminalError, setManualTerminalError] = useState<
    string | null
  >(null);

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

  // Filesystem / project files
  const [fsEntries, setFsEntries] = useState<FileEntry[]>([]);
  const [fsRoot, setFsRoot] = useState<string | null>(null);
  const [fsCurrentSubpath, setFsCurrentSubpath] = useState<string>(""); // param we send to API
  const [fsDisplayPath, setFsDisplayPath] = useState<string>(""); // label from backend
  const [fsSelectedRelPath, setFsSelectedRelPath] = useState<string | null>(
    null
  );
  const [fsOriginalContent, setFsOriginalContent] = useState<string>("");
  const [fsEditedContent, setFsEditedContent] = useState<string>("");
  const [fsIsLoadingList, setFsIsLoadingList] = useState(false);
  const [fsIsLoadingFile, setFsIsLoadingFile] = useState(false);
  const [fsIsSavingFile, setFsIsSavingFile] = useState(false);
  const [fsError, setFsError] = useState<string | null>(null);
  const [fsShowOriginal, setFsShowOriginal] = useState(false);

  // Right‑column workbench tab
  const [rightTab, setRightTab] = useState<
    "tasks" | "docs" | "files" | "search" | "terminal" | "usage" | "notes"
  >("tasks");

  const hasUnsavedFileChanges =
    fsSelectedRelPath != null && fsEditedContent !== fsOriginalContent;

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

  const loadFolders = async (projectId: number) => {
    setIsLoadingFolders(true);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/conversation_folders`
      );
      if (!res.ok) {
        console.error("Fetching folders failed:", res.status);
        setFolders([]);
        return;
      }
      const data: ConversationFolder[] = await res.json();
      setFolders(data);
      if (
        selectedFolderId !== "all" &&
        !data.some((folder) => folder.id === selectedFolderId)
      ) {
        setSelectedFolderId("all");
      }
    } catch (e) {
      console.error("Fetching folders threw:", e);
      setFolders([]);
    } finally {
      setIsLoadingFolders(false);
    }
  };


  const loadTasks = async (projectId: number) => {
    try {
      const res = await fetch(`${BACKEND_BASE}/projects/${projectId}/tasks`);
      if (!res.ok) return;
      const data: Task[] = await res.json();
      setTasks(data);
    } catch (e) {
      console.error("Fetching tasks failed:", e);
    }
  };

  const loadProjectInstructions = async (projectId: number) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/instructions`
      );
      if (!res.ok) {
        setProjectInstructions("");
        setProjectInstructionsUpdatedAt(null);
        return;
      }
      const data: {
        project_id: number;
        instruction_text?: string | null;
        instruction_updated_at?: string | null;
      } = await res.json();
      setProjectInstructions(data.instruction_text ?? "");
      setProjectInstructionsUpdatedAt(data.instruction_updated_at ?? null);
      setProjectInstructionsError(null);
    } catch (e) {
      console.error("Fetching project instructions failed:", e);
      setProjectInstructions("");
      setProjectInstructionsUpdatedAt(null);
    }
  };

  const handleSaveInstructions = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    setIsSavingInstructions(true);
    setProjectInstructionsError(null);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/instructions`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            instruction_text: projectInstructions,
          }),
        }
      );
      if (!res.ok) {
        console.error("Saving instructions failed:", res.status);
        setProjectInstructionsError("Failed to save instructions.");
        return;
      }
      const data = await res.json();
      setProjectInstructions(data.instruction_text ?? "");
      setProjectInstructionsUpdatedAt(data.instruction_updated_at ?? null);
    } catch (e) {
      console.error("Saving instructions threw:", e);
      setProjectInstructionsError("Unexpected error while saving.");
    } finally {
      setIsSavingInstructions(false);
    }
  };

  const loadProjectDecisions = async (projectId: number) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/decisions`
      );
      if (!res.ok) {
        console.error("Fetching decisions failed:", res.status);
        setProjectDecisions([]);
        return;
      }
      const data: ProjectDecision[] = await res.json();
      setProjectDecisions(data);
      setDecisionsError(null);
    } catch (e) {
      console.error("Fetching decisions threw:", e);
      setProjectDecisions([]);
    }
  };

  const handleAddDecision = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    const title = newDecisionTitle.trim();
    if (!title) {
      alert("Decision title cannot be empty.");
      return;
    }
    setIsSavingDecision(true);
    setDecisionsError(null);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/decisions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            details: newDecisionDetails.trim() || null,
            category: newDecisionCategory.trim() || null,
            source_conversation_id:
              linkDecisionToConversation && selectedConversationId
                ? selectedConversationId
                : null,
          }),
        }
      );
      if (!res.ok) {
        console.error("Creating decision failed:", res.status);
        setDecisionsError("Failed to save decision.");
        return;
      }
      await loadProjectDecisions(selectedProjectId);
      setNewDecisionTitle("");
      setNewDecisionDetails("");
      setNewDecisionCategory("");
    } catch (e) {
      console.error("Creating decision threw:", e);
      setDecisionsError("Unexpected error while saving decision.");
    } finally {
      setIsSavingDecision(false);
    }
  };

  const loadUsageForConversation = async (conversationId: number) => {
    try {
      setIsLoadingUsage(true);
      const res = await fetch(
        `${BACKEND_BASE}/conversations/${conversationId}/usage`
      );
      if (!res.ok) {
        console.error("Fetching usage failed:", res.status);
        setUsage(null);
        return;
      }
      const data: ConversationUsage = await res.json();
      setUsage(data);
    } catch (e) {
      console.error("Fetching usage threw:", e);
      setUsage(null);
    } finally {
      setIsLoadingUsage(false);
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
        setUsage(null);
        setFileEditProposal(null);
        setFileEditStatus(null);
        setTerminalProposal(null);
        setTerminalResult(null);
        setTerminalError(null);
      }
    } catch (e) {
      console.error("Fetching conversations failed:", e);
    }
  };

  const extractAiProposals = (msgs: Message[]) => {
    // Look at the latest assistant message only
    const lastAssistant = [...msgs]
      .reverse()
      .find((m) => m.role === "assistant");

    setFileEditProposal(null);
    setFileEditStatus(null);
    setTerminalProposal(null);
    setTerminalError(null);

    if (!lastAssistant) {
      return;
    }

    const text = lastAssistant.content.trim();
    const start = text.lastIndexOf("{");
    const end = text.lastIndexOf("}");

    if (start === -1 || end === -1 || end <= start) {
      return;
    }

    const snippet = text.slice(start, end + 1);

    try {
      const parsed = JSON.parse(snippet);
      if (parsed && parsed.type === "file_edit_proposal") {
        setFileEditProposal(parsed as FileEditProposal);
      } else if (parsed && parsed.type === "terminal_command_proposal") {
        setTerminalProposal(parsed as TerminalCommandProposal);
      }
    } catch (err) {
      console.error("Failed to parse AI proposal JSON:", err);
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
      extractAiProposals(msgs);
    } catch (e) {
      console.error("Fetching messages failed:", e);
    }
  };

  // ---------- Filesystem helpers ----------

  const loadProjectFiles = async (
    projectId: number,
    subpath: string = ""
  ): Promise<void> => {
    setFsIsLoadingList(true);
    setFsError(null);
    try {
      const params = new URLSearchParams();
      if (subpath) params.append("subpath", subpath);
      const url =
        params.toString().length > 0
          ? `${BACKEND_BASE}/projects/${projectId}/fs/list?${params.toString()}`
          : `${BACKEND_BASE}/projects/${projectId}/fs/list`;
      const res = await fetch(url);
      if (!res.ok) {
        console.error("Fetching project files failed:", res.status);
        let detail = "";
        try {
          const body = await res.json();
          if (body && typeof body.detail === "string") {
            detail = body.detail;
          }
        } catch {
          // ignore
        }
        setFsEntries([]);
        setFsRoot(null);
        setFsDisplayPath("");
        setFsError(
          detail || "Project filesystem is not available for this project."
        );
        return;
      }
      const data: {
        root: string;
        path: string;
        entries: FileEntry[];
      } = await res.json();
      setFsRoot(data.root);
      setFsEntries(data.entries ?? []);
      setFsDisplayPath(data.path ?? "");
      setFsCurrentSubpath(subpath);
    } catch (e) {
      console.error("Fetching project files threw:", e);
      setFsEntries([]);
      setFsRoot(null);
      setFsDisplayPath("");
      setFsError("Failed to load project files.");
    } finally {
      setFsIsLoadingList(false);
    }
  };

  const readProjectFile = async (
    projectId: number,
    relPath: string
  ): Promise<void> => {
    setFsIsLoadingFile(true);
    setFsError(null);
    try {
      const params = new URLSearchParams();
      params.append("file_path", relPath);
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/fs/read?${params.toString()}`
      );
      if (!res.ok) {
        console.error("Read file failed:", res.status);
        let detail = "";
        try {
          const body = await res.json();
          if (body && typeof body.detail === "string") {
            detail = body.detail;
          }
        } catch {
          // ignore
        }
        setFsError(detail || "Failed to read file.");
        return;
      }
      const data: { root: string; path: string; content: string } =
        await res.json();
      setFsRoot(data.root);
      setFsSelectedRelPath(relPath);
      setFsOriginalContent(data.content ?? "");
      setFsEditedContent(data.content ?? "");
      setFsShowOriginal(false);
    } catch (e) {
      console.error("Read file threw:", e);
      setFsError("Failed to read file.");
    } finally {
      setFsIsLoadingFile(false);
    }
  };

  const handleOpenFsEntry = async (entry: FileEntry) => {
    if (!selectedProjectId) return;
    if (entry.is_dir) {
      await loadProjectFiles(selectedProjectId, entry.rel_path);
      // Navigating clears file selection
      setFsSelectedRelPath(null);
      setFsOriginalContent("");
      setFsEditedContent("");
      setFsShowOriginal(false);
    } else {
      await readProjectFile(selectedProjectId, entry.rel_path);
    }
  };

  const handleFsUp = async () => {
    if (!selectedProjectId) return;
    if (!fsCurrentSubpath) return; // already at root
    const segments = fsCurrentSubpath.split(/[\\/]+/).filter(Boolean);
    if (segments.length <= 1) {
      await loadProjectFiles(selectedProjectId, "");
    } else {
      const parent = segments.slice(0, -1).join("/");
      await loadProjectFiles(selectedProjectId, parent);
    }
    setFsSelectedRelPath(null);
    setFsOriginalContent("");
    setFsEditedContent("");
    setFsShowOriginal(false);
  };

  const handleFsRefresh = async () => {
    if (!selectedProjectId) return;
    await loadProjectFiles(selectedProjectId, fsCurrentSubpath);
  };

  const handleSaveFile = async () => {
    if (!selectedProjectId || !fsSelectedRelPath) return;
    if (!hasUnsavedFileChanges) return;

    setFsIsSavingFile(true);
    setFsError(null);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/fs/write`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            file_path: fsSelectedRelPath,
            content: fsEditedContent,
            create_dirs: false,
          }),
        }
      );
      if (!res.ok) {
        console.error("Write file failed:", res.status);
        let detail = "";
        try {
          const body = await res.json();
          if (body && typeof body.detail === "string") {
            detail = body.detail;
          }
        } catch {
          // ignore
        }
        setFsError(detail || "Failed to save file.");
        return;
      }
      setFsOriginalContent(fsEditedContent);
      if (selectedProjectId != null) {
        await loadProjectFiles(selectedProjectId, fsCurrentSubpath);
      }
    } catch (e) {
      console.error("Write file threw:", e);
      setFsError("Failed to save file.");
    } finally {
      setFsIsSavingFile(false);
    }
  };

  const handleApplyFileEdit = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!fileEditProposal) {
      alert("No AI file edit proposal to apply.");
      return;
    }

    setIsApplyingFileEdit(true);
    setFileEditStatus(null);

    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/fs/ai_edit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            file_path: fileEditProposal.file_path,
            instruction: fileEditProposal.instruction,
            model: null,
            mode: "code",
            apply_changes: true,
            conversation_id: selectedConversationId,
            message_id: null,
          }),
        }
      );

      if (!res.ok) {
        console.error("AI file edit failed:", res.status);
        setFileEditStatus("AI edit failed. See backend logs.");
        return;
      }

      const data = await res.json();

      if (data.applied) {
        setFileEditStatus(
          `Applied edit to ${data.path || fileEditProposal.file_path}.`
        );
        // Optional: refresh file list if it might affect sizes / timestamps
        if (selectedProjectId != null) {
          await loadProjectFiles(selectedProjectId, fsCurrentSubpath);
        }
      } else {
        setFileEditStatus(
          "AI returned an edit but it was not applied (applied=false)."
        );
      }
    } catch (e) {
      console.error("AI file edit threw:", e);
      setFileEditStatus("Unexpected error while applying AI edit.");
    } finally {
      setIsApplyingFileEdit(false);
    }
  };

  const handleDismissFileEditProposal = () => {
    setFileEditProposal(null);
    setFileEditStatus(null);
  };

  // ---------- Terminal + AI follow‑up helpers ----------

  const sendTerminalOutputToChat = async (messageText: string) => {
    if (!selectedProjectId || !selectedConversationId) {
      // No conversation to attach to; still show result in terminal panel.
      return;
    }

    setIsSending(true);

    const convIdBefore = selectedConversationId;

    try {
      const res = await fetch(`${BACKEND_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId,
          conversation_id: convIdBefore,
          message: messageText,
          mode: chatMode,
          model: null,
        }),
      });

      if (!res.ok) {
        console.error("Chat (terminal follow-up) error:", res.status);
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
      await loadUsageForConversation(convId);
    } catch (e) {
      console.error("Chat (terminal follow-up) request threw:", e);
    } finally {
      setIsSending(false);
    }
  };

  const handleRunTerminalProposal = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!selectedConversationId) {
      alert("No conversation selected.");
      return;
    }
    if (!terminalProposal) {
      alert("No AI terminal command proposal to run.");
      return;
    }

    setIsRunningTerminalCommand(true);
    setTerminalError(null);

    const body = {
      project_id: selectedProjectId,
      cwd: terminalProposal.cwd ?? "",
      command: terminalProposal.command,
      timeout_seconds: 120,
    };

    try {
      const res = await fetch(`${BACKEND_BASE}/terminal/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        console.error("Terminal run failed:", res.status);
        let detail = "";
        try {
          const errBody = await res.json();
          if (errBody && typeof errBody.detail === "string") {
            detail = errBody.detail;
          }
        } catch {
          // ignore
        }
        setTerminalError(detail || "Failed to run terminal command.");
        return;
      }

      const data: TerminalRunResult = await res.json();
      setTerminalResult(data);

      // Step 3.5: feed the output back into the conversation automatically
      const stdout = data.stdout || "";
      const stderr = data.stderr || "";
      const MAX_STDOUT = 4000;

      let stdoutSnippet = stdout;
      let truncated = false;

      if (stdoutSnippet.length > MAX_STDOUT) {
        stdoutSnippet =
          stdoutSnippet.slice(0, MAX_STDOUT) +
          "\n...[stdout truncated]...";
        truncated = true;
      }

      let summaryMessage =
        "I ran the terminal command you proposed.\n\n" +
        `Command: ${data.command}\n` +
        `CWD: ${data.cwd && data.cwd.trim() ? data.cwd : "(project root)"}\n` +
        `Exit code: ${data.exit_code}\n\n` +
        "STDOUT:\n" +
        (stdoutSnippet || "(no stdout)") +
        "\n\n" +
        "STDERR:\n" +
        (stderr || "(no stderr)");

      if (truncated) {
        summaryMessage +=
          "\n\n(Note: stdout was truncated when sending it back to you in this message.)";
      }

      await sendTerminalOutputToChat(summaryMessage);
    } catch (e) {
      console.error("Terminal run threw:", e);
      setTerminalError("Unexpected error while running terminal command.");
    } finally {
      setIsRunningTerminalCommand(false);
    }
  };

  const handleRunManualTerminalCommand = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!manualTerminalCommand.trim()) {
      alert("Enter a terminal command to run.");
      return;
    }
    if (manualTerminalSendToChat && !selectedConversationId) {
      alert(
        "Select a conversation (or uncheck “Send output to chat”) before sending results back to the assistant."
      );
      return;
    }

    setIsRunningManualTerminal(true);
    setManualTerminalError(null);

    const body = {
      project_id: selectedProjectId,
      cwd: manualTerminalCwd.trim(),
      command: manualTerminalCommand.trim(),
      timeout_seconds: 120,
    };

    try {
      const res = await fetch(`${BACKEND_BASE}/terminal/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        console.error("Manual terminal run failed:", res.status);
        let detail = "";
        try {
          const errBody = await res.json();
          if (errBody && typeof errBody.detail === "string") {
            detail = errBody.detail;
          }
        } catch {
          // ignore
        }
        setManualTerminalError(
          detail || "Failed to run manual terminal command."
        );
        return;
      }

      const data: TerminalRunResult = await res.json();
      setTerminalResult(data);

      if (manualTerminalSendToChat && selectedConversationId) {
        const stdout = data.stdout || "";
        const stderr = data.stderr || "";
        const MAX_STDOUT = 4000;
        let stdoutSnippet = stdout;
        let truncated = false;

        if (stdoutSnippet.length > MAX_STDOUT) {
          stdoutSnippet =
            stdoutSnippet.slice(0, MAX_STDOUT) + "\n...[stdout truncated]...";
          truncated = true;
        }

        let summaryMessage =
          "I ran a manual terminal command from the workbench.\n\n" +
          `Command: ${data.command}\n` +
          `CWD: ${data.cwd && data.cwd.trim() ? data.cwd : "(project root)"}\n` +
          `Exit code: ${data.exit_code}\n\n` +
          "STDOUT:\n" +
          (stdoutSnippet || "(no stdout)") +
          "\n\n" +
          "STDERR:\n" +
          (stderr || "(no stderr)");

        if (truncated) {
          summaryMessage +=
            "\n\n(Note: stdout was truncated when sending it back to you in this message.)";
        }

        await sendTerminalOutputToChat(summaryMessage);
      }
    } catch (e) {
      console.error("Manual terminal run threw:", e);
      setManualTerminalError(
        "Unexpected error while running manual terminal command."
      );
    } finally {
      setIsRunningManualTerminal(false);
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
            // Preload for first project
            refreshConversations(firstId);
            loadProjectDocs(firstId);
            loadTasks(firstId);
            loadProjectFiles(firstId, "");
          }
        }
      } catch (e) {
        console.error("Fetching projects failed:", e);
      }
    };

    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------- When project changes, load its conversations + docs + tasks + files ----------

  useEffect(() => {
    if (selectedProjectId == null) {
      setConversations([]);
      setMessages([]);
      setProjectDocs([]);
      setTasks([]);
      setUsage(null);
      setFolders([]);
      setSelectedFolderId("all");

      setFileEditProposal(null);
      setFileEditStatus(null);
      setTerminalProposal(null);
      setTerminalResult(null);
      setTerminalError(null);

      setProjectInstructions("");
      setProjectInstructionsUpdatedAt(null);
      setProjectInstructionsError(null);
      setProjectDecisions([]);
      setDecisionsError(null);

      // Clear filesystem state
      setFsEntries([]);
      setFsRoot(null);
      setFsCurrentSubpath("");
      setFsDisplayPath("");
      setFsSelectedRelPath(null);
      setFsOriginalContent("");
      setFsEditedContent("");
      setFsShowOriginal(false);
      setFsError(null);
      return;
    }
    refreshConversations(selectedProjectId);
    loadProjectDocs(selectedProjectId);
    loadTasks(selectedProjectId);
    loadProjectInstructions(selectedProjectId);
    loadProjectDecisions(selectedProjectId);
    loadFolders(selectedProjectId);
    loadProjectFiles(selectedProjectId, "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId]);

  // ---------- When conversation changes, load its messages + usage ----------

  useEffect(() => {
    if (selectedConversationId != null) {
      refreshMessages(selectedConversationId);
      loadUsageForConversation(selectedConversationId);
    } else {
      setMessages([]);
      setUsage(null);
      setFileEditProposal(null);
      setFileEditStatus(null);
      setTerminalProposal(null);
      setTerminalResult(null);
      setTerminalError(null);
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
          project_id: selectedProjectId,
          conversation_id: convIdBefore,
          message: userText,
          mode: chatMode,
          model: null,
          // Frontend always sends the conversation_id (if existing), so folder assignment
          // happens server-side already. For new chats (convIdBefore=null), backend picks default folder.
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
      await loadUsageForConversation(convId);
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
    setUsage(null);
    setFileEditProposal(null);
    setFileEditStatus(null);
    setTerminalProposal(null);
    setTerminalResult(null);
    setTerminalError(null);
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
      setTasks([]);
      setUsage(null);

      setFileEditProposal(null);
      setFileEditStatus(null);
      setTerminalProposal(null);
      setTerminalResult(null);
      setTerminalError(null);

      // Clear filesystem state too
      setFsEntries([]);
      setFsRoot(null);
      setFsCurrentSubpath("");
      setFsDisplayPath("");
      setFsSelectedRelPath(null);
      setFsOriginalContent("");
      setFsEditedContent("");
      setFsShowOriginal(false);
      setFsError(null);
      return;
    }
    setSelectedProjectId(parseInt(val, 10));
  };

  // ---------- Rename conversation handler ----------

  const handleRenameConversation = async (conversationId: number) => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }

    const trimmed = renameTitle.trim();
    if (!trimmed) {
      alert("Title cannot be empty.");
      return;
    }

    try {
      const res = await fetch(
        `${BACKEND_BASE}/conversations/${conversationId}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: trimmed }),
        }
      );

      if (!res.ok) {
        console.error("Rename conversation failed:", res.status);
        alert("Failed to rename conversation. Check backend logs.");
        return;
      }

      await refreshConversations(selectedProjectId);

      setRenamingConversationId(null);
      setRenameTitle("");
    } catch (e) {
      console.error("Rename conversation threw:", e);
      alert("Unexpected error renaming conversation. See console.");
    }
  };

  const openFolderModalForCreate = () => {
    setEditingFolder(null);
    setFolderFormName("");
    setFolderFormColor("#4F46E5");
    setFolderFormSortOrder(folders.length);
    setFolderFormIsDefault(false);
    setFolderFormIsArchived(false);
    setFolderFormError(null);
    setFolderModalOpen(true);
  };

  const openFolderModalForEdit = (folder: ConversationFolder) => {
    setEditingFolder(folder);
    setFolderFormName(folder.name);
    setFolderFormColor(folder.color || "#4F46E5");
    setFolderFormSortOrder(folder.sort_order);
    setFolderFormIsDefault(folder.is_default);
    setFolderFormIsArchived(folder.is_archived);
    setFolderFormError(null);
    setFolderModalOpen(true);
  };

  const closeFolderModal = () => {
    setFolderModalOpen(false);
  };

  const handleFolderFormSubmit = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    const trimmedName = folderFormName.trim();
    if (!trimmedName) {
      setFolderFormError("Folder name cannot be empty.");
      return;
    }

    try {
      if (editingFolder) {
        const res = await fetch(
          `${BACKEND_BASE}/conversation_folders/${editingFolder.id}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: trimmedName,
              color: folderFormColor || null,
              sort_order: folderFormSortOrder,
              is_default: folderFormIsDefault,
              is_archived: folderFormIsArchived,
            }),
          }
        );
        if (!res.ok) {
          console.error("Update folder failed:", res.status);
          setFolderFormError("Failed to update folder.");
          return;
        }
      } else {
        const res = await fetch(`${BACKEND_BASE}/conversation_folders`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: selectedProjectId,
            name: trimmedName,
            color: folderFormColor || null,
            sort_order: folderFormSortOrder,
            is_default: folderFormIsDefault,
            is_archived: folderFormIsArchived,
          }),
        });
        if (!res.ok) {
          console.error("Create folder failed:", res.status);
          setFolderFormError("Failed to create folder.");
          return;
        }
      }

      await loadFolders(selectedProjectId);
      await refreshConversations(selectedProjectId);
      setFolderModalOpen(false);
    } catch (e) {
      console.error("Saving folder threw:", e);
      setFolderFormError("Unexpected error while saving folder.");
    }
  };

  const handleDeleteFolder = async () => {
    if (!editingFolder) return;
    if (
      !window.confirm(
        `Delete folder "${editingFolder.name}"? Conversations will be moved to Unsorted.`
      )
    ) {
      return;
    }
    try {
      const res = await fetch(
        `${BACKEND_BASE}/conversation_folders/${editingFolder.id}`,
        {
          method: "DELETE",
        }
      );
      if (!res.ok) {
        console.error("Delete folder failed:", res.status);
        setFolderFormError("Failed to delete folder.");
        return;
      }

      if (
        typeof selectedFolderId === "number" &&
        selectedFolderId === editingFolder.id
      ) {
        setSelectedFolderId("all");
      }

      if (selectedProjectId != null) {
        await loadFolders(selectedProjectId);
        await refreshConversations(selectedProjectId);
      }
      setFolderModalOpen(false);
    } catch (e) {
      console.error("Delete folder threw:", e);
      setFolderFormError("Unexpected error while deleting folder.");
    }
  };

  const handleMoveConversationToFolder = async (
    conversationId: number,
    folderId: number | null
  ) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/conversations/${conversationId}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ folder_id: folderId }),
        }
      );

      if (!res.ok) {
        console.error("Move conversation failed:", res.status);
        alert("Failed to move conversation. Check backend logs.");
        return;
      }

      if (selectedProjectId != null) {
        await refreshConversations(selectedProjectId);
      }
    } catch (e) {
      console.error("Move conversation threw:", e);
      alert("Unexpected error while moving conversation.");
    }
  };

  // ---------- Task handlers ----------

  const handleAddTask = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    const desc = newTaskDescription.trim();
    if (!desc) {
      alert("Task description cannot be empty.");
      return;
    }

    setIsSavingTask(true);
    try {
      const res = await fetch(`${BACKEND_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId,
          description: desc,
        }),
      });

      if (!res.ok) {
        console.error("Create task failed:", res.status);
        alert("Failed to create task. See backend logs.");
        return;
      }

      setNewTaskDescription("");
      await loadTasks(selectedProjectId);
    } catch (e) {
      console.error("Create task threw:", e);
      alert("Unexpected error while creating task.");
    } finally {
      setIsSavingTask(false);
    }
  };

  const handleToggleTaskStatus = async (task: Task) => {
    const newStatus = task.status === "done" ? "open" : "done";
    try {
      const res = await fetch(`${BACKEND_BASE}/tasks/${task.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!res.ok) {
        console.error("Update task failed:", res.status);
        alert("Failed to update task. See backend logs.");
        return;
      }

      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id ? { ...t, status: newStatus } : t
        )
      );
    } catch (e) {
      console.error("Update task threw:", e);
      alert("Unexpected error while updating task.");
    }
  };

  const handleNewTaskKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (!isSavingTask) {
        handleAddTask();
      }
    }
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
              <div className="foldered-conversation-list">
                <div className="folder-toolbar">
                  <select
                    value={
                      selectedFolderId === "all"
                        ? "all"
                        : selectedFolderId === "none"
                        ? "none"
                        : selectedFolderId.toString()
                    }
                    onChange={(e) => {
                      const value = e.target.value;
                      setSelectedFolderId(
                        value === "all"
                          ? "all"
                          : value === "none"
                          ? "none"
                          : parseInt(value, 10)
                      );
                    }}
                  >
                    <option value="all">All folders</option>
                    <option value="none">Unsorted only</option>
                    {folders
                      .filter((f) => !f.is_archived)
                      .map((folder) => (
                        <option key={folder.id} value={folder.id}>
                          {folder.name}
                        </option>
                      ))}
                  </select>
                  <div className="folder-toolbar-actions">
                    <button
                      type="button"
                      className="btn-secondary small"
                      onClick={openFolderModalForCreate}
                      disabled={!selectedProjectId}
                    >
                      + Folder
                    </button>
                    <button
                      type="button"
                      className="btn-link small"
                      onClick={() => {
                        if (typeof selectedFolderId === "number") {
                          const folder = folders.find(
                            (f) => f.id === selectedFolderId
                          );
                          if (folder) {
                            openFolderModalForEdit(folder);
                          }
                        }
                      }}
                      disabled={
                        typeof selectedFolderId !== "number" ||
                        isLoadingFolders
                      }
                    >
                      Edit selected
                    </button>
                  </div>
                </div>

                <ul>
                  {conversations
                    .filter((c) => {
                      if (selectedFolderId === "all") return true;
                      if (selectedFolderId === "none") {
                        return c.folder_id == null;
                      }
                      return c.folder_id === selectedFolderId;
                    })
                    .map((c) => {
                      const isActive =
                        c.id === selectedConversationId;
                      const isRenaming =
                        c.id === renamingConversationId;

                      return (
                        <li key={c.id}>
                          <div
                            className={
                              "conversation-row" +
                              (isActive ? " active" : "")
                            }
                          >
                            {isRenaming ? (
                              <>
                                <input
                                  className="conversation-rename-input"
                                  value={renameTitle}
                                  onChange={(e) =>
                                    setRenameTitle(e.target.value)
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                      handleRenameConversation(c.id);
                                    } else if (e.key === "Escape") {
                                      setRenamingConversationId(null);
                                      setRenameTitle("");
                                    }
                                  }}
                                  autoFocus
                                />
                                <div className="conversation-actions">
                                  <button
                                    type="button"
                                    className="btn-secondary small"
                                    onClick={() =>
                                      handleRenameConversation(c.id)
                                    }
                                  >
                                    Save
                                  </button>
                                  <button
                                    type="button"
                                    className="btn-link small"
                                    onClick={() => {
                                      setRenamingConversationId(null);
                                      setRenameTitle("");
                                    }}
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="conversation-main">
                                  <button
                                    type="button"
                                    className={
                                      "conversation-item" +
                                      (isActive ? " active" : "")
                                    }
                                    onClick={() =>
                                      setSelectedConversationId(c.id)
                                    }
                                  >
                                    {c.title || `Chat #${c.id}`}
                                  </button>
                                  {selectedFolderId === "all" && (
                                    <span
                                      className="conversation-folder-pill"
                                      style={{
                                        backgroundColor:
                                          c.folder_color || "#e5e7eb",
                                      }}
                                    >
                                      {c.folder_name || "Unsorted"}
                                    </span>
                                  )}
                                </div>
                                <div className="conversation-actions">
                                  <button
                                    type="button"
                                    className="btn-link small"
                                    onClick={() => {
                                      setRenamingConversationId(c.id);
                                      setRenameTitle(c.title || "");
                                    }}
                                  >
                                    Rename
                                  </button>
                                  <select
                                    className="folder-assign-select"
                                    value={
                                      c.folder_id != null
                                        ? c.folder_id.toString()
                                        : "none"
                                    }
                                    onChange={(e) => {
                                      const value = e.target.value;
                                      handleMoveConversationToFolder(
                                        c.id,
                                        value === "none"
                                          ? null
                                          : parseInt(value, 10)
                                      );
                                    }}
                                  >
                                    <option value="none">
                                      Unsorted
                                    </option>
                                    {folders
                                      .filter((f) => !f.is_archived)
                                      .map((folder) => (
                                        <option
                                          key={folder.id}
                                          value={folder.id}
                                        >
                                          {folder.name}
                                        </option>
                                      ))}
                                  </select>
                                </div>
                              </>
                            )}
                          </div>
                        </li>
                      );
                    })}
                </ul>
              </div>
            )}
          </div>
          {folderModalOpen && (
            <div className="folder-modal-backdrop">
              <div className="folder-modal">
                <h3>
                  {editingFolder ? "Edit folder" : "Create folder"}
                </h3>
                <div className="folder-form-field">
                  <label htmlFor="folder-name">Name</label>
                  <input
                    id="folder-name"
                    type="text"
                    value={folderFormName}
                    onChange={(e) => setFolderFormName(e.target.value)}
                  />
                </div>
                <div className="folder-form-field">
                  <label htmlFor="folder-color">Color</label>
                  <input
                    id="folder-color"
                    type="color"
                    value={folderFormColor}
                    onChange={(e) => setFolderFormColor(e.target.value)}
                  />
                </div>
                <div className="folder-form-field">
                  <label htmlFor="folder-sort">Sort order</label>
                  <input
                    id="folder-sort"
                    type="number"
                    value={folderFormSortOrder}
                    onChange={(e) =>
                      setFolderFormSortOrder(
                        Number.isNaN(parseInt(e.target.value, 10))
                          ? 0
                          : parseInt(e.target.value, 10)
                      )
                    }
                  />
                </div>
                <label className="folder-checkbox">
                  <input
                    type="checkbox"
                    checked={folderFormIsDefault}
                    onChange={(e) =>
                      setFolderFormIsDefault(e.target.checked)
                    }
                  />
                  Default for new chats
                </label>
                <label className="folder-checkbox">
                  <input
                    type="checkbox"
                    checked={folderFormIsArchived}
                    onChange={(e) =>
                      setFolderFormIsArchived(e.target.checked)
                    }
                  />
                  Archived (hidden by default)
                </label>
                {folderFormError && (
                  <div className="notes-error">{folderFormError}</div>
                )}
                <div className="folder-modal-actions">
                  {editingFolder && (
                    <button
                      type="button"
                      className="btn-link small danger"
                      onClick={handleDeleteFolder}
                    >
                      Delete folder
                    </button>
                  )}
                  <div className="folder-modal-actions-right">
                    <button
                      type="button"
                      className="btn-link small"
                      onClick={closeFolderModal}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn-secondary small"
                      onClick={handleFolderFormSubmit}
                      disabled={isLoadingFolders}
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
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

        {/* RIGHT: Workbench (tabbed) */}
        <section className="column column-right">
          <div className="right-tabs">
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "tasks" ? " active" : "")
              }
              onClick={() => setRightTab("tasks")}
            >
              Tasks
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "docs" ? " active" : "")
              }
              onClick={() => setRightTab("docs")}
            >
              Docs
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "notes" ? " active" : "")
              }
              onClick={() => setRightTab("notes")}
            >
              Notes
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "files" ? " active" : "")
              }
              onClick={() => setRightTab("files")}
            >
              Files
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "search" ? " active" : "")
              }
              onClick={() => setRightTab("search")}
            >
              Search
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "terminal" ? " active" : "")
              }
              onClick={() => setRightTab("terminal")}
            >
              Terminal
            </button>
            <button
              type="button"
              className={
                "right-tab" + (rightTab === "usage" ? " active" : "")
              }
              onClick={() => setRightTab("usage")}
            >
              Usage
            </button>
          </div>

          {rightTab === "tasks" && (
            <>
              {/* Project tasks */}
              <div className="tasks-header">Project tasks</div>
              <div className="tasks-new">
                <input
                  className="tasks-input"
                  type="text"
                  placeholder="Add a task for this project..."
                  value={newTaskDescription}
                  onChange={(e) => setNewTaskDescription(e.target.value)}
                  onKeyDown={handleNewTaskKeyDown}
                />
                <button
                  className="btn-secondary small"
                  type="button"
                  onClick={handleAddTask}
                  disabled={
                    isSavingTask ||
                    !newTaskDescription.trim() ||
                    !selectedProjectId
                  }
                >
                  Add
                </button>
              </div>
              <div className="tasks-list">
                {selectedProjectId == null ? (
                  <div className="tasks-empty">No project selected.</div>
                ) : tasks.length === 0 ? (
                  <div className="tasks-empty">
                    No tasks yet. Add one above.
                  </div>
                ) : (
                  <ul>
                    {tasks.map((task) => (
                      <li key={task.id} className="task-item">
                        <input
                          type="checkbox"
                          checked={task.status === "done"}
                          onChange={() => handleToggleTaskStatus(task)}
                        />
                        <div
                          className={
                            "task-text" +
                            (task.status === "done" ? " done" : "")
                          }
                        >
                          {task.description}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}

          {rightTab === "docs" && (
            <>
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
                        <div className="project-doc-id">
                          Doc ID {doc.id}
                        </div>
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
                    onChange={(e) =>
                      setNewDocDescription(e.target.value)
                    }
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
                    {isIngestingTextDoc
                      ? "Ingesting…"
                      : "Ingest text doc"}
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
                    onChange={(e) =>
                      setRepoNamePrefix(e.target.value)
                    }
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
            </>
          )}

          {rightTab === "notes" && (
            <>
              <div className="notes-header">Project instructions</div>
              <div className="notes-panel">
                {selectedProjectId == null ? (
                  <div className="notes-empty">No project selected.</div>
                ) : (
                  <>
                    <textarea
                      className="instructions-textarea"
                      placeholder="Use this space to capture coding conventions, sensitive areas, current priorities..."
                      value={projectInstructions}
                      onChange={(e) => setProjectInstructions(e.target.value)}
                    />
                    <div className="instructions-meta">
                      {projectInstructionsUpdatedAt
                        ? `Last updated ${new Date(
                            projectInstructionsUpdatedAt
                          ).toLocaleString()}`
                        : "Instructions not set yet."}
                    </div>
                    {projectInstructionsError && (
                      <div className="notes-error">
                        {projectInstructionsError}
                      </div>
                    )}
                    <div className="instructions-actions">
                      <button
                        type="button"
                        className="btn-secondary small"
                        onClick={handleSaveInstructions}
                        disabled={isSavingInstructions}
                      >
                        {isSavingInstructions
                          ? "Saving…"
                          : "Save instructions"}
                      </button>
                      <button
                        type="button"
                        className="btn-link small"
                        onClick={() =>
                          selectedProjectId &&
                          loadProjectInstructions(selectedProjectId)
                        }
                      >
                        Refresh
                      </button>
                    </div>
                    <div className="instructions-preview">
                      <div className="instructions-preview-label">
                        Prompt preview
                      </div>
                      <pre className="instructions-preview-content">
                        {projectInstructions
                          ? `Project-specific instructions:\n${projectInstructions}`
                          : "(No instructions will be injected.)"}
                      </pre>
                    </div>
                  </>
                )}
              </div>

              <div className="decisions-header">Decision log</div>
              <div className="decisions-panel">
                {selectedProjectId == null ? (
                  <div className="notes-empty">No project selected.</div>
                ) : (
                  <>
                    <div className="decision-form">
                      <input
                        className="decision-input"
                        type="text"
                        placeholder="Decision title (e.g., Adopt FastAPI)"
                        value={newDecisionTitle}
                        onChange={(e) => setNewDecisionTitle(e.target.value)}
                      />
                      <input
                        className="decision-input"
                        type="text"
                        placeholder="Category (optional, e.g., Architecture)"
                        value={newDecisionCategory}
                        onChange={(e) =>
                          setNewDecisionCategory(e.target.value)
                        }
                      />
                      <textarea
                        className="decision-textarea"
                        placeholder="Details (optional)"
                        value={newDecisionDetails}
                        onChange={(e) =>
                          setNewDecisionDetails(e.target.value)
                        }
                      />
                      <label className="decision-checkbox">
                        <input
                          type="checkbox"
                          checked={linkDecisionToConversation}
                          disabled={!selectedConversationId}
                          onChange={(e) =>
                            setLinkDecisionToConversation(e.target.checked)
                          }
                        />
                        Link to current conversation
                        {!selectedConversationId && (
                          <span className="decision-checkbox-hint">
                            (Select a conversation to enable)
                          </span>
                        )}
                      </label>
                      <div className="decision-actions">
                        <button
                          type="button"
                          className="btn-secondary small"
                          onClick={handleAddDecision}
                          disabled={isSavingDecision}
                        >
                          {isSavingDecision ? "Saving…" : "Add decision"}
                        </button>
                        <button
                          type="button"
                          className="btn-link small"
                          onClick={() =>
                            selectedProjectId &&
                            loadProjectDecisions(selectedProjectId)
                          }
                        >
                          Refresh log
                        </button>
                      </div>
                      {decisionsError && (
                        <div className="notes-error">{decisionsError}</div>
                      )}
                    </div>
                    <div className="decisions-list">
                      {projectDecisions.length === 0 ? (
                        <div className="notes-empty">
                          No decisions logged yet.
                        </div>
                      ) : (
                        <ul>
                          {projectDecisions.map((decision) => (
                            <li
                              key={decision.id}
                              className="decision-item"
                            >
                              <div className="decision-title-row">
                                <span className="decision-title">
                                  {decision.title}
                                </span>
                                {decision.category && (
                                  <span className="decision-chip">
                                    {decision.category}
                                  </span>
                                )}
                              </div>
                              {decision.details && (
                                <div className="decision-details">
                                  {decision.details}
                                </div>
                              )}
                              <div className="decision-meta">
                                <span>
                                  {new Date(
                                    decision.created_at
                                  ).toLocaleString()}
                                </span>
                                {decision.source_conversation_id && (
                                  <span className="decision-meta-link">
                                    Linked to conversation #
                                    {decision.source_conversation_id}
                                  </span>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          {rightTab === "files" && (
            <>
              {/* Project files */}
              <div className="files-header">Project files</div>
              <div className="files-panel">
                {selectedProjectId == null ? (
                  <div className="files-empty">No project selected.</div>
                ) : fsError ? (
                  <div className="files-error">{fsError}</div>
                ) : (
                  <>
                    <div className="files-location-row">
                      <div className="files-location">
                        Location: {fsDisplayPath || "."}
                        {fsRoot && (
                          <span className="files-root-hint">
                            {" "}
                            (root: {fsRoot})
                          </span>
                        )}
                      </div>
                      <div className="files-location-actions">
                        <button
                          type="button"
                          className="btn-secondary small"
                          onClick={handleFsUp}
                          disabled={
                            !fsCurrentSubpath || fsIsLoadingList
                          }
                        >
                          ↑ Up
                        </button>
                        <button
                          type="button"
                          className="btn-secondary small"
                          onClick={handleFsRefresh}
                          disabled={fsIsLoadingList}
                        >
                          Refresh
                        </button>
                      </div>
                    </div>
                    <div className="files-list">
                      {fsIsLoadingList ? (
                        <div className="files-empty">
                          Loading files…
                        </div>
                      ) : fsEntries.length === 0 ? (
                        <div className="files-empty">
                          No files or folders at this level.
                        </div>
                      ) : (
                        <ul>
                          {fsEntries.map((entry) => {
                            const isSelected =
                              !entry.is_dir &&
                              fsSelectedRelPath === entry.rel_path;
                            return (
                              <li
                                key={entry.rel_path}
                                className="file-list-item"
                              >
                                <button
                                  type="button"
                                  className={
                                    "file-list-entry-button" +
                                    (isSelected ? " selected" : "")
                                  }
                                  onClick={() =>
                                    handleOpenFsEntry(entry)
                                  }
                                >
                                  <span className="file-list-name">
                                    {entry.is_dir ? "📁" : "📄"}{" "}
                                    {entry.name}
                                  </span>
                                  {!entry.is_dir &&
                                    entry.size != null && (
                                      <span className="file-list-meta">
                                        {entry.size} bytes
                                      </span>
                                    )}
                                </button>
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>

                    {fsSelectedRelPath && (
                      <div className="file-editor">
                        <div className="file-editor-header">
                          <div className="file-editor-title">
                            Editing: {fsSelectedRelPath}
                            {hasUnsavedFileChanges && (
                              <span className="unsaved-indicator">
                                ● Unsaved changes
                              </span>
                            )}
                          </div>
                          <div className="file-editor-controls">
                            <label className="show-original-toggle">
                              <input
                                type="checkbox"
                                checked={fsShowOriginal}
                                onChange={(e) =>
                                  setFsShowOriginal(e.target.checked)
                                }
                              />
                              Show original
                            </label>
                            <button
                              type="button"
                              className="btn-secondary small"
                              onClick={handleSaveFile}
                              disabled={
                                fsIsSavingFile ||
                                !hasUnsavedFileChanges
                              }
                            >
                              {fsIsSavingFile
                                ? "Saving…"
                                : "Save file"}
                            </button>
                          </div>
                        </div>
                        <textarea
                          className="file-editor-textarea"
                          value={fsEditedContent}
                          onChange={(e) =>
                            setFsEditedContent(e.target.value)
                          }
                          disabled={fsIsLoadingFile}
                        />
                        {fsShowOriginal && (
                          <div className="file-original-box">
                            <div className="file-original-label">
                              Original (read-only)
                            </div>
                            <pre className="file-original-content">
                              {fsOriginalContent}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* AI file edit proposal */}
              <div className="fileedit-header">AI file edit</div>
              <div className="fileedit-panel">
                {selectedConversationId == null ? (
                  <div className="fileedit-empty">
                    No conversation selected.
                  </div>
                ) : !fileEditProposal ? (
                  <div className="fileedit-empty">
                    No AI file edit proposals in the latest assistant
                    reply.
                  </div>
                ) : (
                  <>
                    <div className="fileedit-path">
                      <span className="fileedit-label">File:</span>{" "}
                      <span className="fileedit-value">
                        {fileEditProposal.file_path}
                      </span>
                    </div>
                    <div className="fileedit-reason">
                      <span className="fileedit-label">Reason:</span>{" "}
                      <span className="fileedit-value">
                        {fileEditProposal.reason}
                      </span>
                    </div>
                    <div className="fileedit-instruction">
                      <span className="fileedit-label">
                        Instruction:
                      </span>
                      <div className="fileedit-instruction-text">
                        {fileEditProposal.instruction}
                      </div>
                    </div>
                    <div className="fileedit-buttons">
                      <button
                        type="button"
                        className="btn-secondary small"
                        onClick={handleApplyFileEdit}
                        disabled={isApplyingFileEdit}
                      >
                        {isApplyingFileEdit
                          ? "Applying…"
                          : "Apply AI edit"}
                      </button>
                      <button
                        type="button"
                        className="btn-link small"
                        onClick={handleDismissFileEditProposal}
                      >
                        Dismiss
                      </button>
                    </div>
                    {fileEditStatus && (
                      <div className="fileedit-status">
                        {fileEditStatus}
                      </div>
                    )}
                  </>
                )}
              </div>
            </>
          )}

          {rightTab === "search" && (
            <>
              {/* Search memory */}
              <div className="search-header">Search memory</div>

              <div className="search-tabs">
                <button
                  className={
                    "search-tab" +
                    (searchTab === "messages" ? " active" : "")
                  }
                  type="button"
                  onClick={() => setSearchTab("messages")}
                >
                  Messages
                </button>
                <button
                  className={
                    "search-tab" +
                    (searchTab === "docs" ? " active" : "")
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
                        <li
                          key={hit.message_id}
                          className="search-result-item"
                        >
                          <div className="search-result-meta">
                            Conversation {hit.conversation_id} ·{" "}
                            {hit.role}
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
                      <li
                        key={hit.chunk_id}
                        className="search-result-item"
                      >
                        <div className="search-result-meta">
                          Doc {hit.document_id} · chunk{" "}
                          {hit.chunk_index}
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
            </>
          )}

          {rightTab === "terminal" && (
            <>
              <div className="terminal-manual-header">
                Manual terminal command
              </div>
              <div className="terminal-panel manual-terminal-panel">
                {selectedProjectId == null ? (
                  <div className="terminal-empty">
                    Select a project to run manual commands.
                  </div>
                ) : (
                  <>
                    <div className="manual-terminal-cwd-row">
                      <label className="terminal-label" htmlFor="manual-cwd">
                        CWD (optional):
                      </label>
                      <input
                        id="manual-cwd"
                        type="text"
                        className="manual-terminal-input"
                        placeholder="e.g. backend, frontend, scratch"
                        value={manualTerminalCwd}
                        onChange={(e) => setManualTerminalCwd(e.target.value)}
                      />
                    </div>
                    <textarea
                      className="manual-terminal-textarea"
                      placeholder="Enter a command to run (PowerShell / cmd syntax)..."
                      value={manualTerminalCommand}
                      onChange={(e) =>
                        setManualTerminalCommand(e.target.value)
                      }
                      rows={3}
                    />
                    <label className="manual-terminal-send">
                      <input
                        type="checkbox"
                        checked={manualTerminalSendToChat}
                        onChange={(e) =>
                          setManualTerminalSendToChat(e.target.checked)
                        }
                      />
                      Send output to chat (requires selected conversation)
                    </label>
                    <div className="terminal-buttons">
                      <button
                        type="button"
                        className="btn-secondary small"
                        onClick={handleRunManualTerminalCommand}
                        disabled={
                          isRunningManualTerminal ||
                          !manualTerminalCommand.trim()
                        }
                      >
                        {isRunningManualTerminal ? "Running…" : "Run command"}
                      </button>
                      <button
                        type="button"
                        className="btn-link small"
                        onClick={() => {
                          setManualTerminalCommand("");
                          setManualTerminalCwd("");
                          setManualTerminalError(null);
                        }}
                      >
                        Clear
                      </button>
                    </div>
                    {manualTerminalError && (
                      <div className="terminal-status terminal-status-error">
                        {manualTerminalError}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* AI terminal command proposal */}
              <div className="terminal-header">AI terminal command</div>
              <div className="terminal-panel">
                {selectedConversationId == null ? (
                  <div className="terminal-empty">
                    No conversation selected.
                  </div>
                ) : !terminalProposal ? (
                  <div className="terminal-empty">
                    No AI terminal command proposals in the latest
                    assistant reply.
                  </div>
                ) : (
                  <>
                    <div className="terminal-row">
                      <span className="terminal-label">CWD:</span>{" "}
                      <span className="terminal-value">
                        {terminalProposal.cwd &&
                        terminalProposal.cwd.trim()
                          ? terminalProposal.cwd
                          : "(project root)"}
                      </span>
                    </div>
                    <div className="terminal-row">
                      <span className="terminal-label">
                        Command:
                      </span>{" "}
                      <span className="terminal-value mono">
                        {terminalProposal.command}
                      </span>
                    </div>
                    {terminalProposal.reason && (
                      <div className="terminal-row">
                        <span className="terminal-label">
                          Reason:
                        </span>{" "}
                        <span className="terminal-value">
                          {terminalProposal.reason}
                        </span>
                      </div>
                    )}
                    <div className="terminal-buttons">
                      <button
                        type="button"
                        className="btn-secondary small"
                        onClick={handleRunTerminalProposal}
                        disabled={isRunningTerminalCommand}
                      >
                        {isRunningTerminalCommand
                          ? "Running…"
                          : "Run command"}
                      </button>
                      <button
                        type="button"
                        className="btn-link small"
                        onClick={() => setTerminalProposal(null)}
                      >
                        Dismiss
                      </button>
                    </div>
                    {terminalError && (
                      <div className="terminal-status terminal-status-error">
                        {terminalError}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Terminal last run output */}
              <div className="terminal-output-header">
                Last terminal run
              </div>
              <div className="terminal-output-panel">
                {!terminalResult ? (
                  <div className="terminal-empty">
                    No terminal command has been run yet from this UI.
                  </div>
                ) : (
                  <>
                    <div className="terminal-output-meta">
                      <div>
                        <span className="terminal-label">
                          Command:
                        </span>{" "}
                        <span className="terminal-value mono">
                          {terminalResult.command}
                        </span>
                      </div>
                      <div>
                        <span className="terminal-label">CWD:</span>{" "}
                        <span className="terminal-value">
                          {terminalResult.cwd &&
                          terminalResult.cwd.trim()
                            ? terminalResult.cwd
                            : "(project root)"}
                        </span>
                      </div>
                      <div>
                        <span className="terminal-label">
                          Exit code:
                        </span>{" "}
                        <span className="terminal-value">
                          {terminalResult.exit_code}
                        </span>
                      </div>
                    </div>
                    <div className="terminal-output-note">
                      (This output was also sent to the assistant so it
                      can decide what to do next.)
                    </div>
                    <div className="terminal-output-block">
                      <div className="terminal-output-label">STDOUT</div>
                      <pre className="terminal-output-stdout">
                        {terminalResult.stdout || "(no stdout)"}
                      </pre>
                    </div>
                    <div className="terminal-output-block">
                      <div className="terminal-output-label">STDERR</div>
                      <pre className="terminal-output-stderr">
                        {terminalResult.stderr || "(no stderr)"}
                      </pre>
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          {rightTab === "usage" && (
            <>
              {/* Usage panel */}
              <div className="usage-header">
                Usage (this conversation)
              </div>
              <div className="usage-panel">
                {selectedConversationId == null ? (
                  <div className="usage-empty">
                    No conversation selected.
                  </div>
                ) : isLoadingUsage ? (
                  <div className="usage-empty">Loading usage…</div>
                ) : !usage || !usage.records.length ? (
                  <div className="usage-empty">
                    No usage records yet for this conversation.
                  </div>
                ) : (
                  <>
                    <div className="usage-summary">
                      <div>
                        <span className="usage-label">
                          Total tokens in:
                        </span>{" "}
                        <span className="usage-value">
                          {usage.total_tokens_in ?? 0}
                        </span>
                      </div>
                      <div>
                        <span className="usage-label">
                          Total tokens out:
                        </span>{" "}
                        <span className="usage-value">
                          {usage.total_tokens_out ?? 0}
                        </span>
                      </div>
                      <div>
                        <span className="usage-label">
                          Total cost:
                        </span>{" "}
                        <span className="usage-value">
                          {usage.total_cost_estimate != null
                            ? `$${usage.total_cost_estimate.toFixed(4)}`
                            : "—"}
                        </span>
                      </div>
                    </div>
                    <div className="usage-records">
                      <div className="usage-records-title">
                        Recent assistant calls
                      </div>
                      <ul>
                        {usage.records
                          .slice()
                          .reverse()
                          .slice(0, 10)
                          .map((r) => (
                            <li
                              key={r.id}
                              className="usage-record-item"
                            >
                              <div className="usage-record-main">
                                <span className="usage-model">
                                  {r.model || "model?"}
                                </span>
                                <span className="usage-tokens">
                                  in {r.tokens_in ?? 0} · out{" "}
                                  {r.tokens_out ?? 0}
                                </span>
                              </div>
                              <div className="usage-record-sub">
                                msg #{r.message_id ?? "?"} ·{" "}
                                {new Date(
                                  r.created_at
                                ).toLocaleTimeString()}
                              </div>
                            </li>
                          ))}
                      </ul>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
