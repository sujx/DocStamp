/**
 * 下载名以服务端 Content-Disposition 为准（「〈会议名称〉纪要.docx」的拼法只有一份）。
 * RFC 6266：send_file 会同时给 ASCII 兜底的 filename= 与 RFC 5987 的 filename*=，
 * 中文名只在后者里，所以必须优先取 filename*=。
 */
import { describe, it, expect } from "vitest";
import { filenameFromDisposition } from "../contentDisposition";

const FALLBACK = "Meeting Minutes.docx";

describe("filenameFromDisposition", () => {
  it("取 Flask 实发的双参数头里的 UTF-8 名字", () => {
    const header =
      "attachment; filename=.docx; filename*=UTF-8''%E4%BF%A1%E6%81%AF%E6%8A%80%E6%9C%AF%E4%B8%AD%E5%BF%83%E4%BE%8B%E4%BC%9A%E7%BA%AA%E8%A6%81.docx";
    expect(filenameFromDisposition(header, FALLBACK)).toBe("信息技术中心例会纪要.docx");
  });

  it("只有 ASCII 名字时用它", () => {
    expect(filenameFromDisposition('attachment; filename="plan.docx"', FALLBACK)).toBe("plan.docx");
    expect(filenameFromDisposition("attachment; filename=plan.docx", FALLBACK)).toBe("plan.docx");
  });

  it("没有头或没有文件名时回落到传入的名字", () => {
    expect(filenameFromDisposition(undefined, FALLBACK)).toBe(FALLBACK);
    expect(filenameFromDisposition("inline", FALLBACK)).toBe(FALLBACK);
  });
});
