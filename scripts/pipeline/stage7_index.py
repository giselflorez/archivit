"""
DOC-8 Agent Analysis Pipeline - Stage 7: Index

Handles:
- Generate embeddings for semantic search
- Build search index
- Create inverted index for keyword search
- Optimize for retrieval
"""

import json
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import numpy as np

from .models import Source, Segment, ProcessingStatus


class IndexError(Exception):
    """Error during indexing"""
    pass


class Stage7Index:
    """
    Stage 7: Indexing

    Creates searchable indexes for segments:
    - Semantic embeddings for similarity search
    - Inverted index for keyword search
    - Metadata index for filtering
    """

    def __init__(self, index_path: str = None, embedding_model: str = "sentence-transformers"):
        """
        Initialize indexing stage.

        Args:
            index_path: Path to store indexes
            embedding_model: Model to use for embeddings
        """
        self.index_path = Path(index_path or '~/.arc8/search_index').expanduser()
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model = embedding_model
        self.embedder = None
        self._backend = None

        # In-memory indexes
        self.embeddings: Dict[str, np.ndarray] = {}  # segment_id -> embedding
        self.inverted_index: Dict[str, List[Tuple[str, float]]] = {}  # term -> [(segment_id, tf-idf)]
        self.metadata_index: Dict[str, Dict] = {}  # segment_id -> metadata
        self.segment_texts: Dict[str, str] = {}  # segment_id -> text

        self._loaded = False

    def _load_embedder(self):
        """Lazy load embedding model"""
        if self.embedder is not None:
            return

        # Try sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self._backend = "sentence-transformers"
            print("[Stage7] Loaded sentence-transformers embedding model")
            return
        except ImportError:
            pass

        # Try OpenAI embeddings
        try:
            import openai
            if openai.api_key:
                self._backend = "openai"
                print("[Stage7] Using OpenAI embeddings")
                return
        except (ImportError, AttributeError):
            pass

        # Fallback to TF-IDF
        self._backend = "tfidf"
        print("[Stage7] Using TF-IDF embeddings (sentence-transformers not available)")

    def _load_index(self):
        """Load existing index from disk"""
        if self._loaded:
            return

        # Load embeddings
        embeddings_file = self.index_path / 'embeddings.pkl'
        if embeddings_file.exists():
            with open(embeddings_file, 'rb') as f:
                self.embeddings = pickle.load(f)

        # Load inverted index
        inverted_file = self.index_path / 'inverted.json'
        if inverted_file.exists():
            with open(inverted_file) as f:
                self.inverted_index = json.load(f)

        # Load metadata
        metadata_file = self.index_path / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file) as f:
                self.metadata_index = json.load(f)

        # Load segment texts
        texts_file = self.index_path / 'texts.json'
        if texts_file.exists():
            with open(texts_file) as f:
                self.segment_texts = json.load(f)

        self._loaded = True
        print(f"[Stage7] Loaded index: {len(self.embeddings)} embeddings, "
              f"{len(self.inverted_index)} terms")

    def _save_index(self):
        """Save index to disk"""
        # Save embeddings
        with open(self.index_path / 'embeddings.pkl', 'wb') as f:
            pickle.dump(self.embeddings, f)

        # Save inverted index
        with open(self.index_path / 'inverted.json', 'w') as f:
            json.dump(self.inverted_index, f)

        # Save metadata
        with open(self.index_path / 'metadata.json', 'w') as f:
            json.dump(self.metadata_index, f)

        # Save segment texts
        with open(self.index_path / 'texts.json', 'w') as f:
            json.dump(self.segment_texts, f)

    def index(self, source: Source) -> Source:
        """
        Index source segments for search.

        Args:
            source: Source with processed segments

        Returns:
            Source (unchanged, indexing is side-effect)
        """
        source.status = ProcessingStatus.INDEXING
        self._load_embedder()
        self._load_index()

        try:
            # Generate embeddings
            texts = [seg.content_raw for seg in source.segments]
            segment_ids = [seg.segment_id for seg in source.segments]

            if self._backend == "sentence-transformers":
                embeddings = self._generate_st_embeddings(texts)
            elif self._backend == "openai":
                embeddings = self._generate_openai_embeddings(texts)
            else:
                embeddings = self._generate_tfidf_embeddings(texts)

            # Store embeddings
            for seg_id, embedding in zip(segment_ids, embeddings):
                self.embeddings[seg_id] = embedding

            # Build inverted index
            self._build_inverted_index(source.segments)

            # Index metadata
            self._index_metadata(source.segments)

            # Store segment texts
            for seg in source.segments:
                self.segment_texts[seg.segment_id] = seg.content_raw

            # Save to disk
            self._save_index()

            source.metadata['indexed_segments'] = len(source.segments)
            return source

        except Exception as e:
            source.error_message = str(e)
            source.error_stage = "index"
            raise IndexError(f"Indexing failed: {e}")

    def _generate_st_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using sentence-transformers"""
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        return [emb for emb in embeddings]

    def _generate_openai_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API"""
        import openai

        embeddings = []
        # Batch in groups of 100
        for i in range(0, len(texts), 100):
            batch = texts[i:i+100]
            response = openai.Embedding.create(
                input=batch,
                model="text-embedding-ada-002"
            )
            for item in response['data']:
                embeddings.append(np.array(item['embedding']))

        return embeddings

    def _generate_tfidf_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate TF-IDF based embeddings (fallback)"""
        # Build vocabulary
        vocab = defaultdict(int)
        doc_freq = defaultdict(int)

        for text in texts:
            words = set(text.lower().split())
            for word in words:
                vocab[word] += 1
                doc_freq[word] += 1

        # Filter to top 1000 words
        sorted_vocab = sorted(vocab.items(), key=lambda x: -x[1])[:1000]
        word_to_idx = {word: idx for idx, (word, _) in enumerate(sorted_vocab)}

        # Generate TF-IDF vectors
        n_docs = len(texts)
        embeddings = []

        for text in texts:
            words = text.lower().split()
            word_counts = defaultdict(int)
            for word in words:
                word_counts[word] += 1

            # TF-IDF vector
            vec = np.zeros(len(word_to_idx))
            for word, count in word_counts.items():
                if word in word_to_idx:
                    idx = word_to_idx[word]
                    tf = count / len(words)
                    idf = np.log(n_docs / (1 + doc_freq[word]))
                    vec[idx] = tf * idf

            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            embeddings.append(vec)

        return embeddings

    def _build_inverted_index(self, segments: List[Segment]):
        """Build inverted index for keyword search"""
        # Document frequencies for IDF
        doc_freq = defaultdict(int)
        term_docs = defaultdict(list)

        for seg in segments:
            words = set(seg.content_raw.lower().split())
            for word in words:
                if len(word) >= 3:  # Filter short words
                    doc_freq[word] += 1
                    term_docs[word].append(seg.segment_id)

        n_docs = len(segments)

        # Calculate TF-IDF scores
        for term, seg_ids in term_docs.items():
            idf = np.log(n_docs / (1 + doc_freq[term]))

            for seg_id in seg_ids:
                # Get term frequency
                seg_text = self.segment_texts.get(seg_id, '')
                if not seg_text:
                    for seg in segments:
                        if seg.segment_id == seg_id:
                            seg_text = seg.content_raw
                            break

                words = seg_text.lower().split()
                tf = words.count(term.lower()) / len(words) if words else 0
                tfidf = tf * idf

                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((seg_id, tfidf))

        # Sort by TF-IDF score
        for term in self.inverted_index:
            self.inverted_index[term].sort(key=lambda x: -x[1])

    def _index_metadata(self, segments: List[Segment]):
        """Index segment metadata for filtering"""
        for seg in segments:
            self.metadata_index[seg.segment_id] = {
                'source_id': seg.source_id,
                'speaker': seg.speaker_name,
                'segment_type': seg.segment_type.value if seg.segment_type else None,
                'topics': seg.topics,
                'entities': [
                    {'type': e.type, 'value': e.value}
                    for e in seg.entities
                ],
                'training_weight': seg.training_weight,
                'training_categories': seg.training_categories,
            }

    def search(self, query: str, limit: int = 10, filter_source: str = None) -> List[Dict]:
        """
        Search indexed segments.

        Args:
            query: Search query
            limit: Maximum results
            filter_source: Optional source_id filter

        Returns:
            List of search results with scores
        """
        self._load_embedder()
        self._load_index()

        results = []

        # Semantic search
        if self._backend in ("sentence-transformers", "openai"):
            semantic_results = self._semantic_search(query, limit * 2)
            results.extend(semantic_results)

        # Keyword search
        keyword_results = self._keyword_search(query, limit * 2)
        results.extend(keyword_results)

        # Merge and deduplicate
        seen = set()
        merged = []
        for r in sorted(results, key=lambda x: -x['score']):
            if r['segment_id'] not in seen:
                # Apply source filter
                if filter_source:
                    meta = self.metadata_index.get(r['segment_id'], {})
                    if meta.get('source_id') != filter_source:
                        continue

                seen.add(r['segment_id'])
                # Add text
                r['text'] = self.segment_texts.get(r['segment_id'], '')[:200]
                r['metadata'] = self.metadata_index.get(r['segment_id'], {})
                merged.append(r)

                if len(merged) >= limit:
                    break

        return merged

    def _semantic_search(self, query: str, limit: int) -> List[Dict]:
        """Search using semantic similarity"""
        # Generate query embedding
        if self._backend == "sentence-transformers":
            query_embedding = self.embedder.encode([query])[0]
        elif self._backend == "openai":
            import openai
            response = openai.Embedding.create(
                input=[query],
                model="text-embedding-ada-002"
            )
            query_embedding = np.array(response['data'][0]['embedding'])
        else:
            return []

        # Calculate similarities
        results = []
        for seg_id, embedding in self.embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding) + 1e-9
            )
            results.append({
                'segment_id': seg_id,
                'score': float(similarity),
                'match_type': 'semantic'
            })

        # Sort by similarity
        results.sort(key=lambda x: -x['score'])
        return results[:limit]

    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Search using keyword matching"""
        query_terms = query.lower().split()

        # Aggregate scores per segment
        segment_scores = defaultdict(float)

        for term in query_terms:
            if term in self.inverted_index:
                for seg_id, score in self.inverted_index[term]:
                    segment_scores[seg_id] += score

        # Convert to results
        results = [
            {
                'segment_id': seg_id,
                'score': score,
                'match_type': 'keyword'
            }
            for seg_id, score in segment_scores.items()
        ]

        results.sort(key=lambda x: -x['score'])
        return results[:limit]

    def get_similar(self, segment_id: str, limit: int = 5) -> List[Dict]:
        """Find segments similar to a given segment"""
        self._load_index()

        if segment_id not in self.embeddings:
            return []

        query_embedding = self.embeddings[segment_id]

        results = []
        for seg_id, embedding in self.embeddings.items():
            if seg_id == segment_id:
                continue

            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding) + 1e-9
            )
            results.append({
                'segment_id': seg_id,
                'score': float(similarity),
                'text': self.segment_texts.get(seg_id, '')[:200]
            })

        results.sort(key=lambda x: -x['score'])
        return results[:limit]

    def get_index_stats(self) -> Dict:
        """Get index statistics"""
        self._load_index()

        return {
            'total_embeddings': len(self.embeddings),
            'total_terms': len(self.inverted_index),
            'total_segments': len(self.metadata_index),
            'embedding_backend': self._backend or 'not loaded',
        }


