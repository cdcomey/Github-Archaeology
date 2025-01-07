import subprocess

def find_commit_hashes():
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, cwd='../data/godot', text=True)
    result = result.stdout.split('\n')
    # print(result)
    hashes = [r[:r.find(' ')] for r in result if ' ' in r]
    return hashes

def main():
    hashes = find_commit_hashes()
    for h in hashes:
        print(h)

if __name__ == '__main__':
    main()