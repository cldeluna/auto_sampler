#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: 04_New_PortChannel
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/15/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"

import streamlit as st


def some_function():
    pass


def main():
    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")

    with st.sidebar:
        st.image(
            "images/EIAlogo_OnWhite-01-Transparent2.jpg",
            caption="",
            width=75,
        )

        url = "https://eianow.com/"
        st.markdown(f"**[EIA]({url})**")

        st.image("images/WorkInProgress.png", width=200)


# Standard call to the main() function.
if __name__ == "__main__":
    main()
