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
- v2 (20231214): Add explict license checkout
- v3 (20231223): Add loop structure for dependent job
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
import math

import rescale_rest_api as rescale

def generate_batch_and_job_names(commands):
    # Split the commands_text into lines
    commands_lines = [line.strip() for line in commands.strip().split('\n')]

    # Create batch_names and job_names arrays based on the number of lines in commands
    batch_names = [f'job{i + 1}' for i in range(len(commands_lines))]

    current_user = getpass.getuser()
    job_names = [f"{current_user}@{batch_name}@{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}" for batch_name in batch_names]

    job_id = [None] * len(commands_lines)

    return commands_lines, batch_names, job_names, job_id

if __name__ == "__main__":

     # User Define section
     commands='''
abaqus job=s4b cpus=$RESCALE_CORES_PER_SLOT scratch=$PWD/tmp interactive
abaqus job=s4b cpus=$RESCALE_CORES_PER_SLOT scratch=$PWD/tmp interactive
'''
     # End of User Define section

     # 0. Predefined section by admin
     code_name = 'abaqus'
     version_code = '2022-2241'
     license_info = { 'LM_LICENSE_FILE': '27003@mgmt0' }
     coretype_code='starlite_max' 
     core_per_slot= 1
     feature_name='abaqus' # it is essential for explicit license checkout, if you do not want to please set as ''
     def feature_count_cal(n): # calculate abaqus feature
         result = 5 * n ** 0.422
         result_rounded = math.ceil(result)
         return int(result_rounded)
     feature_count=feature_count_cal(core_per_slot) # it is essential for explicit license checkout, if you do not want to please set as ''
     slot = '1'
     walltime=2
     projectid= 'xDdRk' # KR solutions

     print(f"code_name = {code_name}")
     print(f"version_code = {version_code}")
     print(f"license_info = {license_info}")
     print(f"coretype_code = {coretype_code}")
     print(f"core_per_slot = {core_per_slot}")
     print(f"feature_name = {feature_name}")
     print(f"feature_count = {feature_count}")
     print(f"slot = {slot}")
     print(f"walltime = {walltime}")
     print(f"projectid = {projectid}")

     # 0. End of Prefined section by admin

     # Varialbes for Rescale Job submission
     rescale_platform=None # or 'https://kr.rescale.com'
     my_token=None # or 'Token '+'Rescale API key'

     # 1. Rescale platform and API token
     rescale_platform, my_token = rescale.platform_my_token(rescale_platform, my_token)

     # 2. Compress input files as rescale.tar.gz for designated path (Default path is current python execut
     rescale.create_tar_gz()

     # Generate_batch_and_job_names
     commands_lines, batch_names, job_names, job_id = generate_batch_and_job_names(commands) 

     # Iterate through jobs
     for i, (batch_name, command, job_name) in enumerate(zip(batch_names, commands_lines, job_names)):

         now = datetime.datetime.now()  # Declare now for each job

         if i == 0:
             # 3. Upload input file to Rescale files (AWS S3) only for the first job
             inputfiles_list = rescale.upload_local_files(rescale_platform, my_token)

             # 4. Rescale Job Configuration
             job_id[i] = rescale.job_setup(rescale_platform, my_token, job_name, command, feature_name, feature_count, code_name, version_code, license_info, coretype_code, core_per_slot, slot, walltime, projectid, inputfiles_list)

             # 5. Rescale Job Submit
             rescale.job_submit(rescale_platform, my_token, job_name, job_id[i])

             # 6. Rescale Job Monitor
             rescale.job_monitor(rescale_platform, my_token, job_id[i])

         if i > 0:
             # 3.1 Get the ID of the input file in Rescale files (AWS S3) from the previous Rescale Job
             inputfiles_list = rescale.file_previous_job(rescale_platform, my_token, job_id[i-1])

             # 4.1 Rescale Job Configuration
             job_id[i] = rescale.job_setup(rescale_platform, my_token, job_name, command, feature_name, feature_count, code_name, version_code, license_info, coretype_code, core_per_slot, slot, walltime, projectid, inputfiles_list)

             # 5.1 Rescale Job Submit
             rescale.job_submit(rescale_platform, my_token, job_name, job_id[i])

             # 6.1 Rescale Job Monitor
             rescale.job_monitor(rescale_platform, my_token, job_id[i])

             if i == len(batch_names) - 1:
                 # 7. Rescale Job Download
                 rescale.job_download(rescale_platform, my_token, job_name, job_id[i])
