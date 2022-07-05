#!/usr/bin/env python3
import sys
import os
import socket
from datetime import datetime,date,time
from time import sleep
import subprocess
from fpdf import FPDF 
import tkinter as tk
from tkinter import ttk

#This is the GUI app. The command line
# version is searchgnucash.py

# Source is q3:/home/davea/misc/cash/searchcash.py
# The values here useful
# for passing to scan and/or scanaddpage
# Geometry is width x height
mygeom="1000x950"
testing = False
macos=False

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
        return False
    confpath= os.path.join(ghome,"searchgnucash.conf")
    try:
        f= open(confpath,"r")
    except:
        print("Cannot open",confpath);
        return False;
    if not f:
        print("Cannot open",confpath);
        return False;
    s,macos= readfor(f)
    f.close()
    return s,macos

hostname = socket.gethostname()
ghome    = os.getenv("HOME",None)
path,macos = readconf()
# Milliseconds
afterwaittime=10000
watchloopcount = 0
targetdir = ''

def findreturnedname(term,sa):
    global sclog
    if sa.find(term) == -1:
        print("backup: unknown return A  looking for",\
            term,sa,curtime(),flush=True,file=sclog)
        return None
    sb = sa.split()
    # We do not assume the string has just the desired 
    # but allow for extra words before (likely debug trash)
    # term likely has leading/trailing space, and after
    # split we do not want those spaces.
    termalone = term.strip()
    for i,s in enumerate(sb):
        if s == termalone:
            if len(sb) == int(i+1):
                # ends with term string? Odd. 
                break
            curpdfname = sb[i+1]
            return curpdfname
    print("backup: unknown return C looking for",\
        term,sa,curtime(),flush=True,file=sclog)
    return None

def curtime():
    dt=datetime.now()
    tm=dt.strftime("%Y-%m-%d %H:%M")
    return tm

def curtimefile():
    dt=datetime.now()
    tm=dt.strftime("%Y-%m-%d-%H-%M-%S")
    v = ''.join(["search-",tm,".pdf"])
    return v

if not ghome:
    print("backup Failed as HOME environment variable missing ",\
        logname)
    sys.exit(1)
global sclog
try:
    logname = "/var/tmp/searchcash.log"
    sclog = open(logname,"a")
except:
    print("backup Failed log open ", logname)
    sys.exit(1)

def quotewrap(s):
    s2 = ''.join(['"',s,'"'])
    return sr2

# ASSERT:
# Already leading trailing spaces removed.
def argquote(s):
    if s.find(" ") == -1:
        #No quoting needed
        return s
    if s.find("'") == -1:
        s2 = ''.join(["'",s,"'"])
        return s2
    if s.find('"') == -1:
        return quotewrap(s)
    s3 = s.strip('"')
    return quotewrap(s3)

def validateposted(s):
    sl = s.lower()
    if sl == "posted":
        return True
    if sl == "paid":
        return True
    if sl == "entered":
        return True
    return False

def validdate(value):
    d = value
    #print("dadebug validdate ",d)
    if len(d) == 0:
        print("Return TRUE value length 0");
        return True
    wds=str(d).split("-")
    if len(wds) > 3:
        return False
    m=None
    d=None
    y = wds[0]
    if not y.isdigit():
         return False
    if int(y) < 1700:
         return False
    if int(y) > 2100:
         return False
    if len(wds) > 1:
        m = wds[1]
        if not m.isdigit():
            return False
        if int(m) < 0:
            return False
        if int(m) > 12:
            return False
    if len(wds) > 2:
        d = wds[2]
        if not d.isdigit():
            return False
        if int(d) < 0:
            return False
        if int(d) > 32:
            return False
    return True

