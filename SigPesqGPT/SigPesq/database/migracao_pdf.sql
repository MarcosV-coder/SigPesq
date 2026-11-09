-- Faça backup. Execute UMA vez, apenas sobre o SQL original fornecido.
-- DDL do MySQL faz commit implícito; não é uma migração transacional.
-- Se houver falha parcial, verifique o esquema antes de repetir ALTERs.
USE sigpesq;
ALTER TABLE financiamento MODIFY agencia_financiadora ENUM('capes','fapes','cnpq','finep') NOT NULL;
ALTER TABLE producao_cientifica
 MODIFY tipo_prod ENUM('artigo','cap_livro','software','relatorio_tecnico','patente') NOT NULL,
 ADD COLUMN veiculo VARCHAR(200) NULL,
 ADD COLUMN identificador VARCHAR(200) NULL;
ALTER TABLE vinculo_projeto_participante
 ADD COLUMN carga_semanal SMALLINT UNSIGNED NOT NULL DEFAULT 20 CHECK (carga_semanal BETWEEN 1 AND 168),
 ADD COLUMN fomento VARCHAR(100) NULL,
 ADD COLUMN plano_trabalho VARCHAR(2000) NULL;

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
