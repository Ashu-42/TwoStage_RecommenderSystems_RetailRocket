# Two Stage Wide & Deep Recommender Systems for HomePage using retail Rocket Dataset

## Project Overview

This project builds a two-stage product recommendation system for an e-commerce homepage setting using the RetailRocket dataset.

The recommendation problem is framed as:

> When a returning user starts a new session, retrieve and rank products that the user is likely to view, add to cart, or purchase during that session.

The system follows a standard large-scale recommender architecture:

1. **Candidate Generator**: retrieves a broad set of potentially relevant products from the item universe.
2. **Ranker / Reranker**: scores and reorders the retrieved candidates based on predicted user engagement.

The main focus of the project is to build a practical, industry-style recommendation pipeline with time-aware data splits, leakage-safe feature construction, multi-source candidate generation, and a learned reranker.

---

## Dataset

The project uses the **RetailRocket e-commerce dataset**, which contains:

* User event logs:

  * `view`
  * `addtocart`
  * `transaction`
* Item property metadata
* Category hierarchy

The raw events are sessionized using a **30-minute inactivity threshold**.

In this project, a **new session start** is treated as a proxy for a user opening the app or landing on the homepage.

---

## Problem Definition

The project models homepage recommendation as a **session-start recommendation problem**.

For each query:

* `query_time` = start time of a user session
* input history = all user interactions before `query_time`
* target items = products interacted with later in the same session

The main evaluation focuses on **returning users**, where the user has at least one prior session.

This avoids using current-session behavior as input and keeps the task aligned with homepage recommendation, rather than in-session continuation recommendation.

---

## Labels

Multiple future-label columns are created for analysis and ranker training:

| Label               | Meaning                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| `label_interaction` | Candidate was viewed, added to cart, or purchased later in the session |
| `label_view`        | Candidate was viewed later in the session                              |
| `label_atc`         | Candidate was added to cart later in the session                       |
| `label_order`       | Candidate was purchased later in the session                           |
| `label_engagement`  | Candidate was added to cart or purchased later in the session          |

The first learned ranker is trained using:

```text
label_engagement = addtocart OR transaction
```

This is used because transaction-only labels are sparse, while add-to-cart still represents strong buying intent.

---

## Time-Aware Data Setup

The project uses chronological, time-aware splits to avoid future-data leakage.

Candidate-generation artifacts are built using only past data relative to each query block.

The system uses a walk-forward setup:

```text
past artifact window → future query block
```

This ensures that item-item maps, popularity signals, category popularity, and generality scores are created only from data available before the recommendation period.

For model training, validation, and testing, candidate sets are generated separately for each time block using the corresponding past artifact window.

---

## Candidate Generator V1

The final Candidate Generator V1 is a **multi-source homepage candidate generator**.

It combines several retrieval sources:

1. **User historical item-to-item co-interaction**

   * Uses the user’s past interacted items.
   * Retrieves products that historically co-occurred with those items.

2. **User category-based retrieval**

   * Uses the user’s historical categories.
   * Retrieves popular products from categories relevant to the user.

3. **User category-conditioned generality retrieval**

   * Retrieves broadly appealing products from categories relevant to the user.

4. **Global category popularity**

   * Retrieves popular products from globally popular categories.

5. **Global item popularity**

   * Retrieves recently popular products.

6. **Global generality fallback**

   * Retrieves products with broad appeal across many users and sessions.

The final candidate list is created using rank-aware source fusion and returns up to **500 candidates per query**.

---

## Product Generality

A product generality score is engineered to identify products that are not only popular, but broadly appealing.

The score uses item-level volume and spread signals such as:

* total interactions
* weighted interaction score
* unique users
* unique sessions
* number of active days

This helps distinguish between:

* products that are repeatedly interacted with by a narrow user group
* products that are interacted with broadly across many users and sessions

This is especially useful for homepage recommendation, where immediate user intent may be weak.

---

## Candidate Generation Evaluation

Candidate Generation is evaluated using:

* HitRate@K
* Recall@K
* MRR@K

The main values of K are:

```text
K = 100, 200, 300, 500
```

For realistic returning-user homepage/session-start queries, Candidate Generator V1 achieves approximately:

| Metric      |  Value |
| ----------- | -----: |
| HitRate@100 | ~26.7% |
| HitRate@500 | ~31.1% |

These results are for the harder homepage/session-start setting, where the model cannot use any current-session behavior as input.

---

## Ranker Dataset Creation

The ranker dataset is created by exploding the candidate list into row-level format:

```text
one row = query_id × candidate_itemid
```

Each row contains:

