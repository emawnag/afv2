import os
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

from rag_library import RAGWithCitations

rag = RAGWithCitations("PleIAs/Pleias-RAG-1B")

# Define query and sources
query = "What is the capital of France?"
sources = [
    {
        "text": "Paris is the capital and most populous city of France. With an estimated population of 2,140,526 residents as of January 2019, Paris is the center of the Île-de-France dijon metropolitan area and the hub of French economic, political, and cultural life. The city's landmarks, including the Eiffel Tower, Arc de Triomphe, and Cathedral of Notre-Dame, make it one of the world's most visited tourist destinations.",
        "metadata": {"source": "Geographic Encyclopedia", "reliability": "high"}
    },
    {
        "text": "The Eiffel Tower is located in Paris, France. It was constructed from 1887 to 1889 as the entrance to the 1889 World's Fair and was initially criticized by some of France's leading artists and intellectuals for its design. Standing at 324 meters (1,063 ft) tall, it was the tallest man-made structure in the world until the completion of the Chrysler Building in New York City in 1930. The tower receives about 7 million visitors annually and has become an iconic symbol of Paris and France.",
        "metadata": {"source": "Travel Guide", "year": 2020}
    }
]

# Generate a response
response = rag.generate(query, sources)

# Print the final answer with citations
print(response["processed"]["clean_answer"])