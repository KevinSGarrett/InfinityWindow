import React, {
  useEffect,
  useState,
  useMemo,
  useCallback,
  useRef,
} from "react";
import type { KeyboardEvent } from "react";
import "./App.css";

// ---------- Types ----------

type Project = {
  id: number;
  name: string;
  description?: string | null;
  instruction_text?: string | null;
  instruction_updated_at?: string | null;
  local_root_path?: string | null;
  pinned_note_text?: string | null;
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
  folder_name?: string | null;
  folder_color?: string | null;
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
  priority: string;
  blocked_reason?: string | null;
  auto_notes?: string | null;
  auto_confidence?: number | null;
  auto_last_action?: string | null;
  auto_last_action_at?: string | null;
  group?: string | null;
  created_at: string;
  updated_at: string;
};

type TaskSuggestion = {
  id: number;
  project_id: number;
  conversation_id: number | null;
  target_task_id: number | null;
  action_type: "add" | "complete" | string;
  payload: Record<string, any>;
  confidence: number;
  status: string;
  task_description?: string | null;
  task_status?: string | null;
  task_priority?: string | null;
  task_blocked_reason?: string | null;
  created_at: string;
  updated_at: string;
};

type TaskOverview = {
  tasks: Task[];
  suggestions: TaskSuggestion[];
};

type TaskTelemetryAction = {
  timestamp: string;
  action: string;
  confidence: number;
  task_id?: number | null;
  task_description?: string | null;
  task_status?: string | null;
  task_priority?: string | null;
  task_blocked_reason?: string | null;
  task_auto_notes?: string | null;
  task_group?: string | null;
  project_id?: number | null;
  conversation_id?: number | null;
  details?: Record<string, any>;
  matched_text?: string | null;
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
  mode?: string | null;
};

