# investlib-optimizer

MyInvest V0.3 - Parameter Optimization Library

## Features

- **Grid Search**: Exhaustive parameter space exploration
- **Walk-Forward Validation**: Rolling window train/test splits
- **Overfitting Detection**: Automatic detection when train/test Sharpe diverges
- **Heatmap Visualization**: Plotly-based parameter performance visualization

## Installation

```bash
pip install -e .
```

## Usage

```python
from investlib_optimizer import GridSearchOptimizer, WalkForwardValidator

# Define parameter space
param_space = {
    'stop_loss_pct': [5, 10, 15],
    'take_profit_pct': [10, 15, 20, 25],
    'position_size_pct': [10, 15, 20]
}

# Run grid search
optimizer = GridSearchOptimizer()
results = optimizer.run_grid_search(strategy, symbol, data, param_space)

# Walk-forward validation
validator = WalkForwardValidator()
train_sharpe, test_sharpe = validator.run_walk_forward(
    strategy, data, best_params
)
```

## Components

- `grid_search.py`: Grid search engine with parallel execution
- `walk_forward.py`: Walk-forward validation framework
- `overfitting.py`: Overfitting detection (FR-017)
- `visualizer.py`: Plotly heatmap generation
