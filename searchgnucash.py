#!/usr/bin/env python3
#Copyright (c) 2020 David Anderson
#All rights reserved.
#
#Redistribution and use in source and binary forms, with
#or without modification, are permitted provided that the
#following conditions are met:
#
#    Redistributions of source code must retain the above
#    copyright notice, this list of conditions and the following
#    disclaimer.
#
#    Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
#EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# gnucashsearch.py
# This is a command-line app. The gui is cashsearch.py
#
# On the financial machine as ~/bin/xread.py
# An application that reads GnuCash
# data (xml data in a gzip file is the GnuCash way)
# and allows simple searches, producing a text output.
# While gnucash is quite capable of doing sophisticated
# searches on its own this code provides a simpler
# interface that does not interfere with whatever
# the user is doing in gnucash.
#
# By default this pulls the gnucash file full path from
# searchgnucash.py 
#
# if you are looking at other versions of a cash file
# the -f option lets you do a search against any version
# without touching the gnusearchcash's default file.
#
# This is entirely text based but (depending on your
# OS of choice may be easy or difficult to wrap in a GUI
# package so it can be used by folks not used to
# typing on a command line.

# python3 gnucashsearch.py -h to see all options.

# Example:
#   python3 gnucashsearch.py -case 0 -s something -s somethingelse -d 2013
# which searches (ignoring case) for
# transactions with the string 'something' and
# the string 'somethingelse' which were posted in  the year 2013.

# This program is known to work on  versions of Linux and MacOS.

import sys 
import os
import gzip
from datetime import datetime, date, time
import xml.etree.ElementTree as ET


def usage(msg):
    # All splits is always on now.
    print(msg)
    print("Usage: [-case {1,0}]")
    print("       [-s srchterm]* ")
    print("       [-d dateselected]") 
    print("       [-allafter date]")
    print("       [-datetype [both|posted|entered]]")
    print("       [-onlytranslines]" )
    print("       [-accountreport] [-accountselect acctname] ")
    print("       [-printacctnames] ")
    print("       [-csv] ")
    print("       [-f cashpath]")
    print("       [-h] ")
 
    print("Any dates here must be in the form YYYY-MM-DD or")
    print("  any initial subrange of that ('2021-11' for example).")  
    print("Where -h prints this usage and exits.")
    print("Where -s terms (any number of -s arguments allowed)")
    print("  are 'and' terms so all must match to select transaction")
    print("  to print.")
    print("Where -d dateselected is ISO extended-date form:")
    print("  '-d 2014'         matches 2014")
    print("  '-d 2013-02'      matches any February 2013 date")
    print("  '-d 2013-02-12'   matches any  February 12, 2013 ")
    print("       split transaction.")
    print("Where '-case 0' means ignore case in searches.")
    print("      '-case 1' means honor case in searches.")
    print("Where -allafter means print transaction detail matching")
    print("  other criteria that are also after that date.")
    print("  date format is like  2015-02-09 (yyyy-mm-dd).")
    print("Where -datetype lets one specify whether 'entered' or ")
    print("  'posted' or 'both' (both is the default) is to be")
    print("  checked against date ranges. By default checks both")
    print("  and accepts if either passes.")
    print("Where -accountreport causes a simple report format")
    print("  useful for year-end reporting.")
    print("Where -accountselect allows specifying an account name.")
    print("  Only transactions using that name will be printed.")
    print("Where -csv means splits are  a three column csv format")
    print("Where -printacctnames produces a list of account")
    print("   names so you can get the precise spelling(s).")
    sys.exit(1)


def badfield(f):
    newlinecount = 0
    res = False
    for c in f:
        if c == "\n":
            newlinecount = int(newlinecount) + 1
        v = ord(c)
        if v < 32:
            res = True
        elif v > 126:
            res = True
        continue
    return (res, newlinecount)


def actic(v, st):
    """Return original string if casesense == "y"
    Return lower-case version of casesense == "n"
    """
    casesense = st._casesense
    if casesense == "y":
        return v
    return v.lower()


def slimdescr(s, outlen):
    if len(s) < int(outlen):
        return s
    return s[0:outlen]


def acticlist(v, st):
    """Return original string if casesense == "y"
    Return lower-case versin of casesense == "n"
    """
    casesense = st._casesense
    if casesense == "y":
        return v
    outlist = []
    for s in v:
        outlist += [s.lower()]
    return outlist


