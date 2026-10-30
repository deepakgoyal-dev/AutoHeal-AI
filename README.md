# AutoHeal AI: Autonomous Self-Healing Data Pipeline & Instant Analytics

[![GitHub Pages Deployment](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://deepakgoyal-dev.github.io/AutoHeal-AI/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**AutoHeal AI** is a zero-human-intervention autonomous data pipeline and interactive analytics web application. It ingests degraded, corrupted real-world data, autonomously detects anomalies across 6 vectors, executes 7 multi-pass self-healing repairs, calculates a Data Health Score ($0$ to $100$), and generates instant visual analytics with plain-English executive briefings.

👉 **Try the Live Web App in Your Browser:**  
**[https://deepakgoyal-dev.github.io/AutoHeal-AI/](https://deepakgoyal-dev.github.io/AutoHeal-AI/)**  
*(Drag and drop any raw CSV file to watch it self-heal and visualize instantly!)*

---

## 🌟 Key Architecture & Capabilities

```mermaid
flowchart TD
    A["Raw / Corrupted Data Ingestion<br/>(CSV, JSON, Parquet, Web Upload)"] --> B["Multi-Vector Corruption Detector"]
    
    subgraph S1["Anomaly Detection Vectors"]
        B1["Masked Sentinel Nulls ('-999', 'N/A', '??')"]
        B2["Formatting Chaos (Currency '$', '€', '%')"]
        B3["Statistical Outliers (1.5x IQR / Modified Z-Score)"]
        B4["Categorical Drift & Typos (Levenshtein)"]
        B5["Schema & Header Inconsistencies"]
        B6["Exact & Near-Duplicate Records"]
    end
    B --> S1
    S1 --> C["Autonomous Multi-Pass Self-Healer"]
    
    subgraph S2["Zero-Intervention Healing Passes"]
        C1["Pass 1: Schema & Header Sanitization"]
        C2["Pass 2: Masked Sentinel Null Normalization"]
        C3["Pass 3: Type Coercion & ISO-8601 Timestamp Standardizer"]
        C4["Pass 4: Categorical Consensus Typo Healing"]
        C5["Pass 5: Context-Aware Adaptive Imputation (Median/Mode)"]
        C6["Pass 6: Extreme Outlier Winsorization"]
        C7["Pass 7: Exact Duplicate Record Purging"]
    end
    C --> S2
    S2 --> D["Tamper-Evident Healing Ledger<br/>(Health Score Delta 0-100)"]
    
    D --> E1["Sanitized Dataset Export<br/>(Clean CSV / JSON)"]
    D --> E2["Instant Visual Analytics<br/>(Interactive HTML5 / Canvas Web App)"]
    D --> E3["Plain-English AI Intelligence<br/>(Executive Briefing & Strategic Recs)"]
```

---

## 🌐 Running on the Web

### Option A: 100% Client-Side Web App (GitHub Pages)
Visit the deployed application at **[https://deepakgoyal-dev.github.io/AutoHeal-AI/](https://deepakgoyal-dev.github.io/AutoHeal-AI/)**.
- **Zero Installation Required**: Runs directly in Chrome, Edge, Safari, or Firefox.
- **Drag-and-Drop Ingestion**: Drop any messy CSV into the browser window.
- **Client-Side Self-Healing**: Detects sentinels, parses currency strings, bounds outliers via IQR, and calculates before/after health deltas right in your browser.
- **Interactive Visualizations**: Canvas-based distribution histograms, correlation heatmaps, side-by-side diff inspectors, and searchable audit ledgers.

---

### Option B: Local Web Server with Python Backend
Run the high-performance local server:
```bash
python server.py --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser for local batch and REST API processing.

---

### Option C: Cloud Container Deployment (Docker / Render / Railway)
Build and run the Docker container:
```bash
docker build -t autoheal-ai .
docker run -p 8000:8000 autoheal-ai
```

---

## 💻 CLI & Autonomous Background Watcher

### 1. Run Autonomous Demonstration
```bash
python run_pipeline.py --demo all --rows 500
```

### 2. Process Custom File
```bash
python run_pipeline.py --input path/to/corrupted_data.csv
```

### 3. Continuous Background Watcher Mode
Watches `data/incoming/` continuously and self-heals files the moment they are dropped:
```bash
python run_pipeline.py --watch
```

### 4. Run Unit Test Suite
```bash
python -m unittest test_aegis.py
```

---

## 📊 Anomaly Resolution Matrix

| Anomaly Vector | Detection Heuristic | Autonomous Self-Healing Action |
| :--- | :--- | :--- |
| **Masked Sentinels** | Regex dictionary (`-999`, `N/A`, `??`, `null`, `missing`) | Normalizes to standard NaN, followed by context-aware imputation |
| **Dirty Types & Currency** | Currency regex symbols (`$`, `€`, `£`, `USD`) & percentage formatters | Regex numeric extraction, decimal parsing, and float casting |
| **Heterogeneous Dates** | Multi-pattern timestamp candidate evaluation | Normalizes mixed EU/US/ISO/Epoch strings to unified ISO-8601 |
| **Categorical Typos** | Low-frequency vs high-frequency Gestalt pattern matching | Maps typos to high-frequency ground truth (`>80%` similarity) |
| **Missing Values** | Skewness and cardinality profiling | Skewed: robust median; Symmetrical: Gaussian mean; Correlated: group median |
| **Statistical Outliers** | 1.5 * IQR & 3.0 * IQR bounds | Adaptive Winsorization (bounds extreme spikes to 1.5*IQR threshold) |
| **Duplicate Records** | Exact hash duplicate matching | Identifies redundant rows and purges duplicate entries |

---

## 📜 License
MIT License. Created by [Deepak Goyal](https://github.com/deepakgoyal-dev).
