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
import platform
import os
import tarfile

# 1. Get platform information
def platform_my_token(rescale_platform,my_token):
    api_key = None
    rescale_platform = None

    # Determine the configuration file path based on the operating system
    if (platform.system() == 'Windows' ):
        apiconfig_file = os.environ['USERPROFILE']+"\\.config\\rescale\\apiconfig"
    else:
        apiconfig_file = os.environ['HOME']+"/.config/rescale/apiconfig"

    try:
        with open(apiconfig_file, 'r') as f:
            lines = f.readlines()

            # Extract API key and platform information from the configuration file
            rescale_platform =lines[1].split('=')[1].rstrip('\n').lstrip().replace("'","")
            api_key =lines[2].split('=')[1].rstrip('\n').lstrip().replace("'","")
    except (IOError, IndexError, KeyError) as e:
        print(f"Error reading apiconfig file: {e}")
        exit(1)

    # Validate API key and platform information
    if api_key is None :
        print("API key should be defined in the $HOME/.config/rescale/apiconfig")
        exit(1)

    if rescale_platform is None :
        print("Platform address should be defined in the $HOME/.config/rescale/apiconfig")
        exit(1)

    my_token = 'Token ' + api_key

    print(f"rescale_platform = {rescale_platform}")
    print(f"my_token = {my_token}")

    return rescale_platform, my_token

# 2. Create input tar file regarding given path
def create_tar_gz(input_path=None, output_filename="rescale.tar.gz") :
    # If no input path is provided, use the current execution directory
    if not input_path:
        input_path = os.getcwd()

    # Get the list of files in the input path
    file_list = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f))]

    # Create a tar.gz file
    with tarfile.open(output_filename, "w:gz") as tar:
        for file in file_list:
            file_path = os.path.join(input_path, file)
            tar.add(file_path, arcname=os.path.basename(file_path))

    print(f"Successfully created rescale.tar.gz in {os.getcwd()}")

    return

# 3. Uploads local files to a specified platform
def upload_local_files(rescale_platform,my_token,input_file="rescale.tar.gz") :

    # Set the upload URL
    upload_url = rescale_platform + '/api/v2/files/contents/'

    # Split input file paths
    input_files = input_file.split()
    inputfile_id = {}
    inputfiles_list = []
    uploaded_files = ''

    # Iterate through each input file
    for i in range(len(input_files)) :
        try:
            # Open the file in binary mode
            with open(input_files[i], 'rb') as ifile:

                encoder = MultipartEncoder(fields={'file': (ifile.name, ifile)})
                monitor = MultipartEncoderMonitor(encoder)

                # Make a request to upload the file
                upload_file = requests.post(
                    upload_url,
                    data=monitor,
                    headers={'Authorization' : my_token,'Content-Type': encoder.content_type})

                # Check if the upload was successful
                if (upload_file.status_code == 201) :
                    print('- ' + input_files[i] + ' uploaded')
                    uploaded_files = uploaded_files + ' ' + os.path.basename(input_files[i])
                    upload_file_dict = json.loads(upload_file.text)
                    inputfile_id[i] = upload_file_dict['id']
                    inputfiles_list.append({'id':inputfile_id[i],'decompress':True})
                else:
                    print('- ' + input_files[i] + ' upload failed')
                    exit(1)

        except FileNotFoundError as e:
            print (e)
            exit(1)

    print("All files uploaded successfully!")
    print(f"inputfiles_list = {inputfiles_list}")
    return inputfiles_list

# 4. Job setup
def job_setup (rescale_platform, my_token, job_name, command, code_name, version_code, license_info, coretype_code, core_per_slot, slot, walltime, projectid, inputfiles_list):
    # remove input rescale.tar.gz and compress all output
    zip_command = 'rm rescale.tar.gz \ntar --exclude=rescale_rest_api.py --exclude=main.py --exclude=process_output.log --exclude=__pycache__ --exclude=tmp -czvf rescale.tar.gz ./* \n'
    # remove all files except ouput rescale.tar.gz
    rm_command = 'find . ! -name "rescale.tar.gz" -type f -exec rm -f "{}" \; \nrm $HOME/work/process_output.log\n sleep 5'
    
    job_command = command + zip_command + rm_command

    # Rescale API for batch job configuration
    job_url = rescale_platform + '/api/v2/jobs/'
    job_setup = requests.post(
        job_url,
        json = {
            'name' : job_name,
            'isLowPriority' : False,
            'projectId' : projectid,
            'jobanalyses' : [
                {
                    'envVars' : license_info,
                    'useRescaleLicense' : False, # For Rescale internal test please switch to True
                   #'onDemandLicenseSeller' : { 
                   #    'code' : 'rescale-trial',
                   #    'name' : 'Rescale Trial'
                   #},
                    'useMPI' : False,
                    'flags' : {
                        'igCv': True
                        },
                    'command' : job_command,
                    'analysis' : {
                        'code' : code_name,
                        'version' : version_code
                    },
                    'hardware' : {
                        'coresPerSlot' : core_per_slot,
                        'slots' : slot,
                        'walltime' : walltime,
                        'coreType' : coretype_code,
                    },
                    'inputFiles' : inputfiles_list
                },
            ] 
        },
        headers={'Content-Type' : 'application/json',
                 'Authorization' : my_token}
    )

    if (job_setup.status_code != 201) :
        print (job_setup.text)
        print ('Job creation failed')
        exit(1)

    job_setup_dict = json.loads(job_setup.text)
    job_id = job_setup_dict['id'].strip()
    print(f"Job_ID: {job_id}")

    return job_id 