class transaction_entry:
    def __init__(self):
        # Posted is the date the transaction applies to.
        self._dateposted = ""
        # entered is the date the transaction was created.
        self._dateentered = ""
        self._transactionnum = ""
        self._description = ""
        self._foundmatch = False
        self._tguid = "n"

    def __init__(self, dateposted, dateentered, transnum, descr, tguid):
        self._dateposted = dateposted
        self._dateentered = dateentered
        self._transactionnum = transnum
        self._description = descr
        self._tguid = tguid

    def add_tdata(self, dateposted, dateentered, transnum, descr, tguid):
        self._dateposted = dateposted
        self._dateentered = dateentered
        self._transactionnum = transnum
        self._description = descr
        self._tguid = tguid

    def markmatch(self):
        self._foundmatch = True

    def tprint(self, st):
        # print("dadebug","posted",self._dateposted,"entered",self._dateentered)
        # print("            %6s"%self._transactionnum,":",self._description)
        ew = self._dateposted.strip().split()
        if len(ew) > 0:
            ews = ew[0]
        else:
            ews = "no-date"
        print("")
        ee = self._dateentered.strip().split()
        print(
            "Trans: p:%s e:%s %-6s %s"
             % (
                ews,
                ee[0],
                slimdescr(self._transactionnum.strip(), 6),
                self._description.strip())
            )
        b, nl = badfield(self._transactionnum)
        if b:
            print("  Badfield", nl, " transactionnum", self._transactionnum)
            print("  tguid   ", self._tguid)
        b, nl = badfield(self._description)
        if b:
            print("  Badfield", nl, " description ", self._description)
            print("  tguid   ", self._tguid)

    def __lt__(self, other):
        if self._dateposted == other._dateposted:
            return self._dateentered < other._dateentered
        return self._dateposted < other._dateposted


class split_entry:
    def __init__(self):
        self._memo = ""
        self._value = ""
        self._chknum = ""
        self._acctname = ""
        self._accttype = ""
        self._foundmatch = False
        self._sguid = ""

    def markmatch(self):
        #print("dadebug markmatch on",self._memo)
        self._foundmatch = True

    # Value is a string of a float created by stdval()
    def add_splitdata(self, memo, tnum, value, acctname, accttype, sguid):
        self._memo = memo
        self._value = value
        self._chknum = tnum
        self._acctname = acctname
        self._accttype = accttype
        self._guid = sguid

    def sprint(self, msg, acctsumdict,st):
        acctname = self._acctname.strip()
        val = float(self._value)
        ov = acctsumdict.get(acctname, 0)
        acctsumdict[acctname] = float(ov) + val
        memo=self._memo.strip()
        chknum=self._chknum.strip()
        if st._csvformat:
            f= '\"%s %24s\",%9.2f,\"%s\"'% \
                (chknum,memo,val,acctname)
            print(f)
        elif len(memo) < 26:
            print( msg,
                " %-4s %-26s %9.2f %-22s"
                % (
                    slimdescr(chknum, 4),
                    memo,
                    val,
                    acctname,
               ))
        else:
            print( msg,
                " %-4s %s " %(
                slimdescr(chknum,4),
                memo))
            print( msg, 
                "%33s %8.2f %s"%('',
                    val, 
                    acctname))
        b, nl = badfield(self._memo)
        if b:
            print("   Badfield", nl, " memo ", self._memo)
            print("   sguid  ", self._guid)
        b, nl = badfield(self._chknum)
        if b:
            print("   Badfield", nl, " chknum ", self._chknum)
            print("   sguid  ", self._guid)

def dictaddfloat(dct,key,val):
    v1 = dct.get(key,0.0)
    v2 = float(val) +float(v1)
    dct[key] = v2

