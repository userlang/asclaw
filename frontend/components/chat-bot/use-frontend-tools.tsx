"use client"

import { useRenderTool } from "@copilotkitnext/react"
import { Check, LoaderCircle } from "lucide-react"

/**
 * Register all frontend tools for the chat bot.
 * Call this hook once inside the CopilotKit provider.
 */
export function useFrontendTools() {
  // ----------------------------------
  // 🔧 Default Tool Rendering
  // Renders backend tool call status in the chat
  // ----------------------------------
  useRenderTool({
    name: "*",
    render: ({ name, status, args }: { name: string; status: string; args?: unknown }) => {
      // 截断展示参数，避免长参数撑爆界面
      const argsText = (() => {
        try {
          const text = JSON.stringify(args)
          return text && text !== "{}" ? text : ""
        } catch {
          return ""
        }
      })().slice(0, 120)
      const isDone = status === "complete"
      return (
        <div className="border-border/60 bg-muted/40 mt-2 rounded-lg border px-3 py-2 text-sm">
          <div className="flex items-center gap-2">
            {isDone ? (
              <Check className="text-primary h-4 w-4 shrink-0" />
            ) : (
              <LoaderCircle className="text-muted-foreground h-4 w-4 shrink-0 animate-spin" />
            )}
            <span className="font-medium">{name}</span>
            <span className="text-muted-foreground text-xs">
              {isDone ? "调用完成" : "正在调用…"}
            </span>
          </div>
          {argsText && (
            <p className="text-muted-foreground mt-1 break-all font-mono text-xs">
              {argsText}
            </p>
          )}
        </div>
      )
    },
  })

  // ----------------------------------
  // 🪁 Frontend Tools
  // Add new useFrontendTool / useHumanInTheLoop calls below
  // ----------------------------------
}
