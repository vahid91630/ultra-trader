# Ultra Trader ML Pipeline

## Overview

The Ultra Trader ML Pipeline provides a professional, production-ready machine learning framework for financial prediction using Gradient Boosted Trees (GBT). The system is designed for both local development and Railway deployment, featuring automated hyperparameter optimization, comprehensive backtesting, and explainable AI capabilities.

## Features

- **Advanced ML Models**: LightGBM and XGBoost with automated hyperparameter optimization via Optuna
- **Data Sources**: Support for both CSV files and MongoDB data loading
- **Feature Engineering**: Comprehensive technical indicators using the `ta` library
- **Cross-Validation**: Time-series aware validation with configurable splits
- **Backtesting**: Walk-forward backtesting with realistic fee modeling
- **Explainability**: SHAP-based model interpretability and feature importance analysis
- **Optional LLM Analysis**: GPT-powered market insights (disabled by default)
- **Railway Ready**: Environment variable configuration for seamless cloud deployment

## Quick Start

### 1. Install Dependencies

```bash
# Install ML dependencies
pip install -r requirements-ml.txt

# For basic Streamlit dashboard only
pip install -r requirements.txt
```

### 2. Basic Training

```bash
# Train with default configuration
python training/pipeline_gbt.py

# Train with custom config
python training/pipeline_gbt.py --config configs/experiments/custom.yaml
```

### 3. View Results

After training, check the `models/` directory for saved artifacts:
- `lightgbm_YYYYMMDD_HHMMSS.pkl`: Trained model
- `lightgbm_YYYYMMDD_HHMMSS_metadata.yaml`: Training metadata and metrics

## Directory Structure

```
ultra-trader/
├── training/
│   └── pipeline_gbt.py          # Main training pipeline
├── evaluation/
│   └── backtest.py              # Backtesting utilities
├── analysis/
│   └── explainability.py       # SHAP analysis tools
├── configs/
│   └── experiments/
│       └── gbt_default.yaml     # Default configuration
├── services/
│   └── llm_analysis.py          # Optional GPT analysis
├── models/                      # Model artifacts (auto-created)
├── docs/
│   └── ML_PIPELINE.md           # This documentation
├── requirements-ml.txt          # ML dependencies
└── .gitignore                   # Excludes model artifacts
```

## Configuration

### Environment Variables

The pipeline supports extensive configuration via environment variables:

#### Data Configuration
- `DATA_SOURCE`: `csv` or `mongodb` (default: `csv`)
- `CSV_PATH`: Path to CSV file (default: `data/sample_data.csv`)
- `MONGODB_URI`: MongoDB connection string
- `MONGODB_COLLECTION`: Collection name (default: `price_data`)

#### Training Configuration
- `MODEL_TYPE`: `lightgbm` or `xgboost` (default: `lightgbm`)
- `N_SPLITS`: Cross-validation splits (default: `5`)
- `OPTUNA_TRIALS`: Hyperparameter optimization trials (default: `100`)

#### Optional Features
- `OPENAI_API_KEY`: Enable GPT-based analysis (optional)

### YAML Configuration

The system uses YAML files for detailed configuration. See `configs/experiments/gbt_default.yaml` for the complete structure:

```yaml
# Example configuration
experiment_name: "gbt_default"
model_type: "lightgbm"

data:
  source: "csv"
  csv_path: "data/sample_data.csv"
  technical_indicators:
    - "sma_5"
    - "sma_20"
    - "rsi_14"
    - "macd"
  
model:
  lightgbm:
    objective: "binary"
    metric: "binary_logloss"
    num_leaves: 31
    learning_rate: 0.1

optuna:
  n_trials: 100
  timeout: 3600
```

## Data Requirements

### CSV Format

The pipeline expects CSV files with the following columns:
- `timestamp`: Date/time (any pandas-compatible format)
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

Example:
```csv
timestamp,open,high,low,close,volume
2023-01-01 00:00:00,50000,50100,49900,50050,1000000
2023-01-01 01:00:00,50050,50200,50000,50150,1200000
```

### MongoDB Format

For MongoDB data sources, documents should contain the same fields as the CSV format. The pipeline automatically converts MongoDB collections to DataFrames.

### Sample Data Generation

If no data file is found, the pipeline automatically generates synthetic financial data for demonstration purposes.

## Model Training Pipeline