class whole_transaction:
    def __init__(self):
        self._trans = ""
        self._splits = []
        self._foundmatch = False
        self._printallsplits = True

    def markmatch(self):
        self._foundmatch = True

    def add_transentry(self, transentry):
        self._trans = transentry
        self._splits = []

    def addsplit(self, splitentry):
        self._splits += [splitentry]

    def findmarkedsplits(self,st):
        splitmarklist = []
        for (i, s) in enumerate(self._splits):
            if s._foundmatch:
                splitmarklist += [s]
        return splitmarklist


    def wprint(self, title, st, acctsumdict):
        #print("dadebug wprint entered. ")
        if st._accountreport:
            posted= self._trans._dateposted.strip().split()
            entered =self._trans._dateentered.strip().split()
            dayonly = posted[0]
            monthonly = dayonly[0:7]
            yearonly = dayonly[0:4]
            edayonly = entered[0]
            
            lastmonthonlyname = acctsumdict.get('lastmonth',False)
            lastyearonlyname = acctsumdict.get('lastyear',False)
            #print("dadebug ",lastmonthonlyname,lastyearonlyname)
            if lastmonthonlyname:
                if lastmonthonlyname != monthonly:
                    tot = acctsumdict.get(lastmonthonlyname);
                    if not tot:
                       tot = 0.0
                    print("===========Posted Month %s Sum %9.2f"% \
                        (lastmonthonlyname, \
                        float(tot)))
                    lastmonthonlyname = monthonly
                    acctsumdict["lastmonth"] = monthonly
                else:
                    pass
            else:
                lastmonthonlyname= monthonly
                acctsumdict["lastmonth"] = monthonly
            if lastyearonlyname:
                if lastyearonlyname != yearonly:
                    tot = acctsumdict.get(lastyearonlyname)
                    if not tot:
                        tot = 0.0
                    print("===========Posted Year %s Sum %9.2f"%\
                        (lastyearonlyname, \
                        float(tot)))
                    lastyearonlyname = yearonly
                    acctsumdict["lastyear"] = yearonly
                else:
                    pass
            else:
                lastyearonlyname = yearonly
                acctsumdict["lastyear"] = yearonly
            descr=  self._trans._description.strip()
            slist = self.findmarkedsplits(st)
            for s in slist:
                #print("dadebug acctrep item ",s._memo,s._foundmatch)
                if not s._foundmatch:
                    continue
                act = s._acctname.strip()
                val = float(s._value)
                dictaddfloat(acctsumdict,act,val)
                dictaddfloat(acctsumdict,yearonly,val)
                dictaddfloat(acctsumdict,monthonly,val)
                f1  = float(s._value.strip())
                f2  = float(acctsumdict.get(act))
                memo = s._memo.strip()

                if len(descr) > 20  or len(memo) > 20 or len(act) > 10:
                    print("p:%s e:%s "%(dayonly,edayonly),end='')
                    print("    %-s"%(descr))
                    if len(memo) <= 20:
                        # two lines
                        print("    %-15s memo:%-20s"%(act[0:15],memo),end='') 
                        print("%37s  %9.2f %9.2f"% ("",f1,f2))
                    else:
                        # three lines
                        print("    %-15s memo: %s"%(act,memo)) 
                        print("%82s  %9.2f %9.2f"% ("",f1,f2))
                else:
                    print("dadebug all one line")
                    print("p:%s e:%s "%(dayonly,edayonly),end='')
                    print("%-20s %-15s %-20s %9.2f %9.2f"% \
                        (descr[0:20],\
                        act[0:15], \
                        memo[0:20], \
                        f1, f2 ))
            return
        self._trans.tprint(st)
        if st._onlytranslines:
            #print("dadebug onlytrans")
            return
        splitmarklist = []
        for (i, s) in enumerate(self._splits):
            #print("dadebug enumerate split ",i,\
            #    s._memo,s._foundmatch)
            if s._foundmatch:
                splitmarklist += [str(i)]
        if len(splitmarklist) == 0:
            # Only transaction marked. Mark all the splits.
            for s in self._splits:
                s.markmatch()
        for s in self._splits:
            #print("dadebug split ",s._memo,s._foundmatch)
            if s._foundmatch or self._printallsplits:
                s.sprint("", acctsumdict,st)

    def __lt__(self, other):
        return self._trans < other._trans


def curtime():
    dt = datetime.now()
    tm = dt.strftime("%Y-%m-%d %H:%M:%S")
    return tm


def quoteme(s):
    s2 = '"%s"' % s
    return s2


