<template>
  <div class="md2docx-root">
    <!-- Editor + Preview (equal columns) -->
    <div class="columns-wrapper">
      <!-- Left: Editor Panel -->
      <div class="column-panel">
        <div
          class="panel-card"
          :style="{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)' }"
        >
          <!-- Header -->
          <div class="panel-header">
            <span class="panel-title">
              <UIcon name="i-heroicons-pencil-square" class="w-4 h-4" />
              {{ $t("md2docx.editor") }}
            </span>
            <div class="toolbar">
              <UButton size="xs" variant="outline" color="neutral" @click="upload">
                <UIcon name="i-heroicons-folder-open" class="w-3.5 h-3.5 mr-1" />
                {{ $t("md2docx.upload") }}
              </UButton>
              <UButton size="xs" variant="outline" color="neutral" @click="loadSample">
                <UIcon name="i-heroicons-document-text" class="w-3.5 h-3.5 mr-1" />
                {{ $t("md2docx.sample") }}
              </UButton>
              <UButton size="xs" variant="outline" color="neutral" @click="clearAll">
                <UIcon name="i-heroicons-trash" class="w-3.5 h-3.5 mr-1" />
                {{ $t("md2docx.clear") }}
              </UButton>
              <UButton
                size="xs" color="primary" variant="outline"
                :loading="aiCorrecting" :disabled="!content.trim()"
                @click="aiCorrect"
              >
                <UIcon name="i-heroicons-sparkles" class="w-3.5 h-3.5 mr-1" />
                {{ aiCorrecting ? $t("ai.correcting") : $t("ai.correct") }}
              </UButton>
            </div>
            <input ref="fileInput" type="file" accept=".md,.markdown,.txt" class="hidden" @change="onFileUpload" />
          </div>

          <!-- Editor Area -->
          <div
            class="editor-area"
            :class="{ 'is-dragover': dragOver }"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="onDrop"
          >
            <div v-if="dragOver" class="drop-overlay">
              <UIcon name="i-heroicons-arrow-up-tray" class="w-10 h-10" />
              <p>{{ $t("md2docx.dropHint") }}</p>
            </div>
            <textarea
              ref="editorEl"
              v-model="content"
              class="md-editor"
              :placeholder="$t('md2docx.placeholder')"
              :aria-label="$t('md2docx.editor')"
              spellcheck="false"
              @input="onInput"
            />
          </div>
        </div>
      </div>

      <!-- Right: Preview Panel -->
      <div class="column-panel">
        <div
          class="panel-card preview-panel"
          :style="{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)' }"
        >
          <!-- Header -->
          <div class="panel-header">
            <span class="panel-title">
              <UIcon name="i-heroicons-eye" class="w-4 h-4" />
              {{ $t("md2docx.preview") }}
            </span>
            <span class="panel-badge" v-if="previewHtml" style="background: var(--color-brand-soft); color: var(--color-brand-700);">
              {{ $t("md2docx.live") }}
            </span>
          </div>

          <!-- Preview Content -->
          <div class="preview-area">
            <!-- Loading -->
            <div v-if="previewLoading" class="preview-placeholder">
              <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin" />
              <p>{{ $t("md2docx.previewLoading") }}</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!previewHtml" class="preview-placeholder">
              <div class="empty-icon-circle">
                <UIcon name="i-heroicons-document-text" class="w-8 h-8" />
              </div>
              <p class="empty-title">{{ $t("md2docx.emptyTitle") }}</p>
              <span class="empty-hint">{{ $t("md2docx.emptyHint") }}</span>
            </div>

            <!-- Rendered Document Paper -->
            <div v-else class="doc-paper" v-html="previewHtml" ref="paperEl" />
          </div>
        </div>
      </div>
    </div>

    <!-- AI format hint -->
    <div v-if="aiClassified" class="flex justify-center mt-4">
      <span
        class="inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full"
        :class="aiIsOfficial ? 'bg-brand-soft text-brand-700' : 'text-tertiary'"
        :style="aiIsOfficial ? {} : { backgroundColor: 'var(--color-muted)' }"
      >
        <UIcon :name="aiIsOfficial ? 'i-heroicons-sparkles' : 'i-heroicons-document'" class="size-3" />
        {{ aiIsOfficial ? $t("ai.officialSuggestion") : $t("ai.unofficial") }}
      </span>
    </div>

    <!-- Action Bar -->
    <div class="action-bar">
      <div class="convert-buttons">
        <UButton
          variant="outline" size="lg"
          :disabled="!content.trim()" :loading="convertingPlain"
          class="convert-btn"
          @click="convertPlain"
        >
          <UIcon name="i-heroicons-document" class="w-5 h-5 mr-2" />
          {{ convertingPlain ? $t("md2docx.converting") : $t("md2docx.convertPlain") }}
        </UButton>
        <UButton
          color="primary" size="lg"
          :disabled="!content.trim()" :loading="convertingOfficial"
          class="convert-btn"
          @click="convertOfficial"
        >
          <UIcon name="i-heroicons-arrow-right-circle" class="w-5 h-5 mr-2" />
          {{ convertingOfficial ? $t("md2docx.converting") : $t("md2docx.convertOfficial") }}
        </UButton>
      </div>
      <p class="privacy-hint text-pretty">
        <UIcon name="i-heroicons-shield-check" class="w-3.5 h-3.5 inline" />
        {{ $t("md2docx.privacy") }}
      </p>
      <a
        href="/GBT9704-2012.pdf" target="_blank"
        class="text-xs underline underline-offset-2"
        :style="{ color: 'var(--color-text-tertiary)' }"
      >{{ $t("md2docx.gbtLink") }}</a>
    </div>

    <!-- Loading Overlay -->
    <Transition name="overlay-fade">
      <div v-if="convertingPlain || convertingOfficial" class="loading-overlay">
        <svg class="spinner" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
          <circle class="track" cx="25" cy="25" r="20" fill="none" stroke="var(--color-border-default)" stroke-width="4" />
          <circle class="ring" cx="25" cy="25" r="20" fill="none" stroke="var(--color-brand-700)" stroke-width="4" stroke-linecap="round" stroke-dasharray="90 150" />
        </svg>
        <p class="loading-text">{{ $t("md2docx.converting") }}</p>
        <p class="loading-sub">{{ $t("md2docx.convertingHint") }}</p>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { nextTick } from "vue";
