/**
 * Tests for usePdfRedactMarks — the geometry behind drag-to-mark.
 *
 * 标记只存「页面归一化左上角分数」（x/y/w/h ∈ [0,1]），所以缩放、设备像素比、页面旋转
 * 全都不进模型。这里钉住三件事：拖拽方向不影响结果、标记永远留在页面内、关键词命中去重。
 */
import { describe, it, expect } from "vitest";
import type { MarkBox, RedactMark } from "../usePdfRedactMarks";
import {
  MIN_MARK_SIZE,
  addKeywordMarks,
  boxFromDrag,
  boxesOverlap,
  clampBox,
  createMarkHistory,
  moveBox,
  percent,
  resizeBox,
  toFraction,
} from "../usePdfRedactMarks";

const RECT = { left: 100, top: 50, width: 400, height: 800 };
const box = (over: Partial<MarkBox> = {}) => ({
  page: 1,
  x: 0.2,
  y: 0.2,
  w: 0.3,
  h: 0.1,
  ...over,
});
const mark = (over: Partial<MarkBox> = {}): RedactMark => ({ ...box(over), id: "m1", source: "manual" });

describe("toFraction", () => {
  it("把视口坐标换算成页面分数", () => {
    expect(toFraction(300, 450, RECT)).toEqual({ x: 0.5, y: 0.5 });
  });

  it("页面外的点会被夹到 [0,1]", () => {
    expect(toFraction(0, 0, RECT)).toEqual({ x: 0, y: 0 });
    expect(toFraction(900, 2000, RECT)).toEqual({ x: 1, y: 1 });
  });
});

describe("boxFromDrag", () => {
  it("正向拖拽得到左上角 + 宽高", () => {
    const mark = boxFromDrag(2, { x: 0.1, y: 0.2 }, { x: 0.4, y: 0.5 })!;

    expect(mark.page).toBe(2);
    expect(mark.x).toBeCloseTo(0.1);
    expect(mark.y).toBeCloseTo(0.2);
    expect(mark.w).toBeCloseTo(0.3);
    expect(mark.h).toBeCloseTo(0.3);
  });

  it("反向拖拽（右下往左上）得到同样的框", () => {
    const forward = boxFromDrag(1, { x: 0.1, y: 0.2 }, { x: 0.4, y: 0.5 });
    const backward = boxFromDrag(1, { x: 0.4, y: 0.5 }, { x: 0.1, y: 0.2 });

    expect(backward!.x).toBeCloseTo(forward!.x);
    expect(backward!.y).toBeCloseTo(forward!.y);
    expect(backward!.w).toBeCloseTo(forward!.w);
    expect(backward!.h).toBeCloseTo(forward!.h);
  });

  it("小于最小尺寸的拖拽（误点）被丢弃", () => {
    expect(boxFromDrag(1, { x: 0.5, y: 0.5 }, { x: 0.5 + MIN_MARK_SIZE / 2, y: 0.5 })).toBeNull();
  });

  it("超出页面的拖拽被夹回页内", () => {
    const mark = boxFromDrag(1, { x: -0.2, y: 0.9 }, { x: 0.5, y: 1.4 })!;

    expect(mark.x).toBe(0);
    expect(mark.y + mark.h).toBeLessThanOrEqual(1);
  });
});

describe("clampBox", () => {
  it("把溢出的框收进页面", () => {
    const clamped = clampBox(box({ x: 0.8, y: 0.95, w: 0.5, h: 0.5 }));

    expect(clamped.x).toBeCloseTo(0.8);
    expect(clamped.y).toBeCloseTo(0.95);
    expect(clamped.x + clamped.w).toBeCloseTo(1);
    expect(clamped.y + clamped.h).toBeCloseTo(1);
  });

  it("给过小的框一个下限尺寸", () => {
    const clamped = clampBox(box({ w: 0, h: 0 }));

    expect(clamped.w).toBeGreaterThanOrEqual(MIN_MARK_SIZE);
    expect(clamped.h).toBeGreaterThanOrEqual(MIN_MARK_SIZE);
  });
});

describe("moveBox", () => {
  it("平移时尺寸不变", () => {
    const moved = moveBox(box(), 0.1, -0.1);

    expect(moved.x).toBeCloseTo(0.3);
    expect(moved.y).toBeCloseTo(0.1);
    expect(moved.w).toBeCloseTo(0.3);
    expect(moved.h).toBeCloseTo(0.1);
  });

  it("顶到右边界时停止滑动而不是压缩", () => {
    const moved = moveBox(box({ x: 0.7, w: 0.3 }), 0.5, 0);

    expect(moved.x).toBeCloseTo(0.7);
    expect(moved.w).toBeCloseTo(0.3);
  });

  it("顶到左/上边界时停在 0", () => {
    const moved = moveBox(box(), -0.9, -0.9);

    expect(moved.x).toBe(0);
    expect(moved.y).toBe(0);
  });
});

