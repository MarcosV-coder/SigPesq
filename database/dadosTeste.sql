-- Execute depois de bancoDeDados.sql, apenas uma vez, em uma base nova.
-- Senha de TODAS as contas fictícias: Pesquisa@2026
-- Senhas armazenadas como PBKDF2 com salt individual.
USE sigpesq;
START TRANSACTION;
INSERT INTO projeto (codigo_projeto,titulo,descricao,situacao,data_inicio,data_termino) VALUES
(101,'Monitoramento de recursos hídricos','Sensores e análise de qualidade da água.','1','2026-01-10',NULL),
(102,'Aprendizagem de máquina aplicada','Estudo de classificadores supervisionados.','1','2026-02-01',NULL),
(103,'Acervo digital regional','Digitalização e catalogação de documentos históricos.','2','2025-03-01','2026-03-01');
INSERT INTO participante (cpf,nome,email,tipo_participante,senha) VALUES
('11111111111','Ana Ribeiro','ana@exemplo.com','2','pbkdf2_sha256$600000$7a1183d55d5409821fb7beab84a107bd$59b1b3a609bdb8e796284b1b53f94ed32f74fafdbe58fc8dcfc231237426f9aa'),
('22222222222','Bruno Lima','bruno@exemplo.com','3','pbkdf2_sha256$600000$d53b23736c8617bbf713f63283085417$e807887dc63aef57af47b6e2ff5d292df72fdadebf7decb5c30b663ce2b01921'),
('33333333333','Carla Souza','carla@exemplo.com','1','pbkdf2_sha256$600000$3c07e7f177b43f38d36fab701e32eb74$f880857971b0b781c397c88442259f4f8e7e3e19bee5153dc94d9019533dd918'),
('44444444444','Daniel Costa','daniel@exemplo.com','2','pbkdf2_sha256$600000$1feb6030d98009feb5b08a48336b8a65$9b3edc1cfb2a13b7371bbcd538308a4f24b4c47f21ce58120e1e69a2d90758f9'),
('55555555555','Elisa Martins','elisa@exemplo.com','1','pbkdf2_sha256$600000$d5936cf038f1b9bfb77ea7148f2bc8c5$63a20fb77cced0008cdc7ab4f2bb3b51a8cd6ff2d5ff75a0b4bee5d0ad8ea0b4');
INSERT INTO financiamento (codigo_financiamento,agencia_financiadora,tipo_fomento,valor_total,data_inicio,data_termino) VALUES
(201,'1','1',48000.00,'2026-01-01','2027-12-31'),
(202,'2','2',30000.00,'2026-01-01','2027-12-31'),
(203,'3','3',12000.00,'2025-01-01','2026-12-31');
INSERT INTO producao_cientifica (codigo_projeto,codigo_prod,titulo,tipo_prod,meio_divulgacao,ano_publicacao) VALUES
(101,1,'Análise de sensores de baixo custo','1','1',2026),
(102,1,'Classificador experimental','3','3',2026),
(103,1,'Relatório de digitalização','4','3',2026);
INSERT INTO vinculo_projeto_participante (codigo_projeto,cpf,funcao_desempenhada,data_entrada,data_saida) VALUES
(101,'11111111111','3','2026-01-10',NULL),
(101,'22222222222','1','2026-01-10',NULL),
(101,'33333333333','2','2026-02-01',NULL),
(102,'44444444444','3','2026-02-01',NULL),
(102,'55555555555','2','2026-02-01',NULL),
(103,'11111111111','3','2025-03-01','2026-03-01'),
(103,'33333333333','1','2025-03-01','2026-03-01');
INSERT INTO vinculo_projeto_financiamento (codigo_projeto,codigo_financiamento,valor_destinado) VALUES (101,201,48000.00),(102,202,30000.00),(103,203,12000.00);
INSERT INTO autoria_producao (codigo_projeto,codigo_prod,cpf) VALUES
(101,1,'11111111111'),(101,1,'33333333333'),
(102,1,'44444444444'),(102,1,'55555555555'),
(103,1,'11111111111');
COMMIT;
