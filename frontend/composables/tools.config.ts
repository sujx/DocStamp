export interface ToolDef {
  key: string
  to: string
  icon: string
  label: string
  desc?: string
  group?: string
  order: number
}

export interface ToolGroup {
  key: string
  icon: string
  label: string
  tools: ToolDef[]
}

export const TOOLS: ToolDef[] = [
  // ── 顶层 ──
  { key: "dashboard", to: "/", icon: "i-heroicons-home", label: "tabs.dashboard", desc: "dashboard.description", order: 1 },
  { key: "md2docx", to: "/md-to-docx", icon: "i-heroicons-arrow-down-tray", label: "tabs.md2docx", desc: "md2docx.description", order: 2 },
  { key: "watermark", to: "/watermark", icon: "i-heroicons-beaker", label: "tabs.watermarkManagement", desc: "watermark.description", order: 3 },

  // ── Office 工具（展开到顶层）──
  { key: "properties", to: "/properties", icon: "i-heroicons-document-text", label: "tabs.properties", desc: "properties.description", order: 10 },
  { key: "excel-merge", to: "/excel-merge", icon: "i-heroicons-table-cells", label: "tabs.excelMerge", desc: "excelMerge.description", order: 11 },
  { key: "format-docx", to: "/format-docx", icon: "i-heroicons-document-check", label: "tabs.formatDocx", desc: "format.description", order: 12 },

  // ── PDF 工具组 ──
  { key: "file-assembly", to: "/file-assembly", icon: "i-heroicons-arrows-right-left", label: "tabs.fileAssembly", desc: "img2pdf.description", group: "pdf", order: 20 },
  { key: "print-split", to: "/print-split", icon: "i-heroicons-printer", label: "tabs.printSplit", desc: "printSplit.description", group: "pdf", order: 21 },
  { key: "pdf-editor", to: "/pdf-editor", icon: "i-heroicons-document", label: "tabs.pdfEditor", desc: "pdfEditor.description", group: "pdf", order: 22 },
  { key: "pdf-tools", to: "/pdf-tools", icon: "i-heroicons-wrench-screwdriver", label: "tabs.pdf-tools", desc: "pdf-tools.description", group: "pdf", order: 23 },
  { key: "pdf-merge", to: "/pdf-merge", icon: "i-heroicons-plus-circle", label: "tabs.pdfMerge", desc: "pdfMerge.description", group: "pdf", order: 24 },

  // ── 顶层 ──
  { key: "status", to: "/status", icon: "i-heroicons-chart-bar", label: "tabs.status", desc: "status.description", order: 30 },
]

export const SIDEBAR_GROUPS: (ToolDef | ToolGroup)[] = (() => {
  const map = new Map<string, ToolDef[]>()
  const roots: ToolDef[] = []

  for (const t of TOOLS) {
    if (t.group) {
      if (!map.has(t.group)) map.set(t.group, [])
      map.get(t.group)!.push(t)
    } else {
      roots.push(t)
    }
  }

  const result: (ToolDef | ToolGroup)[] = []
  const allItems = [...TOOLS].sort((a, b) => a.order - b.order)
  const seenGroups = new Set<string>()

  for (const t of allItems) {
    if (!t.group) {
      result.push(t)
    } else if (!seenGroups.has(t.group)) {
      seenGroups.add(t.group)
      const groupTools = map.get(t.group)!
      const firstTool = groupTools.reduce((min, tool) => tool.order < min.order ? tool : min)
      result.push({
        key: t.group,
        icon: firstTool.icon,
        label: `tabs.${t.group === 'office' ? 'officeTools' : 'pdfTools'}`,
        tools: groupTools.sort((a, b) => a.order - b.order),
      })
    }
  }

  return result
})()

export const DASHBOARD_TOOLS = TOOLS.filter(t => t.key !== "dashboard" && t.key !== "status")
