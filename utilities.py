#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: utilities.py
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/13/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"


import os
import re
import sys
import yaml
import requests
import time
import datetime
import jinja2
import ciscoconfparse
import dotenv

import pandas as pd
import streamlit as st

import logging
import netmiko
from netmiko import ConnectHandler, redispatch


def load_yaml_file(yfile):
    content = None

    with open(yfile) as f:
        try:
            content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            st.error(e)
    return content


def save_yaml_file(data, fn):

    with open(fn, "w") as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False)


def create_or_append_to_file(data_list, fn):
    with open(fn, "a") as f:
        for line in data_list:
            f.write(f"{line}\n")


def try_sq_rest_call_http(uri_path, url_options):
    """_summary_
    SuzieQ API REST Calln in a Try/Except block
    Args:
        url (_type_): _description_

    Returns:
        _type_: _description_
    """
    API_ACCESS_TOKEN = "496157e6e869ef7f3d6ecb24a6f6d847b224ee4f"
    API_ENDPOINT = "10.1.10.47"

    # http://10.1.10.47:8000/api/v2/devconfig/show?hostname=indian-ocean-sw01&view=latest&columns=default&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f
    # http://10.1.10.47:8000/api/v2/devconfig/show??hostname=indian-ocean-sw01&view=latest&columns=default&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f
    url = f"http://{API_ENDPOINT}:8000{uri_path}?{url_options}&access_token={API_ACCESS_TOKEN}"
    print(url)

    # Send API request, return as JSON
    response = dict()
    try:
        response = requests.get(url).json()
    except Exception as e:
        st.error(
            "Connection to SuzieQ REST API Failed.  Please confirm the REST API is running!"
        )
        st.text(e)
        # st.stop()
        response = False

    return response


def find_vlans_in_namespace(namespace):

    ns_vlan_bool = False
    ns_vlan_list = list()
    dont_care_vlans = [1, 1002, 1003, 1004, 1005]

    URI_PATH = "/api/v2/vlan/unique"
    URL_OPTIONS = f"namespace={namespace}&view=latest&columns=vlan"

    sq_api_response_vlan = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)

    if sq_api_response_vlan:
        ns_vlan_bool = True
        ns_vlan_list = [
            line["vlan"]
            for line in sq_api_response_vlan
            if line["vlan"] not in dont_care_vlans
        ]
    else:
        st.error(f"Error getting Unique Vlans in namespace")
        sq_api_response_vlan = []

    return ns_vlan_bool, ns_vlan_list


def find_vlan_on_switch(vlanx, switch):
    vlan_configured_on_sw = False

    URI_PATH = "/api/v2/vlan/show"
    URL_OPTIONS = f"hostname={switch}&view=latest&columns=default&vlan={vlanx}"

    sq_api_response_vlan = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)

    if sq_api_response_vlan:
        vlan_configured_on_sw = True
    else:
        st.error(f"Vlan {vlanx} is not configured on switch {switch}")
        sq_api_response_vlan = []

    URL_OPTIONS = f"hostname={switch}&view=latest&columns=default&state=active"

    sq_api_response_vlan_allvlans = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)

    # http://10.1.10.47:8000/api/v2/vlan/show?hostname=indian-ocean-sw01&view=latest&columns=default&state=active&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f

    if sq_api_response_vlan_allvlans:
        vlan_configured_on_sw = True
    else:
        st.error(f"Failed to get all Vlans on switch {switch}")
        sq_api_response_vlan_allvlans = []

    return vlan_configured_on_sw, sq_api_response_vlan, sq_api_response_vlan_allvlans


def get_namespace_list():

    # Initialize
    namespace_list = list()

    # Trick to get a unique list of namespaces for the pull down
    URI_PATH = "/api/v2/device/unique"
    URL_OPTIONS = f"columns=namespace&ignore_neverpoll=true"
    ns_response = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    #
    # st.write(ns_response)
    # for line in ns_response:
    #     st.text(line)

    # Create a list of namespaces from the list of dictionaries
    if ns_response:
        namespace_list = [line["namespace"] for line in ns_response]
    else:
        st.error(f"Problem with accessing SuzieQ REST API")
        st.write(f"OK Response: {ns_response.ok}")
        st.write(f"Status Code: {ns_response.status_code}")
        st.write(f"Reason: {ns_response.reason}")
        st.write(ns_response.json())

    return namespace_list


