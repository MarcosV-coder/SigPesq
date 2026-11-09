# SIGPesq — Gestão de Pesquisa

Aplicação **desktop** em Python, CustomTkinter e MySQL Connector/Python. Usa SQL explícito, sem ORM e sem framework web. O MySQL Server armazena os dados; o Workbench administra o servidor e executa os scripts.

A interface segue a composição do PDF: navbar, cinco cards iniciais, formulário lateral e tabela de registros. Os números da home vêm do banco. As tabelas usam ttk.Treeview integrado ao CustomTkinter, com rolagem horizontal e vertical.

## 1. Pré-requisitos

- Python 3.10+ com Tkinter.
- MySQL Server **8.0.16+**, para aplicação efetiva das restrições CHECK.
- MySQL Workbench com conexão funcional.
- Ambiente gráfico; resolução recomendada: 1440 × 900. Mínimo da janela: 1120 × 720.

No Windows, instale o Python com Tcl/Tk e marque “Add Python to PATH”. Teste:

~~~powershell
py --version
py -m tkinter
~~~

No Ubuntu/Debian, se necessário:

~~~bash
sudo apt install python3-tk python3-venv
~~~

No WSL, a interface precisa de WSLg ou servidor gráfico. No Windows, você pode rodar diretamente pelo Python do Windows.

## 2. Preparar o banco no Workbench

### Banco novo

1. Abra a conexão no Workbench.
2. Em **File → Open SQL Script**, abra **database/schema.sql**.
3. Execute o script inteiro pelo botão de raio. Ele cria sigpesq e suas sete tabelas.
4. Opcionalmente, execute **database/dados_exemplo.sql** uma única vez, em um banco vazio.
5. Atualize o painel Schemas.

Não execute schema.sql sobre tabelas já existentes: o script não remove nem substitui tabelas e os CREATE TABLE irão falhar.

### Banco já criado pelo SQL anexado

Faça backup com **Server → Data Export**.

Execute **somente database/migracao_pdf.sql, uma única vez**. Ela mantém as seis tabelas originais e seus dados, acrescenta os campos usados pelo PDF e cria a tabela de autoria. Não execute o schema completo sobre esse banco.

DDL no MySQL faz commit implícito. Se houver falha parcial, confira os campos já adicionados antes de repetir os ALTERs. Registros antigos ficam sem autores e sem os novos campos opcionais; carga semanal recebe 20 horas e pode ser ajustada em Vínculos.

**database/original.sql** é uma cópia do SQL recebido para consulta.

### Usuário da aplicação

Com uma conta administradora, execute o exemplo **substituindo a senha**:

~~~sql
CREATE USER 'sigpesq_app'@'localhost' IDENTIFIED BY 'SUBSTITUA_POR_UMA_SENHA_FORTE';
GRANT SELECT, INSERT, UPDATE, DELETE ON sigpesq.* TO 'sigpesq_app'@'localhost';
~~~

Se o servidor distinguir a conexão TCP em 127.0.0.1 da conexão local, crie/conceda o usuário para o host correspondente à instalação.

## 3. Instalar as dependências

Abra o terminal **na pasta SigPesq**, onde está main.py.

Windows / PowerShell:

~~~powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

Linux / macOS:

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
~~~

Não é necessário ativar o ambiente virtual: os comandos usam seu executável diretamente.

## 4. Configurar e executar

config.py lê variáveis de ambiente. Nenhuma senha é incluída no projeto; arquivos .env não são carregados automaticamente.

| Variável | Padrão |
| --- | --- |
| SIGPESQ_DB_HOST | 127.0.0.1 |
| SIGPESQ_DB_PORT | 3306 |
| SIGPESQ_DB_USER | sigpesq_app |
| SIGPESQ_DB_PASSWORD | vazio |
| SIGPESQ_DB_NAME | sigpesq |

Windows / PowerShell, **no mesmo terminal** usado para iniciar:

~~~powershell
$env:SIGPESQ_DB_HOST = "127.0.0.1"
$env:SIGPESQ_DB_PORT = "3306"
$env:SIGPESQ_DB_USER = "sigpesq_app"
$env:SIGPESQ_DB_PASSWORD = "SUA_SENHA"
$env:SIGPESQ_DB_NAME = "sigpesq"
.\.venv\Scripts\python.exe main.py
~~~

Linux / macOS:

~~~bash
export SIGPESQ_DB_HOST="127.0.0.1"
export SIGPESQ_DB_PORT="3306"
export SIGPESQ_DB_USER="sigpesq_app"
export SIGPESQ_DB_PASSWORD="SUA_SENHA"
export SIGPESQ_DB_NAME="sigpesq"
.venv/bin/python main.py
~~~

Se usar outro banco, ajuste também os CREATE DATABASE/USE nos scripts. Variáveis definidas no terminal valem para a sessão; não inclua senhas em arquivos versionados.

