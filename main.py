#!/usr/bin/env python

'''
[Notice]
This script is a guideline code written to make it easier to use Rescale REST-API.
This code does not represent Rescale's official opinion and does not guarantee any level of service level when user using in the Rescale Web platform.
Rescale is not obligated to provide any technical support for the code under the basic contract. (including global technical support)
All responsibility for the use of this code lies with the end user, and Rescale assumes no responsibility or liability whatsoever.
You can suggest improvements to the code through the community base, but this does not guarantee improvement or commit development.
The purpose of this code is to serve as an example of the Rescale REST-API automation guidelines, and does not imply that the script should be maintained or improved upon.

Script Name: Rescale REST-API script
Author: Seungkyu Hong
Email: shong@rescale.com
Date: Dec 04, 2023
Versions:
- v1 (20231204): Initial version-controlled implementation
'''

import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

import json
import sys
import time
import os
import datetime
import getpass
import json

import rescale_rest_api as rescale

if __name__ == "__main__":
     # User Define section
     batch_name1='job1'
     batch_name2='job2'
     batch_name3='job3'
     batch_name4='job4'

     command1="abaqus job=s4b cpus=$RESCALE_CORES_PER_SLOT scratch=$PWD/tmp interactive \n"
     command2="abaqus job=s4b cpus=$RESCALE_CORES_PER_SLOT scratch=$PWD/tmp interactive \n"
     # End of User Define section

     # 0. Predefined section by admin
     now = datetime.datetime.now()
     current_user = getpass.getuser()

     job_name1 = current_user+'@'+batch_name1+'@'+now.strftime('%Y%m%d-%H%M%S')
     job_name2 = current_user+'@'+batch_name2+'@'+now.strftime('%Y%m%d-%H%M%S')
    #job_name3 = current_user+'@'+batch_name3+'@'+now.strftime('%Y%m%d-%H%M%S')
    #job_name4 = current_user+'@'+batch_name4+'@'+now.strftime('%Y%m%d-%H%M%S')
     code_name = 'abaqus'
     version_code = '2022-2241'
     license_info = { 'LM_LICENSE_FILE': '27003@mgmt0' }
     coretype_code='starlite_max' 
     core_per_slot= 1
     slot = '1'
     walltime=2
     projectid= 'xDdRk' # KR solutions

     print(f"job_name1 = {job_name1}")
     print(f"job_name2 = {job_name2}")
     print(f"code_name = {code_name}")
     print(f"version_code = {version_code}")
     print(f"license_info = {license_info}")
     print(f"coretype_code = {coretype_code}")
     print(f"core_per_slot = {core_per_slot}")
     print(f"slot = {slot}")
     print(f"walltime = {walltime}")
     print(f"projectid = {projectid}")

     # 0. End of Prefined section by admin

     # Varialbes for Rescale Job submission
     rescale_platform=None # or 'https://kr.rescale.com'
     my_token=None # or 'Token '+'Rescale API key'
     inputfiles_list = [] # Rescale input fiiles ID list, default: rescale.tar.gz

     # 1. Rescale platform and API token
     rescale_platform, my_token = rescale.platform_my_token(rescale_platform, my_token)

     # 2. Compress input files as rescale.tar.gz for designated path (Default path is current python execut
     rescale.create_tar_gz()

     # 3. Upload input file to Rescale files (AWS S3). Get the ID of input file in Rescale files
     inputfiles_list1 = rescale.upload_local_files(rescale_platform, my_token)

     # 4. Rescale Job Configuration
     job_id1 = rescale.job_setup(rescale_platform, my_token, job_name1, command1, code_name, version_code, license_info, coretype_code, core_per_slot, slot, walltime, projectid, inputfiles_list1)

     # 5. Rescale Job Submit
     rescale.job_submit(rescale_platform, my_token, job_name1, job_id1)

     # 6. Rescale Job Moinitor
     rescale.job_monitor(rescale_platform, my_token, job_id1)

     # iterate as you want from 3.1 to 6.1 for dependent job
     # 3.1 Get the ID of input file in Rescale files (AWS S3) from Previous Rescale Job
     inputfiles_list2 = rescale.file_previous_job(rescale_platform, my_token, job_id1)
     # 4.1 Rescale Job Configuration
     job_id2 = rescale.job_setup(rescale_platform, my_token, job_name2, command2, code_name, version_code, license_info, coretype_code, core_per_slot, slot, walltime, projectid, inputfiles_list2)
     # 5.1 Rescale Job Submit
     rescale.job_submit(rescale_platform, my_token, job_name2, job_id2)
     # 6.1 Rescale Job Moinitor
     rescale.job_monitor(rescale_platform, my_token, job_id2)

     # 7. Rescale Job Download
     rescale.job_download(rescale_platform, my_token, job_name2, job_id2)