class searchterms:
    def __init__(
        self,
        searchtermlist,
        dateselected,
        casesense,
        printallsplits,
        printallafter,
        onlytranslines,
        accountselect,
        printacctnames,
        accountreport,
        datetype,csvformat
    ):
        self._casesense = casesense
        self._dateselected = dateselected
        self._printallafter = printallafter
        self._searchchecklist = []
        self._printchecklist = []
        self._printallsplits = printallsplits
        self._onlytranslines = onlytranslines
        self._accountselect = accountselect
        self._printacctnames = printacctnames
        self._accountreport = accountreport
        self._datetype = datetype
        self._csvformat = csvformat
        # this is a bit like passing incompletely
        # constructed record...
        # Even though all our fields are set to something.
        self._printchecklist = searchtermlist
        self._searchchecklist = acticlist(searchtermlist, self)

    def afterdate(self,l,dtocheck,allafter):
        nums = dtocheck.split("-")
        alls = allafter.split("-")
        lenalls = int(len(alls))
        #print("dadebug ",l,"date",dtocheck,"allafter",allafter,"lengths",len(nums),len(alls))
        if alls[0] < nums[0]:
            #print("dadebug true1");
            return True
        if alls[0] == nums[0]:
            if lenalls < 2:
                #print("dadebug true2",len(alls));
                return True
            else:
                pass
        else: 
            #print("dadebug false2b",len(alls));
            return False
        if lenalls < 2:
            #print("dadebug false2",len(alls));
            return False
        if alls[1] < nums[1]:
            #print("dadebug true3");
            return True
        if alls[1] == nums[1]:
            if lenalls < 3:
                #print("dadebug true4");
                return True
            else:
                pass
        else:
            #print("dadebug false4b",len(alls));
            return False
        if lenalls < 3:
            #print("dadebug false4",len(alls));
            return False
        if alls[2] <= nums[2]:
            #print("dadebug true5");
            return True
        #print("dadebug False");
        return False
    def checkfirstn(self,l,d,b):
        for i in range(l):
            if d[i] !=  b[i]:
                return False
        return True
    def dateinrange(self,posted,entered):
        if  self._datetype:
            if self._datetype == "posted":
                return self.dateinrangeb(posted);
            else:
                return self.dateinrangeb(entered);
        if self.dateinrangeb(posted):
            return True
        if self.dateinrangeb(entered):
            return True
        return False
    def dateinrangeb(self,d):
        donly = d[0:10]
        if self._dateselected:
            b = self._dateselected
            l = len(b)
            return self.checkfirstn(l,donly,b)
        if self._printallafter:
            b = self._printallafter
            l = len(b)
            return self.afterdate(l,donly,b)
        return True

    def stermsprint(self,fname):
        print(    "Search Date   :", curtime())
        print(    "Search In     :", fname)
        if len(self._printchecklist) > 0:
            print(    "Searchterms   :", \
                str(len(self._printchecklist)))
            for i in self._printchecklist:
                s = quoteme(i)
                print( \
                  "SearchFor     :", s)
        else:
            print("Searchterms   : none")

        cs = "Casesensitive : %s" % yesno(self._casesense)
        print(cs)

          
        content = "posted and entered checked"
        if self._datetype:
            content = self._datetype
        d =   "Date Type     : %s" % content
        print(d)

        content = ""
        if self._dateselected:
            content =   self._dateselected
        d =   "Date Selected : %s" % content
        print(d)


        content = ""
        if self._printallafter:
            content = self._printallafter
        alla= "AllAfterDate  : %s" % content
        print(alla)
        
        content = "no" 
        if self._onlytranslines:
             content = "yes"
        d =   "Trans. Only   : %s" % content
        print(d)

        content = "no"
        if self._accountreport:
            content = "yes"
        d =   "Account Report: %s" % content
        print(d)

        content = ""
        if self._accountselect:
            content=str(self._accountselect)
        print("Report Account:", content)

        print("We truncate the description and memo fields in")
        print("the output,so the matching part of a transaction")
        print("or split might not show in this report.")


def yesno(yn):
    if yn == "y":
        return "yes"
    return "no"


def searchmatchtransaction(tran, st):
    """Failing a date check means we are done
    and we return a list of a single string "date", regardless
    of other things.
    Otherwise we return a list of numbers of the matches that
    matched here.
    """
    dateselected = st._dateselected
    searchlist = st._searchchecklist
    # Posted is the date it applies to
    posted = actic(tran._dateposted, st)
    # Entered is the date the data entry was initially done.
    entered = actic(tran._dateentered, st)
    matchedck = []
    if st.dateinrange(posted,entered):
        pass
    else:
        return ["date"]
    termnum = 0
    transnum = actic(tran._transactionnum, st)
    transdescr = actic(tran._description, st)
    # print("dadebug searchlist",searchlist)
    for searchstr in searchlist:
        m = transnum.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        m = transdescr.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        m = entered.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        termnum = int(termnum) + 1
    return matchedck


