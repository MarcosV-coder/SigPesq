import ModuleCard from "../components/ModuleCard";
import { modules } from "../data/modules";

export default function Home() {
    return (
        <main className="mx-auto max-w-7xl px-4 pb-16 pt-10 sm:px-8">
            <section>
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                    Bem-vindo ao SIGPesq
                </h1>
                <p className="mt-2 text-slate-600">
                    Sistema Integrado de Gestão de Pesquisa.
                    <br />
                    Selecione um módulo abaixo para cadastrar, editar ou gerenciar dados
                    da sua produção científica e equipe.
                </p>
            </section>

            <section className="mt-10">
                <div className="flex items-end justify-between gap-4">
                    <h2 className="text-xl font-semibold">Módulos Operacionais</h2>
                    <span className="hidden text-xs text-slate-600 sm:block">
                        Selecione uma área para gerenciamento completo
                    </span>
                </div>

                <div className="mt-5 flex flex-col gap-6">
                    {modules.map((m) => (
                        <ModuleCard key={m.id} module={m} />
                    ))}
                </div>
            </section>
        </main>
    );
}