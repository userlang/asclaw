// 作者：langjunnan
// 开发时间：2025年7月23日

"use client";

import { APP_NAME } from "@/lib/config";
import Link from "next/link";


export default function Footer() {
  return (
    <footer className="border-border/50 border-t">
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Main row */}
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          {/* Brand */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-foreground text-sm font-semibold">
                {APP_NAME}
              </span>
            </Link>
            <span className="text-muted-foreground hidden text-sm sm:inline">
              Build Agents that think and act
            </span>
          </div>
        </div>

        {/* Bottom row */}
        <div className="border-border/50 text-muted-foreground mt-6 flex flex-col items-center justify-between gap-3 border-t pt-6 text-xs sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} {APP_NAME}. All rights reserved.
          </p>
          <div className="flex gap-4">
            <Link
              href="/privacy"
              className="hover:text-foreground transition-colors"
            >
              隐私政策
            </Link>
            <Link
              href="/terms"
              className="hover:text-foreground transition-colors"
            >
              服务条款
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
