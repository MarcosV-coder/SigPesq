import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { ModuleItem } from "../types/module";

export default function ModuleCard({ module: m }: { module: ModuleItem }) {
    const Icon = m.icon;

    return (
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            {/* topo: ícone + badge */}
            <div className="flex items-start justify-between gap-3">
                <div
                    className={`flex h-12 w-12 items-center justify-center rounded-lg text-white ${m.tone === "dark" ? "bg-brand" : "bg-brand-alt"
                        }`}
                >
                    <Icon size={22} />
                </div>
                <span className="rounded-full bg-chip px-3 py-1 text-xs font-medium text-slate-700">
                    {m.badge}
                </span>
            </div>

            {/* conteúdo */}
            <h3 className="mt-4 text-base font-semibold text-navy">{m.title}</h3>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">{m.description}</p>

            {/* rodapé: status + botão */}
            <div className="mt-8 flex items-center justify-between gap-4 border-t border-slate-100 pt-4">
                <span className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-brand-alt" />
                    {m.status}
                </span>

                <Link
                    to={m.to}
                    className="flex items-center gap-3 rounded-lg bg-brand px-5 py-3 text-center text-sm font-medium leading-tight text-white transition hover:bg-navy"
                >
                    {m.cta}
                    <ArrowRight size={16} />
                </Link>
            </div>
        </article>
    );
}