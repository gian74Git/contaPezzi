#!/usr/bin/env python
#!/usr/bin/env python
import tkinter as tk
from tkinter import *
import time
import os
import time
from time import sleep
import pymysql
import datetime
from datetime import timedelta

DEBUG = True
if (not DEBUG):
    CONST_DB = "letturePezziDB"
    import RPi.GPIO as GPIO

else:
    CONST_DB = "letturePezziDB"

CONST_DIM_CHAR_TITOLI = 90
CONST_DIM_CHAR_DATI = 120
CONST_TOT_GIORNALIERO = 403

#18
CONST_DIM_CHAR_ORARI = 34
    
class Application(tk.Frame):              
    numPzTotaleGiorn = 0
    numPzLettiGiorn = 0
    lLbOrari = []
    dateNow = datetime.datetime.now().strftime("%Y-%m-%d")
    datePassed = datetime.datetime.now().strftime("%Y-%m-%d")
    minutePassed = datetime.datetime.now().strftime("%M")
    totPrevistiNow = 0
    db = pymysql.connect("localhost", "root", "sardegna", CONST_DB)

    def __init__(self, master=None):        
        tk.Frame.__init__(self, master)
        self.parent = master
        self.createWidgets()                
        self.update_clock(True)

    def aggiornaColorePrevistiNow(self):
        if (self.totPrevistiNow > self.numPzLettiGiorn):
            lbTotFattoGiorn["bg"] = "red"
        else:
            lbTotFattoGiorn["bg"] = "green"

    def update_frame_orari(self):
        for child in frameOrari.winfo_children():
            child.destroy()

        lbOra = Label(frameOrari, text="Ora", font =("Helvetica", CONST_DIM_CHAR_ORARI))
        lbPrevisto = Label(frameOrari, text="Previsto", font =("Helvetica", CONST_DIM_CHAR_ORARI))
        lbFatti = Label(frameOrari, text="Fatti", font =("Helvetica", CONST_DIM_CHAR_ORARI))
        lbOra.grid(row=0, column=0, padx=10)
        lbPrevisto.grid(row=0, column=1, padx=10)
        lbFatti.grid(row=0, column=2, padx=10)

        # db = pymysql.connect("localhost", "root", "sardegna")
        cursor = self.db.cursor()
        cursor.execute("USE " + CONST_DB)

        currDate = datetime.datetime.now().strftime("%Y-%m-%d")
        #self.lLbOrari.clear()
        #Svuoto la lista. Il .clear vale solo da python3.4 in su.
        self.lLbOrari[:] = []
        lLbOrario = []
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM TOra_Orari order by tOraIni")
        rowOrario = cursor.fetchone()
        iRow = 0
        while rowOrario is not None:
            iPrevistoOra = rowOrario[3]
            iRow += 1
            tmDa = datetime.datetime.strptime(rowOrario[1].__str__(), "%H:%M:%S").strftime("%H:%M")
            tmA = datetime.datetime.strptime(rowOrario[2].__str__(), "%H:%M:%S").strftime("%H:%M")
            lLbOrario.append(Label(frameOrari, text = tmDa + " - " + tmA, font = ("Helvetica", CONST_DIM_CHAR_ORARI)))
            if iPrevistoOra is not None:
                sPrevistoOra = "%d" %iPrevistoOra
            else:
                sPrevistoOra = ""
                iPrevistoOra = 0

            lLbOrario.append(Label(frameOrari, text=sPrevistoOra, font = ("Helvetica", CONST_DIM_CHAR_ORARI)))

            curLett = self.db.cursor()
            sQryTmp = "SELECT iLetNumProg FROM TLet_Letture WHERE dLetDataLettura = '%s' and tLetOraIni >= '%s' and tLetOraFine <= '%s'" %(currDate, tmDa, tmA)
            curLett.execute(sQryTmp)
            rowTotXOra = curLett.fetchone()
            iTotPerOra = 0
            if rowTotXOra != None:
                iTotPerOra = rowTotXOra[0]
                totLett = self.db.cursor()
                sQryTmp = "SELECT Sum(iLetNumProg) FROM TLet_Letture WHERE dLetDataLettura = '%s'" %(currDate)
                totLett.execute(sQryTmp)
                self.numPzLettiGiorn = totLett.fetchone()[0]
                totLett.close()
                #self.numPzLettiGiorn = self.numPzLettiGiorn + iTotPerOra

            if (iTotPerOra < iPrevistoOra):
                bgColor = "red"
            else:
                bgColor = "green"

            lLbOrario.append(Label(frameOrari, text = iTotPerOra, bg=bgColor, font = ("Helvetica", 18)))
            self.lLbOrari.append("idOra=%s" %rowOrario[0])
            self.lLbOrari.append([lLbOrario, tmDa, tmA, iTotPerOra, iPrevistoOra])

            self.lLbOrari[-1][0][0].grid(row=iRow, column = 0)
            self.lLbOrari[-1][0][1].grid(row=iRow, column = 1)
            self.lLbOrari[-1][0][2].grid(row=iRow, column = 2, sticky=W+E+N+S)

            lLbOrario = []
            rowOrario = cursor.fetchone()
            curLett.close()

        self.db.commit()
        cursor.close()

    def update_tot_previsto(self, always=False):
        self.minuteNow = datetime.datetime.now().strftime("%M")
        if ((self.minuteNow != self.minutePassed) | (always)):
            self.minutePassed = datetime.datetime.now().strftime("%M")
            # db = pymysql.connect("localhost", "root", "sardegna", CONST_DB)
            cursor = self.db.cursor()
            now = datetime.datetime.now() - timedelta(hours=1)
            oldTime = now.strftime('%H:%M:%S')
            currTime = datetime.datetime.now().strftime('%H:%M:%S')

            sQry = "SELECT sum(fOraTotPezzi) FROM TOra_Orari WHERE tOraIni < '%s'" %oldTime
            cursor.execute(sQry)
            totPrec = cursor.fetchone()

            sQry = "SELECT fOraTotPezzi FROM TOra_Orari WHERE (tOraIni <= '%s') and (tOraFine > '%s') " %(currTime, currTime)
            cursor.execute(sQry)
            prevNow = cursor.fetchone()
            if (prevNow != None):
                totActual = (prevNow[0] * float(self.minutePassed)) // 60.0

                if (totPrec != None):
                    #  Nel caso della prima ora, non leggo nulla quindi assumo 0 come totPrec (totale ora precedente)
                    if (totPrec[0] != None):
                        self.totPrevistiNow = totPrec[0] + totActual
                    else:
                        self.totPrevistiNow = totActual
                    lbTotPrevisto["text"] = "%d" %(self.totPrevistiNow)

                    self.aggiornaColorePrevistiNow()
            else:
                lbTotPrevisto["text"] = "0"

            cursor.close()
            self.update_frame_orari()



    def update_clock(self, firstLaunch=False):
        self.dateNow = datetime.datetime.now().strftime("%Y-%m-%d")
        self.update_tot_previsto()

        #Cambio di data: reinizializza! 
        if (self.dateNow != self.datePassed) | (firstLaunch):
            self.datePassed = datetime.datetime.now().strftime("%Y-%m-%d")
            edNumPezzi.delete(0, 1000)
            edNumPezzi.insert(0, "0")
            labelDate["text"] = "%s" %datetime.datetime.now().strftime('%d/%m/%Y')

            self.initDatiDB()

            # db = pymysql.connect("localhost", "root", "sardegna")
            cursor = self.db.cursor()
            cursor.execute("USE %s" %CONST_DB)
            sQry = "SELECT iTimQta FROM TTim_TotaleImpostati WHERE dTimData = '%s'" %datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute(sQry)
            row = cursor.fetchone()
            if (row != None):
                self.numPzTotaleGiorn = row[0]
            else:
                self.numPzTotaleGiorn = CONST_TOT_GIORNALIERO
            cursor.close()
            # db.close()
            self.internalImposta()
            lbTotGiorn["text"] = "%d" %self.numPzTotaleGiorn 
            
            if (not firstLaunch):
                self.numPzLettiGiorn = 0
                lbTotFattoGiorn["text"] = "%d" %self.numPzLettiGiorn
                for listaLabel in self.lLbOrari:
                    if (type(listaLabel) == list):
                        #Azzeramento del contatore correlato.
                        listaLabel[3] = 0

                        bgColor = "red"
                        listaLabel[0][2]["text"] = 0
                        listaLabel[0][2]["bg"] = bgColor
            self.aggiornaColorePrevistiNow()

        self.schiacciaBottone()     

            

    def schiacciaBottone(self):  
        if (not DEBUG):
            if GPIO.input(3) == False:                
                self.scriviLettura()
                self.aggiornaColorePrevistiNow()
                while GPIO.input(3) == False:
                    time.sleep(2)
        self.after(1, self.update_clock)
        
        
    def btnTestClick(self):
        self.scriviLettura()            
    
    def internalImposta(self):
        # db = pymysql.connect("localhost", "root", "sardegna")
        cursor = self.db.cursor()
        cursor.execute("USE %s" %CONST_DB)
        sQry = "SELECT iTimId FROM TTim_TotaleImpostati WHERE dTimData = '%s'" %datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute(sQry)
        row = cursor.fetchone()
        if (row != None):
            sQry = "update TTim_TotaleImpostati set iTimQta = %d where iTimId = %d" %(self.numPzTotaleGiorn, row[0])
        else:
            sQry = "insert into TTim_TotaleImpostati set dTimData = '%s', iTimQta = %d" %(datetime.datetime.now().strftime("%Y-%m-%d"), self.numPzTotaleGiorn)
        cursor.execute(sQry)

        sQry = "SELECT count(*) FROM TOra_Orari order by tOraIni"
        cursor.execute(sQry)            
        iTotOre = int(cursor.fetchone()[0])

        self.iPrevistoOra = int(self.numPzTotaleGiorn / iTotOre)      

        for listaLabel in self.lLbOrari:
            if (type(listaLabel) == list):
                #listaLabel[0][1]["text"] = "%d" %self.iPrevistoOra                
                iTotPrevXOra = listaLabel[4]
                if (int(listaLabel[0][2]["text"]) < iTotPrevXOra):
                    bgColor = "red"
                else:
                    bgColor = "green"
                listaLabel[0][2]["bg"] = bgColor
    
        cursor.close()
        self.db.commit()
        # db.close()
    
    def enterKeyPress(self, event):
        self.btnImpostaClick()
        
    def btnImpostaClick(self):
        sNumPz = edNumPezzi.get()
        if (sNumPz != ""):
            self.numPzTotaleGiorn = int(edNumPezzi.get())
            lbTotGiorn["text"] = "%d" %self.numPzTotaleGiorn 
            self.internalImposta()


    def initDatiDB(self):
        # db = pymysql.connect("localhost", "root", "sardegna")
        cursor = self.db.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS " + CONST_DB)
        cursor.execute("USE " + CONST_DB)
        cursor.execute("""CREATE TABLE IF NOT EXISTS `TLet_Letture` (
          `iLetId` int(11) NOT NULL AUTO_INCREMENT,
          `sLetNote` varchar(200) NOT NULL,
          `dLetDataLettura` date NOT NULL DEFAULT '0000-00-00',
          `tLetOraIni` time NOT NULL,
          `tLetOraFine` time NOT NULL,
          `iLetNumProg` int(11) NOT NULL,
          PRIMARY KEY (`iLetId`)
        ) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS `TOra_Orari` (
          `iOraId` int(11) NOT NULL AUTO_INCREMENT,
          `tOraIni` time NOT NULL,
          `tOraFine` time NOT NULL,
          PRIMARY KEY (`iOraId`)
          ) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS `TTim_TotaleImpostati` (
          `iTimId` int(11) NOT NULL AUTO_INCREMENT,
          `dTimData` date NOT NULL,
          `iTimQta` int(11) NOT NULL,
          PRIMARY KEY (`iTimId`)
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1""")

        sQry = "SELECT iTimQta FROM TTim_TotaleImpostati WHERE dTimData = '%s'" %datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute(sQry)
        row = cursor.fetchone()
        if (row != None):
            self.numPzTotaleGiorn = int(row[0])
            sQry = "SELECT count(*) FROM TOra_Orari order by tOraIni"
            cursor.execute(sQry)
            iTotOre = int(cursor.fetchone()[0])
            self.iPrevistoOra = int(self.numPzTotaleGiorn / iTotOre)

        self.db.commit()
        cursor.close()
        # db.close()
        
    def createWidgets(self):
        self.initDatiDB()
        currDate = datetime.datetime.now().strftime("%Y-%m-%d")
        self.parent.title("Contatore pezzi ...")
        frame = Frame(self, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand = 1)
        self.pack(fill=BOTH, expand = 1)

        #**********   DEFINIZIONE FRAMES   ***********
        frameTop = Frame(frame, relief=RAISED, borderwidth=1)
        frameTop.pack(fill=X, side=TOP)
        labelTitle = Label(frameTop, text="VIST TECH", font=("Helvetica", 24))
        labelTitle.pack(side = TOP)

        global labelDate
        labelDate = Label(frameTop, text="%s" %datetime.datetime.now().strftime('%d/%m/%Y'), font = ("Helvetica", 24))
        labelDate.pack(side = LEFT)
                
        frameLeft = Frame(frame, relief=RAISED, borderwidth=1)
        frameLeft.pack(fill=BOTH, expand=1, side=LEFT)


        global frameRight
        frameRight = Frame(frame, relief=RAISED, borderwidth=1)
        frameRight.pack(fill=BOTH, expand=1, side=RIGHT)

        global frameOrari
        frameOrari = Frame(frameRight, relief=RAISED, borderwidth=1)
        frameOrari.pack(fill=Y, side=RIGHT)

        frameRightTop = Frame(frameRight, relief=RAISED, borderwidth=1)
        frameRightTop.pack(fill=BOTH, expand=1, side=TOP)

        #**********   DEFINIZIONE FRAMES   ***********
        self.update_frame_orari()

        #**********        PREVISTO        ***********
        lbPrevisto = Label(frameLeft, text="Previsto", font=("Helvetica", CONST_DIM_CHAR_TITOLI))
        lbPrevisto.pack(side=TOP)

        global lbTotPrevisto
        lbTotPrevisto = Label(frameLeft, text="0", font=("Helvetica", CONST_DIM_CHAR_TITOLI))
        lbTotPrevisto.pack(side=LEFT, fill=X, expand=1)
        #**********        PREVISTO        ***********

        #**********   TOTALE GIORNALIERO   ***********
        lbGiornaliero = Label(frameRight, text="Giornaliero", font=("Helvetica", CONST_DIM_CHAR_TITOLI))
        lbGiornaliero.pack(side=TOP)
                
        global lbTotGiorn
        lbTotGiorn = Label(frameRight, text="0", font=("Helvetica", CONST_DIM_CHAR_DATI))
        lbTotGiorn.pack(side=LEFT, fill=X, expand=1)
        lbTotGiorn["text"] = "%d" %self.numPzTotaleGiorn
        #**********   TOTALE GIORNALIERO   ***********

        #**********   FATTO GIORNALIERO   ***********
        lbFattoGiorn = Label(frameRightTop, text="Fatto", font=("Helvetica", CONST_DIM_CHAR_TITOLI))
        lbFattoGiorn.pack(side=TOP)
         
        global lbTotFattoGiorn
        lbTotFattoGiorn = Label(frameRightTop, text="%d" %self.numPzLettiGiorn, font=("Helvetica", CONST_DIM_CHAR_DATI))
        lbTotFattoGiorn.pack(side=LEFT, fill=X, expand=1)
        self.update_tot_previsto(True)
        #**********   FATTO GIORNALIERO   ***********

        frameBT = Frame(self, borderwidth=1)
        frameBT.pack(side=BOTTOM, fill=X)

        lbNote = Label(frameBT, text="Note:")
        lbNote.pack(side=LEFT)

        global edNote
        edNote = Entry(frameBT, width=400)
        edNote.pack(side=LEFT, fill=X)        
                
        closeButton = Button(self, text = "Chiudi", command=self.quit)
        closeButton.pack(side=RIGHT, padx=5, pady=5)
        if (DEBUG):
            btnTest = Button(self, text = "Test", command=self.btnTestClick)
            btnTest.pack(side=RIGHT)
        
        global btnImposta
        btnImposta = Button(self, text = "Imposta", command=self.btnImpostaClick)
        btnImposta.pack(side=RIGHT)

        global edNumPezzi
        edNumPezzi = Entry(self)
        edNumPezzi.focus()
        edNumPezzi.bind('<Return>', self.enterKeyPress)
        edNumPezzi.pack(side=RIGHT)        

        lbNumPzStart = Label(self, text="Num. pezzi partenza:")
        lbNumPzStart.pack(side=RIGHT)
                                
    def scriviLettura(self):
        # db = pymysql.connect("localhost", "root", "sardegna", CONST_DB)
        cursor = self.db.cursor()
        
        currDate = datetime.datetime.now().strftime('%Y-%m-%d')
        currTime = datetime.datetime.now().strftime('%H:%M:%S')

        #Se trovo gli orari nella tabella relativi all'ora di passaggio prosegui altrimenti non faccio nulla!
        sQry = "SELECT iOraId, tOraIni, tOrafine FROM TOra_Orari WHERE tOraIni <= '%s' and tOraFine >= '%s'" %(currTime, currTime)
        cursor.execute(sQry)
        rowOrari = cursor.fetchone()
        if (rowOrari != None):
            iIndexLista = self.lLbOrari.index("idOra=%s" %rowOrari[0]) + 1
            if (iIndexLista >= 1):
                iNewValue = self.lLbOrari[iIndexLista][3] + 1                
                self.lLbOrari[iIndexLista][3] = iNewValue
                sQry = "SELECT iLetId FROM TLet_Letture WHERE dLetDataLettura = '%s' and tLetOraini <= '%s' and tLetOraFine >= '%s'" %(currDate, currTime, currTime)
                cursor.execute(sQry)
                
                
                rowLetture = cursor.fetchone()
                iLetId = 0
                if (rowLetture != None):
                    iLetId = rowLetture[0]
                if (iLetId != 0):
                    sQry = "update TLet_Letture set iLetNumProg = %d, sLetNote = '%s' where iLetId = %d" %(iNewValue, edNote.get(), iLetId)
                else:
                    sQry = "insert into TLet_Letture set dLetDataLettura = '%s', sLetNote = '%s', tLetOraini = '%s', tLetOraFine = '%s', iLetNumProg = %d" %(currDate, edNote.get(), rowOrari[1], rowOrari[2], iNewValue)

                cursor.execute(sQry)
                self.lLbOrari[iIndexLista][0][2]["text"] = "%d" %iNewValue
                iTotPrevXOra = self.lLbOrari[iIndexLista][4]
                if (iNewValue < iTotPrevXOra):
                    self.lLbOrari[iIndexLista][0][2]["bg"] = "red"
                else:
                    self.lLbOrari[iIndexLista][0][2]["bg"] = "green"
                self.numPzLettiGiorn = self.numPzLettiGiorn + 1
                lbTotFattoGiorn["text"] = "%d" %self.numPzLettiGiorn
                self.aggiornaColorePrevistiNow()
                
            
        self.db.commit()
        cursor.close()
        #db.close()


if (not DEBUG):
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(3, GPIO.IN)

root = Tk()
w = root.winfo_screenwidth()
h = root.winfo_screenheight() - 60
sSize = "%dx%d+0+0" % (w,h)
root.geometry(sSize)
#root.geometry("800x600+300+300")
app = Application(root)

app.mainloop()
app.db.close()
#app.destroy()
