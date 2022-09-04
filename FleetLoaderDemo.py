import requests, json
import pandas as pd
import tkinter as tk
from tkinter import *
from tkinter import  filedialog as tkFileDialog
from tkinter import scrolledtext
from tkinter.ttk import Progressbar
from tkinter import ttk
from tkinter import simpledialog

BaseURL = r'http://site/cityworks'
UserName = r'username'
Password = r'pasword'
FuelFile = r'C:\fuel.csv'
PartsFile = r'C:\Projects 2\IBS Integration\Transactions June 2022 Testing 2.xlsx'
BillDate = r'01/01/1901'
ValidationList = ['Transaction Date','Transaction Time','Custom Vehicle/Asset ID','VIN', "Current Odometer","Units","Transaction Date","Product","Product Description","Net Cost", "Custom Vehicle/Asset ID"]
ValidationList2 = ['INVOICE NUMBER','INVOICE DATE','LINE ABBREV','PART NUMBER', "DESCRIPTION","QUANTITY SOLD","NET PRICE","EXTENDED PRICE","PO NUMBER", "ATTENTION"]
AcctDict = {"BOX":"PARTS","CARD":"PARTS","EACH":"PARTS","FOOT":"PARTS","GAL":"FLUIDS","PAIR":"PARTS", "QT":"FLUIDS", "FL":"FLUIDS"}
FuelSupplierSID = "24947"
PartsSupplierSID = "25024"
DTBL = None
Token = None


def Messenger(Message):
    txt1.configure(state ='normal')
    txt1.insert(END, Message+'\n')
    txt1.see(END)
    txt1.configure(state ='disabled')
    window.update()

def Messenger2(Message):
    txt14.configure(state ='normal')
    txt14.insert(END, Message+'\n')
    txt14.see(END)
    txt14.configure(state ='disabled')
    window.update()

def PercentEncoder(String):
    s = String.replace('"','\\"').replace('%', '%25').replace(' ', '%20').replace('!', '%21').replace('#', '%23').replace('$', '%24').replace('&', '%26').replace("'", '%27').replace('(', '%28').replace(')', '%29').replace('*', '%2A').replace('+', '%2B').replace('/', '%2F').replace(':','%3A').replace(';', '%3B').replace('=','%3D').replace('?','%3F').replace('@','%40').replace('[','5B').replace(']','%5D')
    return s
    
def Validator(base, un, pw, ff):
    global FuelSupplierSID
    msg = 'Connecting to %s as %s...'% (base, un)
    Messenger(msg)
    try:
        Aurl = base + 'Services/General/Authentication/Authenticate?'
        AData = 'data={"LoginName":"%s","Password":"%s"}'% (un, pw)
        authenticate = requests.post(Aurl, params = AData)
        Token = json.loads(authenticate.content)['Value']['Token']

        Messenger( 'Token Acquired: ' + str(len(Token)))
        Messenger( 'Accessing Data from %s...' %ff )

        DTBL = pd.read_csv(ff)
        
        Messenger("Validating Column Names")
        
        fnn = 0
        for fn in ValidationList:
            if fn not in DTBL:
                fnn+=1
                Messenger("Source Fuels Missing Column %s" %fn)
        if fnn > 0:
            return
        else:
            Messenger("Column Validation Complete")
            
        vinlist = DTBL["VIN"].unique() 
        Messenger('Found %s Unique VINs in Fuel Records. \nAccessing Cityworks VINs.' %str(len(vinlist)))
        
        Burl = base + r'services/Ams/Entity/Search?'
        BData = 'data={"EntityType":"HELENAFLEET","Attributes":["VIN"],"ReturnGeometry":false}&token=%s'% (Token)
        BReq = requests.post(Burl, params = BData)
        BRes = json.loads(BReq.content)
        CWVinlist = []  
        for veh in BRes['Value']['Records']:
            CWVinlist.append(veh['attributes']['VIN'])
        Messenger('Accessed %s Cityworks VINs.'%str(len(CWVinlist)))
        nvn = 0
        for vn in vinlist:
            if vn not in CWVinlist:
                nvn += 1
                Messenger("Unmatched VIN %s found in source fuels!" %vn)
        if nvn >0:
            return
        else:
            Messenger('No Unmatched VINs Found.')

    except Exception as e:
            Messenger(str(e))