def searchmatchsplit(s, st):
    searchlist = st._searchchecklist
    smemo = actic(s._memo, st)
    svalue = actic(s._value, st)
    sacct = actic(s._acctname, st)
    chknum = actic(s._chknum, st)
    # We do not use termnum itself, it is
    # really just a flag 'found' as we print
    # the transaction and all splits,
    # not just the matching splits.
    termnum = 0
    matchedck = []
    acctterm = int(len(searchlist)) + 1
    if st._accountselect:
        us = actic(st._accountselect, st)
        if sacct == us:
            matchedck =  [str(termnum)]
            return matchedck, True, acctterm
        if st._accountreport:
            # empty list, not matched, check no search terms.
            return matchedck, True, acctterm
    for searchstr in searchlist:
        m = smemo.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        m = sacct.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        m = svalue.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        m = chknum.find(searchstr)
        if m != -1:
            matchedck += [str(termnum)]
        termnum = int(termnum) + 1
    # print("dadebug split matchedck ",matchedck)
    return matchedck, False, acctterm


def searchmatches(wholetrans, st):
    """See if the trans matches. Return "y" if so, else return "n" """
    transcheck = wholetrans._trans
    foundlist = searchmatchtransaction(transcheck, st)
    founddict = {}
    if len(foundlist) == 1 and foundlist[0] == "printall":
        return "y"
    if len(foundlist) == 1 and foundlist[0] == "noprint":
        return "n"
    if len(foundlist) == 1 and foundlist[0] == "date":
        # Wrong date, not a transaction we want to show.
        return "n"
    for e in foundlist:
        founddict[e] = 1
    if len(foundlist) > 0:
        #print("dadebug searchmatches wholetrans found",foundlist)
        wholetrans._trans.markmatch()
        wholetrans._printallsplits = st._printallsplits
    else:
        if st._accountreport:
            #print("dadebug account report searchmatches wholetrans found nothing")
            wholetrans._trans.markmatch()
            wholetrans._printallsplits = st._printallsplits
    splen = len(wholetrans._splits)
    i = 0
    foundcount = 0;
    while i < splen:
        s = wholetrans._splits[i]
        foundlist, accountselect, termnum = searchmatchsplit(s, st)
        if len(foundlist) > 0:
            #print("dadebug searchmatchsplit() wholetrans found"\
            #,i,s._acctname)
            s.markmatch()
            wholetrans._printallsplits = st._printallsplits
            foundcount = int(foundcount) +1
        if accountselect and st._accountselect:
            if i in founddict:
                # We do not really care what the count is, 1 is enough.
                ov = founddict[e]
                nv = int(ov) + 1
            # No need to look at search terms, if any we match this.
            #print("dadebug found accountselect match")
            i = int(i) + 1
            continue
        # if search found ensure all terms matched.
        for e in foundlist:
            # different splits could match different searchterms.
            if e in founddict:
                # We do not really care what the count is, 1 is enough.
                ov = founddict[e]
                nv = int(ov) + 1
                founddict[e] = str(nv)
            else:
                founddict[e] = 1
        i = int(i) + 1
    if st._accountselect:
        if foundcount > 0:
            return "y"
        # If requested an account match we never found one in splits.
        return "n"
    # Checking done.
    # If every term satisfied, it is an overall match.
    # Overall match if found in split or in accountselect.
    #print("dadebug searchmatchsplit fieldcount",fieldcount)
    for k in range(len(st._searchchecklist)):
        kstr = str(k)
        if not kstr in founddict:
            # This search term not satisfied anywhere
            # in the transaction or splits.
            return "n"
    # All search terms found.
    # print("dadebug match, returning y")
    return "y"


def printtransmatch(wholetrans, st, acctsumdict):
    """Print a report for the matching transaction."""
    # On overall match (meaning we were called):
    # Print the base transaction record.
    # If several splits had a partial match, print those.
    # If no splits contributed, print all the splits.
    #   (or should we just print one as a token?)
    wholetrans.wprint("Match:", st, acctsumdict)


def shorttag(orig):
    """we strip out the xmlns part of the tag"""
    wds = orig.split("}")
    wct = len(wds)
    tag = wds[int(wct) - 1]
    return tag