The training pipeline consists of several stages:

### 1. Data Loading
- Loads data from CSV or MongoDB based on configuration
- Validates required columns
- Generates sample data if source unavailable

### 2. Feature Engineering
- Adds technical indicators using the `ta` library
- Creates price-based features (returns, ratios)
- Handles missing values appropriately

### 3. Target Construction
- Supports multiple target types:
  - `direction`: Predict price direction (up/down)
  - `returns`: Predict future returns
  - `volatility`: Predict future volatility
- Configurable prediction horizon

### 4. Cross-Validation
- Uses TimeSeriesSplit for proper temporal validation
- Configurable number of splits
- Prevents look-ahead bias

### 5. Hyperparameter Optimization
- Optuna-based Bayesian optimization
- Model-specific parameter spaces
- Configurable trial count and timeout

### 6. Final Training
- Trains final model on full dataset
- Early stopping on validation set
- Comprehensive performance evaluation

### 7. Model Persistence
- Saves trained model as pickle file
- Stores metadata including:
  - Model parameters
  - Performance metrics
  - Feature list
  - Training configuration

## Backtesting

The backtesting module provides realistic performance evaluation:

### Features
- Walk-forward validation
- Transaction cost modeling
- Multiple signal types (long/flat, long/short)
- Comprehensive performance metrics

### Usage

```python
from evaluation.backtest import BacktestEngine

# Create backtest engine
engine = BacktestEngine(
    initial_capital=10000,
    fee_rate=0.001,  # 0.1% per trade
    risk_free_rate=0.02
)

# Run backtest
results = engine.run_backtest(signals, prices)
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

### Metrics Provided
- Total and annualized returns
- Sharpe ratio
- Maximum drawdown
- Calmar ratio
- Win rate
- Transaction costs

## Explainability

The explainability module uses SHAP (SHapley Additive exPlanations) for model interpretation:

### Features
- Feature importance analysis
- Individual prediction explanations
- Multiple plot types (summary, beeswarm, waterfall)
- Model-agnostic approach

### Usage

```python
from analysis.explainability import SHAPAnalyzer

# Create analyzer
analyzer = SHAPAnalyzer(model, X_background, model_type="tree")

# Generate feature importance
importance = analyzer.get_feature_importance(X_test)

# Create visualizations
analyzer.generate_summary_plot(X_test, save_path="shap_summary.png")
analyzer.generate_beeswarm_plot(X_test, save_path="shap_beeswarm.png")
```

## LLM Analysis (Optional)

The LLM analysis service provides AI-powered insights using GPT models:

### Features (when enabled)
- Market sentiment analysis
- Model explanation in plain English
- Trading signal interpretation
- Comprehensive strategy reports

### Setup

```bash
# Enable LLM analysis
export OPENAI_API_KEY="your-api-key-here"

# Install OpenAI library (not in requirements-ml.txt by default)
pip install openai
```

### Usage

```python
from services.llm_analysis import LLMAnalyzer

analyzer = LLMAnalyzer()

# Market analysis
analysis = analyzer.analyze_market_data(price_data, predictions)

# Model explanation
explanation = analyzer.explain_model_predictions(
    feature_importance, predictions, model_metrics
)
```

### Safety Note
LLM analysis is **disabled by default** and requires explicit API key configuration. This ensures safe deployment in all environments.

## Railway Deployment

The system is designed for seamless Railway deployment:

### Environment Setup

1. **Set Environment Variables** in Railway dashboard:
   ```
   DATA_SOURCE=mongodb
   MONGODB_URI=your-mongodb-connection-string
   MODEL_TYPE=lightgbm
   N_SPLITS=5
   OPTUNA_TRIALS=50
   ```

2. **Install Dependencies** via Railway build:
   ```bash
   pip install -r requirements-ml.txt
   ```

### Deployment Options

#### Option 1: Scheduled Training Jobs
Create a Railway service that runs training on a schedule:
```bash
# In Railway "Run" command
python training/pipeline_gbt.py
```

#### Option 2: Ephemeral Training
Trigger training manually via Railway dashboard:
```bash
railway run python training/pipeline_gbt.py
```

#### Option 3: Combined Service
Run both Streamlit dashboard and training in the same deployment:
- Use existing Procfile for dashboard: `web: streamlit run ultra_dashboard/dashboard.py --server.port $PORT`
- Add training endpoint or scheduled job

### Railway Best Practices

1. **Resource Management**: Set appropriate CPU/RAM limits for training jobs
2. **Data Persistence**: Use Railway volumes or external storage for model artifacts
3. **Environment Isolation**: Separate training and serving environments if needed
4. **Monitoring**: Use Railway logs to monitor training progress

## Local Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd ultra-trader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements-ml.txt
```

