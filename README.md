# sc2-build-tokenizer

`sc2-build-tokenizer` is an NLP-like library made for StarCraft 2 build orders rather than text.

It can extract builds from replay files or replay objects output by [`zephyrus-sc2-parser`](https://github.com/ZephyrBlu/zephyrus-sc2-parser), and can generate tokenized builds from those extracted builds.

What a tokenized build is an why you would want to do this is explained in the motivation section below.

## Motivation

Build orders are a fundamental part of StarCraft 2, they are the building blocks that the rest of your play is built upon. Yet as a community, we have no way to analyze and compare build orders.

### Build Order Blocks (Tokens)

On the most basic level, a build order is literally the order of the buildings you create in the game. However, build orders contain a lot of implicit information.

Build orders are assumed to be safe and efficient paths through the game that are optimized for your specific game plan.

Looking at the list of buildings (Even with supply numbers) does not convey this information to people, which is why new players often don't understand the point of build orders or struggle to follow them.

On a more advanced level, build orders can be viewed as a combination of common blocks. For example, standard openers can be considered blocks.

Max Yu from [TerranCraft](https://terrancraft.com/) covers a similar idea in one of his posts: [The Concept of Build Order Blocks](https://terrancraft.com/2019/06/30/the-concept-of-build-order-blocks/).

To summarize, he defines three build order blocks: opening, build and composition. The opening is one of the standard openings for your race (E.g. Hatch, Gas, Pool), the build is your chosen opening strategy (E.g. Mine drop, Oracle opener, Ling/bane, etc) and the composition is your mid-game strategy (E.g. Mech, Roach/Ravager, etc).

For our purposes, we will define build order blocks slightly differently than Max has. Build order blocks are called tokens, and they are simply defined as a sequence of buildings.

Ex: `('Gateway', 'Nexus', 'CyberneticsCore')`

The term tokens is borrowed from Natural Language Processing (NLP) (See: [Tokenization](https://en.wikipedia.org/wiki/Lexical_analysis#Tokenization)). Buildings are analogous to characters and build order blocks to tokens or words.

### The Benefits of Thinking About Builds in Terms of Tokens

Now that we've established what tokens are, let's go over why thinking about builds in terms of groups of buildings is useful.

Thinking about build orders as a list of buildings implies that all buildings are independent of one another, which is completely wrong. When we're talking about optimized build orders, each building and it's position in the build order is *highly* dependent on other buildings.

Another thing to point out is that build orders tend to re-use common sequences of buildings. You can think of build orders as a tree where many builds may share similar paths. If you're a skilled player, thinking about builds like this is probably second nature to you.

For example, in Protoss builds a very common pattern is 20 Nexus -> Tech -> 2x Gateways -> 3rd Nexus. There are also a lot of variations on this where you might swap out one of those steps for something else, like your 3rd Nexus for another tech building or more Gateways.

This is where the idea of viewing and analyzing builds as sequences of buildings (Tokens) shines. Tokens can capture the relationships between particular buildings and allow us to think in terms of build order blocks instead of individual buildings.
