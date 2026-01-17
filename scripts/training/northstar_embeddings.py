#!/usr/bin/env python3
"""
NORTHSTAR Artist Embeddings - Local Training Pipeline

ChromaDB + Local Embedding Model
Sovereign knowledge base for the 22 NORTHSTAR Masters

Usage:
    # First time - build the database
    python northstar_embeddings.py --build

    # Query the knowledge
    python northstar_embeddings.py --query "How did Tesla approach creativity?"

    # Add new artist
    python northstar_embeddings.py --add-artist path/to/artist.json

    # List all artists
    python northstar_embeddings.py --list
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# =============================================================================
# CONFIGURATION
# =============================================================================

CHROMA_DB_PATH = PROJECT_ROOT / "data" / "northstar_vectors"
ARTIST_AGENTS_PATH = PROJECT_ROOT / "scripts" / "agents" / "ARTIST_AGENTS.json"
TRAINING_DATA_PATH = PROJECT_ROOT / "knowledge_base" / "training_data.json"

# Local embedding model - runs entirely on device
# all-MiniLM-L6-v2 is fast and good quality
# Can upgrade to all-mpnet-base-v2 for better quality (slower)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Collection names
COLLECTION_MASTERS = "northstar_masters"
COLLECTION_QUOTES = "verified_quotes"
COLLECTION_TECHNIQUES = "techniques"

# =============================================================================
# EMBEDDING ENGINE
# =============================================================================

class NorthstarEmbeddings:
    """
    Local-first embedding system for NORTHSTAR Masters.
    All data stays on device. No external API calls.
    """

    def __init__(self):
        print("Initializing NORTHSTAR Embeddings (Local-First)...")

        # Ensure data directory exists
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)  # No telemetry
        )

        # Load local embedding model
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print("✓ Model loaded (running locally)")

        # Get or create collections
        self.masters = self.client.get_or_create_collection(
            name=COLLECTION_MASTERS,
            metadata={"description": "22 NORTHSTAR Masters - Artist as the Art"}
        )
        self.quotes = self.client.get_or_create_collection(
            name=COLLECTION_QUOTES,
            metadata={"description": "Verified quotes with sources"}
        )
        self.techniques = self.client.get_or_create_collection(
            name=COLLECTION_TECHNIQUES,
            metadata={"description": "Teachable techniques and methods"}
        )

    def _embed(self, texts):
        """Create embeddings using local model."""
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts).tolist()

    def build_from_artists(self):
        """
        Build the vector database from ARTIST_AGENTS.json

        Creates embeddings for:
        - Master profiles (who they were, how they lived)
        - Verified quotes (with sources)
        - Techniques (what can be learned)
        - Philosophies (how they thought)
        """
        print("\n" + "="*60)
        print("BUILDING NORTHSTAR KNOWLEDGE BASE")
        print("="*60)

        # Load artist data
        if not ARTIST_AGENTS_PATH.exists():
            print(f"ERROR: {ARTIST_AGENTS_PATH} not found")
            return False

        with open(ARTIST_AGENTS_PATH) as f:
            data = json.load(f)

        # Process all agents (feminine + masculine)
        all_agents = data.get("agents", {}).get("feminine", []) + \
                     data.get("agents", {}).get("masculine", [])

        print(f"\nProcessing {len(all_agents)} NORTHSTAR Masters...")

        master_docs = []
        master_metas = []
        master_ids = []

        quote_docs = []
        quote_metas = []
        quote_ids = []

        tech_docs = []
        tech_metas = []
        tech_ids = []

        for agent in all_agents:
            agent_id = agent.get("id", "unknown")
            name = agent.get("name", "Unknown")
            era = agent.get("era", "Unknown")
            domain = agent.get("domain", "")
            polarity = agent.get("polarity", "")

            print(f"  → {name} ({era})")

            # === MASTER PROFILE ===
            # Create a rich narrative about who they were
            profile_text = f"""
{name} ({era}) - {domain}

POLARITY: {polarity}

HOW THEY LIVED:
{name} was known for their work in {domain}.

