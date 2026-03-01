# Temporal Hybrid Retrieval for COVID-19 Literature

> Neural sparse + dense retrieval with temporal filtering and diversity ranking

## Features
- 🔍 Hybrid Search: SPLADE (sparse) + Sentence-BERT (dense) via RRF fusion
- ⏰ Temporal Filtering: Explicit year detection + implicit recency boost
- 🎯 Diversity Ranking: MMR (λ=0.7) to reduce redundancy
- ⚡ Performance: <2s latency, nDCG@10 > 0.60

## Dataset
- TREC-COVID (BEIR format): 171,332 documents
- 50 expert-crafted topics + 66,336 human relevance judgments
- NIST metadata: publish_time, journal, DOI, authors

## Quick Start
[installation instructions]

## Evaluation
Metrics: nDCG@10, MAP@10, P@10, α-nDCG@10, Temporal Accuracy
Baselines: BM25-only, Dense-only, RRF-Full, RRF-NoDiversity

## Citation
[your course/assignment info]
