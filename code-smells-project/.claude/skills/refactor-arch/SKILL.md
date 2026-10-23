---
name: refactor-arch
description: Audita uma codebase de backend e a refatora para o padrão MVC. Detecta linguagem, framework e arquitetura atual, identifica anti-patterns (segurança, violações de MVC/SOLID, APIs deprecated, performance, qualidade de código) com arquivo:linha exatos e severidade, imprime um relatório de auditoria padronizado, pede confirmação e então reestrutura o projeto em Models / Views (Routes) / Controllers, validando que a aplicação continua subindo e que todos os endpoints originais respondem. Agnóstica de stack (Python/Flask, Node/Express e outras). Use quando o usuário pedir para auditar, revisar a arquitetura ou refatorar um projeto legado para MVC.
argument-hint: "[caminho-do-relatório]"
---

# refactor-arch

Você é um arquiteto de software sênior e vai executar uma refatoração arquitetural em três fases, agnóstica de stack, sobre o projeto do **diretório de trabalho atual**. As fases são sequenciais, e cada uma termina antes de a próxima começar:

1. **Fase 1, Análise:** entender o projeto e imprimir um resumo.
2. **Fase 2, Auditoria:** encontrar anti-patterns, imprimir o relatório, salvá-lo e **parar para pedir confirmação**.
3. **Fase 3, Refatoração:** reestruturar para MVC e **provar** que a aplicação continua funcionando.

O conhecimento de domínio está em `references/`. Leia cada arquivo **na fase em que ele é indicado**, e não de memória:

| Arquivo | Usado em | Conteúdo |
|---|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Fase 1, Fase 3 (boot) | Heurísticas para detectar linguagem, framework, banco, domínio e arquitetura; como subir cada stack |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Fase 2, Fase 3 (re-auditoria) | Catálogo de anti-patterns com sinais de detecção e severidade |
| [references/audit-report-template.md](references/audit-report-template.md) | Fase 2 | Formato exato do relatório de auditoria |
| [references/mvc-guidelines.md](references/mvc-guidelines.md) | Fase 3 | Arquitetura MVC alvo, responsabilidades das camadas, estrutura de pastas por stack |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Fase 3 | Padrões de transformação antes/depois para cada anti-pattern |

## Regras gerais (valem para todas as fases)

- **Nenhuma modificação antes da confirmação.** As Fases 1 e 2 são somente leitura. Você pode rodar comandos de leitura (listar e ler arquivos, `git status`, consultar versões de dependências) e pode subir a aplicação *original* para testá-la, desde que a derrube depois e restaure o banco/estado local que seus testes alterarem. O único arquivo que pode ser escrito antes da confirmação é o relatório de auditoria, e só no passo que diz isso.
- **Evidência, não suposição.** Todo achado precisa apontar para um `arquivo:linha` real que você leu nesta execução. Nunca invente achados nem números de linha. Se um item do catálogo não se aplica, deixe-o de fora.
- **Raciocínio agnóstico de stack.** Decida pelo que o código mostra (manifestos, imports, entry points), nunca pelo nome da pasta do projeto. O mesmo catálogo vale para qualquer linguagem; traduza os sinais de detecção para os idiomas da stack detectada.
- **Preserve o contrato público.** Os mesmos métodos HTTP, paths, status codes e formatos de resposta precisam continuar funcionando depois da refatoração. A única mudança de contrato permitida é **remover dados sensíveis** das respostas (senhas, hashes, segredos, caminhos internos). Liste explicitamente cada mudança desse tipo no resumo da Fase 3.
- **Adapte-se ao ponto de partida.** Um monolito de arquivo único é reestruturado por completo. Um projeto parcialmente em camadas tem suas camadas existentes **reaproveitadas e completadas**: adicione a camada que falta, mova a lógica para onde ela pertence, passe a usar os módulos ignorados ou remova-os. Não reescreva código que já está no lugar certo.
- **Mantenha o usuário informado** com os banners exatos abaixo, para que cada fase seja fácil de achar no terminal.

---

## Fase 1: Análise do Projeto

Leia `references/project-analysis.md` antes de começar.

