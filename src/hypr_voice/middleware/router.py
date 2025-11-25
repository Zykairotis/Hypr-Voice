"""
Request Router Middleware

Routes incoming requests to appropriate handlers.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RouteMethod(str, Enum):
    """HTTP-like methods for routing."""
    QUERY = "QUERY"
    COMMAND = "COMMAND"
    EVENT = "EVENT"
    STREAM = "STREAM"


@dataclass
class Route:
    """Definition of a route."""
    pattern: str
    method: RouteMethod
    handler: Callable
    description: str = ""
    middleware: list[Callable] = field(default_factory=list)
    
    def matches(self, path: str, method: RouteMethod) -> bool:
        """Check if this route matches the given path and method."""
        if self.method != method:
            return False
        
        # Support simple patterns and regex
        if "{" in self.pattern:
            # Convert {param} to regex groups
            regex_pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", self.pattern)
            return bool(re.match(f"^{regex_pattern}$", path))
        else:
            return self.pattern == path
    
    def extract_params(self, path: str) -> dict:
        """Extract parameters from path."""
        if "{" not in self.pattern:
            return {}
        
        regex_pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", self.pattern)
        match = re.match(f"^{regex_pattern}$", path)
        
        if match:
            return match.groupdict()
        return {}


@dataclass
class RequestContext:
    """Context for a request."""
    path: str
    method: RouteMethod
    data: dict
    params: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class RequestRouter:
    """
    Routes requests to appropriate handlers.
    
    Supports:
    - Path-based routing with parameters
    - Method-based filtering (QUERY, COMMAND, EVENT, STREAM)
    - Middleware chains
    - Fallback handlers
    """
    
    def __init__(self):
        self._routes: list[Route] = []
        self._global_middleware: list[Callable] = []
        self._fallback_handler: Optional[Callable] = None
    
    def add_route(
        self,
        pattern: str,
        method: RouteMethod,
        handler: Callable,
        description: str = "",
        middleware: list[Callable] = None,
    ):
        """
        Add a route.
        
        Args:
            pattern: URL-like pattern (e.g., "/agents/{id}/status")
            method: Request method
            handler: Handler function
            description: Route description
            middleware: Route-specific middleware
        """
        route = Route(
            pattern=pattern,
            method=method,
            handler=handler,
            description=description,
            middleware=middleware or [],
        )
        self._routes.append(route)
        logger.debug(f"Added route: {method.value} {pattern}")
    
    def use(self, middleware: Callable):
        """Add global middleware."""
        self._global_middleware.append(middleware)
    
    def set_fallback(self, handler: Callable):
        """Set fallback handler for unmatched routes."""
        self._fallback_handler = handler
    
    async def route(self, path: str, method: RouteMethod, data: dict = None) -> Any:
        """
        Route a request to the appropriate handler.
        
        Args:
            path: Request path
            method: Request method
            data: Request data
            
        Returns:
            Handler result
        """
        data = data or {}
        
        # Find matching route
        for route in self._routes:
            if route.matches(path, method):
                params = route.extract_params(path)
                
                context = RequestContext(
                    path=path,
                    method=method,
                    data=data,
                    params=params,
                )
                
                # Execute middleware chain
                try:
                    # Global middleware
                    for mw in self._global_middleware:
                        result = await self._execute_middleware(mw, context)
                        if result is not None:
                            return result
                    
                    # Route middleware
                    for mw in route.middleware:
                        result = await self._execute_middleware(mw, context)
                        if result is not None:
                            return result
                    
                    # Execute handler
                    return await self._execute_handler(route.handler, context)
                    
                except Exception as e:
                    logger.error(f"Route handler error: {e}")
                    return {"error": str(e)}
        
        # No matching route
        if self._fallback_handler:
            context = RequestContext(path=path, method=method, data=data)
            return await self._execute_handler(self._fallback_handler, context)
        
        return {"error": f"No route found for {method.value} {path}"}
    
    async def _execute_middleware(self, middleware: Callable, context: RequestContext) -> Any:
        """Execute a middleware function."""
        import asyncio
        
        if asyncio.iscoroutinefunction(middleware):
            return await middleware(context)
        else:
            return middleware(context)
    
    async def _execute_handler(self, handler: Callable, context: RequestContext) -> Any:
        """Execute a handler function."""
        import asyncio
        
        if asyncio.iscoroutinefunction(handler):
            return await handler(context)
        else:
            return handler(context)
    
    def list_routes(self) -> list[dict]:
        """List all registered routes."""
        return [
            {
                "pattern": route.pattern,
                "method": route.method.value,
                "description": route.description,
            }
            for route in self._routes
        ]


# Convenience decorators

def query(pattern: str, description: str = ""):
    """Decorator for QUERY routes."""
    def decorator(func: Callable):
        func._route_pattern = pattern
        func._route_method = RouteMethod.QUERY
        func._route_description = description
        return func
    return decorator


def command(pattern: str, description: str = ""):
    """Decorator for COMMAND routes."""
    def decorator(func: Callable):
        func._route_pattern = pattern
        func._route_method = RouteMethod.COMMAND
        func._route_description = description
        return func
    return decorator


def event(pattern: str, description: str = ""):
    """Decorator for EVENT routes."""
    def decorator(func: Callable):
        func._route_pattern = pattern
        func._route_method = RouteMethod.EVENT
        func._route_description = description
        return func
    return decorator


def register_routes(router: RequestRouter, obj: Any):
    """Register all decorated routes from an object."""
    for name in dir(obj):
        attr = getattr(obj, name)
        if callable(attr) and hasattr(attr, "_route_pattern"):
            router.add_route(
                pattern=attr._route_pattern,
                method=attr._route_method,
                handler=attr,
                description=getattr(attr, "_route_description", ""),
            )