def PartsValidator(base, un, pw, ff):
    global PartsSupplierSID
    msg = 'Connecting to %s as %s...'% (base, un)
    Messenger2(msg)
    Infos = []
    Warnings = []
    Errors = []
    try:
       # print("CheckA")
        Aurl = base + 'Services/General/Authentication/Authenticate?'
        AData = 'data={"LoginName":"%s","Password":"%s"}'% (un, pw)
        authenticate = requests.post(Aurl, params = AData)
        global Token
        Token = json.loads(authenticate.content)['Value']['Token']

        Messenger2( 'Token Acquired: ' + str(len(Token)))
        Messenger2( 'Accessing Data from %s...' %ff )

        DF1 = pd.read_excel(ff)
        DTBL = DF1[DF1['CUSTOMER NUMBER'].notnull()]

        
        fnn = 0
        for fn in ValidationList2:
            if fn not in DTBL.columns:
                fnn+=1
                Messenger2("Source Parts Missing Column %s" %fn)
                Errors.append("Source Parts Missing Column %s" %fn)
        if fnn > 0:
            return
        else:
            Messenger2("Column Validation Complete")
            
        POlist = DTBL["PO NUMBER"].unique() 
        Messenger2('Found %s Unique PO NUMBERS in IBS Records. \nAccessing Cityworks WOs.' %str(len(POlist)))
        nrow  = 0
        for PO in POlist:
           # print("CheckA1")
            #print(PO)
            Messenger2("##################################################################################")
            nrow +=1.00
            pg2['value'] = (nrow/len(POlist)*1.00)*100
           # print("CheckA!")
            Messenger2(str(int(PO)))
            Burl = base + 'services/Ams/WorkOrder/ById?'
            BData = 'data={"WorkOrderId":%s}&token=%s'% (str(int(PO)), Token)
            BReq = requests.post(Burl, params = BData)
           # print (BReq.content)
            
            try:
            #    print("CheckA1A")
                BRes = json.loads(BReq.content)
            #    print("CheckA1B")
                if BRes['Value']['WOTemplateId'] not in ('26488', '26489', '26490', '26491','26492','26493','26497'):
                  #  Messenger2("WO# %s is not a valid workorder because it is the wrong Type."%PO)
                    Errors.append(PO)
                if BRes['Value']["Status"] in ("CANCEL", "CLOSED"):
                    Warnings.append(PO)
                    Messenger2("Item Can not be loaded to the indicated workorder because the workorder is %s.  A child workorder on the same vehicle will be created and left on INVOICE status."%BRes['Value']["Status"])
                else:
                  #  Messenger2("costs will be loaded to WorkOrder %s" %PO)
                    Infos.append(PO)
                
            except:
                try:    
                    Curl = base + 'services/Ams/Entity/Search?'
                    CData = 'data={"Attributes": ["VIN"],"EntityType": "HELENAFLEET","Uids": ["%s"]}&token=%s'% (str(PO), Token)
                    CReq = requests.post(Curl, params = CData)
                    rvin = str(json.loads(CReq.content)['Value']['Records'][0]['attributes']['VIN'])
                    if rvin == str(PO):
                        Infos.append('Costs will be loaded to account: %s'%str(rvin))
                    #print (CData)
                    #print (CReq.content)
                except Exception as e:
                    Errors.append([str(e),str(PO)])
                    Messenger2(str(e))
                   # print('exception'+' ' + str(e))
        Messenger2('Validating Cost Column')
        for row in DTBL.iterrows():
            try:
               # print(row[1])
                if row[1]["EXTENDED PRICE"] == ' $0.00 ':
                    Messenger2("PO Number %s contains $0.00 cost item"%row["PO NUMBER"])
                    Errors.append("PO Number %s contains $0.00 cost item"%row["PO NUMBER"])
                else:
                    pass
                  #  print("row Costs Validated")
            except e as exception:
                Messenger2(e)
        Messenger2("Validating Unit Of Measure for Billing Cagegory")
        
        for row in DTBL.iterrows():
            if row[1]["UNIT OF MEASURE"] not in AcctDict:
                    Messenger2("UNIT OF MEASURE %s is not recognized for Parts / Fluids"%row[1]["UNIT OF MEASURE"])
                    Errors.append("UNIT OF MEASURE %s is not recognized for Parts / Fluids"%row[1]["UNIT OF MEASURE"])
        if len(Errors) == 0:
            Messenger2("Costs Validated")
            Messenger2("Unit of Measure Validated")
        elif len(Errors)>0:
            Messenger2(str(Errors))
           


    except Exception as e:
            Messenger2(str(e))
    
    if len(Errors) > 0:
        btn12["state"] = 'disabled'
    else:
        btn12["state"] = 'normal'
        Messenger2("Ready to load records")

