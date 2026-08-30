# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""pytest 路径引导：prompts 独立叶仓自测入口。

prompts 是独立叶仓（可单独 clone/测试），顶层包为 `prompts`。本 conftest 将
仓库根加入 sys.path，使 `from prompts.tuner...` 类导入在 CI 与本地均可用；
伞仓组装场景下 ecosystem.prompts 前缀由伞仓根 pytest 运行（见 ecosystem/
聚合测试）处理。
"""

import sys
from pathlib import Path

_PROMPTS_ROOT = Path(__file__).resolve().parent

if str(_PROMPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROMPTS_ROOT))
