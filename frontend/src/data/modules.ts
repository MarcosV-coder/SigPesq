import { BookOpen, Banknote, Folder, Link2, Users } from "lucide-react";
import type { ModuleItem } from "../types/module";

export const modules: ModuleItem[] = [
    {
        id: "projetos",
        title: "Projetos de Pesquisa",
        description:
            "Cadastro direto de projetos, cronograma, objetivos e vinculação rápida de participantes e bolsistas.",
        badge: "12 Projetos Ativos",
        status: "2 em renovação",
        to: "/projetos",
        cta: "Acessar Projetos",
        icon: Folder,
        tone: "dark",
    },
    {
        id: "participantes",
        title: "Participantes",
        description:
            "Gestão direta de pesquisadores, docentes, discentes bolsistas e voluntários, com controle de vigência e CPF.",
        badge: "48 Pesquisadores",
        status: "100% validados",
        to: "/participantes",
        cta: "Acessar Participantes",
        icon: Users,
        tone: "light",
    },
    {
        id: "financiamentos",
        title: "Financiamentos & Bolsas",
        description:
            "Controle financeiro de editais, agências de fomento (CNPq, CAPES, FAPES), convênios e valores aplicados.",
        badge: "R$ 1.450.000,00",
        status: "4 editais ativos",
        to: "/financiamentos",
        cta: "Acessar Financiamentos",
        icon: Banknote,
        tone: "dark",
    },
    {
        id: "producoes",
        title: "Produções Científicas",
        description:
            "Registro ágil de artigos em periódicos, patentes, softwares registrados e relatórios técnicos com validação de DOI.",
        badge: "35 Validadas",
        status: "Sincronizado Lattes",
        to: "/producoes",
        cta: "Acessar Produções",
        icon: BookOpen,
        tone: "light",
    },
    {
        id: "vinculos",
        title: "Vínculos dos participantes",
        description: "Gestão de vínculo entre participantes e projetos.",
        badge: "10 Vínculos",
        status: "Sincronizado Bioinformática",
        to: "/vinculos",
        cta: "Acessar Vínculos",
        icon: Link2,
        tone: "light",
    },
];