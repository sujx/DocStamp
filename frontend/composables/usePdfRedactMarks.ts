/**
 * Geometry and list operations for the PDF redaction marks.
 *
 * 标记只存「页面归一化左上角分数」：x/y 是左上角占页面宽高的比例，w/h 是宽高比例，
 * 全部 ∈ [0,1]。缩放、设备像素比、页面旋转因此都不需要进模型——浏览器量出来的像素
 * 换算成分数之后，同一份坐标既能画在当前缩放下，也能原样发给后端。
 *
 * 纯函数，无 Vue 依赖，便于单测。
 */

export interface Point {
  x: number;
  y: number;
}

export interface MarkBox {
  page: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export type MarkSource = "manual" | "keyword";

export interface RedactMark extends MarkBox {
  id: string;
  source: MarkSource;
}

/** 8 个缩放把手：四个角 + 四条边的中点。 */
export type ResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

export interface RectLike {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** 小于页面这个比例的框视为误点，直接丢弃。 */
export const MIN_MARK_SIZE = 0.004;

let _seq = 0;

export function nextMarkId(): string {
  _seq += 1;
  return `m${_seq}`;
}

function clamp(value: number, lo: number, hi: number): number {
  return Math.min(Math.max(value, lo), hi);
}

function clamp01(value: number): number {
  return clamp(value, 0, 1);
}

/** 视口坐标 → 页面分数。 */
export function toFraction(px: number, py: number, rect: RectLike): Point {
  return {
    x: clamp01((px - rect.left) / (rect.width || 1)),
    y: clamp01((py - rect.top) / (rect.height || 1)),
  };
}

/** 两个分数的点 → 归一化框；太小（误点）返回 null。 */
export function boxFromDrag(page: number, start: Point, end: Point): MarkBox | null {
  const x1 = clamp01(start.x);
  const y1 = clamp01(start.y);
  const x2 = clamp01(end.x);
  const y2 = clamp01(end.y);

  const box: MarkBox = {
    page,
    x: Math.min(x1, x2),
    y: Math.min(y1, y2),
    w: Math.abs(x2 - x1),
    h: Math.abs(y2 - y1),
  };
  if (box.w < MIN_MARK_SIZE || box.h < MIN_MARK_SIZE) return null;
  return box;
}

/** 把框收进页面，并保证不小于最小尺寸。 */
export function clampBox(box: MarkBox): MarkBox {
  const x = Math.min(clamp01(box.x), 1 - MIN_MARK_SIZE);
  const y = Math.min(clamp01(box.y), 1 - MIN_MARK_SIZE);
  return {
    page: box.page,
    x,
    y,
    w: clamp(box.w, MIN_MARK_SIZE, 1 - x),
    h: clamp(box.h, MIN_MARK_SIZE, 1 - y),
  };
}

/** 平移：尺寸不变，顶到边界就停住（不压缩）。 */
export function moveBox(box: MarkBox, dx: number, dy: number): MarkBox {
  const w = Math.min(box.w, 1);
  const h = Math.min(box.h, 1);
  return {
    page: box.page,
    x: clamp(box.x + dx, 0, 1 - w),
    y: clamp(box.y + dy, 0, 1 - h),
    w,
    h,
  };
}

/** 拖某个把手：只动对应的边，拖过头停在最小尺寸而不是翻转。 */
export function resizeBox(box: MarkBox, handle: ResizeHandle, dx: number, dy: number): MarkBox {
  let left = box.x;
  let top = box.y;
  let right = box.x + box.w;
  let bottom = box.y + box.h;

  if (handle.includes("w")) left = Math.min(Math.max(0, left + dx), right - MIN_MARK_SIZE);
  if (handle.includes("e")) right = Math.max(Math.min(1, right + dx), left + MIN_MARK_SIZE);
  if (handle.includes("n")) top = Math.min(Math.max(0, top + dy), bottom - MIN_MARK_SIZE);
  if (handle.includes("s")) bottom = Math.max(Math.min(1, bottom + dy), top + MIN_MARK_SIZE);

  return { page: box.page, x: left, y: top, w: right - left, h: bottom - top };
}

/** 同页且真正相交（仅边界相接不算）。 */
export function boxesOverlap(a: MarkBox, b: MarkBox): boolean {
  return (
    a.page === b.page &&
    a.x < b.x + b.w &&
    b.x < a.x + a.w &&
    a.y < b.y + b.h &&
    b.y < a.y + a.h
  );
}

/** 追加关键词命中；与已有标记重叠的命中跳过，避免重复搜索叠框。 */
export function addKeywordMarks(
  existing: RedactMark[],
  boxes: MarkBox[],
  idFactory: () => string = nextMarkId,
): RedactMark[] {
  const all = [...existing];
  for (const box of boxes) {
    const candidate: RedactMark = { ...box, id: idFactory(), source: "keyword" };
    if (all.some((mark) => boxesOverlap(mark, candidate))) continue;
    all.push(candidate);
  }
  return all.length === existing.length ? existing : all;
}

/** 分数 → 整数百分比，给标记列表显示用。 */
export function percent(value: number): string {
  return `${Math.round(clamp01(value) * 100)}%`;
}

/**
 * 撤销栈：每次改动标记前压一份快照，撤销即弹回上一份。
 *
 * 只存标记数组，不存页面、选中状态——撤销只回退「有哪些标记、各自在哪」，视图状态由组件自理。
 * 压栈时逐个浅拷贝，避免调用方之后原地改标记把历史一起改掉。
 */
export function createMarkHistory(limit = 50) {
  const stack: RedactMark[][] = [];

  return {
    push(marks: RedactMark[]): void {
      stack.push(marks.map((mark) => ({ ...mark })));
      if (stack.length > limit) stack.shift();
    },
    undo(): RedactMark[] | null {
      return stack.pop() ?? null;
    },
  };
}
