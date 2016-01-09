import sys

def is_mac():
    return sys.platform=="darwin"

def is_win():
    return sys.platform[:3] == "win"

def is_linux():
    return sys.platform[:5] == "linux"

def accelerator_string():
    if is_mac():
        return "Command"
    else:
        return "Ctrl"

def diffmerge_exec():
    #@todo: Add to the config file    
    #osx_diffmerge_exec = "/Applications/Programming/DiffMerge/DiffMerge.app/Contents/MacOS/DiffMerge"
    osx_diffmerge_exec = "/Applications/DiffMerge/DiffMerge.app/Contents/MacOS/DiffMerge"
    win_diffmerge_exec = "C:/Program Files (x86)/SourceGear/DiffMerge/DiffMerge.exe"
    linux_diffmerge_exec = "diffmerge"
    if is_mac():
        return osx_diffmerge_exec
    if is_win():
        return win_diffmerge_exec
    return linux_diffmerge_exec