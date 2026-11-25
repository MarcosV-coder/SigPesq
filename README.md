# SIGPesq

Aplicação Desktop de simulação para assistência e acompanhamento em Projetos de Pesquisa. Trabalho acadêmico de Banco de Dados I.

Segue abaixo os requisitos e o passo a passo para executar a aplicação:

## 1. Preparar o banco no Workbench

Tenha MySQL Server em execução, MySQL Workbench e Python 3.10 ou superior.

1. Abra o Workbench. Se precisar criar a conexão, clique em **+** ao lado de
   **MySQL Connections** e use **Standard (TCP/IP)**, servidor `127.0.0.1`,
   porta `3306`, usuário `root` e a senha definida na instalação do MySQL.
   Clique em **Test Connection**, salve e abra a conexão.
2. Em **File > Open SQL Script**, abra e execute `database/01_banco.sql` inteiro.
3. Abra e execute `database/02_dados_iniciais.sql` inteiro.

A base utilizada é **`sigpesq`**.

## 2. Conectar o Python

No terminal, dentro da pasta `SigPesq`, execute:

```console
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python configurar.py
```

`configurar.py` pede **apenas a conexão MySQL**:

| Campo | Valor para a instalação local padrão |
| --- | --- |
| Servidor | `127.0.0.1` |
| Porta | `3306` |
| Usuário MySQL | `root` |
| Banco | `sigpesq` |
| Senha do MySQL | A mesma senha usada na conexão do Workbench |

Pressione **Enter** para aceitar os valores que aparecem entre colchetes. Se a sua instalação
usa outros valores, informe os mesmos do Workbench. A senha será pedida em seu
próprio campo e **não aparece enquanto você digita**.

## 3. Abrir a aplicação

```console
.venv\Scripts\python main.py
```

Na tela de login, para utilizar como administrador geral, use:

| Login | Senha |
| --- | --- |
| `admin` | `admin123` |

Esse administrador **já vem pronto**, não é participante, não possui CPF e não
precisa estar vinculado a projetos. Ele pode consultar, cadastrar, editar e
excluir registros em todas as seções. Não é necessário criar uma conta
administrativa no configurador ou no banco.

A tela inicial apresenta os módulos e seus indicadores reais. Clique em
**Acessar** ou use a navegação superior para abrir uma seção.
Nas tabelas, os ícones à direita são, nesta ordem: **Detalhes**, **Editar**
e **Excluir**. Use o botão **Novo/Adicionar** para cadastrar.
A busca e o filtro ajudam na consulta e realizam os requisitos de busca específicos.

## Acesso dos participantes

O login dos participantes continua disponível por e-mail ou CPF e senha.
Todos os usuários autenticados consultam os mesmos projetos, participantes,
financiamentos, produções, vínculos e destinações. Senhas nunca são exibidas.
As permissões variam somente nas operações de cadastro, edição e exclusão:

| Perfil | Permissões |
| --- | --- |
| Administrador | Cadastrar, editar e excluir em todas as seções |
| Docente | Criar projetos; ao criar, é vinculado como coordenador |
| Coordenador ativo | Editar o projeto que coordena e gerenciar seus registros relacionados |
| Técnico ativo no projeto | Editar esse projeto e gerenciar seus registros relacionados; não cria projetos |
| Discente sem coordenação | Consultar tudo e atualizar seus próprios dados pessoais |

O cadastro opcional cria uma conta discente. O administrador define os tipos
Docente e Técnico-administrativo.

As contas fictícias usam a senha `Pesquisa@2026`: `ana@exemplo.com` é coordenadora
do projeto 101, `bruno@exemplo.com` é técnico vinculado ao 101 e
`carla@exemplo.com` é bolsista com acesso de consulta.

## Observações rápidas

- A senha do MySQL conecta ao banco. `admin123` é a senha do administrador
  **da aplicação**, não a senha do usuário MySQL `root`.
- Pode fechar o Workbench após importar os SQLs; mantenha o servidor MySQL ligado.
- Se a conexão falhar, confira os dados e rode `configurar.py` novamente.
- Chaves primárias e estrangeiras definem a identidade e os relacionamentos no SQL;
  validações e permissões adicionais são tratadas na aplicação.
- No Linux/macOS, substitua `.venv\Scripts\python` por `.venv/bin/python`.
  O Python precisa ter Tkinter disponível.


## Autores das produções científicas

Para um banco que já existe, execute `database/03_autores.sql` no Workbench
antes de abrir esta versão. Esse script somente cria a tabela de autorias.
Não execute novamente os scripts de criação e dados iniciais no banco existente.
Para uma instalação nova, execute `01_banco.sql` e depois `02_dados_iniciais.sql`.

No cadastro ou edição de uma produção, escolha o projeto e marque um ou mais
autores. Somente os participantes vinculados àquele projeto são oferecidos.
A lista muda quando o projeto é alterado. Os autores salvos aparecem em Detalhes
e podem ser encontrados pela busca da consulta de produções.
A aplicação exige pelo menos um autor, confirma o vínculo novamente ao salvar
e grava produção e autoria na mesma transação.

A nova tabela `autoria_producao` identifica cada autoria por
`(codigo_projeto, codigo_prod, cpf)`. Uma FK composta aponta para a produção
com cascatas de atualização e exclusão. Outra aponta para o vínculo da equipe,
com atualização em cascata e exclusão restrita para preservar a autoria.
Remova ou substitua o autor nas produções antes de excluir seu vínculo ou conta.
Excluir um projeto pela aplicação remove suas produções, autorias e vínculos.

Produções antigas continuam preservadas, com autoria pendente; abra cada uma
para definir seus autores reais. Não são escolhidos autores automaticamente.
Vínculos encerrados também podem ser autores, preservando a autoria histórica;
não há exigência de vínculo ativo na data atual.
O banco agora possui sete tabelas. O roteiro de revisão anterior descrevia a
versão com seis tabelas e deve considerar essa nova associação de autoria.
