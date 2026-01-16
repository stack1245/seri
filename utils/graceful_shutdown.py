"""안전한 종료 처리"""
from __future__ import annotations
import signal
import sys
from typing import Callable, List

__all__ = ["register_shutdown_callback", "setup_graceful_shutdown"]

_callbacks: List[Callable[[], None]] = []
_active = False


def register_shutdown_callback(cb: Callable[[], None]) -> None:
    """종료 시 실행할 콜백 등록
    
    Args:
        cb: 실행할 콜백 함수
    """
    _callbacks.append(cb)


def _run_callbacks() -> None:
    """모든 콜백 실행"""
    for cb in _callbacks:
        try:
            cb()
        except Exception:
            pass


def setup_graceful_shutdown() -> None:
    """SIGINT/SIGTERM 핸들러 설정"""
    global _active
    
    if _active:
        return
    
    _active = True

    def signal_handler(signum: int, frame: object) -> None:
        _run_callbacks()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
