import runpy
file_globals=runpy.run_path("source/data.py")
globals().update(file_globals)
file_globals_2=runpy.run_path("source/pricing.py")
globals().update(file_globals_2)
file_globals_3=runpy.run_path("source/describe.py")
globals().update(file_globals_3)
file_globals_4=runpy.run_path("source/regression.py")
globals().update(file_globals_4)
file_globals_5=runpy.run_path("source/filter.py")
globals().update(file_globals_5)