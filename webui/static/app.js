const form = document.getElementById("typhon-form");
const modeInput = document.getElementById("mode");
const modeButtons = Array.from(document.querySelectorAll(".mode-btn"));
const langButtons = Array.from(document.querySelectorAll(".lang-btn"));
const runBtn = document.getElementById("run-btn");
const resetBtn = document.getElementById("reset-btn");
const output = document.getElementById("output");
const terminalShell = document.getElementById("terminal-shell");
const statusBadge = document.getElementById("status-badge");
const durationNode = document.getElementById("duration");
const exitCodeNode = document.getElementById("exit-code");
const runnerCodeNode = document.getElementById("runner-code");

const rceOnlyNodes = Array.from(document.querySelectorAll(".rce-only"));
const readOnlyNodes = Array.from(document.querySelectorAll(".read-only"));
const cmdInput = document.getElementById("cmd");
const filepathInput = document.getElementById("filepath");
const localScopeInput = document.getElementById("local_scope");

const translations = {
  zh: {
    page_title: "Typhon 控制台",
    eyebrow: "Typhon 控制台",
    hero_title: "Web UI",
    hero_subtitle: "填写参数后运行 Typhon，在同一页面查看生成 payload 和执行输出。",

    mode_rce: "RCE 模式",
    mode_read: "READ 模式",
    label_cmd: "命令 (`cmd`)",
    label_filepath: "目标文件 (`filepath`)",
    label_rce_method: "RCE 方法",

    basic_scope_title: "执行上下文",
    basic_scope_desc: "优先填写题目的真实 globals/locals 环境。",
    label_local_scope: "local_scope (JSON)",
    hint_local_scope: "支持 `@builtin:list`、`@module:os` 等 token。",

    basic_filter_title: "WAF / 过滤规则",
    basic_filter_desc: "黑白名单是常规参数，直接放在主配置区域。",
    label_banned_chr: "banned_chr（逗号/换行分隔 或 python 列表）",
    hint_banned_chr: "目标禁止的字符或字符串列表。",
    label_allowed_chr: "allowed_chr（逗号/换行分隔 或 python 列表）",
    hint_allowed_chr: "白名单模式。不要和 `banned_chr` 同时设置。",
    label_banned_re: "banned_re（逗号/换行分隔）",
    hint_banned_re: "目标 WAF 禁止匹配的正则规则。",
    label_banned_ast: "banned_ast（AST 类名）",
    hint_banned_ast: "例如 `Import`、`Attribute`，多个值用逗号分隔。",
    label_max_length: "max_length",
    hint_max_length: "目标允许的 payload 最大长度。留空表示不限制。",

    advanced_options: "高级选项",
    advanced_intro: "这里仅保留扫描深度、递归与输出策略等引擎调优参数。",

    group_search_title: "搜索策略",
    group_search_desc: "在速度与覆盖率之间做权衡。",
    label_depth: "depth",
    hint_depth: "越大越可能找到绕过链，但速度会更慢。",
    label_recursion_limit: "recursion_limit",
    hint_recursion_limit: "Python 递归上限，影响深层 payload 生成。",
    check_allow_unicode: "allow_unicode_bypass",
    hint_allow_unicode: "尝试 Unicode 混淆字符。部分终端可能不兼容。",

    group_runtime_title: "运行行为",
    group_runtime_desc: "控制超时、日志级别和交互式能力。",
    label_timeout: "timeout_sec",
    hint_timeout: "单次任务最大运行时长（秒）。",
    label_log_level: "log_level",
    hint_log_level: "DEBUG 最详细，QUIET 会减少过程输出。",
    check_interactive: "interactive",
    hint_interactive: "允许使用依赖 stdin 的 payload 路径。",
    check_exception_leak: "is_allow_exception_leak",
    hint_exception_leak: "仅 READ 模式生效。通过异常回显泄露文件内容。",

    group_output_title: "输出策略",
    group_output_desc: "控制输出信息量和候选 payload 展示。",
    check_print_all_payload: "print_all_payload",
    hint_print_all_payload: "打印所有可用 payload，而不只第一个命中结果。",

    btn_run: "运行 Typhon",
    btn_reset: "重置",
    result_title: "执行输出",
    terminal_title: "Typhon 输出终端",
    status_idle: "空闲",
    status_running: "运行中",
    status_success: "已绕过",
    status_finished: "已完成",
    status_failed: "失败",
    status_request_error: "请求异常",
    meta_duration: "耗时: -",
    meta_exit_code: "退出码: -",
    meta_runner_code: "Runner 退出码: -",
    meta_duration_label: "耗时",
    meta_exit_code_label: "退出码",
    meta_runner_code_label: "Runner 退出码",
    output_ready: "就绪。",
    output_executing: "正在执行 Typhon...",
    output_request_failed: "请求失败:",
    output_progress_fold: "... 已折叠 {count} 条进度日志 ...",
    ph_cmd: "cat /flag",
    ph_filepath: "/etc/passwd",
  },
  en: {
    page_title: "Typhon Visual Console",
    eyebrow: "Typhon Visual Console",
    hero_title: "Web UI",
    hero_subtitle: "Fill options, run Typhon, and inspect generated payload output in one place.",

    mode_rce: "RCE Mode",
    mode_read: "READ Mode",
    label_cmd: "Command (`cmd`)",
    label_filepath: "Target file (`filepath`)",
    label_rce_method: "RCE method",

    basic_scope_title: "Execution Context",
    basic_scope_desc: "Prefer real challenge globals/locals when available.",
    label_local_scope: "local_scope (JSON)",
    hint_local_scope: "Supports tokens like `@builtin:list`, `@module:os`.",

    basic_filter_title: "WAF / Filter Rules",
    basic_filter_desc: "Blacklist/whitelist are common options, kept in the main area.",
    label_banned_chr: "banned_chr (comma/newline split)",
    hint_banned_chr: "Blacklisted characters or strings blocked by target.",
    label_allowed_chr: "allowed_chr (comma/newline split)",
    hint_allowed_chr: "Whitelist mode. Do not combine with `banned_chr`.",
    label_banned_re: "banned_re (comma/newline split)",
    hint_banned_re: "Regex patterns blocked by target WAF.",
    label_banned_ast: "banned_ast (AST class names)",
    hint_banned_ast: "Examples: `Import`, `Attribute`, separated by comma.",
    label_max_length: "max_length",
    hint_max_length: "Maximum payload length accepted by target. Empty means unlimited.",

    advanced_options: "Advanced Options",
    advanced_intro: "Engine tuning only: recursion, scan depth, and output strategy.",

    group_search_title: "Search Strategy",
    group_search_desc: "Trade off between speed and bypass coverage.",
    label_depth: "depth",
    hint_depth: "Higher depth may find more chains but can be slower.",
    label_recursion_limit: "recursion_limit",
    hint_recursion_limit: "Python recursion cap affecting deep payload generation.",
    check_allow_unicode: "allow_unicode_bypass",
    hint_allow_unicode: "Try unicode-confusable bypasses. Some terminals may not support it.",

    group_runtime_title: "Runtime Behavior",
    group_runtime_desc: "Control timeout, log verbosity, and interactive capability.",
    label_timeout: "timeout_sec",
    hint_timeout: "Maximum runtime per task (seconds).",
    label_log_level: "log_level",
    hint_log_level: "DEBUG is verbose. QUIET minimizes process logs.",
    check_interactive: "interactive",
    hint_interactive: "Enable payload paths depending on stdin behavior.",
    check_exception_leak: "is_allow_exception_leak",
    hint_exception_leak: "READ mode only. Leak file output via exception traceback.",

    group_output_title: "Output Strategy",
    group_output_desc: "Control detail level and payload candidate printing.",
    check_print_all_payload: "print_all_payload",
    hint_print_all_payload: "Print all valid payloads instead of only the first successful one.",

    btn_run: "Run Typhon",
    btn_reset: "Reset",
    result_title: "Execution Output",
    terminal_title: "Typhon Output Terminal",
    status_idle: "Idle",
    status_running: "Running",
    status_success: "Jail broken",
    status_finished: "Finished",
    status_failed: "Failed",
    status_request_error: "Request error",
    meta_duration: "Duration: -",
    meta_exit_code: "Exit code: -",
    meta_runner_code: "Runner code: -",
    meta_duration_label: "Duration",
    meta_exit_code_label: "Exit code",
    meta_runner_code_label: "Runner code",
    output_ready: "Ready.",
    output_executing: "Executing Typhon...",
    output_request_failed: "Request failed:",
    output_progress_fold: "... collapsed {count} progress lines ...",
    ph_cmd: "cat /flag",
    ph_filepath: "/etc/passwd",
  },
};

