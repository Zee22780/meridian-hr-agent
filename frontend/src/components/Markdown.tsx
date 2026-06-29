import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownProps {
  children: string
}

/**
 * Renders agent message markdown (headings, bold, lists, tables, rules)
 * with styling tuned for the chat bubble. Tailwind v4 here has no typography
 * plugin, so elements are mapped explicitly.
 */
export function Markdown({ children }: MarkdownProps) {
  return (
    <div className="text-sm text-slate-700 leading-relaxed space-y-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-base font-bold text-slate-900 mt-3 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-bold text-slate-900 mt-3 first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-900 mt-3 first:mt-0">{children}</h3>,
          p: ({ children }) => <p className="whitespace-pre-wrap">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => <ul className="list-disc pl-5 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="marker:text-slate-400">{children}</li>,
          a: ({ href, children }) => (
            <a href={href} className="text-indigo-600 underline hover:text-indigo-700" target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
          hr: () => <hr className="border-slate-200 my-3" />,
          code: ({ children }) => (
            <code className="px-1 py-0.5 rounded bg-slate-100 text-slate-800 text-xs font-mono">{children}</code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-slate-200 pl-3 text-slate-600 italic">{children}</blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="border-b border-slate-200 px-2 py-1 font-semibold text-slate-900">{children}</th>,
          td: ({ children }) => <td className="border-b border-slate-100 px-2 py-1 align-top">{children}</td>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
