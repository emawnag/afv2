import multiprocessing as mp
import os

def run_rag():
    # Place imports here to delay CUDA init until after spawn is set
    from pleias_rag_interface import RAGWithCitations

    # Initialize with your preferred model
    rag = RAGWithCitations("PleIAs/Pleias-RAG-350M")

    # Define query and sources
    query = "What is the capital of France?"
    sources = [
        {
            "text": "Paris is the capital and most populous city of France.",
            "metadata": {"source": "Geographic Encyclopedia", "reliability": "high"}
        },
        {
            "text": "The Eiffel Tower is located in Paris, France.",
            "metadata": {"source": "Travel Guide", "year": 2020}
        }
    ]

    # Generate a response
    response = rag.generate(query, sources)

    # Print the final answer with citations
    print(response["processed"]["clean_answer"])

if __name__ == "__main__":
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    mp.set_start_method("spawn", force=True)
    run_rag()
