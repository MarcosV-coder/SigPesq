DROP DATABASE IF EXISTS sigpesq;
CREATE DATABASE IF NOT EXISTS sigpesq
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sigpesq;

CREATE TABLE projeto (
    codigo_projeto INT UNSIGNED PRIMARY KEY,
    titulo VARCHAR(100) NOT NULL,
    descricao VARCHAR(300) NOT NULL,
    situacao INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_termino DATE
);

CREATE TABLE participante (
    cpf CHAR(11) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    tipo_participante INT NOT NULL,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE financiamento (
    codigo_financiamento INT UNSIGNED PRIMARY KEY,
    agencia_financiadora INT NOT NULL,
    tipo_fomento INT NOT NULL,
    valor_total DECIMAL(20,2) NOT NULL,
    data_inicio DATE NOT NULL,
    data_termino DATE NOT NULL
);

CREATE TABLE producao_cientifica (
    codigo_projeto INT UNSIGNED NOT NULL,
    codigo_prod INT UNSIGNED NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    tipo_prod INT NOT NULL,
    meio_divulgacao INT NOT NULL,
    ano_publicacao INT UNSIGNED NOT NULL,

    PRIMARY KEY (codigo_projeto, codigo_prod),

    FOREIGN KEY (codigo_projeto)
        REFERENCES projeto (codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE vinculo_projeto_participante (
    codigo_projeto INT UNSIGNED NOT NULL,
    cpf CHAR(11) NOT NULL,
    funcao_desempenhada INT NOT NULL,
    data_entrada DATE NOT NULL,
    data_saida DATE,

    PRIMARY KEY (codigo_projeto, cpf),

    FOREIGN KEY (codigo_projeto)
        REFERENCES projeto (codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (cpf)
        REFERENCES participante (cpf)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE autoria_producao (
    codigo_projeto INT UNSIGNED NOT NULL,
    codigo_prod INT UNSIGNED NOT NULL,
    cpf CHAR(11) NOT NULL,

    PRIMARY KEY (codigo_projeto, codigo_prod, cpf),

    FOREIGN KEY (codigo_projeto, codigo_prod)
        REFERENCES producao_cientifica (codigo_projeto, codigo_prod)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (codigo_projeto, cpf)
        REFERENCES vinculo_projeto_participante (codigo_projeto, cpf)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE vinculo_projeto_financiamento (
    codigo_projeto INT UNSIGNED,
    codigo_financiamento INT UNSIGNED,
    valor_destinado DECIMAL(20,2) NOT NULL,

    PRIMARY KEY (codigo_projeto, codigo_financiamento),

    CONSTRAINT uq_financiamento_por_projeto
        UNIQUE (codigo_projeto),

    FOREIGN KEY (codigo_projeto)
        REFERENCES projeto (codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (codigo_financiamento)
        REFERENCES financiamento (codigo_financiamento)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