def stdval(val):
    """Turn the x/y value into normal text"""
    revisedval = []
    sign = ""
    if val[0] == "-":
        sign = "-"
        w = val[1:]
        val = w
    wds = val.split("/")
    if len(wds) == 2:
        if wds[1] == "100":
            if int(wds[0]) < 100:
                rv = wds[0]
                if sign == "-":
                    revisedval += ["-"]
                revisedval += ["0"]
                revisedval += ["."]
                if len(rv) == 1:
                    revisedval += ["0"]
                    revisedval += [rv[0]]
                else:  # len is 2.
                    revisedval += [rv[0]]
                    revisedval += [rv[1]]
            else:
                rv = wds[0]
                charct = len(rv)
                dotpoint = int(charct) - 2
                for (i, c) in enumerate(rv):
                    if int(i) == int(dotpoint):
                        revisedval += ["."]
                    revisedval += [c]
            return "".join(revisedval)
        else:
            # This is surprising.
            return val
    else:
        return val


def datewithouttz(d):
    """we strip off the trailing tz info, no need for that"""
    wds = d.split()
    v = " ".join([wds[0], wds[1]])
    return v


def quotearound(s):
    return '"' + s + '"'


def print_account_names(acctdict):
    ct = len(acctdict)
    print("Number of Accounts:", ct)
    if int(ct) < 1:
        print("No account names present")
    else:
        acctlist = list(acctdict.values())
        y = sorted(acctlist)
        print("#name,type,guid,parentguid")
        print("acctnames = [ \\")
        for e in y:
            ea = quotearound(str(e[0]))
            eb = quotearound(str(e[1]))
            # Skip parent guid here
            ec = quotearound(str(e[3]))
            parentguid = str(e[2])
            fmt = "(%-20s,%-9s,%s,\\"
            print(fmt % (ea, eb, ec))

            parentname = ""
            if parentguid != "":
                (parentname, t, p, o) = acctdict[parentguid]
            fmt = "         %s ),\\"
            print(fmt % (quotearound(parentguid)))
            if parentname != "Root Account":
                print("         #parentparentname:", parentname)
        print("]")
    sys.exit(0)


def gettransdata(elem, acctdict, splitdict, transdict, st):
    transposteddate = ""
    transenteredate = ""
    transguid = ""
    transdescr = ""
    transnum = ""
    slotposted = ""
    transactionmatch = "n"
    wholetrans = whole_transaction()
    for child in elem:
        ctag = shorttag(child.tag)
        if ctag == "date-posted":
            for child2 in child:
                dtag = shorttag(child2.tag)
                if dtag == "date":
                    transposteddate = datewithouttz(child2.text)
                    break
        elif ctag == "date-entered":
            for child2 in child:
                dtag = shorttag(child2.tag)
                if dtag == "date":
                    transentereddate = datewithouttz(child2.text)
                    break
        elif ctag == "num":
            transnum = child.text
        elif ctag == "description":
            transdescr = child.text
        elif ctag == "id":
            isguid = child.get("type")
            if isguid == "guid":
                transguid = child.text
        elif ctag == "slots":
            # slots not needed.
            for child2 in child:
                c2tag = shorttag(child2.tag)
            #  if c2tag == "slot":
            #    for child3 in child2:
            #      c3tag = shorttag(child3.tag)
            #      if c3tag == "value":
            #        isdate = child3.get("type")
            #        if isdate == "gdate":
            #          for child4 in child3:
            #            c4tag = shorttag(child4.tag)
            #            if c4tag == "gdate":
            #              slotposted = child4.text
        elif ctag == "splits":
            # We 'know' all the base transaction is before splits.
            transaction = transaction_entry(
                transposteddate,
                transentereddate,
                str(transnum),
                str(transdescr),
                str(transguid),
            )
            wholetrans.add_transentry(transaction)
            for child2 in child:
                sguid = ""
                svalue = ""
                smemo = ""
                sacctguid = ""
                acctname = ""
                accttype = ""
                tnum = ""
                c2tag = shorttag(child2.tag)
                if c2tag == "split":
                    for child3 in child2:
                        c3tag = shorttag(child3.tag)
                        # print("dadebug entry field:",c3tag)
                        if c3tag == "id":
                            sisguid = child3.get("type")
                            sguid = child3.text

                        elif c3tag == "action":
                            # This is the 'check number' field in trans entries
                            # Why was this calling stdval() before 01/2021?
                            tnum = child3.text
                        elif c3tag == "value":
                            svalue = stdval(child3.text)
                        # elif c3tag =="num":
                        #  tnum = stdval(child3.text)
                        elif c3tag == "memo":
                            smemo = child3.text
                        elif c3tag == "account":
                            isguid = child3.get("type")
                            if isguid == "guid":
                                sacctguid = child3.text
                    (acctname, accttype, parentguid, ourguid) = acctdict[sacctguid]
                    split = split_entry()
                    acctname = str(acctname)
                    if parentguid != "":
                        # We assume just one level of parent present
                        (pname, ptype, ppguid, ourguid) = acctdict[parentguid]
                        # Root Account is boring.
                        if str(pname) != "Root Account":
                            acctname = str(pname) + ":" + acctname
                    split.add_splitdata(
                        str(smemo),
                        str(tnum),
                        str(svalue),
                        acctname,
                        str(accttype),
                        str(sguid),
                    )
                    wholetrans.addsplit(split)
    res = searchmatches(wholetrans, st)
    if res == "y":
        return ("y", wholetrans)
    return ("n", wholetrans)


