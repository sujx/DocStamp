/**
 * Tests for useApiError composable.
 *
 * extractError 是各工具组件共用的错误提取入口，错误体有 JSON 信封、纯文本、
 * Blob 和对象四种到达形态，这里逐条钉住各分支的取值优先级。
 */
import { describe, it, expect } from "vitest";
import { useApiError } from "../useApiError";

describe("useApiError", () => {
  const { extractError } = useApiError();

  it("JSON 信封错误体取 error 字段", async () => {
    const e = { response: { data: JSON.stringify({ error: "boom" }) } };
    expect(await extractError(e)).toBe("boom");
  });

  it("纯文本错误体原样返回", async () => {
    const e = { response: { data: "plain failure" } };
    expect(await extractError(e)).toBe("plain failure");
  });

  it("Blob 错误体先 text() 再取 msg 字段", async () => {
    const e = { response: { data: new Blob([JSON.stringify({ msg: "blob boom" })]) } };
    expect(await extractError(e)).toBe("blob boom");
  });

  it("对象错误体取 message 字段", async () => {
    const e = { response: { data: { message: "object boom" } } };
    expect(await extractError(e)).toBe("object boom");
  });

  it("HTML 错误页不作为消息返回，回落到 fallback", async () => {
    const e = { response: { data: "<html>502 Bad Gateway</html>" } };
    expect(await extractError(e, "fallback msg")).toBe("fallback msg");
  });

  it("无响应体时用 Error.message 顶替 fallback", async () => {
    expect(await extractError(new Error("network down"), "fallback msg")).toBe("network down");
  });
});
