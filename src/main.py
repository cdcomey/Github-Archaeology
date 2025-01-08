import subprocess
import datetime

def find_commit_hashes():
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout.split('\n')
    hashes = [r[:r.find(' ')] for r in result if ' ' in r]
    return hashes

def find_file_extension(line):
    line = line[line.find('diff --git a/') + len('diff --git a/'):]
    first_file, last_file = line.split(' b/')

    dot_index_a = first_file.rfind('.')
    dot_index_b = last_file.rfind('.')
    assert first_file[dot_index_a:] == last_file[dot_index_b:]

    return first_file[dot_index_a:]

def parse_timestamp(date_str):
    date = datetime.datetime.strptime(date_str[:-6], '%a %b %d %H:%M:%S %Y')

    offset_str = date_str[-5:]
    offset_hours = int(offset_str[:3])
    offset_minutes = int(offset_str[0] + offset_str[3:])  # Preserve the sign for minutes
    offset = datetime.timedelta(hours=offset_hours, minutes=offset_minutes)
    dt_with_offset = date.replace(tzinfo=datetime.timezone(offset))

    return dt_with_offset
    
def analyze_commit(commit_hash):
    commit_timestamp = {}
    result = subprocess.run(['git', 'show', commit_hash], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout
    # print(result)
    date = ''
    file_extension = ''
    lines_added = 0
    for line in result.split('\n'):
        if line.startswith('Date:   '):
            date_str = line[len('Date:   '):]
            date = parse_timestamp(date_str)

        elif line.startswith('diff --git a/'):
            if file_extension in commit_timestamp:
                commit_timestamp[file_extension] += lines_added
            else:
                commit_timestamp[file_extension] = lines_added
            
            file_extension = find_file_extension(line)
            lines_added = 0

        elif line.startswith('+'):
            lines_added += 1
        elif line.startswith('-'):
            lines_added -= 1
    
    del commit_timestamp['']
    return date, commit_timestamp

def add_timestamp_to_histories(language_histories, commit_timestamp):
    pass

def main():
    language_histories = []

    hashes = find_commit_hashes()
    date, commit_info = analyze_commit(hashes[1000])
    print(date)
    print(commit_info)
    
if __name__ == '__main__':
    main()

# list of dicts
# 	key = lang name
# 	val = sorted dict
# 		keys = times
# 		vals = num lines