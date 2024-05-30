#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: Automation_Sampler.py
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/13/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"

import streamlit as st
import yaml

import utilities


def load_yaml_file(yfile):
    content = None

    with open(yfile) as f:
        try:
            content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            st.error(e)
    return content


def main():
    """
    This is the main entrance point to calling the Automation Sampler tools
    :return: N/A
    """
    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")

    with st.sidebar:
        st.image(
            "images/EIAlogo_OnWhite-01-Transparent2.jpg",
            caption="",
            width=75
            ,
        )

        url = "https://eianow.com/"
        st.markdown(f"**[EIA]({url})**")

    st.title("AutoCon1 Automation Sampler")

    st.image(
        "images/NAF_AnatomyOfNetChange.jpg",
        caption="Anatomy of a Well Known Network Change",
        use_column_width=True
    )

    st.image(
        "images/2024-05-13_12-06-19.jpg",
        caption="AutoCon1 Automation Sampler",
        width=650,
    )

    well_known_actions_dict = utilities.load_wellknown_actions()

    st.markdown(
        """
        ## Well Know Actions
        """
    )

    for action in well_known_actions_dict["Well_Known_Actions"].keys():
        st.write(f"- {action}")

    st.session_state.well_known_acts_dict = well_known_actions_dict[
        "Well_Known_Actions"
    ]


# Standard call to the main() function.
if __name__ == "__main__":
    main()
