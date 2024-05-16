#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: 02_New_Layer2_Vlan
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/13/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"

import argparse


def some_function():
    pass


def main():
    action = "New_Vlan_L2"

# Standard call to the main() function.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script Description",
        epilog="Usage: ' python 01_Extend_Existing_Layer2_Vlan' ",
    )

    # parser.add_argument('all', help='Execute all exercises in week 4 assignment')
    # parser.add_argument('-a', '--all', help='Execute all exercises in week 4 assignment', action='store_true',default=False)
    arguments = parser.parse_args()
    main()
