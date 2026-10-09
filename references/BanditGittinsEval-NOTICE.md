# BanditGittinsEval reference and attribution

Reference repository: https://github.com/QianJaneXie/BanditGittinsEval

Pinned revision: `a4992e22a48e781327efd5411fb7d0921ad5ab61`.

`scripts/mathqa_bandits.py` adapts the Gaussian `m_diff` expectation, backward
dynamic program and finite-population transitions from `src/q_estimation.py`,
`src/gittins_index_computation.py`, `src/gittins_lookup.py`,
`src/gittins_shrinking_posterior.py`, and `src/simple_regret_recommend.py`.
It ports the schedule/reallocation from `src/sysrs_policy.py`, itself a port of
[llm-bandits-sysrs Smart-SR](https://github.com/zifanlyu/llm-bandits-sysrs).
Reference files were read but are not imported or executed by the experiment.

The numerical port uses NumPy float64 and standard-library normal CDF evaluation;
the reference uses JAX/Torch, generally float32. RNG and recommendation ties are
documented replay adaptations. This is not a bitwise library reproduction.

Copyright 2025 Qian Xie, Theo Brown, Ziv Scully, Alexander Terenin.
Copyright 2025 Theo Brown.
Copyright 2026 Qian Xie.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
