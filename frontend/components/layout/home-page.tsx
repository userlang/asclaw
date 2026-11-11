"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { ArrowUpRight } from "@phosphor-icons/react"
import Link from "next/link"

/** 五域画卷：home/ 六张国风插画中的五张单域图（仙境汇总图用作首屏背景） */
const REALMS = [
  { src: "/home/kunlun.jpg", name: "昆仑山脉", motto: "万山之祖，云海宫阙" },
  { src: "/home/penglai.jpg", name: "蓬莱仙境", motto: "沧溟浮岛，紫气东来" },
  { src: "/home/shennongjia.jpg", name: "神农架林区", motto: "千峰叠翠，百川归谷" },
  { src: "/home/qinling.jpg", name: "秦岭山脉", motto: "红叶燃山，霜华点雪" },
  { src: "/home/changbai.jpg", name: "长白山脉", motto: "天池如镜，映彻冰峰" },
]

export default function HomePage() {
  return (
    <div className="@container/main relative flex min-h-screen flex-col">
      {/* Hero — 仙境汇总全景作背景，缓慢推近；中央柔光罩托起文字 */}
      <section className="relative flex min-h-dvh items-center justify-center overflow-hidden px-4 pt-24 pb-16 sm:px-6 lg:px-8">
        <div className="absolute inset-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/home/panorama.jpg"
            alt=""
            className="animate-hero-zoom h-full w-full object-cover"
          />
          {/* 顶部：给固定导航留出过渡带 */}
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "linear-gradient(to bottom, color-mix(in oklab, var(--background) 90%, transparent) 0%, transparent 20%)",
            }}
          />
          {/* 中央柔光罩：托起标题与 CTA */}
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse 64% 58% at 50% 52%, color-mix(in oklab, var(--background) 88%, transparent) 0%, color-mix(in oklab, var(--background) 45%, transparent) 55%, transparent 80%)",
            }}
          />
          {/* 底部：融入下一节 */}
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "linear-gradient(to top, var(--background) 0%, color-mix(in oklab, var(--background) 60%, transparent) 10%, transparent 36%)",
            }}
          />
        </div>

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          {/* Top badge */}
          <p className="animate-fade-in-up mb-6 text-muted-foreground text-sm">智能体将改变世界</p>

          {/* Title */}
          <p className="animate-fade-in-up font-xian mb-8 text-4xl font-medium tracking-wide text-foreground drop-shadow-sm sm:text-5xl [animation-delay:100ms]">
            赋予 AsClaw 无限能力
          </p>

          {/* 企业入驻 CTA */}
          <div className="animate-fade-in-up flex flex-col items-center gap-4 [animation-delay:150ms]">
            <Link
              href="/enterprise/apply"
              className="group inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-[length:200%_auto] px-8 py-4 text-xl font-bold text-white shadow-lg transition-all hover:bg-right hover:shadow-xl"
            >
              申请入驻平台
              <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
            <p className="text-muted-foreground text-sm">
              提交企业资质，管理员审核通过后即可使用企业账号登录平台
            </p>
            <Link
              href="/enterprise/login"
              className="text-muted-foreground hover:text-primary text-sm underline-offset-4 hover:underline"
            >
              已有企业账号？前往登录
            </Link>
          </div>
        </div>
      </section>

      {/* 五域画卷 — 悬停展开的单域长卷 */}
      <section id="realms" className="relative mx-auto w-full max-w-7xl scroll-mt-14 px-4 pb-16 sm:px-6 lg:px-8">
        <div className="mb-10 text-center">
          <h2 className="font-xian text-3xl font-medium tracking-wide text-foreground">
            五域画卷
          </h2>
          <p className="text-muted-foreground mt-2 text-sm">
            昆仑之巅 · 蓬莱之屿 · 神农之林 · 秦岭之秋 · 长白之雪
          </p>
        </div>

        <div className="flex flex-col gap-3 md:h-[68vh] md:flex-row">
          {REALMS.map((realm) => (
            <figure
              key={realm.name}
              className="group relative h-60 w-full overflow-hidden rounded-2xl ring-1 ring-black/10 md:h-auto md:flex-1 md:transition-[flex] md:duration-500 md:ease-out md:hover:flex-[2.8]"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={realm.src}
                alt={realm.name}
                loading="lazy"
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
              />
              {/* 底部压暗，保证题字可读 */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/5 to-transparent" />

              {/* 竖排题字：桌面端折叠态的域名牌（白底深字，呼应地图上的题字牌），展开后让位给横排详情 */}
              <span className="font-xian absolute top-5 right-5 hidden rounded-md border border-stone-200/80 bg-white/85 px-1.5 py-3 text-lg tracking-[0.35em] text-stone-700 shadow-sm backdrop-blur-sm transition-opacity duration-300 [writing-mode:vertical-rl] md:block md:group-hover:opacity-0">
                {realm.name}
              </span>

              {/* 详情：移动端常显；桌面端悬停展开时浮现 */}
              <figcaption className="absolute inset-x-0 bottom-0 p-6">
                <p className="font-xian text-2xl tracking-wide text-white drop-shadow-md transition-all duration-500 md:translate-y-3 md:opacity-0 md:group-hover:translate-y-0 md:group-hover:opacity-100">
                  {realm.name}
                </p>
                <p className="mt-1 text-sm text-white/85 transition-opacity duration-500 md:opacity-0 md:delay-100 md:group-hover:opacity-100">
                  {realm.motto}
                </p>
              </figcaption>
            </figure>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Link
            href="/mcp"
            className="group inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/60 px-6 py-3 text-sm font-medium text-foreground backdrop-blur-sm transition-colors hover:border-primary/50 hover:text-primary"
          >
            探索全部 MCP
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>
      </section>
    </div>
  )
}