* query identifiers
* candidate item id
* CG rank
* CG normalized score
* CG raw score
* CG source flags
* source-specific ranks
* user history features
* candidate history-match flags
* future labels

Example ranker row:

```text
query_id | candidate_itemid | cg_rank | cg_score_norm | source flags | label_engagement
```

The ranker is trained to predict whether each candidate will receive future engagement.

---

## Sparse Logistic / Wide-Style Reranker

The first learned ranker is a sparse logistic regression reranker.

It predicts:

```text
P(future add-to-cart or order | query, candidate, features)
```

The predicted probability is used as a ranking score.

For each query:

1. Candidate Generator retrieves up to 500 products.
2. Logistic ranker scores each candidate.
3. Candidates are sorted by predicted score.
4. Ranking metrics are computed on the reordered list.

This model acts as a **wide-style reranker baseline** because it uses sparse categorical indicators, binary flags, rank buckets, and manually engineered features.

It is not yet a full Wide & Deep model, because it does not include a deep neural network branch or embeddings.

---

## Logistic Ranker Features

The sparse logistic reranker uses features such as:

### Candidate Generator Features

* CG rank bucket
* CG normalized score
* log-transformed CG raw score
* source-specific rank buckets
* source flags:

  * from user co-interaction CG
  * from user category CG
  * from user generality CG

### User History Features

* past view count
* past add-to-cart count
* past order count
* user history bucket

### Candidate History Features

* candidate was previously purchased by the user
* candidate appeared in the user’s recent history

### Time Features

* day of week
* hour of day

Training uses query-wise negative sampling:

```text
For each positive candidate, sample negative candidates from the same query.
```

This creates harder negatives because all sampled negatives were also retrieved by the Candidate Generator.

Validation and test evaluation are performed on full candidate lists for sampled query groups.

---

## Ranker Evaluation

The learned ranker is compared against the original Candidate Generator order.

### Baseline

```text
score = -cg_rank
```

This preserves the original CG ranking.

### Logistic Ranker

```text
score = predicted engagement probability
```

Ranking metrics used:

* HitRate@K
* Recall@K
* NDCG@K
* MRR@K

Two evaluation views are reported:

### 1. Reranker-only Evaluation

Includes only queries where the candidate set contains at least one future engagement-positive item.

This measures:

```text
When CG retrieved a useful product, can the ranker place it higher?
```

### 2. All-query Evaluation

Includes all homepage/session-start queries.

This measures end-to-end system behavior, including cases where CG does not retrieve any engagement-positive item.

---

## Logistic Ranker Results

The sparse logistic reranker significantly improves candidate ordering over the original CG rank.

On reranker-only test queries:

| Metric     | CG Baseline | Logistic Ranker |
| ---------- | ----------: | --------------: |
| NDCG@10    |      ~0.157 |          ~0.513 |
| HitRate@10 |      ~0.277 |          ~0.712 |
| NDCG@20    |      ~0.185 |          ~0.535 |
| HitRate@20 |      ~0.390 |          ~0.780 |

On all-query test evaluation, absolute values are lower because most homepage sessions do not contain an engagement-positive candidate in the retrieved set.

However, the logistic ranker still improves over the CG baseline:

| Metric     | CG Baseline | Logistic Ranker |
| ---------- | ----------: | --------------: |
| NDCG@10    |     ~0.0028 |         ~0.0091 |
| HitRate@10 |     ~0.0049 |         ~0.0126 |

This shows that:

> When the Candidate Generator retrieves a useful product, the learned reranker is much better than the original CG order at pushing that product higher.

It also shows that end-to-end performance is still limited by candidate-generation coverage and sparse engagement behavior.

---

## Current Project Status

Completed:

* Raw data cleaning
* Sessionization using 30-minute inactivity threshold
* Homepage/session-start query construction
* Time-aware rolling artifact creation
* Multi-source Candidate Generator V1
* Product generality feature engineering
* CG evaluation at multiple K values
* Ranker dataset creation
* Sparse logistic / wide-style reranker
* CG baseline vs learned reranker evaluation
* Hyperparameter tuning for logistic regression regularization

Current best logistic reranker uses:

```text
label = label_engagement
model = sparse logistic regression
regularization = L2
selected C = 0.3
```

---

## Key Learnings So Far

1. Homepage recommendation is much harder than in-session recommendation because no current-session behavior can be used.
2. Candidate generation recall is the ceiling for the ranker.
3. Multi-source retrieval works better than relying only on item-to-item co-interaction.
4. Product generality is useful as a fallback and broad-appeal signal.
5. A learned reranker can substantially improve ordering when the candidate generator retrieves useful products.
6. End-to-end performance is still constrained by sparse engagement labels and candidate-generation coverage.