def get_switches_in_location(namespacex):

    # Initialize
    switch_list = list()

    view = "latest"

    # Trick to get a unique list of namespaces for the pull down
    URI_PATH = "/api/v2/device/show"
    URL_OPTIONS = f"view={view}&namespace={namespacex}"
    sw_response = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    #
    # st.write(sw_response)
    # for line in sw_response:
    #     st.text(line)

    # Create a list of namespaces from the list of dictionaries
    if sw_response:
        switch_list = [line["hostname"] for line in sw_response]
    else:
        st.error(f"Problem with accessing SuzieQ REST API")
        st.write(f"OK Response: {sw_response.ok}")
        st.write(f"Status Code: {sw_response.status_code}")
        st.write(f"Reason: {sw_response.reason}")
        st.write(sw_response.json())

    return switch_list


def load_vlan_guidelines():

    st.markdown("---")
    vlan_guidelines_df = pd.DataFrame()
    # Load Vlan Guidelines
    st.markdown("### Loading Vlan Guidelines")
    vlan_guidelines_fn = "vlan_guidelines.yml"
    vlan_guidelines_dict = load_yaml_file(vlan_guidelines_fn)
    vlan_type_list = vlan_guidelines_dict.keys()

    vlan_guidelines_df = pd.DataFrame.from_dict(vlan_guidelines_dict)

    return vlan_type_list, vlan_guidelines_dict, vlan_guidelines_df


def load_wellknown_actions():

    st.write("Loading Well know Actions Data")
    wk_yml_fn = "WellKnownActions_PROD.yml"
    well_known_actions_dict = load_yaml_file(wk_yml_fn)

    return well_known_actions_dict


def load_wellknown_action(act_dict_key):

    load_wellknown_actions()

    if "well_known_acts_dict" not in st.session_state:
        st.error("State not Set")
        st.stop()

    act_dict = st.session_state.well_known_acts_dict
    # st.write(act_dict[act_dict_key])

    st.write(f"Action Workflow Steps")

    for item_tuple in enumerate(act_dict[act_dict_key]["Description"], start=1):
        st.write(f"- {item_tuple[0]}. {item_tuple[1]}")

    st.write(f"Action Impact: {act_dict[act_dict_key]['Impact_Rating']}")
    st.write(f"- {act_dict[act_dict_key]['Impact_Description']}")

    return act_dict


# Get MLAG


def get_mlag_from_switch(hn):
    pass

    # http://10.1.10.47:8000/api/v2/mlag/show?hostname=redsea_sw01&view=latest&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f


def get_intf_bonded_switch(switch):
    pass
    # bond
    # http://10.1.10.47:8000/api/v2/interface/show?hostname=atlantic-sw01&view=latest&columns=default&type=bond&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f

    # bond_slave
    # http://10.1.10.47:8000/api/v2/interface/show?hostname=atlantic-sw01&view=latest&columns=default&type=bond_slave&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f

    po_configured_on_sw_bool = False
    view = "latest"

    URI_PATH = "/api/v2/interface/show"
    URL_OPTIONS = f"hostname={switch}&view=latest&columns=default&type=bond_slave"

    sq_api_response_po = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    # st.write(sq_api_response_po)

    if sq_api_response_po:
        po_configured_on_sw_bool = True
        po_configured_on_sw_dict = sq_api_response_po
    else:
        st.error(f"No Port-channel is configured on switch {switch}")
        po_configured_on_sw_dict = []

    return po_configured_on_sw_bool, po_configured_on_sw_dict


def get_intf_trunk_switch(switch):

    # http://10.1.10.47:8000/api/v2/interface/show?hostname=atlantic-sw01&view=latest&columns=default&portmode=trunk&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f

    po_configured_on_sw_bool = False
    view = "latest"

    URI_PATH = "/api/v2/interface/show"
    URL_OPTIONS = f"hostname={switch}&view=latest&columns=default&portmode=trunk"

    sq_api_response_po = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    # st.write(sq_api_response_po)

    if sq_api_response_po:
        po_configured_on_sw_bool = True
        po_configured_on_sw_dict = sq_api_response_po
    else:
        st.error(f"No Port-channel is configured on switch {switch}")
        po_configured_on_sw_dict = []

    return po_configured_on_sw_bool, po_configured_on_sw_dict