describe("resizeBox", () => {
  it("拖右下角改变宽高，左上角不动", () => {
    const resized = resizeBox(box(), "se", 0.1, 0.2);

    expect(resized.x).toBeCloseTo(0.2);
    expect(resized.y).toBeCloseTo(0.2);
    expect(resized.w).toBeCloseTo(0.4);
    expect(resized.h).toBeCloseTo(0.3);
  });

  it("拖左上角时对角保持不动", () => {
    const resized = resizeBox(box(), "nw", 0.05, 0.05);

    expect(resized.x).toBeCloseTo(0.25);
    expect(resized.y).toBeCloseTo(0.25);
    expect(resized.w).toBeCloseTo(0.25);
    expect(resized.h).toBeCloseTo(0.05);
  });

  it("只拖下边缘不影响左右", () => {
    const resized = resizeBox(box(), "s", 0.4, 0.1);

    expect(resized.x).toBeCloseTo(0.2);
    expect(resized.w).toBeCloseTo(0.3);
    expect(resized.h).toBeCloseTo(0.2);
  });

  it("反向拖到翻转时停在最小尺寸，不产生负宽高", () => {
    const resized = resizeBox(box({ x: 0.2, w: 0.3 }), "w", 0.9, 0);

    expect(resized.w).toBeGreaterThanOrEqual(MIN_MARK_SIZE);
    expect(resized.x + resized.w).toBeCloseTo(0.5);
  });

  it("不会越过页面边界", () => {
    const resized = resizeBox(box(), "se", 5, 5);

    expect(resized.x + resized.w).toBeLessThanOrEqual(1);
    expect(resized.y + resized.h).toBeLessThanOrEqual(1);
  });
});

describe("boxesOverlap", () => {
  it("相交为真", () => {
    expect(boxesOverlap(box(), box({ x: 0.3, y: 0.25 }))).toBe(true);
  });

  it("仅边界相接算不相交", () => {
    expect(boxesOverlap(box({ x: 0, w: 0.2 }), box({ x: 0.2, w: 0.2 }))).toBe(false);
  });

  it("不同页永远不相交", () => {
    expect(boxesOverlap(box(), box({ page: 3 }))).toBe(false);
  });
});

describe("addKeywordMarks", () => {
  it("为每个命中生成一个关键词标记", () => {
    const marks = addKeywordMarks([], [box({ x: 0, w: 0.1 }), box({ x: 0.5, w: 0.1 })]);

    expect(marks).toHaveLength(2);
    expect(marks.every((m) => m.source === "keyword")).toBe(true);
    expect(new Set(marks.map((m) => m.id)).size).toBe(2);
  });

  it("跳过与已有标记重叠的命中，避免重复搜索叠框", () => {
    const existing = addKeywordMarks([], [box({ x: 0.2, w: 0.2 })]);

    const again = addKeywordMarks(existing, [box({ x: 0.25, w: 0.2 })]);

    expect(again).toHaveLength(1);
  });

  it("保留同一批里互不重叠的命中", () => {
    const marks = addKeywordMarks([], [box({ x: 0, w: 0.1 }), box({ x: 0.6, w: 0.1 })]);

    expect(marks.map((m) => m.source)).toEqual(["keyword", "keyword"]);
    expect(marks[0]!.x).toBeCloseTo(0);
    expect(marks[1]!.x).toBeCloseTo(0.6);
  });
});

describe("percent", () => {
  it("把分数转成整数百分比", () => {
    expect(percent(0.1234)).toBe("12%");
    expect(percent(1)).toBe("100%");
    expect(percent(0)).toBe("0%");
  });
});

describe("createMarkHistory", () => {
  it("撤销拿回上一次改动前的标记", () => {
    const history = createMarkHistory();
    const before = [mark()];

    history.push(before);

    expect(history.undo()).toEqual(before);
  });

  it("没有可撤销的改动时返回 null", () => {
    expect(createMarkHistory().undo()).toBeNull();
  });

  it("压栈的是快照副本，之后改动原数组不会污染撤销结果", () => {
    const history = createMarkHistory();
    const live = [mark()];

    history.push(live);
    live.push(mark({ x: 0.9 }));
    live[0]!.x = 0.7;

    expect(history.undo()).toEqual([mark()]);
  });

  it("连续撤销按后进先出逐层回退", () => {
    const history = createMarkHistory();
    history.push([]);
    history.push([mark()]);

    expect(history.undo()).toEqual([mark()]);
    expect(history.undo()).toEqual([]);
    expect(history.undo()).toBeNull();
  });

  it("超过上限后丢掉最早的快照", () => {
    const history = createMarkHistory(2);
    history.push([mark({ x: 0.1 })]);
    history.push([mark({ x: 0.2 })]);
    history.push([mark({ x: 0.3 })]);

    expect(history.undo()).toEqual([mark({ x: 0.3 })]);
    expect(history.undo()).toEqual([mark({ x: 0.2 })]);
    expect(history.undo()).toBeNull();
  });
});
