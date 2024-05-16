#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: 99_Deploy_ConfigurationPayload
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/15/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"

import streamlit as st
import yaml
import time

import utilities


def main():

    # Deploy Configuration Payload
    st.title("Deploy Approved Configuration Payload")

    # Load Subnet File to QA
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "Choose a Site Segmentation Subnet Excel file and click the Check Subnet File button",
        # type=["xlsx"],
    )

    cfg_dry_run = st.checkbox(
        "Dry Run Configuration (Only Display Commands to send)",
        key="CfgDryRun",
        value=True,
    )

    execute_commands = st.checkbox(
        "Execute Commands (Push Configuration to Switches)",
        key="ExecuteRun",
        value=False,
    )

    snow_tix = st.text_input("Enter the Change Request Number under which this work is covered:",
                             value="SNOW123456",
                             max_chars=10,
                             # placeholder="SNOW123456",
                             )

    approved_window = st.checkbox("Confirm Change is within approved change window")

    st.markdown("---")

    with st.form(key="Load_Configuration_Payload"):

        results_list = list()
        expander_check = st.expander("Configuration Payload", expanded=False)
        check_option = st.form_submit_button(label="Load Config Payload File")

        if check_option and approved_window:
            if uploaded_file is not None:
                file_name = uploaded_file.name
                loaded_config = yaml.safe_load(uploaded_file)
                with expander_check:
                    st.write(loaded_config)


                if cfg_dry_run:
                    # Show the payload for each switch

                    st.write(f"Configuration for Upstream Device {loaded_config['uplink_dev']}")
                    for line in loaded_config['cfg_list']:
                        st.text(line)
                    results_list.append(f"{loaded_config['uplink_dev']} DRY RUN ONLY")

                    st.write(f"Configuration for Access Device {loaded_config['hostname']}")
                    for line in loaded_config['cfg_list']:
                        st.text(line)
                    results_list.append(f"{loaded_config['hostname']} DRY RUN ONLY")

                if not cfg_dry_run and execute_commands:
                    # Execute payload
                    results_list.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Upstream Device ----------------------------------------------------------
                    st.markdown("---")
                    st.write(f"Configuration for Upstream Device {loaded_config['uplink_dev']}")

                    # create_cat_devobj_from_json_list
                    device_obj = utilities.create_autodetect_devobj(
                        loaded_config['uplink_dev'], session_log=True
                    )

                    if device_obj["username"] and device_obj["password"]:
                        (
                            conn_obj,
                            login_success,
                        ) = utilities.conn_netmiko(
                            "cisco_xe",
                            loaded_config['uplink_dev'],
                            device_obj["username"],
                            device_obj["password"],
                            device_obj["password"],
                        )

                        if login_success:

                            st.success(f"Login to {loaded_config['uplink_dev']} sucessful!")

                            # Show Vlans
                            st.write("PRE show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False
                            )
                            st.text(output)

                            # Push config
                            st.write("PUSHING Configuration Payload")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                loaded_config['cfg_list'],
                                method="config_set",
                                cfgmode_bool=True
                            )
                            st.text(output)

                            # Show Vlans
                            st.write("POST show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False
                            )
                            st.text(output)

                            # Disconnect from switch
                            conn_obj.disconnect()

                    # Access Device ----------------------------------------------------------
                    st.markdown("---")
                    st.write(f"Configuration for Access Device {loaded_config['hostname']}")

                    # create_cat_devobj_from_json_list
                    device_obj = utilities.create_autodetect_devobj(
                        loaded_config['hostname'], session_log=True
                    )

                    if device_obj["username"] and device_obj["password"]:
                        (
                            conn_obj,
                            login_success,
                        ) = utilities.conn_netmiko(
                            "cisco_xe",
                            loaded_config['hostname'],
                            device_obj["username"],
                            device_obj["password"],
                            device_obj["password"],
                        )

                        if login_success:
                            st.success(f"Login to {loaded_config['uplink_dev']} sucessful!")

                            # Show Vlans
                            st.write("PRE show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False
                            )
                            st.text(output)

                            # Push config
                            st.write("PUSHING Configuration Payload")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                loaded_config['cfg_list'],
                                method="config_set",
                                cfgmode_bool=True
                            )
                            st.text(output)

                            # Show Vlans
                            st.write("POST show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False
                            )
                            st.text(output)

                            # Show spanning tree
                            st.write("POST show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_config['uplink_dev'],
                                [f"show spanning-tree vlan {loaded_config['vlan_id']}"],
                                method="command",
                                cfgmode_bool=False
                            )
                            st.text(output)

                            # Disconnect from switch
                            conn_obj.disconnect()

                # Verification via SuzieQ


            else:
                st.error("Please load a File to process...")

# Standard call to the main() function.
if __name__ == '__main__':
    main()
