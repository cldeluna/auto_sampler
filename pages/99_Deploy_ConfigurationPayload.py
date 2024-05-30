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
import datetime

import utilities


def main():

    # Start of script execution
    start_time = datetime.datetime.now()

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

    snow_tix = st.text_input(
        "Enter the Change Request Number under which this work is covered:",
        value="SNOW123456",
        max_chars=10,
        # placeholder="SNOW123456",
    )

    approved_window = st.checkbox("Confirm Change is within approved change window")

    st.markdown("---")

    with st.form(key="Load_Configuration_Payload"):

        results_list = list()

        # Turn True into PASSED
        result_lookup = {True: "PASSED", False: "FAILED"}

        expander_check = st.expander("Configuration Payload", expanded=False)

        if cfg_dry_run:
            label = "Load Config Payload"
        elif not cfg_dry_run and execute_commands and approved_window and snow_tix:
            label = "Load and Execute Config Payload"
        else:
            label = "Load Config Payload"

        check_option = st.form_submit_button(label=label)

        if check_option and approved_window and snow_tix:
            if uploaded_file is not None:
                file_name = uploaded_file.name
                loaded_cfgpayload = yaml.safe_load(uploaded_file)
                with expander_check:
                    st.write(loaded_cfgpayload)

                if cfg_dry_run:
                    # Show the payload for each switch

                    st.write(
                        f"Configuration for Upstream Device {loaded_cfgpayload['uplink_dev']}"
                    )
                    for line in loaded_cfgpayload["cfg_list"]:
                        st.text(line)
                    results_list.append(
                        f"{loaded_cfgpayload['uplink_dev']} DRY RUN ONLY"
                    )

                    st.write(
                        f"Configuration for Access Device {loaded_cfgpayload['hostname']}"
                    )
                    for line in loaded_cfgpayload["cfg_list"]:
                        st.text(line)
                    results_list.append(f"{loaded_cfgpayload['hostname']} DRY RUN ONLY")

                if not cfg_dry_run and execute_commands:
                    # Execute payload
                    results_list.append(
                        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    # Upstream Device ----------------------------------------------------------
                    st.markdown("---")
                    st.write(
                        f"Configuration for Upstream Device {loaded_cfgpayload['uplink_dev']}"
                    )

                    # create_cat_devobj_from_json_list
                    device_obj = utilities.create_autodetect_devobj(
                        loaded_cfgpayload["uplink_dev"], session_log=True
                    )

                    if device_obj["username"] and device_obj["password"]:
                        (
                            conn_obj,
                            login_success,
                        ) = utilities.conn_netmiko(
                            "cisco_xe",
                            loaded_cfgpayload["uplink_dev"],
                            device_obj["username"],
                            device_obj["password"],
                            device_obj["password"],
                        )

                        if login_success:

                            st.success(
                                f"Login to {loaded_cfgpayload['uplink_dev']} successful!"
                            )

                            # Show Vlans
                            st.write("PRE show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False,
                            )
                            st.text(output)

                            # Push config
                            st.write("PUSHING Configuration Payload")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                loaded_cfgpayload["cfg_list"],
                                method="config_set",
                                cfgmode_bool=True,
                            )
                            st.text(output)

                            # Show Vlans
                            st.write("POST show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False,
                            )
                            st.text(output)

                            # Disconnect from switch
                            conn_obj.disconnect()

                    # Access Device ----------------------------------------------------------
                    st.markdown("---")
                    st.write(
                        f"Configuration for Access Device {loaded_cfgpayload['hostname']}"
                    )

                    # create_cat_devobj_from_json_list
                    device_obj = utilities.create_autodetect_devobj(
                        loaded_cfgpayload["hostname"], session_log=True
                    )

                    if device_obj["username"] and device_obj["password"]:
                        (
                            conn_obj,
                            login_success,
                        ) = utilities.conn_netmiko(
                            "cisco_xe",
                            loaded_cfgpayload["hostname"],
                            device_obj["username"],
                            device_obj["password"],
                            device_obj["password"],
                        )

                        if login_success:
                            st.success(
                                f"Login to {loaded_cfgpayload['uplink_dev']} successful!"
                            )

                            results_list.append(f"Change Request {snow_tix}")
                            results_list.append(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}")
                            results_list.append(f"Updates to device {loaded_cfgpayload['uplink_dev']}")

                            # Show Vlans
                            st.write("PRE show vlans")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False,
                            )
                            # st.text(output)

                            # Push config
                            st.write("PUSHING Configuration Payload")
                            output = utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                loaded_cfgpayload["cfg_list"],
                                method="config_set",
                                cfgmode_bool=True,
                            )
                            # st.text(output)

                            # Show Vlans
                            st.write("POST show vlans")
                            output += utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                ["show vlan"],
                                method="command",
                                cfgmode_bool=False,
                            )
                            # st.text(output)

                            # Show spanning tree
                            st.write("POST show vlans")
                            output += utilities.send_netmiko_commands(
                                conn_obj,
                                loaded_cfgpayload["uplink_dev"],
                                [
                                    f"show spanning-tree vlan {loaded_cfgpayload['vlan_id']}"
                                ],
                                method="command",
                                cfgmode_bool=False,
                            )
                            st.text(output)
                            results_list.extend(output.splitlines())

                            test_list = ["901", "IOT_1.1.1.0/24", "Root"]
                            test_res_dict = utilities.split_and_search(output, test_list)

                            st.write(test_res_dict)
                            test_res_list = test_res_dict.values()
                            test_res_setlist = list(set(test_res_list))

                            # Record Tests
                            for line in test_list:
                                results_list.append(f"Test {line}: {result_lookup[test_res_dict[line]]}")

                            # If there PASS and save config
                            if len(test_res_setlist) == 1 and test_res_setlist[0]:
                                st.success(":white_check_mark: Checks PASSED!")
                                # Save Configuration
                                st.subheader("Saving Configuration")
                                out = conn_obj.save_config()
                                st.text(out)

                                st.success(
                                    f"Configuration Payload Successfully Executed!  All Operational Tests Passed"
                                )
                                ready_for_closeout = True

                            # Disconnect from switch
                            conn_obj.disconnect()

                            # Save Testing Results to Testing Report
                            # Date stamp for Report Output
                            file_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

                            filename = f"{snow_tix}_TestResults_{file_timestamp}.txt"
                            utilities.create_or_append_to_file(results_list, filename)
                            st.write(f"Saved Test Results to {filename}")

                    # Verification via SuzieQ ----------------------------------------------------
                    st.markdown("---")
                    st.title("Verification")

                    with st.spinner("Waiting for Polling Cycle to complete"):
                        time.sleep(5)

                    # Get Existing Vlan Details
                    vlan_details_dict = utilities.find_vlan_at_site(
                        loaded_cfgpayload["location"],
                        loaded_cfgpayload["vlan_id"],
                        format="dictionary",
                    )
                    st.write(vlan_details_dict)

                    st.markdown(f"### Is the vlan configured on both switches?")
                    # Confirm Vlan is on Uplink switch
                    onsw_bool, vlan_response, allvlans_response = (
                        utilities.find_vlan_on_switch(
                            loaded_cfgpayload["vlan_id"],
                            loaded_cfgpayload["uplink_dev"],
                        )
                    )
                    st.write(vlan_response)

                    if onsw_bool:
                        st.success(
                            f"Vlan {loaded_cfgpayload['vlan_id']} configured "
                            f"on switch {loaded_cfgpayload['uplink_dev']}"
                        )
                        st.write(vlan_response)
                    # Confirm Vlan is on Access switch
                    onsw_bool, vlan_response, allvlans_response = (
                        utilities.find_vlan_on_switch(
                            loaded_cfgpayload["vlan_id"],
                            loaded_cfgpayload["hostname"],
                        )
                    )
                    if onsw_bool:
                        st.success(
                            f"Vlan {loaded_cfgpayload['vlan_id']} configured "
                            f"on switch {loaded_cfgpayload['hostname']}"
                        )

                    st.markdown(f"### Is the vlan trunked on both switches?")
                    # Is vlan on uplink Po loaded_cfgpayload['uplink_po']
                    if (
                        loaded_cfgpayload["uplink_po"]
                        in vlan_details_dict[loaded_cfgpayload["uplink_dev"]][
                            "interfaces"
                        ]
                    ):
                        st.success(
                            f"Vlan {loaded_cfgpayload['vlan_id']} is trunked "
                            f"on {loaded_cfgpayload['uplink_po']} "
                            f"on switch {loaded_cfgpayload['uplink_dev']}"
                        )
                        st.write(
                            vlan_details_dict[loaded_cfgpayload["uplink_dev"]][
                                "interfaces"
                            ]
                        )

                    # Is vlan on uplink Po loaded_cfgpayload['uplink_po']
                    if (
                        loaded_cfgpayload["uplink_po"]
                        in vlan_details_dict[loaded_cfgpayload["hostname"]][
                            "interfaces"
                        ]
                    ):
                        st.success(
                            f"Vlan {loaded_cfgpayload['vlan_id']} is trunked "
                            f"on {loaded_cfgpayload['uplink_po']} "
                            f"on switch {loaded_cfgpayload['hostname']}"
                        )
                        st.write(
                            vlan_details_dict[loaded_cfgpayload["hostname"]][
                                "interfaces"
                            ]
                        )
                    st.image(
                        "images/Step8CloseOut.jpg",
                        caption="We are Done!",
                        width=950,
                    )

                st.markdown("---")
                # ----------------------------------- SCRIPT EXECUTION TIME --------------------------------------------
                st.success(f"Change Request {snow_tix} Successfully Completed and Documented")
                end_time = datetime.datetime.now()
                st.markdown(f"**Execution Time: {end_time - start_time}**")

            else:
                st.error("Please load a File to process...")



# Standard call to the main() function.
if __name__ == "__main__":
    main()
