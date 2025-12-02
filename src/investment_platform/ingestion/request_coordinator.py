"""Request coordinator for intelligent batching of API requests."""

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class Request:
    """Represents a single data collection request."""

    request_id: str
    collector_type: str
    symbol: str
    asset_type: str
    start_date: datetime
    end_date: datetime
    collector_kwargs: Dict[str, Any]
    callback: Callable[[Any], None]
    error_callback: Optional[Callable[[Exception], None]] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class BatchRequest:
    """Represents a batch of requests that can be combined."""

    collector_type: str
    requests: List[Request]
    start_date: datetime
    end_date: datetime
    collector_kwargs: Dict[str, Any]


class RequestCoordinator:
    """
    Coordinates API requests to enable intelligent batching.

    Groups requests by collector type and time window, then executes
    batch requests when collectors support them.
    """

    # Registry of collectors that support batch requests
    _batch_supported_collectors = {
        "StockCollector": True,
        "CommodityCollector": True,  # yfinance supports batch
        # Add more as needed
    }

    def __init__(
        self,
        enabled: Optional[bool] = None,
        window_seconds: Optional[float] = None,
        batch_executor_workers: int = 5,
    ):
        """
        Initialize the request coordinator.

        Args:
            enabled: Whether coordinator is enabled (default: from env var or True)
            window_seconds: Time window for grouping requests (default: from env var or 1.0)
            batch_executor_workers: Number of workers for batch execution
        """
        if enabled is None:
            enabled = os.getenv("ENABLE_REQUEST_COORDINATOR", "true").lower() == "true"
        if window_seconds is None:
            window_seconds = float(os.getenv("REQUEST_COORDINATOR_WINDOW_SECONDS", "1.0"))

        self.enabled = enabled
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._pending_requests: Dict[str, List[Request]] = defaultdict(list)
        self._batch_executor = ThreadPoolExecutor(max_workers=batch_executor_workers)
        self._processing = False
        self._stop_event = threading.Event()

        if self.enabled:
            logger.info(
                f"Request coordinator enabled (window: {window_seconds}s, "
                f"batch workers: {batch_executor_workers})"
            )
        else:
            logger.info("Request coordinator disabled")

    def submit_request(
        self,
        collector_type: str,
        symbol: str,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
        collector_kwargs: Dict[str, Any],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[Exception], None]] = None,
        wait_for_result: bool = False,
        timeout: Optional[float] = None,
    ) -> Union[str, Any]:
        """
        Submit a request for data collection.

        Args:
            collector_type: Type of collector (e.g., 'StockCollector')
            symbol: Asset symbol
            asset_type: Type of asset
            start_date: Start date for collection
            end_date: End date for collection
            collector_kwargs: Additional kwargs for collector
            callback: Callback function to receive result
            error_callback: Optional callback for errors

        Returns:
            Request ID
        """
        # If waiting for result, use future for synchronous execution
        if wait_for_result:
            future = Future()
            result_container = {"data": None, "error": None}

            def result_callback(data):
                result_container["data"] = data
                if not future.done():
                    future.set_result(data)

            def error_callback_wrapper(error):
                result_container["error"] = error
                if not future.done():
                    future.set_exception(error)

            # Submit request without waiting
            request_id = self._submit_request_internal(
                collector_type,
                symbol,
                asset_type,
                start_date,
                end_date,
                collector_kwargs,
                result_callback,
                error_callback_wrapper,
            )

            # Wait for result
            try:
                if timeout:
                    result = future.result(timeout=timeout)
                else:
                    result = future.result()
                return result
            except Exception as e:
                if result_container["error"]:
                    raise result_container["error"]
                raise

        if not self.enabled:
            # If coordinator is disabled, execute immediately
            # This maintains backward compatibility
            return self._execute_immediate(
                collector_type,
                symbol,
                asset_type,
                start_date,
                end_date,
                collector_kwargs,
                callback,
                error_callback,
                wait_for_result,
                timeout,
            )

        return self._submit_request_internal(
            collector_type,
            symbol,
            asset_type,
            start_date,
            end_date,
            collector_kwargs,
            callback,
            error_callback,
        )

    def _submit_request_internal(
        self,
        collector_type: str,
        symbol: str,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
        collector_kwargs: Dict[str, Any],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[Exception], None]] = None,
    ) -> str:
        """Internal method to submit request without waiting."""
        request_id = f"{collector_type}_{symbol}_{int(time.time() * 1000000)}"
        request = Request(
            request_id=request_id,
            collector_type=collector_type,
            symbol=symbol,
            asset_type=asset_type,
            start_date=start_date,
            end_date=end_date,
            collector_kwargs=collector_kwargs,
            callback=callback,
            error_callback=error_callback,
        )

        with self._lock:
            self._pending_requests[collector_type].append(request)

        # Trigger processing if not already running
        self._process_requests_async()

        return request_id

    def _process_requests_async(self):
        """Process pending requests asynchronously."""
        if self._processing:
            return

        self._processing = True
        self._batch_executor.submit(self._process_requests)

    def _process_requests(self):
        """Process pending requests, grouping and batching when possible."""
        try:
            # Wait for the time window to collect requests
            time.sleep(self.window_seconds)

            with self._lock:
                if not self._pending_requests:
                    self._processing = False
                    return

                # Group requests by collector type
                requests_to_process = dict(self._pending_requests)
                self._pending_requests.clear()

            # Process each collector type
            for collector_type, requests in requests_to_process.items():
                if not requests:
                    continue

                # Check if this collector supports batch requests
                supports_batch = self._batch_supported_collectors.get(collector_type, False)

                if supports_batch and len(requests) > 1:
                    # Try to batch requests
                    self._process_batch(collector_type, requests)
                else:
                    # Process individually
                    for request in requests:
                        self._execute_request(request)

        except Exception as e:
            logger.error(f"Error processing requests: {e}", exc_info=True)
        finally:
            self._processing = False

    def _process_batch(self, collector_type: str, requests: List[Request]):
        """
        Process a batch of requests together.

        Args:
            collector_type: Type of collector
            requests: List of requests to batch
        """
        # Group requests by time window and collector kwargs
        # For now, we'll batch requests with same date ranges and kwargs
        batch_groups = self._group_requests_for_batching(requests)

        for batch_group in batch_groups:
            if len(batch_group) > 1:
                # Execute as batch
                self._execute_batch(collector_type, batch_group)
            else:
                # Execute individually
                self._execute_request(batch_group[0])

    def _group_requests_for_batching(self, requests: List[Request]) -> List[List[Request]]:
        """
        Group requests that can be batched together.

        Groups requests with:
        - Same collector type (already grouped)
        - Same date range (or overlapping)
        - Same collector_kwargs

        Args:
            requests: List of requests to group

        Returns:
            List of request groups
        """
        groups: Dict[Tuple[datetime, datetime, str], List[Request]] = defaultdict(list)

        for request in requests:
            # Create key from date range and kwargs
            kwargs_key = str(sorted(request.collector_kwargs.items()))
            key = (request.start_date, request.end_date, kwargs_key)
            groups[key].append(request)

        return list(groups.values())

    def _execute_batch(self, collector_type: str, requests: List[Request]):
        """
        Execute a batch of requests.

        Args:
            collector_type: Type of collector
            requests: List of requests to execute as batch
        """
        try:
            # Get symbols from all requests
            symbols = [req.symbol for req in requests]
            first_request = requests[0]

            logger.info(
                f"Executing batch request for {collector_type}: {len(symbols)} symbols "
                f"({', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''})"
            )

            # Import collector dynamically
            collector = self._get_collector_instance(collector_type)

            # Check if collector has batch collection method
            if hasattr(collector, "collect_historical_data_batch"):
                # Use batch method
                results = collector.collect_historical_data_batch(
                    symbols=symbols,
                    start_date=first_request.start_date,
                    end_date=first_request.end_date,
                    **first_request.collector_kwargs,
                )

                # Distribute results to callbacks
                for i, request in enumerate(requests):
                    try:
                        if i < len(results):
                            request.callback(results[i])
                        else:
                            # No result for this symbol, call error callback
                            if request.error_callback:
                                request.error_callback(
                                    Exception(f"No data returned for {request.symbol}")
                                )
                    except Exception as e:
                        logger.error(f"Error in callback for {request.symbol}: {e}")
                        if request.error_callback:
                            request.error_callback(e)
            else:
                # Collector doesn't support batch, execute individually
                logger.warning(
                    f"{collector_type} doesn't support batch collection, " "executing individually"
                )
                for request in requests:
                    self._execute_request(request)

        except Exception as e:
            logger.error(f"Error executing batch request: {e}", exc_info=True)
            # On error, execute individually as fallback
            for request in requests:
                try:
                    if request.error_callback:
                        request.error_callback(e)
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {callback_error}")

    def _execute_request(self, request: Request):
        """
        Execute a single request.

        Args:
            request: Request to execute
        """
        try:
            collector = self._get_collector_instance(request.collector_type)

            result = collector.collect_historical_data(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                **request.collector_kwargs,
            )

            request.callback(result)

        except Exception as e:
            logger.error(f"Error executing request {request.request_id}: {e}", exc_info=True)
            if request.error_callback:
                request.error_callback(e)

    def _execute_immediate(
        self,
        collector_type: str,
        symbol: str,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
        collector_kwargs: Dict[str, Any],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[Exception], None]] = None,
        wait_for_result: bool = False,
        timeout: Optional[float] = None,
    ) -> Union[str, Any]:
        """Execute request immediately (when coordinator is disabled)."""
        if wait_for_result:
            # Execute synchronously
            collector = self._get_collector_instance(collector_type)
            result = collector.collect_historical_data(
                symbol=symbol, start_date=start_date, end_date=end_date, **collector_kwargs
            )
            return result

        request_id = f"{collector_type}_{symbol}_{int(time.time() * 1000000)}"

        def execute():
            try:
                collector = self._get_collector_instance(collector_type)
                result = collector.collect_historical_data(
                    symbol=symbol, start_date=start_date, end_date=end_date, **collector_kwargs
                )
                callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    logger.error(f"Error in immediate execution: {e}", exc_info=True)

        self._batch_executor.submit(execute)
        return request_id

    def _get_collector_instance(self, collector_type: str):
        """
        Get an instance of the collector.

        Args:
            collector_type: Type of collector (e.g., 'StockCollector')

        Returns:
            Collector instance
        """
        from investment_platform.collectors import (
            StockCollector,
            CryptoCollector,
            ForexCollector,
            BondCollector,
            CommodityCollector,
            EconomicCollector,
        )

        collector_map = {
            "StockCollector": StockCollector,
            "CryptoCollector": CryptoCollector,
            "ForexCollector": ForexCollector,
            "BondCollector": BondCollector,
            "CommodityCollector": CommodityCollector,
            "EconomicCollector": EconomicCollector,
        }

        collector_class = collector_map.get(collector_type)
        if not collector_class:
            raise ValueError(f"Unknown collector type: {collector_type}")

        return collector_class(output_format="dataframe")

    def shutdown(self):
        """Shutdown the coordinator and wait for pending requests."""
        self._stop_event.set()
        self._batch_executor.shutdown(wait=True)
        logger.info("Request coordinator shut down")


# Global coordinator instance
_coordinator: Optional[RequestCoordinator] = None
_coordinator_lock = threading.Lock()


def get_coordinator() -> RequestCoordinator:
    """Get the global request coordinator instance."""
    global _coordinator

    with _coordinator_lock:
        if _coordinator is None:
            _coordinator = RequestCoordinator()
        return _coordinator
