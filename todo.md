是的，我觉得在 agent 时代，**文档 + agent skill** 会比单纯文档更有说服力，尤其是你们的 artifact 本身就有“适配新输入、替换 sampler、扩展 RCA algorithm”这种可操作流程。对于 Reusable badge，这样写会更强：

- 文档证明：人类 reviewer 可以读懂、手动操作、排错。
- Skill 证明：agent 可以按结构化流程帮用户迁移数据、改配置、扩展模块、跑验证。
- 两者结合说明 artifact 不只是“可复现”，而是“可被别人带到新数据和新算法场景中继续使用”。

我建议你们把 reusable 部分组织成两层：

**1. Documentation 层**

可以明确写两个 new input integration paths：

- **Path A: Legacy TracePicker Trace-Only Dataset**
  - 输入：旧 TracePicker 数据。
  - 转换：通过脚本转换成新的 Dataset-B 格式。
  - 限制：只有 normal-stage traces，没有 logs，没有 alarms。
  - 运行方式：使用 `Gleaner` 的 no-log / no-alarm-detection 变体。
  - 适用场景：trace-only RCA，或者评估 sampler / trace-based pipeline。
  - 文档应说明：输入目录结构、转换脚本参数、输出格式、运行命令、预期结果、限制。

- **Path B: Raw ClickHouse OpenTelemetry Dataset**
  - 输入：完整 raw ClickHouse OTel 数据。
  - 包含：traces、logs、alarms。
  - 运行方式：完整 `Gleaner` pipeline。
  - 适用场景：端到端 RCA，包括 alarm、log、trace 联合分析。
  - 文档应说明：ClickHouse schema、导出/读取方式、字段映射、alarm/log/trace 对齐规则、完整运行命令。

这样 reviewer 会看到你们不是只支持一个固定 benchmark，而是已经考虑了两种现实迁移场景：

```text
We provide two documented paths for adapting Gleaner to new inputs:
(1) a trace-only conversion path from legacy TracePicker data into the Dataset-B format, which runs with the no-log/no-alarm variant of Gleaner; and
(2) a full raw ClickHouse OpenTelemetry ingestion path, which preserves alarms, logs, and traces and supports the complete Gleaner pipeline.
```

**2. Agent Skill 层**

我觉得可以写，而且可以在 artifact README 里专门放一个小节：

```text
Agent-Assisted Adaptation
```

核心意思是：

```text
In addition to human-readable documentation, we provide an agent skill that encodes the reusable workflows for adapting the artifact. The skill guides an AI coding agent through input-format inspection, dataset conversion, configuration updates, sampler extension, RCA algorithm integration, and validation checks.
```

这个说法很适合 Reusable，因为它强调 artifact 的操作知识不是散落在代码里，而是被显式封装了。

可以做两个 skill，或者一个总 skill 下面分 task。

我建议一个主 skill 就够，名字例如：

```text
gleaner-adapter
```

里面分四个 workflow：

- `integrate-tracepicker-input`
- `integrate-clickhouse-otel-input`
- `extend-sampler`
- `extend-rca-algorithm`

这样比拆太多 skill 更清晰。

**建议文档结构**

可以在 repo 里加：

```text
docs/
  reusable-guide.md
  new-inputs.md
  extending-samplers.md
  extending-rca-algorithms.md
  troubleshooting.md

.codex/skills/
  gleaner-adapter/
    SKILL.md
```

或者如果你们不想绑定 Codex，也可以叫：

```text
agent_skills/
  gleaner-adapter/
    SKILL.md
```

`docs/new-inputs.md` 里重点写：

```text
# Adapting Gleaner to New Inputs

## Path A: TracePicker Trace-Only Conversion
- When to use this path
- Required input files
- Conversion command
- Generated Dataset-B layout
- Running Gleaner without logs and alarms
- Expected outputs
- Known limitations

## Path B: Raw ClickHouse OpenTelemetry Ingestion
- When to use this path
- Required ClickHouse tables
- Required OTel fields
- Alarm/log/trace mapping
- Running full Gleaner
- Expected outputs
- Troubleshooting
```

