# CComplete

A sublime plugin providing code completion for C and C++.

## CComplete

This plugin was created after testing other plugins for sublime. The plugin is simple, requires no background deamon or and is designed to be used with very large projects in mind. However, this plugin is only an alpha version and should be considered as such. This means it can still be optimized for both speed and memory footprint, it will error or stop working and basic functionality might still not work.

## What it does

- Provide code completion in c and c++ files
- Deduct members of structs/unions (if you're lucky)
- Provide type information for word under cursor
- Jump to definitions

## What it does not do

- References: ctags does not support references, this can be solved using other plugins such as SublimeGtags
- Whole project search, indexing a whole project takes tens of minutes (depending on the project size ofcourse) and since this plugin tries to do all indexing live thats out of the question.

## CTags

This plugin requires ctags to be installed on the system, however no tag files must be created. This plugin will automatically detect which files to scan and parse the output straight into memory.

## Todo / Future work
- Improve ctags flags, it might be doing more than what is required by the plugin
- Filter results when multiple results are found
- Better include path deduction, at this point all includes are searched from the project folders, relative includes from the parsed files are not yet found
- Settings, provide settings to optimize this plugin or to customize the behavior
- Run ctags for all files seperately and cache the output when files do not change

## Contributing
- Since I don't have much time I don't have I don't have an issues page
- If you have an issue or a great idea, feel free to fork and create a pull request
- No special coding rules, just make it readable and test it a bit
