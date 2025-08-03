"""
Parameter optimization module for finding optimal strategy parameters.
Uses grid search, genetic algorithms, and walk-forward analysis.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from itertools import product
import structlog
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

from config import get_settings, update_strategy_params
from backtesting.backtest_engine import get_backtest_engine

logger = structlog.get_logger()


@dataclass
class OptimizationResult:
    """Optimization result data structure."""
    parameters: Dict[str, Any]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    score: float  # Combined score for ranking


class ParameterOptimizer:
    """Parameter optimization using multiple methods."""
    
    def __init__(self):
        self.settings = get_settings()
        self.backtest_engine = None
        self.results = []
    
    async def initialize(self):
        """Initialize the optimizer."""
        self.backtest_engine = await get_backtest_engine()
    
    async def grid_search(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, List[Any]],
        initial_capital: float = 100000.0,
        max_workers: int = None
    ) -> List[OptimizationResult]:
        """Perform grid search optimization."""
        try:
            logger.info("Starting grid search optimization")
            
            # Generate all parameter combinations
            param_names = list(parameter_ranges.keys())
            param_values = list(parameter_ranges.values())
            combinations = list(product(*param_values))
            
            logger.info(f"Testing {len(combinations)} parameter combinations")
            
            # Run backtests in parallel
            if max_workers is None:
                max_workers = min(mp.cpu_count(), 8)
            
            results = []
            
            # Process combinations in batches
            batch_size = max_workers
            for i in range(0, len(combinations), batch_size):
                batch = combinations[i:i + batch_size]
                
                # Create tasks for batch
                tasks = []
                for params in batch:
                    param_dict = dict(zip(param_names, params))
                    task = self._run_backtest_with_params(
                        symbols, start_date, end_date, param_dict, initial_capital
                    )
                    tasks.append(task)
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error in batch {i//batch_size}, combination {j}: {result}")
                        continue
                    
                    if result:
                        results.append(result)
                
                logger.info(f"Completed batch {i//batch_size + 1}/{(len(combinations) + batch_size - 1)//batch_size}")
            
            # Sort results by score
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Grid search completed. Found {len(results)} valid results")
            return results
            
        except Exception as e:
            logger.error(f"Error in grid search: {e}")
            return []
    
    async def _run_backtest_with_params(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameters: Dict[str, Any],
        initial_capital: float
    ) -> Optional[OptimizationResult]:
        """Run backtest with specific parameters."""
        try:
            # Update parameters
            update_strategy_params(parameters)
            
            # Run backtest
            results = await self.backtest_engine.run_backtest(
                symbols, start_date, end_date, initial_capital
            )
            
            if not results:
                return None
            
            # Calculate combined score
            score = self._calculate_score(results)
            
            return OptimizationResult(
                parameters=parameters,
                total_return=results.total_return,
                sharpe_ratio=results.sharpe_ratio,
                max_drawdown=results.max_drawdown_pct,
                win_rate=results.win_rate,
                profit_factor=results.profit_factor,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error running backtest with parameters {parameters}: {e}")
            return None
    
    def _calculate_score(self, results) -> float:
        """Calculate combined score for ranking results."""
        try:
            # Weighted combination of metrics
            weights = {
                'sharpe_ratio': 0.3,
                'total_return_pct': 0.25,
                'win_rate': 0.2,
                'profit_factor': 0.15,
                'max_drawdown': 0.1
            }
            
            # Normalize metrics
            sharpe_score = min(results.sharpe_ratio / 2.0, 1.0)  # Cap at 2.0
            return_score = min(results.total_return_pct / 0.5, 1.0)  # Cap at 50%
            win_score = results.win_rate
            profit_score = min(results.profit_factor / 3.0, 1.0)  # Cap at 3.0
            drawdown_score = 1.0 - results.max_drawdown_pct  # Lower is better
            
            # Calculate weighted score
            score = (
                weights['sharpe_ratio'] * sharpe_score +
                weights['total_return_pct'] * return_score +
                weights['win_rate'] * win_score +
                weights['profit_factor'] * profit_score +
                weights['max_drawdown'] * drawdown_score
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return 0.0
    
    async def walk_forward_optimization(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, List[Any]],
        window_size: int = 252,  # 1 year
        step_size: int = 63,      # 3 months
        initial_capital: float = 100000.0
    ) -> List[OptimizationResult]:
        """Perform walk-forward optimization."""
        try:
            logger.info("Starting walk-forward optimization")
            
            # Generate time windows
            windows = self._generate_windows(start_date, end_date, window_size, step_size)
            
            results = []
            
            for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
                logger.info(f"Processing window {i+1}/{len(windows)}")
                
                # Optimize on training period
                train_results = await self.grid_search(
                    symbols, train_start, train_end, parameter_ranges, initial_capital
                )
                
                if not train_results:
                    continue
                
                # Get best parameters from training
                best_params = train_results[0].parameters
                
                # Test on out-of-sample period
                test_result = await self._run_backtest_with_params(
                    symbols, test_start, test_end, best_params, initial_capital
                )
                
                if test_result:
                    test_result.parameters['window'] = i
                    test_result.parameters['train_period'] = f"{train_start.date()} - {train_end.date()}"
                    test_result.parameters['test_period'] = f"{test_start.date()} - {test_end.date()}"
                    results.append(test_result)
            
            # Sort by score
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Walk-forward optimization completed. Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in walk-forward optimization: {e}")
            return []
    
    def _generate_windows(
        self,
        start_date: datetime,
        end_date: datetime,
        window_size: int,
        step_size: int
    ) -> List[Tuple[datetime, datetime, datetime, datetime]]:
        """Generate training and testing windows."""
        windows = []
        current_start = start_date
        
        while current_start + timedelta(days=window_size) < end_date:
            train_end = current_start + timedelta(days=window_size)
            test_start = train_end
            test_end = min(test_start + timedelta(days=step_size), end_date)
            
            if test_end > test_start:
                windows.append((current_start, train_end, test_start, test_end))
            
            current_start += timedelta(days=step_size)
        
        return windows
    
    async def genetic_optimization(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, List[Any]],
        population_size: int = 50,
        generations: int = 20,
        mutation_rate: float = 0.1,
        initial_capital: float = 100000.0
    ) -> List[OptimizationResult]:
        """Perform genetic algorithm optimization."""
        try:
            logger.info("Starting genetic optimization")
            
            # Initialize population
            population = self._initialize_population(parameter_ranges, population_size)
            best_results = []
            
            for generation in range(generations):
                logger.info(f"Generation {generation + 1}/{generations}")
                
                # Evaluate population
                results = []
                for individual in population:
                    result = await self._run_backtest_with_params(
                        symbols, start_date, end_date, individual, initial_capital
                    )
                    if result:
                        results.append(result)
                
                # Sort by fitness
                results.sort(key=lambda x: x.score, reverse=True)
                
                # Store best results
                best_results.extend(results[:5])
                
                # Selection and crossover
                new_population = self._selection_crossover(results, population_size)
                
                # Mutation
                new_population = self._mutation(new_population, parameter_ranges, mutation_rate)
                
                population = new_population
            
            # Sort final results
            best_results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Genetic optimization completed. Found {len(best_results)} results")
            return best_results[:20]  # Return top 20
            
        except Exception as e:
            logger.error(f"Error in genetic optimization: {e}")
            return []
    
    def _initialize_population(
        self,
        parameter_ranges: Dict[str, List[Any]],
        population_size: int
    ) -> List[Dict[str, Any]]:
        """Initialize genetic algorithm population."""
        population = []
        
        for _ in range(population_size):
            individual = {}
            for param, values in parameter_ranges.items():
                individual[param] = np.random.choice(values)
            population.append(individual)
        
        return population
    
    def _selection_crossover(
        self,
        results: List[OptimizationResult],
        population_size: int
    ) -> List[Dict[str, Any]]:
        """Selection and crossover for genetic algorithm."""
        if len(results) < 2:
            return [r.parameters for r in results]
        
        new_population = []
        
        # Elitism: keep best individuals
        elite_size = max(1, population_size // 10)
        new_population.extend([r.parameters for r in results[:elite_size]])
        
        # Tournament selection and crossover
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = self._tournament_selection(results)
            parent2 = self._tournament_selection(results)
            
            # Crossover
            child = self._crossover(parent1, parent2)
            new_population.append(child)
        
        return new_population
    
    def _tournament_selection(self, results: List[OptimizationResult]) -> Dict[str, Any]:
        """Tournament selection for genetic algorithm."""
        tournament_size = 3
        tournament = np.random.choice(results, tournament_size, replace=False)
        return max(tournament, key=lambda x: x.score).parameters
    
    def _crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crossover operation for genetic algorithm."""
        child = {}
        for param in parent1.keys():
            if np.random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
    
    def _mutation(
        self,
        population: List[Dict[str, Any]],
        parameter_ranges: Dict[str, List[Any]],
        mutation_rate: float
    ) -> List[Dict[str, Any]]:
        """Mutation operation for genetic algorithm."""
        for individual in population:
            for param, values in parameter_ranges.items():
                if np.random.random() < mutation_rate:
                    individual[param] = np.random.choice(values)
        return population
    
    def get_optimization_summary(self, results: List[OptimizationResult]) -> Dict[str, Any]:
        """Get summary of optimization results."""
        if not results:
            return {}
        
        try:
            # Calculate statistics
            scores = [r.score for r in results]
            returns = [r.total_return for r in results]
            sharpes = [r.sharpe_ratio for r in results]
            drawdowns = [r.max_drawdown for r in results]
            
            summary = {
                'total_results': len(results),
                'best_score': max(scores),
                'avg_score': np.mean(scores),
                'best_return': max(returns),
                'avg_return': np.mean(returns),
                'best_sharpe': max(sharpes),
                'avg_sharpe': np.mean(sharpes),
                'min_drawdown': min(drawdowns),
                'avg_drawdown': np.mean(drawdowns),
                'top_parameters': results[0].parameters
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating optimization summary: {e}")
            return {}
    
    def print_optimization_results(self, results: List[OptimizationResult], top_n: int = 10):
        """Print optimization results."""
        if not results:
            print("No optimization results available")
            return
        
        print("\n" + "="*80)
        print("OPTIMIZATION RESULTS")
        print("="*80)
        
        for i, result in enumerate(results[:top_n]):
            print(f"\nRank {i+1}:")
            print(f"  Score: {result.score:.4f}")
            print(f"  Total Return: {result.total_return:.2f} ({result.total_return/100000:.2%})")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {result.max_drawdown:.2%}")
            print(f"  Win Rate: {result.win_rate:.2%}")
            print(f"  Profit Factor: {result.profit_factor:.2f}")
            print(f"  Parameters: {result.parameters}")
        
        print("\n" + "="*80)


# Global optimizer instance
optimizer = ParameterOptimizer()


async def get_optimizer() -> ParameterOptimizer:
    """Get the global optimizer instance."""
    return optimizer


if __name__ == "__main__":
    # Test the optimizer
    async def test():
        opt = ParameterOptimizer()
        await opt.initialize()
        
        # Define parameter ranges
        parameter_ranges = {
            'z_score_threshold': [1.5, 2.0, 2.5, 3.0],
            'lookback_window': [10, 15, 20, 25],
            'position_size_pct': [0.01, 0.02, 0.03],
            'stop_loss_pct': [0.03, 0.05, 0.07]
        }
        
        # Run grid search
        results = await opt.grid_search(
            symbols=["AAPL"],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 30),
            parameter_ranges=parameter_ranges
        )
        
        opt.print_optimization_results(results)
    
    asyncio.run(test()) 