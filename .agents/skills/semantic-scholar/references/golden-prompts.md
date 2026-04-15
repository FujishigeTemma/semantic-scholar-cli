# Golden Prompts

## Direct prompts

- "Use Semantic Scholar to find recent survey papers on retrieval-augmented generation."
- "Get the BibTeX citation for Attention Is All You Need."
- "Find the authors of DOI:10.1038/nature14539."
- "Which papers cite ARXIV:1706.03762?"

## Indirect prompts

- "Can you look up this paper in Semantic Scholar and tell me whether it has an open access PDF?"
- "I need the top candidate authors for Geoffrey Hinton from Semantic Scholar before I pick one."
- "Check Semantic Scholar for papers about mechanistic interpretability from 2024."

## Negative prompts

- "Search the web for recent AI chip news."
- "Review this Python package and fix the failing tests."
- "Summarize the PDFs already stored in this folder."
- "Find papers on Google Scholar."

## Command mapping hints

- Topic or title fragment -> start with `paper search`
- Exact paper id -> `paper get` or `citation get`
- Ambiguous person name -> `author search`
- Exact author id -> `author get`
- Reference traversal -> `paper citations` or `paper references`