import { marked } from "marked";
import hljs from "highlight.js";
import DOMPurify from "dompurify";

const { t } = useI18n();
const toast = useToast();
const { showError } = useError();
const { correct: aiCorrectText, classify: aiClassifyText, loading: aiCorrecting } = useAi();

const aiClassified = ref(false);
const aiIsOfficial = ref(false);

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
  highlight: function (code: string, lang: string) {
    try {
      const language = hljs.getLanguage(lang) ? lang : "plaintext";
      return hljs.highlight(code, { language }).value;
    } catch { return code; }
  },
});

function sanitize(html: string): string {
  try {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ["h1","h2","h3","h4","h5","h6","p","br","hr","strong","em","b","i","u","s","del","ins","sub","sup","ol","ul","li","a","img","table","thead","tbody","tr","th","td","blockquote","pre","code","span","div","svg","g","path","rect","circle","ellipse","line","polyline","polygon","text","tspan","defs","marker","use","math","semantics","annotation","mrow","mi","mo","mn","mfrac","msqrt","mroot","mover","munder","msub","msup"],
      ALLOWED_ATTR: ["href","title","target","src","alt","width","height","class","align","valign","viewBox","d","fill","stroke","stroke-width","stroke-linecap","stroke-linejoin","transform","x","y","cx","cy","r","rx","ry","x1","y1","x2","y2","points","id","xmlns"],
    });
  } catch { return html; }
}

// State
const content = ref("");
const previewHtml = ref("");
const previewLoading = ref(false);
const convertingPlain = ref(false);
const convertingOfficial = ref(false);
const dragOver = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const paperEl = ref<HTMLElement | null>(null);
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// ── Preview rendering ──────────────────────────────────────────
const API_BASE = import.meta.dev ? "http://localhost:5000" : "";

function renderMarkdown(val: string): string {
  if (!val.trim()) return "";
  try {
    const raw = marked.parse(val) as string;
    return sanitize(raw);
  } catch (e) {
    console.error("Markdown render error:", e);
    // Fallback: escape HTML and wrap in <pre>
    return "<pre>" + val.replace(/&/g,"&amp;").replace(/</g,"&lt;") + "</pre>";
  }
}

