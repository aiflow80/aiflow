import importlib.util
import os
import sys
import asyncio
from aiflow import logger
from aiflow.events import event_base

def run_module(file_path):
    try:
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Cannot run module: Invalid file path: {file_path}")
            return False
        else:
            logger.info(f"Running module from full file path: {os.path.abspath(file_path)}")
            # Set the caller file path if event_base exists and caller file is unknown
            if not event_base.caller_file:
                event_base.set_caller_file(os.path.abspath(file_path))
        
        # Get the module name from the file path
        module_name = os.path.basename(file_path)
        if (module_name.endswith('.py')):
            module_name = module_name[:-3]
        
        # Load and execute the module
        logger.info(f"Running module from file: {file_path}")
        
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
            logger.info(f"Successfully executed module: {module_name} as __main__")
            return True
        except RuntimeError as e:
            pass
        finally:
            # Restore original __main__ and sys.argv
            if original_main:
                sys.modules['__main__'] = original_main
            sys.argv = original_argv
            
    except Exception as e:
        logger.error(f"Error running module {file_path}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        # Keep the original sys.argv for the script to use
        success = run_module(script_path)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python -m aiflow.events.run <script_path> [args...]")
        sys.exit(1)