Teste a conexão sem abrir a interface:

~~~powershell
.\.venv\Scripts\python.exe -c "from db import testar_conexao; print(testar_conexao())"
~~~

No Linux/macOS, troque o executável por .venv/bin/python.

## 5. Como usar

Ordem sugerida em um banco vazio:

1. **Participantes**: cadastre primeiro um docente sem vínculo inicial, que é opcional.
2. **Projetos**: informe um código numérico único e selecione o docente coordenador. Projeto e vínculo de coordenação são salvos na mesma transação.
3. Cadastre os outros participantes, com vínculo inicial opcional.
4. **Vínculos**: associe participantes aos projetos com função, datas, carga semanal, fomento e atividades. Na edição de um participante, gerencie seus vínculos nesse módulo.
5. **Financiamentos**: cadastre o contrato. Clique em **Destinar a projetos** para distribuir valores a um ou mais projetos; **Voltar a contratos** retorna à lista principal.
6. **Produções**: selecione um projeto, use um código único dentro dele e marque os autores. Só aparecem participantes vinculados ao projeto.

Operações comuns:

- **Salvar** cria ou atualiza o registro em edição.
- Selecione uma linha e clique em **Editar**, ou dê duplo clique.
- **Novo registro** limpa o formulário.
- As chaves primárias ficam bloqueadas na edição. Para mudar a composição de um vínculo, exclua o antigo e crie outro.
- **Excluir** pede confirmação e explica os efeitos em cascata.
- **Atualizar** consulta novamente o MySQL e limpa o formulário.
- Busca sem distinção de acentos/maiúsculas; inclui equipe dos projetos, projetos dos participantes e autores das produções.
- Filtros por categoria e, nas produções, por ano. Clique numa coluna para ordenar.
- **Exportar CSV** exporta os resultados filtrados com UTF-8 e separador ponto e vírgula.
- MySQL trabalha em uma thread separada; widgets são atualizados na thread principal. Aguarde terminar antes de trocar de módulo ou fechar.

Projetos concluídos/cancelados também podem receber registros históricos. As listas não são limitadas a projetos ativos.

## 6. Análise do SQL e ajustes para o PDF

O SQL original define **seis tabelas**, sem AUTO_INCREMENT. Os códigos são informados manualmente. O CPF é textual para manter zeros à esquerda. A produção usa a chave composta (codigo_projeto, codigo_prod): o mesmo código pode aparecer em projetos diferentes.

A coordenação fica em vinculo_projeto_participante, com função coordenador, sem duplicar uma coluna em projeto. Projeto–participante e projeto–financiamento são relações muitos-para-muitos.

| Diferença no PDF | Implementação |
| --- | --- |
| FINEP | Acrescentada ao ENUM de agências |
| Patente | Acrescentada ao ENUM de produção |
| Periódico/evento e DOI/registro | Novos campos veiculo e identificador |
| Autores selecionáveis | Nova tabela autoria_producao com duas FKs compostas |
| Carga semanal, fomento e atividades | Novos campos no vínculo de participante |
| Coordenador responsável | Docente vinculado; salvo junto com o projeto |
| Projeto apoiado e valor aplicado | Tela de destinações dentro de Financiamentos |
| Código como PRJ-2024-001 | Mantido INT UNSIGNED; use um número, ex.: 2024001 |
| Orientando, voluntário e títulos específicos de bolsa | Mantidos os três papéis originais; detalhes entram em fomento/plano |
| Meio de divulgação com nome livre | Mantido ENUM revista/congresso/repositorio e adicionado veículo livre |

As sete tabelas finais são: projeto, participante, financiamento, producao_cientifica, vinculo_projeto_participante, vinculo_projeto_financiamento e autoria_producao.

### Validações

- Obrigatoriedade, limites de texto e categorias.
- Datas em DD/MM/AAAA ou AAAA-MM-DD; término não pode anteceder início.
- CPF com ou sem pontuação; salva 11 dígitos. Assim como o SQL original, **não valida os dígitos verificadores**.
- Nome segue o SQL original: letras e espaços. Pontos, hífens e apóstrofos não são aceitos.
- Validação básica de e-mail e unicidade no MySQL.
- Valores positivos em Decimal, até DECIMAL(20,2), com no máximo duas casas. Exemplos: 1234,56; 1.234,56; 1234.56. Use as duas casas em valores com separador para evitar ambiguidades.
- Carga semanal entre 1 e 168; ano de publicação de 1000 a 9999, como no SQL.
- Coordenador deve ser docente; um coordenador por projeto. Ao trocar a coordenação em Projetos, o antigo vira colaborador e outros detalhes do vínculo existente são preservados.
- A soma destinada não pode superar o valor do contrato. O contrato não pode ser reduzido abaixo do total destinado. A linha do contrato é bloqueada durante essas gravações para serializar operações concorrentes.
- Autores precisam ter vínculo com o projeto. Produção e autorias são salvas juntas.
- SQL parametrizado com %s; identificadores de tabelas/colunas vêm de metadados internos fixos.
- Em falhas: rollback e fechamento de cursores/conexões.

