# Setup 

1. Place the annotate and delete_annotation files in your Sioyek folder (i.e. sioyek-release-windows, for Windows users)
2. Create a folder to hold the annotation Markdown files and update ANNOTATIONS_FOLDER_PATH in the extension files
3. Create a memory.pkl file and place its path in ANNOTATIONS_MEMORY (one day I will get the initializer working)
4. Add the following to your Sioyek config files.

### prefs_user.config
- ```new_command _annotate python ABSOLUTE_PATH_TO_annotate.py "%{sioyek_path}" "%{local_database}" "%{shared_database}" "%{file_path}" "%{file_name}" "%{mouse_pos_document}"```
- ```new_command _delete_annotation python ABSOLUTE_PATH_TO_delete_annotation.py "%{sioyek_path}" "%{local_database}" "%{shared_database}" "%{file_path}" "%{file_name}" "%{mouse_pos_document}"```
### keys.config
- ```_annotate aa```
- ```_delete_annotation da```

These config files can be opened from Sioyek by pressing : and searching "prefs_user" or "keys", respectively.

# Use

Pressing ```aa``` will open a Markdown file associated to the Sioyek document highlight nearest to your cursor. The file will open in your default program for editing .md files.

Pressing ```da``` while hovering over a highlight will unlink the highlight and its corresponding .md file, and open that .md file for you to delete with your editor. It does NOT delete the file automatically.