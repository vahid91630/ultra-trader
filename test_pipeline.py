#!/usr/bin/env python3
"""
Test script for Ultra Trader ML Pipeline

Tests core functionality without requiring full ML dependencies.
Can be used to validate the pipeline structure and basic operations.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_directory_structure():
    """Test that all required directories exist."""
    print("🧪 Testing directory structure...")
    
    required_dirs = [
        'training',
        'evaluation', 
        'analysis',
        'configs/experiments',
        'services',
        'docs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories exist")
        return True

def test_file_structure():
    """Test that all required files exist."""
    print("🧪 Testing file structure...")
    
    required_files = [
        'training/pipeline_gbt.py',
        'evaluation/backtest.py',
        'analysis/explainability.py',
        'configs/experiments/gbt_default.yaml',
        'services/llm_analysis.py',
        'docs/ML_PIPELINE.md',
        'requirements-ml.txt',
        '.gitignore'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_config_loading():
    """Test YAML configuration loading."""
    print("🧪 Testing configuration loading...")
    
    try:
        import yaml
        config_path = project_root / 'configs' / 'experiments' / 'gbt_default.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required config sections
        required_sections = ['experiment_name', 'model_type', 'data', 'model', 'cv', 'optuna', 'training']
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            print(f"❌ Missing config sections: {missing_sections}")
            return False
        else:
            print("✅ Configuration loading successful")
            return True
            
    except ImportError:
        print("⚠️ PyYAML not available, skipping config test")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_backtest_module():
    """Test backtesting functionality."""
    print("🧪 Testing backtesting module...")
    
    try:
        from evaluation.backtest import BacktestEngine
        
        # Create sample data
        np.random.seed(42)
        n_periods = 100
        prices = pd.Series([100 * (1 + np.random.normal(0.001, 0.02))**i for i in range(n_periods)])
        signals = pd.Series((np.random.random(n_periods) > 0.5).astype(int))
        
        # Run backtest
        engine = BacktestEngine(initial_capital=10000, fee_rate=0.001)
        results = engine.run_backtest(signals, prices)
        
        # Check results structure
        required_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        missing_metrics = [metric for metric in required_metrics if metric not in results]
        
        if missing_metrics:
            print(f"❌ Missing backtest metrics: {missing_metrics}")
            return False
        else:
            print(f"✅ Backtesting successful - Sharpe: {results['sharpe_ratio']:.3f}")
            return True
            
    except Exception as e:
        print(f"❌ Backtesting test failed: {e}")
        return False

def test_llm_service():
    """Test LLM analysis service."""
    print("🧪 Testing LLM analysis service...")
    
    try:
        from services.llm_analysis import LLMAnalyzer
        
        # Create analyzer (should work without API key)
        analyzer = LLMAnalyzer()
        
        # Test disabled state
        if not analyzer.is_enabled():
            print("✅ LLM service correctly disabled without API key")
            
            # Test fallback messages
            sample_data = pd.DataFrame({
                'close': [100, 101, 102, 103, 104],
                'open': [100, 101, 102, 103, 104],
                'high': [101, 102, 103, 104, 105],
                'low': [99, 100, 101, 102, 103],
                'volume': [1000, 1100, 1200, 1300, 1400]
            })
            
            analysis = analyzer.analyze_market_data(sample_data)
            if "LLM Market Analysis (Disabled)" in analysis:
                print("✅ Fallback message working correctly")
                return True
            else:
                print("❌ Fallback message not working")
                return False
        else:
            print("⚠️ LLM service enabled (API key found)")
            return True
            
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        return False

def test_imports():
    """Test that core modules can be imported."""
    print("🧪 Testing module imports...")
    
    modules_to_test = [
        ('evaluation.backtest', 'BacktestEngine'),
        ('services.llm_analysis', 'LLMAnalyzer'),
    ]
    
    failed_imports = []
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
        except Exception as e:
            failed_imports.append(f"{module_name}.{class_name}: {e}")
    
    if failed_imports:
        print(f"❌ Import failures: {failed_imports}")
        return False
    else:
        print("✅ All core modules importable")
        return True

def test_ml_dependencies():
    """Test availability of ML dependencies."""
    print("🧪 Testing ML dependencies...")
    
    required_deps = [
        'pandas',
        'numpy', 
        'yaml'
    ]
    
    optional_deps = [
        'sklearn',
        'lightgbm',
        'xgboost',
        'optuna',
        'shap',
        'ta'
    ]
    
    missing_required = []
    missing_optional = []
    
    # Test required dependencies
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_required.append(dep)
    
    # Test optional dependencies
    for dep in optional_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_optional.append(dep)
    
    if missing_required:
        print(f"❌ Missing required dependencies: {missing_required}")
        return False
    else:
        print("✅ All required dependencies available")
        if missing_optional:
            print(f"⚠️ Missing optional ML dependencies: {missing_optional}")
            print("   Install with: pip install -r requirements-ml.txt")
        else:
            print("✅ All ML dependencies available")
        return True

def run_all_tests():
    """Run all tests and summarize results."""
    print("🚀 Starting Ultra Trader ML Pipeline Tests\n")
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("File Structure", test_file_structure), 
        ("Module Imports", test_imports),
        ("Dependencies", test_ml_dependencies),
        ("Configuration Loading", test_config_loading),
        ("Backtesting", test_backtest_module),
        ("LLM Service", test_llm_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
            print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The ML pipeline is ready.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)