def PartsLoader(base, pf):
    Infos = []
    Warnings = []
    Errors = []
    nrow = 0
    DF1 = pd.read_excel(pf)
    DTBL = DF1[DF1['CUSTOMER NUMBER'].notnull()]
    #DTBL = pd.read_excel(pf)
    Messenger2("Using Token from previous session: " + str(len(Token)))
    for index, row in DTBL.iterrows():
        Messenger2("##################################################################################")
        nrow +=1.00
        pg2['value'] = (nrow/len(DTBL.index*1.00))*100
        cost = row["EXTENDED PRICE"]
        AcctType = AcctDict[row["UNIT OF MEASURE"]]
        if row["LINE ABBREV"] == "9LO":
            ps = '25025'
        else:
            ps = '25024'
        units = abs(row["QUANTITY SOLD"])
        desc = PercentEncoder(row["DESCRIPTION"])
        print(desc)
       # tdate = row["Transaction Date"]
        woid = str(int(row["PO NUMBER"]))
        try:
            Messenger2("Loading PO# %s" %woid)
            Burl = base + 'services/Ams/WorkOrder/ById?'
            BData = 'data={"WorkOrderId":%s}&token=%s'% (woid, Token)
            BReq = requests.post(Burl, params = BData)
            BRes = json.loads(BReq.content)
            print(str(BRes))
            #Curl = base + 'services/AMS/WorkOrder/Entities?'
            #CData = 'data={"WorkOrderId":"%s"}'%BRes['Value']["WorkOrderId"]
            Messenger2("Checking WorkOrder %s" %woid)
            if (BRes['Value']["WorkOrderId"]):
                woid = BRes['Value']["WorkOrderId"]
                print("CheckA")
                if BRes['Value']["Status"] in ("CANCEL", "CLOSED"):
                    Messenger2("WorkOrder %s has an incompatible status, creating Child Workorder..." %woid)
                    Warnings.append("WorkOrder %s has an incompatible status, creating Child Workorder..." %woid)
                    print("CheckA1")
                    #print(BRes)
                    Curl = base + 'services/Ams/WorkOrder/CreateFromParent?'
                    CData = 'data={"WorkOrderId":"%s", "WOTemplateId":"26490","Status":"COMPLETE"}&token=%s'%(woid,  Token)
                    #print(Curl, CData)
                    #print (BRes)
                    CReq = requests.post(Curl, params = CData)     
                    CRes = json.loads(CReq.content)
                    print("CheckA1.1")
                    print("Creating Child Workorder %s"%json.loads(CReq.content)["Value"][0]['WorkOrderId'])
                    woid = CRes['Value'][0]["WorkOrderId"]
                    #print(json.loads(CReq.content))

                else:
                    print("CheckA2")
                    
                #BRes1 = BReq.content
                Messenger2("Loading Costs to WorkOrder %s"%woid)
                Durl = base + 'services/AMS/WorkOrder/Entities?'
                DData = 'data={"WorkOrderId":"%s"}&token=%s'%(woid, Token)
                DReq = requests.post(Durl, params = DData)
                DRes = json.loads(DReq.content)
                tveh = (DRes['Value'][0]['EntityUid'])
                Eurl = base + 'services/Ams/MaterialCost/AddWorkOrderCosts?'
                EData = 'data={"WorkOrderId":"%s","Units":"%s","ContractorSids":["%s"],"AcctNum":"%s","ContractorMaterialId":"%s","ContractorMaterialDescription":"%s","ContractorMaterialCost":"%s","CombineIssuesByMaterialSid":false,"Entities":[{"EntityType":"HELENAFLEET", "EntityUid":"%s"}]}&token=%s'% (woid, units, ps, AcctType, int(row["INVOICE NUMBER"]), desc, cost, tveh,  Token)
                print(str(EData))
                EReq = requests.post(Eurl, params = EData)
                ERes = json.loads(EReq.content)
                print(str(EData))
                print(str(ERes))
                Messenger2("Loaded %s for $%s to WorkOrder %s" %(row["DESCRIPTION"], cost,woid))
                Infos.append("Loaded %s for $%s to WorkOrder %s" %(row["DESCRIPTION"], cost,woid))
                # Furl = base + 'services/AMS/WorkOrder/Update?'
                # FData ='data={"WorkOrderId":"%s","Status":"COMPLETE"}&token=%s'% (woid, Token)
                
                # FReq = requests.post(Furl, params = FData)
                # FRes = EReq.content
        except Exception as e:
                Errors.append(str(e))
                Messenger2(str(e))
    Messenger2("Load Complete with %s records, %s warnings, and %s errors"%(str(len(Infos)), str(len(Warnings)), str(len(Errors))))
    Messenger2(str(Errors))