# 5. Submit job
def job_submit (rescale_platform, my_token, job_name, job_id):

    # Rescale API for batch job submission
    job_submit_url = rescale_platform + '/api/v2/jobs/' + job_id + '/submit/'
    submit_job = requests.post(
        job_submit_url,
        headers={'Authorization': my_token}
    )
    if (submit_job.status_code == 200) :
        print ('Job ' + job_id + ' : submitted')
        job_info_filename = job_name+".job"
        job_info_file = open(job_info_filename, 'w')
        job_info_file.write(job_id)
        job_info_file.close()

        if (platform.system() == 'Windows' ):
            job_url_filename = job_name+".url"
            job_url_file = open(job_url_filename, 'w')
            url = 'URL='+rescale_platform+'/jobs/'+job_id+'/runs/1/results/'
            url = '[InternetShortcut]\n'+url
        else:
            job_url_filename = job_name+".desktop"
            job_url_file = open(job_url_filename, 'w')
            url = 'URL='+rescale_platform+'/jobs/'+job_id+'/runs/1/results/'
            url = '[Desktop Entry]\nType=Link\n'+url

        job_url_file.write(url)
        job_url_file.close()

    else:
        print ('Job submission Failed')
        exit(1)

    return

# 6. Monitoring job
def job_monitor (rescale_platform, my_token, job_id):

    job_status_url = rescale_platform + '/api/v2/jobs/' + job_id + '/statuses/'

    prev_status = None
    current_status = None
    job_completed = False

    # Tail out file
    tail_out = 'process_output.log'

    while job_completed == False :
        prev_status = current_status
        job_status = requests.get(
            job_status_url,
            headers={'Authorization': my_token}
        )
        job_status_dict = json.loads(job_status.text)
        current_status = job_status_dict['results'][0]['status']

        if (current_status != prev_status) :
            print ('Job ' + job_id + ' : ' + current_status)

            while current_status == 'Executing' :
                # Live tail of tail out file
                tail_file_url = rescale_platform + '/api/v2/jobs/' + job_id + '/runs/1/tail/' + tail_out
                tail_file = requests.get(
                    tail_file_url,
                    headers={'Authorization': my_token},
                    params={'lines':20}
                )

                try :
                    tail_file_dict = json.loads(tail_file.text)
                    print(json.dumps(tail_file_dict['lines'],indent=2))
                except:
                    print('Waiting.....')

                sys.stdout.flush()
                sys.stderr.flush()

                time.sleep(15)

                prev_status = current_status
                job_status = requests.get(
                    job_status_url,
                    headers={'Authorization': my_token}
                )
                job_status_dict = json.loads(job_status.text)
                current_status = job_status_dict['results'][0]['status']

            # End of Live tail

        if current_status == 'Completed':
           job_completed = True

        sys.stdout.flush()
        sys.stderr.flush()

        time.sleep(5)

    if job_completed != True :
        print('Job execution Failed')
        exit(1)

    return

# 7. Download job
def job_download(rescale_platform, my_token, job_name, job_id) :

    list_output_files_url = rescale_platform + '/api/v2/jobs/' + job_id + '/files/'

    current_page = 1
    file_count = 0
    last_page = False
    current_dir = os.getcwd()

    list_output_files = requests.get(
        list_output_files_url,
        headers={'Authorization': my_token}
    )
    list_output_files_dict = json.loads(list_output_files.text)

    total_file_size = 0
    files_count = list_output_files_dict['count']

    print ('Total ' + str(files_count) + ' files will be downloaded')
    if files_count != 0 :

        top_dir = job_name + '/'

        if not(os.path.exists(top_dir)) :
            os.makedirs(top_dir)

        while (not(last_page)):

            list_output_files = requests.get(
                list_output_files_url,
                params = {'page' : current_page},
                headers={'Authorization': my_token}
            )
            list_output_files_dict = json.loads(list_output_files.text)

            for label in list_output_files_dict['results'] :
                path = ''

                os.chdir(current_dir)
                file_count += 1
                total_file_size += label['decryptedSize']
                relative_path = label['relativePath'].rsplit('/',1)[0]

                if relative_path != label['relativePath'] :
                    path = relative_path

                if not os.path.exists(top_dir + path) :
                    os.makedirs(top_dir + path)

                os.chdir(top_dir + path)

                downloadUrl = label['downloadUrl']
                filename = os.path.basename(label['relativePath'])

                response = requests.get(
                    downloadUrl,
                    headers={'Authorization': my_token}
                )

                with open(filename, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=100):
                        fd.write(chunk)
                print (file_count, label['path']+' downloaded')


            current_page += 1
            if (list_output_files_dict['next'] == None):
                last_page = True

    print ('Total ' + str(file_count) + ' files, %.3f MB downloaded'%(total_file_size/1024/1024))

    return

# 8. Get Rescale files from Previous Rescale Job  
def file_previous_job(rescale_platform, my_token, job_id) :

    inputfiles_list = []
    list_output_files_url = rescale_platform + '/api/v2/jobs/' + job_id + '/files/'

    current_page = 1
    file_count = 0
    last_page = False

    list_output_files = requests.get(
        list_output_files_url,
        headers={'Authorization': my_token}
    )
    list_output_files_dict = json.loads(list_output_files.text)

    files_count = list_output_files_dict['count']

    if files_count != 0 :

        while (not(last_page)):

            list_output_files = requests.get(
                list_output_files_url,
                params = {'page' : current_page},
                headers={'Authorization': my_token}
            )
            list_output_files_dict = json.loads(list_output_files.text)

            for label in list_output_files_dict['results'] :
                inputfiles_list.append({'id':label['id'],'decompress':True})
                file_count += 1

            current_page += 1
            if (list_output_files_dict['next'] == None):
                last_page = True

    else:
        print(f'There is no file in previoous Rescale job {job_id}')
        exit(1)

    print(f"inputfiles_list = {inputfiles_list}")
    return inputfiles_list