function doUpdatePreview() {
  previewHtml.value = renderMarkdown(content.value);
}

// Sample content
const sampleText = `# 关于召开工作会议的通知

各部门：

为总结第一季度工作成果，部署下一阶段重点工作，经研究决定召开工作会议。现将有关事项通知如下：

## 一、会议时间

2026年6月1日（星期一）上午9时

## 二、会议地点

机关办公楼三楼会议室

## 三、参会人员

各部门负责人及相关工作人员。

### （一）会议主持

由办公室张主任主持本次会议。

### （二）会议记录

由办公室李秘书负责会议记录。

## 四、会议议程

1. 各部门汇报第一季度工作完成情况；
2. 研究部署第二季度重点工作任务；
3. 讨论审议相关制度修订草案；
4. 其他需要研究的事项。

- 请各部门提前准备好汇报材料
- 与会人员请提前10分钟入场

## 五、有关要求

各部门要高度重视本次会议，认真做好参会准备。如有特殊情况不能参会，须提前向办公室请假。

特此通知。

办公室
2026年5月30日`;

// Methods
function upload() { fileInput.value?.click(); }

function onDrop(e: DragEvent) {
  dragOver.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    readFile(files[0]);
  }
}

function onFileUpload(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) readFile(f);
}

async function readFile(f: File) {
  try {
    const text = await f.text();
    content.value = text;
    toast.add({ title: t("md2docx.fileLoaded", { name: f.name }), color: "success" });
  } catch {
    toast.add({ title: t("md2docx.fileReadError"), color: "error" });
  }
}

function loadSample() {
  content.value = sampleText;
  doUpdatePreview();
}

function clearAll() {
  content.value = "";
  previewHtml.value = "";
}

function onInput() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(doUpdatePreview, 200);
}

function updatePreview() {
  doUpdatePreview();
}

// ... (keep renderPostProcess unchanged)

async function renderPostProcess() {
  const container = paperEl.value;
  if (!container) return;

  const mermaidBlocks = container.querySelectorAll("pre.mermaid");
  if (mermaidBlocks.length > 0) {
    try {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({ startOnLoad: false, theme: "default" });
      await mermaid.run({ nodes: Array.from(mermaidBlocks) });
    } catch { /* optional */ }
  }
}

async function aiCorrect() {
  try {
    const result = await aiCorrectText(content.value);
    if (result.changed) {
      content.value = result.text;
      doUpdatePreview();
      toast.add({ title: t("ai.corrected", { n: 1 }), color: "success" });
    }
  } catch { /* silent — backend degrades gracefully */ }
}

// Classify on debounced input (2s after last keystroke)
let classifyTimer: ReturnType<typeof setTimeout> | null = null;
watch(content, (val) => {
  if (classifyTimer) clearTimeout(classifyTimer);
  if (!val.trim()) { aiClassified.value = false; return; }
  classifyTimer = setTimeout(async () => {
    try {
      const result = await aiClassifyText(val);
      aiClassified.value = true;
      aiIsOfficial.value = result.is_official;
    } catch { aiClassified.value = false; }
  }, 2000);
});

async function doConvert(format: "plain" | "official") {
  if (!content.value.trim()) {
    toast.add({ title: t("md2docx.emptyWarning"), color: "warning" });
    return;
  }
  if (format === "plain") convertingPlain.value = true;
  else convertingOfficial.value = true;
  try {
    const resp = await axios.post(`${API_BASE}/api/v1/convert?format=${format}`, { content: content.value });
    const dlResp = await axios.get(`${API_BASE}/api/v1/download/${resp.data.download_id}`, { responseType: "blob" });
    const url = URL.createObjectURL(dlResp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = resp.data.filename;
    a.click();
    URL.revokeObjectURL(url);
    toast.add({ title: t("md2docx.success"), color: "success" });
  } catch (e: any) {
    showError(e);
  } finally {
    convertingPlain.value = false;
    convertingOfficial.value = false;
  }
}

function convertPlain() { doConvert("plain"); }
function convertOfficial() { doConvert("official"); }
</script>

<style scoped>
.md2docx-root {
  max-width: 1440px;
  margin: 0 auto;
}

.columns-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .columns-wrapper {
    grid-template-columns: 1fr;
  }
}