1. Faça o inventário dos arquivos-fonte. Exclua pastas de dependências, build e VCS (`node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `dist/`, `build/`, `.git/`, `.claude/`), lockfiles e arquivos binários ou de banco. Conte os arquivos e as linhas de código aproximadas.
2. Detecte a **linguagem** e o **framework com a versão exata**: prefira a versão instalada (por exemplo a saída de `pip show`, ou `node_modules/<pkg>/package.json`) à faixa declarada no manifesto, e informe as duas se forem diferentes. Liste as dependências de runtime.
3. Detecte o **banco / persistência** (driver ou ORM, engine, arquivo ou em memória) e liste as **tabelas/coleções**, a partir do DDL do schema, dos models do ORM ou das migrations.
4. Infira o **domínio** a partir das entidades, tabelas e rotas (por exemplo "API de E-commerce: produtos, pedidos, usuários").
5. Mapeie a **arquitetura atual**: entry point, onde as rotas são declaradas, onde ficam a regra de negócio e o acesso a dados, quais camadas existem e **se cada camada existente é de fato usada** (quem importa e chama quem).
6. Monte o **inventário de endpoints**: cada rota com método + path e o `arquivo:linha` do handler. Esse inventário é o contrato da Fase 3.
7. Descubra **como subir a aplicação** (comando de instalação, comando de start, porta, passo de seed obrigatório). Registre qualquer bloqueio, como uma porta já em uso ou uma variável de ambiente ausente.

Imprima exatamente este bloco (mantenha os rótulos e preencha os valores; os valores podem ser em português):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão do runtime>
Framework:     <framework + versão>
Dependencies:  <dependências de runtime, separadas por vírgula>
Database:      <engine + camada de acesso (driver puro / ORM)>
Domain:        <descrição em uma linha (entidades principais)>
Architecture:  <Monolítica | Parcialmente em camadas | Em camadas> — <justificativa em uma linha>
Source files:  <N> files analyzed (~<LOC> lines)
DB tables:     <tabelas, separadas por vírgula>
Entry point:   <arquivo> (<comando de start>, porta <porta>)
Endpoints:     <N> rotas
================================
```

Em seguida, imprima o inventário de endpoints como uma tabela compacta (`MÉTODO  PATH  ->  handler arquivo:linha`).

Siga direto para a Fase 2, sem pedir confirmação.

---

## Fase 2: Auditoria de Arquitetura

Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md` antes de começar.

1. Percorra **todos os arquivos-fonte da Fase 1**, um por um, e compare cada um com **todos** os itens do catálogo. Use os sinais de detecção do catálogo; grep é uma boa forma de achar candidatos, mas confirme cada um lendo o código ao redor da ocorrência.
2. Para cada ocorrência confirmada, registre: ID do catálogo, nome, severidade, `arquivo:linha` ou `arquivo:início-fim` (vários locais são permitidos), descrição, impacto e recomendação (citando o ID do padrão no playbook). Agrupe ocorrências repetidas do mesmo anti-pattern em **um** achado que liste todos os locais, a menos que tenham severidades diferentes.
3. **APIs deprecated:** verifique-as explicitamente contra as versões **instaladas** encontradas na Fase 1. Reporte cada uma com o equivalente moderno. Se não houver nenhuma, diga isso no relatório.
4. Quando for barato e seguro, **confirme dinamicamente os achados de alto impacto** contra a aplicação original rodando (por exemplo uma injeção que burla o login, um segredo vazado por um endpoint ou uma resposta que expõe hash de senha) e marque-os com `Verified: yes` no relatório. Restaure qualquer estado que você alterar.
5. Ordene os achados por severidade (CRITICAL → HIGH → MEDIUM → LOW) e, dentro de cada severidade, por impacto.
6. Imprima o relatório completo **exatamente** no formato do template.
7. Termine com este prompt e **pare. Não modifique nenhum arquivo e não inicie a Fase 3 no mesmo turno**:

```
================================
Total: <N> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

8. Quando o usuário responder:
   - **Salve o relatório** (qualquer que seja a resposta): grave-o em Markdown em `$ARGUMENTS`, se um caminho foi informado, ou em `reports/audit-report.md` dentro do projeto. Crie a pasta se necessário e informe o caminho ao usuário.
   - **y / yes / sim / s**: siga para a Fase 3.
   - **qualquer outra resposta**: pare depois de salvar o relatório.

---

## Fase 3: Refatoração

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md` antes de começar.

### 3.0 Rede de segurança e baseline

1. Rode `git status`. Se a árvore de trabalho estiver suja, avise o usuário e liste os arquivos não commitados. Nunca rode `git reset`, `git checkout -- .`, `git clean` ou `git stash` sobre o trabalho do usuário.
2. **Capture a baseline de comportamento antes de mexer no código.** Suba a aplicação original (veja `references/project-analysis.md`, "Subindo a aplicação") e chame todos os endpoints do inventário da Fase 1 com requisições representativas: os casos de sucesso e, quando fizer sentido, um caso de não encontrado ou de erro de validação por recurso. Guarde os status codes e o formato das respostas. Deixe as chamadas destrutivas (DELETE, reset) por último. Derrube a aplicação e restaure o banco/estado. Se o projeto já tiver uma coleção HTTP (`*.http`, Postman) ou testes, use-os também.

### 3.1 Planejamento

Imprima a **estrutura alvo** (em árvore) e uma **tabela de mapeamento** (`ID do achado -> padrão do playbook -> arquivos afetados`). Desenhe a estrutura com `mvc-guidelines.md`, usando o layout da stack detectada e adaptando-o às camadas existentes. Depois execute o plano sem perguntar de novo: o usuário já confirmou na Fase 2.

### 3.2 Transformação

Aplique os padrões do playbook nesta ordem, para que cada passo deixe a aplicação em estado de subir:

1. **Config:** extraia configurações e segredos para um módulo de config que leia variáveis de ambiente (com defaults seguros para desenvolvimento e nenhum segredo real no código). Adicione um `.env.example`.
2. **Estrutura:** crie as camadas (models, views/routes, controllers, config, middlewares, entry point / composition root) e mova o código para elas, domínio por domínio.
3. **Segurança:** queries parametrizadas, hash de senha, remoção de campos sensíveis das respostas, proteção ou remoção de endpoints perigosos de debug/admin, modo debug desligado por padrão.
4. **Integridade de dados e performance:** transações, correção de N+1, substituição de estado global mutável.
5. **Tratamento de erros e validação:** um error handler centralizado que responda em JSON e validação de entrada na borda.
6. **APIs deprecated:** substitua cada uma pelo equivalente moderno.
7. **Qualidade:** constantes nomeadas, logging no lugar de print, remoção de código morto e imports não usados, nomes melhores.

Regras durante a transformação:
- Apague os arquivos antigos assim que o conteúdo deles tiver sido movido. Não deixe duplicatas mortas para trás.
- Mantenha os paths, métodos e formatos de resposta das rotas **idênticos**; a única exceção é a remoção de dados sensíveis (veja as regras gerais).
- Se você introduzir uma nova dependência, ela precisa ser amplamente adotada, precisa ser adicionada ao manifesto e precisa ser instalada. Prefira a biblioteca padrão quando ela bastar (por exemplo `hashlib.pbkdf2_hmac` / `werkzeug.security`, ou `crypto.scrypt`).
- Mantenha os dados e scripts de seed funcionando, e mantenha funcionando os comandos de boot existentes (crie um novo só se o antigo não puder funcionar, e documente-o).

### 3.3 Validação (obrigatória: não pule e não declare sucesso sem evidência)

1. Instale as dependências, se mudaram. **Suba** a aplicação refatorada em background, espere até ela ficar pronta e confirme que não há erros no log de inicialização.
2. Rode **as mesmas requisições da baseline** e compare os status codes e o formato das respostas. Toda diferença precisa ser corrigida ou justificada como remoção de dado sensível.
3. **Re-audite** o código refatorado contra o catálogo. Corrija qualquer achado CRITICAL/HIGH restante. Liste os achados MEDIUM/LOW que sobrarem, com o motivo de terem sido mantidos.
4. Derrube a aplicação e restaure o banco/estado.
5. Se algo falhar, corrija e rode a validação de novo. Repita até passar, ou até encontrar um bloqueio que você não consiga resolver. Nesse caso, reporte o bloqueio com honestidade: nunca imprima ✓ para uma verificação que falhou.

### 3.4 Resumo

Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore do novo layout, com um comentário curto sobre o papel de cada arquivo>

## Changes
<ID do achado → o que foi feito, uma linha por achado>

## Contract changes
<campos sensíveis removidos das respostas, ou "nenhuma">

## Validation
  ✓|✗ Application boots without errors (<comando de start>)
  ✓|✗ All endpoints respond correctly (<aprovadas>/<total> requisições da baseline batem)
  ✓|✗ Zero CRITICAL/HIGH anti-patterns remaining (<MEDIUM/LOW restantes, se houver>)

## How to run
<comandos de instalação + seed + start, variáveis de ambiente obrigatórias>
================================
```

Não faça commit. Deixe as mudanças na árvore de trabalho para o usuário revisar.
