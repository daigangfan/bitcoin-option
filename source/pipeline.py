import runpy

globals().update(runpy.run_path("source/data.py"))
globals().update(runpy.run_path("source/pricing.py"))
globals().update(runpy.run_path("source/describe.py"))
globals().update(runpy.run_path("source/new_regression.py"))
globals().update(runpy.run_path("source/filter.py"))
globals().update(runpy.run_path("source/strategy.py"))