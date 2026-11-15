DROP DATABASE sigpesq;
CREATE DATABASE IF NOT EXISTS sigpesq
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sigpesq;

CREATE TABLE projeto (
    codigo_projeto INT UNSIGNED,
    titulo VARCHAR(100),
    descricao VARCHAR(300),
    situacao INT,
    data_inicio DATE,
    data_termino DATE,
    PRIMARY KEY (codigo_projeto)
);

CREATE TABLE participante (
    cpf CHAR(11),
    nome VARCHAR(100),
    email VARCHAR(100),
    tipo_participante INT,
    senha VARCHAR(255),
    PRIMARY KEY (cpf)
);

CREATE TABLE financiamento (
    codigo_financiamento INT UNSIGNED,
    agencia_financiadora INT,
    tipo_fomento INT,
    valor_total DECIMAL(20,2),
    data_inicio DATE,
    data_termino DATE,
    PRIMARY KEY (codigo_financiamento)
);

CREATE TABLE producao_cientifica (
    codigo_projeto INT UNSIGNED,
    codigo_prod INT UNSIGNED,
    titulo VARCHAR(100),
    tipo_prod INT,
    meio_divulgacao INT,
    ano_publicacao INT UNSIGNED,
    PRIMARY KEY (codigo_projeto, codigo_prod),

    FOREIGN KEY (codigo_projeto)
        REFERENCES projeto (codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE vinculo_projeto_participante (
    codigo_projeto INT UNSIGNED,
    cpf CHAR(11),
    funcao_desempenhada INT,
    data_entrada DATE,
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
    codigo_projeto INT UNSIGNED,
    codigo_prod INT UNSIGNED,
    cpf CHAR(11),
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
    valor_destinado DECIMAL(20,2),
    PRIMARY KEY (codigo_projeto, codigo_financiamento),

    FOREIGN KEY (codigo_projeto)
        REFERENCES projeto (codigo_projeto)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (codigo_financiamento)
        REFERENCES financiamento (codigo_financiamento)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS autoria_producao (
    codigo_projeto INT UNSIGNED,
    codigo_prod INT UNSIGNED,
    cpf CHAR(11),
    PRIMARY KEY (codigo_projeto, codigo_prod, cpf),
    FOREIGN KEY (codigo_projeto, codigo_prod)
        REFERENCES producao_cientifica (codigo_projeto, codigo_prod)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (codigo_projeto, cpf)
        REFERENCES vinculo_projeto_participante (codigo_projeto, cpf)
        ON DELETE RESTRICT ON UPDATE CASCADE
);
