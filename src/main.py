import subprocess
import datetime
from sortedcontainers import SortedDict

def find_commit_hashes():
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout.split('\n')
    hashes = [r[:r.find(' ')] for r in result if ' ' in r]
    return hashes

def parse_file_names(line):
    b_loc = line.find(' b/')
    file1 = line[line.find('a/')+2:b_loc]
    file_extension1 = file1[file1.rfind('.'):]

    file2 = line[b_loc+3:]
    file_extension2 = file2[file2.rfind('.'):]

    return file1, file_extension1, file2, file_extension2

def parse_timestamp(date_str):
    date = datetime.datetime.strptime(date_str[:-6], '%a %b %d %H:%M:%S %Y')

    offset_str = date_str[-5:]
    offset_hours = int(offset_str[:3])
    offset_minutes = int(offset_str[0] + offset_str[3:])  # Preserve the sign for minutes
    offset = datetime.timedelta(hours=offset_hours, minutes=offset_minutes)
    dt_with_offset = date.replace(tzinfo=datetime.timezone(offset))

    return dt_with_offset

def find_file_length(hash, file):
    result = subprocess.run(['git', 'show', f'{hash}:{file}'], capture_output=True, cwd='../data/godot', text=True)
    if result.returncode == 0:
        return len(result.stdout.splitlines())
    else:
        raise ValueError(f'Failed to retrieve file content for {file} at {hash}')

def add_to_dict(dict, key, val):
    if key in dict:
        dict[key] += val
    else:
        dict[key] = val

# parse the diff text of a commit and return the line count changes for each file type
def analyze_commit(commit_hash):
    print('showing', commit_hash)

    # get the commit text
    result = subprocess.run(['git', 'show', '--no-merges', commit_hash], capture_output=True, cwd='../data/godot')
    result = result.stdout.decode('utf-8', errors='ignore')

    date = ''
    file_extension = ''
    lines_added = 0
    commit_info = {}
    for line in result.split('\n'):
        # parse date string and store as datetime
        if line.startswith('Date:   '):
            date_str = line[len('Date:   '):]
            date = parse_timestamp(date_str)
        
        # determine file type
        elif line.startswith('diff --git a/'):
            file1, file_extension1, file2, file_extension2 = parse_file_names(line)
            if file_extension1 != file_extension2:
                old_file_length = find_file_length(commit_hash, file2)
                add_to_dict(commit_info, file_extension1, -1*old_file_length)
                add_to_dict(commit_info, file_extension2, old_file_length)
            
            file_extension = file_extension2
            add_to_dict(commit_info, file_extension, lines_added)
            lines_added = 0

        # count when lines are added or deleted
        elif line.startswith('+'):
            lines_added += 1
        elif line.startswith('-'):
            lines_added -= 1
    
    if '' in commit_info.keys():
        del commit_info['']
    return date, commit_info
        
def add_timestamp_to_histories(language_histories, commit_timestamp, commit_info):
    for lang in commit_info.keys():
        if lang in language_histories.keys():
            language_histories[lang][commit_timestamp] = commit_info[lang]
        else:
            language_histories[lang] = SortedDict({commit_timestamp: commit_info[lang]})
    
    return language_histories

def print_language_histories(language_histories):
    for lang in language_histories.keys():
        print(lang)
        running_total = 0
        for timestamp in language_histories[lang].keys():
            print('\t', timestamp)

            lines_added_at_timestamp = language_histories[lang][timestamp]
            print('\t', lines_added_at_timestamp, 'lines added')

            running_total += lines_added_at_timestamp
            print('\t', running_total, 'lines so far')
            

def main():
    language_histories = {}

    # list is reversed to place in chronological order
    hashes = find_commit_hashes()
    hashes.reverse()
    for hash in hashes:
        date, commit_info = analyze_commit(hash)
        language_histories = add_timestamp_to_histories(language_histories, date, commit_info)
    print_language_histories(language_histories)

if __name__ == '__main__':
    main()