#!/usr/bin/env python3


import os
import datetime
import subprocess
import getpass
import sys
import shlex


CWD = None  # Current working directory
HOMEDIR = os.path.expanduser("~")   # Home directory of user

# Very dangerous commands.
CRITICAL_DANGEROUS = [
    'rm -rf /',
    'rm -rf /*',
    'rm -rf ~',
    'rm -rf ~/*',
    'rm -rf .',
    'rm -rf ..',
    'rm -rf *',
    'rm -r /',
    'rm -r /*',
    ':(){:|:&};:',  # Fork bomb
    'mkfs',  # Format filesystem
    'dd if=/dev/zero of=/dev/sda',  # Wipe disk
    'dd if=/dev/random of=/dev/sda',
    '> /dev/sda',  # Overwrite disk
    'mv / /dev/null',
    'chmod -R 777 /',
    'chown -R nobody /',
]

# Common variables used in echo
echo_environment_variables = {
    'HOME': os.environ.get('HOME'),
    'PWD': os.environ.get('PWD'),
    'USER': os.environ.get('USER'),
    'SHELL': os.environ.get('SHELL'),
    'PATH': os.environ.get('PATH'),
    'BASH': os.environ.get('BASH'),
    'HOSTNAME': os.environ.get('HOSTNAME'),
    'LANG': os.environ.get('LANG'),
    'TERM': os.environ.get('TERM'),
    'LOGNAME': os.environ.get('LOGNAME'),
    'UID': os.environ.get('UID'),
    'MAIL': os.environ.get('MAIL'),
    'HOSTTYPE': os.environ.get('HOSTTYPE'),
    'OSTYPE': os.environ.get('OSTYPE'),
}

# Python dict for storing exports
export_Entries = {}

# Python dict for storing aliases
alias_Entries = {}

# Saving Logs
PSH_HISTORY_FILENAME = ".psh_history.txt"
base_num_filename = 0  # we start with ".psh_history.txt" filename and then after reaching 500 lines, we make a new file names ".psh_history_0.txt" and then so on.

def psh_history(log):
    global PSH_HISTORY_FILENAME
    global base_num_filename

    if not log:
        return

    try:
        # Reading the history file to check the number of lines
        with open(PSH_HISTORY_FILENAME, 'r') as f:
            history_content = f.readlines()
    
    except FileNotFoundError:
        history_content = []       

    while len(history_content) > 500:       # if file has over 500 lines
        base_num_filename += 1      
        PSH_HISTORY_FILENAME = f".psh_history_{base_num_filename}.txt" 
        try:
            with open(PSH_HISTORY_FILENAME, 'r') as f:
                history_content = f.readlines()
        except FileNotFoundError:
            history_content = []

    logtext = f"{log.strip()}\n"        
    try:
        # Writes the log in history file
        with open(PSH_HISTORY_FILENAME, 'a', encoding='utf-8') as f:
            f.write(str(logtext))       
    except Exception as e:
        print(f"[Error]: {e}")

def alias(text):
    global alias_Entries
    if not text:
        return
    
    # Syntax Handling
    if '=' not in text:
        print("Invalid Syntax!! Use: alias name=command")
        return

    try:
        text = text.replace('alias', '', 1).strip() # Sanatizing the text
        alias_name, alias_cmd = text.split('=', 1)  # Spliting the '=' from the text
        alias_name = alias_name.strip()
        alias_cmd = alias_cmd.strip().strip('"').strip("'")

        if not alias_name:
            print("Alias name cannot be empty")
            return

        alias_Entries[alias_name] = alias_cmd   # Writing the alias in the dict.
        print(f"Alias '{alias_name}' created")
    except Exception as e:
        print(f"[Error]: {e}")

def unalias(text):
    global alias_Entries
    if not text:
        return

    try:
        alias_name = text.replace('unalias', '').strip()    
        if alias_name in alias_Entries.keys():
            del alias_Entries[alias_name]       # removes the alias from the the dict.
            print(f"{alias_name} removed.") 
        else:
            print(f"{alias_name} is not defined.")
    except Exception as e:
        print(f"[Error]: {e}")

