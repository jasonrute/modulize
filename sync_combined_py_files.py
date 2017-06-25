import re
import os

# Regex key:
# ' *' means any number of spaces
# '-{5}' means -----
# '.*' means any group of characters ('.' means any character)
# '-*' means any number of consequtive dashes
# '--*' means one dash followed by any number of consequtive dashes
# '$' means the end of the string 
#     (else re.match will only matches the beginning of the string)
# '|' means "or" (i.e. can match on either version)
# all other characters, incuding spaces, are literal
begin = re.compile(' *##-{5} Begin .* -*##$')
begin_parts = re.compile('##-{5} Begin | --*##')
end = re.compile(' *##-{5} End .* -*##$')
end_parts = re.compile(' *##-{5} End | --*##')

def get_file_contents(file_path):
    with open(file_path, 'r') as f:
        file_contents = f.readlines()
        if file_contents and (not file_contents[-1] or file_contents[-1][-1] != '\n'):
            file_contents[-1] = file_contents[-1] + '\n'
    
    return file_contents

def get_code_blocks(combined_file):
    cnt = 0
    while True:
        for line in combined_file:
            cnt += 1
            if begin.match(line):
                indent_spaces, file, _ = begin_parts.split(line)
                indent = len(indent_spaces)
                break
        else:
            return None # end of file, no more code_blocks

        start = cnt
        block = []
        for line in combined_file:
            cnt += 1
            if end.match(line) and end_parts.split(line)[1] == file:
                break
            else:
                block.append(line[indent:]) # contains newlines
        else:
            return None # no End to match the Begin, error

        finish = cnt - 1

        if block and block[-1] == '\n':
            del block[-1]
        
        yield start, finish, indent, file, block

def get_all_blocks(combined_file):
    with open(combined_file, 'r') as f:
        file_blocks = list(get_code_blocks(f))

    return file_blocks

def file_block_synced(file_path, textlines):
    file_contents = get_file_contents(file_path)

    if file_contents != textlines:
        print("file:", file_contents)
        print("block", textlines)
    
    return file_contents == textlines

def update_file(file_path, textlines):
    with open(file_path, 'w') as f:
        f.writelines(textlines)

def update_block_in_combined_file(combined_file, start, end, indent, textlines):
    with open(combined_file, 'r') as f:
        contents = f.readlines()

    indented_textlines = [' '*indent + line for line in textlines]
    contents = contents[:start] + indented_textlines + contents[end:]

    with open(combined_file, 'w') as f:
        f.writelines(contents)

def sync(directory, combined_file):
    combined_modified = os.path.getmtime(combined_file)

    # reverse the order to prevent the start/end values from changing
    for start, end, indent, file, textlines in reversed(get_all_blocks(combined_file)):
        file_path = directory + file
        file_contents = get_file_contents(file_path)
        if file_contents != textlines:
            file_modified = os.path.getmtime(file_path)

            if combined_modified > file_modified:
                update_file(file_path, textlines)
                print("Syncing", file, "to match", combined_file)
            else:
                update_block_in_combined_file(combined_file, start, end, indent, file_contents)
                print("Syncing", combined_file, "to match", file)

if __name__ == '__main__':
    import sys # replace with argparser
    import time
    directory = sys.argv[1]
    combined_file = sys.argv[2]

    print("Running...")

    try:
        while True:
            try:
                time.sleep(.1)
            finally:
                start_time = time.perf_counter()
                sync(directory, combined_file)
                #print(time.perf_counter() - start_time)
    except KeyboardInterrupt:
        print("\nGOOD BYE!")














