# Ultra Trader ML Pipeline - Quick Start

## 🚀 Quick Setup

### 1. Basic Installation (Streamlit Dashboard Only)
```bash
pip install -r requirements.txt
```

### 2. Full ML Installation
```bash
pip install -r requirements-ml.txt
```

### 3. Test Installation
```bash
python test_pipeline.py
```

### 4. Run Demo
```bash
python demo_pipeline.py
```

## 📊 Features Added

✅ **GBT Training Pipeline** (`training/pipeline_gbt.py`)
- LightGBM + XGBoost support with Optuna hyperparameter optimization
- CSV and MongoDB data sources
- Technical indicators using `ta` library
- TimeSeriesSplit cross-validation
- Automatic model persistence

✅ **Backtesting Engine** (`evaluation/backtest.py`)
- Walk-forward backtesting with realistic fees
- Comprehensive metrics (Sharpe, drawdown, win rate)
- Support for long/flat and long/short strategies

✅ **Explainability Tools** (`analysis/explainability.py`)
- SHAP-based feature importance analysis
- Multiple plot types (summary, beeswarm, waterfall)
- Model interpretation utilities

✅ **LLM Analysis Service** (`services/llm_analysis.py`)
- Optional GPT-powered market insights
- **Disabled by default** for safety
- Graceful fallback with helpful guidance

✅ **Professional Configuration** (`configs/experiments/`)
- YAML-based experiment configuration
- Environment variable support for Railway deployment
- Comprehensive parameter spaces

✅ **Complete Documentation** (`docs/ML_PIPELINE.md`)
- Setup instructions for local and Railway deployment
- API reference and examples
- Troubleshooting guide

## 🛠 Usage

### Basic Training
```bash
# Train with default config
python training/pipeline_gbt.py

# Custom configuration
python training/pipeline_gbt.py --config configs/experiments/custom.yaml
```

### Environment Variables (Railway Compatible)
```bash
export DATA_SOURCE=mongodb
export MONGODB_URI="your-connection-string"
export MODEL_TYPE=lightgbm
export N_SPLITS=5
export OPTUNA_TRIALS=100
```

### Optional LLM Features
```bash
export OPENAI_API_KEY="your-api-key"  # Enables GPT analysis
```

## 📁 Structure

```
├── training/
│   └── pipeline_gbt.py          # Main ML training pipeline
├── evaluation/
│   └── backtest.py              # Backtesting utilities
├── analysis/
│   └── explainability.py       # SHAP model interpretation
├── configs/experiments/
│   └── gbt_default.yaml         # Default configuration
├── services/
│   └── llm_analysis.py          # Optional GPT analysis
├── models/                      # Model artifacts (auto-created)
├── docs/
│   └── ML_PIPELINE.md           # Complete documentation
├── requirements-ml.txt          # ML dependencies
├── test_pipeline.py             # Comprehensive test suite
└── demo_pipeline.py             # Interactive demo
```

## 🚢 Railway Deployment

The ML pipeline is fully compatible with Railway:

1. **Existing Streamlit Dashboard**: Unchanged, works as before
2. **ML Training Jobs**: Can be triggered via Railway "Run" command
3. **Environment Variables**: Fully configurable via Railway dashboard
4. **Dependencies**: Separated into `requirements.txt` (dashboard) and `requirements-ml.txt` (training)

### Railway Commands
```bash
# Dashboard (existing)
streamlit run ultra_dashboard/dashboard.py --server.port $PORT

# Training job
python training/pipeline_gbt.py

# One-time setup
pip install -r requirements-ml.txt
```

## 🔒 Safety Features

- **No Breaking Changes**: Existing Streamlit dashboard unchanged
- **Graceful Degradation**: Works without ML dependencies
- **Disabled LLM**: Safe for all environments by default
- **Error Handling**: Comprehensive error messages and fallbacks
- **Resource Management**: Configurable limits for memory/compute

## 📚 Next Steps

1. **Read Documentation**: See `docs/ML_PIPELINE.md` for complete guide
2. **Run Tests**: Execute `python test_pipeline.py`
3. **Try Demo**: Run `python demo_pipeline.py`
4. **Install Dependencies**: `pip install -r requirements-ml.txt`
5. **Train First Model**: `python training/pipeline_gbt.py`

For issues and detailed setup instructions, see the complete documentation.