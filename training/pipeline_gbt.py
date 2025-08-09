#!/usr/bin/env python3
"""
Ultra Trader GBT Training Pipeline

End-to-end machine learning pipeline for financial prediction using
Gradient Boosted Trees (LightGBM/XGBoost) with hyperparameter optimization.

Usage:
    python training/pipeline_gbt.py [--config path/to/config.yaml]

Environment Variables:
    DATA_SOURCE: csv or mongodb (default: csv)
    CSV_PATH: path to CSV file (default: data/sample_data.csv)
    MONGODB_URI: MongoDB connection string
    N_SPLITS: number of CV splits (default: 5)
    OPTUNA_TRIALS: number of Optuna trials (default: 100)
    MODEL_TYPE: lightgbm or xgboost (default: lightgbm)
"""

import os
import sys
import argparse
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Graceful dependency handling
try:
    import pandas as pd
    import numpy as np
    import yaml
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import roc_auc_score, classification_report
    import optuna
    import joblib
    
    # ML libraries
    LIGHTGBM_AVAILABLE = False
    XGBOOST_AVAILABLE = False
    TA_AVAILABLE = False
    PYMONGO_AVAILABLE = False
    
    try:
        import lightgbm as lgb
        LIGHTGBM_AVAILABLE = True
    except ImportError:
        logger.warning("LightGBM not available")
    
    try:
        import xgboost as xgb
        XGBOOST_AVAILABLE = True
    except ImportError:
        logger.warning("XGBoost not available")
    
    try:
        import ta
        TA_AVAILABLE = True
    except ImportError:
        logger.warning("Technical Analysis library (ta) not available")
    
    try:
        from pymongo import MongoClient
        PYMONGO_AVAILABLE = True
    except ImportError:
        logger.warning("PyMongo not available")

except ImportError as e:
    logger.error(f"Critical dependency missing: {e}")
    logger.error("Please install ML dependencies with: pip install -r requirements-ml.txt")
    sys.exit(1)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class DataLoader:
    """Handle data loading from CSV or MongoDB sources."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_config = config.get('data', {})
    
    def load_data(self) -> pd.DataFrame:
        """Load data based on configuration."""
        source = os.getenv('DATA_SOURCE', self.data_config.get('source', 'csv'))
        
        if source == 'csv':
            return self._load_csv()
        elif source == 'mongodb':
            return self._load_mongodb()
        else:
            raise ValueError(f"Unsupported data source: {source}")
    
    def _load_csv(self) -> pd.DataFrame:
        """Load data from CSV file."""
        csv_path = os.getenv('CSV_PATH', self.data_config.get('csv_path', 'data/sample_data.csv'))
        
        if not os.path.exists(csv_path):
            # Create sample data if file doesn't exist
            logger.warning(f"CSV file {csv_path} not found. Creating sample data...")
            return self._create_sample_data()
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows from {csv_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            logger.info("Creating sample data as fallback...")
            return self._create_sample_data()
    
    def _load_mongodb(self) -> pd.DataFrame:
        """Load data from MongoDB."""
        if not PYMONGO_AVAILABLE:
            raise ImportError("PyMongo not available. Install with: pip install pymongo[srv]")
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        try:
            client = MongoClient(mongodb_uri)
            db_name = mongodb_uri.split("/")[-1].split("?")[0]
            collection_name = self.data_config.get('mongodb_collection', 'price_data')
            
            collection = client[db_name][collection_name]
            cursor = collection.find().sort("timestamp", 1)
            df = pd.DataFrame(list(cursor))
            
            logger.info(f"Loaded {len(df)} rows from MongoDB collection {collection_name}")
            return df
        except Exception as e:
            logger.error(f"Error loading from MongoDB: {e}")
            logger.info("Creating sample data as fallback...")
            return self._create_sample_data()
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Create sample financial data for demonstration."""
        logger.info("Generating sample financial data...")
        
        # Create synthetic price data
        np.random.seed(42)
        n_samples = 1000
        
        # Generate price series with some trend and volatility
        prices = []
        price = 50000  # Starting price
        
        for i in range(n_samples):
            # Random walk with slight upward bias
            change = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
            price *= (1 + change)
            prices.append(price)
        
        # Create timestamps
        timestamps = pd.date_range(start='2023-01-01', periods=n_samples, freq='1H')
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'close': prices,
            'volume': np.random.lognormal(10, 1, n_samples)
        })
        
        logger.info(f"Created sample dataset with {len(df)} rows")
        return df


