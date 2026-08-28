from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..models.investigation import Investigation
from ..models.graph import EvidenceNode, EvidenceEdge
from ..models.finding import Finding
from ..models.iocs import IOC
import hashlib

class EvidenceGraphService:
    @staticmethod
    async def build_graph(investigation_id: str, session: AsyncSession):
        inv = await session.get(Investigation, investigation_id)
        if not inv: return

        findings_res = await session.execute(select(Finding).where(Finding.investigation_id == investigation_id))
        findings = findings_res.scalars().all()
        
        from ..models.agent import SandboxSession
        sb_res = await session.execute(select(SandboxSession).where(SandboxSession.investigation_id == investigation_id).order_by(SandboxSession.created_at.desc()))
        sandbox_sessions = sb_res.scalars().all()

        nodes = {} # hash -> node instance
        edges = [] # list of (source_hash, target_hash, relation, conf, src)
        
        def add_node(node_type, label, value, source, conf=1.0, metadata=None):
            h = hashlib.sha256(f"{investigation_id}_{node_type}_{value}".encode()).hexdigest()
            if h not in nodes:
                nodes[h] = EvidenceNode(
                    investigation_id=investigation_id,
                    node_type=node_type,
                    label=label,
                    value_hash=h,
                    safe_display_value=value,
                    source=source,
                    confidence=conf,
                    metadata_json=metadata
                )
            return h

        # Base Investigation Node
        inv_hash = add_node("INVESTIGATION", "Investigation", inv.display_id, "System")
        
        # Target URL Node
        url_hash = add_node("URL", "Target URL", inv.target, "User_Input")
        edges.append((inv_hash, url_hash, "ANALYZES", 1.0, "System"))
        
        # Findings to Nodes & Edges
        for f in findings:
            f_hash = add_node("FINDING", f.title, f.id, f.agent, f.confidence)
            edges.append((f_hash, url_hash, "DETECTED_ON", f.confidence, f.agent))
            
            # Map specific behavior agents to pseudo-nodes
            if f.category == "credential_harvesting":
                login_hash = add_node("PAGE", "Suspicious Page", "Fake Login", f.agent, f.confidence)
                edges.append((url_hash, login_hash, "CONTAINS", f.confidence, f.agent))
                pw_hash = add_node("INPUT", "Input Field", "Password Field", f.agent, f.confidence)
                edges.append((login_hash, pw_hash, "CONTAINS", f.confidence, f.agent))
                
                if "External Credential Submission" in f.title:
                    ext_hash = add_node("DOMAIN", "External Domain", "External POST Target", f.agent, f.confidence)
                    edges.append((pw_hash, ext_hash, "SUBMITS_TO", f.confidence, f.agent))

        # Sandbox Events
        if sandbox_sessions and sandbox_sessions[0].events:
            for ev in sandbox_sessions[0].events:
                if ev["event_type"] == "REDIRECT":
                    url = ev["metadata"].get("url", "")
                    r_hash = add_node("URL", "Redirect", url, "Sandbox")
                    edges.append((url_hash, r_hash, "REDIRECTS_TO", 1.0, "Sandbox"))
                elif ev["event_type"] == "DOWNLOAD_DETECTED":
                    d_hash = add_node("DOWNLOAD", "File Download", ev["metadata"].get("filename", "unknown"), "Sandbox")
                    edges.append((url_hash, d_hash, "TRIGGERS", 1.0, "Sandbox"))

        # IOCs
        iocs_res = await session.execute(select(IOC).where(IOC.investigation_id == investigation_id))
        iocs = iocs_res.scalars().all()
        for ioc in iocs:
            ioc_hash = add_node("THREAT_INTEL", "Threat IOC", ioc.value, ioc.source_agent, ioc.confidence)
            edges.append((ioc_hash, url_hash, "FLAGS", ioc.confidence, ioc.source_agent))

        # Idempotent DB insert (simple flush to get IDs)
        # Avoid dupes
        existing_nodes = (await session.execute(select(EvidenceNode).where(EvidenceNode.investigation_id == investigation_id))).scalars().all()
        existing_hashes = {n.value_hash: n.id for n in existing_nodes}
        
        new_nodes = []
        for h, node in nodes.items():
            if h not in existing_hashes:
                new_nodes.append(node)
                
        if new_nodes:
            session.add_all(new_nodes)
            await session.commit()
            
            for n in new_nodes:
                existing_hashes[n.value_hash] = n.id
                
        # Existing edges (to avoid dupes)
        existing_edges = (await session.execute(select(EvidenceEdge).where(EvidenceEdge.investigation_id == investigation_id))).scalars().all()
        edge_set = {(e.source_node_id, e.target_node_id, e.relationship_type) for e in existing_edges}
        
        new_edges = []
        for s_hash, t_hash, rel, conf, src in edges:
            s_id = existing_hashes.get(s_hash)
            t_id = existing_hashes.get(t_hash)
            if s_id and t_id and (s_id, t_id, rel) not in edge_set:
                new_edges.append(EvidenceEdge(
                    investigation_id=investigation_id,
                    source_node_id=s_id,
                    target_node_id=t_id,
                    relationship_type=rel,
                    confidence=conf,
                    source=src
                ))
                edge_set.add((s_id, t_id, rel))
                
        if new_edges:
            session.add_all(new_edges)
            await session.commit()