const ANSI_REGEX = /\u001b\[[0-9;?]*[ -/]*[@-~]/g;
const PROGRESS_REGEX = /^Bypassing\s*\(/;
const SECTION_REGEX = /^-+Progress-+/;

let currentLang = "en";
let currentStatusKey = "status_idle";
let outputState = "ready";
let outputErrorDetail = "";

const metaState = {
  duration: null,
  exitCode: null,
  runnerCode: null,
};

function t(key) {
  return translations[currentLang]?.[key] ?? translations.en[key] ?? key;
}

function formatProgressFold(count) {
  return t("output_progress_fold").replace("{count}", String(count));
}

function setBadge(type, statusKey) {
  statusBadge.className = `badge ${type}`;
  currentStatusKey = statusKey;
  statusBadge.textContent = t(statusKey);
}

function setTerminalTone(tone) {
  terminalShell.classList.remove("tone-idle", "tone-running", "tone-success", "tone-error");
  terminalShell.classList.add(`tone-${tone}`);
}

function setTerminalRunning(isRunning) {
  terminalShell.classList.toggle("running", isRunning);
}

function pulseTerminal() {
  terminalShell.classList.remove("updated");
  // Restart animation.
  void terminalShell.offsetWidth;
  terminalShell.classList.add("updated");
}

function setOutputState(nextState, detail = "") {
  outputState = nextState;
  outputErrorDetail = detail;
  if (nextState === "custom") {
    return;
  }
  if (nextState === "ready") {
    output.textContent = t("output_ready");
    return;
  }
  if (nextState === "executing") {
    output.textContent = t("output_executing");
    return;
  }
  if (nextState === "request_failed") {
    output.textContent = `${t("output_request_failed")}\n${detail}`;
  }
}

function updateMetaNodes() {
  const durationText = metaState.duration === null ? "-" : `${metaState.duration} ms`;
  const exitCodeText = metaState.exitCode === null ? "-" : `${metaState.exitCode}`;
  const runnerCodeText = metaState.runnerCode === null ? "-" : `${metaState.runnerCode}`;

  durationNode.textContent = `${t("meta_duration_label")}: ${durationText}`;
  exitCodeNode.textContent = `${t("meta_exit_code_label")}: ${exitCodeText}`;
  runnerCodeNode.textContent = `${t("meta_runner_code_label")}: ${runnerCodeText}`;
}

function normalizeOutputText(rawText) {
  const text = String(rawText ?? "")
    .replace(ANSI_REGEX, "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");

  const lines = text.split("\n");
  const out = [];
  let foldedProgress = 0;
  let previousBlank = false;

  for (const line of lines) {
    const cleaned = line.replace(/\t/g, "  ").trimEnd();

    if (PROGRESS_REGEX.test(cleaned)) {
      if (cleaned.includes("100.0%")) {
        out.push(`✓ ${cleaned}`);
        previousBlank = false;
      } else {
        foldedProgress += 1;
      }
      continue;
    }

    if (!cleaned) {
      if (!previousBlank && out.length > 0) {
        out.push("");
      }
      previousBlank = true;
      continue;
    }

    if (SECTION_REGEX.test(cleaned) && out[out.length - 1] === cleaned) {
      continue;
    }

    out.push(cleaned);
    previousBlank = false;
  }

  if (foldedProgress > 0) {
    out.unshift(formatProgressFold(foldedProgress), "");
  }

  const formatted = out.join("\n").trim();
  return formatted || t("output_ready");
}

function applyTranslations() {
  document.documentElement.lang = currentLang === "zh" ? "zh-CN" : "en";

  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    if (!key) {
      return;
    }
    node.textContent = t(key);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.dataset.i18nPlaceholder;
    if (!key) {
      return;
    }
    node.placeholder = t(key);
  });

  document.title = t("page_title");
  statusBadge.textContent = t(currentStatusKey);
  updateMetaNodes();

  if (outputState === "ready" || outputState === "executing") {
    setOutputState(outputState);
  }
  if (outputState === "request_failed") {
    setOutputState("request_failed", outputErrorDetail);
  }
}

