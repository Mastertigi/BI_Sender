// Página de documentação: guia completo de configuração ponta a ponta.
export default function Docs() {
  return (
    <div className="doc">
      <h1 className="page-title">Documentação</h1>
      <p className="page-sub">
        Guia completo para configurar o BI Notify e preencher uma regra de
        roteamento — do registro do app no Azure à captura de cada ID.
      </p>

      <div className="toc">
        <a href="#visao">Visão geral</a>
        <a href="#sp">1. Service Principal</a>
        <a href="#perm">2. Permissões</a>
        <a href="#pbi">3. Power BI Admin</a>
        <a href="#ids">4. Onde achar os IDs</a>
        <a href="#rls">5. RLS</a>
        <a href="#teams">6. IDs do Teams</a>
        <a href="#env">7. .env</a>
        <a href="#regra">8. Criar a regra</a>
      </div>

      <h2 id="visao">Visão geral</h2>
      <p>
        O BI Notify escuta a conclusão de um <strong>Dataflow</strong>, atualiza o{" "}
        <strong>modelo semântico</strong>, exporta cada página do relatório em{" "}
        <strong>PDF</strong> (respeitando RLS), cruza com as{" "}
        <strong>Regras de Roteamento</strong> e entrega por <strong>e-mail</strong> e{" "}
        <strong>Teams</strong>. A autenticação é feita por um{" "}
        <strong>Service Principal</strong> (app-only), sem usuário interativo.
      </p>
      <div className="warn-box">
        Pré-requisito: o relatório precisa estar em um workspace com capacidade{" "}
        <strong>Premium, Embedded ou Fabric</strong>. O <code>exportToFile</code> não
        é suportado em Premium Per User (PPU) para relatórios Power BI.
      </div>

      <h2 id="sp">1. Criar o Service Principal (Entra ID / Azure AD)</h2>
      <ol>
        <li>
          Portal do Azure → <strong>Microsoft Entra ID</strong> →{" "}
          <strong>App registrations</strong> → <strong>New registration</strong>.
        </li>
        <li>
          Dê um nome (ex.: <code>bi-notify</code>) e registre. Anote o{" "}
          <strong>Application (client) ID</strong> e o{" "}
          <strong>Directory (tenant) ID</strong> da página Overview.
        </li>
        <li>
          Em <strong>Certificates &amp; secrets</strong>, crie um{" "}
          <strong>Client secret</strong> (dev) e copie o valor na hora. Em
          produção, prefira <strong>certificado</strong>.
        </li>
        <li>
          Crie um <strong>grupo de segurança</strong> no Entra ID e adicione esse
          app como membro — o Power BI libera APIs para o SP via esse grupo.
        </li>
      </ol>
      <p>
        Esses três valores vão para o <code>.env</code>: <code>AZURE_TENANT_ID</code>,{" "}
        <code>AZURE_CLIENT_ID</code>, <code>AZURE_CLIENT_SECRET</code>.
      </p>

      <h2 id="perm">2. Permissões de API (Microsoft Graph)</h2>
      <p>
        Em <strong>API permissions</strong> do app, adicione permissões de{" "}
        <strong>aplicação</strong> (Application, não Delegated) e clique em{" "}
        <strong>Grant admin consent</strong>:
      </p>
      <ul>
        <li>
          <code>Mail.Send</code> — envio de e-mail. Restrinja as caixas permitidas
          com uma <strong>Application Access Policy</strong> (PowerShell Exchange).
        </li>
        <li>
          <code>ChannelMessage.Send</code> (e/ou <code>Group.ReadWrite.All</code>,
          conforme política do tenant) — postar no canal do Teams.
        </li>
      </ul>
      <div className="note">
        Para Power BI, a permissão não é concedida via Graph e sim habilitando o SP
        no portal de administração do Power BI (próximo passo).
      </div>

      <h2 id="pbi">3. Configurar o Power BI</h2>
      <ol>
        <li>
          <strong>Admin Portal</strong> → <strong>Tenant settings</strong> →
          habilite <em>“Service principals can use Power BI APIs”</em> e informe o
          grupo de segurança criado.
        </li>
        <li>
          Habilite <em>“Export reports as PowerPoint presentations or PDF
          documents”</em>.
        </li>
        <li>
          No <strong>workspace</strong> dos relatórios, adicione o Service Principal
          como <strong>Membro/Admin</strong> (Contributor mínimo; <strong>Admin</strong>{" "}
          ou Member é necessário para exportar com RLS).
        </li>
      </ol>

      <h2 id="ids">4. Onde achar cada ID (Workspace, Dataset, Report, Página)</h2>
      <p>
        Abra o relatório no <strong>Power BI Service</strong> (app.powerbi.com). A
        URL tem todos os IDs:
      </p>
      <pre><code>{`app.powerbi.com/groups/{WORKSPACE_ID}/reports/{REPORT_ID}/{PAGE_NAME}`}</code></pre>
      <ul>
        <li>
          <strong>Workspace ID</strong>: o valor após <code>/groups/</code>.
        </li>
        <li>
          <strong>Report ID</strong>: o valor após <code>/reports/</code>.
        </li>
        <li>
          <strong>Page Name</strong>: o último trecho da URL (ex.:{" "}
          <code>ReportSection0a1b2c…</code>) ao navegar até a página desejada. É o{" "}
          <em>nome interno</em> da página, não o título exibido.
        </li>
        <li>
          <strong>Dataset ID</strong>: no workspace, abra as reticências (…) do{" "}
          <em>modelo semântico</em> → <strong>Configurações</strong>; o ID aparece na
          URL após <code>/datasets/</code>.
        </li>
      </ul>
      <div className="note">
        Alternativa via API (com o token do SP):{" "}
        <code>GET /v1.0/myorg/groups/&#123;ws&#125;/reports</code> lista reports e
        datasets; <code>GET …/reports/&#123;id&#125;/pages</code> lista os{" "}
        <code>name</code> (pageName) de cada página.
      </div>

      <h2 id="rls">5. RLS (segurança por linha) — opcional</h2>
      <p>
        Se o relatório usa RLS, informe a identidade efetiva para a exportação:
      </p>
      <ul>
        <li>
          <strong>RLS username</strong>: um UPN/e-mail (ex.:{" "}
          <code>financeiro@empresa.com.br</code>) que represente o usuário daquela área.
        </li>
        <li>
          <strong>RLS roles</strong>: os nomes <em>exatos</em> das funções definidas
          em <strong>Power BI Desktop → Modelagem → Gerenciar funções</strong>.
        </li>
      </ul>
      <p>
        Exportar com RLS exige <strong>write no dataset</strong> + Admin/Member no
        workspace. Relatórios com rótulo de confidencialidade não exportam para PDF
        via Service Principal.
      </p>

      <h2 id="teams">6. IDs do Teams (Team e Channel)</h2>
      <ol>
        <li>
          No Teams, passe o mouse no time → <strong>(…)</strong> →{" "}
          <strong>Obter link para a equipe</strong>. No link, o{" "}
          <strong>Team ID</strong> é o valor de <code>groupId=</code>.
        </li>
        <li>
          No canal → <strong>(…)</strong> → <strong>Obter link para o canal</strong>.
          O <strong>Channel ID</strong> é o trecho no formato{" "}
          <code>19:xxxxxxxx@thread.tacv2</code>.
        </li>
      </ol>
      <div className="note">
        Deixe os campos do Teams vazios se a regra só deve enviar e-mail.
      </div>

      <h2 id="env">7. Configurar o .env</h2>
      <pre><code>{`AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
GRAPH_SENDER_USER_ID=automacao.bi@empresa.com.br
DATABASE_URL=postgresql+psycopg2://bi_notify:bi_notify@db:5432/bi_notify
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
WEBHOOK_SHARED_SECRET=troque-este-valor
CORS_ORIGINS=http://localhost:5173`}</code></pre>
      <p>
        <code>GRAPH_SENDER_USER_ID</code> é a caixa de e-mail (UPN) usada como
        remetente em <code>/users/&#123;id&#125;/sendMail</code>.
      </p>

      <h2 id="regra">8. Criar a regra de roteamento</h2>
      <p>
        Em <strong>Regras de Roteamento → + Nova regra</strong>, preencha os campos
        (cada um traz a dica de onde achar o valor). Resumo do mapeamento:
      </p>
      <ul>
        <li><strong>Diretoria</strong> → nome da área (organização).</li>
        <li><strong>Nome do relatório</strong> → aparece no PDF e no e-mail.</li>
        <li><strong>Workspace / Dataset / Report / Página</strong> → da URL do Service.</li>
        <li><strong>RLS username/roles</strong> → identidade efetiva da exportação.</li>
        <li><strong>Destinatários / CC</strong> → e-mails (vírgula).</li>
        <li><strong>Teams Team/Channel ID</strong> → canal de notificação.</li>
        <li><strong>Anexar PDF</strong> → anexo (ligado) ou link (desligado).</li>
      </ul>
      <p>
        Salve e dispare em <strong>Execuções → Disparo manual</strong> (Workspace ID
        + Dataset ID) para testar a ponta a ponta sem esperar o Dataflow.
      </p>
    </div>
  );
}
