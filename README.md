# CComplete

A sublime plugin providing code completion for C and C++.

## CComplete

This plugin was created after testing other plugins for sublime. The plugin is simple, requires no background deamon or and is designed to be used with very large projects in mind. However, this plugin is only an alpha version and should be considered as such. This means it can still be optimized for both speed and memory footprint, it will error or stop working and basic functionality might still not work.

## What it does

- Provide code completion in c and c++ files
- Deduct members of structs/unions
- Provide type information for word under cursor
- Jump to definitions
- The plugin caches information in memory and on disk to speedup information lookups

## What it does not do

- References: ctags does not support references, this can be solved using other plugins such as SublimeGtags
- Whole project search, indexing a whole project takes tens of minutes (depending on the project size ofcourse) and since this plugin tries to do all indexing live thats out of the question.

## CTags

This plugin requires ctags to be installed on the system, however no tag files must be created. This plugin will automatically detect which files to scan and parse the output straight into memory.

## Todo / Future work
- Improve ctags flags, it might be doing more than what is required by the plugin
- Improve the filter that handles symbol collision
- Settings, provide settings to optimize this plugin or to customize the behavior
- Add menuitems to access the settings/commands

## Contributing
- If you have an issue or a great idea, feel free to fork and create a pull request
- No special coding rules, just make it readable and test it a bit
- Issues will be handled at a best effort basis
