// Hero + visualização do fluxo de 5 passos — deixa claro o que o sistema faz.
import { ReactNode } from "react";

const Arrow = () => (
  <svg className="arrow" width="22" height="22" viewBox="0 0 24 24" fill="none">
    <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2.2"
      strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

interface Step {
  title: string;
  desc: string;
  icon: ReactNode;
}

const I = {
  data: (
    <svg viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="5" rx="8" ry="3" stroke="currentColor" strokeWidth="1.8" /><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" stroke="currentColor" strokeWidth="1.8" /></svg>
  ),
  refresh: (
    <svg viewBox="0 0 24 24" fill="none"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 4v5h-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  pdf: (
    <svg viewBox="0 0 24 24" fill="none"><path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-5z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /><path d="M8 13h2.5a1.5 1.5 0 0 1 0 3H8v-3zM8 16v2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
  ),
  mail: (
    <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" /><path d="m3 7 9 6 9-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  teams: (
    <svg viewBox="0 0 24 24" fill="none"><path d="M7 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM4 21v-6a3 3 0 0 1 3-3h0a3 3 0 0 1 3 3v6M16 10a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM13 21v-5a3 3 0 0 1 3-3h2a3 3 0 0 1 3 3v3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
};

const STEPS: Step[] = [
  { title: "Dados atualizados", desc: "O Dataflow conclui a atualização e dispara o webhook.", icon: I.data },
  { title: "Automação dispara", desc: "O modelo semântico (dataset) é atualizado automaticamente.", icon: I.refresh },
  { title: "Páginas exportadas", desc: "Cada área vira um PDF — com segmentação e RLS aplicados.", icon: I.pdf },
  { title: "E-mail enviado", desc: "PDF por diretoria entregue por e-mail (anexo ou link).", icon: I.mail },
  { title: "Teams notificado", desc: "O canal de cada área recebe o aviso de entrega.", icon: I.teams },
];

export function Hero() {
  return (
    <section className="hero">
      <span className="eyebrow">🔗 Entrega de BI automatizada</span>
      <h1>
        Do link solto a <span className="grad-text">PDFs por área</span>,
        enviados por e-mail e Teams.
      </h1>
      <p>
        O BI Notify orquestra todo o caminho: escuta a atualização dos dados,
        exporta cada relatório em PDF respeitando o acesso de cada diretoria e
        distribui automaticamente — substituindo fluxos engessados do Power Automate.
      </p>
    </section>
  );
}

export function Pipeline() {
  return (
    <section className="pipeline">
      <div className="pipeline-head">
        <h3>Como funciona</h3>
        <span>5 passos, do dado ao destinatário</span>
      </div>
      <div className="steps">
        {STEPS.map((s, i) => (
          <div className="step" key={s.title}>
            <div className="num">{i + 1}</div>
            <div className="ico">{s.icon}</div>
            <h4>{s.title}</h4>
            <p>{s.desc}</p>
            <Arrow />
          </div>
        ))}
      </div>
    </section>
  );
}
