import os

#returns the paths and urls to the parent directorys
#e.g. if the path is /foo/bar/blah returns the urls for [/foo,/foo/bar]
def get_parent_dirs(path):
    parents=[]
    while path != "":
        name = os.path.basename(path)
        url = os.path.join("/files",path)
        parents.append({"name" : name, "url" : url})
        path = os.path.dirname(path)

    parents.reverse()
    # for parent in parents:
        # print(parent)
    return parents



#creates a list of all files and directories in a directory
def list_directory(dir,root):
    #create list of items in the directory

    entries=os.listdir(dir)
    files=[]
    dirs=[]

    #sort this list
    entries.sort()

    for entry in entries:
        dict = {}

        if entry[0]==".": continue #do not show hidden files

        dict["name"]=entry
        dict["url"]=os.path.join(root,entry)
        path=os.path.join(dir,entry)
        dict["path"]=path
        if os.path.isfile(path):
            dict["type"]="file"
            files.append(dict)
        elif os.path.isdir(path):
            dict["type"]="dir"
            dirs.append(dict)
        # else:
            # print("Error: unknown item '%s'"%entry)

    contents = dirs + files

    return contents
