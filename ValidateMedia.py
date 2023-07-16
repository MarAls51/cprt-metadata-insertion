import subprocess
import re
import ExtractMedia 
import MediaTransfer
import time
import argparse
import ErrorHandling
import os
import Database

video_media = "video"
audio_media = "audio"
uuid_db = "uuid"

# extract uuid -> extracts the uuid, self explanatory. Looks into the given file and attempts to find the uuid inside the mp4dump value = 
# Args:
#  dash obj, dash dictionary containing all information associated with the extracted prased mpd file
# quality id, the video or audio quality id
# media type, either audio or video, whatever we are looking for.
def extract_uuid(dash_obj, quality_id, media_type):
    print('''--------------- Extracting uuid ---------------------
    ''')
    if(media_type == "video"):
        init_template = dash_obj["init_template_video"].replace('$RepresentationID$', str(quality_id))
    else:  
        init_template = dash_obj["init_template_audio"].replace('$RepresentationID$', str(quality_id))

    dump_mp4 = f"mp4dump {init_template}"

    result = subprocess.run(dump_mp4, shell=True, capture_output=True, text=True)
    output = result.stdout

    match = re.findall(r'value = (\S+)', output) 

    for extracted_value in match:
         if(len(extracted_value) == 36):
            print("UUID Successfully extracted, UUID:", extracted_value)
            return extracted_value
    print("No UUID has been found")
    return None

# validate uuid -> validates a given uuid, accepts uuid to validate as an optional argument otherwise it just looks inside the db.json file
# Args:
# extracted_value, its the value extracted from the init.
# uuid_to_validate, optional argument that is the uuid, not necessary
def validate_uuid(extracted_value, uuid_to_validate):
    
    print('''--------------- Validating uuid ---------------------
    ''')

    uuid_reference = None
    if(uuid_to_validate):
        uuid_reference = uuid_to_validate
    else:
        uuid_reference = Database.extract_db_values(uuid_db) 

    if(extracted_value in uuid_reference):
        print("UUID Successfully validated, UUID:", extracted_value)
        subprocess.run(f'echo "{extracted_value}" > s3.txt', shell=True)
    else:
        print("The UUID has failed to validate.")

parser = argparse.ArgumentParser()
# output -> folder that it outputs to.
# Args:
# o, output
parser.add_argument(
    "-o",
    "--output",
)

# manifest_url -> arugment that accepts a manifest url, necessary to download the segments.
# Args:
# u or manifest_url 
parser.add_argument(
    "-u",
    "--manifest_url",
)
args = parser.parse_args()

# Main for validation
# Args: the cli args as stated in the comments
# Validates a given stream, looks for the uuid inside the init of the first id.
def main():
    
    start_time = time.time()

    dash_obj = {
    'manifest_path' : None, 
    'uuid_value' : None, 
    'root_folder' : None,
    'manifest_root' : None,
    'manifest_output_path' : None,
    'manifest_output_nested_path' : None,
    'bucket_path' : "testbucket-watermarking/validated_signal",
    'video_qualities' : [],
    'audio_qualities' : [],
    'init_template_video' : None,
    'segment_template_video' : None,
    'init_template_audio' : None,
    'segment_template_audio' : None,
    'total_segments' : None }
    
    root = args.output
    url = args.manifest_url

    if(not root or not url):
        ErrorHandling.error_handling_format("Invalid args")

    dash_obj['root_folder'] = f"{root}"
    dash_obj['manifest_output_path'] = f"{root}/output_mpd.txt"


    dash_obj['manifest_path'] = url.rsplit('/', 1)[-1]
    dash_obj['manifest_root'] = url[:url.rindex('/')]

    dash_obj['manifest_output_path'] = f"{root}/{dash_obj['manifest_path']}"

    MediaTransfer.extract_media_into_folder(dash_obj["manifest_root"], dash_obj["manifest_path"], dash_obj["manifest_output_path"], True)
    
    ExtractMedia.parse_mpd(dash_obj) 

    os.chdir(os.path.dirname(dash_obj['manifest_output_nested_path']))
    
    ExtractMedia.extract_media(dash_obj, dash_obj["video_qualities"][0], video_media, True)
    extracted_uuid = extract_uuid(dash_obj, dash_obj["video_qualities"][0], video_media)

    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    if(extracted_uuid != None):
        validate_uuid(extracted_uuid, dash_obj['uuid_value'])
        MediaTransfer.insert_media_into_aws(dash_obj["root_folder"], dash_obj["bucket_path"], extracted_uuid, dash_obj["manifest_path"], dash_obj["manifest_output_nested_path"], True)
    
    end_time = time.time()
    total_time_ms = int((end_time - start_time) * 1000)

    print("Time duration to validate:", total_time_ms," milliseconds")

if __name__ == "__main__":
    main()