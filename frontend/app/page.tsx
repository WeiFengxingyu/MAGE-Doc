import { getApiStatus, getV2Status } from "@/lib/api";
import { listDocuments, listPageTables, listPageTextBlocks, listPages } from "@/lib/api";
import { DocumentList } from "@/components/document-list";
import { DocumentWorkbench } from "@/components/document-workbench";
import { UploadForm } from "@/components/upload-form";

const pipeline = [
  "Upload",
  "Prepare",
  "Evidence",
  "Ask",
  "Repair",
  "Export",
];

async function StatusPanel() {
  try {
    const status = await getApiStatus();
    return (
      <div className="status status-ok">
        <span className="status-dot" />
        <div>
          <p className="status-label">Backend online</p>
          <p className="status-detail">
            {status.service} · v{status.version} · {status.environment}
          </p>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="status status-warn">
        <span className="status-dot" />
        <div>
          <p className="status-label">Backend unavailable</p>
          <p className="status-detail">
            Start the FastAPI service to enable live document workflows.
          </p>
        </div>
      </div>
    );
  }
}

async function V2CapabilityPanel() {
  try {
    const status = await getV2Status();
    return (
      <div className="v2-capability-panel">
        <div className="capability-heading">
          <div>
            <p className="eyebrow">V2 Platform</p>
            <h3>{status.batch}</h3>
          </div>
          <span>{status.capabilities.length}/8</span>
        </div>
        <div className="capability-grid">
          {status.capabilities.map((capability) => (
            <div className="capability-item" key={capability.name}>
              <div>
                <strong>{capability.name}</strong>
                <span>{capability.phase}</span>
              </div>
              <p>{capability.evidence}</p>
            </div>
          ))}
        </div>
      </div>
    );
  } catch {
    return null;
  }
}

export default function Home() {
  const documentsPromise = listDocuments().catch(() => []);

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Product-grade Agentic RAG Demo</p>
          <h1>MAGE-Doc</h1>
          <p className="subtitle">
            Multimodal Agentic RAG for trusted long-PDF QA, self-correction, and
            citation-backed report export.
          </p>
        </div>
        <div className="phase-badge">V3 + Product Demo</div>
      </section>

      <section className="workspace">
        <aside className="panel pipeline-panel">
          <h2>Core Pipeline</h2>
          <div className="steps">
            {pipeline.map((step, index) => (
              <div className="step" key={step}>
                <span>{index + 1}</span>
                <p>{step}</p>
              </div>
            ))}
          </div>
        </aside>

        <section className="panel document-panel">
          <div className="workspace-header">
            <div>
              <p className="eyebrow">Document Workspace</p>
              <h2>Run trusted document QA.</h2>
            </div>
            <span className="stage-label">Product Demo</span>
          </div>
          <div className="workspace-grid">
            <UploadForm />
            <DocumentListAsync documentsPromise={documentsPromise} />
          </div>
          <DocumentWorkbenchAsync documentsPromise={documentsPromise} />
        </section>

        <aside className="panel system-panel">
          <h2>System Status</h2>
          <StatusPanel />
          <div className="note">
            <p>Current scope</p>
            <strong>V3 repair trace, evidence graph, report export</strong>
          </div>
          <V2CapabilityPanel />
        </aside>
      </section>
    </main>
  );
}

async function DocumentListAsync({
  documentsPromise,
}: {
  documentsPromise: Promise<Awaited<ReturnType<typeof listDocuments>>>;
}) {
  const documents = await documentsPromise;
  return <DocumentList documents={documents} />;
}

async function DocumentWorkbenchAsync({
  documentsPromise,
}: {
  documentsPromise: Promise<Awaited<ReturnType<typeof listDocuments>>>;
}) {
  const documents = await documentsPromise;
  const activeDocument = documents[0] ?? null;
  const pages = activeDocument ? await listPages(activeDocument.id).catch(() => []) : [];
  const firstPage = pages[0] ?? null;
  const textBlocks =
    activeDocument && firstPage
      ? await listPageTextBlocks(activeDocument.id, firstPage.page_number).catch(() => [])
      : [];
  const tables =
    activeDocument && firstPage
      ? await listPageTables(activeDocument.id, firstPage.page_number).catch(() => [])
      : [];
  return (
    <DocumentWorkbench
      document={activeDocument}
      pages={pages}
      textBlocks={textBlocks}
      tables={tables}
    />
  );
}
