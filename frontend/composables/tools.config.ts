export interface ToolDef {
  key: string
  to: string
  icon: string
  label: string
  desc?: string
  order: number
}

export const TOOLS: ToolDef[] = [
  // ── 顶层 ──
  { key: "dashboard", to: "/", icon: "i-heroicons-home", label: "tabs.dashboard", order: 1 },
  { key: "md2docx", to: "/md-to-docx", icon: "i-heroicons-arrow-down-tray", label: "tabs.md2docx", desc: "md2docx.description", order: 2 },
  { key: "doc-to-md", to: "/doc-to-md", icon: "i-heroicons-document-arrow-down", label: "tabs.docToMd", desc: "docToMd.description", order: 3 },
  { key: "format-docx", to: "/format-docx", icon: "i-heroicons-document-check", label: "tabs.formatDocx", desc: "format.description", order: 4 },
  { key: "video-convert", to: "/video-convert", icon: "i-heroicons-video-camera", label: "tabs.videoConvert", desc: "videoConvert.description", order: 6 },
  { key: "rss-detect", to: "/rss-detect", icon: "i-heroicons-signal", label: "tabs.rssDetect", desc: "rssDetect.description", order: 7 },

  // ── Office 工具（展开到顶层）──
  { key: "properties", to: "/properties", icon: "i-heroicons-document-text", label: "tabs.properties", desc: "properties.description", order: 10 },
  { key: "excel-merge", to: "/excel-merge", icon: "i-heroicons-table-cells", label: "tabs.excelMerge", desc: "excelMerge.description", order: 11 },

  // ── PDF 工具（展开到顶层）──
  { key: "file-assembly", to: "/file-assembly", icon: "i-heroicons-arrows-right-left", label: "tabs.fileAssembly", desc: "img2pdf.description", order: 20 },
  { key: "print-split", to: "/print-split", icon: "i-heroicons-printer", label: "tabs.printSplit", desc: "printSplit.description", order: 21 },
  { key: "pdf-editor", to: "/pdf-editor", icon: "i-heroicons-document", label: "tabs.pdfEditor", desc: "pdfEditor.description", order: 22 },
  { key: "pdf-tools", to: "/pdf-tools", icon: "i-heroicons-wrench-screwdriver", label: "tabs.pdf-tools", desc: "pdf-tools.description", order: 23 },
  { key: "pdf-merge", to: "/pdf-merge", icon: "i-heroicons-plus-circle", label: "tabs.pdfMerge", desc: "pdfMerge.description", order: 24 },

  // ── 顶层 ──
  { key: "status", to: "/status", icon: "i-heroicons-chart-bar", label: "tabs.status", desc: "status.description", order: 30 },
]

// Sidebar 读这里；order 是展示顺序的唯一来源
export const SIDEBAR_ITEMS: ToolDef[] = [...TOOLS].sort((a, b) => a.order - b.order)
