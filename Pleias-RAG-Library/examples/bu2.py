from pleias_rag_interface import RAGWithCitations
import os
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

def main():
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

if __name__ == '__main__':
    main()
