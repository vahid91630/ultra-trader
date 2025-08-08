#!/usr/bin/env python3
"""
Ultra Trader Explainability Module

SHAP-based model explainability for understanding feature importance
and model predictions in trading strategies.

Usage:
    from analysis.explainability import SHAPAnalyzer
    
    analyzer = SHAPAnalyzer(model, X_train)
    analyzer.generate_summary_plot(X_test)
    importance = analyzer.get_feature_importance()
"""

import warnings
from typing import Dict, List, Optional, Union, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Graceful dependency handling
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    SHAP_AVAILABLE = False
    try:
        import shap
        SHAP_AVAILABLE = True
    except ImportError:
        logger.warning("SHAP not available. Install with: pip install shap")

except ImportError as e:
    logger.error(f"Critical dependency missing: {e}")
    logger.error("Please install ML dependencies with: pip install -r requirements-ml.txt")
    raise

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class SHAPAnalyzer:
    """
    SHAP-based explainability analyzer for ML trading models.
    
    Provides feature importance analysis, prediction explanations,
    and visualization capabilities.
    """
    
    def __init__(
        self,
        model: Any,
        X_background: pd.DataFrame,
        model_type: str = "tree",
        max_evals: int = 1000
    ):
        """
        Initialize SHAP analyzer.
        
        Args:
            model: Trained model (LightGBM, XGBoost, or sklearn-compatible)
            X_background: Background dataset for SHAP explainer
            model_type: Type of model ("tree", "linear", "kernel")
            max_evals: Maximum evaluations for kernel explainer
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP not available. Install with: pip install shap")
        
        self.model = model
        self.X_background = X_background
        self.model_type = model_type
        self.max_evals = max_evals
        self.explainer = None
        self.shap_values = None
        
        self._initialize_explainer()
    
    def _initialize_explainer(self):
        """Initialize appropriate SHAP explainer based on model type."""
        try:
            if self.model_type == "tree":
                # For tree-based models (LightGBM, XGBoost, RandomForest)
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("Initialized TreeExplainer")
            
            elif self.model_type == "linear":
                # For linear models
                self.explainer = shap.LinearExplainer(self.model, self.X_background)
                logger.info("Initialized LinearExplainer")
            
            elif self.model_type == "kernel":
                # For black-box models
                self.explainer = shap.KernelExplainer(
                    self.model.predict_proba, 
                    self.X_background,
                    link="logit"
                )
                logger.info("Initialized KernelExplainer")
            
            else:
                # Try to auto-detect explainer
                self.explainer = shap.Explainer(self.model, self.X_background)
                logger.info("Initialized auto-detected Explainer")
                
        except Exception as e:
            logger.warning(f"Error initializing {self.model_type} explainer: {e}")
            logger.info("Falling back to kernel explainer...")
            
            # Fallback to kernel explainer
            def predict_func(X):
                if hasattr(self.model, 'predict_proba'):
                    return self.model.predict_proba(X)[:, 1]
                else:
                    return self.model.predict(X)
            
            self.explainer = shap.KernelExplainer(
                predict_func,
                self.X_background.sample(min(100, len(self.X_background))),  # Smaller background for speed
                link="identity"
            )
            logger.info("Initialized fallback KernelExplainer")
    
    def calculate_shap_values(self, X: pd.DataFrame, max_samples: int = 500) -> np.ndarray:
        """
        Calculate SHAP values for given dataset.
        
        Args:
            X: Input features
            max_samples: Maximum number of samples to analyze (for performance)
        
        Returns:
            SHAP values array
        """
        if self.explainer is None:
            raise ValueError("Explainer not initialized")
        
        # Limit samples for performance
        X_sample = X.sample(min(max_samples, len(X))) if len(X) > max_samples else X
        
        try:
            if self.model_type == "kernel":
                # Kernel explainer is slower, use fewer evaluations
                shap_values = self.explainer.shap_values(X_sample, nsamples=min(self.max_evals, 100))
            else:
                shap_values = self.explainer.shap_values(X_sample)
            
            # Handle different SHAP value formats
            if isinstance(shap_values, list):
                # Multi-class case, take positive class
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            self.shap_values = shap_values
            logger.info(f"Calculated SHAP values for {len(X_sample)} samples")
            
            return shap_values
            
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            raise
    
    def get_feature_importance(
        self, 
        X: Optional[pd.DataFrame] = None,
        method: str = "mean_abs"
    ) -> pd.Series:
        """
        Get feature importance based on SHAP values.
        
        Args:
            X: Input features (if None, uses cached SHAP values)
            method: Importance calculation method ("mean_abs", "mean", "std")
        
        Returns:
            Feature importance series
        """
        if X is not None:
            shap_values = self.calculate_shap_values(X)
        elif self.shap_values is not None:
            shap_values = self.shap_values
        else:
            raise ValueError("No SHAP values available. Provide X or calculate SHAP values first.")
        
        feature_names = self.X_background.columns.tolist()
        
        if method == "mean_abs":
            importance = np.mean(np.abs(shap_values), axis=0)
        elif method == "mean":
            importance = np.mean(shap_values, axis=0)
        elif method == "std":
            importance = np.std(shap_values, axis=0)
        else:
            raise ValueError(f"Unknown importance method: {method}")
        
        importance_series = pd.Series(importance, index=feature_names)
        importance_series = importance_series.sort_values(ascending=False)
        
        return importance_series
    
    def generate_summary_plot(
        self,
        X: pd.DataFrame,
        max_display: int = 20,
        figsize: tuple = (10, 8),
        save_path: Optional[str] = None
    ) -> None:
        """
        Generate SHAP summary plot.
        
        Args:
            X: Input features
            max_display: Maximum number of features to display
            figsize: Figure size
            save_path: Optional path to save plot
        """
        shap_values = self.calculate_shap_values(X)
        
        plt.figure(figsize=figsize)
        shap.summary_plot(
            shap_values,
            X.iloc[:len(shap_values)],  # Ensure same length
            max_display=max_display,
            show=False
        )
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Summary plot saved to {save_path}")
        
        plt.show()
    
    def generate_beeswarm_plot(
        self,
        X: pd.DataFrame,
        max_display: int = 20,
        figsize: tuple = (10, 8),
        save_path: Optional[str] = None
    ) -> None:
        """
        Generate SHAP beeswarm plot.
        
        Args:
            X: Input features
            max_display: Maximum number of features to display
            figsize: Figure size
            save_path: Optional path to save plot
        """
        shap_values = self.calculate_shap_values(X)
        
        plt.figure(figsize=figsize)
        shap.plots.beeswarm(
            shap.Explanation(
                values=shap_values,
                data=X.iloc[:len(shap_values)].values,
                feature_names=X.columns.tolist()
            ),
            max_display=max_display,
            show=False
        )
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Beeswarm plot saved to {save_path}")
        
        plt.show()
    
    def generate_waterfall_plot(
        self,
        X: pd.DataFrame,
        instance_idx: int = 0,
        figsize: tuple = (10, 6),
        save_path: Optional[str] = None
    ) -> None:
        """
        Generate SHAP waterfall plot for a single prediction.
        
        Args:
            X: Input features
            instance_idx: Index of instance to explain
            figsize: Figure size
            save_path: Optional path to save plot
        """
        shap_values = self.calculate_shap_values(X)
        
        if instance_idx >= len(shap_values):
            raise ValueError(f"Instance index {instance_idx} out of range")
        
        plt.figure(figsize=figsize)
        shap.plots.waterfall(
            shap.Explanation(
                values=shap_values[instance_idx],
                base_values=self.explainer.expected_value if hasattr(self.explainer, 'expected_value') else 0,
                data=X.iloc[instance_idx].values,
                feature_names=X.columns.tolist()
            ),
            show=False
        )
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Waterfall plot saved to {save_path}")
        
        plt.show()
    
    def get_top_features(
        self,
        X: pd.DataFrame,
        n_features: int = 10,
        method: str = "mean_abs"
    ) -> List[str]:
        """
        Get top N most important features.
        
        Args:
            X: Input features
            n_features: Number of top features to return
            method: Importance calculation method
        
        Returns:
            List of top feature names
        """
        importance = self.get_feature_importance(X, method=method)
        return importance.head(n_features).index.tolist()
    
    def explain_prediction(
        self,
        X: pd.DataFrame,
        instance_idx: int = 0,
        n_features: int = 10
    ) -> Dict[str, float]:
        """
        Explain a single prediction with top contributing features.
        
        Args:
            X: Input features
            instance_idx: Index of instance to explain
            n_features: Number of top features to show
        
        Returns:
            Dictionary of feature contributions
        """
        shap_values = self.calculate_shap_values(X)
        
        if instance_idx >= len(shap_values):
            raise ValueError(f"Instance index {instance_idx} out of range")
        
        feature_names = X.columns.tolist()
        contributions = dict(zip(feature_names, shap_values[instance_idx]))
        
        # Sort by absolute contribution
        sorted_contributions = sorted(
            contributions.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )
        
        return dict(sorted_contributions[:n_features])


class ModelInterpretability:
    """
    High-level model interpretability class combining multiple explainability techniques.
    """
    
    def __init__(self, model: Any, X_train: pd.DataFrame, model_type: str = "tree"):
        """
        Initialize interpretability analyzer.
        
        Args:
            model: Trained model
            X_train: Training features for background
            model_type: Type of model for SHAP explainer selection
        """
        self.model = model
        self.X_train = X_train
        self.model_type = model_type
        
        # Initialize SHAP analyzer if available
        self.shap_analyzer = None
        if SHAP_AVAILABLE:
            try:
                # Use a sample of training data as background
                background_size = min(100, len(X_train))
                X_background = X_train.sample(background_size, random_state=42)
                self.shap_analyzer = SHAPAnalyzer(model, X_background, model_type)
                logger.info("SHAP analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize SHAP analyzer: {e}")
    
    def generate_feature_importance_report(
        self,
        X_test: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feature importance report.
        
        Args:
            X_test: Test features
            save_path: Optional path to save report
        
        Returns:
            Dictionary containing importance metrics and plots
        """
        report = {}
        
        # SHAP-based importance
        if self.shap_analyzer:
            try:
                shap_importance = self.shap_analyzer.get_feature_importance(X_test)
                report['shap_importance'] = shap_importance
                
                # Generate plots
                if save_path:
                    summary_path = save_path.replace('.png', '_summary.png')
                    beeswarm_path = save_path.replace('.png', '_beeswarm.png')
                    
                    self.shap_analyzer.generate_summary_plot(X_test, save_path=summary_path)
                    self.shap_analyzer.generate_beeswarm_plot(X_test, save_path=beeswarm_path)
                
                logger.info("SHAP importance analysis completed")
                
            except Exception as e:
                logger.warning(f"SHAP analysis failed: {e}")
        
        # Model-specific feature importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            model_importance = pd.Series(
                self.model.feature_importances_,
                index=X_test.columns
            ).sort_values(ascending=False)
            report['model_importance'] = model_importance
        
        return report
    
    def create_interpretability_dashboard(
        self,
        X_test: pd.DataFrame,
        y_test: Optional[pd.Series] = None,
        save_dir: Optional[str] = None
    ) -> None:
        """
        Create comprehensive interpretability dashboard.
        
        Args:
            X_test: Test features
            y_test: Optional test targets
            save_dir: Directory to save dashboard plots
        """
        if save_dir:
            import os
            os.makedirs(save_dir, exist_ok=True)
        
        # Feature importance comparison
        plt.figure(figsize=(15, 10))
        
        if self.shap_analyzer:
            plt.subplot(2, 2, 1)
            shap_importance = self.shap_analyzer.get_feature_importance(X_test)
            shap_importance.head(15).plot(kind='barh', title='SHAP Feature Importance')
            plt.xlabel('Mean |SHAP Value|')
        
        if hasattr(self.model, 'feature_importances_'):
            plt.subplot(2, 2, 2)
            model_importance = pd.Series(
                self.model.feature_importances_,
                index=X_test.columns
            ).sort_values(ascending=False)
            model_importance.head(15).plot(kind='barh', title='Model Feature Importance')
            plt.xlabel('Importance Score')
        
        # Prediction distribution
        if hasattr(self.model, 'predict_proba'):
            plt.subplot(2, 2, 3)
            probas = self.model.predict_proba(X_test)[:, 1]
            plt.hist(probas, bins=50, alpha=0.7, edgecolor='black')
            plt.title('Prediction Probability Distribution')
            plt.xlabel('Predicted Probability')
            plt.ylabel('Frequency')
        
        # Correlation with target (if available)
        if y_test is not None and self.shap_analyzer:
            plt.subplot(2, 2, 4)
            shap_importance = self.shap_analyzer.get_feature_importance(X_test)
            top_features = shap_importance.head(10).index
            
            correlations = []
            for feature in top_features:
                if feature in X_test.columns:
                    corr = X_test[feature].corr(y_test)
                    correlations.append(corr)
                else:
                    correlations.append(0)
            
            corr_series = pd.Series(correlations, index=top_features)
            corr_series.plot(kind='barh', title='Feature-Target Correlation (Top 10)')
            plt.xlabel('Correlation')
        
        plt.tight_layout()
        
        if save_dir:
            dashboard_path = os.path.join(save_dir, 'interpretability_dashboard.png')
            plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
            logger.info(f"Dashboard saved to {dashboard_path}")
        
        plt.show()


# Demo and testing functions
def _demo_explainability():
    """Demonstrate explainability functionality with synthetic data."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        
        # Generate synthetic data
        X, y = make_classification(
            n_samples=1000,
            n_features=20,
            n_informative=10,
            n_redundant=5,
            random_state=42
        )
        
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        X_df = pd.DataFrame(X, columns=feature_names)
        y_series = pd.Series(y)
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_df, y_series)
        
        # Create interpretability analyzer
        interpreter = ModelInterpretability(model, X_df, model_type="tree")
        
        # Generate report
        report = interpreter.generate_feature_importance_report(X_df)
        
        print("Feature Importance Demo:")
        print("-" * 40)
        if 'shap_importance' in report:
            print("Top 10 SHAP Important Features:")
            print(report['shap_importance'].head(10))
        
        if 'model_importance' in report:
            print("\nTop 10 Model Important Features:")
            print(report['model_importance'].head(10))
        
        return report
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return None


if __name__ == "__main__":
    _demo_explainability()