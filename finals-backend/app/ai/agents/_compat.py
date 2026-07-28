"""
Compatibility shim: langchain_core's legacy get_debug()/get_verbose() fall
back to reading `langchain.debug` / `langchain.verbose` for backwards
compatibility. If a newer, unrelated `langchain>=1.0` happens to be present
on the machine (e.g. via a shared/system site-packages), it no longer exposes
those attributes and langgraph's ainvoke() blows up on an AttributeError.
We don't use any langchain feature here (our agents are pure Python), so we
simply tell langchain_core there's nothing to fall back to.
"""
from __future__ import annotations

import langchain_core.globals as _lc_globals

_lc_globals._HAS_LANGCHAIN = False
