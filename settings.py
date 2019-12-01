#!/usr/bin/env python3
"""
Common settings for my election/referendum related code.

This file should be written so that doing

  from settings import *

shouldn't have any nasty side-effects
"""

import os

INCLUDES_DIR = os.path.join(os.path.dirname(__file__), 'includes')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
