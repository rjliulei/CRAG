# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import ray
import torch
import vllm
from blingfire import text_to_sentences_and_offsets
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

######################################################################################################
######################################################################################################
###
### Please pay special attention to the comments that start with "TUNE THIS VARIABLE"
###                        as they depend on your model and the available GPU resources.
###
### DISCLAIMER: This baseline has NOT been tuned for performance
###             or efficiency, and is provided as is for demonstration.
######################################################################################################


# Load the environment variable that specifies the URL of the MockAPI. This URL is essential
# for accessing the correct API endpoint in Task 2 and Task 3. The value of this environment variable
# may vary across different evaluation settings, emphasizing the importance of dynamically obtaining
# the API URL to ensure accurate endpoint communication.

CRAG_MOCK_API_URL = os.getenv("CRAG_MOCK_API_URL", "http://localhost:8000")


#### CONFIG PARAMETERS ---

# Define the number of context sentences to consider for generating an answer.
NUM_CONTEXT_SENTENCES = 20
# Set the maximum length for each context sentence (in characters).
MAX_CONTEXT_SENTENCE_LENGTH = 1000
# Set the maximum context references length (in characters).
MAX_CONTEXT_REFERENCES_LENGTH = 4000

# Batch size you wish the evaluators will use to call the `batch_generate_answer` function
SUBMISSION_BATCH_SIZE = 4 # TUNE THIS VARIABLE depending on the number of GPUs you are requesting and the size of your model.

# VLLM Parameters 
VLLM_TENSOR_PARALLEL_SIZE = 1 # TUNE THIS VARIABLE depending on the number of GPUs you are requesting and the size of your model.
VLLM_GPU_MEMORY_UTILIZATION = 0.85 # TUNE THIS VARIABLE depending on the number of GPUs you are requesting and the size of your model.
# Llama-3.1 defaults to 131072; single 24GB card KV cache is ~30k — cap context for vLLM.
VLLM_MAX_MODEL_LEN = 8192

# Sentence Transformer Parameters
SENTENTENCE_TRANSFORMER_BATCH_SIZE = 128 # TUNE THIS VARIABLE depending on the size of your embedding model and GPU mem available

# Step 4 / v2 abstain (read at call time via _abstain_config so .env load order is safe)
def _abstain_config() -> dict:
    return {
        # v1: reject before generation if max query–chunk cosine < tau
        "v1_enabled": os.getenv("RAG_ABSTAIN_ENABLED", "0") == "1",
        "v1_min_max_score": float(os.getenv("RAG_ABSTAIN_MIN_MAX_SCORE", "0.40")),
        # v2: after generation, reject if max answer–chunk cosine < tau
        "v2_enabled": os.getenv("RAG_ABSTAIN_V2_ENABLED", "0") == "1",
        "v2_min_answer_sim": float(os.getenv("RAG_ABSTAIN_ANSWER_MIN_SIM", "0.35")),
        "response": os.getenv("RAG_ABSTAIN_RESPONSE", "I don't know"),
    }


# Back-compat aliases (may be stale if env loaded after import; batch path uses _abstain_config)
RAG_ABSTAIN_ENABLED = os.getenv("RAG_ABSTAIN_ENABLED", "0") == "1"
RAG_ABSTAIN_MIN_MAX_SCORE = float(os.getenv("RAG_ABSTAIN_MIN_MAX_SCORE", "0.40"))
RAG_ABSTAIN_RESPONSE = os.getenv("RAG_ABSTAIN_RESPONSE", "I don't know")


# CAMUS: constraint-aware marginal utility selection (read at call time)
_CAMUS_STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "where",
        "what", "which", "who", "whom", "whose", "how", "why", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "shall", "can",
        "of", "in", "on", "at", "to", "for", "from", "by", "with", "as", "into",
        "about", "than", "that", "this", "these", "those", "it", "its", "their",
        "there", "here", "not", "no", "yes", "all", "any", "some", "such", "only",
        "own", "same", "so", "too", "very", "just", "also", "please", "tell", "me",
        "you", "your", "we", "our", "they", "he", "she", "his", "her", "them",
    }
)