def showEcho(text):
    global export_Entries
    if not text:
        return

    text = text.replace('echo', '', 1).strip() # Sanatizing the thext
    
    import re
    var_pattern = r'\$([A-Za-z_][A-Za-z0-9_]*)'     # Variable pattern

    def replace_var(match):
        var_name = match.group(1)
        if var_name in export_Entries:
            return str(export_Entries[var_name])
        
        elif var_name in echo_environment_variables:
            val = echo_environment_variables[var_name]
            return str(val) if val else ""
        
        else:
            return match.group(0)

    result = re.sub(var_pattern, replace_var, text)
    print(result)

def export(text):
    global export_Entries
    if not text:
        return

    text = text.replace('export', '', 1).strip()

    if text.lower() == 'list':          # If prompt is 'export list'
        for key, value in export_Entries.items():
            print(f"{key}: {value}")        # Prints all the exports with their values
        return

    # Syntax Handling
    if '=' not in text: 
        print("Invalid Syntax!! Use: export VAR=value")
        return

    # Example: MY_VAR='Hello World'
    try:
        var_name, var_value = text.split('=', 1)
        var_name = var_name.strip()
        var_value = var_value.strip().strip('"').strip("'")

        if not var_name:
            print("Variable name cannot be empty")
            return

        export_Entries[var_name] = var_value        # Writing the variable to the dict
        os.environ[var_name] = var_value
        print(f"Exported {var_name} with value: {var_value}")

    except Exception as e:
        print(f"[Error]: {e}")

def setCmd(text):
    if not text:
        return

    # Syntax Handling
    parts = text.split('=')
    if len(parts) != 2 or parts[0].strip() != parts[0] or parts[1].strip() != parts[1]:
        print("Invalid Syntax!!")
        return
    
    try:
        var_name, var_value = text.split('=')
        var_name = var_name.replace('set', '').strip()
        locals()[var_name] = var_value  # Saving as a local variable
        print(f"Local variable {var_name} set to {var_value}")
    except Exception as e:
        print(f"[Error]: {e}")

def unset(text):
    global export_Entries
    if not text:
        return
    
    try:
        var_name = text.replace('unset', '').strip()
        if var_name in export_Entries.keys():
            del export_Entries[var_name]        # removes the set
            os.environ.pop(var_name, None)
            print(f"{var_name} removed.")
        else:
            print(f"{var_name} is not defined.")
    except Exception as e:
        print(f"[Error]: {e}")

def getPWD():       # Get print working directory
    pwd = f"PWD: {os.getcwd()}"
    print(pwd)
    
def changeDir(cmd):
    global CWD
    if not cmd:
        return

    try:
        parts = cmd.split(maxsplit=1)

        if len(parts) == 1 or parts[0].lower() == 'cd':
            target = HOMEDIR
        else:
            target = parts[1]

            target = os.path.expanduser(target)     # expands the path of '~'

            target = os.path.abspath(target)
        
        os.chdir(target)
        CWD = os.getcwd()

    except FileNotFoundError:
        print(f"cd: {target}: No such file or directory")
    except PermissionError:
        print(f"cd: {target}: Permission denied")
    except Exception as e:
        print(f"[Error]: {e}")

def pipes(text):
    if not text:
        return

    try:
        cmds = text.split("|")
        prev = None
        for cmd in cmds:    
            parts = shlex.split(cmd)    # Spliting the command
            if prev is None:        # if it's the first time
                p = subprocess.Popen(parts, stdout=subprocess.PIPE)
            else:       # else times.
                p = subprocess.Popen(parts, stdin=prev.stdout, stdout=subprocess.PIPE)
            prev = p
        
        output = prev.communicate()[0]
        print(output.decode())
    except Exception as e:
        print(f"[Error]: {e}")

def redirection(text):
    if not text:
        return

    program = None
    file = None
    try:
        
        # For overwriting files
        if ">" in text:
            program, file = text.split(">")
            mode = "w"

        # For appending in files
        elif ">>" in text:
            program, file = text.split(">>")
            mode = "a"
        
        # For reading from files
        elif "<" in text:
            program, file = text.split("<")
            mode = "r"
    
        with open(file.strip(), mode) as f:
            if "<" in text:
                subprocess.Popen(shlex.split(program), stdin=f)
            else:
                subprocess.Popen(shlex.split(program), stdout=f)
    except Exception as e:
        print(f"[Error]: {e}")

