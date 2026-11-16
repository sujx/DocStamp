/**
 * 名单输入解析（10.3「标注出席人单位、姓名」）：一行一人，「单位 姓名」。
 * 中文单位名里可以有空格，姓名一般不含空格，所以按最后一个空白切。
 */
import { describe, it, expect } from "vitest";
import { parseRoster } from "../roster";

describe("parseRoster", () => {
  it("把「单位 姓名」拆成一对字段", () => {
    expect(parseRoster("信息技术中心 张三")).toEqual([{ org: "信息技术中心", name: "张三" }]);
  });

  it("单位名里的空格不拆，只按最后一个空白切", () => {
    expect(parseRoster("卫星应用中心 总体室 李四")).toEqual([
      { org: "卫星应用中心 总体室", name: "李四" },
    ]);
  });

  it("没有空白时整行是姓名", () => {
    expect(parseRoster("王五")).toEqual([{ org: "", name: "王五" }]);
  });

  it("按行拆多人，空行与首尾空白忽略", () => {
    expect(parseRoster("信息技术中心 张三\n\n  综合处 李四  \n")).toEqual([
      { org: "信息技术中心", name: "张三" },
      { org: "综合处", name: "李四" },
    ]);
  });

  it("空文本产出空数组（该块整体不排）", () => {
    expect(parseRoster("")).toEqual([]);
    expect(parseRoster("  \n \n")).toEqual([]);
  });
});
