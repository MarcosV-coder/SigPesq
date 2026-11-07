import { NavLink } from "react-router-dom";
import { User } from "lucide-react";

const links = [
    { to: "/projetos", label: "Projetos" },
    { to: "/participantes", label: "Participantes" },
    { to: "/financiamentos", label: "Financiamentos" },
    { to: "/producoes", label: "Produções" },
    { to: "/vinculos", label: "Vínculos" },
];

export default function Navbar() {
    return (
        <header className="sticky top-0 z-10 border-b border-slate-100 bg-surface/90 backdrop-blur">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
                <div className="flex items-center gap-6">
                    <NavLink to="/" className="text-lg font-bold tracking-tight text-navy">
                        SIGPesq
                    </NavLink>
                    <span className="hidden h-4 w-px bg-slate-300 md:block" />
                    <nav className="hidden items-center gap-8 md:flex">
                        {links.map((l) => (
                            <NavLink
                                key={l.to}
                                to={l.to}
                                className={({ isActive }) =>
                                    `text-sm transition-colors hover:text-navy ${isActive ? "font-semibold text-navy" : "text-slate-600"
                                    }`
                                }
                            >
                                {l.label}
                            </NavLink>
                        ))}
                    </nav>
                </div>

                <div className="flex items-center gap-3">
                    <div className="hidden text-right text-xs leading-tight sm:block">
                        <p className="font-semibold text-navy">Coordenador</p>
                        <p className="text-slate-600">Pró-Reitoria de Pesquisa</p>
                    </div>
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-navy text-white">
                        <User size={16} />
                    </div>
                </div>
            </div>
        </header>
    );
}