def get_lldp_switch(switch, ifname="all"):

    # http://10.1.10.47:8000/api/v2/lldp/show?hostname=redsea_sw01&view=latest&columns=default&ifname=GigabitEthernet1%2F0%2F24&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f
    lldp_nei_bool = False
    view = "latest"

    URI_PATH = "/api/v2/lldp/show"

    if ifname == "all":
        URL_OPTIONS = f"hostname={switch}&view=latest&columns=default"
    else:
        URL_OPTIONS = f"hostname={switch}&view=latest&columns=default&ifname={ifname}"

    sq_api_response = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    # st.write(sq_api_response)

    if sq_api_response:
        lldp_nei_bool = True
        lldp_nei_lod = sq_api_response
    else:
        st.error(f"No results for LLDP search on switch {switch} interface {ifname}")
        lldp_nei_lod = []

    return lldp_nei_bool, lldp_nei_lod


def get_devcfg_switch(switch):

    # http://10.1.10.47:8000/api/v2/devconfig/show?hostname=redsea_sw01&view=latest&columns=default&access_token=496157e6e869ef7f3d6ecb24a6f6d847b224ee4f

    cfg_bool = False
    view = "latest"

    URI_PATH = "/api/v2/devconfig/show"
    URL_OPTIONS = f"hostname={switch}&view=latest&columns=default"

    sq_api_response = try_sq_rest_call_http(URI_PATH, URL_OPTIONS)
    # st.write(sq_api_response_po)

    if sq_api_response:
        cfg_bool = True
        cfg_lod = sq_api_response
    else:
        st.error(f"Unable to extract device configuration for {switch}")
        po_configured_on_sw_dict = []

    return cfg_bool, cfg_lod


def cfg_xfer_clab(cfg):
    st.write(
        "Transforming production device configuration from SuzieQ to containerlab configuration"
    )
    content_list = cfg.splitlines()
    # st.write(len(content_list))
    # st.write(content_list)

    clab_cfg_list = list()

    parsed_obj = ciscoconfparse.CiscoConfParse(content_list)
    # st.write(parsed_obj)
    # Hostname
    lines_obj = parsed_obj.find_lines(r"^hostname")
    # st.write(lines_obj[0])
    clab_cfg_list.append(lines_obj[0])

    # Add Lab Authentication
    lab_aaa_list = [
        "aaa new-model",
        "aaa authentication login default local",
        "aaa authorization exec default local",
        "username admin privilege 15 password admin123",
        "username cisco privilege 15 password cisco",
    ]
    clab_cfg_list.extend(lab_aaa_list)

    # Vlans
    lines_obj = parsed_obj.find_objects(r"^vlan\s\d+")
    lines_with_kids_list = get_kids(lines_obj)
    clab_cfg_list.extend(lines_with_kids_list)

    # Spanning Tree
    lines_obj = parsed_obj.find_objects(r"^spanning-tree")
    clab_cfg_list.extend(get_kids(lines_obj))

    # Domain
    lines_obj = parsed_obj.find_objects(r"domain")
    clab_cfg_list.extend(get_kids(lines_obj))

    # VTP mode
    lines_obj = parsed_obj.find_objects(r"vtp")
    clab_cfg_list.extend(get_kids(lines_obj))

    # Interfaces
    lines_obj = parsed_obj.find_objects(r"^interface")
    clab_cfg_list.extend(get_kids(lines_obj))

    st.write(clab_cfg_list)
    # st.stop()


def get_kids(parent_obj):

    cfg_list = list()
    for item in parent_obj:

        # st.text("parent: \n{}".format(item.text))
        it = item.text.rstrip()
        cfg_list.append(it)
        child_list = []
        for child in item.all_children:
            # st.text("children: {}".format(child.text))
            child_list.append(child.text.rstrip())
        cfg_list.extend(child_list)

    return cfg_list


def render_j2template(cfg, j2_template, debug=False):
    ##############################################
    ### Render the Jinja2 Template with the values
    ##############################################

    cwd = os.path.dirname(os.path.realpath(__file__))
    j2envpath = os.path.join(cwd)
    template_dir_full_path = os.path.join(j2envpath, "./templates")
    if debug:
        print(f"j2envpath: {j2envpath}")
    if debug:
        print(f"template_full_path: {template_dir_full_path}")
    if debug:
        print(f"j2_template: {j2_template}")

    J2ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir_full_path))

    template = J2ENV.get_template(j2_template)
    dattim = format(datetime.datetime.now())

    rendered = template.render(dattim=dattim, cfg=cfg, template=j2_template)
    if debug:
        print(rendered)

    return rendered