THEIR PHILOSOPHIES:
{chr(10).join('• ' + p for p in agent.get('philosophies', []))}

WHAT THEY CREATED:
Their techniques included:
{chr(10).join('• ' + t for t in agent.get('techniques', []))}

WHAT CAN BE LEARNED:
{chr(10).join('• ' + tp for tp in agent.get('teaching_points', []))}
            """.strip()

            master_docs.append(profile_text)
            master_metas.append({
                "id": agent_id,
                "name": name,
                "era": era,
                "domain": domain,
                "polarity": polarity,
                "type": "master_profile"
            })
            master_ids.append(f"master_{agent_id}")

            # === VERIFIED QUOTES ===
            for i, quote_data in enumerate(agent.get("verified_quotes", [])):
                quote_text = quote_data.get("quote", "")
                source = quote_data.get("source", "Unknown")
                year = quote_data.get("year", "Unknown")

                quote_doc = f'"{quote_text}" — {name}, {source} ({year})'

                quote_docs.append(quote_doc)
                quote_metas.append({
                    "master_id": agent_id,
                    "master_name": name,
                    "source": source,
                    "year": year,
                    "type": "verified_quote"
                })
                quote_ids.append(f"quote_{agent_id}_{i}")

            # === TECHNIQUES ===
            for i, technique in enumerate(agent.get("techniques", [])):
                tech_doc = f"{name}'s technique: {technique}"

                tech_docs.append(tech_doc)
                tech_metas.append({
                    "master_id": agent_id,
                    "master_name": name,
                    "domain": domain,
                    "type": "technique"
                })
                tech_ids.append(f"tech_{agent_id}_{i}")

        # === EMBED AND STORE ===
        print("\nCreating embeddings (local model)...")

        # Masters
        if master_docs:
            print(f"  Embedding {len(master_docs)} master profiles...")
            master_embeddings = self._embed(master_docs)
            self.masters.upsert(
                ids=master_ids,
                embeddings=master_embeddings,
                documents=master_docs,
                metadatas=master_metas
            )

        # Quotes
        if quote_docs:
            print(f"  Embedding {len(quote_docs)} verified quotes...")
            quote_embeddings = self._embed(quote_docs)
            self.quotes.upsert(
                ids=quote_ids,
                embeddings=quote_embeddings,
                documents=quote_docs,
                metadatas=quote_metas
            )

        # Techniques
        if tech_docs:
            print(f"  Embedding {len(tech_docs)} techniques...")
            tech_embeddings = self._embed(tech_docs)
            self.techniques.upsert(
                ids=tech_ids,
                embeddings=tech_embeddings,
                documents=tech_docs,
                metadatas=tech_metas
            )

        print("\n" + "="*60)
        print("✓ KNOWLEDGE BASE BUILT")
        print(f"  Masters: {self.masters.count()}")
        print(f"  Quotes: {self.quotes.count()}")
        print(f"  Techniques: {self.techniques.count()}")
        print(f"  Storage: {CHROMA_DB_PATH}")
        print("="*60)

        return True

    def query(self, question, n_results=5, collection="all"):
        """
        Query the NORTHSTAR knowledge base.

        Args:
            question: Natural language question
            n_results: Number of results per collection
            collection: "all", "masters", "quotes", or "techniques"

        Returns:
            List of relevant results with metadata
        """
        print(f"\nQuerying: {question}")
        print("-" * 40)

        # Embed the question
        query_embedding = self._embed(question)

        results = []

        # Query relevant collections
        if collection in ["all", "masters"]:
            master_results = self.masters.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            for i, doc in enumerate(master_results["documents"][0]):
                results.append({
                    "type": "master",
                    "content": doc,
                    "metadata": master_results["metadatas"][0][i],
                    "distance": master_results["distances"][0][i]
                })

        if collection in ["all", "quotes"]:
            quote_results = self.quotes.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            for i, doc in enumerate(quote_results["documents"][0]):
                results.append({
                    "type": "quote",
                    "content": doc,
                    "metadata": quote_results["metadatas"][0][i],
                    "distance": quote_results["distances"][0][i]
                })

        if collection in ["all", "techniques"]:
            tech_results = self.techniques.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            for i, doc in enumerate(tech_results["documents"][0]):
                results.append({
                    "type": "technique",
                    "content": doc,
                    "metadata": tech_results["metadatas"][0][i],
                    "distance": tech_results["distances"][0][i]
                })

        # Sort by relevance (lower distance = more relevant)
        results.sort(key=lambda x: x["distance"])

        return results[:n_results * 2]  # Return top results across all

    def add_artist(self, artist_data):
        """
        Add a new artist to the knowledge base.

        Args:
            artist_data: Dict with artist profile matching schema
        """
        agent_id = artist_data.get("id", f"artist_{datetime.now().timestamp()}")
        name = artist_data.get("name", "Unknown Artist")

        print(f"\nAdding artist: {name}")

        # Build profile text
        profile_text = f"""
{name} ({artist_data.get('era', 'Contemporary')}) - {artist_data.get('domain', '')}

