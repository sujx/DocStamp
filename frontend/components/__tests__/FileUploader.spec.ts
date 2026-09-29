/**
 * FileUploader 尺寸闸门契约：
 * - maxSize prop 单位是 MB（与后端 file_security.MAX_FILE_SIZE=100MB 对齐），
 *   历史 bug 是拿 f.size（字节）直接和 maxSize 比，导致 >100 字节的文件全被挡下。
 * - 被拒文件必须 emit("file-rejected", { name, size, maxSizeMb })，
 *   调用点靠它给用户反馈（历史 bug 是无人监听，静默失效）。
 * - maxSize=0（默认）表示不限制。
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import FileUploader from "../FileUploader.vue";

const stubs = {
  UIcon: true,
  UButton: true,
};

function makeFile(name: string, size: number): File {
  const f = new File([], name);
  // happy-dom 的 File 构造器不接受 size 覆盖，测试里显式钉住字节数
  Object.defineProperty(f, "size", { value: size });
  return f;
}

function mountUploader(maxSize?: number) {
  return mount(FileUploader, {
    props: maxSize === undefined ? {} : { maxSize },
    global: { stubs, mocks: { $t: (k: string) => k } },
  });
}

describe("FileUploader maxSize(MB) 闸门", () => {
  it("maxSize=100 时 101MB 文件被拒并 emit 结构化 payload", async () => {
    const w = mountUploader(100);
    const big = makeFile("big.pdf", 101 * 1048576);

    (w.vm as unknown as { setFile: (f: File) => void }).setFile(big);

    const rejected = w.emitted("file-rejected");
    expect(rejected).toHaveLength(1);
    expect(rejected![0][0]).toEqual({ name: "big.pdf", size: big.size, maxSizeMb: 100 });
    expect(w.emitted("file-selected")).toBeUndefined();
  });

  it("maxSize=100 时恰为 100MB 的文件放行（边界含等号）", () => {
    const w = mountUploader(100);
    const edge = makeFile("edge.pdf", 100 * 1048576);

    (w.vm as unknown as { setFile: (f: File) => void }).setFile(edge);

    expect(w.emitted("file-rejected")).toBeUndefined();
    expect(w.emitted("file-selected")).toHaveLength(1);
  });

  it("maxSize 未传（0）时任意大小都放行", () => {
    const w = mountUploader();
    const huge = makeFile("huge.pdf", 3 * 1024 * 1048576);

    (w.vm as unknown as { setFile: (f: File) => void }).setFile(huge);

    expect(w.emitted("file-rejected")).toBeUndefined();
    expect(w.emitted("file-selected")).toHaveLength(1);
  });

  it("正常小文件 emit file-selected 且不 emit file-rejected", () => {
    const w = mountUploader(100);
    const small = makeFile("ok.pdf", 1024);

    (w.vm as unknown as { setFile: (f: File) => void }).setFile(small);

    expect(w.emitted("file-rejected")).toBeUndefined();
    expect(w.emitted("file-selected")).toHaveLength(1);
  });
});
