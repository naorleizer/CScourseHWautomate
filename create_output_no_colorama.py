from multiprocessing.spawn import freeze_support
import os
import sys
from multiprocessing import Process
# import colorama
import subprocess
import pathlib
import re

"""
The goal of this program is to automate the creating and comparing (specifically using diffmerge program)
of Computer Science introdction courses assignamnts input and output files.
The program take as input a sample input file and the python program to run the input files with.
The program searches for additional input files (currently hardcoded pattern - q<num>in<itertable_num>.txt)
in the input file directory, and then serving all of the founded files through the given python file, saving the output
to a directory "output" in the same folder of the python file (creates one if doesn't exist)
Afterwards the program perform a (very) basic analysis of the given-output files (searches for them in the same directory of the
given-input files) and the created output files and indicates if a difference exists.
The program also launches Diffmerge with the given-output files and the generated output files to allow manual comparison.
"""

PYTHON_LOCATION = pathlib.Path("C:\Program Files\Python310\python.exe")
PYTHON_SHORTCUT = "py"
DIFFMERGE_FLAG = True   # changes to False with --no-diffmerge argument

# diffmerge location - currently hardcoded, should probably search in some windows-given program files directory...
DIFFMERGE_LOCATION = pathlib.Path(
    "C:\Program Files\SourceGear\Common\DiffMerge\sgdm.exe"
).resolve()

def diff_the_merge(diff_loc, source_file, test_file):
    # subprocess.run(f'"{diff_loc.resolve()}" "{source_file.resolve()}" "{test_file.resolve()}"')
    os.execv(
        diff_loc.resolve(),
        [
            f'"{source_file.resolve()}"',   # not sure why, but the first argutment is needed twice -_-
            f'"{source_file.resolve()}"',
            f'"{test_file.resolve()}"',
        ],
    )


def input_file_handling(input_file, ending):
    """handling of argv files input; promt to exit or continue if issue occours"""
    input_file = pathlib.Path(input_file).resolve()
    (
        print(
            # f"File {input_file.name} does not exists"
            f"File {input_file.name} does not exists"
        )
        & exit()
        if input_file.exists() == False
        else ()
    )
    if input_file.suffix != ending:
        (exit(1)) if (
            input(
                f"Unexpected file suffix found: {input_file.name}{os.linesep}\
Would like to continue execution? (type n/no to stop) "
            ).lower()
            in ["n", "no"]
        ) else ()
    return input_file


def sort_by_num(file):
    # print(file)
    try:
        return int(re.findall("^q\d[inout]+(\d+)", file.name)[0])
    except IndexError:
        return 0


