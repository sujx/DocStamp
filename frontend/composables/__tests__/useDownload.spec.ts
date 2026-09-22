/**
 * Tests for useDownload composable.
 *
 * downloadBlob 的时序必须钉死：先把临时 <a> 挂进 body 再 click，对象 URL 要等当前
 * 任务结束、下载已经启动之后才 revoke——在点击的同一个任务里立刻 revokeObjectURL
 * 会让部分浏览器直接取消下载。临时 <a> 与对象 URL 都必须回收，否则留到页面关闭。
 *
 * import.meta.client 在 vitest 默认未定义（Nuxt 客户端构建里为 true），vitest.config.ts
 * 已将其定义为 true，因此这里的 toast 断言验证的是客户端真实分支。
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { useDownload } from "../useDownload";

describe("useDownload", () => {
  let revokeSpy: ReturnType<typeof vi.fn>;
  let clickSpy: ReturnType<typeof vi.fn>;
  let toastAdd: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    if (!URL.createObjectURL) {
      (URL as unknown as Record<string, unknown>).createObjectURL = () => "";
    }
    if (!URL.revokeObjectURL) {
      (URL as unknown as Record<string, unknown>).revokeObjectURL = () => {};
    }
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock-url");
    revokeSpy = vi.fn();
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(revokeSpy);
    clickSpy = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(clickSpy);
    toastAdd = vi.fn();
    vi.stubGlobal("useToast", () => ({ add: toastAdd }));
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    document.body.innerHTML = "";
  });

  it("把临时 <a> 挂到 body，带上 href/download 并点击", () => {
    const { downloadBlob } = useDownload();

    downloadBlob(new Blob(["hi"], { type: "text/plain" }), "report.pdf", "done");

    const anchor = document.body.querySelector("a");
    expect(anchor).not.toBeNull();
    expect(anchor!.getAttribute("href")).toBe("blob:mock-url");
    expect(anchor!.getAttribute("download")).toBe("report.pdf");
    expect(clickSpy).toHaveBeenCalledTimes(1);
  });

  it("不在点击的同一个任务里 revoke 对象 URL", () => {
    const { downloadBlob } = useDownload();

    downloadBlob(new Blob(["hi"]), "report.pdf", "done");

    expect(revokeSpy).not.toHaveBeenCalled();
  });

  it("下载启动之后回收对象 URL 并摘掉临时 <a>", () => {
    const { downloadBlob } = useDownload();

    downloadBlob(new Blob(["hi"]), "report.pdf", "done");
    vi.advanceTimersByTime(100);

    expect(revokeSpy).toHaveBeenCalledTimes(1);
    expect(revokeSpy).toHaveBeenCalledWith("blob:mock-url");
    expect(document.body.querySelector("a")).toBeNull();
  });

  it("传入成功文案时弹一条成功 toast", () => {
    const { downloadBlob } = useDownload();

    downloadBlob(new Blob(["hi"]), "report.pdf", "已保存");

    expect(toastAdd).toHaveBeenCalledWith({ title: "已保存", color: "success" });
  });

  it("不传成功文案时完全不碰 toast", () => {
    const { downloadBlob } = useDownload();

    downloadBlob(new Blob(["hi"]), "report.pdf");

    expect(toastAdd).not.toHaveBeenCalled();
  });
});
