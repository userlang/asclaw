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

          {/* Social icons */}
          <div className="flex items-center gap-3">
            <a
              href="https://x.com/tomeclaw"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1.5 transition-colors"
              aria-label="Twitter"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M13.6823 10.6218L20.2391 3H18.6854L12.9921 9.61788L8.44486 3H3.2002L10.0765 13.0074L3.2002 21H4.75404L10.7663 14.0113L15.5549 21H20.7996L13.6819 10.6218H13.6823ZM11.5541 13.0956L10.8574 12.0991L5.31391 4.16971H7.70053L12.1742 10.5689L12.8709 11.5655L18.6861 19.8835H16.2995L11.5541 13.096V13.0956Z" />
              </svg>
            </a>
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
