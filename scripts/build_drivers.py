#!/usr/bin/env python3
"""Build daily ERA5 and astronomical tide drivers from existing on-disk data."""
import json
from floodrisk.drivers import build_all

if __name__=='__main__':
    result=build_all();print(json.dumps(result,indent=2))
