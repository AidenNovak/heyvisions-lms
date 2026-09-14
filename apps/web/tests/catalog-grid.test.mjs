import { describe, expect, test } from "bun:test";

import { catalogGridClass } from "../lib/catalog-grid.ts";

/** 类名里出现的列数声明，按断点取出，便于断言「从哪个断点起是几列」。 */
function columnsByBreakpoint(className) {
  const out = {};
  for (const part of className.split(/\s+/)) {
    const m = part.match(/^(sm|md|lg|xl)?:?grid-cols-(\d+)$/);
    if (m) out[m[1] ?? "base"] = Number(m[2]);
  }
  return out;
}

describe("catalogGridClass", () => {
  test("移动端始终单列，不随数量变化", () => {
    for (const count of [0, 1, 2, 3, 4, 9]) {
      expect(columnsByBreakpoint(catalogGridClass(count)).base).toBe(1);
    }
  });

  test("只有 1 门课时收成一列，并给列宽上限（对齐静态站 560px）", () => {
    const cls = catalogGridClass(1);
    // 关键：sm 及以上不能再声明多列，否则又变成「4 列里放一张卡」。
    const cols = columnsByBreakpoint(cls);
    expect(cols.sm).toBeUndefined();
    expect(cols.md).toBeUndefined();
    expect(cols.lg).toBeUndefined();
    expect(cls).toContain("sm:max-w-[35rem]"); // 35rem = 560px
  });

  test("2、3 门课按数量给列", () => {
    expect(columnsByBreakpoint(catalogGridClass(2)).sm).toBe(2);
    expect(columnsByBreakpoint(catalogGridClass(2)).md).toBeUndefined();

    const three = columnsByBreakpoint(catalogGridClass(3));
    expect(three.sm).toBe(2);
    expect(three.md).toBe(3);
    expect(three.lg).toBeUndefined();
  });

  test("4 门及以上保持原有响应式列数（回归项）", () => {
    for (const count of [4, 12]) {
      const cols = columnsByBreakpoint(catalogGridClass(count));
      expect(cols).toEqual({ base: 1, sm: 2, md: 3, lg: 4 });
    }
  });

  test("0 门课保持铺满：空状态用 col-span-full，不能收窄", () => {
    const cls = catalogGridClass(0);
    expect(cls).not.toContain("max-w-");
    expect(columnsByBreakpoint(cls)).toEqual({ base: 1, sm: 2, md: 3, lg: 4 });
  });

  test("不产生 Tailwind 扫不到的动态类名（不得出现模板占位）", () => {
    for (const count of [0, 1, 2, 3, 4]) {
      expect(catalogGridClass(count)).not.toContain("${");
    }
  });
});
