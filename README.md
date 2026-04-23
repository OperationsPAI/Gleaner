# Gleaner

## Getting Started

### 0. Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management, which provides faster and more reliable package installation.

#### Option A: Using uv (Recommended)

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

#### Option B: Using pip

If you prefer using traditional pip:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .
```

**Note:** After activating the virtual environment (either with uv or pip), you can use `python` directly in the following commands.

### 1. Download and Extract the Dataset

First, download the dataset from Zenodo at [https://doi.org/10.5281/zenodo.19637628](https://doi.org/10.5281/zenodo.19637628) and place the archive in your workspace.

Then, extract the dataset archive:

```bash
tar -xzf gleaner-dataset.tar.gz
```

This will extract the dataset files into the `data/` directory.

### 2. Run Sampling

After extracting the dataset, you can run the sampling command:

```bash
python ./main.py sample batch -s gleaner -d gleaner --mode online --rate 0.05 --clear
```

**Command Parameters:**
- `-s gleaner`: Source dataset name
- `-d gleaner`: Destination dataset name
- `--mode online`: Sampling mode (online)
- `--rate 0.05`: Sampling rate (5% of the data)
- `--clear`: Clear previous results


### 3. View Results

After sampling, you can view the performance metrics:

```bash
python main.py sample perf-report -d gleaner
```

This command will output summary statistics for key performance metrics. For detailed performance data, check the Parquet files in:
```
output/rcabench-platform-v2/sampler_reports/gleaner/
```

## Data Format

#### Traces

Traces file contains a time series of spans.

|     Column     |   Type   | Description                                              |
| :------------: | :------: | :------------------------------------------------------- |
|      time      | datetime | start time of a span in UTC                              |
|    trace_id    |  string  | unique identifier of a trace (a trace groups many spans) |
|    span_id     |  string  | unique identifier of a span                              |
| parent_span_id |  string  | identifier of the parent span (for trace hierarchy)      |
|  service_name  |  string  | name of the service that generated the span              |
|   span_name    |  string  | name of the operation represented by the span            |
|    duration    |  uint64  | duration of a span in nanoseconds                        |
|     attr.*     |    *     | other attributes of a span                               |

#### Metrics

Metrics file contains a time series of metric values.

|    Column    |   Type   | Description                                         |
| :----------: | :------: | :-------------------------------------------------- |
|     time     | datetime | UTC timestamp of a metric value                     |
|    metric    |  string  | name of the metric value                            |
|    value     | float64  | value of the metric value                           |
| service_name |  string  | name of the service that generated the metric value |
|    attr.*    |    *     | other attributes of a metric value                  |

#### Logs

Logs file contains a time series of log events.

|    Column    |   Type   | Description                                      |
| :----------: | :------: | :----------------------------------------------- |
|     time     | datetime | UTC timestamp of a log event                     |
|   trace_id   |  string  | unique identifier of a trace                     |
|   span_id    |  string  | unique identifier of a span                      |
| service_name |  string  | name of the service that generated the log event |
|    level     |  string  | log level (e.g., INFO, ERROR)                    |
|   message    |  string  | log message                                      |
|    attr.*    |    *     | other attributes of a log event                  |

## Citation

If you use Gleaner in your research, please cite:

```bibtex
@misc{yang2026gleanersemanticallyrichefficientonline,
  title={Gleaner: A Semantically-Rich and Efficient Online Sampler for Microservice Diagnostics},
  author={Yifan Yang and Aoyang FANG and Songhan Zhang and Pinjia He},
  year={2026},
  eprint={2604.16810},
  archivePrefix={arXiv},
  primaryClass={cs.SE},
  url={https://arxiv.org/abs/2604.16810},
}
```