function setLanguage(nextLang) {
  if (!translations[nextLang]) {
    return;
  }
  currentLang = nextLang;
  localStorage.setItem("typhon_webui_lang", nextLang);
  langButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === nextLang);
  });
  applyTranslations();
}

function initLanguage() {
  const saved = localStorage.getItem("typhon_webui_lang");
  if (saved && translations[saved]) {
    setLanguage(saved);
    return;
  }
  const browserLang = navigator.language?.toLowerCase() || "en";
  setLanguage(browserLang.startsWith("zh") ? "zh" : "en");
}

function switchMode(nextMode) {
  modeInput.value = nextMode;
  modeButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === nextMode);
  });

  const isRce = nextMode === "rce";
  rceOnlyNodes.forEach((node) => node.classList.toggle("hidden", !isRce));
  readOnlyNodes.forEach((node) => node.classList.toggle("hidden", isRce));

  if (isRce) {
    cmdInput.setAttribute("required", "required");
    filepathInput.removeAttribute("required");
  } else {
    filepathInput.setAttribute("required", "required");
    cmdInput.removeAttribute("required");
  }
}

function collectPayload() {
  return {
    mode: modeInput.value,
    cmd: cmdInput.value.trim(),
    filepath: filepathInput.value.trim(),
    rce_method: document.getElementById("rce_method").value,
    is_allow_exception_leak: document.getElementById("is_allow_exception_leak").checked,
    local_scope: localScopeInput.value.trim(),
    banned_chr: document.getElementById("banned_chr").value,
    allowed_chr: document.getElementById("allowed_chr").value,
    banned_ast: document.getElementById("banned_ast").value,
    banned_re: document.getElementById("banned_re").value,
    max_length: document.getElementById("max_length").value,
    allow_unicode_bypass: document.getElementById("allow_unicode_bypass").checked,
    print_all_payload: document.getElementById("print_all_payload").checked,
    interactive: document.getElementById("interactive").checked,
    depth: document.getElementById("depth").value,
    recursion_limit: document.getElementById("recursion_limit").value,
    log_level: document.getElementById("log_level").value,
    timeout_sec: document.getElementById("timeout_sec").value,
  };
}