def _camus_config() -> dict:
    return {
        "enabled": os.getenv("RAG_CAMUS", "0") == "1",
        "budget": int(os.getenv("RAG_CAMUS_BUDGET", "8")),
        "epsilon": float(os.getenv("RAG_CAMUS_EPSILON", "0")),
        "lam": float(os.getenv("RAG_CAMUS_LAMBDA", "0.5")),
        "gamma": float(os.getenv("RAG_CAMUS_GAMMA", "1.0")),
        "pool": int(os.getenv("RAG_CAMUS_POOL", "40")),
        "harm_sim_tau": float(os.getenv("RAG_CAMUS_HARM_SIM_TAU", "0.55")),
        "debug": os.getenv("RAG_CAMUS_DEBUG", "0") == "1",
    }


def _camus_parse_constraints(query: str) -> dict:
    """Rule-based constraints from the query only (no labels / GT)."""
    years = re.findall(r"\b(?:19|20)\d{2}\b", query)
    after_years = re.findall(
        r"\b(?:after|since|post|later than)\s+((?:19|20)\d{2})\b", query, flags=re.I
    )
    before_years = re.findall(
        r"\b(?:before|until|prior to)\s+((?:19|20)\d{2})\b", query, flags=re.I
    )

    q_starters = {
        "What", "Which", "Who", "Where", "When", "How", "Why",
        "Is", "Are", "Do", "Does", "Did", "In", "On", "At", "The", "A", "An", "Of",
    }
    entities: List[str] = []
    for ent in re.findall(
        r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*)\b", query
    ):
        parts = [p for p in ent.split() if p not in q_starters]
        if parts:
            entities.append(" ".join(parts).lower())

    is_set = bool(
        re.search(
            r"\b(list|names?|movies?|films?|members?|albums?|songs?|episodes?|"
            r"which of|how many|all the|as many)\b",
            query,
            flags=re.I,
        )
    ) or bool(re.search(r"^\s*who are\b", query, flags=re.I))

    atoms: List[str] = []
    for y in after_years:
        atoms.append(f"year>{y}")
    for y in before_years:
        atoms.append(f"year<{y}")
    used_rel = set(after_years) | set(before_years)
    for y in years:
        if y not in used_rel:
            atoms.append(y)

    for ent in entities:
        atoms.append(ent)

    if not atoms:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9\-']{3,}", query):
            wl = w.lower()
            if wl not in _CAMUS_STOPWORDS:
                atoms.append(wl)
        atoms = list(dict.fromkeys(atoms))[:8]
    else:
        atoms = list(dict.fromkeys(atoms))

    return {
        "atoms": atoms,
        "is_set": is_set,
        "years": years,
        "after_years": after_years,
        "before_years": before_years,
    }


def _camus_atom_supported(text: str, atom: str) -> bool:
    """Whether chunk text supports one constraint atom."""
    if atom.startswith("year>"):
        thr = int(atom[5:])
        return any(int(y) > thr for y in re.findall(r"\b(?:19|20)\d{2}\b", text))
    if atom.startswith("year<"):
        thr = int(atom[5:])
        return any(int(y) < thr for y in re.findall(r"\b(?:19|20)\d{2}\b", text))
    return atom.lower() in text.lower()


def _camus_covered_atoms(texts: Sequence[str], atoms: Sequence[str]) -> Set[str]:
    blob = " ".join(texts)
    return {a for a in atoms if _camus_atom_supported(blob, a)}


def _camus_cov_gain(
    chunk: str, selected_texts: Sequence[str], atoms: Sequence[str]
) -> float:
    if not atoms:
        return 0.0
    before = _camus_covered_atoms(selected_texts, atoms)
    after = _camus_covered_atoms(list(selected_texts) + [chunk], atoms)
    return float(len(after - before))


def _camus_list_inducement(chunk: str) -> bool:
    if chunk.count(",") >= 3:
        return True
    return bool(
        re.search(r"\b(including|such as|e\.g\.|for example|among them)\b", chunk, re.I)
    )


def _camus_harm(
    chunk: str,
    query_cos: float,
    gain: float,
    is_set: bool,
    harm_sim_tau: float,
) -> float:
    harm = 0.0
    if query_cos > harm_sim_tau and gain <= 0:
        harm += 1.0
    if is_set and _camus_list_inducement(chunk):
        harm += 1.0
    return harm