POLARITY: {artist_data.get('polarity', 'unknown')}

THEIR PHILOSOPHIES:
{chr(10).join('• ' + p for p in artist_data.get('philosophies', []))}

THEIR TECHNIQUES:
{chr(10).join('• ' + t for t in artist_data.get('techniques', []))}
        """.strip()

        # Embed and store
        embedding = self._embed(profile_text)

        self.masters.upsert(
            ids=[f"master_{agent_id}"],
            embeddings=embedding,
            documents=[profile_text],
            metadatas=[{
                "id": agent_id,
                "name": name,
                "era": artist_data.get("era", ""),
                "domain": artist_data.get("domain", ""),
                "polarity": artist_data.get("polarity", ""),
                "type": "master_profile"
            }]
        )

        print(f"✓ Added {name} to knowledge base")
        return True

    def list_masters(self):
        """List all masters in the knowledge base."""
        results = self.masters.get()

        print("\n" + "="*60)
        print("NORTHSTAR MASTERS IN KNOWLEDGE BASE")
        print("="*60)

        for meta in results["metadatas"]:
            print(f"  {meta.get('name', 'Unknown'):30} | {meta.get('era', ''):15} | {meta.get('domain', '')}")

        print(f"\nTotal: {len(results['metadatas'])} masters")
        return results["metadatas"]

    def get_stats(self):
        """Get knowledge base statistics."""
        return {
            "masters": self.masters.count(),
            "quotes": self.quotes.count(),
            "techniques": self.techniques.count(),
            "storage_path": str(CHROMA_DB_PATH)
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NORTHSTAR Artist Embeddings - Local Training Pipeline"
    )
    parser.add_argument("--build", action="store_true",
                        help="Build/rebuild the vector database from ARTIST_AGENTS.json")
    parser.add_argument("--query", type=str,
                        help="Query the knowledge base")
    parser.add_argument("--add-artist", type=str,
                        help="Add new artist from JSON file")
    parser.add_argument("--list", action="store_true",
                        help="List all masters in knowledge base")
    parser.add_argument("--stats", action="store_true",
                        help="Show database statistics")
    parser.add_argument("-n", type=int, default=5,
                        help="Number of results to return (default: 5)")

    args = parser.parse_args()

    # Initialize
    engine = NorthstarEmbeddings()

    if args.build:
        engine.build_from_artists()

    elif args.query:
        results = engine.query(args.query, n_results=args.n)

        print(f"\nTop {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] ({r['type']}) - Relevance: {1 - r['distance']:.2%}")
            print(f"    {r['content'][:200]}...")
            print()

    elif args.add_artist:
        with open(args.add_artist) as f:
            artist_data = json.load(f)
        engine.add_artist(artist_data)

    elif args.list:
        engine.list_masters()

    elif args.stats:
        stats = engine.get_stats()
        print("\nKnowledge Base Statistics:")
        print(f"  Masters: {stats['masters']}")
        print(f"  Quotes: {stats['quotes']}")
        print(f"  Techniques: {stats['techniques']}")
        print(f"  Storage: {stats['storage_path']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
