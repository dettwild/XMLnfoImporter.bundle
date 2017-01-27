XMLnfoImporter.bundle-for-Plex
=====================================
The agent is supposed to import metadata from a LOCAL *.nfo file (xml format).
It can be installed by copying the bundle to the Plug-Ins folder.

Alternatively you can install manually by downloading the [zipped bundle](https://github.com/dettwild/XMLnfoImporter.bundle/archive/master.zip) from github, extract it, rename it to **XMLnfoImporter.bundle**.

Manual steps to install on ubuntu 14.04:
- Download from github and unzip
- Remove "-master" from the end of folder name --> folder name ends in *.bundle.
- Copy *.bundle folder to:  /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins   or :  /apps/plexmediaserver/MediaLibrary/Plex Media Server/Plug-ins/
- "cd" to Plug-ins folder in step 3 and change ownership of the new *.bundle folder: "sudo chown -R plex:{gid} XBMC*"
- run "sudo service plexmediaserver restart".
Done.
