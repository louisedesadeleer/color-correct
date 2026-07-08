#!/bin/bash
# Regenerate all .cube LUTs from the look chains (subtle defaults + full-strength)
set -e
cd "$(dirname "$0")/.."
mkdir -p luts/subtle luts/full

gen() { python3 scripts/chain2cube.py "$3" "luts/$1/$2.cube" "$2 ($1)"; }

# --- subtle (default) ---
gen subtle golden-hour "colortemperature=temperature=6150,curves=master='0/0.018 0.6/0.59 1/0.94',colorbalance=rs=0.015:gh=0.015,vibrance=intensity=0.08"
gen subtle honey       "colortemperature=temperature=6050,curves=master='0/0.023 0.5/0.5 1/0.95',vibrance=intensity=0.04,colorbalance=gm=0.01:gh=0.01"
gen subtle linen       "curves=master='0/0.018 0.5/0.5 1/0.915',colortemperature=temperature=6100,colorbalance=gh=-0.015,eq=saturation=0.965"
gen subtle super-8     "curves=master='0/0.02 0.5/0.51 1/0.9',colortemperature=temperature=5900,colorbalance=gs=-0.01:gm=-0.01,vibrance=intensity=0.05"
gen subtle oat-milk    "curves=master='0/0.035 0.5/0.51 1/0.915',colorbalance=rs=0.02:rm=0.015:rh=-0.03:bh=0.025,eq=saturation=0.985"
gen subtle espresso    "eq=contrast=1.03:saturation=0.95,colorbalance=rm=0.025:bm=-0.015,curves=master='0/0.02 0.5/0.485 1/0.94'"
gen subtle velvet      "curves=master='0/0.035 0.5/0.5 1/0.935',colortemperature=temperature=6000,colorbalance=gs=-0.01:gh=0.015,vibrance=intensity=0.04"
gen subtle popsicle    "eq=brightness=0.01:contrast=1.03,curves=master='0/0.025 0.5/0.515 1/1',vibrance=intensity=0.06,colorbalance=gh=0.015"
gen subtle terracotta  "eq=contrast=1.035,colortemperature=temperature=5850,colorbalance=gs=-0.02:gm=-0.01,curves=master='0/0.01 0.5/0.5 1/0.99'"

# --- full strength (consensus reference) ---
gen full golden-hour "colortemperature=temperature=5800,curves=master='0/0.035 0.6/0.58 1/0.885',colorbalance=rs=0.03:gh=0.03,vibrance=intensity=0.15"
gen full honey       "colortemperature=temperature=5600,curves=master='0/0.045 0.5/0.5 1/0.9',vibrance=intensity=0.08,colorbalance=gm=0.02:gh=0.02"
gen full linen       "curves=master='0/0.035 0.5/0.5 1/0.83',colortemperature=temperature=5700,colorbalance=gh=-0.03,eq=saturation=0.93"
gen full super-8     "curves=master='0/0.04 0.5/0.52 1/0.8',colortemperature=temperature=5300,colorbalance=gs=-0.02:gm=-0.02,vibrance=intensity=0.1"
gen full oat-milk    "curves=master='0/0.07 0.5/0.52 1/0.83',colorbalance=rs=0.04:rm=0.03:rh=-0.06:bh=0.05,eq=saturation=0.97"
gen full espresso    "eq=contrast=1.06:saturation=0.9,colorbalance=rm=0.05:bm=-0.03,curves=master='0/0.04 0.5/0.47 1/0.88'"
gen full velvet      "curves=master='0/0.07 0.5/0.5 1/0.87',colortemperature=temperature=5500,colorbalance=gs=-0.02:gh=0.03,vibrance=intensity=0.08"
gen full popsicle    "eq=brightness=0.02:contrast=1.06,curves=master='0/0.05 0.5/0.53 1/1',vibrance=intensity=0.12,colorbalance=gh=0.03"
gen full terracotta  "eq=contrast=1.07,colortemperature=temperature=5200,colorbalance=gs=-0.04:gm=-0.02,curves=master='0/0.02 0.5/0.5 1/0.98'"

echo "done: $(ls luts/subtle | wc -l | tr -d ' ') subtle + $(ls luts/full | wc -l | tr -d ' ') full"
