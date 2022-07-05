# Search Gnu Cash

For Version 0.1.0

These are
programs to allow more targeted searches from a GnuCash
(the GNU personal accounting program) data file.

While GnuCash has many very useful report options
its reports do not seem useful for dealing with
some kinds of problems one encounters.
Which motivated writing these programs.

See www.gnucash.org

Ubuntu:  sudo apt install gnucash

These assume $HOME/searchgnucash.conf has been created
to specify globally meaningful basic information (see below).

An actual gnucash data file consists of gzip'd xml.
Amounts in the file are expressed (in the xml) as
rational numbers such as   <value>1123/100</value> 
meaning USD11.23 here (applicable
to US Dollars or any currency with 100 'pennies'
per basic unit, dollars here).
This approach GnuCash has taken
lends itself to any currency, though
the programs here are expecting USD values.

Since all is plain text xml one can copy or
move a GnuCash
file to any other machine without any problems.

We internally treat the values as floating point.
Note that python3 floating point values can
accommodate extraordinarily large (arbitrarily large?)
values without loss.

## searchgnucash

This is the command line program, it produces text output.
It produces selected results in a pleasant
human-readable format.

It uses $HOME/searchgnucash.conf to find a default
GnuCash file to read, but one can use the -f option
to name another file to read.

To see the available options:

    searchgnucash -h

### Use Case: Simple Report

For example, to restrict to transactions in 2022
with the letters PG in a description or memo field:
Multiple -s  options are allowed.

    searchgnucash -d 2022 -s PG
    # To look for all transactions with value 255.41
    searchgnucash -s 255.41

### Use Case: Comparison

Assuming you have two GnuCash files (lets
call them a.gnucash and b.gnucash) with slightly different
content and one is not sure
where there is any difference (but hopefully not
thousands!!)  one can see the differences easily.

    searchgnucash a.gnucash  >a.temp
    searchgnucash b.gnucash  >b.temp
    # then
    diff   a.temp b.temp
    # or use a graphical diff, for example:
    fldiff a.temp b.temp

### Use Case: Account Names

Sometimes one needs the precise spelling of a GnuCash account.
This lists all the account names.

    searchgnucash  -printacctnames

### Use Case: Spreadsheet (csv)

Given a transaction with many splits (anything over 20
or so) reconciling with
other records can be a chore if the sum in a transaction
splits does not seem to match other relevant data.

    searchgnucash  -d 2022-02-24 -s Chase -csv >a.csv
    #Now read in a.csv with a spreadsheet, such as
    #soffice, and select comma separation
    #The split entries will be in a three-column format
    #with the second column the values.
    soffice a.csv
    #Save the spreadsheet (as a .ods, for example)
    #And add a sum() row to add the entries of interest.

## searchcash

This is a python/tk/ttk graphical front end to searchgnucash.

It's main panel allows entry of search terms, dates, and more.

Click 'Quit' to exit the program.

Much of what searchgnucash can create is reportable and
this program assumes that a pdf output is desired for
to a graphical/click based use then plain text.
The pdf is created in the ~/Desktop directory.

Most useful for reporting a modest-size output based
on the selected options.

## searchcash on Macos

One must have Apple command line tools available.
These are free from Apple.

One needs the tool named 'py2app' on Macos to turn
searchcash into a runnable Macos app one can put
into /Applications and the Apple Dock.

More will be said on this.

