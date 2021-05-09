# StarCraft 2 Build Orders in Terms of Groups of Buildings

`sc2-build-tokenizer` is an NLP-like library made for StarCraft 2 build orders rather than text.

It can extract builds from replay files or replay objects output by [`zephyrus-sc2-parser`](https://github.com/ZephyrBlu/zephyrus-sc2-parser), and can generate tokenized builds from those extracted builds.

What a tokenized build is an why you would want to do this is explained in the motivation section below.

## Motivation

Build orders are a fundamental part of StarCraft 2. They are the building blocks that the rest of the game is built upon. Yet as a community, we have no way to analyze and compare build orders.

### Build Order Blocks

On the most basic level, a build order is literally the order of the buildings you create in the game. However, build orders contain a lot of implicit information.

Build orders are assumed to be safe and efficient paths through the game that are optimized for your specific game plan.

Looking at the list of buildings (Even with supply numbers) does not convey this information to people, which is why new players often don't understand the point of build orders or struggle to follow them.

On a more advanced level, build orders can be viewed as a combination of common blocks. For example, standard openers could be considered blocks.

Max Yu from [TerranCraft](https://terrancraft.com/) covers a similar idea in one of his posts: [The Concept of Build Order Blocks](https://terrancraft.com/2019/06/30/the-concept-of-build-order-blocks/).

To summarize, he defines three build order blocks: opening, build and composition. The opening is one of the standard openings for your race (E.g. Hatch, Gas, Pool), the build is your chosen opening strategy (E.g. Mine drop, Oracle opener, Ling/bane, etc) and the composition is your mid-game strategy (E.g. Mech, Roach/Ravager, etc).

For our purposes we will define build order blocks slightly differently than Max has. Build order blocks are called tokens, and they are simply defined as any sequence of buildings.

`Ex: (Gateway, Nexus, CyberneticsCore)`

The term tokens is borrowed from Natural Language Processing (NLP) (See: [Tokenization](https://en.wikipedia.org/wiki/Lexical_analysis#Tokenization)). Buildings are analogous to characters and build order blocks to tokens or words.

### The Benefits of Build Order Blocks

Now that we've established what tokens are, let's go over why thinking about builds in terms of groups of buildings is useful.

Thinking about build orders as a list of buildings implies that all buildings are independent of one another, which is completely wrong. When we're talking about optimized build orders, each building and it's position in the build order is *highly* dependent on the other buildings.

Build orders also tend to re-use common sequences of buildings. You can think of build orders as a tree where many builds may share similar paths. If you're a highly skilled player, thinking about builds like this is probably second nature to you.

For example, in Protoss builds a very common pattern is: `20 Nexus -> Tech -> 2x Gateways -> 3rd Nexus`. There are also a lot of variations on this where you might swap out one of those steps for something else, like your 3rd Nexus for another tech building or more Gateways.

This is where the idea of viewing and analyzing build orders as sequences of buildings (Tokens) shines. Tokens can capture the relationships between particular buildings and allow us to think in terms of build order blocks instead of individual buildings, which preserves context and is more intuitive.

Of course, we can already divide build orders into arbitrary groups of buildings if we want to. But the benefit of a quantitative tokenization process is that tokenized builds (Build orders represented by groups of buildings) can be directly compared and analyzed against other tokenized builds.

## Overview of Build Tokenization Model

### Pre-processing: Build Order Extraction

Build orders are extracted from replays by [`zephyrus-sc2-parser`](https://github.com/ZephyrBlu/zephyrus-sc2-parser) with particular buildings such as supply buildings ignored and only buildings up to the 7 minute mark being counted as part of the build order.

### Pre-processing: Generating N-grams and Token Distributions from Build Orders

[N-grams](https://en.wikipedia.org/wiki/N-gram) are an idea from NLP which we use to generate possible tokens from a build order. In NLP, they're sequences of words in the [corpus](https://en.wikipedia.org/wiki/Text_corpus).

A common usage of n-grams is predicting the next word in a sequence. This is done by finding all the word sequences of length n in the corpus (I.e. n-grams of size n), then calculating conditional probability distributions for the last word in the sequence given the preceding words.

`Ex: "my favourite colour is blue" = 5-gram -> P("blue"|"my favourite colour is") = x`

For example, if we have a build `(A, B, C)` then we can generate the following n-grams:

- Unigrams: `(A)`, `(B)`, `(C)`
- Bigrams: `(A, B)`, `(B, C)`
- Trigrams: `(A, B, C)`

We will refer to these generated n-grams as tokens.

Similar to textual n-grams, we can calculate conditional probability distributions for the last building in a token given the preceding buildings based on a corpus of extracted build orders. 

### Generating Tokenized Build Permutations

Now that we've generated all the possible n-grams based on our extracted build orders, we can use them as a reference to generate possible tokenized builds for a given build order.

### Finding the Optimal Tokenized Build

After we've generated all the possible tokenized builds it's actually very easy to find the optimal build since it's just the build with the highest probability, and all the heavy lifting is done while the build permutations are being searched.

That heavy lifting is all about calculating the conditional probabilities of buildings given previous buildings. Different conditional probabilities (And hence different tokens) will generate different overall probabilities, so our goal is to find the permutation of tokens that maximizes the overall probability of the tokenized build.

Let's think about two opposite permutations:

- The tokenized build consists of all buildings as their own token (Ex: `((A), (B), (C))`)
- The tokenized build consists of a single token containing all buildings (Ex: `((A, B, C))`)

In the first case, we treat each building as being [independent](https://en.wikipedia.org/wiki/Independence_(probability_theory)) of the previous ones so the overall probability of the sequence is equal to the product of the probabilities of A, B and C idependently occurring.

`Ex: P((A), (B), (C)) = P(A) * P(B) * P(C)`

In the second case, buildings are dependent on the previous buildings so the overall probability is the product of the *conditional* probabilities of A, B and C rather than the independent ones.

`Ex: P((A, B, C)) = P(A) * P(B|(A)) * P(C|(A, B))`

Because buildings are not independent of one another, these calculations will yield different results.

The optimal tokenized build is the one that maximizes the probability of conditional sequences of buildings like `(A, B, C)`, which incentivizes common sequences of buildings.
