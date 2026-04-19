import re

with open('users/badge_system.py', 'r') as f:
    content = f.read()

# Make sure we're caching across the strategy array, by storing the results on the `cache` dict argument passed to the checks.
# Wait, actually let me inspect what's happening. The cache dict is actually `strategy_cache = {}` inside `check_badges`
# which is passed to *all* strategies. So putting things in `cache` should persist across the entire `check_badges` loop.

content = re.sub(
    r"        if cache is not None:",
    r"""        if cache is not None:""",
    content
)
