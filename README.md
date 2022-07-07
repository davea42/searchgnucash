# Search Gnu Cash

For Version 0.1.0

These are
programs to allow more targeted searches from a GnuCash
(the GNU accounting program) data file.
GnuCash is a full double-entry bookkeeping system.

While GnuCash has many very useful report options
its reports do not seem useful for dealing with
some kinds of problems one encounters in
doing the bookkeeping.
For example, reconciling a transaction with many
entries (called 'splits') on a credit card for a month with
the report from the credit card company.
Or when one thinks one's own typo (possibly in a date)
has caused a tranaction to move to an unexpected place
and you need to find it.
Issues like this motivated writing this code.

See www.gnucash.org

Ubuntu:  sudo apt install gnucash

These assume $HOME/searchgnucash.conf has been created
to specify globally meaningful basic information.
Use the version in this directory, copy to $HOME, and update
to match your situation.

Python3 defaults to UTF-8 characters so the content is not
restricted to ASCII.

An actual gnucash data file consists of gzip'd xml.
Amounts in the file are expressed (in the xml) as
rational numbers such as   <value>1123/100</value> 
meaning USD11.23 here (applicable
to US Dollars or any currency with 100 'pennies'
per basic unit).
This approach GnuCash has taken
lends itself to any currency, though
the programs here are expecting USD values.
See the function 'stdval()' in searchgnucash.py, the
only place where the issue arises.

We internally treat the values as floating point.
Note that python3 floating point can
accommodate extraordinarily large (arbitrarily large?)
values without loss.

Since the gnucash data file is plain text xml one can copy or
move a GnuCash file to any other machine (of any endianness)
without problems.

## searchgnucash

This is the command line program, it produces text output.
It produces results in a pleasant
human-readable format.

It uses $HOME/searchgnucash.conf to find a default
GnuCash file to read, but one can use the -f option
to name another file to read.

To see all the available options with explanatory
details:

    searchgnucash -h

If parts of that are unclear consider posting an issue
on github explaining what is confusing.

### Use Case: Simple Report

For example, to restrict to transactions in 2022
with the letter pair PG in a description or memo field:

    searchgnucash -d 2022 -s PG
    # To look for all transactions with value 255.41
    searchgnucash -s 255.41

Multiple -s  options are allowed.

### Use Case: Comparison

Assuming you have two GnuCash files (lets
call them a.gnucash and b.gnucash) with slightly different
content and one is not sure
where there is any difference (but hopefully not
thousands of differences!!)
one can see the differences easily.
Of course usual options such as -s and -d etc
allow more selectivity when you know more precisely
where to find differences of interest.
One has to do regular (frequent) backups of the
gnucash data file for this to be of much use.

    searchgnucash -f a.gnucash  >a.temp
    searchgnucash -f b.gnucash  >b.temp
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

Here searching the gnucash file named 
in $HOME/searchgnucash.conf:

    searchgnucash  -d 2022-02-24 -s Chase -csv >a.csv
    # Now read in a.csv with a spreadsheet, such as
    # soffice, and select only comma separation of fields when
    # the spreadsheet program asks how to deal with the csv.
    # The split entries will be in a three-column format
    # with the second column the values.
    soffice a.csv
    # Save the spreadsheet (as a .ods, for example)
    # And add a sum() cell to add the entries 
    # of interest from column B.

## searchcash

This is a python/tk/ttk graphical front end to searchgnucash.

It's main panel allows entry of search terms, dates, and more.

Click 'Quit' to exit the program.

Much of what searchgnucash can create is reportable and
searchcash assumes that a pdf output is desired
rather than plain text.
The pdf is created in the ~/Desktop directory.

This is most useful for reporting a modest-size output based
on the selected options.

The appearance of the 
panel is automatically 
consistent  with other graphical panels
of whatever OS you are running (Linux,Windows,Macos).

## searchcash on Macos

One must have Apple command line tools available.
These are free from Apple.

One needs the tool named 'py2app' on Macos to turn
searchcash into a runnable Macos app one can put
into /Applications and the Apple Dock.

See READMEMAC.md for details.