def logicalOperators(text):
    if not text:
        return

    try:   
        
        # cmd1 && cmd2 here && means run cmd2 if cmd1 succeeded 
        if "&&" in text:
            c1, c2 = text.split("&&", 1)
            r = subprocess.run(c1.strip(), shell=True)
            if r.returncode == 0:
                subprocess.run(c2.strip(), shell=True)

        # cmd1 || cmd2 here || means run cmd2 if cmd1 fails
        elif "||" in text:
            c1, c2 = text.split("||", 1)
            r = subprocess.run(c1.strip(), shell=True)
            if r.returncode != 0:
                subprocess.run(c2.strip(), shell=True)

        # cmd1 ; cmd2 here ; means run cmd2 no matter what 
        elif ";" in text:
            for c in text.split(";"):
                subprocess.run(c.strip(), shell=True)
    except Exception as e:
        print(f"[Error]: {e}")

def backgroundJobs(text):
    if not text:
        return

    try:
        cmd = text.rstrip('&').strip()
        parts = shlex.split(cmd)
        subprocess.Popen(parts)     # running commands in new child process
        print("[Background job started]")
        
    except Exception as e:
        print(f"[Error]: {e}")

def runCommands(cmdtext):
    if not cmdtext:
        return

    # Moving specific commands to their functions
    if "|" in cmdtext:
        pipes(cmdtext)

    elif ">" in cmdtext or ">>" in cmdtext or "<" in cmdtext:
        redirection(cmdtext)
    
    elif cmdtext.endswith("&"):
        backgroundJobs(cmdtext)

    elif "&&" in cmdtext or "||" in cmdtext or ";" in cmdtext:
        logicalOperators(cmdtext)

    else:
        try:
            try:
                parts = shlex.split(cmdtext)
                process = subprocess.Popen(
                    parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            except:
                process = subprocess.Popen(
                    cmdtext,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True
                )

                for line in process.stdout:
                    print(line, end="")

                process.wait()
        except Exception as e:
            print(f"Command not found or error: {e}")

def main():
    while True:
        try:
            # [user@hostname:Month Day Year Directory]$ 
            user = getpass.getuser()
            hostname = os.uname().nodename
            currentTime = datetime.datetime.now().strftime("%b %d %Y")
            if CWD:
                workingDir = CWD
            else:
                workingDir = os.getcwd()
            inputTxt = f"[{user}@{hostname}:{currentTime} {workingDir}]$\n-> "

            cmd = input(inputTxt).strip()
            psh_history(cmd)

            if cmd.lower() in CRITICAL_DANGEROUS:
                print(f"{cmd} is very dangerous and can harm your device.")
                bypassPrompt = input("To bypass this warning, Answer these questions [Yes/No]: ").strip()
                if bypassPrompt.lower() in ['no', 'n']:
                    return
                elif bypassPrompt.lower() in ['yes', 'y']:
                    securityQuestions = {
                        "Enter hostname of this device: ": hostname,
                        "Enter current user name: ": user,
                        "Are you authorized to perform this action on this system?(yes/no): ": "yes",
                    }

                    for question in securityQuestions:
                        ask = input(question)
                        if ask == securityQuestions[question]:
                            runCommands(cmd)                        
                        else:
                            print("Operation Failed.")
                            continue

                else:
                    print("Invalid response, Try again.")
                    continue
                
                continue
            if cmd in alias_Entries.keys():
                runCommands(alias_Entries[cmd].replace("\'", '').strip())
                continue

            if cmd.lower() in ["exit", "quit", "logout"]:
                sys.exit()
                break

            elif "cd" in cmd.lower():
                changeDir(cmd)
                continue
            
            elif cmd.lower() == 'pwd':
                getPWD()
                continue
            
            elif cmd.lower().startswith('echo'):
                showEcho(cmd)
                continue
            
            elif cmd.lower().startswith('export'):
                export(cmd)
                continue
            
            elif cmd.lower().startswith('unset'):
                unset(cmd)
                continue
            
            elif cmd.lower().startswith('alias'):
                alias(cmd)
                continue
            
            elif cmd.lower().startswith('unalias'):
                unalias(cmd)
                continue

            else:
                runCommands(cmd)
                continue
        except KeyboardInterrupt:
            print('')
            continue
        except Exception as e:
            print(f"[MAIN ERROR]: {e}")
            break





if __name__ == '__main__':
    main()