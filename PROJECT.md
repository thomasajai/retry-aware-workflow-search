# Cost-Efficient Search for Agentic Workflows with Retries

This is the project description supplied by the team. Keep this page as the canonical statement of the topic and scope.

***Motivation.*** Choosing models for an agentic workflow requires balancing task success, cost, and latency across multiple stages. Retries complicate this tradeoff: an inexpensive model followed by a stronger retry may be preferable to using the stronger model immediately, but repeated failures can erase the savings. The broader goal is to discover effective model combinations without spending more on profiling than the resulting configuration saves during deployment.

***Problem.*** Can we efficiently profile and search over model combinations when retries are allowed, without exhaustively evaluating every configuration? Allowing different models across retry attempts enlarges the search space, while early termination means that not every execution reaches every attempt. Profiling must therefore capture both the cost of unsuccessful attempts and the contribution of later attempts to eventual success. The challenge is to determine which configurations and execution paths need additional measurements, and which can be estimated or eliminated using existing observations.

***Proposed approach.*** This project will investigate retry-aware profiling and search, using AgentOpt and VineLM as starting points. Potential directions include reusing measurements across shared execution prefixes, allocating more evaluation effort to promising or uncertain configurations, and stopping evaluation of clearly uncompetitive candidates. Students will study when these techniques can reduce profiling effort without overlooking useful model combinations. Evaluation will compare against random search, uniform allocation of evaluation samples, and existing profiling and search methods, with exhaustive evaluation on small search spaces as a reference. Experiments will vary the number of available models, workflow stages, and retry limits. The intended outcome is a search procedure that finds strong cost–latency–success tradeoffs under a limited profiling budget, reporting both the expense of finding a configuration and its performance on held-out tasks.

***Suggested reading.***

- AgentOpt v0.1 Technical Report: Client-Side Optimization for LLM-Based Agent — Budget-efficient search over model combinations in multi-stage agent pipelines.
- VineLM: Trie-Based Fine-Grained Control for Agentic Workflows — Shared-prefix representations, checkpointing, and sparse profiling for workflows with retries and refinement loops.

## Course and references

- [Course page and current schedule](https://daplab.cs.columbia.edu/agentic-systems/)
- [Local paper collection and source links](papers/README.md)