# CLI for testing
if __name__ == '__main__':
    import sys

    indexer = Stage7Index()

    if len(sys.argv) < 2:
        stats = indexer.get_index_stats()
        print("Search Index Statistics:")
        print("-" * 40)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif sys.argv[1] == 'search':
        if len(sys.argv) < 3:
            print("Usage: python stage7_index.py search <query>")
            sys.exit(1)
        query = ' '.join(sys.argv[2:])
        results = indexer.search(query)
        print(f"Found {len(results)} results for '{query}':")
        for r in results:
            print(f"\n  [{r['match_type']}] {r['segment_id']} (score: {r['score']:.3f})")
            print(f"    {r['text'][:100]}...")
    elif sys.argv[1] == 'similar':
        if len(sys.argv) < 3:
            print("Usage: python stage7_index.py similar <segment_id>")
            sys.exit(1)
        results = indexer.get_similar(sys.argv[2])
        print(f"Similar segments to {sys.argv[2]}:")
        for r in results:
            print(f"  {r['segment_id']} (score: {r['score']:.3f})")
            print(f"    {r['text'][:80]}...")
    else:
        from .orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        source = orchestrator.get_result(sys.argv[1])

        if not source:
            print(f"Source not found: {sys.argv[1]}")
            sys.exit(1)

        source = indexer.index(source)

        print(f"Indexing complete!")
        print(f"Indexed segments: {source.metadata.get('indexed_segments', 0)}")
