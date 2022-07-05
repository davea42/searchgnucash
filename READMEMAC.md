# Macos-specific searchcash

We'll assume here, that you are in
a terminal window in your $HOME 
directory.

To get GnuCash you will need to go to gnucash.org
and dowmload and install with the gnucash dmg.

You need python3 from python.org (if you
do not have it), download  install
with dmg.  Assuming the current is 3.9.1 or similar,
in the /Applications/python3.9/ directory there are install
certificates making a mac application possible.
/usr/local/bin/python3 links to the 3.9.1 command
line program.

lets call our local source/buiild area scripts/searchgnucash
    cd
    mkdir scripts
    cd scripts
    # Now mkdir searchgnucash and copy the source 
    # into searchgnucash/

## Assuming initial setup done:

    cd scripts/searchgnucash
    source venv/bin/activate
    python3 setup.py py2app -A

    # run the new version by 
    open dist/searchcash.app
    # note the app name comes
    # from setup.py

    #install via
    rm -rf /Applications/searchcash.app
    cp -rp searchcash.app  /Applications/

## Initial setup:

    pip3 install -U py2app
    cd scripts/searchgnucash
    # create a python virtualenv
    python3 -m venv venv
    source venv/bin/activate
    pip3 install wheel fpdf
    # to leave the venv type:
    # deactivate
