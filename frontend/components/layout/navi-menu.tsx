"use client";

import { useUser } from "@/components/providers/user-provider";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { List } from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";


export function NaviMenu() {
    const pathname = usePathname()
    const {user, isJwtAuthenticated} = useUser()
    const isLoggedIn = !!user || isJwtAuthenticated
    const [open, setOpen] = useState(false)

    const linkClass =
        "bg-gradient-to-r from-muted-foreground/80 to-muted-foreground/50 bg-clip-text text-base text-transparent transition-all hover:from-indigo-500 hover:via-purple-500 hover:to-fuchsia-500"
    const activeLinkClass =
        "relative bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 bg-clip-text text-base text-transparent after:absolute after:inset-x-0 after:-bottom-1 after:h-0.5 after:rounded-full after:bg-gradient-to-r after:from-indigo-500 after:via-purple-500 after:to-fuchsia-500 after:content-['']"
    const mobileLinkClass =
        "block bg-gradient-to-r from-foreground/80 to-foreground/50 bg-clip-text py-3 text-lg text-transparent transition-all hover:from-indigo-500 hover:via-purple-500 hover:to-fuchsia-500"
    const mobileActiveLinkClass =
        "relative block bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 bg-clip-text py-3 text-lg text-transparent after:absolute after:inset-x-0 after:bottom-1.5 after:h-0.5 after:rounded-full after:bg-gradient-to-r after:from-indigo-500 after:via-purple-500 after:to-fuchsia-500 after:content-['']"

    const isActive = (href: string) => {
        if (href === "/") {
            return pathname === "/"
        }
        return pathname.startsWith(href)
    }

    return (
      <>
        {/* Desktop Navigation */}
        <div className="hidden items-center gap-6 text-xl font-medium md:flex">
          <Link
            href="/chat"
            className={isActive("/chat") ? activeLinkClass : linkClass}
          >
            Chat
          </Link>
          <Link
            href="/mcp"
            className={isActive("/mcp") ? activeLinkClass : linkClass}
          >
            MCP
          </Link>
          <Link
            href="/skills"
            className={isActive("/skills") ? activeLinkClass : linkClass}
          >
            Skill
          </Link>
          {isLoggedIn && (user?.is_staff || user?.is_superuser) && (
            <Link
              href="/user/admin/review"
              className={
                isActive("/user/admin/review") ? activeLinkClass : linkClass
              }
            >
              Review
            </Link>
          )}
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <button className="text-muted-foreground hover:text-foreground p-2">
                <List size={24} />
              </button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[250px] pt-12">
              <nav className="flex flex-col">
                <Link
                  href="/chat"
                  className={
                    isActive("/chat")
                      ? mobileActiveLinkClass
                      : mobileLinkClass
                  }
                  onClick={() => setOpen(false)}
                >
                  Chat
                </Link>
                <Link
                  href="/mcp"
                  className={
                    isActive("/mcp") ? mobileActiveLinkClass : mobileLinkClass
                  }
                  onClick={() => setOpen(false)}
                >
                  MCP
                </Link>
                <Link
                  href="/skills"
                  className={
                    isActive("/skills")
                      ? mobileActiveLinkClass
                      : mobileLinkClass
                  }
                  onClick={() => setOpen(false)}
                >
                  Skill
                </Link>
                {isLoggedIn && (user?.is_staff || user?.is_superuser) && (
                  <Link
                    href="/user/admin/review"
                    className={
                      isActive("/user/admin/review")
                        ? mobileActiveLinkClass
                        : mobileLinkClass
                    }
                    onClick={() => setOpen(false)}
                  >
                    Review
                  </Link>
                )}
                {!isLoggedIn && (
                  <Link
                    href="/enterprise/login"
                    onClick={() => setOpen(false)}
                    className="block bg-gradient-to-r from-foreground/80 to-foreground/50 bg-clip-text py-3 text-left text-lg text-transparent transition-all hover:from-indigo-500 hover:via-purple-500 hover:to-fuchsia-500"
                  >
                    登录
                  </Link>
                )}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </>
    )
}
