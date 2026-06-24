import { getApiStatus } from "@/lib/api";
import { listDocuments, listPageTables, listPageTextBlocks, listPages } from "@/lib/api";
import { DocumentList } from "@/components/document-list";
import { PageViewer } from "@/components/page-viewer";
import { UploadForm } from "@/components/upload-form";

const pipeline = [
  "Upload",
  "Render",
  "Parse",
  "Retrieve",
  "Ask",
  "Cite",
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

export default function Home() {
  const documentsPromise = listDocuments().catch(() => []);

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">V0 Foundation</p>
          <h1>MAGE-Doc</h1>
          <p className="subtitle">
            Multimodal Agentic RAG for long-PDF reasoning with evidence graphs.
          </p>
        </div>
        <div className="phase-badge">Phase 4</div>
      </section>

      <section className="workspace">
        <aside className="panel pipeline-panel">
          <h2>V0 Pipeline</h2>
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
              <h2>Upload and track long PDFs.</h2>
            </div>
            <span className="stage-label">Phase 4</span>
          </div>
          <div className="workspace-grid">
            <UploadForm />
            <DocumentListAsync documentsPromise={documentsPromise} />
          </div>
          <PageViewerAsync documentsPromise={documentsPromise} />
        </section>

        <aside className="panel system-panel">
          <h2>System Status</h2>
          <StatusPanel />
          <div className="note">
            <p>Current scope</p>
            <strong>Text and table evidence overlay</strong>
          </div>
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

async function PageViewerAsync({
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
    <PageViewer
      document={activeDocument}
      pages={pages}
      textBlocks={textBlocks}
      tables={tables}
    />
  );
}
