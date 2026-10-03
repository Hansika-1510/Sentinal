from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.incident_memory import IncidentMemory
from app.models.incident import Incident
from app.schemas.postmortem import IncidentMemoryRead
from app.integrations.llm import get_embedding_provider, cosine_similarity
from app.core.logging import logger


class IncidentMemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def store_incident_memory(
        self,
        incident_id: str,
        summary: str,
        symptoms: str,
        rca: str,
        resolution: str,
        outcome: str
    ) -> IncidentMemory:
        """Embeds and saves an incident into historical memory."""
        combined_text = f"{summary}\nSymptoms: {symptoms}\nRCA: {rca}\nResolution: {resolution}"
        embedding_vec = await self.embedding_provider.get_embedding(combined_text)

        # Check if already exists for this incident
        existing = self.db.scalars(select(IncidentMemory).where(IncidentMemory.incident_id == incident_id)).first()
        if existing:
            existing.summary = summary
            existing.symptoms = symptoms
            existing.rca = rca
            existing.resolution = resolution
            existing.outcome = outcome
            existing.embedding = embedding_vec
            self.db.commit()
            self.db.refresh(existing)
            return existing

        memory = IncidentMemory(
            incident_id=incident_id,
            summary=summary,
            symptoms=symptoms,
            rca=rca,
            resolution=resolution,
            outcome=outcome,
            embedding=embedding_vec
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        logger.info(f"Incident {incident_id} saved to IncidentMemory with {len(embedding_vec)}-dim vector.")
        return memory

    async def find_similar_incidents(self, query_text: str, top_k: int = 3, threshold: float = 0.1) -> List[IncidentMemoryRead]:
        """Performs semantic similarity search across stored historical incidents."""
        query_vec = await self.embedding_provider.get_embedding(query_text)
        all_memories = list(self.db.scalars(select(IncidentMemory)).all())

        scored: List[tuple[IncidentMemory, float]] = []
        for mem in all_memories:
            sim = cosine_similarity(query_vec, mem.embedding or [])
            if sim >= threshold:
                scored.append((mem, sim))

        # Sort by highest similarity
        scored.sort(key=lambda x: x[1], reverse=True)

        results: List[IncidentMemoryRead] = []
        for mem, score in scored[:top_k]:
            results.append(IncidentMemoryRead(
                id=mem.id,
                incident_id=mem.incident_id,
                summary=mem.summary,
                symptoms=mem.symptoms,
                rca=mem.rca,
                resolution=mem.resolution,
                outcome=mem.outcome,
                similarity_score=round(score, 4),
                created_at=mem.created_at
            ))
        return results
