"""
Decorators to eliminate common service patterns.
"""

import functools
import inspect


def log_operation(operation_name: str = None):
    """Decorator for consistent operation logging."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__

            try:
                result = await func(self, *args, **kwargs)
                self._logger.debug(f"{op_name} completed successfully")
                return result
            except Exception as e:
                self._logger.error(f"{op_name} failed: {str(e)}")
                raise

        return wrapper
    return decorator


def validate_issue_key(func):
    """Decorator to validate issue_key parameter."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Get function signature to find issue_key parameter
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        # Find and validate issue_key
        if 'issue_key' in bound_args.arguments:
            issue_key = bound_args.arguments['issue_key']
            self._validate_issue_key(issue_key)

        return await func(self, *args, **kwargs)
    return wrapper


def validate_project_key(func):
    """Decorator to validate project_key parameter."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Get function signature to find project_key parameter
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        # Find and validate project_key
        if 'project_key' in bound_args.arguments:
            project_key = bound_args.arguments['project_key']
            self._validate_project_key(project_key)

        return await func(self, *args, **kwargs)
    return wrapper


def resolve_instance(func):
    """Decorator to resolve instance_name parameter."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Get function signature to find instance_name parameter
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        # Find and resolve instance_name
        if 'instance_name' in bound_args.arguments:
            instance_name = bound_args.arguments['instance_name']
            resolved_instance = self._resolve_instance_name(instance_name)

            # Update kwargs with resolved instance
            if 'instance_name' in kwargs:
                kwargs['instance_name'] = resolved_instance
            else:
                # Find the parameter position and update args
                param_names = list(sig.parameters.keys())
                if 'instance_name' in param_names:
                    param_index = param_names.index('instance_name') - 1  # -1 for self
                    if param_index < len(args):
                        args = list(args)
                        args[param_index] = resolved_instance
                        args = tuple(args)
                    else:
                        kwargs['instance_name'] = resolved_instance

        return await func(self, *args, **kwargs)
    return wrapper


def validate_and_resolve(func):
    """Combined decorator for common validation and resolution."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Apply resolve_instance logic
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        if 'instance_name' in bound_args.arguments:
            instance_name = bound_args.arguments['instance_name']
            resolved_instance = self._resolve_instance_name(instance_name)
            if 'instance_name' in kwargs:
                kwargs['instance_name'] = resolved_instance
            else:
                param_names = list(sig.parameters.keys())
                if 'instance_name' in param_names:
                    param_index = param_names.index('instance_name') - 1
                    if param_index < len(args):
                        args = list(args)
                        args[param_index] = resolved_instance
                        args = tuple(args)
                    else:
                        kwargs['instance_name'] = resolved_instance

        # Apply logging
        op_name = func.__name__
        try:
            result = await func(self, *args, **kwargs)
            self._logger.debug(f"{op_name} completed successfully")
            return result
        except Exception as e:
            self._logger.error(f"{op_name} failed: {str(e)}")
            raise

    return wrapper