/* ── Panel Card ──────────────────────────────────────────────── */
.column-panel {
  display: flex;
}

.panel-card {
  display: flex;
  flex-direction: column;
  border: 1px solid;
  border-radius: 10px;
  overflow: hidden;
  width: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-default);
  background: #fafbfc;
  flex-shrink: 0;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 9999px;
  font-weight: 600;
}

.toolbar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Editor ───────────────────────────────────────────────────── */
.editor-area {
  flex: 1;
  position: relative;
  min-height: 0;
}

.editor-area.is-dragover {
  background: var(--color-brand-soft);
}

.drop-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-brand-soft);
  border: 2px dashed var(--color-brand-700);
  z-index: 10;
  color: var(--color-brand-700);
}

.drop-overlay p {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
}

.md-editor {
  width: 100%;
  height: 100%;
  min-height: 560px;
  border: none;
  outline: none;
  resize: none;
  padding: 20px;
  font-family: "JetBrains Mono", "Fira Code", Consolas, Monaco, monospace;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
  background: var(--color-surface);
}

.md-editor:focus {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--color-brand-700);
}

.md-editor::placeholder {
  color: #b8bcc2;
  font-size: 13px;
}

/* ── Preview Area ─────────────────────────────────────────────── */
.preview-area {
  flex: 1;
  overflow-y: auto;
  background: var(--color-muted);
  padding: 20px;
  min-height: 560px;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 506px;
  color: var(--color-text-tertiary);
}

.empty-icon-circle {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-muted);
  border-radius: 50%;
  margin-bottom: 4px;
  color: var(--color-text-tertiary);
}

.empty-title {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.empty-hint {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.6;
}

/* ── Document Paper ──────────────────────────────────────────── */
.doc-paper {
  background:
    #fefefe;
  padding: 56px 48px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 3px 8px rgba(0, 0, 0, 0.05);
  font-family: "仿宋_GB2312", "FangSong", "STFangsong", serif;
  font-size: 16px;
  line-height: 28.6pt;
  color: #000;
  word-break: break-word;
  border-radius: 2px;
}

.doc-paper :deep(h1) {
  text-align: center;
  font-family: "方正小标宋简体", "STSong", serif;
  font-size: 22pt;
  font-weight: 400;
  margin-bottom: 1.2em;
  line-height: 1.4;
}

.doc-paper :deep(h2) {
  font-family: "黑体", "SimHei", "STHeiti", sans-serif;
  font-size: 16pt;
  font-weight: 700;
  margin: 0.6em 0;
  text-align: justify;
}

.doc-paper :deep(h3) {
  font-family: "楷体_GB2312", "KaiTi", "STKaiti", serif;
  font-size: 16pt;
  font-weight: 700;
  margin: 0.6em 0;
  text-align: justify;
}

.doc-paper :deep(h4) {
  font-family: "仿宋_GB2312", "FangSong", serif;
  font-size: 16pt;
  font-weight: 700;
  margin: 0.6em 0;
  text-align: justify;
}

.doc-paper :deep(p) {
  text-indent: 2em;
  margin: 0;
  text-align: justify;
}

@media (max-width: 768px) {
  .preview-area { padding: 12px; min-height: 454px; }
  .doc-paper { padding: 32px 24px; }
  .md-editor { min-height: 454px; padding: 16px; }
}

/* ── Action Bar ─────────────────────────────────────────────── */
.action-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
}

.convert-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.convert-btn {
  min-width: 160px;
  transition: transform 150ms ease-out, box-shadow 150ms ease-out;
}

.convert-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 138, 61, 0.25);
}

.privacy-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ── Loading Overlay ────────────────────────────────────────── */
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: rgba(249, 247, 232, 0.94);
}

.spinner {
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

.spinner .ring {
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

@keyframes dash {
  0% { stroke-dasharray: 1, 150; stroke-dashoffset: 0; }
  50% { stroke-dasharray: 90, 150; stroke-dashoffset: -35; }
  100% { stroke-dasharray: 90, 150; stroke-dashoffset: -124; }
}

.loading-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.loading-sub {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.overlay-fade-enter-active { transition: opacity 200ms ease-out; }
.overlay-fade-leave-active { transition: opacity 150ms ease-out; }
.overlay-fade-enter-from,
.overlay-fade-leave-to { opacity: 0; }
</style>