def write_rendered_to_file(full_file_path, content, filename, type="full", mode="w"):
    output_filename = os.path.join(full_file_path, filename)
    st.write(
        f"Creating rendered configuration file {filename} type {type.upper()}: \n\tFull Path: {full_file_path}\n"
    )
    content_list = list()
    with open(output_filename, mode) as outfile:
        if type.lower() == "full":
            outfile.write(content)
            content_list = content.splitlines()
        elif type.lower() == "cfg":
            content_with_lines = content.splitlines()
            for line in content_with_lines:
                if not re.search(r"^!", line) and not re.search(r"^$", line):
                    outfile.write(line + "\n")
                    content_list.append(line)
        elif type.lower() == "rollback":
            content_with_lines = content.splitlines()
            for line in content_with_lines:
                if re.search(r"^!-", line) and not re.search(r"^$", line):
                    newline = re.sub(r"^!-", "", line)
                    outfile.write(newline + "\n")
                    content_list.append(newline)
        else:
            outfile.write(content)

    # Return a stripped list of the commands
    return [l.strip() for l in content_list]


def netmiko_jump(
    show_cmd="show Vlan",
    access_hn="Access_Switch",
    uplink_hn="Uplink_Switch",
    cfg_list=[],
    force_lab_restart=False
):

    passed_tests = False
    out = ""
    test_report_list = list()

    # Define jump server details
    #  1077  cp autotools_droplet_rsa autotools_droplet_rsa.private.backup
    #  1078  ssh-keygen -p -m PEM -f ./autotools_droplet_rsa
    # had to fiddle with key
    jump_server = "74.208.184.140"
    jump_server = {
        "device_type": "linux",  # or the appropriate device type
        "host": jump_server,
        "username": "claudia",
        "password": "D0dgers1!",
        "secret": "D0dgers1!",
        "use_keys": True,
        "key_file": "/Users/claudiadeluna/.ssh/autotools_droplet_rsa",
        "session_log": "log_jumpbox_output.txt",
        # "read_timeout_override": 120,
        "delay_factor_compat": True,
        "fast_cli": False,
    }

    # Define remote device details
    # Uplink device
    remote_device = {
        "device_type": "cisco_ios",
        "host": "172.20.20.2",
        "username": "cisco",
        "password": "cisco",
        "session_log": "log_remotedev_output.txt",
        "delay_factor_compat": True,
        "fast_cli": False,
        "role": "distribution",
        "hostname": uplink_hn,
    }

    # Uplink device
    remote_device_access = {
        "device_type": "cisco_ios",
        "host": "172.20.20.3",
        "username": "cisco",
        "password": "cisco",
        "session_log": "log_remotedev_output.txt",
        "delay_factor_compat": True,
        "fast_cli": False,
        "role": "access",
        "hostname": access_hn,
    }

    # Connect to the jump server
    jump_conn = ConnectHandler(**jump_server)
    # output = jump_conn.send_command('pwd')
    # st.write(output)

    # Elevate privileges to root
    jump_conn.enable()

    # output = jump_conn.send_command(
    #     'sudo apt-get update',
    #     expect_string=r"root@ubuntu:.+#",
    # )
    # st.write(output)
    virtual_lab = "new_l2vlan_lab"
    clab_name = "newl2vlan"
    st.write("Moving to virtual testlab directory ...")
    output = jump_conn.send_command(
        f"cd /home/claudia/containerlabs/{virtual_lab}",
        expect_string=r"root@ubuntu:.+#",
    )
    st.write(output)
    test_report_list.append(f"Virtual Lab: {virtual_lab}")
    test_report_list.append(f"Container Lab Name: {clab_name}")
    test_report_list.append(output)

    output = jump_conn.send_command(
        "pwd",
        expect_string=r"root@ubuntu:.+#",
    )
    st.write(output)
    test_report_list.append(output)

    # Check to see if lab is up
    st.write(f"Checking to see if virtual lab {clab_name}  is running")
    output = jump_conn.send_command(
        "sudo containerlab inspect",
        expect_string=r"root@ubuntu:.+#",
    )
    st.text(output)
    test_report_list.append(output)

    test_res_dict = split_and_search(output, [clab_name, "running"])

    st.write(test_res_dict)
    test_res_list = test_res_dict.values()
    test_res_setlist = list(set(test_res_list))
    st.write(f"Test Results: {test_res_setlist}")

    if len(test_res_setlist) == 1 and test_res_setlist[0] and not force_lab_restart:
        st.info(f"Lab is running")
        test_report_list.append("Lab is running")
        wait_secs = 0
    else:
        if force_lab_restart:
            st.write(":eight_pointed_black_star: Requested vLab restart")
        # Start the lab
        st.write(":roller_coaster: Spinning up containerlab topology ...")
        output = jump_conn.send_command(
            "sudo containerlab deploy --reconfigure",
            expect_string=r"root@ubuntu:.+#",
        )
        st.text(output)
        test_report_list.append("Spinning up vLab")
        test_report_list.append(output)
        wait_secs = 7

    # st.write("Clearing SSH keys ...")
    # # ssh-keygen -f "/root/.ssh/known_hosts" -R "172.20.20.3"
    # output = jump_conn.send_command(
    #     'ssh-keygen -f "/root/.ssh/known_hosts" -R "172.20.20.3',
    #     expect_string=r"root@ubuntu:.+#",
    # )
    # st.text(output)
    #
    # output = jump_conn.send_command(
    #     'ssh-keygen -f "/root/.ssh/known_hosts" -R "172.20.20.2',
    #     expect_string=r"root@ubuntu:.+#",
    # )
    # st.text(output)

    # Wait a few seconds for switches to accept ssh connections
    time.sleep(wait_secs)
    st.write("Sending Command to Virtual Lab Switch")
    # showVersionThroughtJumpHost(jump_conn, remote_device)

    # Turn True into PASSED
    result_lookup = {True: "PASSED", False: "FAILED"}

    # Configure remote_device_uplink
    st.subheader(f"Updating vLab Uplink {remote_device['hostname']}")
    passed_tests_uplink = send_command_via_jumphost(
        jump_conn, remote_device, command="show vlan", cfg_set=cfg_list
    )
    test_report_list.append(f"Updating vLab Uplink {remote_device['host']}")
    test_report_list.append(f"vLab Test Results: {result_lookup[passed_tests_uplink]}")

    st.subheader(f"Updating vLab Access {remote_device_access['hostname']}")
    passed_tests_access = send_command_via_jumphost(
        jump_conn, remote_device_access, command="show vlan", cfg_set=cfg_list
    )
    test_report_list.append(f"Updating vLab Access {remote_device_access['hostname']}")
    test_report_list.append(f"vLab Test Results: {result_lookup[passed_tests_access]}")

    if passed_tests_uplink and passed_tests_access:
        passed_tests = True
        test_report_list.append(
            f"All vLab Tests Results: {result_lookup[passed_tests]}"
        )

    # Disconnect from the remote device and jump server
    jump_conn.disconnect()

    # TODO: Save Testing Results to Testing Report
    # Date stamp for Report Output
    file_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    cwd_path = os.getcwd()

    filename = f"vLab_TestResults_{file_timestamp}.txt"
    create_or_append_to_file(test_report_list, filename)
    st.write(f"Saved Test Results to {filename}")

    return passed_tests


