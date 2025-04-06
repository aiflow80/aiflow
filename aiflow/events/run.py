import importlib.util
import os
import sys
import subprocess
import runpy
from aiflow import logger
from aiflow.events import event_base

def run_module_subprocess(file_path):
    """Run a Python module as a subprocess."""
    try:
        result = subprocess.run([sys.executable, file_path] + sys.argv[2:], 
                               check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess execution failed: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running subprocess: {str(e)}")
        return False

def run_module_exec(file_path):
    """Run a Python module using exec()."""
    try:
        with open(file_path, 'r') as file:
            code = compile(file.read(), file_path, 'exec')
            # Create a new global namespace
            globals_dict = {
                '__file__': file_path,
                '__name__': '__main__'
            }
            exec(code, globals_dict)
        return True
    except Exception as e:
        logger.error(f"Error executing module with exec(): {str(e)}")
        return False

def run_module_runpy(file_path):
    """Run a Python module using runpy."""
    try:
        runpy.run_path(file_path, run_name='__main__')
        return True
    except Exception as e:
        logger.error(f"Error running module with runpy: {str(e)}")
        return False

def run_module_importlib(file_path):
    """Run a Python module using importlib (original method)."""
    try:
        # Get the module name from the file path
        module_name = os.path.basename(file_path)
        if (module_name.endswith('.py')):
            module_name = module_name[:-3]
        
        # Save original __main__ and sys.argv
        original_main = sys.modules.get('__main__')
        original_argv = sys.argv.copy()
        
        try:
            # Make the target module appear as __main__ to itself
            spec = importlib.util.spec_from_file_location('__main__', file_path)
            if spec is None:
                logger.error(f"Failed to create spec for module: {file_path}")
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules['__main__'] = module
            sys.argv[0] = file_path  # Set argv[0] to the script path
            
            # Execute the module as if run directly
            spec.loader.exec_module(module)
            return True
        except RuntimeError as e:
            logger.error(f"Runtime error: {str(e)}")
            return False
        finally:
            # Restore original __main__ and sys.argv
            if original_main:
                sys.modules['__main__'] = original_main
            sys.argv = original_argv
            
    except Exception as e:
        logger.error(f"Error running module with importlib {file_path}: {str(e)}")
        return False

def run_module(file_path, method='auto', **kwargs):
    try:
        # Handle deprecated 'threaded' parameter for backward compatibility
        if 'threaded' in kwargs:
            logger.warning("The 'threaded' parameter is deprecated. Use 'method' instead.")
            if kwargs['threaded'] and method == 'auto':
                # If threaded was True, use subprocess as the closest equivalent
                method = 'subprocess'
            
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Cannot run module: Invalid file path: {file_path}")
            return False
        else:
            # Set the caller file path if event_base exists and caller file is unknown
            if not event_base.caller_file:
                event_base.set_caller_file(os.path.abspath(file_path))
        
        # Run using the specified or default method
        if method == 'subprocess':
            return run_module_subprocess(file_path)
        elif method == 'exec':
            return run_module_exec(file_path)
        elif method == 'runpy':
            return run_module_runpy(file_path)
        elif method == 'importlib':
            return run_module_importlib(file_path)
        elif method == 'auto':
            # Try different methods in order
            methods = [
                ('runpy', run_module_runpy),
                ('subprocess', run_module_subprocess),
                ('importlib', run_module_importlib),
                ('exec', run_module_exec)
            ]
            
            for name, func in methods:
                logger.debug(f"Attempting to run module using {name}")
                if func(file_path):
                    return True
            
            logger.error("All module execution methods failed")
            return False
        else:
            logger.error(f"Unknown execution method: {method}")
            return False
            
    except Exception as e:
        logger.error(f"Error running module {file_path}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        method = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        # Keep the original sys.argv for the script to use
        success = run_module(script_path, method)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python -m aiflow.events.run <script_path> [method] [args...]")
        sys.exit(1)
