-- Base NOVA. Não migra nem apaga o banco antigo.
CREATE DATABASE IF NOT EXISTS sigpesq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sigpesq;
-- Somente PRIMARY KEY permanece como identidade técnica dos registros.
-- Regras, relações, exclusões relacionadas e e-mails únicos: aplicação Python.
CREATE TABLE projeto (
    codigo_projeto INT UNSIGNED,
    titulo VARCHAR(100),
    descricao VARCHAR(300),
    situacao INT,
    data_inicio DATE,
    data_termino DATE,
    PRIMARY KEY (codigo_projeto)
) ENGINE=InnoDB;

CREATE TABLE participante (
    cpf CHAR(11),
    nome VARCHAR(100),
    email VARCHAR(100),
    tipo_participante INT,
    senha VARCHAR(255),
    PRIMARY KEY (cpf)
) ENGINE=InnoDB;

CREATE TABLE financiamento (
    codigo_financiamento INT UNSIGNED,
    agencia_financiadora INT,
    tipo_fomento INT,
    valor_total DECIMAL(20,2),
    data_inicio DATE,
    data_termino DATE,
    PRIMARY KEY (codigo_financiamento)
) ENGINE=InnoDB;

CREATE TABLE producao_cientifica (
    codigo_projeto INT UNSIGNED,
    codigo_prod INT UNSIGNED,
    titulo VARCHAR(100),
    tipo_prod INT,
    meio_divulgacao INT,
    ano_publicacao SMALLINT UNSIGNED,
    PRIMARY KEY (codigo_projeto, codigo_prod)
) ENGINE=InnoDB;

CREATE TABLE vinculo_projeto_participante (
    codigo_projeto INT UNSIGNED,
    cpf CHAR(11),
    funcao_desempenhada INT,
    data_entrada DATE,
    data_saida DATE,
    PRIMARY KEY (codigo_projeto, cpf)
) ENGINE=InnoDB;

CREATE TABLE vinculo_projeto_financiamento (
    codigo_projeto INT UNSIGNED,
    codigo_financiamento INT UNSIGNED,
    valor_destinado DECIMAL(20,2),
    PRIMARY KEY (codigo_projeto, codigo_financiamento)
) ENGINE=InnoDB;

