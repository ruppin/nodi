"""Test suite runner for executing multiple scripts."""

import yaml
import time
import concurrent.futures
from typing import Dict, Any, List, Optional
from pathlib import Path

from .engine import ScriptEngine, ScriptExecutionError


class SuiteRunner:
    """Execute test suites defined in YAML files."""

    def __init__(self, script_engine: ScriptEngine):
        self.engine = script_engine

    def run_suite(self, suite_path: str) -> Dict[str, Any]:
        """
        Run a test suite from YAML file.

        Args:
            suite_path: Path to suite YAML file

        Returns:
            Suite execution results
        """
        start_time = time.time()

        # Load suite file
        path = Path(suite_path)
        if not path.exists():
            raise ScriptExecutionError(f"Suite file not found: {suite_path}")

        with open(path, 'r', encoding='utf-8') as f:
            suite_config = yaml.safe_load(f)

        suite_name = suite_config.get('name', 'Unnamed Suite')

        # Determine suite directory for resolving relative script paths
        suite_dir = path.parent

        results = {
            'suite': suite_name,
            'path': suite_path,
            'start_time': start_time,
            'steps': [],
            'total': 0,
            'passed': 0,
            'failed': 0,
            'duration': 0
        }

        # Handle different suite formats
        if 'scripts' in suite_config:
            # Simple sequential list
            scripts = suite_config['scripts']
            stop_on_error = suite_config.get('options', {}).get('stop_on_error', True)

            results['steps'] = self._run_sequential_scripts(
                scripts, suite_dir, stop_on_error
            )

        elif 'parallel_groups' in suite_config:
            # Parallel groups
            groups = suite_config['parallel_groups']
            results['steps'] = self._run_parallel_groups(groups, suite_dir)

        elif 'steps' in suite_config:
            # Mixed sequential/parallel steps
            steps = suite_config['steps']
            results['steps'] = self._run_mixed_steps(steps, suite_dir)

        # Calculate totals
        for step in results['steps']:
            results['total'] += 1
            if step['status'] == 'PASS':
                results['passed'] += 1
            else:
                results['failed'] += 1

        results['duration'] = time.time() - start_time

        return results

    def _run_sequential_scripts(self, scripts: List[str], suite_dir: Path,
                                stop_on_error: bool = True) -> List[Dict[str, Any]]:
        """Run scripts sequentially."""
        results = []

        for i, script in enumerate(scripts):
            script_path = suite_dir / script

            try:
                result = self.engine.run_script(str(script_path))
                results.append({
                    'step': i + 1,
                    'script': script,
                    'status': result['status'],
                    'duration': result['duration'],
                    'output': result.get('output', [])
                })

                if stop_on_error and result['status'] == 'FAIL':
                    break

            except Exception as e:
                results.append({
                    'step': i + 1,
                    'script': script,
                    'status': 'FAIL',
                    'duration': 0,
                    'error': str(e)
                })
                if stop_on_error:
                    break

        return results

    def _run_parallel_groups(self, groups: List[Dict[str, Any]],
                            suite_dir: Path) -> List[Dict[str, Any]]:
        """Run parallel groups."""
        all_results = []

        for group in groups:
            group_name = group.get('name', 'Unnamed Group')
            parallel = group.get('parallel', False)
            scripts = group.get('scripts', [])

            if parallel:
                # Run scripts in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {}
                    for script in scripts:
                        script_path = suite_dir / script
                        future = executor.submit(self.engine.run_script, str(script_path))
                        futures[future] = script

                    for future in concurrent.futures.as_completed(futures):
                        script = futures[future]
                        try:
                            result = future.result()
                            all_results.append({
                                'group': group_name,
                                'script': script,
                                'status': result['status'],
                                'duration': result['duration'],
                                'output': result.get('output', [])
                            })
                        except Exception as e:
                            all_results.append({
                                'group': group_name,
                                'script': script,
                                'status': 'FAIL',
                                'duration': 0,
                                'error': str(e)
                            })
            else:
                # Run scripts sequentially
                results = self._run_sequential_scripts(scripts, suite_dir, stop_on_error=True)
                for result in results:
                    result['group'] = group_name
                    all_results.append(result)

        return all_results

    def _run_mixed_steps(self, steps: List[Dict[str, Any]],
                        suite_dir: Path) -> List[Dict[str, Any]]:
        """Run mixed sequential/parallel steps."""
        all_results = []

        for step_config in steps:
            step_name = step_config.get('name', 'Unnamed Step')

            if 'script' in step_config:
                # Single script
                script = step_config['script']
                script_path = suite_dir / script

                try:
                    result = self.engine.run_script(str(script_path))
                    all_results.append({
                        'step': step_name,
                        'script': script,
                        'status': result['status'],
                        'duration': result['duration'],
                        'output': result.get('output', [])
                    })
                except Exception as e:
                    all_results.append({
                        'step': step_name,
                        'script': script,
                        'status': 'FAIL',
                        'duration': 0,
                        'error': str(e)
                    })

            elif 'scripts' in step_config:
                # Multiple scripts
                scripts = step_config['scripts']
                parallel = step_config.get('parallel', False)

                if parallel:
                    # Run in parallel
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {}
                        for script in scripts:
                            script_path = suite_dir / script
                            future = executor.submit(self.engine.run_script, str(script_path))
                            futures[future] = script

                        for future in concurrent.futures.as_completed(futures):
                            script = futures[future]
                            try:
                                result = future.result()
                                all_results.append({
                                    'step': step_name,
                                    'script': script,
                                    'status': result['status'],
                                    'duration': result['duration'],
                                    'output': result.get('output', [])
                                })
                            except Exception as e:
                                all_results.append({
                                    'step': step_name,
                                    'script': script,
                                    'status': 'FAIL',
                                    'duration': 0,
                                    'error': str(e)
                                })
                else:
                    # Run sequentially
                    results = self._run_sequential_scripts(scripts, suite_dir, stop_on_error=False)
                    for result in results:
                        result['step'] = step_name
                        all_results.append(result)

        return all_results

    def run_scripts_parallel(self, script_paths: List[str]) -> Dict[str, Any]:
        """
        Run multiple scripts in parallel.

        Args:
            script_paths: List of script file paths

        Returns:
            Execution results
        """
        start_time = time.time()
        results = {
            'total': len(script_paths),
            'passed': 0,
            'failed': 0,
            'scripts': [],
            'duration': 0
        }

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {}
            for script_path in script_paths:
                future = executor.submit(self.engine.run_script, script_path)
                futures[future] = script_path

            for future in concurrent.futures.as_completed(futures):
                script_path = futures[future]
                try:
                    result = future.result()
                    results['scripts'].append({
                        'script': script_path,
                        'status': result['status'],
                        'duration': result['duration'],
                        'output': result.get('output', [])
                    })

                    if result['status'] == 'PASS':
                        results['passed'] += 1
                    else:
                        results['failed'] += 1

                except Exception as e:
                    results['scripts'].append({
                        'script': script_path,
                        'status': 'FAIL',
                        'duration': 0,
                        'error': str(e)
                    })
                    results['failed'] += 1

        results['duration'] = time.time() - start_time
        return results

    def run_scripts_sequential(self, script_paths: List[str],
                              stop_on_error: bool = False) -> Dict[str, Any]:
        """
        Run multiple scripts sequentially.

        Args:
            script_paths: List of script file paths
            stop_on_error: Stop execution on first error

        Returns:
            Execution results
        """
        start_time = time.time()
        results = {
            'total': len(script_paths),
            'passed': 0,
            'failed': 0,
            'scripts': [],
            'duration': 0
        }

        for i, script_path in enumerate(script_paths):
            try:
                result = self.engine.run_script(script_path)
                results['scripts'].append({
                    'step': i + 1,
                    'script': script_path,
                    'status': result['status'],
                    'duration': result['duration'],
                    'output': result.get('output', [])
                })

                if result['status'] == 'PASS':
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    if stop_on_error:
                        break

            except Exception as e:
                results['scripts'].append({
                    'step': i + 1,
                    'script': script_path,
                    'status': 'FAIL',
                    'duration': 0,
                    'error': str(e)
                })
                results['failed'] += 1
                if stop_on_error:
                    break

        results['duration'] = time.time() - start_time
        return results
