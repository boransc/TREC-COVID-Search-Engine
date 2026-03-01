# covid-temporal-search-engine
A production-ready search engine for TREC-COVID (171K documents) combining  neural sparse (SPLADE) and dense (Sentence-BERT) retrieval with Reciprocal  Rank Fusion (RRF). Features temporal filtering via publish_time metadata and  MMR-based diversity ranking to reduce redundancy. Achieves nDCG@10 > 0.60  with &lt;2s query latency.
