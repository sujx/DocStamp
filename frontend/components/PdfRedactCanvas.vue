<template>
  <div class="overflow-auto rounded-lg bg-muted">
    <div class="relative mx-auto my-3" :style="{ width: `${zoom * 100}%` }">
      <img
        :src="pageUrl"
        class="block w-full select-none"
        draggable="false"
        alt=""
        @load="imageLoaded = true"
        @error="imageLoaded = false"
      />

      <div
        ref="stage"
        class="absolute inset-0 touch-none"
        :class="imageLoaded ? 'cursor-crosshair' : 'pointer-events-none'"
        @pointerdown="onStageDown"
      >
        <div
          v-for="mark in displayMarks"
          :key="mark.id"
          class="absolute cursor-move border-2 bg-brand-500/20"
          :class="[mark.id === selectedId || mark.id === DRAFT_ID ? 'border-brand-700' : 'border-white']"
          :style="rectStyle(mark)"
          @pointerdown="onMarkDown($event, mark)"
        >
          <span class="pointer-events-none absolute left-0 top-0 max-w-full truncate rounded-br bg-brand-700 px-1 text-xs text-white">
            {{ sourceLabel(mark.source) }}
          </span>

          <template v-if="mark.id === selectedId && mark.id !== DRAFT_ID">
            <UButton
              class="absolute -right-2 -top-2 !rounded-full !bg-red-600 !p-0 !text-white"
              size="xs"
              color="neutral"
              variant="solid"
              :aria-label="$t('pdfRedact.removeMark')"
              @pointerdown.stop
              @click.stop="emit('remove', mark.id)"
            >
              <UIcon name="i-heroicons-x-mark" class="size-3" />
            </UButton>

            <span
              v-for="h in HANDLES"
              :key="h.handle"
              class="absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white bg-brand-700"
              :class="HANDLE_CLASS[h.handle]"
              :style="h.style"
              @pointerdown.stop="onHandleDown($event, mark, h.handle)"
            />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MarkBox, MarkSource, Point, RedactMark, ResizeHandle } from "~/composables/usePdfRedactMarks";
import { boxFromDrag, clampBox, moveBox, resizeBox, toFraction } from "~/composables/usePdfRedactMarks";

const DRAFT_ID = "__draft__";

const props = defineProps<{
  pageUrl: string;
  pageNo: number;
  marks: RedactMark[];
  selectedId: string | null;
  zoom: number;
}>();

const emit = defineEmits<{
  create: [box: MarkBox];
  update: [id: string, box: MarkBox];
  remove: [id: string];
  select: [id: string | null];
}>();

const { t } = useI18n();

// Tailwind 按字面量扫描，类名必须写成静态字符串，不能拼 `cursor-${…}`。
const HANDLE_CLASS: Record<ResizeHandle, string> = {
  nw: "cursor-nwse-resize",
  n: "cursor-ns-resize",
  ne: "cursor-nesw-resize",
  e: "cursor-ew-resize",
  se: "cursor-nwse-resize",
  s: "cursor-ns-resize",
  sw: "cursor-nesw-resize",
  w: "cursor-ew-resize",
};

const HANDLES: { handle: ResizeHandle; style: Record<string, string> }[] = [
  { handle: "nw", style: { left: "0%", top: "0%" } },
  { handle: "n", style: { left: "50%", top: "0%" } },
  { handle: "ne", style: { left: "100%", top: "0%" } },
  { handle: "e", style: { left: "100%", top: "50%" } },
  { handle: "se", style: { left: "100%", top: "100%" } },
  { handle: "s", style: { left: "50%", top: "100%" } },
  { handle: "sw", style: { left: "0%", top: "100%" } },
  { handle: "w", style: { left: "0%", top: "50%" } },
];

/** 一次拖拽的全部状态；`rect` 在按下时量一次，拖动期间页面不会动。 */
type Drag = {
  kind: "create" | "move" | "resize";
  pointerId: number;
  rect: DOMRect;
  start: Point;
  origin: MarkBox;
  id: string;
  handle: ResizeHandle;
  box: MarkBox | null;
};

const stage = ref<HTMLElement | null>(null);
const imageLoaded = ref(false);
const drag = ref<Drag | null>(null);

watch(
  () => props.pageUrl,
  () => {
    imageLoaded.value = false;
    drag.value = null;
  },
);

/** 本页标记；正在拖的那个换成实时框，草稿框追加在最后。 */
const displayMarks = computed<RedactMark[]>(() => {
  const d = drag.value;
  if (!d || !d.box) return props.marks;
  const live = d.box;
  if (d.kind === "create") return [...props.marks, { ...live, id: DRAFT_ID, source: "manual" }];
  return props.marks.map((mark) => (mark.id === d.id ? { ...mark, ...live } : mark));
});

function rectStyle(box: MarkBox): Record<string, string> {
  return {
    left: `${box.x * 100}%`,
    top: `${box.y * 100}%`,
    width: `${box.w * 100}%`,
    height: `${box.h * 100}%`,
  };
}

function sourceLabel(source: MarkSource): string {
  return source === "keyword" ? t("pdfRedact.sourceKeyword") : t("pdfRedact.sourceManual");
}

function beginDrag(
  evt: PointerEvent,
  kind: Drag["kind"],
  id: string,
  handle: ResizeHandle,
  origin: MarkBox,
) {
  if (evt.button !== 0) return;
  const el = stage.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  if (!rect.width || !rect.height) return;

  (evt.currentTarget as HTMLElement).setPointerCapture(evt.pointerId);
  drag.value = {
    kind,
    pointerId: evt.pointerId,
    rect,
    start: toFraction(evt.clientX, evt.clientY, rect),
    origin,
    id,
    handle,
    box: kind === "create" ? null : { ...origin },
  };
}

function onStageDown(evt: PointerEvent) {
  // 落在空白处：先取消选中，再开始拉新框。
  emit("select", null);
  beginDrag(evt, "create", DRAFT_ID, "se", { page: props.pageNo, x: 0, y: 0, w: 0, h: 0 });
}

function onMarkDown(evt: PointerEvent, mark: RedactMark) {
  evt.stopPropagation();
  emit("select", mark.id);
  beginDrag(evt, "move", mark.id, "se", mark);
}

function onHandleDown(evt: PointerEvent, mark: RedactMark, handle: ResizeHandle) {
  evt.stopPropagation();
  beginDrag(evt, "resize", mark.id, handle, mark);
}

function onPointerMove(evt: PointerEvent) {
  const d = drag.value;
  if (!d || evt.pointerId !== d.pointerId) return;

  const now = toFraction(evt.clientX, evt.clientY, d.rect);
  const dx = now.x - d.start.x;
  const dy = now.y - d.start.y;

  if (d.kind === "create") d.box = boxFromDrag(props.pageNo, d.start, now);
  else if (d.kind === "move") d.box = moveBox(d.origin, dx, dy);
  else d.box = resizeBox(d.origin, d.handle, dx, dy);
}

function onPointerUp(evt: PointerEvent) {
  const d = drag.value;
  if (!d || evt.pointerId !== d.pointerId) return;
  drag.value = null;
  if (!d.box) return;

  if (d.kind === "create") {
    emit("create", { ...d.box, page: props.pageNo });
  } else {
    emit("update", d.id, clampBox({ ...d.box, page: props.pageNo }));
  }
}

// 拖动可能移出画布，所以监听挂在 window 上；指针捕获保证事件不会中途丢失。
onMounted(() => {
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("pointercancel", onPointerUp);
});
</script>
