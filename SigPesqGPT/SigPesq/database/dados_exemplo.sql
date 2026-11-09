-- Opcional: execute UMA vez depois de schema.sql, em um banco de estudo vazio.
-- Dados inteiramente fictícios; os CPFs seguem apenas o formato do SQL original.
USE sigpesq;
START TRANSACTION;
INSERT INTO participante VALUES
('00000000001','Carlos Eduardo Mendes','carlos@example.invalid','docente'),
('00000000002','Helena Soares','helena@example.invalid','docente'),
('00000000003','Mariana Fontes','mariana@example.invalid','discente'),
('00000000004','Lucas Torres','lucas@example.invalid','discente'),
('00000000005','Beatriz Ribeiro','beatriz@example.invalid','tec_adm');
INSERT INTO projeto VALUES
(2024001,'Bioinformática e inteligência artificial','Análise computacional de sinais biomédicos.','em_andamento','2024-03-01','2027-02-28'),
(2024002,'Modelagem molecular','Estudo de novos materiais sustentáveis.','em_andamento','2024-08-01','2027-07-31'),
(2023001,'Ecossistemas costeiros','Monitoramento da biodiversidade.','concluido','2023-01-01','2025-12-31');
INSERT INTO financiamento VALUES
(1,'cnpq','auxilio',420000.00,'2024-03-01','2027-02-28'),
(2,'fapes','bolsa',180000.00,'2024-08-01','2027-07-31'),
(3,'capes','convenio',310000.00,'2023-01-01','2025-12-31');
INSERT INTO vinculo_projeto_participante
(codigo_projeto,cpf,funcao_desempenhada,data_entrada,data_saida,carga_semanal,fomento,plano_trabalho) VALUES
(2024001,'00000000001','coordenador','2024-03-01','2027-02-28',10,NULL,'Coordenar pesquisa e equipe.'),
(2024001,'00000000003','bolsista','2024-03-01','2027-02-28',20,'PIBIC / CNPq','Preparar e analisar os dados.'),
(2024002,'00000000002','coordenador','2024-08-01','2027-07-31',10,NULL,NULL),
(2024002,'00000000004','bolsista','2024-08-01','2027-07-31',20,'FAPES',NULL),
(2023001,'00000000005','colaborador','2023-01-01','2025-12-31',15,NULL,NULL);
INSERT INTO vinculo_projeto_financiamento VALUES
(2024001,1,400000.00),(2024002,2,180000.00),(2023001,3,310000.00);
INSERT INTO producao_cientifica
(codigo_projeto,codigo_prod,titulo,tipo_prod,meio_divulgacao,veiculo,identificador,ano_publicacao) VALUES
(2024001,1,'Classificação de sinais biomédicos','artigo','revista','Revista Fictícia de Pesquisa','DEMO-ART-001',2025),
(2024002,1,'Simulador molecular','software','repositorio','Repositório Institucional','DEMO-SW-001',2026),
(2023001,1,'Relatório de biodiversidade','relatorio_tecnico','repositorio','Relatórios de Campo',NULL,2025);
INSERT INTO autoria_producao VALUES
(2024001,1,'00000000001'),(2024001,1,'00000000003'),
(2024002,1,'00000000002'),(2024002,1,'00000000004'),(2023001,1,'00000000005');
COMMIT;