'''
            try:
                pass
            except Exception as e:
                Messenger2(str(e))
                print('exception')
  '''      

def Loader(base, un, pw, ff, fd):
    msg = 'Connecting to %s as %s...'% (base, un)
    Messenger(msg)
    try:
        Aurl = base + 'Services/General/Authentication/Authenticate?'
        AData = 'data={"LoginName":"%s","Password":"%s"}'% (un, pw)
        authenticate = requests.post(Aurl, params = AData)
        Token = json.loads(authenticate.content)['Value']['Token']

        Messenger( 'Token Acquired: ' + str(len(Token)))
        Messenger( 'Accessing Data from %s...' %ff )

        DTBL = pd.read_csv(ff)
        DTBL["Transaction Date"] = pd.to_datetime(DTBL["Transaction Date"])
        DTBL["Transaction Time"] = pd.to_datetime(DTBL["Transaction Time"], format = "%H:%M:%S")
        nerr = 0
        rerrow = 0
        nrow = 0
        ness = 0
        serrow = 0
        
        for index, row in DTBL.sort_values(by=['Transaction Date', 'Transaction Time']).iterrows():
            
            msg = str(row['Transaction Date']) + ' ' + str(row['Transaction Time']) + ' ' +  row['Custom Vehicle/Asset ID'] + ' ' + str(row['Units']) + 'GAL $'+ str(row['Net Cost']) 
            nrow +=1.00
            pg2['value'] = (nrow/len(DTBL.index*1.00))*100
            Messenger(msg)
            
            Burl = base + 'services/Ams/WorkOrder/Create?'
            BData = 'data={"EntityType":"HELENAFLEET","WOTemplateId":"26493"}&token='+Token
            BReq = requests.post(Burl, params = BData)
            BRes1 = BReq.content
            #print(BRes1)
            BRes = json.loads(BReq.content)["Value"][0]["WorkOrderId"]
            be = json.loads(BRes1)["ErrorMessages"]
            bs = json.loads(BRes1)["Status"]
            
            Curl = base + 'services/Ams/WorkOrder/AddEntities?'
            CData = 'data={"EntityType":"HELENAFLEET","EntityUids":["%s"],"UpdateXY":true,"WorkOrderId":"%s"}&token=%s'% (row["VIN"].upper(), BRes, Token)
            CReq = requests.post(Curl, params = CData)
            CRes = CReq.content
            #print(CRes)
            ce = json.loads(CRes)["ErrorMessages"]
            cs = json.loads(CRes)["Status"]
            
            Durl = base + 'services/Ams/MaterialCost/AddWorkOrderCosts?'
            DData = 'data={"WorkOrderId":"%s","Units":"%s","ContractorSids":["%s"],"TransDate":"%s","AcctNum":"FUEL","ContractorMaterialId":"%s","ContractorMaterialDescription":"%s","ContractorMaterialCost":"%s","CombineIssuesByMaterialSid":false,"Entities":[{"EntityType":"HELENAFLEET", "EntityUid":"%s"}]}&token=%s'% (BRes, row["Units"], FuelSupplierSID, str(row["Transaction Date"]), PercentEncoder(row["Product"]), PercentEncoder(row["Product Description"]), row["Net Cost"], row["VIN"].upper(), Token)
            #DData = DData.replace('%', '%25').replace('#', '%23')
            #DData = requests.utils.quote(DData)
           # print(DData)
            DReq = requests.post(Durl, params = DData)
            DRes = DReq.content
            #Messenger(str(DRes))
            #print(DRes)
            
            de = json.loads(DRes)["ErrorMessages"]
            ds = json.loads(DRes)["Status"]
    
            Eurl = base + 'services/Ams/Workorder/Update?'
            EData ='data={"WorkOrderId":"%s","ActualFinishDate":"%s","Num2":"%s","UpdateGIS": true,"Instructions":"%s","ProjectedStartDate":"%s"}&token=%s'% (BRes, fd, row["Current Odometer"], PercentEncoder(row["Merchant Name"]), str(row["Transaction Date"]), Token)
            #EData = EData.replace('%', '%25').replace('#', '%23')
            EReq = requests.post(Eurl, params = EData)
            ERes = EReq.content
            
            ee = json.loads(ERes)["ErrorMessages"]
            es = json.loads(ERes)["Status"]
            
            Furl = base + 'services/Ams/WorkOrder/Close?'
            FData = 'data={"WorkOrderIds":["%s"]}&token=%s'% (BRes, Token)
            FReq = requests.post(Furl, params = FData)
            FRes = FReq.content
            
            fe = json.loads(FRes)["ErrorMessages"]
            fs = json.loads(FRes)["Status"]
            
            nee = 0            
            for err in (be, ce, de, ee, fe):
                if len(err) > 0:
                    Messenger(str(err))
                    nee += 1
            if nee >0:
                nerr += nee
                rerrow += 1
                
            nes = 0            
            for ess in (bs, cs, ds, es, fs):
                if ess != 0:
                    Messenger('Found Status %s in row.' %ess)
                    nes += 1
            if nes >0:
                ness += nes
                serrow += 1
                
            if [nes, nee] == [0, 0]:
                Messenger('Successfully Loaded to Workorder: %s' %BRes)

        Messenger('Found %s errors in %s rows.'% (str(nerr), str(rerrow)))
            
    except Exception as e:
            Messenger(str(e))
            if e.message:
                Messenger(str(e.message))



            
