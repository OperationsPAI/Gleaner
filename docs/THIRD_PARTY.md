# Third-party Components

The artifact vendors baseline samplers and RCA algorithms as git submodules pinned to the exact commits used by the AE workspace. These repositories are included in the local archive as file contents, not as bare gitlinks, so reviewers can inspect the referenced code from the package.

## Pinned Sources And Access Checks

The public URL checks below were performed with non-mutating `git ls-remote <url>` commands on 2026-06-28. They verify that the configured `.gitmodules` URLs are reachable without credentials from the current environment; they do not upload, mutate, or reserve any external artifact link.

| Component | Purpose | Repository | Pinned commit | `git ls-remote` status | Remote HEAD observed | Pin note |
|---|---|---|---|---|---|---|
| ShapleyIQ | RCA: ShapleyIQ and MicroRCA | https://github.com/LGU-SE-Internal/ShapleyIQ.git | `f45c02e55f5614f8c9e5d54ba1882780c694ce90` | OK, 4 refs visible | `ceac113d2d1a3a571013ca58358e8b9f9e61933f` | Pinned to the reviewed `dev-note` submodule commit, not the remote default HEAD. |
| Nezha | RCA: Nezha | https://github.com/LGU-SE-Internal/Nezha.git | `f0de4db8123a566e13c5fcfe6ac0d9137009f99a` | OK, 8 refs visible | `7b048e7a7fdb2c1237ad7d442f9ada9f929a8ae8` | Pinned to the reviewed submodule commit, not the remote default HEAD. |
| TracePicker | Baseline sampler | https://github.com/LGU-SE-Internal/TracePicker.git | `ca049d2a69e740df8fc1e034ebee3a87c1664245` | OK, 3 refs visible | `ca049d2a69e740df8fc1e034ebee3a87c1664245` | Pinned commit matches remote HEAD observed during the check. |
| TraStrainer | Baseline samplers: TraStrainer, Sieve, Sifter | https://github.com/LGU-SE-Internal/TraStrainer.git | `225e9e956432ed5254bce0d59718720d6b829451` | OK, 5 refs visible | `225e9e956432ed5254bce0d59718720d6b829451` | Pinned commit matches remote HEAD observed during the check. |

The local submodule pin smoke test in `scripts/smoke_test.sh` checks these exact commits when Git metadata is available. In archive/container contexts without `.git`, it checks that each `third_party/` directory exists and is non-empty, then clearly reports that strict SHA verification was skipped.

## License File Evidence

License status is based only on files present in the vendored submodule directories at the pinned commits. If no license file is present, this document records that fact instead of inferring license terms from upstream history.

| Component | License files found in vendored tree | Evidence-based status |
|---|---|---|
| ShapleyIQ | `third_party/ShapleyIQ/LICENSE` | Apache License 2.0 text is present in the vendored tree. |
| Nezha | `third_party/Nezha/LICENSE` | MIT License text is present in the vendored tree. |
| TracePicker | none found under `third_party/TracePicker/` by the AE license-file scan | License is unknown in the vendored LGU fork snapshot; needs upstream/project-owner confirmation before making a license claim. |
| TraStrainer | none found under `third_party/TraStrainer/` by the AE license-file scan | License is unknown in the vendored LGU fork snapshot; needs upstream/project-owner confirmation before making a license claim. |

## Smoke-test Coverage

`scripts/smoke_test.sh` is intentionally a fast artifact smoke test, not a full third-party component test suite. It verifies:

- exact submodule SHAs in a Git checkout;
- non-empty `third_party/` directories in archive/container contexts where `.git` is unavailable;
- importability of the local `gleaner` package;
- installed `rcabench-platform` package metadata.

The reduced RQ wrappers exercise committed reduced reports and RCA evidence, but they do not execute the full TracePicker, TraStrainer, Nezha, MicroRCA, or ShapleyIQ upstream training/inference pipelines. Nezha, ShapleyIQ/MicroRCA, and TraStrainer/Sifter/Sieve are available as uv workspace members for full-path development; TracePicker is intentionally isolated in its own Python 3.12 environment. Full component-level execution is outside the reviewer-verified reduced scope because the full raw datasets are not packaged and TracePicker has a separate runtime stack.

## Dependency-risk Decisions

Nezha, ShapleyIQ/MicroRCA, and TraStrainer/Sifter/Sieve are added as uv workspace members because their updated top-level `pyproject.toml` files align with `rcabench-platform==0.4.1`. TracePicker is intentionally excluded from the workspace and should use a separate Python 3.12 uv environment. The reduced/offline artifact path consumes committed parquet reports and expected outputs instead of rebuilding every baseline environment.

Known risks that remain outside the reduced reviewer path:

- TracePicker requests Python `==3.12.*` in `third_party/TracePicker/pyproject.toml`, while this artifact environment uses Python 3.13.
- TracePicker pins heavy CUDA-oriented dependencies through direct wheel URLs, including `torch==2.4.0`, `dgl`, and `geatpy==2.7.0`.
- The older ShapleyIQ internal requirements file under `third_party/ShapleyIQ/ShapleyIQ/requirements.txt` contains a legacy Python stack; the artifact uses the top-level workspace `pyproject.toml` and committed reduced RCA evidence for the verified path.

A future full-path artifact should add component-level smoke tests for the workspace baselines and the isolated TracePicker environment after the full raw-data runners are pinned and verified.