def _camus_select(
    query: str,
    chunks: np.ndarray,
    cosine_scores: np.ndarray,
    cfg: dict,
    chunk_embeddings: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Greedy CAMUS: ΔU ≈ CovGain − λ·redundancy − γ·harm.

    Uses only query text, chunk text, and embeddings/cosine (no GT / labels).
    """
    n = len(chunks)
    if n == 0:
        return chunks

    budget = min(int(cfg["budget"]), n)
    eps = float(cfg["epsilon"])
    lam = float(cfg["lam"])
    gamma = float(cfg["gamma"])
    pool = min(int(cfg.get("pool", 40)), n)
    harm_tau = float(cfg.get("harm_sim_tau", 0.55))
    debug = bool(cfg.get("debug", False))

    constraints = _camus_parse_constraints(query)
    atoms: List[str] = constraints["atoms"]
    is_set = bool(constraints["is_set"])

    # Restrict greedy search to top-`pool` by query cosine (speed on long HTML).
    pool_idx = (-cosine_scores).argsort()[:pool]
    cosine_scores = np.asarray(cosine_scores, dtype=np.float64)
    if chunk_embeddings is not None:
        emb = np.asarray(chunk_embeddings, dtype=np.float64)
    else:
        emb = None

    selected: List[int] = []
    selected_texts: List[str] = []
    debug_rows: List[Tuple[int, float, float, float, float]] = []

    while len(selected) < budget:
        best_i: Optional[int] = None
        best_du = float("-inf")
        best_parts = (0.0, 0.0, 0.0)

        for i in pool_idx:
            i = int(i)
            if i in selected:
                continue
            chunk = str(chunks[i])
            gain = _camus_cov_gain(chunk, selected_texts, atoms)
            if selected and emb is not None:
                red = float(np.max(emb[selected] @ emb[i]))
            elif selected:
                # No chunk embeddings: approximate redundancy via query-cos proximity.
                red = float(
                    max(1.0 - abs(float(cosine_scores[i]) - float(cosine_scores[j])) for j in selected)
                )
            else:
                red = 0.0
            harm = _camus_harm(
                chunk, float(cosine_scores[i]), gain, is_set, harm_tau
            )
            du = gain - lam * red - gamma * harm
            if du > best_du:
                best_du = du
                best_i = i
                best_parts = (gain, red, harm)

        if best_i is None or best_du <= eps:
            break

        selected.append(best_i)
        selected_texts.append(str(chunks[best_i]))
        debug_rows.append((best_i, best_du, *best_parts))

    # Avoid empty context if every ΔU ≤ ε on round 1.
    if not selected:
        selected = [int(pool_idx[0])]
        selected_texts = [str(chunks[selected[0]])]
        if debug:
            debug_rows.append((selected[0], float("-inf"), 0.0, 0.0, 0.0))

    if debug:
        print(
            f"[CAMUS] q={query[:80]!r} atoms={atoms[:8]} is_set={is_set} "
            f"picked={len(selected)}/{budget}"
        )
        for rank, (idx, du, gain, red, harm) in enumerate(debug_rows, 1):
            snippet = str(chunks[idx]).replace("\n", " ")[:90]
            print(
                f"  #{rank} i={idx} ΔU={du:.3f} gain={gain:.2f} red={red:.3f} "
                f"harm={harm:.2f} cos={float(cosine_scores[idx]):.3f} | {snippet}"
            )

    return np.asarray([chunks[i] for i in selected], dtype=object)


#### CONFIG PARAMETERS END---

class ChunkExtractor:

    @ray.remote
    def _extract_chunks(self, interaction_id, html_source):
        """
        Extracts and returns chunks from given HTML source.

        Note: This function is for demonstration purposes only.
        We are treating an independent sentence as a chunk here,
        but you could choose to chunk your text more cleverly than this.

        Parameters:
            interaction_id (str): Interaction ID that this HTML source belongs to.
            html_source (str): HTML content from which to extract text.

        Returns:
            Tuple[str, List[str]]: A tuple containing the interaction ID and a list of sentences extracted from the HTML content.
        """
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_source, "lxml")
        text = soup.get_text(" ", strip=True)  # Use space as a separator, strip whitespaces

        if not text:
            # Return a list with empty string when no text is extracted
            return interaction_id, [""]

        # Extract offsets of sentences from the text
        _, offsets = text_to_sentences_and_offsets(text)

        # Initialize a list to store sentences
        chunks = []

        # Iterate through the list of offsets and extract sentences
        for start, end in offsets:
            # Extract the sentence and limit its length
            sentence = text[start:end][:MAX_CONTEXT_SENTENCE_LENGTH]
            chunks.append(sentence)

        return interaction_id, chunks

    def extract_chunks(self, batch_interaction_ids, batch_search_results):
        """
        Extracts chunks from given batch search results using parallel processing with Ray.

        Parameters:
            batch_interaction_ids (List[str]): List of interaction IDs.
            batch_search_results (List[List[Dict]]): List of search results batches, each containing HTML text.

        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing an array of chunks and an array of corresponding interaction IDs.
        """
        # Setup parallel chunk extraction using ray remote
        ray_response_refs = [
            self._extract_chunks.remote(
                self,
                interaction_id=batch_interaction_ids[idx],
                html_source=html_text["page_result"]
            )
            for idx, search_results in enumerate(batch_search_results)
            for html_text in search_results
        ]

        # Wait until all sentence extractions are complete
        # and collect chunks for every interaction_id separately
        chunk_dictionary = defaultdict(list)

        for response_ref in ray_response_refs:
            interaction_id, _chunks = ray.get(response_ref)  # Blocking call until parallel execution is complete
            chunk_dictionary[interaction_id].extend(_chunks)

        # Flatten chunks and keep a map of corresponding interaction_ids
        chunks, chunk_interaction_ids = self._flatten_chunks(chunk_dictionary)

        return chunks, chunk_interaction_ids

    def _flatten_chunks(self, chunk_dictionary):
        """
        Flattens the chunk dictionary into separate lists for chunks and their corresponding interaction IDs.

        Parameters:
            chunk_dictionary (defaultdict): Dictionary with interaction IDs as keys and lists of chunks as values.

        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing an array of chunks and an array of corresponding interaction IDs.
        """
        chunks = []
        chunk_interaction_ids = []

        for interaction_id, _chunks in chunk_dictionary.items():
            # De-duplicate chunks within the scope of an interaction ID
            unique_chunks = list(set(_chunks))
            chunks.extend(unique_chunks)
            chunk_interaction_ids.extend([interaction_id] * len(unique_chunks))

        # Convert to numpy arrays for convenient slicing/masking operations later
        chunks = np.array(chunks)
        chunk_interaction_ids = np.array(chunk_interaction_ids)

        return chunks, chunk_interaction_ids

class RAGModel:
    """
    An example RAGModel
    """
    def __init__(self):
        self.initialize_models()
        self.chunk_extractor = ChunkExtractor()

    def initialize_models(self):
        # Initialize Meta Llama 3 - 8B Instruct Model
        self.model_name = "models/meta-llama/Llama-3.1-8B-Instruct"

        if not os.path.exists(self.model_name):
            raise Exception(
                f"""
            The evaluators expect the model weights to be checked into the repository,
            but we could not find the model weights at {self.model_name}
            """
            )

        # Initialize the model with vllm
        self.llm = vllm.LLM(
            self.model_name,
            worker_use_ray=True,
            tensor_parallel_size=VLLM_TENSOR_PARALLEL_SIZE, 
            gpu_memory_utilization=VLLM_GPU_MEMORY_UTILIZATION,
            max_model_len=VLLM_MAX_MODEL_LEN,
            trust_remote_code=True,
            dtype="half", # note: update the dtype based on the available GPU
            enforce_eager=True
        )
        self.tokenizer = self.llm.get_tokenizer()

        # Load a sentence transformer model optimized for sentence embeddings, using CUDA if available.
        self.sentence_model = SentenceTransformer(
            "models/sentence-transformers/all-MiniLM-L6-v2",
            device=torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            ),
        )

    def calculate_embeddings(self, sentences):
        """
        Compute normalized embeddings for a list of sentences using a sentence encoding model.

        This function leverages multiprocessing to encode the sentences, which can enhance the
        processing speed on multi-core machines.

        Args:
            sentences (List[str]): A list of sentences for which embeddings are to be computed.

        Returns:
            np.ndarray: An array of normalized embeddings for the given sentences.

        """
        embeddings = self.sentence_model.encode(
            sentences=sentences,
            normalize_embeddings=True,
            batch_size=SENTENTENCE_TRANSFORMER_BATCH_SIZE,
        )
        # Note: There is an opportunity to parallelize the embedding generation across 4 GPUs
        #       but sentence_model.encode_multi_process seems to interefere with Ray
        #       on the evaluation servers. 
        #       todo: this can also be done in a Ray native approach.
        #       
        return embeddings

    def get_batch_size(self) -> int:
        """
        Determines the batch size that is used by the evaluator when calling the `batch_generate_answer` function.
        
        The evaluation timeouts linearly scale with the batch size. 
            i.e.: time out for the `batch_generate_answer` call = batch_size * per_sample_timeout 
        

        Returns:
            int: The batch size, an integer between 1 and 16. It can be dynamic
                 across different batch_generate_answer calls, or stay a static value.
        """
        self.batch_size = SUBMISSION_BATCH_SIZE  
        return self.batch_size

    def batch_generate_answer(self, batch: Dict[str, Any]) -> List[str]:
        """
        Generates answers for a batch of queries using associated (pre-cached) search results and query times.

        Parameters:
            batch (Dict[str, Any]): A dictionary containing a batch of input queries with the following keys:
                - 'interaction_id;  (List[str]): List of interaction_ids for the associated queries
                - 'query' (List[str]): List of user queries.
                - 'search_results' (List[List[Dict]]): List of search result lists, each corresponding
                                                      to a query.
                - 'query_time' (List[str]): List of timestamps (represented as a string), each corresponding to when a query was made.

        Returns:
            List[str]: A list of plain text responses for each query in the batch. Each response is limited to 75 tokens.
            If the generated response exceeds 75 tokens, it will be truncated to fit within this limit.

        Notes:
        - If the correct answer is uncertain, it's preferable to respond with "I don't know" to avoid
          the penalty for hallucination.
        - Response Time: Ensure that your model processes and responds to each query within 30 seconds.
          Failing to adhere to this time constraint **will** result in a timeout during evaluation.
        """
        batch_interaction_ids = batch["interaction_id"]
        queries = batch["query"]
        batch_search_results = batch["search_results"]
        query_times = batch["query_time"]

        # Chunk all search results using ChunkExtractor
        chunks, chunk_interaction_ids = self.chunk_extractor.extract_chunks(
            batch_interaction_ids, batch_search_results
        )

        cfg = _abstain_config()
        camus_cfg = _camus_config()

        # Calculate all chunk embeddings
        chunk_embeddings = self.calculate_embeddings(chunks)

        # Calculate embeddings for queries
        query_embeddings = self.calculate_embeddings(queries)

        # Retrieve top matches for the whole batch
        batch_retrieval_results = []
        abstain_flags = []
        for _idx, interaction_id in enumerate(batch_interaction_ids):
            query_embedding = query_embeddings[_idx]

            # Identify chunks that belong to this interaction_id
            relevant_chunks_mask = chunk_interaction_ids == interaction_id

            # Filter out the said chunks and corresponding embeddings
            relevant_chunks = chunks[relevant_chunks_mask]
            relevant_chunks_embeddings = chunk_embeddings[relevant_chunks_mask]

            # Calculate cosine similarity between query and chunk embeddings,
            cosine_scores = (relevant_chunks_embeddings * query_embedding).sum(1)

            max_score = float(cosine_scores.max()) if len(cosine_scores) else 0.0
            if cfg["v1_enabled"] and max_score < cfg["v1_min_max_score"]:
                batch_retrieval_results.append([])
                abstain_flags.append(True)
                continue

            # Context selection: baseline top-N, or CAMUS hook (Step 2 stub = top-budget).
            if camus_cfg["enabled"]:
                retrieval_results = _camus_select(
                    queries[_idx],
                    relevant_chunks,
                    cosine_scores,
                    camus_cfg,
                    chunk_embeddings=relevant_chunks_embeddings,
                )
            else:
                retrieval_results = relevant_chunks[
                    (-cosine_scores).argsort()[:NUM_CONTEXT_SENTENCES]
                ]

            # You might also choose to skip the steps above and
            # use a vectorDB directly.
            batch_retrieval_results.append(retrieval_results)
            abstain_flags.append(False)

        generate_indices = [idx for idx, abstain in enumerate(abstain_flags) if not abstain]
        if generate_indices:
            formatted_prompts = self.format_prompts(
                [queries[idx] for idx in generate_indices],
                [query_times[idx] for idx in generate_indices],
                [batch_retrieval_results[idx] for idx in generate_indices],
            )
            responses = self.llm.generate(
                formatted_prompts,
                vllm.SamplingParams(
                    n=1,  # Number of output sequences to return for each prompt.
                    top_p=0.9,  # Float that controls the cumulative probability of the top tokens to consider.
                    temperature=0.1,  # Randomness of the sampling
                    skip_special_tokens=True,  # Whether to skip special tokens in the output.
                    max_tokens=50,  # Maximum number of tokens to generate per output sequence.

                    # Note: We are using 50 max new tokens instead of 75,
                    # because the 75 max token limit for the competition is checked using the Llama2 tokenizer.
                    # Llama3 instead uses a different tokenizer with a larger vocabulary
                    # This allows the Llama3 tokenizer to represent the same content more efficiently,
                    # while using fewer tokens.
                ),
                use_tqdm=False # you might consider setting this to True during local development
            )
        else:
            responses = []

        answers = []
        response_idx = 0
        for abstain in abstain_flags:
            if abstain:
                answers.append(cfg["response"])
            else:
                answers.append(responses[response_idx].outputs[0].text)
                response_idx += 1

        # v2: answer–passage consistency (after generation)
        if cfg["v2_enabled"]:
            check_idx = [
                i
                for i, a in enumerate(answers)
                if not abstain_flags[i]
                and a.strip()
                and "i don't know" not in a.lower()
            ]
            if check_idx:
                ans_embs = self.calculate_embeddings([answers[i] for i in check_idx])
                for j, i in enumerate(check_idx):
                    refs = batch_retrieval_results[i]
                    if len(refs) == 0:
                        answers[i] = cfg["response"]
                        continue
                    ref_embs = self.calculate_embeddings(list(refs))
                    sim = float((ref_embs * ans_embs[j]).sum(1).max())
                    if sim < cfg["v2_min_answer_sim"]:
                        answers[i] = cfg["response"]

        return answers

    def format_prompts(self, queries, query_times, batch_retrieval_results=[]):
        """
        Formats queries, corresponding query_times and retrieval results using the chat_template of the model.
            
        Parameters:
        - queries (List[str]): A list of queries to be formatted into prompts.
        - query_times (List[str]): A list of query_time strings corresponding to each query.
        - batch_retrieval_results (List[str])
        """        
        system_prompt = "You are provided with a question and various references. Your task is to answer the question succinctly, using the fewest words possible. If the references do not contain the necessary information to answer the question, respond with 'I don't know'. There is no need to explain the reasoning behind your answers."
        formatted_prompts = []

        for _idx, query in enumerate(queries):
            query_time = query_times[_idx]
            retrieval_results = batch_retrieval_results[_idx]

            user_message = ""
            references = ""
            
            if len(retrieval_results) > 0:
                references += "# References \n"
                # Format the top sentences as references in the model's prompt template.
                for _snippet_idx, snippet in enumerate(retrieval_results):
                    references += f"- {snippet.strip()}\n"
            
            references = references[:MAX_CONTEXT_REFERENCES_LENGTH]
            # Limit the length of references to fit the model's input size.

            user_message += f"{references}\n------\n\n"
            user_message 
            user_message += f"Using only the references listed above, answer the following question: \n"
            user_message += f"Current Time: {query_time}\n"
            user_message += f"Question: {query}\n"
            
            formatted_prompts.append(
                self.tokenizer.apply_chat_template(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            )

        return formatted_prompts
