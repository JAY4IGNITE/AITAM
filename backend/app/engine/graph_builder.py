import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.investigation import Investigation
from ..models.graph import EvidenceNode, EvidenceEdge
from ..models.finding import Finding
from ..models.iocs import IOC
from ..models.agent import SandboxSession

class EvidenceGraphService:
    @staticmethod
    async def build_graph(investigation_id: str, session: AsyncSession):
        inv = await session.get(Investigation, investigation_id)
        if not inv: 
            return

        findings_res = await session.execute(select(Finding).where(Finding.investigation_id == investigation_id))
        findings = findings_res.scalars().all()
        
        sb_res = await session.execute(select(SandboxSession).where(SandboxSession.investigation_id == investigation_id).order_by(SandboxSession.created_at.desc()))
        sandbox_sessions = sb_res.scalars().all()

        iocs_res = await session.execute(select(IOC).where(IOC.investigation_id == investigation_id))
        iocs = iocs_res.scalars().all()

        nodes = {}  # hash -> node instance
        edges = []  # list of (source_hash, target_hash, relation, conf, src)
        
        def add_node(node_type, label, value, source, conf=1.0, metadata=None):
            h = hashlib.sha256(f"{investigation_id}_{node_type}_{value}".encode()).hexdigest()
            if h not in nodes:
                nodes[h] = EvidenceNode(
                    investigation_id=investigation_id,
                    node_type=node_type,
                    label=label,
                    value_hash=h,
                    safe_display_value=value[:80],
                    source=source,
                    confidence=conf,
                    metadata_json=metadata
                )
            return h

        # 1. Base Investigation Root Node
        inv_hash = add_node("INVESTIGATION", f"Case {inv.display_id}", inv.display_id, "System")
        
        # 2. Target Node
        target_hash = add_node(inv.input_type.value, f"Target {inv.input_type.value}", inv.target, "User_Input")
        edges.append((inv_hash, target_hash, "ANALYZES", 1.0, "System"))
        
        # 3. Dynamic Findings Nodes & Relationships
        for f in findings:
            f_hash = add_node("FINDING", f.title[:30], f.title, f.agent, f.confidence or 0.95)
            edges.append((target_hash, f_hash, "EXHIBITS", f.confidence or 0.95, f.agent))
            
            if f.category in ["credential_harvesting", "email_spoofing"]:
                cat_hash = add_node("TECHNIQUE", "Credential Lure", "T1056 Input Capture", f.agent, 0.95)
                edges.append((f_hash, cat_hash, "MAPS_TO", 0.95, f.agent))
            elif f.category in ["evasion", "quishing"]:
                cat_hash = add_node("TECHNIQUE", "Defense Evasion", "T1036 Obfuscation", f.agent, 0.95)
                edges.append((f_hash, cat_hash, "MAPS_TO", 0.95, f.agent))

        # 4. IoC Nodes
        for ioc in iocs:
            ioc_hash = add_node("IOC", f"IoC: {ioc.ioc_type}", ioc.value, ioc.source_agent, ioc.confidence or 0.95)
            edges.append((target_hash, ioc_hash, "CONTAINS_IOC", ioc.confidence or 0.95, ioc.source_agent))

        # 5. Sandbox Detonation Node & Events
        if sandbox_sessions and sandbox_sessions[0].status.value == "COMPLETED":
            sb = sandbox_sessions[0]
            sb_hash = add_node("SANDBOX", "Browser Detonation", f"Headless {sb.browser_type}", "SandboxAgent")
            edges.append((target_hash, sb_hash, "DETONATED_IN", 1.0, "SandboxAgent"))
            
            if sb.events:
                for ev in sb.events[:5]:
                    ev_type = ev.get("event_type", "EVENT")
                    ev_url = ev.get("metadata", {}).get("url") or ev.get("metadata", {}).get("target") or ev_type
                    ev_hash = add_node("TELEMETRY", ev_type, ev_url[:40], "Sandbox")
                    edges.append((sb_hash, ev_hash, "CAPTURED", 1.0, "Sandbox"))

        # Clear and insert fresh graph nodes & edges
        await session.execute(EvidenceEdge.__table__.delete().where(EvidenceEdge.investigation_id == investigation_id))
        await session.execute(EvidenceNode.__table__.delete().where(EvidenceNode.investigation_id == investigation_id))
        await session.commit()

        if nodes:
            session.add_all(list(nodes.values()))
            await session.commit()
            
            # Map hashes to newly assigned DB IDs
            existing_nodes = (await session.execute(
                select(EvidenceNode).where(EvidenceNode.investigation_id == investigation_id)
            )).scalars().all()
            hash_to_id = {n.value_hash: n.id for n in existing_nodes}

            db_edges = []
            for s_hash, t_hash, rel, conf, src in edges:
                s_id = hash_to_id.get(s_hash)
                t_id = hash_to_id.get(t_hash)
                if s_id and t_id:
                    db_edges.append(EvidenceEdge(
                        investigation_id=investigation_id,
                        source_node_id=s_id,
                        target_node_id=t_id,
                        relationship_type=rel,
                        confidence=conf,
                        source=src
                    ))
            if db_edges:
                session.add_all(db_edges)
                await session.commit()