### Development Workflow

1. **Data Preparation**: Place your CSV files in `data/` directory
2. **Configuration**: Modify `configs/experiments/gbt_default.yaml` as needed
3. **Training**: Run `python training/pipeline_gbt.py`
4. **Analysis**: Use notebooks or scripts to analyze results
5. **Backtesting**: Evaluate strategy performance

### Testing

```bash
# Test training pipeline
python training/pipeline_gbt.py --config configs/experiments/gbt_default.yaml

# Test backtesting
python -c "from evaluation.backtest import _demo_backtest; _demo_backtest()"

# Test explainability (requires trained model)
python -c "from analysis.explainability import _demo_explainability; _demo_explainability()"
```

## Performance Optimization

### Training Speed
- Use smaller Optuna trial counts for faster iteration
- Reduce background sample size for SHAP analysis
- Enable early stopping for cross-validation
- Use parallel processing where available

### Memory Usage
- Limit dataset size for large files
- Use data chunking for MongoDB queries
- Clear intermediate variables in training loop
- Monitor memory usage during optimization

### Model Selection
- LightGBM is generally faster than XGBoost
- Tree-based models work well for tabular financial data
- Consider ensemble methods for improved performance

## Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Error: ModuleNotFoundError
pip install -r requirements-ml.txt
```

#### MongoDB Connection
```bash
# Error: PyMongo connection failed
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/db"
```

#### SHAP Installation
```bash
# Error: SHAP import failed
pip install shap
# For M1 Macs:
pip install shap --no-deps
```

#### Data Format Issues
- Ensure CSV has required columns (timestamp, open, high, low, close, volume)
- Check timestamp format is pandas-compatible
- Verify no missing values in critical columns

### Performance Issues

#### Slow Training
- Reduce `n_trials` in Optuna configuration
- Use smaller datasets for initial testing
- Check system resources (CPU/RAM usage)

#### Memory Errors
- Reduce dataset size
- Lower SHAP background sample size
- Use data chunking for large files

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Models

Extend the pipeline with custom models:

```python
# Add to training/pipeline_gbt.py
class CustomModel:
    def __init__(self, **params):
        self.params = params
    
    def fit(self, X, y):
        # Custom training logic
        pass
    
    def predict_proba(self, X):
        # Custom prediction logic
        pass
```

### Custom Features

Add domain-specific features:

```python
# Extend FeatureEngineer class
def add_custom_features(self, df):
    # Add market regime indicators
    df['volatility_regime'] = self._classify_volatility(df)
    
    # Add correlation features
    df['correlation_spy'] = self._rolling_correlation(df, 'SPY')
    
    return df
```

### Custom Targets

Implement alternative prediction targets:

```python
# Extend TargetBuilder class
def build_custom_target(self, df):
    if self.target_type == 'momentum':
        # Multi-period momentum score
        df['target'] = self._momentum_score(df, [5, 10, 20])
    
    return df
```

## API Reference

### Key Classes

#### `TrainingPipeline`
Main orchestrator for the training process.

#### `DataLoader`
Handles data loading from various sources.

#### `FeatureEngineer`
Creates technical indicators and features.

#### `GBTModel`
Wrapper for LightGBM/XGBoost models.

#### `OptunaTuner`
Hyperparameter optimization using Optuna.

#### `BacktestEngine`
Backtesting and performance evaluation.

#### `SHAPAnalyzer`
Model explainability using SHAP.

#### `LLMAnalyzer`
Optional GPT-based analysis (disabled by default).

### Configuration Schema

See `configs/experiments/gbt_default.yaml` for the complete configuration schema with all available options.

## Contributing

1. Follow existing code style and patterns
2. Add tests for new functionality
3. Update documentation for new features
4. Ensure Railway compatibility
5. Test with both CSV and MongoDB data sources

## License

[Add your license information here]

## Support

For issues and questions:
1. Check this documentation
2. Review existing GitHub issues
3. Create new issue with detailed description
4. Include log output and configuration used