import { useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  CheckCircle,
  ClockCounterClockwise,
  FileDoc,
  FileMagnifyingGlass,
  Flask,
  GraduationCap,
  Receipt,
  ShieldCheck,
  Sparkle,
  UploadSimple,
  WarningCircle,
  XCircle
} from "@phosphor-icons/react";
import { competitionFindings, contractFindings, scenarios } from "./data";
import type { Finding, Scenario, ScenarioId } from "./types";

const iconMap = {
  competition: GraduationCap,
  contract: Briefcase,
  research: Flask,
  resume: FileDoc,
  reimbursement: Receipt
};

const statusLabel = {
  ready: "可体验",
  preview: "预览",
  planned: "规划中"
};

function SeverityIcon({ severity }: { severity: Finding["severity"] }) {
  if (severity === "blocking") return <XCircle weight="fill" />;
  if (severity === "high") return <WarningCircle weight="fill" />;
  if (severity === "medium") return <WarningCircle weight="duotone" />;
  return <CheckCircle weight="duotone" />;
}

function Home({ onOpen }: { onOpen: (id: ScenarioId) => void }) {
  return (
    <main>
      <section className="hero shell">
        <div className="hero-copy">
          <div className="eyebrow"><ShieldCheck weight="duotone" /> 可验证的材料审查</div>
          <h1>让每一条审查结论，<br />都能回到原文。</h1>
          <p>明鉴读取规则、比对多份材料并定位证据，把容易遗漏的检查变成清晰的整改任务。</p>
          <div className="hero-actions">
            <button className="button primary" onClick={() => onOpen("competition")}>体验竞赛审查 <ArrowRight /></button>
            <button className="button secondary" onClick={() => onOpen("contract")}>查看合同审查</button>
          </div>
        </div>
        <div className="hero-evidence" aria-label="审查结果预览">
          <div className="evidence-topline"><span>审查证据</span><span className="live-label">实时定位</span></div>
          <p className="document-line muted">比赛通知.pdf · 第 3 页</p>
          <blockquote>“每支参赛团队须由 <mark>3至5名</mark> 全日制在校学生组成。”</blockquote>
          <div className="trace-line"><span>报名表</span><span>识别到 2 名成员</span></div>
          <div className="trace-line danger"><span>结论</span><span>阻断项</span></div>
        </div>
      </section>

      <section className="scenario-section shell">
        <div className="section-heading">
          <h2>选择审查场景</h2>
          <p>不同场景使用独立规则和字段，共享同一套解析、证据与整改引擎。</p>
        </div>
        <div className="scenario-grid">
          {scenarios.map((scenario, index) => {
            const Icon = iconMap[scenario.id];
            return (
              <button
                className={`scenario-card card-${index + 1}`}
                key={scenario.id}
                onClick={() => scenario.status !== "planned" && onOpen(scenario.id)}
                disabled={scenario.status === "planned"}
              >
                <div className="scenario-card-head">
                  <Icon size={28} weight="duotone" />
                  <span className={`status ${scenario.status}`}>{statusLabel[scenario.status]}</span>
                </div>
                <h3>{scenario.name}</h3>
                <p>{scenario.description}</p>
                <div className="document-tags">
                  {scenario.documentTypes.slice(0, 3).map((item) => <span key={item}>{item}</span>)}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="method shell">
        <div><span>01</span><h3>读取规则</h3><p>从通知、制度和范本中提取候选规则，由用户确认后执行。</p></div>
        <div><span>02</span><h3>建立事实表</h3><p>把不同文件中的主体、人员、金额和日期对齐到统一字段。</p></div>
        <div><span>03</span><h3>定位证据</h3><p>每条结论保留文件、页码、原文片段和解析置信度。</p></div>
      </section>
    </main>
  );
}

function Workspace({ scenario, onBack }: { scenario: Scenario; onBack: () => void }) {
  const initial = scenario.id === "contract" ? contractFindings : competitionFindings;
  const [findings, setFindings] = useState(initial);
  const [selectedId, setSelectedId] = useState(initial[0]?.id ?? "");
  const [isReviewing, setIsReviewing] = useState(false);
  const [uploadState, setUploadState] = useState("支持 PDF、DOCX、XLSX、TXT、CSV 和 JSON。");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const selected = findings.find((item) => item.id === selectedId) ?? findings[0];
  const openCount = findings.filter((item) => !item.resolved).length;
  const blockingCount = findings.filter((item) => item.severity === "blocking" && !item.resolved).length;
  const completion = useMemo(() => Math.round(((findings.length - openCount) / findings.length) * 100), [findings, openCount]);

  function runReview() {
    setIsReviewing(true);
    window.setTimeout(() => setIsReviewing(false), 1200);
  }

  function toggleResolved(id: string) {
    setFindings((items) => items.map((item) => item.id === id ? { ...item, resolved: !item.resolved } : item));
  }

  async function reviewUploadedFiles(fileList: FileList | null) {
    if (!fileList?.length || (scenario.id !== "competition" && scenario.id !== "contract")) return;
    const form = new FormData();
    form.append("scenario", scenario.id);
    Array.from(fileList).forEach((file) => form.append("files", file));
    setUploadState(`正在解析 ${fileList.length} 个文件...`);
    try {
      const response = await fetch("/api/review/files", { method: "POST", body: form });
      if (!response.ok) throw new Error(`接口返回 ${response.status}`);
      const payload = await response.json();
      const nextFindings: Finding[] = payload.findings.map((item: any) => ({
        id: item.finding_id,
        severity: item.severity,
        title: item.title,
        detail: item.detail,
        source: item.evidence[0]?.file ?? "审查规则",
        page: item.evidence[0]?.page ?? 1,
        excerpt: item.evidence[0]?.excerpt ?? "暂无原文证据",
        suggestion: item.suggestion,
        resolved: false
      }));
      setFindings(nextFindings);
      setSelectedId(nextFindings[0]?.id ?? "");
      const characters = payload.files.reduce((sum: number, file: any) => sum + file.characters, 0);
      setUploadState(`已解析 ${payload.files.length} 个文件，共 ${characters.toLocaleString()} 个字符。`);
    } catch (error) {
      setUploadState(`解析失败：${error instanceof Error ? error.message : "未知错误"}`);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <main className="workspace shell">
      <button className="back-button" onClick={onBack}><ArrowLeft /> 返回场景首页</button>
      <div className="workspace-header">
        <div>
          <span className="workspace-kicker">当前项目</span>
          <h1>{scenario.name}</h1>
          <p>{scenario.id === "contract" ? "设备采购合同审查 · 4份材料" : "AI创新应用挑战赛 · 5份材料"}</p>
        </div>
        <button className="button primary" onClick={runReview} disabled={isReviewing}>
          {isReviewing ? <><Sparkle className="pulse" /> 正在复查</> : <><ClockCounterClockwise /> 重新运行审查</>}
        </button>
      </div>

      <section className="metrics" aria-label="审查统计">
        <div><span>待处理问题</span><strong>{openCount}</strong></div>
        <div><span>阻断项</span><strong className="danger-text">{blockingCount}</strong></div>
        <div><span>材料完整度</span><strong>{scenario.id === "contract" ? "92%" : "78%"}</strong></div>
        <div><span>整改进度</span><strong>{completion}%</strong></div>
      </section>

      <section className="review-layout">
        <aside className="finding-list" aria-label="问题列表">
          <div className="panel-title"><span>审查问题</span><span>{findings.length} 项</span></div>
          {findings.map((finding) => (
            <button
              key={finding.id}
              className={`finding-row ${selectedId === finding.id ? "selected" : ""} ${finding.resolved ? "resolved" : ""}`}
              onClick={() => setSelectedId(finding.id)}
            >
              <span className={`severity-icon ${finding.severity}`}><SeverityIcon severity={finding.severity} /></span>
              <span><strong>{finding.title}</strong><small>{finding.id} · {finding.source}</small></span>
            </button>
          ))}
        </aside>

        <article className="document-preview">
          <div className="panel-title"><span>{selected.source}</span><span>第 {selected.page} 页</span></div>
          <div className="paper">
            <div className="paper-title">{scenario.id === "contract" ? "设备采购合同" : "参赛材料"}</div>
            <div className="paper-lines"><span /><span /><span className="short" /></div>
            <p className="highlighted-text">{selected.excerpt}</p>
            <div className="paper-lines"><span /><span /><span /><span className="short" /></div>
          </div>
        </article>

        <aside className="evidence-panel">
          <div className="panel-title"><span>问题详情</span><span className={`severity-chip ${selected.severity}`}>{selected.severity}</span></div>
          <div className="evidence-body">
            <h2>{selected.title}</h2>
            <p>{selected.detail}</p>
            <div className="evidence-box">
              <span>原文证据</span>
              <blockquote>{selected.excerpt}</blockquote>
              <small>{selected.source} · 第 {selected.page} 页</small>
            </div>
            <div className="suggestion">
              <span>整改建议</span>
              <p>{selected.suggestion}</p>
            </div>
            <button className={`button full ${selected.resolved ? "secondary" : "primary"}`} onClick={() => toggleResolved(selected.id)}>
              {selected.resolved ? "恢复为待处理" : "标记为已解决"}
            </button>
          </div>
        </aside>
      </section>

      <section className="upload-strip">
        <div><UploadSimple size={24} /><span><strong>补充或替换材料</strong><small>{uploadState}</small></span></div>
        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          multiple
          accept=".pdf,.docx,.xlsx,.txt,.md,.csv,.json"
          onChange={(event) => reviewUploadedFiles(event.target.files)}
        />
        <button className="button secondary" onClick={() => fileInputRef.current?.click()}>选择文件</button>
      </section>
    </main>
  );
}

export default function App() {
  const [activeScenario, setActiveScenario] = useState<ScenarioId | null>(null);
  const scenario = scenarios.find((item) => item.id === activeScenario);

  return (
    <div className="app-shell">
      <header className="site-header shell">
        <button className="brand" onClick={() => setActiveScenario(null)}><FileMagnifyingGlass weight="duotone" /><span>明鉴</span></button>
        <nav aria-label="主导航">
          <button onClick={() => setActiveScenario(null)}>场景</button>
          <a href="/DEV_STEPS.md">开发文档</a>
          <a href="https://github.com/PaddlePaddle/PaddleOCR" target="_blank" rel="noreferrer">开源参考</a>
        </nav>
        <span className="local-badge"><ShieldCheck /> 本地优先</span>
      </header>
      {scenario ? <Workspace scenario={scenario} onBack={() => setActiveScenario(null)} /> : <Home onOpen={setActiveScenario} />}
      <footer className="site-footer shell"><span>明鉴 · 多场景材料审查</span><span>结论可追溯，规则可确认，问题可整改</span></footer>
    </div>
  );
}