type IngestionJob = {
  id: number;
  project_id: number;
  kind: string;
  source: string;
  status: string;
  total_items: number;
  processed_items: number;
  total_bytes: number;
  processed_bytes: number;
  cancel_requested: boolean;
  error_message?: string | null;
  meta?: Record<string, any> | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

type ConversationUsage = {
  conversation_id: number;
  total_tokens_in: number | null;
  total_tokens_out: number | null;
  total_cost_estimate: number | null;
  records: UsageRecord[];
};

type TelemetrySnapshot = {
  llm: {
    auto_routes: Record<string, number>;
    fallback_attempts: number;
    fallback_success: number;
  };
  tasks: {
    auto_added: number;
    auto_completed: number;
    auto_deduped: number;
    auto_suggested: number;
    recent_actions: TaskTelemetryAction[];
    confidence_stats?: {
      min: number;
      max: number;
      avg: number;
      count: number;
    };
    confidence_buckets?: {
      lt_0_4: number;
      "0_4_0_7": number;
      gte_0_7: number;
    };
    suggestions?: TaskSuggestion[];
  };
  ingestion: Record<string, any>;
};

type ProjectDecision = {
  id: number;
  project_id: number;
  title: string;
  details?: string | null;
  category?: string | null;
  source_conversation_id?: number | null;
  created_at: string;
  updated_at: string;
  status: string;
  tags: string[];
  follow_up_task_id?: number | null;
  is_draft: boolean;
  auto_detected: boolean;
};

type MemoryItem = {
  id: number;
  project_id: number;
  title: string;
  content: string;
  tags: string[];
  pinned: boolean;
  expires_at?: string | null;
  source_conversation_id?: number | null;
  source_message_id?: number | null;
  superseded_by_id?: number | null;
  created_at: string;
  updated_at: string;
};

type RightTab =
  | "tasks"
  | "docs"
  | "files"
  | "search"
  | "terminal"
  | "usage"
  | "notes"
  | "memory";

type CommandHistoryEntry = {
  id: number;
  command: string;
  cwd: string;
  timestamp: string;
};

type Toast = {
  id: number;
  message: string;
  type: "success" | "error";
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

type SearchFilterValue = "all" | number;

// Filesystem types
type FileEntry = {
  name: string;
  is_dir: boolean;
  size: number | null;
  modified_at: string;
  rel_path: string;
};

const formatBytes = (value?: number | null): string => {
  if (!value || value <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let bytes = value;
  let unitIndex = 0;
  while (bytes >= 1024 && unitIndex < units.length - 1) {
    bytes /= 1024;
    unitIndex += 1;
  }
  const precision = unitIndex === 0 ? 0 : bytes < 10 ? 1 : 0;
  return `${bytes.toFixed(precision)} ${units[unitIndex]}`;
};

const formatDuration = (
  startedAt?: string | null,
  finishedAt?: string | null
): string | null => {
  if (!startedAt) return null;
  const start = new Date(startedAt).getTime();
  const end = finishedAt ? new Date(finishedAt).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) return null;
  const seconds = Math.max(0, Math.round((end - start) / 1000));
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs.toString().padStart(2, "0")}s`;
};

const formatDateTime = (value?: string | null): string | null => {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString();
};

// Allow overriding backend base via Vite env; default to localhost:8000.
// For QA runs we set VITE_API_BASE; fallback remains 8000.
const BACKEND_BASE =
  (typeof import.meta !== "undefined" &&
    (import.meta as any)?.env?.VITE_API_BASE) ||
  "http://127.0.0.1:8000";

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
  const [modelOverride, setModelOverride] = useState("");
  const [modelOverrideMode, setModelOverrideMode] = useState("default");
  const [modelOverrideCustom, setModelOverrideCustom] = useState("");

  // Project documents
  const [projectDocs, setProjectDocs] = useState<ProjectDocument[]>([]);
  const [highlightedDocId, setHighlightedDocId] = useState<number | null>(null);

  // Project tasks
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [isSavingTask, setIsSavingTask] = useState(false);
  const [taskSuggestions, setTaskSuggestions] = useState<TaskSuggestion[]>([]);
  const [isLoadingTaskSuggestions, setIsLoadingTaskSuggestions] =
    useState(false);
  const [taskSuggestionError, setTaskSuggestionError] = useState<string | null>(
    null
  );
  const [showAllTaskSuggestions, setShowAllTaskSuggestions] = useState(false);
  const [showSuggestionsPanel, setShowSuggestionsPanel] = useState(false);
  const [processingSuggestionIds, setProcessingSuggestionIds] = useState<
    Set<number>
  >(new Set());
  const setSuggestionProcessing = useCallback(
    (id: number, processing: boolean) => {
      setProcessingSuggestionIds((prev) => {
        const next = new Set(prev);
        if (processing) {
          next.add(id);
        } else {
          next.delete(id);
        }
        return next;
      });
    },
    []
  );

  // Usage (per conversation)
  const [usage, setUsage] = useState<ConversationUsage | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);
  const [usageConversationId, setUsageConversationId] = useState<number | null>(
    null
  );
  const [telemetry, setTelemetry] = useState<TelemetrySnapshot | null>(null);
  const [isLoadingTelemetry, setIsLoadingTelemetry] = useState(false);
  const [telemetryError, setTelemetryError] = useState<string | null>(null);
  const [usageActionFilter, setUsageActionFilter] = useState<string>("all");
  const [usageGroupFilter, setUsageGroupFilter] = useState<string>("all");
  const [usageModelFilter, setUsageModelFilter] = useState<string>("all");
  const [usageTimeFilter, setUsageTimeFilter] = useState<string>("all");
  const [usageRangeFilter, setUsageRangeFilter] = useState<string>("recent");
  const [usageRecordsWindow, setUsageRecordsWindow] =
    useState<string>("all");
  const [usageError, setUsageError] = useState<string | null>(null);
  const [usageExportJson, setUsageExportJson] = useState<string | null>(null);
  const [usageExportFormat, setUsageExportFormat] = useState<"json" | "csv" | null>(null);
  const [usageExportError, setUsageExportError] = useState<string | null>(null);

  // Project instructions
  const [projectInstructions, setProjectInstructions] = useState("");
  const [projectInstructionsUpdatedAt, setProjectInstructionsUpdatedAt] =
    useState<string | null>(null);
  const [isSavingInstructions, setIsSavingInstructions] = useState(false);
  const [projectInstructionsError, setProjectInstructionsError] =
    useState<string | null>(null);
  const [projectInstructionsSaved, setProjectInstructionsSaved] = useState("");
  const [projectPinnedNote, setProjectPinnedNote] = useState("");
  const [projectPinnedNoteSaved, setProjectPinnedNoteSaved] = useState("");

  // Project decisions
  const [projectDecisions, setProjectDecisions] = useState<ProjectDecision[]>(
    []
  );
  const [newDecisionTitle, setNewDecisionTitle] = useState("");
  const [newDecisionDetails, setNewDecisionDetails] = useState("");
  const [newDecisionCategory, setNewDecisionCategory] = useState("");
  const [newDecisionTags, setNewDecisionTags] = useState("");
  const [newDecisionStatus, setNewDecisionStatus] =
    useState<"recorded" | "draft">("recorded");
  const [linkDecisionToConversation, setLinkDecisionToConversation] =
    useState(true);
  const [isSavingDecision, setIsSavingDecision] = useState(false);
  const [decisionsError, setDecisionsError] = useState<string | null>(null);
  const [decisionStatusFilter, setDecisionStatusFilter] =
    useState<string>("all");
  const [decisionCategoryFilter, setDecisionCategoryFilter] =
    useState<string>("all");
  const [decisionTagFilter, setDecisionTagFilter] = useState<string>("all");
  const [decisionSearchQuery, setDecisionSearchQuery] = useState("");
  const [highlightNewDrafts, setHighlightNewDrafts] = useState(false);

  // Project memory
  const [memoryItems, setMemoryItems] = useState<MemoryItem[]>([]);
  const [isLoadingMemory, setIsLoadingMemory] = useState(false);
  const [memoryModalOpen, setMemoryModalOpen] = useState(false);
  const [memoryFormTitle, setMemoryFormTitle] = useState("");
  const [memoryFormContent, setMemoryFormContent] = useState("");
  const [memoryFormTags, setMemoryFormTags] = useState("");
  const [memoryFormPinned, setMemoryFormPinned] = useState(false);
  const [memoryFormExpiresAt, setMemoryFormExpiresAt] =
    useState<string>("");
  const [memoryFormSourceMessageId, setMemoryFormSourceMessageId] =
    useState<number | null>(null);
  const [memoryFormError, setMemoryFormError] = useState<string | null>(
    null
  );
  // AI file edit proposals
  const [fileEditProposal, setFileEditProposal] =
    useState<FileEditProposal | null>(null);
  const [isApplyingFileEdit, setIsApplyingFileEdit] = useState(false);
  const [fileEditStatus, setFileEditStatus] = useState<string | null>(null);
  const [fileEditPreview, setFileEditPreview] = useState<{
    diff: string | null;
    edited_content: string;
    original_content: string;
  } | null>(null);
  const [isPreviewingFileEdit, setIsPreviewingFileEdit] = useState(false);
  const [fileEditError, setFileEditError] = useState<string | null>(null);

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
  const [repoIngestionJob, setRepoIngestionJob] =
    useState<IngestionJob | null>(null);
  const repoIngestionPollRef = useRef<number | null>(null);
  const [repoIngestionJobs, setRepoIngestionJobs] = useState<IngestionJob[]>(
    []
  );
  const [isLoadingRepoJobs, setIsLoadingRepoJobs] = useState(false);

  // Search
  const [searchTab, setSearchTab] = useState<"messages" | "docs">("messages");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchMessageHits, setSearchMessageHits] = useState<
    MessageSearchHit[]
  >([]);
  const [searchDocHits, setSearchDocHits] = useState<DocSearchHit[]>([]);
  const [searchConversationFilter, setSearchConversationFilter] =
    useState<SearchFilterValue>("all");
  const [searchFolderFilter, setSearchFolderFilter] =
    useState<SearchFilterValue>("all");
  const [searchDocFilter, setSearchDocFilter] =
    useState<SearchFilterValue>("all");

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
  const [rightTab, setRightTab] = useState<RightTab>("tasks");
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [commandPaletteQuery, setCommandPaletteQuery] = useState("");
  const [commandPaletteIndex, setCommandPaletteIndex] = useState(0);
  const [manualTerminalHistory, setManualTerminalHistory] = useState<
    CommandHistoryEntry[]
  >([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const chatSectionRef = useRef<HTMLDivElement | null>(null);
  const rightColumnRef = useRef<HTMLDivElement | null>(null);
  const commandPaletteInputRef = useRef<HTMLInputElement | null>(null);
  const [showAllTasks, setShowAllTasks] = useState(false);
  const [showAllDocs, setShowAllDocs] = useState(false);
  const [showAllDecisions, setShowAllDecisions] = useState(false);
  const draftSeenRef = useRef<Set<number>>(new Set());

  const stopRepoIngestionPolling = useCallback(() => {
    if (repoIngestionPollRef.current !== null) {
      window.clearInterval(repoIngestionPollRef.current);
      repoIngestionPollRef.current = null;
    }
  }, []);

  const addToast = useCallback((message: string, type: "success" | "error") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    if (showCommandPalette) {
      setTimeout(() => {
        commandPaletteInputRef.current?.focus();
      }, 0);
    }
  }, [showCommandPalette]);

  useEffect(() => {
    return () => {
      stopRepoIngestionPolling();
    };
  }, [stopRepoIngestionPolling]);

  // Load telemetry/usage when entering the Usage tab
  useEffect(() => {
    if (rightTab === "usage") {
      loadTelemetry(false);
      if (usageConversationId && usageConversationId > 0) {
        loadUsageForConversation(usageConversationId);
      } else if (selectedConversationId) {
        loadUsageForConversation(selectedConversationId);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rightTab]);

  // Ensure telemetry refreshes when project or usage conversation changes while on Usage tab.
  useEffect(() => {
    if (rightTab === "usage") {
      loadTelemetry(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId, usageConversationId]);

  const commandPaletteActions = useMemo(
    () => [
      {
        id: "go-tasks",
        label: "Switch to Tasks tab",
        action: () => setRightTab("tasks"),
      },
      {
        id: "go-docs",
        label: "Switch to Docs tab",
        action: () => setRightTab("docs"),
      },
      {
        id: "go-files",
        label: "Switch to Files tab",
        action: () => setRightTab("files"),
      },
      {
        id: "go-search",
        label: "Switch to Search tab",
        action: () => setRightTab("search"),
      },
      {
        id: "go-terminal",
        label: "Switch to Terminal tab",
        action: () => setRightTab("terminal"),
      },
      {
        id: "go-usage",
        label: "Switch to Usage tab",
        action: () => setRightTab("usage"),
      },
      {
        id: "go-notes",
        label: "Switch to Notes tab",
        action: () => setRightTab("notes"),
      },
      {
        id: "go-memory",
        label: "Switch to Memory tab",
        action: () => setRightTab("memory"),
      },
      {
        id: "focus-chat",
        label: "Focus chat input",
        action: () => {
          chatSectionRef.current
            ?.querySelector<HTMLTextAreaElement>(".chat-input")
            ?.focus();
        },
      },
      {
        id: "collapse-left",
        label: leftCollapsed ? "Expand sidebar" : "Collapse sidebar",
        action: () => setLeftCollapsed((prev) => !prev),
      },
    ],
    [leftCollapsed]
  );

  const filteredCommandActions = useMemo(() => {
    const query = commandPaletteQuery.trim().toLowerCase();
    if (!query) return commandPaletteActions;
    return commandPaletteActions.filter((action) =>
      action.label.toLowerCase().includes(query)
    );
  }, [commandPaletteActions, commandPaletteQuery]);
  const visibleTasks = showAllTasks ? tasks : tasks.slice(0, 5);
  const pendingTaskSuggestions = useMemo(
    () => taskSuggestions.filter((s) => s.status === "pending"),
    [taskSuggestions]
  );
  const pendingSuggestionCount = pendingTaskSuggestions.length;
  const visibleTaskSuggestions = showAllTaskSuggestions
    ? pendingTaskSuggestions
    : pendingTaskSuggestions.slice(0, 3);
  const visibleDocs = showAllDocs ? projectDocs : projectDocs.slice(0, 5);
  const availableDecisionCategories = useMemo(() => {
    const categories = new Set<string>();
    projectDecisions.forEach((decision) => {
      if (decision.category) {
        categories.add(decision.category);
      }
    });
    return Array.from(categories.values()).sort();
  }, [projectDecisions]);
  const availableDecisionTags = useMemo(() => {
    const tags = new Set<string>();
    projectDecisions.forEach((decision) => {
      decision.tags.forEach((tag) => tags.add(tag));
    });
    return Array.from(tags.values()).sort();
  }, [projectDecisions]);
  const filteredDecisions = useMemo(() => {
    return projectDecisions.filter((decision) => {
      if (
        decisionStatusFilter !== "all" &&
        decision.status.toLowerCase() !== decisionStatusFilter.toLowerCase()
      ) {
        return false;
      }
      if (
        decisionCategoryFilter !== "all" &&
        (decision.category || "").toLowerCase() !==
          decisionCategoryFilter.toLowerCase()
      ) {
        return false;
      }
      if (
        decisionTagFilter !== "all" &&
        !decision.tags.some(
          (tag) => tag.toLowerCase() === decisionTagFilter.toLowerCase()
        )
      ) {
        return false;
      }
      if (decisionSearchQuery.trim()) {
        const q = decisionSearchQuery.trim().toLowerCase();
        const haystack = `${decision.title} ${decision.details || ""} ${
          decision.category || ""
        } ${decision.tags.join(" ")}`.toLowerCase();
        if (!haystack.includes(q)) {
          return false;
        }
      }
      return true;
    });
  }, [
    projectDecisions,
    decisionStatusFilter,
    decisionCategoryFilter,
    decisionTagFilter,
    decisionSearchQuery,
  ]);
  const visibleDecisions = showAllDecisions
    ? filteredDecisions
    : filteredDecisions.slice(0, 5);
  const decisionFiltersActive =
    decisionStatusFilter !== "all" ||
    decisionCategoryFilter !== "all" ||
    decisionTagFilter !== "all" ||
    decisionSearchQuery.trim().length > 0;

  useEffect(() => {
    if (pendingSuggestionCount > 0 && !showSuggestionsPanel) {
      setShowSuggestionsPanel(true);
    }
  }, [pendingSuggestionCount, showSuggestionsPanel]);

  useEffect(() => {
    if (showSuggestionsPanel && !telemetry && !isLoadingTelemetry) {
      loadTelemetry(false);
    }
  }, [showSuggestionsPanel, telemetry, isLoadingTelemetry]);

  const groupedMessageHits = useMemo(() => {
    if (!searchMessageHits.length) {
      return [];
    }
    const map = new Map<
      number,
      {
        conversationId: number;
        title: string;
        folderName: string | null;
        folderColor: string | null;
        hits: MessageSearchHit[];
      }
    >();
    searchMessageHits.forEach((hit) => {
      const convo = conversations.find(
        (conversation) => conversation.id === hit.conversation_id
      );
      const title =
        (convo?.title && convo.title.trim()) ||
        `Conversation ${hit.conversation_id}`;
      const existing = map.get(hit.conversation_id);
      if (existing) {
        existing.hits.push(hit);
      } else {
        map.set(hit.conversation_id, {
          conversationId: hit.conversation_id,
          title,
          folderName: hit.folder_name ?? null,
          folderColor: hit.folder_color ?? null,
          hits: [hit],
        });
      }
    });
    return Array.from(map.values());
  }, [searchMessageHits, conversations]);

  const groupedDocHits = useMemo(() => {
    if (!searchDocHits.length) {
      return [];
    }
    const map = new Map<
      number,
      { documentId: number; name: string; hits: DocSearchHit[] }
    >();
    searchDocHits.forEach((hit) => {
      const doc = projectDocs.find((item) => item.id === hit.document_id);
      const name = doc?.name || `Document ${hit.document_id}`;
      const existing = map.get(hit.document_id);
      if (existing) {
        existing.hits.push(hit);
      } else {
        map.set(hit.document_id, {
          documentId: hit.document_id,
          name,
          hits: [hit],
        });
      }
    });
    return Array.from(map.values());
  }, [searchDocHits, projectDocs]);

  const windowedUsageRecords = useMemo(() => {
    if (!usage?.records || usage.records.length === 0) {
      return [];
    }
    if (usageRecordsWindow === "all") return usage.records;
    const now = Date.now();
    const windowMs =
      usageRecordsWindow === "1h"
        ? 60 * 60 * 1000
        : usageRecordsWindow === "24h"
        ? 24 * 60 * 60 * 1000
        : 7 * 24 * 60 * 60 * 1000;
    const cutoff = now - windowMs;
    return usage.records.filter((record) => {
      const ts = new Date(record.created_at ?? 0).getTime();
      return Number.isFinite(ts) && ts >= cutoff;
    });
  }, [usage, usageRecordsWindow]);

  const usageModelBreakdown = useMemo(() => {
    if (!windowedUsageRecords.length) {
      return [];
    }
    const map = new Map<
      string,
      { model: string; count: number; tokensIn: number; tokensOut: number }
    >();
    windowedUsageRecords.forEach((record) => {
      const key = record.model || "unknown";
      const entry =
        map.get(key) ??
        {
          model: key,
          count: 0,
          tokensIn: 0,
          tokensOut: 0,
        };
      entry.count += 1;
      entry.tokensIn += record.tokens_in ?? 0;
      entry.tokensOut += record.tokens_out ?? 0;
      map.set(key, entry);
    });
    return Array.from(map.values());
  }, [windowedUsageRecords]);

  const lastUsageAutoReason = (usage as any)?.auto_reason;

  // Fallback model options from task telemetry when usage breakdown is empty.
  const telemetryModelOptions = useMemo(() => {
    if (!telemetry?.tasks?.recent_actions) return [];
    const models = new Set<string>();
    telemetry.tasks.recent_actions.forEach((a) => {
      if (selectedProjectId && a.project_id !== selectedProjectId) {
        return;
      }
      const actionModel = (a as any).model || a.details?.model;
      if (actionModel) {
        models.add(actionModel);
      }
    });
    return Array.from(models);
  }, [telemetry, selectedProjectId]);

  const modelFilterOptions = useMemo(() => {
    if (usageModelBreakdown.length > 0) {
      return usageModelBreakdown.map((m) => m.model);
    }
    return telemetryModelOptions;
  }, [usageModelBreakdown, telemetryModelOptions]);

  const lastUsageModel = useMemo(() => {
    if (!usage?.records?.length) return null;
    return usage.records[usage.records.length - 1]?.model ?? null;
  }, [usage]);

  const filteredRecentActions = useMemo(() => {
    if (!telemetry?.tasks.recent_actions) return [];
    const suggestedActions = new Set(["auto_suggested", "auto_dismissed", "auto_deduped"]);
    return telemetry.tasks.recent_actions.filter((a) => {
      if (selectedProjectId && a.project_id !== selectedProjectId) {
        return false;
      }
      const action = a.action || "";
      const actionFilter = usageActionFilter;
      const matchesAction =
        actionFilter === "all"
          ? true
          : actionFilter === "suggested"
          ? suggestedActions.has(action)
          : action === actionFilter || action.startsWith(actionFilter);

      const matchesGroup =
        usageGroupFilter === "all" ||
        (a.task_group || "").toLowerCase() === usageGroupFilter;

      const actionModel =
        a.details?.model || (a as any).model || lastUsageModel || null;
      const matchesModel =
        usageModelFilter === "all" || actionModel === usageModelFilter;

      return matchesAction && matchesGroup && matchesModel;
    });
  }, [
    telemetry,
    usageActionFilter,
    usageGroupFilter,
    usageModelFilter,
    lastUsageModel,
    selectedProjectId,
  ]);

  const timeFilteredRecentActions = useMemo(() => {
    if (!filteredRecentActions.length) return [];
    if (usageTimeFilter === "all") return filteredRecentActions;
    const limit = usageTimeFilter === "last5" ? 5 : 10;
    return filteredRecentActions.slice(0, limit);
  }, [filteredRecentActions, usageTimeFilter]);

  const actionCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    timeFilteredRecentActions.forEach((a) => {
      counts[a.action] = (counts[a.action] || 0) + 1;
    });
    return counts;
  }, [timeFilteredRecentActions]);

  const modelCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    timeFilteredRecentActions.forEach((a) => {
      const m = (a as any).model || a.details?.model || "unknown";
      counts[m] = (counts[m] || 0) + 1;
    });
    return counts;
  }, [timeFilteredRecentActions]);

  const bucketCounts = useMemo(() => {
    const counts: Record<string, number> = { "lt_0_4": 0, "0_4_0_7": 0, "gte_0_7": 0 };
    timeFilteredRecentActions.forEach((a) => {
      const c = a.confidence ?? 0;
      if (c < 0.4) counts["lt_0_4"] += 1;
      else if (c < 0.7) counts["0_4_0_7"] += 1;
      else counts["gte_0_7"] += 1;
    });
    return counts;
  }, [timeFilteredRecentActions]);

  const actionChartData = useMemo(() => {
    const entries = Object.entries(actionCounts);
    if (!entries.length) return [];
    const max = Math.max(...entries.map(([, v]) => v));
    return entries
      .map(([action, count]) => ({
        key: action,
        label: action,
        count,
        percent: max ? (count / max) * 100 : 0,
      }))
      .sort((a, b) => b.count - a.count);
  }, [actionCounts]);

  const modelChartData = useMemo(() => {
    const entries = Object.entries(modelCounts);
    if (!entries.length) return [];
    const max = Math.max(...entries.map(([, v]) => v));
    return entries
      .map(([model, count]) => ({
        key: model || "unknown",
        label: model || "unknown",
        count,
        percent: max ? (count / max) * 100 : 0,
      }))
      .sort((a, b) => b.count - a.count);
  }, [modelCounts]);

  const confidenceChartData = useMemo(() => {
    const labels: Record<string, string> = {
      lt_0_4: "<0.4",
      "0_4_0_7": "0.4–0.7",
      gte_0_7: "≥0.7",
    };
    const entries = Object.entries(bucketCounts).map(([bucket, count]) => ({
      key: bucket,
      label: labels[bucket] || bucket,
      count,
    }));
    if (!entries.length) return [];
    const max = Math.max(...entries.map((e) => e.count));
    return entries.map((e) => ({
      ...e,
      percent: max ? (e.count / max) * 100 : 0,
    }));
  }, [bucketCounts]);

  const modeUsageChartData = useMemo(() => {
    const routes = telemetry?.llm?.auto_routes || {};
    const entries = Object.entries(routes)
      .filter(([, count]) => count > 0)
      .map(([mode, count]) => ({ key: mode, label: mode, count }));
    if (!entries.length) return [];
    const max = Math.max(...entries.map((e) => e.count));
    return entries.map((e) => ({
      ...e,
      percent: max ? (e.count / max) * 100 : 0,
    }));
  }, [telemetry]);

  const copyRecentActionsJson = useCallback(() => {
    setUsageExportError(null);
    try {
      const data = JSON.stringify(timeFilteredRecentActions, null, 2);
      setUsageExportFormat("json");
      setUsageExportJson(data);
      navigator.clipboard
        ?.writeText(data)
        .catch(() =>
          setUsageExportError(
            "Failed to copy to clipboard; export is still shown below."
          )
        );
    } catch (err) {
      setUsageExportError("Failed to generate JSON export.");
    }
  }, [timeFilteredRecentActions]);

  const copyRecentActionsCsv = useCallback(() => {
    setUsageExportError(null);
    const header = [
      "timestamp",
      "action",
      "confidence",
      "task_id",
      "task_description",
      "task_status",
      "task_priority",
      "task_group",
      "model",
    ];
    try {
      if (!timeFilteredRecentActions.length) {
        const emptyCsv = header.join(",");
        setUsageExportFormat("csv");
        setUsageExportJson(emptyCsv);
        navigator.clipboard
          ?.writeText(emptyCsv)
          .catch(() =>
            setUsageExportError(
              "Failed to copy CSV; preview remains available."
            )
          );
        return;
      }
      const rows = timeFilteredRecentActions.map((a) => {
        const m = (a as any).model || a.details?.model || "";
        return [
          a.timestamp ?? "",
          a.action ?? "",
          a.confidence ?? "",
          a.task_id ?? "",
          a.task_description ?? "",
          a.task_status ?? "",
          a.task_priority ?? "",
          a.task_group ?? "",
          m,
        ]
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(",");
      });
      const csv = [header.join(","), ...rows].join("\n");
      navigator.clipboard
        ?.writeText(csv)
        .catch(() =>
          setUsageExportError(
            "Failed to copy CSV; export is still shown below."
          )
        );
      setUsageExportFormat("csv");
      setUsageExportJson(csv);
    } catch (err) {
      setUsageExportError("Failed to generate CSV export.");
    }
  }, [timeFilteredRecentActions]);

  const maxActionConfidence =
    telemetry?.tasks.recent_actions?.reduce(
      (max, a) => Math.max(max, a.confidence ?? 0),
      0
    ) ?? 0;

  const confidenceBuckets = telemetry?.tasks.confidence_buckets;
  const confidenceTotal =
    (confidenceBuckets?.lt_0_4 ?? 0) +
    (confidenceBuckets?.["0_4_0_7"] ?? 0) +
    (confidenceBuckets?.gte_0_7 ?? 0);

  const percentToWidthClass = (value: number) => {
    const clamped = Math.max(0, Math.min(100, Math.round(value / 5) * 5));
    return `mini-bar-fill width-${clamped}`;
  };

  const telemetryPanel = (
    <div className="usage-telemetry">
      <div className="usage-telemetry-header">
        <span>Routing & tasks telemetry</span>
        <div className="usage-telemetry-actions">
          <button
            type="button"
            className="btn-secondary small"
            onClick={() => loadTelemetry(false)}
            disabled={isLoadingTelemetry}
          >
            Refresh
          </button>
          <button
            type="button"
            className="btn-link small"
            onClick={() => loadTelemetry(true)}
            disabled={isLoadingTelemetry}
          >
            Refresh & reset
          </button>
        </div>
      </div>
      {isLoadingTelemetry ? (
        <div className="usage-telemetry-body">Loading telemetry…</div>
      ) : telemetryError ? (
        <div className="usage-telemetry-body usage-telemetry-error">
          {telemetryError}
        </div>
      ) : !telemetry ? (
        <div className="usage-telemetry-body">
          No telemetry loaded yet. Click Refresh to fetch routing and task
          counters.
        </div>
      ) : (
        <div className="usage-telemetry-body">
          <div className="usage-telemetry-section">
            <div className="usage-telemetry-title">Auto-mode routes</div>
            {Object.keys(telemetry.llm.auto_routes).length === 0 ? (
              <div className="usage-telemetry-empty">
                No auto-mode calls recorded yet.
              </div>
            ) : (
              <ul className="usage-telemetry-list">
                {Object.entries(telemetry.llm.auto_routes).map(
                  ([mode, count]) => (
                    <li key={mode}>
                      <span className="usage-label">{mode}</span>
                      <span className="usage-value">{count}</span>
                    </li>
                  )
                )}
              </ul>
            )}
          </div>
          <div className="usage-telemetry-section">
            <div className="usage-telemetry-title">Fallbacks & tasks</div>
            <ul className="usage-telemetry-list">
              <li>
                <span className="usage-label">Fallback attempts</span>
                <span className="usage-value">
                  {telemetry.llm.fallback_attempts}
                </span>
              </li>
              <li>
                <span className="usage-label">Fallback successes</span>
                <span className="usage-value">
                  {telemetry.llm.fallback_success}
                </span>
              </li>
              <li>
                <span className="usage-label">Tasks auto-added</span>
                <span className="usage-value">
                  {telemetry.tasks.auto_added}
                </span>
              </li>
              <li>
                <span className="usage-label">Tasks auto-completed</span>
                <span className="usage-value">
                  {telemetry.tasks.auto_completed}
                </span>
              </li>
              <li>
                <span className="usage-label">Tasks auto-deduped</span>
                <span className="usage-value">
                  {telemetry.tasks.auto_deduped}
                </span>
              </li>
            </ul>
          </div>
          <div className="usage-telemetry-section">
            <div className="usage-telemetry-title">Confidence stats</div>
            {telemetry.tasks.confidence_stats ? (
              <ul className="usage-telemetry-list">
                <li>
                  <span className="usage-label">Min</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_stats.min}
                  </span>
                </li>
                <li>
                  <span className="usage-label">Max</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_stats.max}
                  </span>
                </li>
                <li>
                  <span className="usage-label">Avg</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_stats.avg}
                  </span>
                </li>
                <li>
                  <span className="usage-label">Count</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_stats.count}
                  </span>
                </li>
              </ul>
            ) : (
              <div className="usage-telemetry-empty">
                No confidence data yet.
              </div>
            )}
            {telemetry.tasks.confidence_buckets && (
              <ul className="usage-telemetry-list">
                <li>
                  <span className="usage-label">&lt;0.4</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_buckets.lt_0_4}
                  </span>
                  <div className="mini-bar">
                    <div
                      className={percentToWidthClass(
                        confidenceTotal
                          ? (telemetry.tasks.confidence_buckets.lt_0_4 /
                              confidenceTotal) *
                            100
                          : 0
                      )}
                    />
                  </div>
                </li>
                <li>
                  <span className="usage-label">0.4–0.7</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_buckets["0_4_0_7"]}
                  </span>
                  <div className="mini-bar">
                    <div
                      className={percentToWidthClass(
                        confidenceTotal
                          ? (telemetry.tasks.confidence_buckets["0_4_0_7"] /
                              confidenceTotal) *
                            100
                          : 0
                      )}
                    />
                  </div>
                </li>
                <li>
                  <span className="usage-label">≥0.7</span>
                  <span className="usage-value">
                    {telemetry.tasks.confidence_buckets.gte_0_7}
                  </span>
                  <div className="mini-bar">
                    <div
                      className={percentToWidthClass(
                        confidenceTotal
                          ? (telemetry.tasks.confidence_buckets.gte_0_7 /
                              confidenceTotal) *
                            100
                          : 0
                      )}
                    />
                  </div>
                </li>
              </ul>
            )}
          </div>
          <div className="usage-telemetry-section">
            <div className="usage-telemetry-title">Recent task actions</div>
            <div className="usage-telemetry-sub">
              Filters and time window apply to charts, list, and exports.
            </div>
            <div className="usage-charts-grid">
              <div className="usage-chart-card" data-testid="chart-actions">
                <div className="usage-chart-heading">Action types</div>
                {actionChartData.length ? (
                  <ul className="usage-chart-list">
                    {actionChartData.map((entry) => (
                      <li key={entry.key} className="usage-chart-row">
                        <div className="usage-chart-label">
                          {entry.label}
                          <span className="usage-chart-count">
                            {entry.count}
                          </span>
                        </div>
                        <div
                          className="mini-bar"
                          aria-label={`${entry.label} count ${entry.count}`}
                        >
                          <div
                            className={percentToWidthClass(entry.percent)}
                            aria-hidden
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="usage-telemetry-empty">
                    No filtered actions yet.
                  </div>
                )}
              </div>
              <div className="usage-chart-card" data-testid="chart-models">
                <div className="usage-chart-heading">Calls per model</div>
                {modelChartData.length ? (
                  <ul className="usage-chart-list">
                    {modelChartData.map((entry) => (
                      <li key={entry.key} className="usage-chart-row">
                        <div className="usage-chart-label">
                          {entry.label}
                          <span className="usage-chart-count">
                            {entry.count}
                          </span>
                        </div>
                        <div
                          className="mini-bar"
                          aria-label={`${entry.label} calls ${entry.count}`}
                        >
                          <div
                            className={percentToWidthClass(entry.percent)}
                            aria-hidden
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="usage-telemetry-empty">
                    No model data for the current filters.
                  </div>
                )}
              </div>
              <div className="usage-chart-card" data-testid="chart-confidence">
                <div className="usage-chart-heading">Confidence buckets</div>
                {confidenceChartData.length ? (
                  <ul className="usage-chart-list">
                    {confidenceChartData.map((entry) => (
                      <li key={entry.key} className="usage-chart-row">
                        <div className="usage-chart-label">
                          {entry.label}
                          <span className="usage-chart-count">
                            {entry.count}
                          </span>
                        </div>
                        <div
                          className="mini-bar"
                          aria-label={`${entry.label} ${entry.count}`}
                        >
                          <div
                            className={percentToWidthClass(entry.percent)}
                            aria-hidden
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="usage-telemetry-empty">
                    No confidence data for the filtered actions.
                  </div>
                )}
              </div>
              <div className="usage-chart-card" data-testid="chart-modes">
                <div className="usage-chart-heading">
                  Mode usage (auto routes)
                </div>
                <div className="usage-telemetry-sub">
                  Counters reset with “Refresh & reset”.
                </div>
                {modeUsageChartData.length ? (
                  <ul className="usage-chart-list">
                    {modeUsageChartData.map((entry) => (
                      <li key={entry.key} className="usage-chart-row">
                        <div className="usage-chart-label">
                          {entry.label}
                          <span className="usage-chart-count">
                            {entry.count}
                          </span>
                        </div>
                        <div
                          className="mini-bar"
                          aria-label={`${entry.label} routes ${entry.count}`}
                        >
                          <div
                            className={percentToWidthClass(entry.percent)}
                            aria-hidden
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="usage-telemetry-empty">
                    No auto-mode routes recorded yet.
                  </div>
                )}
              </div>
            </div>
            <div className="usage-export">
              <div className="usage-export-header">
                <span>Export filtered actions</span>
                <span className="usage-export-meta">
                  {timeFilteredRecentActions.length} action
                  {timeFilteredRecentActions.length === 1 ? "" : "s"} in view
                </span>
              </div>
              <div className="usage-export-buttons">
                <button
                  type="button"
                  className="btn-link tiny"
                  onClick={copyRecentActionsJson}
                >
                  Copy JSON
                </button>
                <button
                  type="button"
                  className="btn-link tiny"
                  onClick={copyRecentActionsCsv}
                >
                  Copy CSV
                </button>
              </div>
              {usageExportError && (
                <div className="usage-telemetry-error">{usageExportError}</div>
              )}
              {usageExportJson && (
                <pre
                  className="usage-export-json"
                  data-testid="usage-export-preview"
                >
                  {usageExportFormat
                    ? `${usageExportFormat.toUpperCase()} export\n`
                    : ""}
                  {usageExportJson}
                </pre>
              )}
            </div>
            {timeFilteredRecentActions && timeFilteredRecentActions.length > 0 ? (
              <ul
                className="usage-telemetry-list"
                data-testid="recent-actions-list"
              >
                {timeFilteredRecentActions.map((a, idx) => (
                  <li key={`${a.timestamp}-${idx}`}>
                    <div className="usage-label">
                      {a.action} · conf {(a.confidence ?? 0).toFixed(2)}
                      {(() => {
                        const actionModel =
                          a.details?.model ||
                          (a as any).model ||
                          lastUsageModel;
                        return actionModel ? (
                          <span className="usage-subtext">
                            (model: {actionModel})
                          </span>
                        ) : null;
                      })()}
                    </div>
                    <div className="usage-telemetry-sub">
                      {a.task_description ?? "—"}
                    </div>
                    <div className="usage-telemetry-sub">
                      {a.task_status ? `status: ${a.task_status}` : ""}
                      {a.task_priority ? ` · priority: ${a.task_priority}` : ""}
                      {a.task_group ? ` · group: ${a.task_group}` : ""}
                      {a.task_blocked_reason
                        ? ` · blocked: ${a.task_blocked_reason}`
                        : ""}
                    </div>
                    {(a.details?.matched_text || a.matched_text) ? (
                      <div className="usage-telemetry-sub">
                        matched: {a.details?.matched_text ?? a.matched_text}
                      </div>
                    ) : null}
                    <div className="mini-bar">
                      <div
                        className={percentToWidthClass(
                          ((a.confidence ?? 0) /
                            (maxActionConfidence || 1)) *
                            100
                        )}
                      />
                    </div>
                    {a.timestamp ? (
                      <div className="usage-telemetry-sub">at: {a.timestamp}</div>
                    ) : null}
                    {a.task_auto_notes ? (
                      <div className="usage-telemetry-sub">
                        notes: {a.task_auto_notes}
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="usage-telemetry-empty">
                No recent task actions recorded yet.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const executeCommandPaletteAction = useCallback(
    (actionIndex: number) => {
      const action = filteredCommandActions[actionIndex];
      if (!action) return;
      action.action();
      setShowCommandPalette(false);
      setCommandPaletteQuery("");
    },
    [filteredCommandActions]
  );

  const handleCommandPaletteInputKeyDown = (
    event: KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!filteredCommandActions.length) {
        return;
      }
      setCommandPaletteIndex((prev) =>
        Math.min(prev + 1, filteredCommandActions.length - 1)
      );
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!filteredCommandActions.length) {
        return;
      }
      setCommandPaletteIndex((prev) => Math.max(prev - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (!filteredCommandActions.length) return;
      executeCommandPaletteAction(commandPaletteIndex);
      return;
    }
  };

  const handleRefreshAllRightPanels = () => {
    if (selectedProjectId != null) {
      loadTasks(selectedProjectId);
      loadProjectDocs(selectedProjectId);
      loadProjectFiles(selectedProjectId, fsCurrentSubpath || "");
      loadProjectInstructions(selectedProjectId);
      loadProjectDecisions(selectedProjectId);
      loadFolders(selectedProjectId);
      loadMemoryItems(selectedProjectId);
    }
    if (selectedConversationId != null) {
      loadUsageForConversation(selectedConversationId);
      refreshMessages(selectedConversationId);
    }
  };

  useEffect(() => {
    if (filteredCommandActions.length === 0) {
      setCommandPaletteIndex(0);
      return;
    }
    setCommandPaletteIndex((prev) =>
      Math.min(prev, filteredCommandActions.length - 1)
    );
  }, [filteredCommandActions]);

  useEffect(() => {
    if (searchTab === "messages") {
      setSearchDocFilter("all");
    } else {
      setSearchConversationFilter("all");
      setSearchFolderFilter("all");
    }
  }, [searchTab]);

  useEffect(() => {
    if (!selectedConversationId) {
      setUsageConversationId(null);
      setUsage(null);
      return;
    }
    setUsageConversationId((prev) => prev ?? selectedConversationId);
  }, [selectedConversationId]);

  useEffect(() => {
    if (
      highlightNewDrafts &&
      !projectDecisions.some(
        (decision) => decision.is_draft && decision.auto_detected
      )
    ) {
      setHighlightNewDrafts(false);
    }
  }, [highlightNewDrafts, projectDecisions]);

  useEffect(() => {
    draftSeenRef.current.clear();
    setHighlightNewDrafts(false);
  }, [selectedProjectId]);

  useEffect(() => {
    setSearchConversationFilter("all");
    setSearchFolderFilter("all");
    setSearchDocFilter("all");
    setSearchMessageHits([]);
    setSearchDocHits([]);
    setHighlightedDocId(null);
  }, [selectedProjectId]);

  const hasUnsavedFileChanges =
    fsSelectedRelPath != null && fsEditedContent !== fsOriginalContent;
  const parseTagsInput = useCallback((value: string): string[] => {
    return value
      .split(",")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);
  }, []);
  const instructionsDirty =
    projectInstructions !== projectInstructionsSaved ||
    projectPinnedNote !== projectPinnedNoteSaved;

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

  const loadRepoIngestionJobs = useCallback(
    async (projectId: number) => {
      setIsLoadingRepoJobs(true);
      try {
        const res = await fetch(
          `${BACKEND_BASE}/projects/${projectId}/ingestion_jobs?limit=20`
        );
        if (!res.ok) {
          console.error("Fetching ingestion jobs failed:", res.status);
          return;
        }
        const jobs: IngestionJob[] = await res.json();
        setRepoIngestionJobs(jobs);
      } catch (error) {
        console.error("Fetching ingestion jobs threw:", error);
      } finally {
        setIsLoadingRepoJobs(false);
      }
    },
    []
  );

  useEffect(() => {
    if (selectedProjectId && rightTab === "docs") {
      loadRepoIngestionJobs(selectedProjectId);
    }
  }, [selectedProjectId, rightTab, loadRepoIngestionJobs]);

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

  const loadMemoryItems = async (projectId: number) => {
    setIsLoadingMemory(true);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/memory`
      );
      if (!res.ok) {
        console.error("Fetching memory items failed:", res.status);
        setMemoryItems([]);
        return;
      }
      const data: MemoryItem[] = await res.json();
      setMemoryItems(data);
    } catch (e) {
      console.error("Fetching memory items threw:", e);
      setMemoryItems([]);
    } finally {
      setIsLoadingMemory(false);
    }
  };


  const loadTasks = async (projectId: number) => {
    setIsLoadingTaskSuggestions(true);
    setTaskSuggestionError(null);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/tasks/overview`
      );
      if (!res.ok) throw new Error(`Failed with status ${res.status}`);
      const data: TaskOverview = await res.json();
      setTasks(data.tasks || []);
      setTaskSuggestions(data.suggestions || []);
    } catch (e) {
      console.error("Fetching tasks overview failed:", e);
      setTaskSuggestionError("Could not load tasks/suggestions.");
      setTasks([]);
      setTaskSuggestions([]);
    } finally {
      setIsLoadingTaskSuggestions(false);
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
        pinned_note_text?: string | null;
      } = await res.json();
      const instructionText = data.instruction_text ?? "";
      const pinnedNote = data.pinned_note_text ?? "";
      setProjectInstructions(instructionText);
      setProjectInstructionsSaved(instructionText);
      setProjectPinnedNote(pinnedNote);
      setProjectPinnedNoteSaved(pinnedNote);
      setProjectInstructionsUpdatedAt(data.instruction_updated_at ?? null);
      setProjectInstructionsError(null);
    } catch (e) {
      console.error("Fetching project instructions failed:", e);
      setProjectInstructions("");
      setProjectInstructionsUpdatedAt(null);
      setProjectInstructionsSaved("");
      setProjectPinnedNote("");
      setProjectPinnedNoteSaved("");
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
            pinned_note_text: projectPinnedNote,
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
      setProjectInstructionsSaved(data.instruction_text ?? "");
      setProjectPinnedNote(data.pinned_note_text ?? "");
      setProjectPinnedNoteSaved(data.pinned_note_text ?? "");
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
      const unseenDrafts = data.filter(
        (decision) =>
          decision.is_draft &&
          decision.auto_detected &&
          !draftSeenRef.current.has(decision.id)
      );
      if (unseenDrafts.length > 0) {
        unseenDrafts.forEach((decision) =>
          draftSeenRef.current.add(decision.id)
        );
        addToast(
          `Detected ${unseenDrafts.length} decision draft${
            unseenDrafts.length === 1 ? "" : "s"
          } from the latest chat.`,
          "success"
        );
        setHighlightNewDrafts(true);
      }
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
      const tags = parseTagsInput(newDecisionTags);
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
            tags,
            status: newDecisionStatus,
            is_draft: newDecisionStatus === "draft",
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
      setNewDecisionTags("");
      setNewDecisionStatus("recorded");
      addToast("Decision saved", "success");
    } catch (e) {
      console.error("Creating decision threw:", e);
      setDecisionsError("Unexpected error while saving decision.");
    } finally {
      setIsSavingDecision(false);
    }
  };

  const updateDecision = async (
    decisionId: number,
    payload: Record<string, unknown>,
    successMessage?: string
  ) => {
    if (!selectedProjectId) {
      return false;
    }
    try {
      const res = await fetch(`${BACKEND_BASE}/decisions/${decisionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        console.error("Update decision failed:", res.status);
        setDecisionsError("Failed to update decision.");
        return false;
      }
      await loadProjectDecisions(selectedProjectId);
      if (successMessage) {
        addToast(successMessage, "success");
      }
      return true;
    } catch (e) {
      console.error("Update decision threw:", e);
      setDecisionsError("Unexpected error while updating decision.");
      return false;
    }
  };

  const handleDecisionStatusSelect = (
    decision: ProjectDecision,
    status: string
  ) => {
    updateDecision(decision.id, {
      status,
      is_draft: status === "draft" ? decision.is_draft : false,
    });
  };

  const handleDecisionConfirmDraft = (decision: ProjectDecision) =>
    updateDecision(
      decision.id,
      { status: "recorded", is_draft: false },
      "Decision recorded"
    );

  const handleDecisionDismissDraft = (decision: ProjectDecision) =>
    updateDecision(
      decision.id,
      { status: "dismissed", is_draft: false },
      "Draft dismissed"
    );

  const handleDecisionEditTags = (decision: ProjectDecision) => {
    const current = decision.tags.join(", ");
    const next = window.prompt(
      "Edit tags (comma separated)",
      current.length ? current : ""
    );
    if (next === null) return;
    const tags = parseTagsInput(next);
    updateDecision(decision.id, { tags }, "Tags updated");
  };

  const handleDecisionCreateTask = async (decision: ProjectDecision) => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    const description = decision.details
      ? `Follow-up: ${decision.title} — ${decision.details}`
      : `Follow-up: ${decision.title}`;
    try {
      const res = await fetch(`${BACKEND_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId,
          description,
        }),
      });
      if (!res.ok) {
        console.error("Create follow-up task failed:", res.status);
        alert("Failed to create task. See backend logs.");
        return;
      }
      const task: Task = await res.json();
      await loadTasks(selectedProjectId);
      await updateDecision(
        decision.id,
        { follow_up_task_id: task.id },
        "Follow-up task attached"
      );
    } catch (e) {
      console.error("Create follow-up task threw:", e);
      alert("Unexpected error while creating follow-up task.");
    }
  };

  const handleDecisionClearFollowUp = (decision: ProjectDecision) => {
    updateDecision(
      decision.id,
      { follow_up_task_id: 0 },
      "Follow-up task cleared"
    );
  };

  const handleDecisionCreateMemory = async (decision: ProjectDecision) => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/memory`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: decision.title,
            content: decision.details || decision.title,
            tags: decision.tags,
            pinned: false,
            source_conversation_id: decision.source_conversation_id ?? null,
          }),
        }
      );
      if (!res.ok) {
        console.error("Create memory from decision failed:", res.status);
        alert("Failed to create memory. See backend logs.");
        return;
      }
      await loadMemoryItems(selectedProjectId);
      addToast("Decision saved to memory", "success");
    } catch (e) {
      console.error("Create memory from decision threw:", e);
      alert("Unexpected error while creating memory.");
    }
  };

  const handleDecisionCopy = async (decision: ProjectDecision) => {
    const text = `${decision.title}\n\n${decision.details ?? ""}`.trim();
    try {
      await navigator.clipboard.writeText(text);
      addToast("Decision copied to clipboard", "success");
    } catch (e) {
      console.error("Clipboard copy failed:", e);
      alert("Failed to copy to clipboard.");
    }
  };

  const handleOpenDecisionConversation = async (
    conversationId: number | null | undefined
  ) => {
    if (!conversationId) return;
    setSelectedConversationId(conversationId);
    await refreshMessages(conversationId);
    await loadUsageForConversation(conversationId);
  };

  const loadUsageForConversation = async (conversationId: number) => {
    try {
      setIsLoadingUsage(true);
      setUsageConversationId(conversationId);
      setUsageError(null);
      const res = await fetch(
        `${BACKEND_BASE}/conversations/${conversationId}/usage`
      );
      if (!res.ok) {
        console.error("Fetching usage failed:", res.status);
        setUsage(null);
        setUsageError(`Failed to load usage (status ${res.status}).`);
        return;
      }
      const data: ConversationUsage = await res.json();
      setUsage(data);
    } catch (e) {
      console.error("Fetching usage threw:", e);
      setUsage(null);
      setUsageError("Unexpected error loading usage.");
    } finally {
      setIsLoadingUsage(false);
    }
  };

  const loadTelemetry = async (reset: boolean = false) => {
    try {
      setIsLoadingTelemetry(true);
      setTelemetryError(null);
      const url = new URL(`${BACKEND_BASE}/debug/telemetry`);
      if (reset) {
        url.searchParams.set("reset", "true");
      }
      const res = await fetch(url.toString());
      if (!res.ok) {
        console.error("Fetching telemetry failed:", res.status);
        setTelemetry(null);
        setTelemetryError(`Failed to load telemetry (status ${res.status}).`);
        return;
      }
      const data: TelemetrySnapshot = await res.json();
      setTelemetry(data);
    } catch (e: any) {
      console.error("Fetching telemetry threw:", e);
      setTelemetry(null);
      const msg = e?.message
        ? `Unexpected error: ${e.message}`
        : "Unexpected error loading telemetry.";
      setTelemetryError(msg);
    } finally {
      setIsLoadingTelemetry(false);
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
    setFileEditPreview(null);
    setFileEditError(null);
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
    setFileEditError(null);

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
        addToast("AI edit applied", "success");
        setFileEditPreview(null);
        setFileEditError(null);
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

  const handlePreviewFileEdit = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    if (!fileEditProposal) {
      alert("No AI file edit proposal to preview.");
      return;
    }

    setIsPreviewingFileEdit(true);
    setFileEditError(null);
    setFileEditPreview(null);

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
            apply_changes: false,
            include_diff: true,
            conversation_id: selectedConversationId,
            message_id: null,
          }),
        }
      );

      if (!res.ok) {
        console.error("Preview AI edit failed:", res.status);
        setFileEditError("Preview failed. See backend logs.");
        addToast("AI edit preview failed", "error");
        return;
      }

      const data = await res.json();
      setFileEditPreview({
        diff: data.diff ?? null,
        original_content: data.original_content ?? "",
        edited_content: data.edited_content ?? "",
      });
      addToast("AI edit preview ready", "success");
    } catch (e) {
      console.error("Preview AI edit threw:", e);
      setFileEditError("Unexpected error while previewing AI edit.");
      addToast("AI edit preview error", "error");
    } finally {
      setIsPreviewingFileEdit(false);
    }
  };

  const handleDismissFileEditProposal = () => {
    setFileEditProposal(null);
    setFileEditStatus(null);
    setFileEditPreview(null);
    setFileEditError(null);
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
          mode:
            modelOverrideMode !== "default" ? modelOverrideMode : chatMode,
          model:
            (modelOverrideMode === "custom"
              ? modelOverrideCustom
              : modelOverride) ||
            null,
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
      setManualTerminalHistory((prev) => {
        const entry: CommandHistoryEntry = {
          id: Date.now(),
          command: body.command,
          cwd: body.cwd && body.cwd.trim() ? body.cwd : "(project root)",
          timestamp: new Date().toISOString(),
        };
        return [entry, ...prev].slice(0, 6);
      });
      addToast("Command executed", "success");

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
      addToast("Manual command failed", "error");
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
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setShowCommandPalette(true);
        setCommandPaletteQuery("");
        setCommandPaletteIndex(0);
        return;
      }

      if (event.altKey && !event.ctrlKey && !event.metaKey) {
        switch (event.key) {
          case "1":
            setRightTab("tasks");
            event.preventDefault();
            return;
          case "2":
            setRightTab("files");
            event.preventDefault();
            return;
          case "3":
            setRightTab("docs");
            event.preventDefault();
            return;
          case "4":
            setRightTab("search");
            event.preventDefault();
            return;
          case "5":
            setRightTab("terminal");
            event.preventDefault();
            return;
          case "6":
            setRightTab("usage");
            event.preventDefault();
            return;
          case "7":
            setRightTab("notes");
            event.preventDefault();
            return;
          case "8":
            setRightTab("memory");
            event.preventDefault();
            return;
          case "s":
            chatSectionRef.current
              ?.querySelector<HTMLTextAreaElement>(".chat-input")
              ?.focus();
            event.preventDefault();
            return;
          default:
            break;
        }
      }

      if (showCommandPalette && event.key === "Escape") {
        setShowCommandPalette(false);
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown as any);
    return () => window.removeEventListener("keydown", handleKeyDown as any);
  }, [setRightTab, showCommandPalette]);

  // ---------- When project changes, load its conversations + docs + tasks + files ----------

  useEffect(() => {
    if (selectedProjectId == null) {
      setConversations([]);
      setMessages([]);
      setProjectDocs([]);
      setTasks([]);
      setTaskSuggestions([]);
      setTaskSuggestionError(null);
      setIsLoadingTaskSuggestions(false);
      setUsage(null);
      setFolders([]);
      setMemoryItems([]);
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
    loadMemoryItems(selectedProjectId);
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
          mode:
            modelOverrideMode !== "default" ? modelOverrideMode : chatMode,
          model:
            (modelOverrideMode === "custom"
              ? modelOverrideCustom
              : modelOverride) ||
            null,
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
    setFileEditPreview(null);
    setFileEditError(null);
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

  const openMemoryModal = (
    initial?: {
      title?: string;
      content?: string;
      messageId?: number;
    }
  ) => {
    setMemoryFormTitle(initial?.title || "");
    setMemoryFormContent(initial?.content || "");
    setMemoryFormTags("");
    setMemoryFormPinned(false);
    setMemoryFormExpiresAt("");
    setMemoryFormSourceMessageId(initial?.messageId ?? null);
    setMemoryFormError(null);
    setMemoryModalOpen(true);
  };

  const closeMemoryModal = () => {
    setMemoryModalOpen(false);
  };

  const handleSaveMemoryItem = async () => {
    if (!selectedProjectId) {
      alert("No project selected.");
      return;
    }
    const title = memoryFormTitle.trim();
    const content = memoryFormContent.trim();
    if (!title || !content) {
      setMemoryFormError("Title and content are required.");
      return;
    }
    const tags = memoryFormTags
      .split(",")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);

    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/memory`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            content,
            tags,
            pinned: memoryFormPinned,
            expires_at: memoryFormExpiresAt || null,
            source_conversation_id: selectedConversationId,
            source_message_id: memoryFormSourceMessageId,
          }),
        }
      );
      if (!res.ok) {
        console.error("Create memory failed:", res.status);
        setMemoryFormError("Failed to save memory item.");
        return;
      }
      await loadMemoryItems(selectedProjectId);
      setMemoryModalOpen(false);
      addToast("Memory saved", "success");
    } catch (e) {
      console.error("Create memory threw:", e);
      setMemoryFormError("Unexpected error while saving memory.");
    }
  };

  const handleToggleMemoryPinned = async (item: MemoryItem) => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/memory_items/${item.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pinned: !item.pinned }),
        }
      );
      if (!res.ok) {
        console.error("Toggle pinned failed:", res.status);
        alert("Failed to update memory item.");
        return;
      }
      if (selectedProjectId != null) {
        await loadMemoryItems(selectedProjectId);
      }
    } catch (e) {
      console.error("Toggle pinned threw:", e);
      alert("Unexpected error while updating memory.");
    }
  };

  const handleDeleteMemory = async (id: number) => {
    if (
      !window.confirm(
        "Delete this memory item? This cannot be undone."
      )
    ) {
      return;
    }
    try {
      const res = await fetch(
        `${BACKEND_BASE}/memory_items/${id}`,
        {
          method: "DELETE",
        }
      );
      if (!res.ok) {
        console.error("Delete memory failed:", res.status);
        alert("Failed to delete memory item.");
        return;
      }
      if (selectedProjectId != null) {
        await loadMemoryItems(selectedProjectId);
      }
    } catch (e) {
      console.error("Delete memory threw:", e);
      alert("Unexpected error while deleting memory.");
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

      if (selectedProjectId) {
        await loadTasks(selectedProjectId);
      }
    } catch (e) {
      console.error("Update task threw:", e);
      alert("Unexpected error while updating task.");
    }
  };

  const handleApproveTaskSuggestion = async (
    suggestion: TaskSuggestion
  ): Promise<void> => {
    if (!selectedProjectId) {
      addToast("Select a project first", "error");
      return;
    }
    setSuggestionProcessing(suggestion.id, true);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/task_suggestions/${suggestion.id}/approve`,
        {
          method: "POST",
        }
      );
      if (!res.ok) {
        throw new Error(`Status ${res.status}`);
      }
      await Promise.all([
        loadTasks(selectedProjectId),
      ]);
      addToast("Suggestion applied", "success");
    } catch (e) {
      console.error("Approve suggestion failed:", e);
      addToast("Failed to apply suggestion", "error");
    } finally {
      setSuggestionProcessing(suggestion.id, false);
    }
  };

  const handleDismissTaskSuggestion = async (
    suggestion: TaskSuggestion
  ): Promise<void> => {
    if (!selectedProjectId) {
      addToast("Select a project first", "error");
      return;
    }
    setSuggestionProcessing(suggestion.id, true);
    try {
      const res = await fetch(
        `${BACKEND_BASE}/task_suggestions/${suggestion.id}/dismiss`,
        {
          method: "POST",
        }
      );
      if (!res.ok) {
        throw new Error(`Status ${res.status}`);
      }
      await loadTasks(selectedProjectId);
      addToast("Suggestion dismissed", "success");
    } catch (e) {
      console.error("Dismiss suggestion failed:", e);
      addToast("Failed to dismiss suggestion", "error");
    } finally {
      setSuggestionProcessing(suggestion.id, false);
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

  const handleRefreshIngestionJobs = () => {
    if (selectedProjectId) {
      loadRepoIngestionJobs(selectedProjectId);
    }
  };

  const handleCancelIngestionJob = async (jobId: number) => {
    if (!selectedProjectId) return;
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/ingestion_jobs/${jobId}/cancel`,
        {
          method: "POST",
        }
      );
      if (!res.ok) {
        console.error("Cancel ingestion job failed:", res.status);
        addToast("Failed to cancel ingestion job", "error");
        return;
      }
      const job: IngestionJob = await res.json();
      if (repoIngestionJob && repoIngestionJob.id === job.id) {
        setRepoIngestionJob(job);
      }
      await loadRepoIngestionJobs(selectedProjectId);
      addToast("Ingestion job cancellation requested", "success");
    } catch (error) {
      console.error("Cancel ingestion job threw:", error);
      addToast("Failed to cancel ingestion job", "error");
    }
  };

  const pollRepoIngestionJob = async (
    projectId: number,
    jobId: number
  ): Promise<void> => {
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${projectId}/ingestion_jobs/${jobId}`
      );
      if (!res.ok) {
        return;
      }

      const job: IngestionJob = await res.json();
      setRepoIngestionJob(job);

      if (job.status === "completed") {
        stopRepoIngestionPolling();
        setIsIngestingRepo(false);
        addToast("Repo ingestion completed", "success");
        await loadProjectDocs(projectId);
        await loadRepoIngestionJobs(projectId);
      } else if (job.status === "failed") {
        stopRepoIngestionPolling();
        setIsIngestingRepo(false);
        addToast(job.error_message || "Repo ingestion failed", "error");
        await loadRepoIngestionJobs(projectId);
      } else if (job.status === "cancelled") {
        stopRepoIngestionPolling();
        setIsIngestingRepo(false);
        addToast("Repo ingestion cancelled", "success");
        await loadRepoIngestionJobs(projectId);
      }
    } catch (error) {
      console.error("Failed to poll ingestion job", error);
    }
  };

  const startRepoIngestionPolling = (
    projectId: number,
    jobId: number
  ): void => {
    stopRepoIngestionPolling();
    pollRepoIngestionJob(projectId, jobId);
    // Poll every 5 seconds instead of 2 to reduce database contention
    // SQLite can have locking issues with frequent concurrent reads/writes
    repoIngestionPollRef.current = window.setInterval(() => {
      pollRepoIngestionJob(projectId, jobId);
    }, 5000);
  };

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
    setRepoIngestionJob(null);
    stopRepoIngestionPolling();
    try {
      const res = await fetch(
        `${BACKEND_BASE}/projects/${selectedProjectId}/ingestion_jobs`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            kind: "repo",
            source: repoRootPath.trim(),
            name_prefix: repoNamePrefix.trim() || null,
            include_globs: null,
          }),
        }
      );

      if (!res.ok) {
        console.error("Repo ingestion failed:", res.status);
        alert("Repo ingestion failed; see backend logs.");
        setIsIngestingRepo(false);
        return;
      }

      const job: IngestionJob = await res.json();
      setRepoIngestionJob(job);
      startRepoIngestionPolling(selectedProjectId, job.id);
      await loadRepoIngestionJobs(selectedProjectId);
    } catch (e) {
      console.error("Repo ingestion threw:", e);
      alert("Unexpected error while ingesting repo.");
      setIsIngestingRepo(false);
      stopRepoIngestionPolling();
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
        const conversationIdFilter =
          searchConversationFilter === "all"
            ? null
            : searchConversationFilter;
        const folderIdFilter =
          searchFolderFilter === "all" ? null : searchFolderFilter;
        const res = await fetch(`${BACKEND_BASE}/search/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: selectedProjectId,
            query: searchQuery.trim(),
            conversation_id: conversationIdFilter,
            folder_id: folderIdFilter,
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
            document_id:
              searchDocFilter === "all" ? null : searchDocFilter,
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

  const clearSearchFilters = () => {
    setSearchConversationFilter("all");
    setSearchFolderFilter("all");
    setSearchDocFilter("all");
  };

  const handleOpenConversationFromSearch = async (
    conversationId: number
  ) => {
    setSelectedConversationId(conversationId);
    await refreshMessages(conversationId);
    await loadUsageForConversation(conversationId);
  };

  const handleOpenDocFromSearch = (documentId: number) => {
    setHighlightedDocId(documentId);
    setShowAllDocs(true);
    setRightTab("docs");
  };

  const handleUsageConversationChange: React.ChangeEventHandler<
    HTMLSelectElement
  > = (event) => {
    const value = event.target.value;
    if (!value) {
      setUsageConversationId(null);
      setUsage(null);
      return;
    }
    const convId = Number(value);
    loadUsageForConversation(convId);
    loadTelemetry(false);
  };

  const handleFocusCurrentConversationUsage = () => {
    if (!selectedConversationId) return;
    loadUsageForConversation(selectedConversationId);
    loadTelemetry(false);
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
          <a className="skip-link" href="#chat-pane">
            Skip to chat
          </a>
          <div className="backend-pill">
            Backend:{" "}
            <span className="backend-pill-version">
              {backendVersion ? `InfinityWindow v${backendVersion}` : "…"}
            </span>
          </div>
        </div>
      </header>

      {toasts.length > 0 && (
        <div className="toast-stack" aria-live="polite">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={"toast " + toast.type}
            >
              {toast.message}
            </div>
          ))}
        </div>
      )}

      <main className={"app-main" + (leftCollapsed ? " left-collapsed" : "")}>
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
                aria-label="Select project"
                title="Select project"
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
                      aria-label="Filter conversations by folder"
                      title="Filter conversations by folder"
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
                              aria-label="Conversation title"
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
                                    >
                                      {c.folder_name || "Unsorted"}
                                      {c.folder_color
                                        ? ` (${c.folder_color})`
                                        : ""}
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
                            aria-label="Move conversation to folder"
                            title="Move conversation to folder"
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

          {memoryModalOpen && (
            <div className="folder-modal-backdrop">
              <div className="folder-modal memory-modal">
                <h3>Remember this</h3>
                <div className="folder-form-field">
                  <label htmlFor="memory-title">Title</label>
                  <input
                    id="memory-title"
                    type="text"
                    value={memoryFormTitle}
                    onChange={(e) =>
                      setMemoryFormTitle(e.target.value)
                    }
                  />
                </div>
                <div className="folder-form-field">
                  <label htmlFor="memory-content">Content</label>
                  <textarea
                    id="memory-content"
                    value={memoryFormContent}
                    onChange={(e) =>
                      setMemoryFormContent(e.target.value)
                    }
                  />
                </div>
                <div className="folder-form-field">
                  <label htmlFor="memory-tags">
                    Tags (comma-separated)
                  </label>
                  <input
                    id="memory-tags"
                    type="text"
                    value={memoryFormTags}
                    onChange={(e) =>
                      setMemoryFormTags(e.target.value)
                    }
                  />
                </div>
                <div className="folder-form-field">
                  <label htmlFor="memory-expires">
                    Expires at (optional)
                  </label>
                  <input
                    id="memory-expires"
                    type="datetime-local"
                    value={memoryFormExpiresAt}
                    onChange={(e) =>
                      setMemoryFormExpiresAt(e.target.value)
                    }
                  />
                </div>
                <label className="folder-checkbox">
                  <input
                    type="checkbox"
                    checked={memoryFormPinned}
                    onChange={(e) =>
                      setMemoryFormPinned(e.target.checked)
                    }
                  />
                  Pin this memory (always inject into prompt)
                </label>
                {memoryFormError && (
                  <div className="notes-error">{memoryFormError}</div>
                )}
                <div className="folder-modal-actions">
                  <div />
                  <div className="folder-modal-actions-right">
                    <button
                      type="button"
                      className="btn-link small"
                      onClick={closeMemoryModal}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn-secondary small"
                      onClick={handleSaveMemoryItem}
                    >
                      Save memory
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* MIDDLE: Chat */}
        <section
          className="column column-middle"
          ref={chatSectionRef}
          id="chat-pane"
        >
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
                    <div className="chat-message-content">
                      {m.content}
                      {selectedProjectId && selectedConversationId && (
                        <button
                          type="button"
                          className="remember-btn"
                          onClick={() =>
                            openMemoryModal({
                              title:
                                m.role === "user"
                                  ? "User insight"
                                  : "Assistant insight",
                              content: m.content,
                              messageId: m.id,
                            })
                          }
                        >
                          Remember this
                        </button>
                      )}
                    </div>
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
                <label htmlFor="chat-mode">Mode</label>
                <select
                  id="chat-mode"
                  aria-label="Chat mode"
                  title="Chat mode"
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
              <div className="chat-model-override">
                <label htmlFor="model-override-select">Model override</label>
                <select
                  id="model-override-select"
                  aria-label="Model override"
                  title="Model override"
                  value={modelOverrideMode}
                  onChange={(e) => setModelOverrideMode(e.target.value)}
                >
                  <option value="default">Default (use Mode)</option>
                  <option value="auto">auto</option>
                  <option value="fast">fast</option>
                  <option value="deep">deep</option>
                  <option value="budget">budget</option>
                  <option value="research">research</option>
                  <option value="code">code</option>
                  <option value="custom">Custom</option>
                </select>
                {modelOverrideMode === "custom" && (
                  <input
                    id="model-override-input"
                    type="text"
                    placeholder="Custom model id"
                    aria-label="Custom model id"
                    value={modelOverrideCustom}
                    onChange={(e) => setModelOverrideCustom(e.target.value)}
                  />
                )}
                <input
                  id="model-override-input-main"
                  type="text"
                  placeholder="Optional model id"
                  aria-label="Optional model id"
                  value={modelOverride}
                  onChange={(e) => setModelOverride(e.target.value)}
                />
                <div className="chat-model-override-hint">
                  Leave blank to let mode choose automatically; use override or custom to force a model.
                </div>
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
        <section className="column column-right" ref={rightColumnRef}>
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
                "right-tab" + (rightTab === "files" ? " active" : "")
              }
              onClick={() => setRightTab("files")}
            >
              Files
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
                "right-tab" + (rightTab === "memory" ? " active" : "")
              }
              onClick={() => setRightTab("memory")}
            >
              Memory
            </button>
          </div>
          <div className="right-tabs-toolbar">
            <button
              type="button"
              className="btn-link tiny"
              onClick={handleRefreshAllRightPanels}
            >
              Refresh all
            </button>
          </div>

          {rightTab === "tasks" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Project tasks</span>
                    <span className="tab-pill">{tasks.length}</span>
                  </div>
                  <div className="tab-toolbar">
                    {selectedProjectId && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() => loadTasks(selectedProjectId)}
                      >
                        Refresh
                      </button>
                    )}
                    {tasks.length > 5 && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() => setShowAllTasks((prev) => !prev)}
                      >
                        {showAllTasks ? "Show less" : "Show more"}
                      </button>
                    )}
                    <button
                      type="button"
                      className={
                        "btn-link tiny suggestions-toggle" +
                        (showSuggestionsPanel ? " active" : "")
                      }
                      onClick={() =>
                        setShowSuggestionsPanel((prev) => !prev)
                      }
                    >
                      Suggested changes
                      <span className="tab-pill">
                        {pendingSuggestionCount}
                      </span>
                    </button>
                  </div>
                </div>
                <div className="tab-section-body">
                  <div className="task-legend">
                    <span className="task-priority-chip priority-critical">
                      Critical
                    </span>
                    <span className="task-priority-chip priority-high">
                      High
                    </span>
                    <span className="task-priority-chip priority-normal">
                      Normal
                    </span>
                    <span className="task-priority-chip priority-low">Low</span>
                    <span className="task-blocked-chip subtle">
                      Blocked shown when a blocker is detected
                    </span>
                  </div>
                  <div className="tasks-new condensed">
                <input
                  className="tasks-input"
                  type="text"
                      placeholder="Add a task..."
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
                  <div className="tasks-list compact">
                {selectedProjectId == null ? (
                  <div className="tasks-empty">No project selected.</div>
                ) : tasks.length === 0 ? (
                  <div className="tasks-empty">
                    No tasks yet. Add one above.
                  </div>
                ) : (
                  <ul>
                    {visibleTasks.map((task) => {
                      const priority = (task.priority || "normal").toLowerCase();
                      return (
                      <li key={task.id} className="task-item">
                        <input
                          type="checkbox"
                          checked={task.status === "done"}
                          aria-label={`Toggle status for ${task.description}`}
                          onChange={() => handleToggleTaskStatus(task)}
                        />
                          <div className="task-body">
                        <div
                          className={
                            "task-text" +
                            (task.status === "done" ? " done" : "")
                          }
                        >
                          {task.description}
                            </div>
                        <div className="task-meta">
                              <span
                                className={`task-priority-chip priority-${priority}`}
                              >
                                {task.priority || "normal"}
                              </span>
                              {task.group && (
                                <span className={`task-group-chip group-${task.group}`}>
                                  {task.group}
                                </span>
                              )}
                          {typeof task.auto_confidence === "number" && (
                            <span className="task-confidence-chip">
                              {(task.auto_last_action || "auto").replaceAll("_", " ")} ·{" "}
                              {task.auto_confidence.toFixed(2)}
                            </span>
                          )}
                              {task.blocked_reason && (
                                <span className="task-blocked-chip">
                                  Blocked: {task.blocked_reason}
                                </span>
                              )}
                            </div>
                            {task.auto_notes && (
                              <div className="task-notes">
                                {task.auto_notes}
                              </div>
                            )}
                        </div>
                      </li>
                      );
                    })}
                  </ul>
                )}
              </div>
                </div>
              </section>
              {showSuggestionsPanel && (
                <section className="tab-section">
                  <div className="tab-section-header">
                    <div>
                      <span className="tab-section-title">
                        Suggested changes
                      </span>
                      <span className="tab-pill">
                        {pendingSuggestionCount}
                      </span>
                    </div>
                    <div className="tab-toolbar">
                      {selectedProjectId && (
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={() => loadTasks(selectedProjectId)}
                        >
                          Refresh suggestions
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() => loadTelemetry(false)}
                      >
                        Refresh telemetry
                      </button>
                      {pendingSuggestionCount > 3 && (
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={() =>
                            setShowAllTaskSuggestions((prev) => !prev)
                          }
                        >
                          {showAllTaskSuggestions ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="tab-section-body suggestions-body">
                    <div className="suggestion-telemetry">
                      <div className="suggestion-telemetry-item">
                        <span className="label">Auto-added</span>
                        <span>{telemetry?.tasks.auto_added ?? "—"}</span>
                      </div>
                      <div className="suggestion-telemetry-item">
                        <span className="label">Auto-completed</span>
                        <span>{telemetry?.tasks.auto_completed ?? "—"}</span>
                      </div>
                      <div className="suggestion-telemetry-item">
                        <span className="label">Auto-suggested</span>
                        <span>{telemetry?.tasks.auto_suggested ?? "—"}</span>
                      </div>
                    </div>
                    {taskSuggestionError && (
                      <div className="suggestion-error">
                        {taskSuggestionError}
                      </div>
                    )}
                    {isLoadingTaskSuggestions ? (
                      <div className="tasks-empty">Loading suggestions…</div>
                    ) : pendingSuggestionCount === 0 ? (
                      <div className="tasks-empty">
                        No pending suggestions right now.
                      </div>
                    ) : (
                      <ul className="suggestion-list">
                        {visibleTaskSuggestions.map((suggestion) => {
                          const isProcessing = processingSuggestionIds.has(
                            suggestion.id
                          );
                          const candidateDescription =
                            suggestion.action_type === "add"
                              ? suggestion.payload?.description ||
                                "(no description provided)"
                              : `Mark "${suggestion.task_description || "task"}" as done.`;
                          const confidencePercent = Math.round(
                            suggestion.confidence * 100
                          );
                          const derivedPriority =
                            suggestion.payload?.priority ||
                            suggestion.task_priority ||
                            "normal";
                          const blockedReason =
                            suggestion.payload?.blocked_reason ||
                            suggestion.task_blocked_reason ||
                            null;
                          return (
                            <li
                              key={suggestion.id}
                              className="suggestion-item"
                            >
                              <div className="suggestion-heading">
                                <span
                                  className={`suggestion-pill action-${suggestion.action_type}`}
                                >
                                  {suggestion.action_type === "add"
                                    ? "Add task"
                                    : "Complete task"}
                                </span>
                                <span className="suggestion-confidence">
                                  {confidencePercent}% confidence
                                </span>
                              </div>
                              <div className="suggestion-description">
                                {candidateDescription}
                              </div>
                              <div className="task-meta suggestion-meta">
                                <span
                                  className={`task-priority-chip priority-${derivedPriority.toLowerCase()}`}
                                >
                                  {derivedPriority}
                                </span>
                              {blockedReason && (
                                  <span className="task-blocked-chip">
                                  Blocked: {blockedReason}
                                  </span>
                                )}
                              </div>
                              <div className="suggestion-actions">
                                <button
                                  type="button"
                                  className="btn-secondary tiny"
                                  onClick={() =>
                                    handleApproveTaskSuggestion(suggestion)
                                  }
                                  disabled={isProcessing}
                                >
                                  {isProcessing ? "Applying…" : "Approve"}
                                </button>
                                <button
                                  type="button"
                                  className="btn-link tiny"
                                  onClick={() =>
                                    handleDismissTaskSuggestion(suggestion)
                                  }
                                  disabled={isProcessing}
                                >
                                  {isProcessing ? "Working…" : "Dismiss"}
                                </button>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </section>
              )}
            </div>
          )}

          {rightTab === "docs" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Project documents</span>
                    <span className="tab-pill">{projectDocs.length}</span>
                  </div>
                  <div className="tab-toolbar">
                    {selectedProjectId && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() => loadProjectDocs(selectedProjectId)}
                      >
                        Refresh
                      </button>
                    )}
                    {projectDocs.length > 5 && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() => setShowAllDocs((prev) => !prev)}
                      >
                        {showAllDocs ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>
                </div>
                <div className="tab-section-body">
                  <div className="project-docs-list compact">
                {selectedProjectId == null ? (
                  <div className="docs-empty">No project selected.</div>
                ) : projectDocs.length === 0 ? (
                  <div className="docs-empty">
                    No documents yet. Ingest one below.
                  </div>
                ) : (
                  <ul>
                        {visibleDocs.map((doc) => (
                          <li
                            key={doc.id}
                            className={
                              "project-doc-item" +
                              (highlightedDocId === doc.id
                                ? " highlighted"
                                : "")
                            }
                          >
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
                  <details className="ingest-collapsible">
                    <summary>Ingest text document</summary>
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
                  </details>
                  <details className="ingest-collapsible">
                    <summary>Ingest local repo</summary>
                <div className="ingest-repo-form">
                  <input
                    className="ingest-input"
                    type="text"
                    placeholder="Root path (e.g. C:\\InfinityWindow)"
                    aria-label="Repository root path"
                    title="Repository root path"
                    value={repoRootPath}
                    onChange={(e) => setRepoRootPath(e.target.value)}
                  />
                  <input
                    className="ingest-input"
                    type="text"
                    placeholder="Name prefix (e.g. InfinityWindow/)"
                    aria-label="Repository name prefix"
                    title="Repository name prefix"
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
                    {isIngestingRepo ? "Queueing…" : "Ingest repo"}
                  </button>
                  {repoIngestionJob &&
                    repoIngestionJob.project_id === selectedProjectId && (
                      <div className="ingest-job-status">
                        <div className="ingest-job-row">
                          <span>
                            Status:{" "}
                            <strong>{repoIngestionJob.status}</strong>
                          </span>
                          {repoIngestionJob.status === "running" && (
                            <button
                              type="button"
                              className="btn-link tiny"
                              onClick={() =>
                                handleCancelIngestionJob(
                                  repoIngestionJob.id
                                )
                              }
                            >
                              Cancel job
                            </button>
                          )}
                        </div>
                        <div className="ingest-job-progress">
                          {repoIngestionJob.total_items ? (
                            <span>
                              {repoIngestionJob.processed_items}/
                              {repoIngestionJob.total_items} files
                            </span>
                          ) : null}
                          {repoIngestionJob.total_bytes ? (
                            <span>
                              {formatBytes(
                                repoIngestionJob.processed_bytes
                              )}{" "}
                              / {formatBytes(repoIngestionJob.total_bytes)}
                            </span>
                          ) : null}
                        </div>
                        <div className="ingest-job-meta">
                          {formatDuration(
                            repoIngestionJob.started_at,
                            repoIngestionJob.finished_at
                          ) && (
                            <span>
                              Duration:{" "}
                              {formatDuration(
                                repoIngestionJob.started_at,
                                repoIngestionJob.finished_at
                              )}
                            </span>
                          )}
                          {formatDateTime(repoIngestionJob.started_at) && (
                            <span>
                              Started:{" "}
                              {formatDateTime(repoIngestionJob.started_at)}
                            </span>
                          )}
                          {formatDateTime(repoIngestionJob.finished_at) && (
                            <span>
                              Finished:{" "}
                              {formatDateTime(repoIngestionJob.finished_at)}
                            </span>
                          )}
                        </div>
                        {repoIngestionJob.error_message && (
                          <div className="ingest-job-error">
                            {repoIngestionJob.error_message}
                          </div>
                        )}
                      </div>
                    )}
                </div>
                  </details>
                  <details className="ingest-collapsible">
                    <summary>Recent ingestion jobs</summary>
                    <div className="ingest-history">
                      <div className="ingest-history-toolbar">
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={handleRefreshIngestionJobs}
                          disabled={
                            isLoadingRepoJobs || !selectedProjectId
                          }
                        >
                          Refresh
                        </button>
                      </div>
                      {isLoadingRepoJobs ? (
                        <div className="ingest-history-empty">
                          Loading ingestion jobs…
                        </div>
                      ) : repoIngestionJobs.length === 0 ? (
                        <div className="ingest-history-empty">
                          No ingestion jobs yet.
                        </div>
                      ) : (
                        <div className="ingest-history-table-wrapper">
                          <table className="ingest-history-table">
                            <thead>
                              <tr>
                                <th>ID</th>
                                <th>Status</th>
                                <th>Files</th>
                                <th>Bytes</th>
                                <th>Duration</th>
                                <th>Finished</th>
                                <th>Error</th>
                              </tr>
                            </thead>
                            <tbody>
                              {repoIngestionJobs.map((job) => (
                                <tr key={job.id}>
                                  <td>{job.id}</td>
                                  <td>{job.status}</td>
                                  <td>
                                    {job.processed_items}/
                                    {job.total_items ?? 0}
                                  </td>
                                  <td>
                                    {formatBytes(job.processed_bytes)} /{" "}
                                    {formatBytes(job.total_bytes)}
                                  </td>
                                  <td>
                                    {formatDuration(
                                      job.started_at,
                                      job.finished_at
                                    ) || "—"}
                                  </td>
                                  <td>
                                    {formatDateTime(job.finished_at) ||
                                      "—"}
                                  </td>
                                  <td>
                                    {job.error_message
                                      ? job.error_message
                                      : "—"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              </section>
            </div>
          )}

          {rightTab === "notes" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Project instructions</span>
                  </div>
                  <div className="tab-toolbar">
                    {selectedProjectId && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() =>
                          loadProjectInstructions(selectedProjectId)
                        }
                      >
                        Refresh
                      </button>
                    )}
                  </div>
                </div>
                <div className="tab-section-body">
                  {selectedProjectId == null ? (
                    <div className="notes-empty">No project selected.</div>
                  ) : (
                    <>
                      <div className="pinned-note-block">
                        <label className="pinned-note-label">
                          Pinned note (shows at the top of Notes as a quick
                          reminder)
                        </label>
                        <textarea
                          className="pinned-note-textarea"
                          placeholder="Summarize the current sprint goal, the most urgent reminder, or a key constraint..."
                          value={projectPinnedNote}
                          onChange={(e) => setProjectPinnedNote(e.target.value)}
                        />
                      </div>
                      <textarea
                        className="instructions-textarea"
                        placeholder="Use this space to capture coding conventions, sensitive areas, current priorities..."
                        value={projectInstructions}
                        onChange={(e) => setProjectInstructions(e.target.value)}
                      />
                      <div className="instructions-meta">
                        {instructionsDirty ? (
                          <span className="instructions-dirty">
                            Unsaved changes — don’t forget to click Save.
                          </span>
                        ) : projectInstructionsUpdatedAt ? (
                          `Last updated ${new Date(
                            projectInstructionsUpdatedAt
                          ).toLocaleString()}`
                        ) : (
                          "Instructions not set yet."
                        )}
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
                      </div>
                      {instructionsDirty && (
                        <details className="instructions-diff">
                          <summary>View last saved instructions</summary>
                          <pre className="instructions-diff-content">
                            {projectInstructionsSaved || "(empty)"}
                          </pre>
                        </details>
                      )}
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
              </section>

              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Decision log</span>
                    <span className="tab-pill">{filteredDecisions.length}</span>
                  </div>
                  <div className="tab-toolbar">
                    {selectedProjectId && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() =>
                          loadProjectDecisions(selectedProjectId)
                        }
                      >
                        Refresh
                      </button>
                    )}
                    {filteredDecisions.length > 5 && (
                      <button
                        type="button"
                        className="btn-link tiny"
                        onClick={() =>
                          setShowAllDecisions((prev) => !prev)
                        }
                      >
                        {showAllDecisions ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>
                </div>
                <div className="tab-section-body">
                  {selectedProjectId == null ? (
                    <div className="notes-empty">No project selected.</div>
                  ) : (
                    <>
                      <div className="decision-filters">
                        <label className="decision-filter">
                          <span>Status</span>
                          <select
                            aria-label="Filter decisions by status"
                            title="Filter decisions by status"
                            value={decisionStatusFilter}
                            onChange={(e) =>
                              setDecisionStatusFilter(e.target.value)
                            }
                          >
                            <option value="all">All</option>
                            <option value="recorded">Recorded</option>
                            <option value="in-review">In review</option>
                            <option value="draft">Draft</option>
                            <option value="dismissed">Dismissed</option>
                          </select>
                        </label>
                        <label className="decision-filter">
                          <span>Category</span>
                          <select
                            aria-label="Filter decisions by category"
                            title="Filter decisions by category"
                            value={decisionCategoryFilter}
                            onChange={(e) =>
                              setDecisionCategoryFilter(e.target.value)
                            }
                          >
                            <option value="all">All</option>
                            {availableDecisionCategories.map((category) => (
                              <option key={category} value={category}>
                                {category}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="decision-filter">
                          <span>Tag</span>
                          <select
                            aria-label="Filter decisions by tag"
                            title="Filter decisions by tag"
                            value={decisionTagFilter}
                            onChange={(e) =>
                              setDecisionTagFilter(e.target.value)
                            }
                          >
                            <option value="all">All</option>
                            {availableDecisionTags.map((tag) => (
                              <option key={tag} value={tag}>
                                {tag}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="decision-filter decision-search">
                          <span>Search</span>
                          <input
                            type="text"
                            placeholder="Find a decision…"
                            value={decisionSearchQuery}
                            onChange={(e) =>
                              setDecisionSearchQuery(e.target.value)
                            }
                          />
                        </label>
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={() => {
                            setDecisionStatusFilter("all");
                            setDecisionCategoryFilter("all");
                            setDecisionTagFilter("all");
                            setDecisionSearchQuery("");
                          }}
                          disabled={!decisionFiltersActive}
                        >
                          Clear filters
                        </button>
                      </div>
                      {highlightNewDrafts && (
                        <div className="decision-draft-alert">
                          New draft decisions detected — review them below.
                        </div>
                      )}
                      <div className="decision-form compact">
                        <input
                          className="decision-input"
                          type="text"
                          placeholder="Decision title"
                          value={newDecisionTitle}
                          onChange={(e) => setNewDecisionTitle(e.target.value)}
                        />
                        <input
                          className="decision-input"
                          type="text"
                          placeholder="Category (optional)"
                          value={newDecisionCategory}
                          onChange={(e) =>
                            setNewDecisionCategory(e.target.value)
                          }
                        />
                        <input
                          className="decision-input"
                          type="text"
                          placeholder="Tags (comma separated)"
                          value={newDecisionTags}
                          onChange={(e) => setNewDecisionTags(e.target.value)}
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
                          <span>Status:</span>
                          <select
                            value={newDecisionStatus}
                            onChange={(e) =>
                              setNewDecisionStatus(
                                e.target.value as "recorded" | "draft"
                              )
                            }
                          >
                            <option value="recorded">Recorded</option>
                            <option value="draft">Draft</option>
                          </select>
                        </label>
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
                        </div>
                        {decisionsError && (
                          <div className="notes-error">{decisionsError}</div>
                        )}
                      </div>
                      <div className="decisions-list compact">
                        {filteredDecisions.length === 0 ? (
                          <div className="notes-empty">
                            No decisions logged yet.
                          </div>
                        ) : (
                          <ul>
                            {visibleDecisions.map((decision) => {
                              const showHighlight =
                                highlightNewDrafts &&
                                decision.is_draft &&
                                decision.auto_detected;
                              return (
                                <li
                                  key={decision.id}
                                  className={
                                    "decision-item" +
                                    (decision.is_draft ? " draft" : "") +
                                    (showHighlight ? " attention" : "")
                                  }
                                >
                                  <div className="decision-title-row">
                                    <div className="decision-title-meta">
                                      <span className="decision-title">
                                        {decision.title}
                                      </span>
                                      {decision.category && (
                                        <span className="decision-chip">
                                          {decision.category}
                                        </span>
                                      )}
                                      <span className="decision-status-pill">
                                        {decision.status}
                                      </span>
                                      {decision.is_draft && (
                                        <span className="decision-chip draft">
                                          Draft
                                        </span>
                                      )}
                                      {decision.auto_detected && (
                                        <span className="decision-chip auto">
                                          Auto
                                        </span>
                                      )}
                                    </div>
                                    <div className="decision-actions">
                                      <label className="decision-status-select">
                                        <span>Status</span>
                                        <select
                                          value={decision.status}
                                          onChange={(e) =>
                                            handleDecisionStatusSelect(
                                              decision,
                                              e.target.value
                                            )
                                          }
                                        >
                                          <option value="recorded">
                                            Recorded
                                          </option>
                                          <option value="in-review">
                                            In review
                                          </option>
                                          <option value="draft">Draft</option>
                                          <option value="dismissed">
                                            Dismissed
                                          </option>
                                        </select>
                                      </label>
                                      {decision.is_draft && (
                                        <>
                                          <button
                                            type="button"
                                            className="btn-link tiny"
                                            onClick={() =>
                                              handleDecisionConfirmDraft(
                                                decision
                                              )
                                            }
                                          >
                                            Mark recorded
                                          </button>
                                          <button
                                            type="button"
                                            className="btn-link tiny"
                                            onClick={() =>
                                              handleDecisionDismissDraft(
                                                decision
                                              )
                                            }
                                          >
                                            Dismiss draft
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                  {decision.details && (
                                    <div className="decision-details">
                                      {decision.details}
                                    </div>
                                  )}
                                  <div className="decision-meta">
                                    <span>
                                      Created{" "}
                                      {new Date(
                                        decision.created_at
                                      ).toLocaleString()}
                                    </span>
                                    <span>
                                      Updated{" "}
                                      {new Date(
                                        decision.updated_at
                                      ).toLocaleString()}
                                    </span>
                                    {decision.follow_up_task_id && (
                                      <span>
                                        Follow-up task #
                                        {decision.follow_up_task_id}
                                      </span>
                                    )}
                                    {decision.source_conversation_id && (
                                      <button
                                        type="button"
                                    className="btn-link tiny"
                                        onClick={() =>
                                          handleOpenDecisionConversation(
                                            decision.source_conversation_id
                                          )
                                        }
                                      >
                                        Open conversation #
                                        {decision.source_conversation_id}
                                      </button>
                                    )}
                                  </div>
                                  <div className="decision-tags-row">
                                    {decision.tags.length ? (
                                      decision.tags.map((tag) => (
                                        <span
                                          key={`${decision.id}-${tag}`}
                                          className="decision-tag"
                                        >
                                          {tag}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="decision-tag empty">
                                        No tags yet
                                      </span>
                                    )}
                                    <button
                                      type="button"
                                      className="btn-link tiny"
                                      onClick={() =>
                                        handleDecisionEditTags(decision)
                                      }
                                    >
                                      Edit tags
                                    </button>
                                  </div>
                                  <div className="decision-footer">
                                    <button
                                      type="button"
                                      className="btn-secondary tiny"
                                      onClick={() =>
                                        handleDecisionCreateTask(decision)
                                      }
                                    >
                                      Add follow-up task
                                    </button>
                                    {decision.follow_up_task_id && (
                                      <button
                                        type="button"
                                        className="btn-link tiny"
                                        onClick={() =>
                                          handleDecisionClearFollowUp(decision)
                                        }
                                      >
                                        Clear follow-up
                                      </button>
                                    )}
                                    <button
                                      type="button"
                                      className="btn-secondary tiny"
                                      onClick={() =>
                                        handleDecisionCreateMemory(decision)
                                      }
                                    >
                                      Save to memory
                                    </button>
                                    <button
                                      type="button"
                                      className="btn-link tiny"
                                      onClick={() =>
                                        handleDecisionCopy(decision)
                                      }
                                    >
                                      Copy
                                    </button>
                                  </div>
                                </li>
                              );
                            })}
                          </ul>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </section>
            </div>
          )}

          {rightTab === "memory" && (
            <>
              <div className="memory-header">Project memories</div>
              <div className="memory-panel">
                {selectedProjectId == null ? (
                  <div className="memory-empty">
                    No project selected.
                  </div>
                ) : (
                  <>
                    <div className="memory-toolbar">
                      <button
                        type="button"
                        className="btn-secondary small"
                        onClick={() => openMemoryModal()}
                      >
                        + Remember something
                      </button>
                      <button
                        type="button"
                        className="btn-link small"
                        onClick={() => loadMemoryItems(selectedProjectId)}
                        disabled={isLoadingMemory}
                      >
                        Refresh
                      </button>
                    </div>
                    {isLoadingMemory ? (
                      <div className="memory-empty">
                        Loading memories…
                      </div>
                    ) : memoryItems.length === 0 ? (
                      <div className="memory-empty">
                        No memories yet. Capture insights from the chat
                        or enter them manually.
                      </div>
                    ) : (
                      <ul className="memory-list">
                        {memoryItems.map((item) => (
                          <li key={item.id} className="memory-item">
                            <div className="memory-item-header">
                              <div className="memory-item-title">
                                {item.title}
                                {item.pinned && (
                                  <span className="memory-pill">
                                    Pinned
                                  </span>
                                )}
                              </div>
                              <div className="memory-item-actions">
                                <button
                                  type="button"
                                  className="btn-link small"
                                  onClick={() =>
                                    handleToggleMemoryPinned(item)
                                  }
                                >
                                  {item.pinned ? "Unpin" : "Pin"}
                                </button>
                                <button
                                  type="button"
                                  className="btn-link small danger"
                                  onClick={() =>
                                    handleDeleteMemory(item.id)
                                  }
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                            <div className="memory-item-content">
                              {item.content}
                            </div>
                            <div className="memory-item-meta">
                              <span>
                                Saved{" "}
                                {new Date(
                                  item.created_at
                                ).toLocaleString()}
                              </span>
                              {item.tags.length > 0 && (
                                <span>
                                  Tags: {item.tags.join(", ")}
                                </span>
                              )}
                              {item.expires_at && (
                                <span>
                                  Expires{" "}
                                  {new Date(
                                    item.expires_at
                                  ).toLocaleString()}
                                </span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                )}
              </div>
            </>
          )}

          {rightTab === "files" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Project files</span>
                  </div>
                  <div className="tab-toolbar">
                    <button
                      type="button"
                      className="btn-link tiny"
                      onClick={handleFsRefresh}
                      disabled={fsIsLoadingList}
                    >
                      Refresh
                    </button>
                  </div>
                </div>
                <div className="tab-section-body">
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
                                      onClick={() => handleOpenFsEntry(entry)}
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
                                    fsIsSavingFile || !hasUnsavedFileChanges
                              }
                            >
                                  {fsIsSavingFile ? "Saving…" : "Save file"}
                            </button>
                          </div>
                        </div>
                        <textarea
                          className="file-editor-textarea"
                          aria-label="File editor"
                          title="File editor"
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
                </div>
              </section>

              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">AI file edit</span>
                  </div>
                </div>
                <div className="tab-section-body">
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
                            onClick={handlePreviewFileEdit}
                            disabled={isPreviewingFileEdit}
                          >
                            {isPreviewingFileEdit
                              ? "Previewing…"
                              : "Preview edit"}
                          </button>
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
                        {fileEditError && (
                          <div className="fileedit-error">{fileEditError}</div>
                )}
                        {fileEditPreview && (
                          <div className="fileedit-preview">
                            <div className="fileedit-preview-label">
                              Preview diff
              </div>
                            {fileEditPreview.diff ? (
                              <pre className="diff-view">
                                {fileEditPreview.diff}
                              </pre>
                            ) : (
                              <div className="fileedit-preview-text">
                                (No diff available; showing proposed content)
                              </div>
                            )}
                            <details>
                              <summary>View proposed file</summary>
                              <pre className="fileedit-preview-content">
                                {fileEditPreview.edited_content}
                              </pre>
                            </details>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </section>
            </div>
          )}

          {rightTab === "search" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Search memory</span>
                  </div>
                </div>
                <div className="tab-section-body">
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
                  <div className="search-filters">
                    {searchTab === "messages" ? (
                      <>
                        <label className="search-filter">
                          <span>Conversation</span>
                          <select
                            value={
                              searchConversationFilter === "all"
                                ? "all"
                                : String(searchConversationFilter)
                            }
                            onChange={(e) =>
                              setSearchConversationFilter(
                                e.target.value === "all"
                                  ? "all"
                                  : Number(e.target.value)
                              )
                            }
                          >
                            <option value="all">All conversations</option>
                            {conversations.map((conversation) => (
                              <option
                                key={conversation.id}
                                value={conversation.id}
                              >
                                {conversation.title?.trim() ||
                                  `Conversation ${conversation.id}`}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="search-filter">
                          <span>Folder</span>
                          <select
                            value={
                              searchFolderFilter === "all"
                                ? "all"
                                : String(searchFolderFilter)
                            }
                            onChange={(e) =>
                              setSearchFolderFilter(
                                e.target.value === "all"
                                  ? "all"
                                  : Number(e.target.value)
                              )
                            }
                          >
                            <option value="all">All folders</option>
                            {folders.map((folder) => (
                              <option key={folder.id} value={folder.id}>
                                {folder.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={clearSearchFilters}
                        >
                          Clear filters
                        </button>
                      </>
                    ) : (
                      <>
                        <label className="search-filter">
                          <span>Document</span>
                          <select
                            value={
                              searchDocFilter === "all"
                                ? "all"
                                : String(searchDocFilter)
                            }
                            onChange={(e) =>
                              setSearchDocFilter(
                                e.target.value === "all"
                                  ? "all"
                                  : Number(e.target.value)
                              )
                            }
                          >
                            <option value="all">All documents</option>
                            {projectDocs.map((doc) => (
                              <option key={doc.id} value={doc.id}>
                                {doc.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button
                          type="button"
                          className="btn-link tiny"
                          onClick={() => setSearchDocFilter("all")}
                        >
                          Reset selection
                        </button>
                      </>
                    )}
                  </div>
              <div className="search-results">
                {searchTab === "messages" ? (
                      groupedMessageHits.length === 0 ? (
                    <div className="search-empty">
                      No message results yet. Try a query.
                    </div>
                  ) : (
                        <div className="search-groups">
                          {groupedMessageHits.map((group) => (
                            <div
                              key={`search-group-${group.conversationId}`}
                              className="search-group"
                            >
                              <div className="search-group-header">
                                <div>
                                  <span className="search-group-title">
                                    {group.title}
                                  </span>
                                  <span className="search-group-subtitle">
                                    Conversation #{group.conversationId}
                                  </span>
                                  {group.folderName && (
                                    <span className="search-group-chip">
                                      {group.folderName}
                                    </span>
                                  )}
                                </div>
                                <div className="search-group-actions">
                                  <button
                                    type="button"
                                    className="btn-link tiny"
                                    onClick={() =>
                                      handleOpenConversationFromSearch(
                                        group.conversationId
                                      )
                                    }
                                  >
                                    Open conversation
                                  </button>
                                </div>
                              </div>
                              <ul>
                                {group.hits.map((hit, idx) => (
                                  <li
                                    key={`${hit.message_id}-${idx}`}
                          className="search-result-item"
                        >
                          <div className="search-result-meta">
                                      {hit.role} · distance{" "}
                                      {hit.distance.toFixed(3)}
                          </div>
                          <div className="search-result-content">
                            {hit.content}
                          </div>
                        </li>
                      ))}
                    </ul>
                            </div>
                          ))}
                        </div>
                  )
                    ) : groupedDocHits.length === 0 ? (
                  <div className="search-empty">
                    No doc results yet. Try a query.
                  </div>
                ) : (
                      <div className="search-groups">
                        {groupedDocHits.map((group) => (
                          <div
                            key={`doc-group-${group.documentId}`}
                            className="search-group"
                          >
                            <div className="search-group-header">
                              <div>
                                <span className="search-group-title">
                                  {group.name}
                                </span>
                                <span className="search-group-subtitle">
                                  Doc #{group.documentId}
                                </span>
                              </div>
                              <div className="search-group-actions">
                                <button
                                  type="button"
                                  className="btn-link tiny"
                                  onClick={() =>
                                    handleOpenDocFromSearch(group.documentId)
                                  }
                                >
                                  View in Docs tab
                                </button>
                              </div>
                            </div>
                            <ul>
                              {group.hits.map((hit, idx) => (
                                <li
                                  key={`${hit.chunk_id}-${idx}`}
                        className="search-result-item"
                      >
                        <div className="search-result-meta">
                                    Chunk {hit.chunk_index} · distance{" "}
                                    {hit.distance.toFixed(3)}
                        </div>
                        <div className="search-result-content">
                          {hit.content}
                        </div>
                      </li>
                    ))}
                  </ul>
                          </div>
                        ))}
                      </div>
                )}
              </div>
                </div>
              </section>
            </div>
          )}

          {rightTab === "terminal" && (
            <div className="tab-stack">
              <section className="tab-section">
                <div className="tab-section-header">
                  <div>
                    <span className="tab-section-title">Terminal</span>
                    <span className="tab-pill">
                      {manualTerminalHistory.length} saved
                    </span>
                  </div>
                </div>
                <div className="tab-section-body">
                  <div className="terminal-panel manual-terminal-panel">
                    {selectedProjectId == null ? (
                      <div className="terminal-empty">
                        Select a project to run manual commands.
                      </div>
                    ) : (
                      <>
                        <div className="manual-terminal-cwd-row">
                          <label
                            className="terminal-label"
                            htmlFor="manual-cwd"
                          >
                            CWD (optional):
                          </label>
                          <input
                            id="manual-cwd"
                            type="text"
                            className="manual-terminal-input"
                            placeholder="e.g. backend, frontend, scratch"
                            value={manualTerminalCwd}
                            onChange={(e) =>
                              setManualTerminalCwd(e.target.value)
                            }
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
                            {isRunningManualTerminal
                              ? "Running…"
                              : "Run command"}
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

                  <div className="terminal-history-header">
                    Recent manual commands
                  </div>
                  <div className="terminal-history-panel">
                    {manualTerminalHistory.length === 0 ? (
                      <div className="terminal-empty">
                        Commands you run manually will be listed here.
                      </div>
                    ) : (
                      <ul>
                        {manualTerminalHistory.map((entry) => (
                          <li key={entry.id} className="terminal-history-item">
                            <div>
                              <span className="mono">{entry.command}</span>
                              <span className="terminal-history-cwd">
                                ({entry.cwd})
                              </span>
                            </div>
                            <div className="terminal-history-meta">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                              <button
                                type="button"
                                className="btn-link tiny"
                                onClick={() => {
                                  setManualTerminalCommand(entry.command);
                                  setManualTerminalCwd(
                                    entry.cwd === "(project root)"
                                      ? ""
                                      : entry.cwd
                                  );
                                  addToast(
                                    "Loaded command into manual runner",
                                    "success"
                                  );
                                }}
                              >
                                Load
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </section>
            </div>
          )}

          {rightTab === "usage" && (
            <>
              {/* Usage panel */}
              <div className="usage-header">
                Usage dashboard
                {usageConversationId && (
                  <span className="usage-header-subtitle">
                    Conversation #{usageConversationId}
                  </span>
                )}
              </div>
              <div className="usage-panel">
                <div className="usage-toolbar">
                  <label className="usage-filter">
                    <span>Select conversation</span>
                    <select
                    aria-label="Select conversation for usage"
                    title="Select conversation for usage"
                      value={usageConversationId ?? ""}
                      onChange={handleUsageConversationChange}
                    >
                      <option value="">
                        {conversations.length === 0
                          ? "No conversations available"
                          : "Choose…"}
                      </option>
                      {conversations.map((conversation) => (
                        <option key={conversation.id} value={conversation.id}>
                          {conversation.title?.trim() ||
                            `Conversation ${conversation.id}`}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="btn-link small"
                    onClick={handleFocusCurrentConversationUsage}
                    disabled={!selectedConversationId}
                  >
                    Use current chat
                  </button>
              <div className="usage-filter-row">
                <label className="usage-filter">
                  <span>Action filter</span>
                  <select
                    aria-label="Action filter"
                    title="Action filter"
                    value={usageActionFilter}
                    onChange={(e) => setUsageActionFilter(e.target.value)}
                  >
                    <option value="all">All actions</option>
                    <option value="auto_added">Auto-added</option>
                    <option value="auto_completed">Auto-completed</option>
                    <option value="suggested">Suggested (add/complete)</option>
                    <option value="auto_suggested">Auto-suggested</option>
                    <option value="auto_dismissed">Auto-dismissed</option>
                    <option value="auto_deduped">Auto-deduped</option>
                  </select>
                </label>
                <label className="usage-filter">
                  <span>Group filter</span>
                  <select
                    value={usageGroupFilter}
                    onChange={(e) => setUsageGroupFilter(e.target.value)}
                    aria-label="Group filter"
                    title="Group filter"
                  >
                    <option value="all">All groups</option>
                    <option value="critical">Critical</option>
                    <option value="blocked">Blocked</option>
                    <option value="ready">Ready</option>
                  </select>
                </label>
                <label className="usage-filter">
                  <span>Model filter</span>
                  <select
                    value={usageModelFilter}
                    onChange={(e) => setUsageModelFilter(e.target.value)}
                    aria-label="Model filter"
                    title="Model filter"
                  >
                    <option value="all">All models</option>
                    {modelFilterOptions.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="usage-filter">
                  <span>Time filter</span>
                  <select
                    value={usageTimeFilter}
                    onChange={(e) => setUsageTimeFilter(e.target.value)}
                    aria-label="Time filter"
                    title="Time filter"
                  >
                    <option value="all">All</option>
                    <option value="last5">Last 5</option>
                    <option value="last10">Last 10</option>
                  </select>
                </label>
                <label className="usage-filter">
                  <span>Range</span>
                  <select
                    value={usageRangeFilter}
                    onChange={(e) => setUsageRangeFilter(e.target.value)}
                    aria-label="Usage time range"
                    title="Usage time range"
                  >
                    <option value="recent">Recent actions only</option>
                    <option value="records10">Last 10 usage records</option>
                  </select>
                </label>
                <label className="usage-filter">
                  <span>Usage records window</span>
                  <select
                    value={usageRecordsWindow}
                    onChange={(e) => setUsageRecordsWindow(e.target.value)}
                    aria-label="Usage records window"
                    title="Usage records window"
                  >
                    <option value="all">All time</option>
                    <option value="1h">Last hour</option>
                    <option value="24h">Last 24h</option>
                    <option value="7d">Last 7d</option>
                  </select>
                </label>
              </div>
                </div>
                {usageConversationId == null ? (
                  <div className="usage-empty">
                    Select a conversation to view usage analytics.
                  </div>
                ) : usageError ? (
                  <div className="usage-empty usage-telemetry-error">
                    {usageError}
                  </div>
                ) : isLoadingUsage ? (
                  <div className="usage-empty">Loading usage…</div>
                ) : !usage || !windowedUsageRecords.length ? (
                  <div className="usage-empty">
                    No usage records yet for this conversation.
                  </div>
                ) : (
                  <>
                    <div className="usage-summary">
                    <div className="usage-cards">
                    <div className="usage-card">
                      <div className="usage-card-title">Last chosen model</div>
                      <div className="usage-card-value">
                        {usage.records[usage.records.length - 1]?.model ||
                          "—"}
                      </div>
                      {telemetry?.llm?.auto_routes && lastUsageAutoReason && (
                        <div className="usage-subtext">
                          Routed: {lastUsageAutoReason}
                        </div>
                      )}
                      {modelOverrideMode !== "default" && (
                        <div className="usage-subtext">
                          Next override:{" "}
                          {modelOverrideMode === "custom"
                            ? modelOverrideCustom || "custom"
                            : modelOverrideMode}
                        </div>
                      )}
                    </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Total cost</div>
                        <div className="usage-card-value">
                          {usage.total_cost_estimate != null
                            ? `$${usage.total_cost_estimate.toFixed(4)}`
                            : "—"}
                        </div>
                      </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Total calls</div>
                        <div className="usage-card-value">
                          {usage.records.length.toLocaleString()}
                        </div>
                      </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Tokens in</div>
                        <div className="usage-card-value">
                          {usage.total_tokens_in?.toLocaleString() ?? 0}
                        </div>
                      </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Tokens out</div>
                        <div className="usage-card-value">
                          {usage.total_tokens_out?.toLocaleString() ?? 0}
                        </div>
                      </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Auto-added</div>
                        <div className="usage-card-value">
                          {telemetry?.tasks?.auto_added ?? "—"}
                        </div>
                      </div>
                      <div className="usage-card">
                        <div className="usage-card-title">Auto-completed</div>
                        <div className="usage-card-value">
                          {telemetry?.tasks?.auto_completed ?? "—"}
                        </div>
                      </div>
                    </div>
                    </div>
                    <div className="usage-breakdown">
                      <div className="usage-breakdown-title">
                        Model breakdown
                      </div>
                      {usageModelBreakdown.length === 0 ? (
                        <div className="usage-empty">
                          No assistant calls recorded yet.
                        </div>
                      ) : (
                        <ul className="usage-breakdown-list">
                          {usageModelBreakdown.map((entry) => (
                            <li
                              key={entry.model}
                              className="usage-breakdown-item"
                            >
                              <div className="usage-model">
                                {entry.model || "Unknown model"}
                              </div>
                              <div className="usage-model-metrics">
                                <span>
                                  {entry.count} call
                                  {entry.count === 1 ? "" : "s"}
                                </span>
                                <span>
                                  in {entry.tokensIn.toLocaleString()}
                                </span>
                                <span>
                                  out {entry.tokensOut.toLocaleString()}
                                </span>
                              </div>
                              <div className="mini-bar">
                                <div
                                  className={percentToWidthClass(
                                    (entry.count /
                                      (usageModelBreakdown[0]?.count || 1)) *
                                      100
                                  )}
                                />
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="usage-records">
                      <div className="usage-records-title">
                        Recent assistant calls
                      </div>
                      <ul>
                        {(usageRangeFilter === "records10"
                          ? windowedUsageRecords
                              .slice()
                              .reverse()
                              .slice(0, 10)
                          : windowedUsageRecords
                              .slice()
                              .reverse()
                              .slice(0, 5)
                        ).map((r) => (
                            <li
                              key={r.id}
                              className="usage-record-item"
                            >
                              <div className="usage-record-main">
                                <span className="usage-model">
                                  {r.model || "model?"}
                                </span>
                                <span className="usage-tokens">
                                  in {(r.tokens_in ?? 0).toLocaleString()} ·
                                  out {(r.tokens_out ?? 0).toLocaleString()}
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
              {telemetryPanel}
            </>
          )}
        </section>
      </main>

      {showCommandPalette && (
        <div
          className="command-palette-overlay"
          onClick={() => setShowCommandPalette(false)}
        >
          <div
            className="command-palette"
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="command-palette-header">
              <span>Quick actions</span>
              <button
                type="button"
                className="btn-link small"
                onClick={() => setShowCommandPalette(false)}
              >
                Close
              </button>
            </div>
            <input
              ref={commandPaletteInputRef}
              className="command-palette-input"
              placeholder="Search actions…"
              value={commandPaletteQuery}
              onChange={(e) => {
                setCommandPaletteQuery(e.target.value);
                setCommandPaletteIndex(0);
              }}
              onKeyDown={handleCommandPaletteInputKeyDown}
            />
            <div className="command-palette-list">
              {filteredCommandActions.length === 0 ? (
                <div className="command-palette-empty">No matches</div>
              ) : (
                filteredCommandActions.map((action, idx) => (
                  <button
                    key={action.id}
                    type="button"
                    className={
                      "command-palette-item" +
                      (idx === commandPaletteIndex ? " active" : "")
                    }
                    onClick={() => executeCommandPaletteAction(idx)}
                  >
                    {action.label}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
