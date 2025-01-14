import subprocess
import datetime
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt
import json

def find_commit_hashes(repo_dir):
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, cwd=repo_dir, text=True)
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

def find_file_length(hash, file, repo_dir):
    result = subprocess.run(['git', 'show', f'{hash}:{file}'], capture_output=True, cwd=repo_dir, text=True)
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
def analyze_commit(commit_hash, repo_dir):
    print('showing', commit_hash)

    # get the commit text
    result = subprocess.run(['git', 'show', '--no-merges', commit_hash], capture_output=True, cwd=repo_dir)
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
                old_file_length = find_file_length(commit_hash, file2, repo_dir)
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

def save_dict_to_file(language_histories, dict_dir):
    formatted_language_histories = {}
    for lang, v in language_histories.items():
        formatted_language_histories[lang] = {str(time):line_counts for (time, line_counts) in zip(v.keys(), v.values())}
    with open(dict_dir, 'w') as file:
        json.dump(formatted_language_histories, file, indent=4)
    

def import_json_as_dict(dict_dir):
    language_histories = {}
    with open(dict_dir, 'r') as file:
        formatted_language_histories = json.load(file)
    for lang, v in formatted_language_histories.items():
        language_histories[lang] = SortedDict({datetime.datetime.fromisoformat(time):line_counts for (time, line_counts) in zip(v.keys(), v.values())})
    return language_histories

def data_grapher(language_histories):
    threshold = 100
    for lang in language_histories.keys():
        dates = language_histories[lang].keys()
        line_counts = language_histories[lang].values()
        counter = 0
        total_line_counts = []
        for d in dates:
            counter += language_histories[lang][d]
            total_line_counts.append(counter)

        if total_line_counts[-1] >= threshold:
            plt.plot(dates, total_line_counts, label=lang)
            plt.text(dates[-1], total_line_counts[-1], '{}: {}'.format(lang, total_line_counts[-1]))
            print('graphing', lang)

    # plt.legend()
    plt.show()
            

def main():
    language_histories = {}
    repo_dir_partial = 'godot'
    repo_dir = '../data/' + repo_dir_partial
    json_filename = '../data/dicts/' + repo_dir_partial + '.json'

    # list is reversed to place in chronological order
    hashes = find_commit_hashes(repo_dir)
    hashes.reverse()
    for hash in hashes[:100]:
        date, commit_info = analyze_commit(hash, repo_dir)
        language_histories = add_timestamp_to_histories(language_histories, date, commit_info)
    print_language_histories(language_histories)
    data_grapher(language_histories)

    save_dict_to_file(language_histories, json_filename)
    # language_histories = import_json_as_dict(json_filename)
    # print_language_histories(language_histories)
    # data_grapher(language_histories)

if __name__ == '__main__':
    main()