def getacctdata(elem, acctdict):
    ename = ""
    pguid = ""
    ourguid = ""
    etype = ""
    for child in elem:
        ctag = shorttag(child.tag)
        if ctag == "name":
            ename = child.text
        if ctag == "id":
            isguid = child.get("type")
            if isguid == "guid":
                ourguid = child.text
        if ctag == "type":
            etype = child.text
        if ctag == "parent":
            pguid = child.text
    #
    # <act:name>taxable</act:name>
    #  <act:id type="guid">6c4f02d60797e9b17cb72b8bf6db19a5</act:id>
    #  <act:type>INCOME</act:type>
    #  <act:commodity>
    #    <cmdty:space>ISO4217</cmdty:space>
    #    <cmdty:id>USD</cmdty:id>
    #  </act:commodity>
    #  <act:commodity-scu>100</act:commodity-scu>
    #  <act:description>taxable interet income</act:description>
    #  <act:parent type="guid">97ff1d6efd522831b63a11754882b08b</act:parent>

    if ourguid == "":
        print("Internal error. Nothing done")
        sys.exit(1)
    else:
        acctdict[ourguid] = (ename, etype, pguid, ourguid)


def getxml(content, countmax, st):
    root = ET.fromstring(content)
    count = 0
    acctdict = {}
    splitdict = {}
    transdict = {}
    foundlist = []
    if countmax == 0:
        # zero means all. So we hack in a 'big' count.
        countmax = 550000
    # root is the History node.
    for elem in root:
        for child in elem:
            stag = shorttag(child.tag)
            if stag == "account":
                getacctdata(child, acctdict)
                continue
            if stag == "transaction":
                if st._printacctnames:
                    print_account_names(acctdict)
                (yn, trans) = gettransdata(child, acctdict, splitdict, transdict, st)
                if yn == "y":
                    foundlist += [trans]
                continue
            count = int(count) + 1
            if int(count) > int(countmax):
                print("stop i")
                break
        count = int(count) + 1
        if int(count) > int(countmax):
            print("stop o")
            break
    # So now print anything found.
    print("Transactions count", len(foundlist))
    y = sorted(foundlist)
    acctsumdict = {}
    for w in y:
        printtransmatch(w, st, acctsumdict)
    if st._accountreport:
        return
    keys = acctsumdict.keys()
    ksort = sorted(keys)
    if len(ksort) > 0:
        print(" account                      total")
    for k in ksort:
        v = float(acctsumdict[k])
        if 0.0 == v:
            continue
        print("%-26s %7.2f" % (k, v))
    return


def quoted(s1, s2, s3):
    q1 = "'" + str(hrutil.twodig(s1)) + "'"
    q2 = "'" + str(hrutil.twodig(s2)) + "'"
    q3 = "'" + str(hrutil.twodig(s3)) + "'"
    return ",".join([q1, q2, q3])


def validateindex(i, lim, m):
    if int(i) < int(lim):
        return
    print("Improper argument list, missing value for ", m)
    usage("")

def reportallafter(d,msg):
    print("The",msg,"date is not in YYYY-MM-DD form or")
    print(" a proper subset of that.");
    print("It is, instead:",d);
    usage("Date Error!")
