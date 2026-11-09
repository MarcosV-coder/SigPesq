-- Banco NOVO: execute uma vez. Para banco original existente, use migracao_pdf.sql.
CREATE DATABASE IF NOT EXISTS sigpesq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sigpesq;
CREATE TABLE projeto (
    codigo_projeto INT UNSIGNED PRIMARY KEY,
    titulo VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    situacao ENUM('em_andamento', 'concluido', 'cancelado') NOT NULL,
    data_inicio DATE NOT NULL,
    data_termino DATE,
    
    CONSTRAINT chk_projeto_datas CHECK (data_termino IS NULL OR data_termino >= data_inicio)
);

CREATE TABLE participante (
    cpf CHAR(11) PRIMARY KEY
        CHECK (cpf REGEXP '^[0-9]{11}$'),
    nome VARCHAR(100) NOT NULL 
        CHECK (nome REGEXP '^[a-zA-ZÀ-ÿ ]+$'),
    email VARCHAR(100) NOT NULL UNIQUE
        CHECK (email LIKE '%@%'),
    tipo_participante ENUM('discente','docente','tec_adm') NOT NULL
);

CREATE TABLE financiamento (
    codigo_financiamento INT UNSIGNED PRIMARY KEY,
    agencia_financiadora ENUM('capes', 'fapes', 'cnpq', 'finep') NOT NULL,
    tipo_fomento ENUM('bolsa', 'auxilio', 'convenio') NOT NULL,
    valor_total DECIMAL(20,2) NOT NULL CHECK (valor_total > 0),
    data_inicio DATE NOT NULL,
    data_termino DATE NOT NULL,

    CONSTRAINT check_data CHECK(data_inicio <= data_termino)
);

CREATE TABLE producao_cientifica (
    codigo_projeto INT UNSIGNED NOT NULL,
    codigo_prod INT UNSIGNED NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    tipo_prod ENUM('artigo', 'cap_livro', 'software', 'relatorio_tecnico', 'patente') NOT NULL,
    meio_divulgacao ENUM('revista', 'congresso', 'repositorio') NOT NULL,
    veiculo VARCHAR(200),
    identificador VARCHAR(200),
    ano_publicacao SMALLINT UNSIGNED NOT NULL CHECK (ano_publicacao BETWEEN 1000 AND 9999),

    PRIMARY KEY (codigo_projeto, codigo_prod),
    FOREIGN KEY (codigo_projeto) REFERENCES projeto(codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE vinculo_projeto_participante (
    codigo_projeto INT UNSIGNED NOT NULL,
    cpf CHAR(11) NOT NULL,
    funcao_desempenhada ENUM ('colaborador', 'bolsista', 'coordenador'),
    data_entrada DATE,
    data_saida DATE,
    carga_semanal SMALLINT UNSIGNED NOT NULL DEFAULT 20 CHECK (carga_semanal BETWEEN 1 AND 168),
    fomento VARCHAR(100),
    plano_trabalho VARCHAR(2000),

    PRIMARY KEY (codigo_projeto, cpf),
    FOREIGN KEY (codigo_projeto) REFERENCES projeto(codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (cpf) REFERENCES participante(cpf)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT chk_vinculo_part_datas CHECK (data_saida IS NULL OR data_saida >= data_entrada)
);

CREATE TABLE vinculo_projeto_financiamento (
    codigo_projeto INT UNSIGNED NOT NULL,
    codigo_financiamento INT UNSIGNED NOT NULL,
    valor_destinado DECIMAL(20,2) NOT NULL
         CHECK (valor_destinado > 0),
    
    PRIMARY KEY (codigo_projeto, codigo_financiamento),
    FOREIGN KEY (codigo_projeto) REFERENCES projeto(codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (codigo_financiamento) REFERENCES financiamento(codigo_financiamento)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE autoria_producao (
    codigo_projeto INT UNSIGNED NOT NULL,
    codigo_prod INT UNSIGNED NOT NULL,
    cpf CHAR(11) NOT NULL,
    PRIMARY KEY (codigo_projeto, codigo_prod, cpf),
    FOREIGN KEY (codigo_projeto, codigo_prod)
        REFERENCES producao_cientifica(codigo_projeto, codigo_prod)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (codigo_projeto, cpf)
        REFERENCES vinculo_projeto_participante(codigo_projeto, cpf)
        ON DELETE CASCADE ON UPDATE CASCADE
);
