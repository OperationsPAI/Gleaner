# Third-party Components

The artifact vendors baseline samplers and RCA algorithms as git submodules pinned to the exact commits used by the AE workspace.

| Component | Purpose | Repository | Commit | License/notes |
|---|---|---|---|---|
| ShapleyIQ | RCA: ShapleyIQ and MicroRCA | https://github.com/LGU-SE-Internal/ShapleyIQ | f45c02e55f5614f8c9e5d54ba1882780c694ce90 | Public LGU fork |
| Nezha | RCA: Nezha | https://github.com/LGU-SE-Internal/Nezha | f0de4db8123a566e13c5fcfe6ac0d9137009f99a | MIT license |
| TracePicker | Baseline sampler | https://github.com/LGU-SE-Internal/TracePicker | 31e5fc8130c9b2c315220bb91397f2756dda8378 | MIT license in original version |
| TraStrainer | Baseline samplers: TraStrainer, Sieve, Sifter | https://github.com/LGU-SE-Internal/TraStrainer | 82b133d9a0209997e3337506988776ab07ac4ada | Public LGU fork; original repository has no license |

Submodules are intentionally not added as uv workspace members yet because some baselines have conflicting Python/runtime requirements. The artifact runner will invoke them through adapters with pinned environments or compatibility shims.
