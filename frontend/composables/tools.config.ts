/**
 * 工具注册表 — 所有工具的单一定义源。
 *
 * 新增工具只需在此文件加一条记录，Sidebar、Dashboard、
 * 路由配置自动同步，不再需要手动修改 5 个文件。
 *
 * 字段说明：
 *   key       唯一标识（Sidebar 用）
 *   to        路由路径
 *   icon      Heroicons 图标名
 *   label     i18n key（tabs.*）
 *   desc      i18n key（*.description，仪表盘卡片用）
 *   group     分组名（Sidebar 分组用；无则为顶层项）
 *   order     组内排序权重（越小越靠前）
 */

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

  // ── Office 工具组 ──
  { key: "properties", to: "/properties", icon: "i-heroicons-document-text", label: "tabs.properties", desc: "properties.description", group: "office", order: 10 },
  { key: "excel-merge", to: "/excel-merge", icon: "i-heroicons-table-cells", label: "tabs.excelMerge", desc: "excelMerge.description", group: "office", order: 11 },
  { key: "format-docx", to: "/format-docx", icon: "i-heroicons-document-check", label: "tabs.formatDocx", desc: "format.description", group: "office", order: 12 },
  { key: "metadata-clean", to: "/metadata-clean", icon: "i-heroicons-shield-exclamation", label: "tabs.metadataClean", desc: "metadataClean.description", group: "office", order: 13 },

  // ── PDF 工具组 ──
  { key: "file-assembly", to: "/file-assembly", icon: "i-heroicons-arrows-right-left", label: "tabs.fileAssembly", desc: "img2pdf.description", group: "pdf", order: 20 },
  { key: "print-split", to: "/print-split", icon: "i-heroicons-printer", label: "tabs.printSplit", desc: "printSplit.description", group: "pdf", order: 21 },
  { key: "pdf-editor", to: "/pdf-editor", icon: "i-heroicons-document", label: "tabs.pdfEditor", desc: "pdfEditor.description", group: "pdf", order: 22 },
  { key: "pdf-to-text", to: "/pdf-to-text", icon: "i-heroicons-document-magnifying-glass", label: "tabs.pdfToText", desc: "pdfToText.description", group: "pdf", order: 23 },
  { key: "pdf-merge", to: "/pdf-merge", icon: "i-heroicons-plus-circle", label: "tabs.pdfMerge", desc: "pdfMerge.description", group: "pdf", order: 24 },
  { key: "pdf-compress", to: "/pdf-compress", icon: "i-heroicons-arrows-pointing-in", label: "tabs.pdfCompress", desc: "pdfCompress.description", group: "pdf", order: 25 },
  { key: "page-decorate", to: "/page-decorate", icon: "i-heroicons-document-check", label: "tabs.pageDecorate", desc: "pageDecorate.description", group: "pdf", order: 26 },
  { key: "image-process", to: "/image-process", icon: "i-heroicons-photo", label: "tabs.imageProcess", desc: "imageProcess.description", group: "pdf", order: 27 },

  // ── 顶层 ──
  { key: "status", to: "/status", icon: "i-heroicons-chart-bar", label: "tabs.status", desc: "status.description", order: 30 },
]

/** Sidebar 用的分组结构 */
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
  // Insert groups at the position of their first tool
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

/** Dashboard 卡片列表（不含仪表盘自身和 status） */
export const DASHBOARD_TOOLS = TOOLS.filter(t => t.key !== "dashboard" && t.key !== "status")
