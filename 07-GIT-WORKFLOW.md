# BACKTEST PRO — Workflow Git e Deploy

## 1. CONTEXTO

A partir de Março/2026, duas pessoas trabalham simultaneamente no projeto (codebase, Supabase e Vercel). Para evitar conflitos e garantir que nada vai para produção sem teste, adotamos um fluxo baseado em branches.

---

## 2. ESTRUTURA DE BRANCHES

```
main          → produção (Vercel auto-deploy → backtestpro-app.vercel.app)
dev           → desenvolvimento principal (Vercel preview deploy automático)
feature/xxx   → funcionalidades novas (parte de dev)
fix/xxx       → correções de bugs (parte de dev)
content/xxx   → alterações de copy/conteúdo
infra/xxx     → infraestrutura (vercel.json, Supabase migrations, etc)
```

**Regra absoluta: ninguém faz push direto para `main`.** Todo código passa por `dev` e é testado antes do merge para produção.

---

## 3. CONVENÇÃO DE NOMENCLATURA

| Tipo | Padrão | Exemplos |
|---|---|---|
| Funcionalidade nova | `feature/xxx` | `feature/supabase-auth`, `feature/mercado-pago` |
| Correção de bug | `fix/xxx` | `fix/modal-dom-timing`, `fix/dropdown-position` |
| Conteúdo/copy | `content/xxx` | `content/landing-page`, `content/emails` |
| Infraestrutura | `infra/xxx` | `infra/vercel-headers`, `infra/supabase-rls` |

---

## 4. FLUXO DE TRABALHO PADRÃO

### Início de qualquer tarefa
```bash
# 1. Sempre partir da dev atualizada
git checkout dev
git pull origin dev

# 2. Criar branch específica para a tarefa
git checkout -b feature/nome-da-feature
```

### Durante o desenvolvimento
```bash
# Commitar com frequência, mensagens descritivas
git add .
git commit -m "feat: descrição do que foi feito"
git push origin feature/nome-da-feature
```

### Integrar com o trabalho do outro colaborador
```bash
# Quando quiser testar junto com o que o outro desenvolveu
git checkout dev
git pull origin dev
git merge feature/nome-da-feature
git push origin dev
# → Vercel gera preview automático da dev
```

### Deploy para produção
```bash
# Apenas quando os testes na dev estiverem aprovados
# Abrir Pull Request no GitHub: dev → main
# Após merge, Vercel faz o deploy de produção automaticamente
```

---

## 5. COMO FUNCIONA O DEPLOY NA VERCEL

A Vercel está configurada para:

| Branch | Comportamento | URL |
|---|---|---|
| `main` | **Deploy de produção** | `backtestpro-app.vercel.app` |
| `dev` | **Preview automático** | `backtestpro-app-git-dev-xxx.vercel.app` |
| qualquer outra | Preview automático | URL única gerada por push |

**Nenhuma configuração extra é necessária.** A Vercel detecta automaticamente qualquer branch que não seja `main` e gera um preview deploy com URL própria.

### Onde encontrar a URL de preview da `dev`
- **Painel Vercel:** Dashboard → projeto → aba Deployments → filtrar por branch `dev`
- **GitHub:** Ao abrir um Pull Request `dev → main`, a Vercel comenta automaticamente com a URL do preview

---

## 6. CONFIGURAÇÃO INICIAL DO AMBIENTE (para novo colaborador)

```bash
# Clonar o repositório
git clone https://github.com/clayton120178-sketch/backtest-pro.git
cd backtest-pro

# Entrar na branch de desenvolvimento
git checkout dev

# Criar sua branch de trabalho a partir da dev
git checkout -b feature/minha-tarefa
```

**Token de acesso GitHub:** solicitar ao Clayton (token pessoal sem expiração, armazenado fora do repositório por segurança).

Configurar remote com autenticação:
```bash
git remote set-url origin https://<TOKEN>@github.com/clayton120178-sketch/backtest-pro.git
```

---

## 7. REGRAS DE CONVIVÊNCIA

1. **Nunca force-push em `dev` ou `main`.** Apenas em branches pessoais.
2. **Sempre fazer `git pull origin dev` antes de começar a trabalhar** — evita conflitos desnecessários.
3. **Commits atômicos e descritivos.** Um commit = uma mudança lógica. Não acumular dias de trabalho num único commit gigante.
4. **Testar localmente antes de fazer merge na `dev`.** A `dev` deve estar sempre em estado funcional.
5. **Comunicar antes de fazer merge na `main`.** Os dois devem saber que um deploy de produção vai acontecer.

---

## 8. PREFIXOS DE COMMIT (convenção)

| Prefixo | Quando usar |
|---|---|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `style:` | Mudança visual sem impacto funcional |
| `refactor:` | Refatoração sem mudança de comportamento |
| `infra:` | Configuração de infra (Vercel, Supabase, etc) |
| `docs:` | Atualização de documentação |
| `content:` | Alteração de copy/conteúdo |

Exemplos:
```
feat: adicionar autenticação Supabase no wizard
fix: corrigir posicionamento do dropdown de ativos no mobile
infra: restringir CORS nas Edge Functions
style: ajustar espaçamento do passo 3 no mobile
docs: registrar decisão sobre CSP via header HTTP
```