`docs/extending-samplers.md` 写：

```text
# Extending Samplers

## Sampler Interface
## Required Inputs and Outputs
## Adding a New Sampler
## Registering the Sampler
## Configuring Parameters
## Testing the Sampler
```

`docs/extending-rca-algorithms.md` 写：

```text
# Extending RCA Algorithms

## RCA Algorithm Interface
## Adding a New Algorithm
## Accessing Traces, Logs, and Alarms
## Registering the Algorithm
## Changing Algorithm Parameters
## Running Evaluation
```

`docs/troubleshooting.md` 写：

```text
# Troubleshooting

## Dependency Installation
## Python/Package Version Issues
## ClickHouse Connection Issues
## Missing Logs or Alarms
## Dataset Schema Mismatch
## Empty Output or No Root Cause Found
## Slow Queries or Memory Pressure
```

**Skill 内容建议**

`SKILL.md` 不需要很长，但要让 agent 知道该怎么做。可以这样写：

```markdown
# Gleaner Adapter Skill

Use this skill when adapting Gleaner to new input datasets, adding a new sampler, adding a new RCA algorithm, or changing experiment parameters.

## Workflows

### 1. Integrate TracePicker Trace-Only Input
Use when the user has legacy TracePicker data with normal-stage traces only.
Steps:
1. Inspect the TracePicker input directory.
2. Run the TracePicker-to-Dataset-B conversion script.
3. Verify the generated Dataset-B schema.
4. Configure Gleaner to disable log and alarm-dependent modules.
5. Run the no-log/no-alarm Gleaner variant.
6. Check output files and report limitations.

### 2. Integrate Raw ClickHouse OTel Input
Use when the user has raw OpenTelemetry traces, logs, and alarms in ClickHouse.
Steps:
1. Inspect ClickHouse connection configuration.
2. Verify required trace, log, and alarm tables.
3. Check field mappings against Gleaner's expected schema.
4. Run the full ingestion pipeline.
5. Run the complete Gleaner pipeline.
6. Validate generated outputs.

### 3. Extend a Sampler
Steps:
1. Locate the sampler interface and existing sampler implementations.
2. Create a new sampler following the required input/output contract.
3. Register the sampler in the configuration or factory.
4. Add an example configuration.
5. Run a minimal validation job.

### 4. Extend an RCA Algorithm
Steps:
1. Locate the RCA algorithm interface.
2. Implement the new algorithm using the expected trace/log/alarm inputs.
3. Register the algorithm.
4. Add configuration parameters.
5. Run evaluation on a small dataset.
```

**Reusable badge 里可以这样表述**

你们可以在 artifact appendix 或 README 里加一段：

```text
Reusable support. Beyond reproducing the paper results, the artifact includes documentation and agent-oriented adaptation guidance for applying Gleaner to new inputs and extending its components. We provide two new-input workflows: a TracePicker-to-Dataset-B conversion path for trace-only data, which runs with the no-log/no-alarm variant of Gleaner, and a full raw ClickHouse OpenTelemetry ingestion path, which supports traces, logs, and alarms and runs the complete Gleaner pipeline. We also document how to extend samplers and RCA algorithms, modify key parameters, and troubleshoot dependency and schema issues. To further support practical reuse, we include an agent skill that encodes these workflows as step-by-step adaptation procedures.
```

**我的建议**

我会做成：

1. `docs/new-inputs.md`：写两条输入适配路径。
2. `docs/extending.md`：写 sampler、RCA algorithm、参数修改。
3. `docs/troubleshooting.md`：写依赖和常见错误。
4. `agent_skills/gleaner-adapter/SKILL.md`：把上面流程编码成 agent 可执行步骤。
5. README 里加一个 `Reusing Gleaner` 小节，链接到这些文档和 skill。

这样比只说“we provide clearer guidance”强很多，reviewer 能直接看到你们已经提供了“人能读、agent 能执行”的 reusable support。