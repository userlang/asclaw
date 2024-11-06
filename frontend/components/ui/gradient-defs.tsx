const INDIGO = "#6366f1"
const PURPLE = "#a855f7"
const FUCHSIA = "#d946ef"

/**
 * 全局 SVG 渐变定义，供 .icon-gradient / .icon-gradient-fill 通过
 * stroke/fill: url(#asclaw-icon-gradient) 引用，让线性 SVG 图标呈现品牌渐变色。
 * 在根布局挂载一次即可，全站生效。
 */
export function GradientDefs() {
  return (
    <svg
      width="0"
      height="0"
      className="absolute"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id="asclaw-icon-gradient" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={INDIGO} />
          <stop offset="50%" stopColor={PURPLE} />
          <stop offset="100%" stopColor={FUCHSIA} />
        </linearGradient>
      </defs>
    </svg>
  )
}