def Button1Click():
    global BaseURL, FuelFile
    Validator(txt6.get(), txt2.get(), txt3.get(), FuelFile)

def Button2Click():
    global BaseURL, FuelFile
    Loader(txt6.get(), txt2.get(), txt3.get(), FuelFile, txt5.get())

def Button3Click():
    window2 = Tk()
    text_file = tkFileDialog.asksaveasfile(initialdir = "/",title = "Save",filetypes = (("txt files","*.txt"),("all files","*.*")))
    #text_file = open(window2.filename, "w")
    text_file.write(txt1.get(1.0, tk.END))
    text_file.close()


def Button4Click():
    window1 = Tk()
    window1.filename = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))
    global FuelFile
    FuelFile = window1.filename
    txt4.delete(0, END)
    txt4.insert(END, FuelFile)

def Button10Click():
    window1 = Tk()
    window1.filename = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("csv files","*.xlsx"),("all files","*.*")))
    global PartsFile
    PartsFile = window1.filename
    txt10.delete(0, END)
    txt10.insert(END, PartsFile)

def Button11Click():
    global BaseURL, FuelFile
    PartsValidator(txt7.get(), txt8.get(), txt9.get(), PartsFile)

def Button12Click():
    global BaseURL, FuelFile
    PartsLoader(txt7.get(),  PartsFile)

def Button13Click():
    window2 = Tk()
    text_file = tkFileDialog.asksaveasfile(initialdir = "/",title = "Save",filetypes = (("txt files","*.txt"),("all files","*.*")))
    #text_file = open(window2.filename, "w")
    text_file.write(txt14.get(1.0, tk.END))
    text_file.close()


                
window = Tk()
window.title("Cityworks Fleet Importer")
window.geometry('800x400')
window.wm_iconbitmap(r'icon.ico')
TAB_CONTROL = ttk.Notebook(window)
TAB1 = ttk.Frame(TAB_CONTROL)
TAB_CONTROL.add(TAB1, text='Fuel Loader')

TAB2 = ttk.Frame(TAB_CONTROL)
TAB_CONTROL.add(TAB2, text='Parts Loader')
TAB_CONTROL.pack(expand=1, fill="both")