def send_command_via_jumphost(
    jump_host_connobj, device, command="show version", cfg_set="", debug=True
):
    """
        https://netprepare.com/blog/netmiko/
    "
        root@ubuntu:~# ssh -o StrictHostKeyChecking=no cisco@172.20.20.3
        Warning: Permanently added '172.20.20.3' (ED25519) to the list of known hosts.
        (cisco@172.20.20.3) Password:

        :param jump_host_connobj:
        :param device:
        :param command:
        :return:
    """

    ready_for_deployment = False
    out = ""

    if debug:
        logging.basicConfig(filename="demo_netmiko.log", level=logging.DEBUG)
        logger = logging.getLogger("netmiko")

    st.text(f"ssh -o StrictHostKeyChecking=no {device['username']}@{device['host']}")

    out = jump_host_connobj.send_command_timing(
        f"ssh -o StrictHostKeyChecking=no {device['username']}@{device['host']}\n",
    )
    st.text(out)
    if "assword" in out or "added" in out:
        st.text("Sending credentials ...")
        out = jump_host_connobj.send_command_timing(device["password"] + "\n")
    elif "The authenticity of host ":
        out = jump_host_connobj.send_command_timing("yes\n")
        out = jump_host_connobj.send_command_timing(device["password"] + "\n")
    else:
        st.error("-----------Unknown return from ssh session")
    redispatch(jump_host_connobj, device_type=device["device_type"])
    jump_host_connobj.send_command_timing("enable")
    out = jump_host_connobj.find_prompt()
    # st.write(f"Prompt is {out}")
    out = jump_host_connobj.send_command(
        command,
        expect_string=r".+#",
    )
    st.text(out)

    if cfg_set:
        st.write("Sending Configuration Payload")
        st.write(cfg_set)
        out = jump_host_connobj.send_config_set(cfg_set)
        st.text(out)

        out = jump_host_connobj.send_command(
            command,
            expect_string=r".+#",
        )
        st.text(out)

        out += jump_host_connobj.send_command(
            "show run interface Port-channel119",
            expect_string=r".+#",
        )
        st.text(out)

        if device["role"] == "access":
            out += jump_host_connobj.send_command(
                "show spanning-tree vlan 901",
                expect_string=r".+#",
            )
            st.text(out)
            test_list = ["901", "IOT_1.1.1.0/24", "root"]
        else:
            test_list = ["901", "IOT_1.1.1.0/24"]

        test_res_dict = split_and_search(out, test_list)

        st.write(test_res_dict)
        test_res_list = test_res_dict.values()
        test_res_setlist = list(set(test_res_list))

        # If there PASS and save config
        if len(test_res_setlist) == 1 and test_res_setlist[0]:

            st.success(":white_check_mark: Checks PASSED!")
            # Save Configuration
            st.subheader("Saving Virtual Lab Configuration")
            out = jump_host_connobj.save_config()
            st.text(out)
            # net_connect.save_config()

            st.success(
                f"Configuration Payload Generated and Successfully Tested!  Ready for Operational Deployment"
            )
            ready_for_deployment = True

        else:
            st.error(":heavy_exclamation_mark: Payload Test Failed!")

    else:
        st.write("No configuration payload provided")

    return ready_for_deployment


