BCBSKS Demo 2 Proposal
Based on the meeting/request, we should target a tight, rep-focused BCBSKS
call-center demo using watsonx Orchestrate + watsonx.ai. The use case should
feel like a real payer service scenario, not a generic chatbot or enterprise search
demo. A rep should be able to ask a natural-language service or policy question
against SharePoint-based knowledge content, receive a grounded answer with
citations, then request a plain-language talk track for use on the call, and finally
generate a call summary or next-step recommendation.
The business purpose is to show how BCBSKS could modernize or replace
AskOS with a governed rep-assist workflow. The key is to demonstrate more
than search or basic RAG. If we show only document Q&A over SharePoint,
BCBSKS may reasonably ask why they would not simply use a tool like Glean or
Coveo. Our differentiation should therefore be clear: grounded retrieval + cited
answer + plain-language rep assist + workflow-oriented next step.
Goals: The demo could (ideally, should) prove 4 things in one short flow:
1. The rep can ask a real operational question in plain language.
2. The assistant retrieves from approved SharePoint knowledge and gives
a grounded answer with citations/source visibility.
3. The assistant can turn internal policy language into a rep-friendly/member-
friendly talk track.
4. The assistant can help with the next step, such as drafting a call summary,
follow-up note, or suggested action.
Suggested Demo flow
Use one end-to-end scenario, such as a prior auth / benefits / policy
clarification question.
Scene 1: Ask and retrieve
Rep asks a realistic service question.
System retrieves relevant SharePoint content and returns a concise answer with
source references.
Sample prompt
“A member is asking whether outpatient imaging for this condition requires prior
authorization under the current policy.”
What the system can do (examples)
 Search approved knowledge sources
 Retrieve relevant policy / FAQ / procedure document
 Generate concise answer
 Show citations and source links
 Display document date / version where possible
Scene 2: Add nuance
Rep asks a follow-up such as line-of-business difference, exception, or what
changed recently.
System compares/synthesizes the relevant documents and stays grounded.
Sample prompt
“Is that different for commercial versus Medicare Advantage, and has anything
changed recently?”
What the system can do (examples)
 Compare multiple sources
 Distinguish by line of business if supported by documents
 Indicate changes or differences
 Avoid overclaiming if source content is unclear
 Highlight latest approved content
Scene 3: Translate for use on the call
Rep asks for a simpler version to say to the member.
System rewrites the answer into plain-language talk track without inventing
unsupported details.
Sample prompt
“Rewrite that in simple language I can say to the member on the phone.”
What the system can do (examples)
 Convert policy language into plain speech
 Preserve meaning from grounded sources
 Avoid inventing benefit details
 Keep answer short and rep-usable
Scene 4: Help move the work forward
Rep asks for a call summary / case note / next-step suggestion.
System drafts the summary and suggests the appropriate follow-up or escalation
path.
Sample prompt
“Create a call summary and suggest next steps.”
What the system can do (examples)
 Draft CRM/case summary
 Suggest escalation or follow-up path
 Recommend knowledge article reference
 Prepare rep notes for disposition
 Potentially create a task / workflow handoff in a future-state vision
Some key metrics for demo
 SharePoint / approved knowledge source grounding
 citations or source links/snippets
 document date/version awareness where possible
 clear behavior when answer is ambiguous or unsupported
 rep-friendly output, not generic chatbot text
 one next-step action artifact such as call notes, summary, or escalation
recommendation


Architecture digram, rag+milvus/elastic search +docling+watsonx orchestrate2
flowchart LR
%% =========================
%% Nodes
%% =========================
A[SharePoint Knowledge Sources<br/>Policies / FAQs / SOPs / Procedures]
B[Docling Ingestion Layer<br/>OCR + Parsing + Structure Extraction]
C[Chunking + Metadata Enrichment<br/>LOB / Effective Date / Version / Source URL]
D1[Dense Embeddings]
D2[Sparse Indexing]
E1[Milvus Vector Store]
E2[Elasticsearch BM25 Index]
F[Hybrid Retriever]
G[Re-ranking Layer<br/>Cross Encoder / Semantic Ranker]
H[Grounded Context Builder<br/>Top-k Chunks + Citation Metadata]
I[watsonx.ai Foundation Model]
J[watsonx Orchestrate Rep UI]
K1[Grounded Answer with Citations]
K2[Plain Language Talk Track]
K3[Call Summary / CRM Note]
K4[Next Step Recommendation]
L[Governance Layer<br/>Audit / Prompt Guardrails / Logging]
M[Future Workflow Integration<br/>CRM / Case System / Escalation]
%% =========================
%% Flow
%% =========================
A --> B
B --> C
C --> D1
C --> D2
D1 --> E1
D2 --> E2
E1 --> F
E2 --> F
F --> G
G --> H
J --> F
H --> I
I --> K1
I --> K2
I --> K3
I --> K4
L --> F
L --> I
K3 --> M
K4 --> M
%% =========================
%% Subgraphs
%% =========================
subgraph Knowledge_Ingestion
A
B
C
end
subgraph Retrieval_Layer
D1
D2
E1
E2
F
G
H
end
subgraph AI_Orchestration
J
I
K1
K2
K3
K4
end
subgraph Enterprise_Control
L
M
end
%% =========================
%% Styles
%% =========================
style A fill:#dbeafe,stroke:#2563eb,color:#111827,stroke-width:2px
style B fill:#e0f2fe,stroke:#0284c7,color:#111827,stroke-width:2px
style C fill:#e0f2fe,stroke:#0284c7,color:#111827,stroke-width:2px
style D1 fill:#dcfce7,stroke:#16a34a,color:#111827,stroke-width:2px
style D2 fill:#dcfce7,stroke:#16a34a,color:#111827,stroke-width:2px
style E1 fill:#bbf7d0,stroke:#15803d,color:#111827,stroke-width:2px
style E2 fill:#bbf7d0,stroke:#15803d,color:#111827,stroke-width:2px
style F fill:#fef3c7,stroke:#d97706,color:#111827,stroke-width:2px
style G fill:#fde68a,stroke:#ca8a04,color:#111827,stroke-width:2px
style H fill:#fde68a,stroke:#ca8a04,color:#111827,stroke-width:2px
style I fill:#ede9fe,stroke:#7c3aed,color:#111827,stroke-width:2px
style J fill:#ede9fe,stroke:#7c3aed,color:#111827,stroke-width:2px
style K1 fill:#fce7f3,stroke:#db2777,color:#111827,stroke-width:2px
style K2 fill:#fce7f3,stroke:#db2777,color:#111827,stroke-width:2px
style K3 fill:#fce7f3,stroke:#db2777,color:#111827,stroke-width:2px
style K4 fill:#fce7f3,stroke:#db2777,color:#111827,stroke-width:2px
style L fill:#fee2e2,stroke:#dc2626,color:#111827,stroke-width:2px
style M fill:#fee2e2,stroke:#dc2626,color:#111827,stroke-width:2px