function resetOutput() {
  metaState.duration = null;
  metaState.exitCode = null;
  metaState.runnerCode = null;
  setOutputState("ready");
  setBadge("idle", "status_idle");
  updateMetaNodes();
  setTerminalTone("idle");
  setTerminalRunning(false);
}

modeButtons.forEach((btn) => {
  btn.addEventListener("click", () => switchMode(btn.dataset.mode));
});

langButtons.forEach((btn) => {
  btn.addEventListener("click", () => setLanguage(btn.dataset.lang));
});

resetBtn.addEventListener("click", () => {
  form.reset();
  switchMode("rce");
  document.getElementById("depth").value = "5";
  document.getElementById("recursion_limit").value = "200";
  document.getElementById("log_level").value = "INFO";
  document.getElementById("interactive").checked = true;
  document.getElementById("is_allow_exception_leak").checked = true;
  resetOutput();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = collectPayload();

  setBadge("running", "status_running");
  setTerminalTone("running");
  setOutputState("executing");
  setTerminalRunning(true);
  runBtn.disabled = true;

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    const bodyText = normalizeOutputText(
      data.output || data.error || JSON.stringify(data, null, 2)
    );
    outputState = "custom";
    output.textContent = bodyText;
    pulseTerminal();

    metaState.duration = data.duration_ms ?? null;
    metaState.exitCode = data.exit_code ?? null;
    metaState.runnerCode = data.runner_exit_code ?? null;
    updateMetaNodes();

    if (data.ok && data.success) {
      setBadge("success", "status_success");
      setTerminalTone("success");
    } else if (data.ok) {
      setBadge("idle", "status_finished");
      setTerminalTone("idle");
    } else {
      setBadge("error", "status_failed");
      setTerminalTone("error");
    }
  } catch (error) {
    setOutputState("request_failed", String(error));
    setBadge("error", "status_request_error");
    setTerminalTone("error");
  } finally {
    runBtn.disabled = false;
    setTerminalRunning(false);
  }
});

switchMode("rce");
initLanguage();
resetOutput();
