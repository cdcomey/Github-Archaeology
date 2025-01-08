import subprocess

def find_commit_hashes():
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout.split('\n')
    # print(result)
    hashes = [r[:r.find(' ')] for r in result if ' ' in r]
    return hashes
    
def analyze_commit(commit_hash):
    result = subprocess.run(['git', 'show', commit_hash], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout
    lines_added = 0
    for line in result.split('\n'):
        if line.startswith('+'):
            lines_added += 1
        elif line.startswith('-'):
            lines_added -= 1
    
    return lines_added

def main():
    hashes = find_commit_hashes()
    print(hashes[0])
    l = analyze_commit(hashes[1000])
    print(l)
    # for h in hashes:
    #     print(h)

if __name__ == '__main__':
    main()