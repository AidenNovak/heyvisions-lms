/**
 * 课程目录网格的列数规则。
 *
 * 起因：网格类名把列数写死成 `grid-cols-1 sm:grid-cols-2 md:grid-cols-3
 * lg:grid-cols-4`，与课程数量无关。站上只有 1 门课时（本仓库当前就是这种情形），
 * 1440px 视口下是「4 列 × 328px，卡片只占 1 列」，网格内空出 76% —— 页面看起来
 * 像内容没加载出来，而不是像「这里就只有一门课」。
 *
 * 规则与静态站 yettodawn.com 的课程目录一致
 * （`example/src/courses.css` 的 `.catalog-grid.count-1`）：
 *
 *   .catalog-grid.count-1{grid-template-columns:minmax(0,560px)}
 *
 * 平台与站点是同一产品的两个面，稀疏目录的样子不该两边各定一套。
 *
 * 为什么不是 `auto-fit` / `auto-fill`：那类写法会让**唯一的**一张卡片
 * 在 `1fr` 下被拉伸到整行（1361px），把「左侧留白」换成「卡片过宽」，
 * 并不是想要的收敛。按数量给列，宽度才是确定的。
 */

/** 单课程时的列宽上限，取自静态站 `.catalog-grid.count-1` 的 560px（= 35rem）。 */
const SINGLE_CARD_MAX_WIDTH_CLASS = 'sm:max-w-[35rem]' // 35rem = 560px

/**
 * 给课程网格返回 Tailwind 类名。
 *
 * 移动端一律单列（沿用原行为）；从 `sm` 起才按数量决定列数。
 *
 * 注意：类名必须写成完整字面量。Tailwind 是**扫描源码文本**收集候选类的，
 * 用模板串拼 `sm:max-w-[${x}]` 它扫不到，那条规则不会生成，界面上就是没生效。
 *
 * @param count 本次实际渲染的卡片数。传 **0** 时返回原 4 列写法 ——
 *   空状态块用的是 `col-span-full`，需要整行铺满，收窄反而会让空状态变窄。
 */
export function catalogGridClass(count: number): string {
  const base = 'grid gap-4 grid-cols-1'

  if (count === 0) return `${base} sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4`
  if (count === 1) return `${base} ${SINGLE_CARD_MAX_WIDTH_CLASS}`
  if (count === 2) return `${base} sm:grid-cols-2`
  if (count === 3) return `${base} sm:grid-cols-2 md:grid-cols-3`
  return `${base} sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4`
}