def main():

    # ensure proper usage
    if len(sys.argv) not in [3,4]:
        print(
            f"Insufficient Arguments{os.linesep}Usage: {sys.argv[0]} input_file.txt python_file.py"
        )
        exit(1)

    # ensure provided files are expected and convert path to pathlib type
    pyfile = input_file_handling(sys.argv[2], ".py")
    infile = input_file_handling(sys.argv[1], ".txt")

    if len(sys.argv) == 4:
        DIFFMERGE_FLAG = False if sys.argv[3] == "--no-diffmerge" else True


    # find input files parent directory to parse for additional files later
    infile_directory = ""
    if infile.is_dir():
        infile_directory = infile
    else:
        infile_directory = infile.parent
    if infile_directory.is_dir is False:
        print(f"issue with input file\\directory: {sys.argv[2]}")
    else:
        print(f"Searching for files at: {infile_directory}")

    # create a list of given input and output files
    in_file_list = list()
    out_file_list = list()
    # directory_file_list = [x for x in infile_directory.iterdir() if x.is_file()]
    # for file in directory_file_list:
    for file in  [x for x in infile_directory.iterdir() if x.is_file()]:
        # print(file) # debugging
        if file.name[:4] == infile.name[:4]:
            in_file_list.append(infile_directory.joinpath(file))
        if file.name[1] == infile.name[1] and file.name.find("out") > 0:
            out_file_list.append(infile_directory.joinpath(file))
    in_file_list.sort(key=sort_by_num)
    out_file_list.sort(key=sort_by_num)
    # ensure same amount of input and output files
    if len(in_file_list) != len(out_file_list):
        print(
            f"Differet amount of input ({len(in_file_list)}) and output ({len(out_file_list)}) files, please fix the issue{os.linesep}Input files:{os.linesep}{' ,'.join([x.name for x in in_file_list])}{os.linesep}Output files:{os.linesep}{' ,'.join([x.name for x in out_file_list])}"
        )
        exit()

    # check for output directory existance and create one if doesn't exists
    if pathlib.Path.exists(pyfile.parent.joinpath("output")) is False:
        print(f'Creating output files directory: {pyfile.parent.joinpath("output")}')
        pyfile.parent.joinpath("output").mkdir()
    else:
        print(f'Saving output files in {pyfile.parent.joinpath("output")}')

    # start of running the given python files and creating the output files
    problem_file_list = []      # un-identical output and generated-output files are saved in this list
    for output_num, cur_in_file in enumerate(in_file_list):
        # create generated-output file full path as q<same_as_input_file>out<same_as_input_file>_test.txt
        out_file = pyfile.parent.joinpath(
            "output", f"q{infile.name[1]}out{output_num+1}_test.txt"
        )
        # create the command to run in CMD without all of the arguments - "full_path_python_file" < "full_path_input_file" > "full_path_generated_output_file"
        command = f'{PYTHON_SHORTCUT} "{pyfile.absolute()}" < "{cur_in_file.absolute()}" > "{out_file.absolute()}"'
        # command = f'Get-Content "{cur_in_file}" | python {pyfile.name} >"{out_file}"' # powershell syntax, currently running in CMD though so commented out
        return_code = subprocess.Popen(command, shell="CMD", stdout=subprocess.PIPE)    # using subprocess to run the command
        returned = return_code.communicate()    # save return code from CMD
        # stop and exit if CMD ran into issues
        print(
            f"Issues with python execution!{os.linesep}{returned}"
        ) & exit() if return_code.returncode != 0 else ()

        # execute diffmerge as seperate process so the program will keep running without need to close diffmerge (seperate process)
        if DIFFMERGE_FLAG:
            Process(
                target=diff_the_merge,
                args=(DIFFMERGE_LOCATION, out_file_list[output_num], out_file),
                daemon=False,
            ).start()

        # very-very-very basic and stupid line-by-line file comparison - SHOULD NOT BE TRUSTED!!!
        given_sample = open(out_file_list[output_num], "r")
        given_sample_lines = given_sample.readlines()
        given_sample.close()
        output_sample = open(out_file, "r")
        output_sample_lines = output_sample.readlines()
        output_sample.close()
        current_file_all_clear = True    # False if differnces were found in current file
        # for loop to run over every line - if difference in lines amount - run the smaller amount
        if len(given_sample_lines) != len(output_sample_lines):
            current_file_all_clear = False
        for a, b, line_num in zip(
            given_sample_lines,
            output_sample_lines,
            range(max(len(given_sample_lines), len(output_sample_lines)))
        ):
            parse1 = ""
            parse2 = ""
            # go over the letters one by one, if different, start printing them RED
            for c1, c2 in zip(a, b):
                if c1 == c2:
                    parse1 += c1
                    parse2 += c2
                else:
                    parse1 += c1 
                    parse2 += c2 
                    zero_issues = False
                    current_file_all_clear = False
        if current_file_all_clear:
            print(
                f"👍 -All good with test {output_num+1}:{cur_in_file.name} ✔"
            )
        else:
            print(
                f"❌ - issue with file {output_num+1}: {cur_in_file.name}, difference in lines {line_num}{os.linesep}\
    \t{parse1}\t{parse2}"
            )
            problem_file_list.append(cur_in_file.name)

    print(
        f"❌ - Issues found with {', '.join(problem_file_list)} ❌"
    ) if problem_file_list else ()
    print("Finished")


if __name__ == "__main__":
    freeze_support()    # needed for Process library
    main()