def showVersionThroughtJumpHost(jump_host, device):
    netCom = ConnectHandler(**jump_host)
    out = netCom.send_command_timing(
        "ssh {}@{}\n".format(device["username"], device["host"])
    )
    if "assword" in out:
        out = netCom.send_command_timing(device["password"] + "\n")
    elif "The authenticity of host ":
        out = netCom.send_command_timing("yes\n")
        out = netCom.send_command_timing(device["password"] + "\n")
    else:
        st.error("-----------Unknown return from ssh session")
    redispatch(netCom, device_type=device["device_type"])
    netCom.send_command_timing("enable")
    netCom.find_prompt()
    out = netCom.send_command("show version")
    st.write(out)


def split_and_search(out, search_list=[]):

    # Split the output text
    out_lines = out.splitlines()

    # Check for Vlan 901 and name string in out
    test_result_dict = dict()

    # Initialize the DICT with FALSE
    for test in search_list:
        test_result_dict.update({test: False})

        for line in out_lines:
            if test in line:
                test_result_dict.update({test: True})

    return test_result_dict


# From utils_netmiko -----------------------------------
def conn_netmiko(dev_cls, mgt_ip, unm, upw, epw):
    dev_cn = ""
    lgin_suc = False

    prot = "SSH"

    try:
        dev_cn = netmiko.ConnectHandler(
            device_type=dev_cls, ip=mgt_ip, username=unm, password=upw, secret=epw
        )
        lgin_suc = True

    except netmiko.NetMikoAuthenticationException:
        st.write(
            "NetMikoAuthenticationException: Device failed {} Authentication with username {}".format(
                prot, unm
            )
        )
        lgin_suc = False

    except (EOFError, netmiko.NetMikoTimeoutException):
        st.write("SSH is not enabled for this device.")
        lgin_suc = False
        try_tel = True

    except Exception as e:
        st.write(
            "\tGeneral Exception: ERROR!:"
            + str(sys.exc_info()[0])
            + "==>"
            + str(sys.exc_info()[1])
        )
        st.write(str(e))
        lgin_suc = False

    return dev_cn, lgin_suc


def conn_in_enable(dev_conn):
    # Check to see if login has resulted in enable mode (i.e. priv level 15)
    is_enabled = dev_conn.check_enable_mode()
    # print("is enabled = {}".format(is_enabled))

    if not is_enabled:
        try:
            dev_conn.enable()
            en_success = True
        except Exception as e:
            st.write(str(e))
            st.write("Cannot enter enter enable mode on device!")
            en_success = False

    else:
        st.write("Device already in enabled mode!")
        en_success = True

    return en_success


