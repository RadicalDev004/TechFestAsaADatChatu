# smart_librarian/router.py
import importlib.util
import os
import sys
import inspect
from typing import List, Tuple, Union, Optional, Any

class Router:
    def __init__(self):
        self.default_controller = "home"
        self.default_action = "index"

    async def route(self, path: str, request: Optional[Any] = None) -> Union[str, Tuple[str, int]]:
        """
        Routes paths like:
          /<controller>/<action>/<param1>/<param2>/...
          /<controller>/api/<action>/<param1>/<param2>/...
        Falls back to /home/index when pieces are missing.
        Returns either:
          - HTML string
          - (HTML string, status_code)
        """
        parts: List[str] = [p for p in path.strip("/").split("/") if p]

        controller_name = parts[0] if parts else self.default_controller

        # Map /<controller>/api/<action>[/<params...>] --> <action>(*params)
        if len(parts) >= 2 and parts[1] == "api":
            if len(parts) < 3:
                return (f"Error: API action missing for '{controller_name}'", 404)
            action_name = parts[2]       # e.g. "send", "messages"
            params = parts[3:]           # optional params (e.g. conv_id)
        else:
            action_name = parts[1] if len(parts) > 1 else self.default_action
            params = parts[2:] if len(parts) > 2 else []

        controller_file = f"Backend/controllers/{controller_name}_controller.py"
        class_name = f"{controller_name.capitalize()}Controller"

        if not os.path.isfile(controller_file):
            return ("Error: Page not found <br> <a href='/home/index'>Go to Home</a>", 404)

        spec = importlib.util.spec_from_file_location(class_name, controller_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[class_name] = module
        assert spec and spec.loader, "Failed to load controller module spec"
        spec.loader.exec_module(module)

        controller_class = getattr(module, class_name, None)
        if controller_class is None:
            return (f"Error: Controller '{class_name}' not found", 404)

        controller_instance = controller_class()
        if not hasattr(controller_instance, action_name):
            return (f"Error: Action '{action_name}' not found in {class_name}", 404)

        action = getattr(controller_instance, action_name)

        # Best-effort: pass the Request object if the method accepts it
        # We only pass arguments the action can actually take.
        sig = inspect.signature(action)
        call_args = []
        kw_args = {}
        params_iter = iter(params)

        # Map positional path params first
        for p in sig.parameters.values():
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
                if p.name == "request" and request is not None:
                    call_args.append(request)
                elif params:
                    # consume next str param from path if available
                    try:
                        call_args.append(next(params_iter))
                    except StopIteration:
                        # no more path params; rely on default if any
                        if p.default is inspect._empty:
                            return (f"Error: Missing parameter '{p.name}' for {class_name}.{action_name}", 400)
                else:
                    # rely on default or error
                    if p.default is inspect._empty and p.name != "request":
                        return (f"Error: Missing parameter '{p.name}' for {class_name}.{action_name}", 400)
            elif p.kind == p.KEYWORD_ONLY and p.name == "request" and request is not None:
                kw_args["request"] = request
            # We ignore VAR_POSITIONAL/VAR_KEYWORD; most controllers won't need them

        # Support both sync and async controller actions
        if inspect.iscoroutinefunction(action):
            result = await action(*call_args, **kw_args)
        else:
            result = action(*call_args, **kw_args)

        # Normalize: allow string or (string, status)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], str) and isinstance(result[1], int):
            return result
        elif isinstance(result, str):
            return result
        else:
            # If controller returned something else (e.g., dict/Response), let FastAPI handle it upstream.
            # We'll bubble it up by encoding as string (simple fallback).
            return str(result)
