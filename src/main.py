import subprocess

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
    
def analyze_commit(commit_hash):
    commit_timestamp = {}
    result = subprocess.run(['git', 'show', commit_hash], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout
    # print(result)
    file_extension = ''
    lines_added = 0
    for line in result.split('\n'):
        if line.startswith('diff --git a/'):
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
    return commit_timestamp

def main():
    language_histories = []

    hashes = find_commit_hashes()
    # print(hashes[1000])
    l = analyze_commit(hashes[1000])
    print(l)
    # for h in hashes:
    #     print(h)

if __name__ == '__main__':
    main()