def create_autodetect_devobj(dev, auth_timeout=20, session_log=False, debug=False):
    """
        dev = {
        'device_type': 'cisco_nxos',
        'ip' : 'sbx-nxos-mgmt.cisco.com',
        'username' : user,
        'password' : pwd,
        'secret' : sec,
        'port' : 8181,
        "fast_cli": False,
    }
    """

    dotenv.load_dotenv()
    dev_obj = {}
    if debug:
        st.write(os.environ)

    if "INET_USR" in os.environ.keys():
        usr = os.environ['INET_USR']
    else:
        usr = ""
    if "INET_PWD" in os.environ.keys():
        pwd = os.environ['INET_PWD']
    else:
        pwd = ""

    dev_obj.update({'ip': dev.strip()})
    dev_obj.update({'username': usr.strip()})
    dev_obj.update({'password': pwd.strip()})
    dev_obj.update({'secret': pwd.strip()})
    dev_obj.update({'port': 22})
    dev_obj.update({'auth_timeout': auth_timeout})
    # autodetect
    dev_obj.update({'device_type': 'ios_xe'})
    if session_log:
        dev_obj.update({'session_log': 'netmiko_session_log.txt'})

    return dev_obj


def send_netmiko_commands(
    conn, hostnm, cmds, method="command", cfgmode_bool=False
):
    """
    Function to send commands via a netmiko connection
    :param conn: existing netmiko connection passed to function
    :param hostnm: hostname of device used to find the configuration file which should contain the hostname
    :param cmds: if method is "command" this is a list of commands, if method is "from_file" this should be empty
    :param method: "command" if the connections is going to use the command method, "config_set"  if using the file
    method - this option uses the filelist information
    :param find_file_bool:
        True if the function should try to find the corresponding configuration file based on hostname
        False if passing a specific configuration file into filelist
    :param cfgmode_bool:
        True if connection should be in config mode - used for configuring device
        False if connection should NOT be in config mode - used for show commands
    :return: output of the selected netmiko command

    """

    cfgoutput = ""

    if not conn.check_config_mode() and cfgmode_bool:
        conn.config_mode()

    if cfgmode_bool:
        if conn.check_config_mode():
            if method == "command":
                for cmd in cmds:
                    cfgoutput += conn.send_command(
                        cmd, strip_prompt=False, strip_command=False
                    )
            elif method == "config_set":
                cfgoutput = conn.send_config_set(cmds)
                st.text(cfgoutput)


    else:
        # Great for show commands
        if method == "command":
            for cmd in cmds:
                cfgoutput += conn.send_command(
                    cmd, strip_prompt=False, strip_command=False
                )

    return cfgoutput


#
# def try_sq_rest_call(uri_path, url_options, API_ENDPOINT="10.1.10.47", debug=False):
#     """
#     SuzieQ API REST Call
#
#     """
#
#     API_ACCESS_TOKEN = os.getenv("SQ_API_TOKEN")
#     # UWACO Lab  API_ENDPOINT = "10.1.10.22"
#
#     url = f"https://{API_ENDPOINT}:8000{uri_path}?{url_options}&verify=False"
#     # UWACO LAB
#     # url = f"http://{API_ENDPOINT}:8000{uri_path}?{url_options}&verify=False"
#     # url = f"https://{API_ENDPOINT}:8443{uri_path}?{url_options}"
#     payload = "\r\n"
#     headers = {
#         "Content-Type": "text/plain",
#         "Authorization": f"Bearer {API_ACCESS_TOKEN}",
#     }
#
#     if debug:
#         st.write(url)
#
#     # Send API request, return as JSON
#     response = dict()
#     try:
#         # response = requests.get(url).json()
#         # st.write(url)
#         response = requests.get(url, headers=headers, data=payload, verify=False)
#
#     except Exception as e:
#         print(e)
#         st.error(
#             "Connection to SuzieQ REST API Failed.  Please confirm the REST API is running!"
#         )
#         st.text(e)
#         # st.stop()
#         response = False
#
#     if debug:
#         st.write(f"Response is {response}")
#         if response.json():
#             st.write(response.json())
#         else:
#             st.write("No data returned for REST call")
#
#     # Returns full response object
#     return response
#


def main():
    pass


# Standard call to the main() function.
if __name__ == "__main__":
    main()