class Application(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()                   
        self.createWidgets()

    def createWidgets(self):
        tkrow=0
        cspan=4

        self.btstyle = ttk.Style()
        self.btstyle.configure('TButton', font=('Helvetica', 16))
        self.ltstyle = ttk.Style()
        self.ltstyle.configure('TLabel', font=('Helvetica', 16))

        # other states: "running" (search running)
        # and "done" (only quit clickable)
        self.state = "starting"
        self.backupproc = False
        self.starttime = datetime.today()

        self.title = ttk.Label(self,style='TLabel')
        ti = "%s: Search GnuCash"%(hostname)
        self.title["text"] = ti
        self.title.grid(row=tkrow,columnspan=cspan)
        tkrow += 1

        self.blanklabel3 = ttk.Label(self,style='TLabel')
        self.blanklabel3["text"] = "Ready to start a search."
        self.blanklabel3.grid(row=tkrow,columnspan=cspan)
        tkrow += 1

        self.blanklabel2 = ttk.Label(self,style='TLabel')
        t = "Search terms should each be a single word\n" +\
            "or any part of a single word."
        self.blanklabel2["text"] = t;
        self.blanklabel2.grid(row=tkrow,columnspan=cspan)
        tkrow += 1
  
        self.search1label = ttk.Label(self,style='TLabel')
        self.search1label["text"] = "Require"
        self.search1label.grid(row=tkrow,column=2,sticky="w")
  
        self.search1var = tk.StringVar()
        self.search1var = ''
        self.search1entry = ttk.Entry(self,textvariable=self.search1var)
        self.search1entry.grid(row=tkrow,column=3,sticky='w')
        tkrow += 1
  
        self.search2label = ttk.Label(self,style='TLabel')
        self.search2label["text"] = "and Require"
        self.search2label.grid(row=tkrow,column=2,sticky='w')
  
        self.search2var = tk.StringVar()
        self.search2var = ''
        self.search2entry = ttk.Entry(self,textvariable=self.search2var)
        self.search2entry.grid(row=tkrow,column=3,sticky="w")
        tkrow += 1
  
        self.search3label = ttk.Label(self,style='TLabel')
        self.search3label["text"] = "and Require"
        self.search3label.grid(row=tkrow,column=2,sticky="w")

        self.search3var = tk.StringVar()
        self.search3var = ''
        self.search3entry = ttk.Entry(self,textvariable=self.search3var)
        self.search3entry.grid(row=tkrow,column=3,sticky="w")
        tkrow += 1

        self.caselabel = ttk.Label(self,style='TLabel')
        self.caselabel["text"] = "Case is ignored"
        self.caselabel.grid(row=tkrow,column=2,sticky="w")
        self.casevar=0
        self.casebutton = ttk.Checkbutton(self,\
            text="Click to Match Case ",command=self.docase,\
            variable=self.casevar,style="TButton")
        self.casebutton.grid(row=tkrow,column=3,sticky="w")
        self.casebutton.invoke()
        self.casebutton.invoke()
        tkrow += 1

        self.casexlabel = ttk.Label(self,style='TLabel')
        t =  ''.join([\
            "A Standard report shows transaction lines and ",
            "split lines.\n",
            "The limited format only shows split lines ",
            "but shows\nthe transaction description and ",
            "dates (p: and e:)",
            " on the same line.\n",
            "Limited reports also show ",
            "subtotals by month and year"])
        self.casexlabel["text"] = t
        self.casexlabel.grid(row=tkrow,columnspan=cspan,sticky='news')
        tkrow += 1

        self.casearlabel = ttk.Label(self,style='TLabel')
        self.casearlabel["text"] = "Default is Std Rep"
        self.casearlabel.grid(row=tkrow,column=2,sticky="w")
        self.casearvar=0
        self.casearbutton = ttk.Checkbutton(self,\
            text="Click to Match Case ",command=self.acctrep,\
            variable=self.casearvar,style="TButton")
        self.casearbutton.grid(row=tkrow,column=3,sticky="w")
        self.casearbutton.invoke()
        self.casearbutton.invoke()
        tkrow += 1

        self.case2label = ttk.Label(self,style='TLabel')
        t =  ''.join([\
            "Choose a Date: The following field lets one enter a ",
            "partial or fulldate.\nThus restricting the",
            " results to the (partial or full) date.\nExamples:\n",
            "Type 2019 to restrict to just that year.\n",
            "Type 2018-09 to restrict results to September ",
            "2018.\nType 2020-01-09 to restrict results to",
            " Jan 9, 2020."])
        self.case2label["text"] = t
        self.case2label.grid(row=tkrow,columnspan=cspan,sticky='news')
        tkrow += 1

        self.selectdatestr = tk.StringVar()
        self.selectdatestr = ''
        self.selectdate = ttk.Entry(self,\
            textvariable=self.selectdatestr)
        self.selectdate.grid(row=tkrow,column=3,sticky='w')
        tkrow += 1

        self.case3label = ttk.Label(self,style='TLabel')
        t = ''.join([\
            "AllAfter Date:The following field lets one enter",
            " a partial or fulldate.\nIt restricts results to",
            " dates matching and after the date entered.\n",
            "Dates in the same format as the above field.\n",
            "Enter either a Choose or an AllAfter date, not both."])
        self.case3label["text"] = t
        self.case3label.grid(row=tkrow,columnspan=cspan,sticky='news')
        tkrow += 1

        self.selectafterstr = tk.StringVar()
        self.selectafterstr = ''
        self.selectafter = ttk.Entry(self,\
            textvariable=self.selectafterstr)
        self.selectafter.grid(row=tkrow,column=3,sticky='w')
        tkrow += 1

        # choose both, posted (paid), or entered
        self.postedlabel=ttk.Label(self,style='TLabel')
        t = ''.join([\
            "DateToUse:The following field lets one enter",
            " either 'posted'\n", 
            "(date paid) or 'entered' (record entry)"
            " for date comparisons\n",
            "Leave blank to allow either date (meaning if either",
            "passes a date\ncheck",
            " the record may appear)"])
        self.postedlabel["text"] = t
        self.postedlabel.grid(row=tkrow,columnspan=cspan,sticky='news')
        tkrow += 1

        self.selectposted = tk.StringVar()
        self.selectposted = ''
        self.selectposted = ttk.Entry(self,\
            textvariable=self.selectposted)
        self.selectposted.grid(row=tkrow,column=3,sticky='w')
        tkrow += 1
     
        # Select account name
        self.accountnamelabel=ttk.Label(self,style='TLabel')
        t = ''.join([\
            "Account:The following field lets one enter",
            " an account name\n",
            "(such as Charity) restricting the report"
            " to one account.\n"])
        self.accountnamelabel["text"] = t
        self.accountnamelabel.grid(row=tkrow,columnspan=cspan,\
            sticky='news')
        tkrow += 1

        self.selectaccountname = tk.StringVar()
        self.selectaccountname = ''
        self.selectaccountname = ttk.Entry(self,\
            textvariable=self.selectaccountname)
        self.selectaccountname.grid(row=tkrow,column=3,sticky='w')
        tkrow += 1


        self.quit = ttk.Button(self, text='Quit',
            command=self.cleanupdestroy,style='TButton')
        self.quit.grid(row=tkrow,column=0,padx=9,pady=9,sticky=tk.S)

        self.srch = ttk.Button(self, text='Search',
            command=self.search,style='TButton')
        self.srch.grid(row=tkrow,column=2,padx=9,pady=9,sticky=tk.S)
        tkrow += 1
        self.quit.state(["!disabled"]) 
        self.srch.state(["!disabled"]) 
        self.status = ttk.Label(self,text= "     ",style='TLabel')
        self.status.grid(row=tkrow,columnspan=cspan)
      
    def acctrep(self):
        if self.casearvar == 0:
            self.casearvar = 1
            self.casearbutton["text"] = "Click for standard report"
            self.casearlabel["text"] = "Short Report format"
        else:
            self.casearvar = 0
            self.casearbutton["text"] = "Click to limit report"
            self.casearlabel["text"] = "Standard report format"
    def docase(self):
        if self.casevar == 0:
            self.casevar = 1
            self.casebutton["text"] = "Click to Ignore case"
            self.caselabel["text"] = "Case matters"
        else:
            self.casevar = 0
            self.casebutton["text"] = "Click to Match case"
            self.caselabel["text"] = "Case ignored"

    def search(self):
        global sclog
        global targetdir
        self.starttime = datetime.today()
        self.blanklabel2["text"]=" "
        self.status.configure(text=" ")
        #print("dadebugsearch: ",curtime())
        print("search: starting",curtime(),flush=True,file=sclog)
        #print("search: starting");
        cmd = os.path.join(ghome,"bin/searchgnucash")
  
        self.blanklabel3.configure(text=' ')
        self.status.configure(text="Starting search")
  
        # We must quote multi-word args for macos as we must
        # reduce to a string there for the shell.
        # Yet must not add quotes on Linux as there is no
        # shell to strip them off and nothing matches!
        # ugh.
        cmd3=[cmd]
        cmd4=[cmd]
        if self.search1entry.get() and\
            len(self.search1entry.get()) > 0:
            cmd3 += ["-s"] 
            cmd3 += [self.search1entry.get().strip()] 
            cmd4 += ["-s"] 
            cmd4 += [argquote(self.search1entry.get().strip())] 
        if self.search2entry.get() and\
            len(self.search2entry.get()) > 0:
            cmd3 += ["-s"]
            cmd3 += [self.search2entry.get().strip()] 
            cmd4 += ["-s"]
            cmd4 += [argquote(self.search2entry.get().strip())] 
        if self.search2entry.get() and\
            len(self.search3entry.get()) > 0:
            cmd3 += ["-s"]
            cmd3 += [self.search3entry.get().strip()] 
            cmd4 += ["-s"]
            cmd4 += [argquote(self.search3entry.get().strip())] 
        cmd3 += ["-case"]
        cmd4 += ["-case"]
        cmd3 += [str(self.casevar).strip()] 
        cmd4 += [str(self.casevar).strip()] 
     
        stdrep = str(self.casevar).strip()
        if stdrep == "1":
            cmd3 += ["-accountreport"]
            cmd4 += ["-accountreport"]
        # Add nothing for standard report format
        

        da = self.selectafter.get().strip()
        if len(da) > 0:
             ok=validdate(da)
             if not ok:
                 print("search: Invalid after-date :",da,\
                   flush=True,file=sclog)
                 self.status.configure(text="Invalid After Date!")
                 return
        db = self.selectdate.get().strip()
        #print("dadebug datestr: ",db)
        if len(db) > 0:
            ok=validdate(db)
            if not ok:
                print("search: Invalid Date Selected :",db,\
                    flush=True,file=sclog)
                self.status.configure(text="Invalid Chosen Date!")
                return
        if db and len(db) > 0:
            cmd3 += ["-d"]
            cmd3 += [db]
            cmd4 += ["-d"]
            cmd4 += [db]
        else:
            if da  and len(da) > 0:
                cmd3 += ["-allafter"]
                cmd3 += [da]
                cmd4+= ["-allafter"]
                cmd4 += [da]

        dc = self.selectposted.get().strip()
        if len(dc) > 0:
            ok = validateposted(dc)
            if not ok:
                print("search: posted/entered selected :",db,\
                    flush=True,file=sclog)
                self.status.configure(text="Invalid, neither posted nor entered !")
                return
        if dc and len(dc) > 0:
            cmd3 += ["-datetype"]
            cmd3 += [dc]
            cmd4 += ["-datetype"]
            cmd4 += [dc]

        dd = self.selectaccountname.get().strip()
        if dd and len(dd) > 0:
            cmd3 += ["-accountselect"]
            cmd3 += [dd]
            cmd4 += ["-accountselect"]
            cmd4 += [dd]


        #print("dadebug cmd3 ", cmd3)
        #print("dadebug cmd4 ", cmd3)
        expandedcmd =  ' '.join(cmd4)
        self.state = "running"
        print("search: starts now ",cmd3,"  at ",curtime(),\
            flush=True,file=sclog)
        try:
            if macos:
                self.backupproc = subprocess.Popen(expandedcmd,\
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\
                    universal_newlines = True,shell=True)
            else:
                self.backupproc = subprocess.Popen(cmd3,\
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\
                    universal_newlines = True)
        except subprocess.TimeoutExpired as message:
            print("TimeoutExpired at Popen ,maybe dead: ",\
                quotewrap(expandedcmd),message,curtime(),\
                flush=True,file=sclog)
            sys.exit(1)
        except subprocess.CalledProcessError as message:
            print("CalledProcesserror at Popen ,maybe dead: ",\
                quotewrap(expandedcmd),message,curtime(),\
                flush=True,file=sclog)
            sys.exit(1)
        except:
            print("Error in subprocess at Popen ,maybe dead: ",\
                quotewrap(expandedcmd),curtime(),flush=True,file=sclog)
            sys.exit(1)
  
        self.quit.state(["disabled"]) 
        self.srch.state(["disabled"]) 
        self.after(afterwaittime,self.watchsearch)
        return

    def secondsonly(self,mins,minstr):
      sofar = "Run time so far: %s minutes"%(minstr)
      if int(mins) == 1:
        sofar = "Run time so far: %s minute"%(minstr)
      return sofar

    def minutesonly(self,mins,minstr):
        sofar = "Run time so far: %s minutes"%(minstr)
        if int(mins) == 1:
            sofar = "Run time so far: %s minute"%(minstr)
        return sofar

    def writetopdf(self,textlines):
        path = os.path.join(ghome,"Desktop",curtimefile())
        pdf = FPDF()    
        pdf.add_page() 
        # Make second arg "B" for bold. Want a fixed-width font.
        pdf.set_font("Courier","B", size = 12) 
        for x in textlines: 
            pdf.cell(100,8, txt = x.rstrip(), ln = 1, align = 'L') 
        pdf.output(path)

    def watchsearch(self):
        global targetdir
        nowtime = datetime.today()
        kbval = 0.0
        dt = nowtime - self.starttime
        secs = dt.total_seconds()
        mins = int(secs+30)/60
        minstr = str(int(mins))
        secstr = str(int(secs))
        m= "Searchtime so far: %d seconds"%(int(secs))
        self.status.configure(text=m)
        if  not self.backupproc:
            # serious error
            print("backup: impossible error, no backupproc", \
                curtime(),flush=True,file=sclog)
            sys.exit(1)
        if  self.backupproc.poll() == None:
            global watchloopcount
            # loop again,
            if (watchloopcount%10) == 0:
                print("backup: watchsearch loop ",\
                    watchloopcount,".",\
                    curtime(),flush=True,file=sclog)
            self.after(afterwaittime,self.watchsearch)
            watchloopcount = int(watchloopcount) +1
            return
        (s2,errors) = self.backupproc.communicate()
        if errors != '':
            # serious error?
            print("backup: tar messages on stderr? ", \
                curtime(),flush=True,file=sclog)
            print("backup: stderr msgs ", \
                errors,curtime(),flush=True,file=sclog)
        slines = s2.split("\n")
        self.writetopdf(slines)
        self.state = "Ready to Search"
  
        m="Ready for another Search"
        self.status.configure(text=m)
        self.blanklabel2.configure(text="Ready for another search")
        self.quit.state(["!disabled"]) 
        self.srch.state(["!disabled"]) 
  
    def waitonquit(self):
        self.after(afterwaittime,self.waitonquit)
        return

    def cleanupdestroy(self):
        root.destroy()

i = 1
while i < len(sys.argv):
  v = sys.argv[i]
  if v == "-testing":
      i = int(i) +1
      testing = True
  i = int(i) +1

root = tk.Tk()
root.title("Search Gnu Cash")
root.geometry(mygeom)
q3host="q3"
app = Application(master=root)                   
app.mainloop()                      