Coordenação única e limite financeiro são regras da aplicação. Edições diretas no Workbench ou por outros programas podem desrespeitá-las. Dados anteriores à migração não são corrigidos automaticamente. CHECKs e FKs originais continuam no banco.

### Exclusões em cascata

| Excluído | Consequência |
| --- | --- |
| Projeto | Remove suas produções, vínculos, destinações e autorias |
| Participante | Remove seus vínculos e autorias; mantém produções |
| Financiamento | Remove destinações; mantém projetos |
| Vínculo de participante | Remove as autorias desse participante nesse projeto |
| Produção | Remove suas autorias |
| Destinação | Remove apenas a própria destinação |

A interface explica esses efeitos antes da confirmação. Faça backup para recuperar exclusões.

### Escopo

A composição visual é adaptada aos componentes desktop. Não há autenticação: a navbar identifica o contexto acadêmico, sem simular login. Não há integração com Lattes, sincronização externa nem validação online de DOI. DOI/registro é texto opcional. Fomento/bolsa no vínculo é uma descrição e não uma associação automática a um contrato.

## 7. Estrutura

~~~text
SigPesq/
├── main.py
├── db.py
├── config.py
├── repositorio.py          # SQL explícito e transações
├── validacao.py            # validações independentes da interface
├── telas/
│   ├── __init__.py
│   ├── base.py             # formulário, tabela e CRUD compartilhados
│   ├── modelos.py          # campos, categorias e colunas
│   ├── home.py
│   ├── projetos.py
│   ├── participantes.py
│   ├── financiamentos.py
│   ├── producoes.py
│   └── vinculos.py
├── database/
│   ├── schema.sql
│   ├── dados_exemplo.sql
│   ├── migracao_pdf.sql
│   └── original.sql
├── tests/
│   ├── test_validacao.py
│   └── test_transacoes.py
├── requirements.txt
├── .gitignore
└── README.md
~~~

Os auxiliares evitam repetir o mesmo código nos cinco módulos. Cada módulo tem sua própria classe de tela.

## 8. Verificação

Testes automatizados, sem modificar seu banco:

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

Cobrem valores grandes sem float, entradas inválidas, datas reais, CPF, período, vínculo inicial, rollback, fechamento de conexão, parametrização SQL e destinação acima do contrato. Transações usam um conector simulado; não substituem o teste no MySQL.

Roteiro de aceite:

1. Importe os exemplos e confira os cinco cards.
2. Crie um participante, edite o e-mail e confira no Workbench.
3. Tente repetir CPF/e-mail e confira o erro de duplicidade.
4. Crie um projeto e confira seu vínculo de coordenação.
5. Destine recursos; tente superar o contrato e confira que nada foi gravado.
6. Cadastre uma produção com dois autores e confira a tabela de autoria.
7. Filtre, exporte CSV, feche e reabra; os dados devem persistir.
8. Exclua um projeto de teste e confira a cascata.
9. Pare o serviço MySQL, confira a mensagem, reinicie e clique em Atualizar.

## 9. Solução de problemas

| Erro | Ação |
| --- | --- |
| ModuleNotFoundError | Instale requirements.txt pelo mesmo Python usado para executar |
| No module named tkinter | Instale Tcl/Tk ou python3-tk |
| Access denied | Confira senha, variáveis e permissões/host do usuário |
| Conexão recusada | Inicie MySQL Server e confira host/porta; Workbench sozinho não garante servidor ativo |
| Unknown database | Execute schema.sql e confira SIGPESQ_DB_NAME |
| Unknown column / tabela ausente | Execute schema.sql para banco novo ou migração para o original |
| Exemplos duplicados | Os INSERTs são para banco vazio e execução única |
| CHECK inválido | Use MySQL 8.0.16+ e execute o script completo |
| Troca de módulo sem efeito | Aguarde a operação atual terminar |
| Texto fora da área visível | Aumente a janela ou use a rolagem |

Documentação: [CustomTkinter](https://customtkinter.tomschimansky.com/documentation/) e [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/).

## 10. Verificações desta entrega

- Os 10 testes automatizados passaram.
- Todos os arquivos Python foram compilados e os quatro scripts SQL foram analisados no dialeto MySQL.
- Não havia servidor MySQL nem display gráfico disponível no ambiente de geração. Portanto, conexão real, execução da migração no servidor e inspeção visual do aplicativo devem ser confirmadas localmente pelo roteiro de aceite acima.