lbl1 = Label(TAB1, text="Base URL: ")
lbl1.grid(column=0, row=0)
txt6 = Entry(TAB1,width=100)
txt6.grid(column=1, row=0, columnspan = 2, sticky = tk.W+tk.E)
txt6.insert(END, BaseURL)

lbl2 = Label(TAB1, text="Username: ")
lbl2.grid(column=0, row=1)
txt2 = Entry(TAB1,width=25)
txt2.grid(column=1, row=1)
txt2.insert(END, UserName)

lbl3 = Label(TAB1, text="Password: ")
lbl3.grid(column=0, row=2)
txt3 = Entry(TAB1,width=25)
txt3.grid(column=1, row=2)
txt3.insert(END, Password)

lbl4 = Label(TAB1, text="Source Fuels: ")
lbl4.grid(column=0, row=3)
txt4 = Entry(TAB1,width=75)
txt4.grid(column=1, row=3)
txt4.insert(END, FuelFile)
btn4 = Button(TAB1, text="Select...", command=Button4Click)
btn4.grid(column=2, row=3)

lbl5 = Label(TAB1, text="Bill Date: ")
lbl5.grid(column=0, row=4)
txt5 = Entry(TAB1,width=25)
txt5.grid(column=1, row=4)
txt5.insert(END, BillDate)

btn1 = Button(TAB1, text="Validate .csv", command=Button1Click)
btn1.grid(column=0, row=5)

btn2 = Button(TAB1, text="Load Fuels", command=Button2Click)
btn2.grid(column=1, row=5)

btn3 = Button(TAB1, text="Save Log File", command=Button3Click)
btn3.grid(column=0, row=8)

lbl6 = Label(TAB1, text="Messages: ")
lbl6.grid(column=0, row=6)    
txt1 = scrolledtext.ScrolledText(TAB1,width=40,height=10)
txt1.grid(column=0,row=7, columnspan = 3, sticky = tk.W+tk.E)
txt1.configure(state ='disabled') 

pg=Progressbar(TAB1,orient=HORIZONTAL,length=100,mode='determinate')
pg.grid(column=0,row=9, columnspan = 3, sticky = tk.W+tk.E)



lbl7 = Label(TAB2, text="Base URL: ")
lbl7.grid(column=0, row=0)
txt7 = Entry(TAB2,width=100)
txt7.grid(column=1, row=0, columnspan = 2, sticky = tk.W+tk.E)
txt7.insert(END, BaseURL)

lbl8 = Label(TAB2, text="Username: ")
lbl8.grid(column=0, row=1)
txt8 = Entry(TAB2,width=25)
txt8.grid(column=1, row=1)
txt8.insert(END, UserName)

lbl9 = Label(TAB2, text="Password: ")
lbl9.grid(column=0, row=2)
txt9 = Entry(TAB2,width=25)
txt9.grid(column=1, row=2)
txt9.insert(END, Password)

lbl10 = Label(TAB2, text="Source Parts: ")
lbl10.grid(column=0, row=3)
txt10 = Entry(TAB2,width=75)
txt10.grid(column=1, row=3)
txt10.insert(END, PartsFile)
btn10 = Button(TAB2, text="Select...", command=Button10Click)
btn10.grid(column=2, row=3)

btn11 = Button(TAB2, text="Validate .xlsx", command=Button11Click)
btn11.grid(column=0, row=5)

btn12 = Button(TAB2, text="Load Parts", command=Button12Click)
btn12.grid(column=1, row=5)
btn12["state"] = "disabled"

btn13 = Button(TAB2, text="Save Log File", command=Button13Click)
btn13.grid(column=0, row=8)

lbl14 = Label(TAB2, text="Messages: ")
lbl14.grid(column=0, row=6)    
txt14 = scrolledtext.ScrolledText(TAB2,width=40,height=10)
txt14.grid(column=0,row=7, columnspan = 3, sticky = tk.W+tk.E)
txt14.configure(state ='disabled') 


pg2=Progressbar(TAB2,orient=HORIZONTAL,length=100,mode='determinate')
pg2.grid(column=0,row=9, columnspan = 3, sticky = tk.W+tk.E)


TAB1.mainloop()
TAB2.mainloop()