def validatedate(d,msg):
    if len(d) < 4:
        reportallafter(d,msg)
    wds = d.split("-")
    if len(wds) > 3:
        reportallafter(d,msg)
    w = wds[0]
    if len(w) != 4:
        reportallafter(d,msg)
    if not w.isdigit():
        reportallafter(d,msg)
    if len(wds) < 2:
        return
    w = wds[1]
    if len(w) != 2:
        reportallafter(d,msg)
    if not w.isdigit():
        reportallafter(d,msg)
    if len(wds) < 3:
        return
    w = wds[2]
    if len(w) != 2:
        reportallafter(d,msg)
    if not w.isdigit():
        reportallafter(d,msg)
    return

def readfor(f):
    lall = f.readlines()
    path = False
    macos = False
    for n,l in enumerate(lall):
        l2 = l.strip()
        if len(l2) < 1:
            continue
        if l2[0] == "#":
            continue
        if l2.startswith("filepath: "):
            p=l2[10:]
            p2 = p.strip()
            if len(p2)  > 1:
                path = p2;
        if l2.startswith("macos:"):
            macos = True
    return path,macos
 
#   Reading the configure file for a full path
def readconf():
    ghome= os.getenv("HOME",None)
    if not ghome:
        print("No HOME env variable available to find searchgnucash.conf")
        return False,False
    confpath= os.path.join(ghome,"searchgnucash.conf")
    try:
        f= open(confpath,"r")
    except:
        print("Cannot open",confpath)
        return False,False
    if not f:
        print("Cannot open",confpath)
        return False,False
    path,macos= readfor(f)
    f.close()
    return path,macos 

if __name__ == "__main__":
    searchstr = False
    searchtermlist = []
    dateselected = False
    datetype = False 
    # Changed splits default 2020-02-09
    printallsplits = True
    printallafter = False
    onlytranslines = False
    accountselect = False
    printacctnames = False
    accountreport = False
    csvformat = False
    fname = False

    casesense = "n"
    ct = 1
    while int(ct) < len(sys.argv):
        v = sys.argv[ct]
        if v == "-h":
            usage("-h:")
        if v == "-csv":
            csvformat = True
        elif v == "-f":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-f")
            fname = sys.argv[ct]
        elif v == "-datetype":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-datetype")
            if len(sys.argv[ct]) >= 1:
                typed = sys.argv[ct]
                if typed == "posted":
                    datetype = typed
                elif typed == "entered":
                    datetype = typed
                elif typed == "both":
                    datetype = False
                else:
                    print("-datetype arg is ",typed, " which isnot allowed")
        elif v == "-case":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-case")
            if len(sys.argv[ct]) >= 1:
                icval = sys.argv[ct]
                if int(icval) == 0:
                    casesense = "n"
                else:
                    casesense = "y"
        elif v == "-onlytranslines":
            onlytranslines = "y"
        elif v == "-printacctnames":
            printacctnames = True
        elif v == "-accountreport":
            printallsplits = False
            accountreport = True
        elif v == "-accountselect":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-accountselect")
            accountselect = sys.argv[ct]
        elif v == "-allsplits":
            printallsplits = True
        elif v == "-allafter":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-allafter")
            if len(sys.argv[ct]) >= 1:
                printallafter = sys.argv[ct]
                validatedate(printallafter,"-allafter")
        elif v == "-d":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-d")
            if len(sys.argv[ct]) >= 1:
                dateselected = sys.argv[ct]
                validatedate(dateselected,"-d")
        elif v == "-s":
            ct = int(ct) + 1
            validateindex(ct, len(sys.argv), "-s")
            if len(sys.argv[ct]) >= 1:
                searchtermlist += [sys.argv[ct]]
        else:
            print("Got arg ", ct, sys.argv[ct])
            usage("Something wrong with args")
            sys.exit(1)
        ct = int(ct) + 1
    if not fname:
        fname,macos = readconf()
        if not fname:
            print("No file path provided to gnucashsearch.py.")
            print("Unable to continue.")
            sys.exit(1)
    #    sys.exit(1)
    st = searchterms(
        searchtermlist,
        dateselected,
        casesense,
        printallsplits,
        printallafter,
        onlytranslines,
        accountselect,
        printacctnames,
        accountreport,
        datetype,csvformat
    )
    st.stermsprint(fname)
    f = gzip.open(fname, "rb")
    content = f.read()
    f.close
    # Here we read the account data and do the searches
    # and print our findings, if any.
    getxml(content, 100, st)
    sys.exit(0)
