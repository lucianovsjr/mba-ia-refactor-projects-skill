# Template do Relatório de Auditoria

Referência da **Fase 2**. Define o formato **exato** do relatório que é impresso no terminal e salvo em Markdown. O conteúdo impresso e o arquivo salvo são **idênticos**.

## Regras

1. **Ordem:** os achados são ordenados por severidade: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro de cada severidade, os de maior impacto vêm primeiro.
2. **Numeração:** `F-01`, `F-02`, ... na ordem final. Esses IDs são usados na Fase 3 (plano e resumo).
3. **Localização obrigatória e exata:** `File:` recebe `caminho/relativo.ext:linha` ou `caminho:início-fim`. Para várias ocorrências, liste todas separadas por vírgula, por exemplo `models.py:28, 47-50, 92`. Caminhos são relativos à raiz do projeto. É proibido usar "vários arquivos", "em todo o código" ou deixar a linha de fora.
4. **Um achado por anti-pattern**, agrupando as ocorrências. Separe em dois achados só se as severidades forem diferentes.
5. **`Catalog:`** recebe o ID do catálogo (`AP-xx`). **`Recommendation:`** termina com o padrão do playbook (`→ PB-xx`).
6. **`Verified:`** `yes (<como>)` se o achado foi confirmado com a aplicação rodando; `no` se veio só da leitura do código.
7. **Summary** confere com a lista: a soma das severidades é igual ao `Total`.
8. **Deprecated APIs:** a seção é **sempre** impressa. Se não houver nenhuma, escreva `None detected for the installed versions (<libs + versões>)`.
9. **Idioma:** os rótulos (`File:`, `Description:`, `Impact:`...) ficam em inglês, como no template. O texto de cada campo é escrito em português.
10. **Fecho:** o relatório termina com o bloco `Total` e o prompt de confirmação. Na versão salva em arquivo, o prompt é substituído pela resposta do usuário.

## Formato

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework> <versão> (<banco / camada de acesso>)
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | <nome> | AP-xx | <arquivo:linha principal> |
| ... | | | | |

## Findings

### F-01 [CRITICAL] <Nome do anti-pattern>
File: <arquivo:linha[, arquivo:início-fim, ...]>
Catalog: AP-xx
Description: <o que acontece no código, citando o trecho ou a construção problemática>
Impact: <consequência concreta para segurança, manutenção, dados ou performance>
Recommendation: <o que fazer> → PB-xx
Verified: <yes (requisição/comando e resultado) | no>

### F-02 [HIGH] <...>
...

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| <arquivo:linha, ...> | <API> | <equivalente> | <warning observado / versão instalada> |

## Architecture Notes
- Current: <classificação da Fase 1 + justificativa em 1 linha>
- Layers present but unused: <lista, ou "none">
- Target: MVC — <resumo em 1 linha do que muda (ex.: "separar models/controllers/routes por domínio")>

================================
Total: <N> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo preenchido (projeto fictício)

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: biblioteca-api
Stack:   Python 3.11 + Flask 3.1.0 (SQLite / sqlite3 driver)
Files:   3 analyzed | ~420 lines of code
Date:    2026-01-15

## Summary
CRITICAL: 2 | HIGH: 1 | MEDIUM: 2 | LOW: 1

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | SQL Injection | AP-02 | repo.py:14 |
| F-02 | CRITICAL | Hardcoded Credentials | AP-01 | app.py:6 |
| F-03 | HIGH | Fat Controller | AP-08 | app.py:20-95 |
| F-04 | MEDIUM | N+1 Queries | AP-12 | repo.py:40-52 |
| F-05 | MEDIUM | Deprecated API | AP-13 | repo.py:3, 61 |
| F-06 | LOW | Magic Numbers | AP-19 | app.py:44, 71 |

## Findings

### F-01 [CRITICAL] SQL Injection
File: repo.py:14, 27-29, 33
Catalog: AP-02
Description: As queries de busca e login concatenam valores do request, por exemplo `"SELECT * FROM livros WHERE titulo LIKE '%" + termo + "%'"`.
Impact: Permite ler ou alterar qualquer tabela e burlar o login com `' OR 1=1 --`.
Recommendation: Usar placeholders `?` e passar os parâmetros separadamente → PB-02
Verified: yes (`GET /livros?q=%' OR 1=1 --` retornou todos os registros, inclusive os inativos)

### F-02 [CRITICAL] Hardcoded Credentials
File: app.py:6
Catalog: AP-01
Description: `app.config["SECRET_KEY"] = "dev-123"` fixa a chave de assinatura no código.
Impact: A chave fica versionada no git, o que permite forjar sessões em qualquer ambiente.
Recommendation: Ler de `SECRET_KEY` no ambiente via módulo de config, com `.env.example` → PB-01
Verified: no

### F-03 [HIGH] Fat Controller
File: app.py:20-95
Catalog: AP-08
Description: O handler `emprestar()` valida o body, calcula a multa, consulta o estoque e grava o empréstimo no próprio handler da rota.
Impact: A regra de empréstimo não pode ser testada sem HTTP e banco, e está duplicada em `devolver()`.
Recommendation: Mover a regra para `controllers/emprestimo_controller.py`, deixando a rota só com HTTP → PB-07
Verified: no

### F-04 [MEDIUM] N+1 Queries
File: repo.py:40-52
Catalog: AP-12
Description: `listar_emprestimos()` executa uma query de livro e uma de usuário para cada empréstimo dentro do `for`.
Impact: São 1 + 2N queries por chamada, e a latência cresce linearmente com o volume.
Recommendation: Um único `JOIN` entre emprestimos, livros e usuarios → PB-10
Verified: no

### F-05 [MEDIUM] Deprecated API
File: repo.py:3, 61
Catalog: AP-13
Description: `datetime.utcnow()` é usado para calcular o vencimento.
Impact: É deprecated desde o Python 3.12 e devolve datetime sem fuso horário, o que gera erros de comparação.
Recommendation: `datetime.now(timezone.utc)` → PB-11
Verified: no

### F-06 [LOW] Magic Numbers
File: app.py:44, 71
Catalog: AP-19
Description: O prazo `14` (dias) e a multa `0.5` aparecem como literais.
Impact: A regra fica escondida e sujeita a divergir entre os handlers.
Recommendation: Constantes `PRAZO_EMPRESTIMO_DIAS` e `MULTA_DIARIA` → PB-16
Verified: no

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| repo.py:3, 61 | `datetime.utcnow()` | `datetime.now(timezone.utc)` | Deprecated desde o Python 3.12 |

## Architecture Notes
- Current: Monolítica — `app.py` concentra rotas e regras; `repo.py` mistura SQL de 3 domínios
- Layers present but unused: none
- Target: MVC — models por domínio, controllers com as regras, routes só com HTTP, config via env

================================
Total: 6 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Checklist antes de imprimir

- [ ] Todo achado tem `File:` com linha(s) real(is), lidas nesta execução
- [ ] A ordem é CRITICAL → HIGH → MEDIUM → LOW, com a numeração F-xx sequencial nessa ordem
- [ ] O Summary bate com a tabela e com o Total
- [ ] A seção Deprecated APIs está presente (preenchida ou "None detected...")
- [ ] Todo achado cita `AP-xx` e `PB-xx`
- [ ] Nenhum arquivo foi modificado até aqui