class FeatureEngineer:
    """Handle feature engineering including technical indicators."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ta_config = config.get('data', {}).get('technical_indicators', [])
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators and other features."""
        if not TA_AVAILABLE:
            logger.warning("Technical Analysis library not available. Using basic features only.")
            return self._basic_features(df)
        
        df = df.copy()
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Add technical indicators
        for indicator in self.ta_config:
            try:
                if indicator == "sma_5":
                    df['sma_5'] = ta.trend.sma_indicator(df['close'], window=5)
                elif indicator == "sma_20":
                    df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
                elif indicator == "ema_12":
                    df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
                elif indicator == "ema_26":
                    df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
                elif indicator == "rsi_14":
                    df['rsi_14'] = ta.momentum.rsi(df['close'], window=14)
                elif indicator == "macd":
                    macd_line = ta.trend.macd(df['close'])
                    df['macd'] = macd_line
                elif indicator == "bb_upper":
                    bb_upper = ta.volatility.bollinger_hband(df['close'])
                    df['bb_upper'] = bb_upper
                elif indicator == "bb_lower":
                    bb_lower = ta.volatility.bollinger_lband(df['close'])
                    df['bb_lower'] = bb_lower
                elif indicator == "atr_14":
                    df['atr_14'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
                elif indicator == "volume_sma_10":
                    df['volume_sma_10'] = ta.volume.volume_sma(df['close'], df['volume'], window=10)
                
            except Exception as e:
                logger.warning(f"Error adding indicator {indicator}: {e}")
        
        # Add price-based features
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['volume_price_trend'] = df['volume'] * df['price_change']
        
        logger.info(f"Added {len([col for col in df.columns if col not in required_cols + ['timestamp']])} features")
        return df
    
    def _basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic features when TA library is not available."""
        df = df.copy()
        
        # Basic price features
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['volume_price_trend'] = df['volume'] * df['price_change']
        
        # Simple moving averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Simple RSI approximation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        logger.info("Added basic features (TA library not available)")
        return df


class TargetBuilder:
    """Build prediction targets from price data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.target_config = config.get('data', {}).get('target', {})
    
    def build_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build prediction target based on configuration."""
        df = df.copy()
        
        target_type = self.target_config.get('type', 'direction')
        horizon = self.target_config.get('horizon', 1)
        threshold = self.target_config.get('threshold', 0.001)
        
        if target_type == 'direction':
            # Predict price direction (up/down)
            future_price = df['close'].shift(-horizon)
            price_change = (future_price - df['close']) / df['close']
            df['target'] = (price_change > threshold).astype(int)
        
        elif target_type == 'returns':
            # Predict future returns
            future_price = df['close'].shift(-horizon)
            df['target'] = (future_price - df['close']) / df['close']
        
        elif target_type == 'volatility':
            # Predict future volatility
            returns = df['close'].pct_change()
            df['target'] = returns.rolling(window=horizon).std().shift(-horizon)
        
        else:
            raise ValueError(f"Unsupported target type: {target_type}")
        
        # Remove rows with missing targets
        df = df.dropna(subset=['target'])
        
        logger.info(f"Built target '{target_type}' with horizon {horizon}")
        return df


class GBTModel:
    """Gradient Boosted Trees model wrapper."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_config = config.get('model', {})
        self.model_type = os.getenv('MODEL_TYPE', config.get('model_type', 'lightgbm'))
        self.model = None
    
    def create_model(self, params: Optional[Dict] = None):
        """Create model instance with given parameters."""
        if params is None:
            params = self.model_config.get(self.model_type, {})
        
        if self.model_type == 'lightgbm':
            if not LIGHTGBM_AVAILABLE:
                raise ImportError("LightGBM not available. Install with: pip install lightgbm")
            self.model = lgb.LGBMClassifier(**params)
        
        elif self.model_type == 'xgboost':
            if not XGBOOST_AVAILABLE:
                raise ImportError("XGBoost not available. Install with: pip install xgboost")
            self.model = xgb.XGBClassifier(**params)
        
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train the model."""
        if self.model is None:
            self.create_model()
        
        if X_val is not None and y_val is not None:
            if self.model_type == 'lightgbm':
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
                )
            elif self.model_type == 'xgboost':
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=50,
                    verbose=False
                )
        else:
            self.model.fit(X_train, y_train)
    
    def predict_proba(self, X):
        """Get prediction probabilities."""
        return self.model.predict_proba(X)
    
    def predict(self, X):
        """Get predictions."""
        return self.model.predict(X)


class OptunaTuner:
    """Hyperparameter optimization using Optuna."""
    
    def __init__(self, config: Dict[str, Any], model_wrapper: GBTModel):
        self.config = config
        self.optuna_config = config.get('optuna', {})
        self.model_wrapper = model_wrapper
        self.study = None
    
    def optimize(self, X, y) -> Dict[str, Any]:
        """Run hyperparameter optimization."""
        n_trials = int(os.getenv('OPTUNA_TRIALS', self.optuna_config.get('n_trials', 100)))
        timeout = self.optuna_config.get('timeout', 3600)
        
        study_name = self.optuna_config.get('study_name', 'gbt_optimization')
        direction = self.optuna_config.get('optimization_direction', 'maximize')
        
        self.study = optuna.create_study(
            study_name=study_name,
            direction=direction,
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Setup cross-validation
        cv_config = self.config.get('cv', {})
        n_splits = int(os.getenv('N_SPLITS', cv_config.get('n_splits', 5)))
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        def objective(trial):
            # Get parameter search space
            search_space = self.optuna_config.get('search_space', {}).get(self.model_wrapper.model_type, {})
            
            params = {}
            for param_name, param_range in search_space.items():
                if isinstance(param_range, list) and len(param_range) == 2:
                    if isinstance(param_range[0], int):
                        params[param_name] = trial.suggest_int(param_name, param_range[0], param_range[1])
                    else:
                        params[param_name] = trial.suggest_float(param_name, param_range[0], param_range[1])
            
            # Cross-validation
            cv_scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
                y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
                
                # Create and train model
                self.model_wrapper.create_model(params)
                self.model_wrapper.train(X_train_fold, y_train_fold, X_val_fold, y_val_fold)
                
                # Evaluate
                y_pred_proba = self.model_wrapper.predict_proba(X_val_fold)[:, 1]
                score = roc_auc_score(y_val_fold, y_pred_proba)
                cv_scores.append(score)
            
            return np.mean(cv_scores)
        
        logger.info(f"Starting optimization with {n_trials} trials...")
        self.study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=True)
        
        logger.info(f"Best AUC: {self.study.best_value:.4f}")
        logger.info(f"Best parameters: {self.study.best_params}")
        
        return self.study.best_params


class TrainingPipeline:
    """Main training pipeline orchestrator."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.artifacts_path = Path(self.config.get('training', {}).get('artifacts_path', 'models'))
        self.artifacts_path.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    def run(self):
        """Execute the full training pipeline."""
        logger.info("🚀 Starting GBT Training Pipeline")
        
        # 1. Load data
        logger.info("📂 Loading data...")
        data_loader = DataLoader(self.config)
        df = data_loader.load_data()
        
        # 2. Feature engineering
        logger.info("🔧 Engineering features...")
        feature_engineer = FeatureEngineer(self.config)
        df = feature_engineer.engineer_features(df)
        
        # 3. Build targets
        logger.info("🎯 Building targets...")
        target_builder = TargetBuilder(self.config)
        df = target_builder.build_target(df)
        
        # 4. Prepare features and targets
        feature_cols = [col for col in df.columns if col not in ['timestamp', 'target']]
        X = df[feature_cols].select_dtypes(include=[np.number])  # Only numeric features
        y = df['target']
        
        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X, y = X[mask], y[mask]
        
        logger.info(f"📊 Dataset: {len(X)} samples, {len(X.columns)} features")
        logger.info(f"📊 Target distribution: {y.value_counts().to_dict()}")
        
        # 5. Model setup
        model_wrapper = GBTModel(self.config)
        
        # 6. Hyperparameter optimization
        logger.info("🔍 Optimizing hyperparameters...")
        tuner = OptunaTuner(self.config, model_wrapper)
        best_params = tuner.optimize(X, y)
        
        # 7. Final model training
        logger.info("🏋️ Training final model...")
        model_wrapper.create_model(best_params)
        
        # Train/validation split for final training
        cv_config = self.config.get('cv', {})
        test_size = cv_config.get('test_size', 0.2)
        split_idx = int(len(X) * (1 - test_size))
        
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        model_wrapper.train(X_train, y_train, X_val, y_val)
        
        # 8. Final evaluation
        y_pred_proba = model_wrapper.predict_proba(X_val)[:, 1]
        y_pred = model_wrapper.predict(X_val)
        
        final_auc = roc_auc_score(y_val, y_pred_proba)
        
        logger.info(f"✅ Final AUC: {final_auc:.4f}")
        print(f"\n🎉 Training completed! Best AUC: {final_auc:.4f}")
        
        # 9. Save artifacts
        if self.config.get('training', {}).get('save_artifacts', True):
            self._save_artifacts(model_wrapper, X.columns.tolist(), best_params, final_auc)
    
    def _save_artifacts(self, model_wrapper: GBTModel, feature_columns: list, best_params: dict, final_auc: float):
        """Save model and metadata artifacts."""
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"{model_wrapper.model_type}_{timestamp}"
        
        # Save model
        model_path = self.artifacts_path / f"{model_name}.pkl"
        joblib.dump(model_wrapper.model, model_path)
        logger.info(f"💾 Model saved to {model_path}")
        
        # Save metadata
        metadata = {
            'model_type': model_wrapper.model_type,
            'timestamp': timestamp,
            'feature_columns': feature_columns,
            'best_params': best_params,
            'final_auc': final_auc,
            'config': self.config
        }
        
        metadata_path = self.artifacts_path / f"{model_name}_metadata.yaml"
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        logger.info(f"📋 Metadata saved to {metadata_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ultra Trader GBT Training Pipeline')
    parser.add_argument(
        '--config',
        default='configs/experiments/gbt_default.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    try:
        pipeline = TrainingPipeline(args.config)
        pipeline.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()